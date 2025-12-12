"""
Agent Performance Analytics - Track and Optimize Agent Performance

Tracks agent performance metrics and provides optimization suggestions.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


@dataclass
class AgentMetrics:
    """Metrics for an agent."""
    agent_id: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_cost: float = 0.0
    total_latency_ms: float = 0.0
    average_quality_score: float = 0.0
    average_confidence: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    @property
    def average_cost(self) -> float:
        """Calculate average cost."""
        if self.total_requests == 0:
            return 0.0
        return self.total_cost / self.total_requests
    
    @property
    def average_latency_ms(self) -> float:
        """Calculate average latency."""
        if self.total_requests == 0:
            return 0.0
        return self.total_latency_ms / self.total_requests


@dataclass
class OptimizationSuggestion:
    """Optimization suggestion for an agent."""
    agent_id: str
    suggestion_type: str
    description: str
    expected_improvement: str
    priority: int = 5  # 1-10


class AgentAnalytics:
    """
    Tracks agent performance and provides optimization suggestions.
    """
    
    def __init__(self):
        """Initialize agent analytics."""
        self.metrics: Dict[str, AgentMetrics] = {}
        self.historical_data: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.logger = logging.getLogger(__name__)
    
    def record_agent_result(
        self,
        agent_id: str,
        success: bool,
        cost: float = 0.0,
        latency_ms: float = 0.0,
        quality_score: float = 0.0,
        confidence: float = 0.0
    ) -> None:
        """
        Record agent result.
        
        Args:
            agent_id: Agent identifier
            success: Whether request succeeded
            cost: Cost in USD
            latency_ms: Latency in milliseconds
            quality_score: Quality score
            confidence: Confidence score
        """
        if agent_id not in self.metrics:
            self.metrics[agent_id] = AgentMetrics(agent_id=agent_id)
        
        metrics = self.metrics[agent_id]
        metrics.total_requests += 1
        
        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1
        
        metrics.total_cost += cost
        metrics.total_latency_ms += latency_ms
        
        # Update averages
        if metrics.total_requests == 1:
            metrics.average_quality_score = quality_score
            metrics.average_confidence = confidence
        else:
            metrics.average_quality_score = (
                (metrics.average_quality_score * (metrics.total_requests - 1) + quality_score) /
                metrics.total_requests
            )
            metrics.average_confidence = (
                (metrics.average_confidence * (metrics.total_requests - 1) + confidence) /
                metrics.total_requests
            )
        
        metrics.last_updated = datetime.utcnow()
        
        # Store historical data
        self.historical_data[agent_id].append({
            "timestamp": datetime.utcnow(),
            "success": success,
            "cost": cost,
            "latency_ms": latency_ms,
            "quality_score": quality_score,
            "confidence": confidence
        })
        
        # Keep only last 1000 entries
        if len(self.historical_data[agent_id]) > 1000:
            self.historical_data[agent_id] = self.historical_data[agent_id][-1000:]
    
    def get_agent_metrics(
        self,
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get agent metrics.
        
        Args:
            agent_id: Optional agent ID to filter by
            
        Returns:
            Metrics dictionary
        """
        if agent_id:
            if agent_id not in self.metrics:
                return {}
            
            metrics = self.metrics[agent_id]
            return {
                "agent_id": metrics.agent_id,
                "total_requests": metrics.total_requests,
                "success_rate": metrics.success_rate,
                "average_cost": metrics.average_cost,
                "average_latency_ms": metrics.average_latency_ms,
                "average_quality_score": metrics.average_quality_score,
                "average_confidence": metrics.average_confidence
            }
        else:
            return {
                agent_id: {
                    "total_requests": m.total_requests,
                    "success_rate": m.success_rate,
                    "average_cost": m.average_cost,
                    "average_latency_ms": m.average_latency_ms,
                    "average_quality_score": m.average_quality_score
                }
                for agent_id, m in self.metrics.items()
            }
    
    def get_optimization_suggestions(
        self,
        agent_id: Optional[str] = None
    ) -> List[OptimizationSuggestion]:
        """
        Get optimization suggestions for agents.
        
        Args:
            agent_id: Optional agent ID to filter by
            
        Returns:
            List of optimization suggestions
        """
        suggestions = []
        
        agents_to_analyze = [agent_id] if agent_id else list(self.metrics.keys())
        
        for aid in agents_to_analyze:
            if aid not in self.metrics:
                continue
            
            metrics = self.metrics[aid]
            
            # Check success rate
            if metrics.success_rate < 0.90:
                suggestions.append(OptimizationSuggestion(
                    agent_id=aid,
                    suggestion_type="reliability",
                    description=f"Success rate {metrics.success_rate:.1%} is below 90%",
                    expected_improvement="Improve error handling and retry logic",
                    priority=8
                ))
            
            # Check cost efficiency
            if metrics.average_cost > 0.05:  # $0.05 per request
                suggestions.append(OptimizationSuggestion(
                    agent_id=aid,
                    suggestion_type="cost",
                    description=f"Average cost ${metrics.average_cost:.4f} is high",
                    expected_improvement="Consider using lighter model or optimizing prompts",
                    priority=6
                ))
            
            # Check latency
            if metrics.average_latency_ms > 5000:  # 5 seconds
                suggestions.append(OptimizationSuggestion(
                    agent_id=aid,
                    suggestion_type="performance",
                    description=f"Average latency {metrics.average_latency_ms:.0f}ms is high",
                    expected_improvement="Optimize prompts or use faster model",
                    priority=7
                ))
            
            # Check quality
            if metrics.average_quality_score < 0.70:
                suggestions.append(OptimizationSuggestion(
                    agent_id=aid,
                    suggestion_type="quality",
                    description=f"Average quality {metrics.average_quality_score:.2f} is below threshold",
                    expected_improvement="Improve prompts or use higher-quality model",
                    priority=9
                ))
        
        # Sort by priority
        suggestions.sort(key=lambda x: x.priority, reverse=True)
        
        return suggestions

