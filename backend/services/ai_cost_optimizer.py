"""
AI Cost Optimizer - Intelligent Cost Management for AI Operations

Manages AI API costs through:
- Smart agent selection (lighter models for simple tasks)
- Multi-level caching
- Batch processing
- Token optimization
- Cost budgets and limits
- Model routing based on quality requirements
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AIModel(str, Enum):
    """AI models with cost information."""
    GPT4O = "gpt-4o"
    GPT4O_MINI = "gpt-4o-mini"
    GPT4_TURBO = "gpt-4-turbo"


# Cost per 1M tokens (as of 2025)
MODEL_COSTS = {
    AIModel.GPT4O: {"input": 2.50, "output": 10.00},
    AIModel.GPT4O_MINI: {"input": 0.15, "output": 0.60},
    AIModel.GPT4_TURBO: {"input": 10.00, "output": 30.00},
}

# Model capabilities (for routing decisions)
MODEL_CAPABILITIES = {
    AIModel.GPT4O: {
        "vision": True,
        "complex_reasoning": True,
        "quality_threshold": 0.90,
        "max_tokens": 16384
    },
    AIModel.GPT4O_MINI: {
        "vision": False,
        "complex_reasoning": False,
        "quality_threshold": 0.70,
        "max_tokens": 16384
    },
    AIModel.GPT4_TURBO: {
        "vision": True,
        "complex_reasoning": True,
        "quality_threshold": 0.95,
        "max_tokens": 128000
    }
}


@dataclass
class CostBudget:
    """Cost budget configuration."""
    per_request_limit: float = 0.10  # $0.10 per preview
    daily_limit: float = 100.0  # $100 per day
    monthly_limit: float = 3000.0  # $3000 per month
    current_daily_spend: float = 0.0
    current_monthly_spend: float = 0.0


@dataclass
class CostMetrics:
    """Cost metrics for an operation."""
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    operation: str


class AICostOptimizer:
    """
    Intelligent cost optimization for AI operations.
    
    Strategies:
    1. Model Selection: Use cheapest model that meets quality requirements
    2. Caching: Cache at multiple levels to avoid redundant calls
    3. Batching: Batch similar requests
    4. Token Optimization: Optimize prompts to reduce tokens
    5. Budget Enforcement: Enforce cost limits with fallbacks
    """
    
    def __init__(self, budget: Optional[CostBudget] = None):
        """
        Initialize cost optimizer.
        
        Args:
            budget: Cost budget configuration
        """
        self.budget = budget or CostBudget()
        self.logger = logging.getLogger(__name__)
        
    def select_optimal_model(
        self,
        requires_vision: bool = False,
        requires_complex_reasoning: bool = False,
        quality_threshold: float = 0.75,
        estimated_tokens: int = 2000
    ) -> Tuple[AIModel, float]:
        """
        Select optimal model based on requirements and cost.
        
        Args:
            requires_vision: Whether vision capabilities are needed
            requires_complex_reasoning: Whether complex reasoning is needed
            quality_threshold: Minimum quality requirement
            estimated_tokens: Estimated token usage
            
        Returns:
            Tuple of (selected_model, estimated_cost)
        """
        candidates = []
        
        # Filter models by capabilities
        for model in AIModel:
            caps = MODEL_CAPABILITIES[model]
            
            # Check vision requirement
            if requires_vision and not caps["vision"]:
                continue
            
            # Check reasoning requirement
            if requires_complex_reasoning and not caps["complex_reasoning"]:
                continue
            
            # Check quality threshold
            if quality_threshold > caps["quality_threshold"]:
                continue
            
            # Calculate estimated cost
            costs = MODEL_COSTS[model]
            estimated_cost = (
                (estimated_tokens * 0.7 / 1_000_000) * costs["input"] +
                (estimated_tokens * 0.3 / 1_000_000) * costs["output"]
            )
            
            candidates.append((model, estimated_cost))
        
        if not candidates:
            # Fallback to GPT-4o if no candidates
            self.logger.warning("No suitable model found, using GPT-4o as fallback")
            model = AIModel.GPT4O
            costs = MODEL_COSTS[model]
            estimated_cost = (
                (estimated_tokens * 0.7 / 1_000_000) * costs["input"] +
                (estimated_tokens * 0.3 / 1_000_000) * costs["output"]
            )
            return (model, estimated_cost)
        
        # Select cheapest model that meets requirements
        candidates.sort(key=lambda x: x[1])
        selected_model, estimated_cost = candidates[0]
        
        self.logger.info(
            f"Selected model: {selected_model.value} "
            f"(cost: ${estimated_cost:.4f}, vision: {requires_vision}, "
            f"reasoning: {requires_complex_reasoning})"
        )
        
        return (selected_model, estimated_cost)
    
    def check_budget(
        self,
        estimated_cost: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if operation fits within budget.
        
        Args:
            estimated_cost: Estimated cost of operation
            
        Returns:
            Tuple of (allowed, reason_if_not_allowed)
        """
        # Check per-request limit
        if estimated_cost > self.budget.per_request_limit:
            return (False, f"Cost ${estimated_cost:.4f} exceeds per-request limit ${self.budget.per_request_limit}")
        
        # Check daily limit
        if self.budget.current_daily_spend + estimated_cost > self.budget.daily_limit:
            return (False, f"Cost would exceed daily limit ${self.budget.daily_limit}")
        
        # Check monthly limit
        if self.budget.current_monthly_spend + estimated_cost > self.budget.monthly_limit:
            return (False, f"Cost would exceed monthly limit ${self.budget.monthly_limit}")
        
        return (True, None)
    
    def calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """
        Calculate cost for an AI operation.
        
        Args:
            model: Model name
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            
        Returns:
            Cost in USD
        """
        try:
            model_enum = AIModel(model)
            costs = MODEL_COSTS[model_enum]
            
            input_cost = (prompt_tokens / 1_000_000) * costs["input"]
            output_cost = (completion_tokens / 1_000_000) * costs["output"]
            
            return input_cost + output_cost
        except (KeyError, ValueError):
            self.logger.warning(f"Unknown model for cost calculation: {model}")
            return 0.0
    
    def optimize_prompt(
        self,
        prompt: str,
        max_length: Optional[int] = None
    ) -> str:
        """
        Optimize prompt to reduce token usage while maintaining quality.
        
        Args:
            prompt: Original prompt
            max_length: Maximum prompt length (characters)
            
        Returns:
            Optimized prompt
        """
        optimized = prompt
        
        # Remove excessive whitespace
        import re
        optimized = re.sub(r'\n{3,}', '\n\n', optimized)
        optimized = re.sub(r' {2,}', ' ', optimized)
        
        # Truncate if needed
        if max_length and len(optimized) > max_length:
            optimized = optimized[:max_length].rsplit(' ', 1)[0] + "..."
        
        return optimized
    
    def record_cost(
        self,
        cost: float
    ) -> None:
        """
        Record cost for budget tracking.
        
        Args:
            cost: Cost to record
        """
        self.budget.current_daily_spend += cost
        self.budget.current_monthly_spend += cost
        
        self.logger.info(
            f"Cost recorded: ${cost:.4f} "
            f"(Daily: ${self.budget.current_daily_spend:.2f}, "
            f"Monthly: ${self.budget.current_monthly_spend:.2f})"
        )

