"""
AI Orchestrator - Master Agent for Multi-Agent AI Collaboration

Coordinates specialized AI agents to generate high-quality previews through:
- Agent team selection
- Parallel agent execution
- Context fusion
- Conflict resolution
- Quality-driven iteration

UPGRADED: Now uses real GPT-4o agents via AgentExecutor for actual AI-powered extraction.
"""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from enum import Enum

from backend.services.agent_protocol import (
    AgentType, AgentMessage, AgentResponse, AgentProtocol, FusionResult
)
from backend.services.ai_rate_limiter import AIRateLimiter, RateLimitStatus
from backend.services.ai_cost_optimizer import AICostOptimizer, AIModel
from backend.services.agent_executor import get_agent_executor, AgentExecutor

logger = logging.getLogger(__name__)


class OrchestrationStrategy(str, Enum):
    """Orchestration strategies."""
    PARALLEL = "parallel"  # All agents run simultaneously
    SEQUENTIAL = "sequential"  # Agents run in order
    ADAPTIVE = "adaptive"  # Strategy adapts based on complexity


@dataclass
class AgentTeam:
    """Team of agents for a task."""
    agents: List[AgentType]
    strategy: OrchestrationStrategy
    priority: int = 5


@dataclass
class OrchestrationResult:
    """Result from orchestration."""
    success: bool
    fused_result: Dict[str, Any]
    agent_responses: List[AgentResponse]
    fusion_result: Optional[FusionResult] = None
    total_cost: float = 0.0
    total_latency_ms: float = 0.0
    quality_score: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class AIOrchestrator:
    """
    Master agent that coordinates specialized AI agents.
    
    Responsibilities:
    1. Analyze request complexity
    2. Select optimal agent team
    3. Coordinate multi-agent workflow
    4. Manage context and memory
    5. Handle failures and retries
    
    UPGRADED: Now uses real GPT-4o agents via AgentExecutor.
    """
    
    def __init__(
        self,
        rate_limiter: Optional[AIRateLimiter] = None,
        cost_optimizer: Optional[AICostOptimizer] = None,
        agent_executor: Optional[AgentExecutor] = None
    ):
        """
        Initialize AI orchestrator.
        
        Args:
            rate_limiter: Rate limiter instance
            cost_optimizer: Cost optimizer instance
            agent_executor: Agent executor for real AI calls
        """
        self.rate_limiter = rate_limiter or AIRateLimiter()
        self.cost_optimizer = cost_optimizer or AICostOptimizer()
        self.agent_executor = agent_executor or get_agent_executor()
        self.logger = logging.getLogger(__name__)
        self.protocol = AgentProtocol()
        self.logger.info("🤖 AIOrchestrator initialized with real agent execution")
        
    def select_agent_team(
        self,
        url: str,
        complexity: str = "medium",
        requires_vision: bool = True,
        requires_design_dna: bool = True
    ) -> AgentTeam:
        """
        Select optimal agent team for a request.
        
        Args:
            url: URL to process
            complexity: Complexity level (simple, medium, complex)
            requires_vision: Whether vision capabilities are needed
            requires_design_dna: Whether design DNA extraction is needed
            
        Returns:
            AgentTeam with selected agents and strategy
        """
        agents = []
        
        # Always include core agents
        agents.append(AgentType.VISUAL_ANALYST)  # Screenshot analysis
        agents.append(AgentType.CONTENT_CURATOR)  # HTML/content extraction
        
        # Add design DNA extraction if needed
        if requires_design_dna:
            agents.append(AgentType.DESIGN_ARCHAEOLOGIST)
        
        # Add reasoning chain for complex requests
        if complexity in ["medium", "complex"]:
            agents.append(AgentType.REASONING_CHAIN)
        
        # Always include context fusion
        agents.append(AgentType.CONTEXT_FUSION)
        
        # Select strategy based on complexity
        if complexity == "simple":
            strategy = OrchestrationStrategy.PARALLEL
        elif complexity == "medium":
            strategy = OrchestrationStrategy.ADAPTIVE
        else:
            strategy = OrchestrationStrategy.SEQUENTIAL
        
        team = AgentTeam(
            agents=agents,
            strategy=strategy,
            priority=5
        )
        
        self.logger.info(
            f"Selected agent team: {[a.value for a in agents]}, "
            f"strategy: {strategy.value}"
        )
        
        return team
    
    def coordinate_parallel_execution(
        self,
        team: AgentTeam,
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[AgentResponse]:
        """
        Coordinate parallel execution of agent team.
        
        Args:
            team: Agent team to execute
            inputs: Input data for agents
            context: Shared context
            
        Returns:
            List of agent responses
        """
        start_time = time.time()
        responses = []
        
        # Create messages for each agent
        messages = []
        for agent_type in team.agents:
            # Skip context fusion (runs after others)
            if agent_type == AgentType.CONTEXT_FUSION:
                continue
            
            message = AgentMessage(
                agent_type=agent_type,
                operation="extract",
                input_data=inputs,
                context=context,
                priority=team.priority
            )
            messages.append(message)
        
        # Execute agents in parallel
        with ThreadPoolExecutor(max_workers=len(messages)) as executor:
            futures = {}
            
            for message in messages:
                # Check rate limits
                status, wait_time = self.rate_limiter.check_rate_limit(
                    message.agent_type.value,
                    message.priority
                )
                
                if status == RateLimitStatus.ALLOWED:
                    future = executor.submit(
                        self._execute_agent,
                        message
                    )
                    futures[future] = message
                else:
                    self.logger.warning(
                        f"Rate limited for {message.agent_type.value}, "
                        f"wait time: {wait_time}s"
                    )
                    # Create error response
                    error_response = self.protocol.create_error_response(
                        message.message_id,
                        message.agent_type,
                        f"Rate limited: {wait_time}s wait time"
                    )
                    responses.append(error_response)
            
            # Collect results
            for future in as_completed(futures):
                message = futures[future]
                try:
                    response = future.result(timeout=message.timeout)
                    responses.append(response)
                    # Record rate limit
                    self.rate_limiter.record_request(message.agent_type.value)
                except Exception as e:
                    self.logger.error(
                        f"Agent {message.agent_type.value} failed: {e}",
                        exc_info=True
                    )
                    error_response = self.protocol.create_error_response(
                        message.message_id,
                        message.agent_type,
                        str(e)
                    )
                    responses.append(error_response)
        
        # Run context fusion agent
        fusion_message = AgentMessage(
            agent_type=AgentType.CONTEXT_FUSION,
            operation="fuse",
            input_data={"responses": [r.to_dict() for r in responses]},
            context=context,
            priority=team.priority
        )
        
        try:
            fusion_response = self._execute_agent(fusion_message)
            responses.append(fusion_response)
        except Exception as e:
            self.logger.error(f"Context fusion failed: {e}", exc_info=True)
        
        latency_ms = (time.time() - start_time) * 1000
        self.logger.info(
            f"Parallel execution complete: {len(responses)} responses, "
            f"{latency_ms:.0f}ms"
        )
        
        return responses
    
    def _execute_agent(
        self,
        message: AgentMessage
    ) -> AgentResponse:
        """
        Execute a single agent using the AgentExecutor.
        
        This method now routes to real GPT-4o powered agents for:
        - Visual analysis (screenshot understanding)
        - Content curation (HTML/metadata extraction)
        - Design archaeology (design DNA extraction)
        - Quality criticism (preview evaluation)
        - Context fusion (combining agent outputs)
        
        Args:
            message: Agent message with input data
            
        Returns:
            AgentResponse with real AI-generated output
        """
        self.logger.info(f"🚀 Executing agent: {message.agent_type.value}")
        
        try:
            # Use the real agent executor for AI-powered execution
            response = self.agent_executor.execute(message)
            
            self.logger.info(
                f"✅ Agent {message.agent_type.value} completed: "
                f"success={response.success}, "
                f"confidence={response.confidence:.2f}, "
                f"latency={response.latency_ms:.0f}ms"
            )
            
            return response
            
        except Exception as e:
            self.logger.error(
                f"❌ Agent {message.agent_type.value} execution failed: {e}",
                exc_info=True
            )
            # Return error response
            return self.protocol.create_error_response(
                message.message_id,
                message.agent_type,
                str(e)
            )
    
    def fuse_agent_responses(
        self,
        responses: List[AgentResponse],
        strategy: str = "weighted_average"
    ) -> FusionResult:
        """
        Fuse multiple agent responses into unified result.
        
        Args:
            responses: List of agent responses
            strategy: Fusion strategy
            
        Returns:
            FusionResult with fused data
        """
        return self.protocol.merge_responses(responses, strategy)
    
    def orchestrate_preview_generation(
        self,
        url: str,
        screenshot_bytes: bytes,
        html_content: str,
        complexity: str = "medium"
    ) -> OrchestrationResult:
        """
        Orchestrate complete preview generation using multi-agent system.
        
        Args:
            url: URL to process
            screenshot_bytes: Screenshot bytes
            html_content: HTML content
            complexity: Complexity level
            
        Returns:
            OrchestrationResult with fused preview data
        """
        start_time = time.time()
        
        try:
            # 1. Select agent team
            team = self.select_agent_team(
                url=url,
                complexity=complexity,
                requires_vision=True,
                requires_design_dna=True
            )
            
            # 2. Prepare inputs
            inputs = {
                "url": url,
                "screenshot_bytes": screenshot_bytes,
                "html_content": html_content
            }
            
            context = {
                "url": url,
                "timestamp": time.time()
            }
            
            # 3. Execute agent team
            responses = self.coordinate_parallel_execution(team, inputs, context)
            
            # 4. Filter successful responses
            successful_responses = [r for r in responses if r.success]
            
            if not successful_responses:
                return OrchestrationResult(
                    success=False,
                    fused_result={},
                    agent_responses=responses,
                    errors=["All agents failed"],
                    total_latency_ms=(time.time() - start_time) * 1000
                )
            
            # 5. Fuse responses
            fusion_result = self.fuse_agent_responses(successful_responses)
            
            # 6. Calculate metrics
            total_cost = sum(r.cost for r in successful_responses)
            total_latency_ms = (time.time() - start_time) * 1000
            
            # 7. Calculate quality score
            quality_score = fusion_result.overall_confidence
            
            result = OrchestrationResult(
                success=True,
                fused_result=fusion_result.fused_data,
                agent_responses=responses,
                fusion_result=fusion_result,
                total_cost=total_cost,
                total_latency_ms=total_latency_ms,
                quality_score=quality_score,
                warnings=[f"Conflicts: {len(fusion_result.conflicts)}"]
            )
            
            self.logger.info(
                f"Orchestration complete: quality={quality_score:.2f}, "
                f"cost=${total_cost:.4f}, latency={total_latency_ms:.0f}ms"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Orchestration failed: {e}", exc_info=True)
            return OrchestrationResult(
                success=False,
                fused_result={},
                agent_responses=[],
                errors=[str(e)],
                total_latency_ms=(time.time() - start_time) * 1000
            )

