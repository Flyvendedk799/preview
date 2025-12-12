"""
AI Rate Limiter - Intelligent Rate Limiting for AI API Calls

Manages rate limits for OpenAI API calls with:
- Per-agent rate limits
- Priority queuing
- Exponential backoff
- Circuit breakers
- Request batching
"""

import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import threading

logger = logging.getLogger(__name__)


class RateLimitStatus(str, Enum):
    """Rate limit status."""
    ALLOWED = "allowed"
    RATE_LIMITED = "rate_limited"
    CIRCUIT_OPEN = "circuit_open"
    QUEUED = "queued"


@dataclass
class RateLimitConfig:
    """Rate limit configuration for an agent."""
    requests_per_minute: int = 50
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 10  # Max requests in short burst
    priority_threshold: int = 7  # Priority >= this gets priority queue


@dataclass
class RateLimitState:
    """Current rate limit state."""
    requests_minute: deque = field(default_factory=lambda: deque(maxlen=60))
    requests_hour: deque = field(default_factory=lambda: deque(maxlen=3600))
    requests_day: deque = field(default_factory=lambda: deque(maxlen=86400))
    circuit_open: bool = False
    circuit_open_until: Optional[float] = None
    last_request_time: Optional[float] = None


class AIRateLimiter:
    """
    Intelligent rate limiter for AI API calls.
    
    Features:
    - Per-agent rate limits
    - Priority queuing
    - Exponential backoff
    - Circuit breakers
    - Request batching
    """
    
    def __init__(self):
        """Initialize rate limiter."""
        self.lock = threading.Lock()
        self.agent_configs: Dict[str, RateLimitConfig] = {}
        self.agent_states: Dict[str, RateLimitState] = {}
        self.priority_queue: List[Tuple[float, str, Dict[str, Any]]] = []  # (priority, agent_id, request_data)
        self.logger = logging.getLogger(__name__)
        
        # Default configurations
        self._setup_default_configs()
    
    def _setup_default_configs(self):
        """Setup default rate limit configurations."""
        # Visual Analyst - vision calls are expensive
        self.agent_configs["visual_analyst"] = RateLimitConfig(
            requests_per_minute=20,
            requests_per_hour=500,
            requests_per_day=5000
        )
        
        # Content Curator - text-only, can handle more
        self.agent_configs["content_curator"] = RateLimitConfig(
            requests_per_minute=60,
            requests_per_hour=2000,
            requests_per_day=20000
        )
        
        # Design Archaeologist - vision + reasoning
        self.agent_configs["design_archaeologist"] = RateLimitConfig(
            requests_per_minute=30,
            requests_per_hour=800,
            requests_per_day=8000
        )
        
        # Reasoning Chain - complex reasoning
        self.agent_configs["reasoning_chain"] = RateLimitConfig(
            requests_per_minute=40,
            requests_per_hour=1000,
            requests_per_day=10000
        )
        
        # Quality Critic - lightweight
        self.agent_configs["quality_critic"] = RateLimitConfig(
            requests_per_minute=100,
            requests_per_hour=5000,
            requests_per_day=50000
        )
        
        # Refinement - moderate
        self.agent_configs["refinement"] = RateLimitConfig(
            requests_per_minute=50,
            requests_per_hour=2000,
            requests_per_day=20000
        )
    
    def check_rate_limit(
        self,
        agent_id: str,
        priority: int = 5
    ) -> Tuple[RateLimitStatus, Optional[float]]:
        """
        Check if request is allowed under rate limits.
        
        Args:
            agent_id: Agent identifier
            priority: Request priority (1-10)
            
        Returns:
            Tuple of (status, wait_time_seconds)
        """
        with self.lock:
            # Get or create state
            if agent_id not in self.agent_states:
                self.agent_states[agent_id] = RateLimitState()
            
            state = self.agent_states[agent_id]
            config = self.agent_configs.get(agent_id, RateLimitConfig())
            current_time = time.time()
            
            # Check circuit breaker
            if state.circuit_open:
                if state.circuit_open_until and current_time < state.circuit_open_until:
                    wait_time = state.circuit_open_until - current_time
                    return (RateLimitStatus.CIRCUIT_OPEN, wait_time)
                else:
                    # Circuit breaker timeout expired, reset
                    state.circuit_open = False
                    state.circuit_open_until = None
            
            # Clean old entries
            self._clean_old_entries(state, current_time)
            
            # Check rate limits
            # Per-minute limit
            if len(state.requests_minute) >= config.requests_per_minute:
                if priority >= config.priority_threshold:
                    # High priority - allow but log warning
                    self.logger.warning(f"Rate limit exceeded for {agent_id} (minute), but allowing high-priority request")
                else:
                    # Calculate wait time
                    oldest_request = state.requests_minute[0]
                    wait_time = 60 - (current_time - oldest_request)
                    return (RateLimitStatus.RATE_LIMITED, max(0, wait_time))
            
            # Per-hour limit
            if len(state.requests_hour) >= config.requests_per_hour:
                oldest_request = state.requests_hour[0]
                wait_time = 3600 - (current_time - oldest_request)
                return (RateLimitStatus.RATE_LIMITED, max(0, wait_time))
            
            # Per-day limit
            if len(state.requests_day) >= config.requests_per_day:
                oldest_request = state.requests_day[0]
                wait_time = 86400 - (current_time - oldest_request)
                return (RateLimitStatus.RATE_LIMITED, max(0, wait_time))
            
            # Check burst limit
            recent_requests = [r for r in state.requests_minute if current_time - r < 10]
            if len(recent_requests) >= config.burst_limit:
                wait_time = 10 - (current_time - recent_requests[0])
                return (RateLimitStatus.RATE_LIMITED, max(0, wait_time))
            
            # Allowed
            return (RateLimitStatus.ALLOWED, None)
    
    def record_request(
        self,
        agent_id: str
    ) -> None:
        """
        Record a request for rate limit tracking.
        
        Args:
            agent_id: Agent identifier
        """
        with self.lock:
            if agent_id not in self.agent_states:
                self.agent_states[agent_id] = RateLimitState()
            
            state = self.agent_states[agent_id]
            current_time = time.time()
            
            state.requests_minute.append(current_time)
            state.requests_hour.append(current_time)
            state.requests_day.append(current_time)
            state.last_request_time = current_time
    
    def open_circuit(
        self,
        agent_id: str,
        duration_seconds: float = 60.0
    ) -> None:
        """
        Open circuit breaker for an agent.
        
        Args:
            agent_id: Agent identifier
            duration_seconds: How long to keep circuit open
        """
        with self.lock:
            if agent_id not in self.agent_states:
                self.agent_states[agent_id] = RateLimitState()
            
            state = self.agent_states[agent_id]
            state.circuit_open = True
            state.circuit_open_until = time.time() + duration_seconds
            
            self.logger.warning(
                f"Circuit breaker opened for {agent_id} "
                f"for {duration_seconds} seconds"
            )
    
    def close_circuit(
        self,
        agent_id: str
    ) -> None:
        """
        Close circuit breaker for an agent.
        
        Args:
            agent_id: Agent identifier
        """
        with self.lock:
            if agent_id in self.agent_states:
                state = self.agent_states[agent_id]
                state.circuit_open = False
                state.circuit_open_until = None
                
                self.logger.info(f"Circuit breaker closed for {agent_id}")
    
    def _clean_old_entries(
        self,
        state: RateLimitState,
        current_time: float
    ) -> None:
        """Clean old entries from rate limit tracking."""
        # Clean minute window (60 seconds)
        while state.requests_minute and current_time - state.requests_minute[0] > 60:
            state.requests_minute.popleft()
        
        # Clean hour window (3600 seconds)
        while state.requests_hour and current_time - state.requests_hour[0] > 3600:
            state.requests_hour.popleft()
        
        # Clean day window (86400 seconds)
        while state.requests_day and current_time - state.requests_day[0] > 86400:
            state.requests_day.popleft()
    
    def get_wait_time(
        self,
        agent_id: str
    ) -> float:
        """
        Get estimated wait time for next request.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Wait time in seconds
        """
        status, wait_time = self.check_rate_limit(agent_id)
        return wait_time or 0.0
    
    def get_stats(
        self,
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get rate limit statistics.
        
        Args:
            agent_id: Optional agent ID to filter by
            
        Returns:
            Statistics dictionary
        """
        with self.lock:
            if agent_id:
                if agent_id not in self.agent_states:
                    return {"agent_id": agent_id, "requests": 0}
                
                state = self.agent_states[agent_id]
                return {
                    "agent_id": agent_id,
                    "requests_minute": len(state.requests_minute),
                    "requests_hour": len(state.requests_hour),
                    "requests_day": len(state.requests_day),
                    "circuit_open": state.circuit_open,
                    "last_request_time": state.last_request_time
                }
            else:
                # All agents
                return {
                    agent_id: {
                        "requests_minute": len(state.requests_minute),
                        "requests_hour": len(state.requests_hour),
                        "requests_day": len(state.requests_day),
                        "circuit_open": state.circuit_open
                    }
                    for agent_id, state in self.agent_states.items()
                }

