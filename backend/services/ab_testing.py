"""
A/B Testing Framework - Experiment Tracking and Analysis

Manages A/B tests with:
- Experiment tracking
- Statistical significance
- Automatic winner selection
- Multi-variant testing
"""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import statistics
import uuid

logger = logging.getLogger(__name__)


class ExperimentStatus(str, Enum):
    """Experiment status."""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class Variant:
    """Test variant."""
    variant_id: str
    name: str
    config: Dict[str, Any]
    traffic_percentage: float = 50.0  # 0-100


@dataclass
class ExperimentResult:
    """Result for a variant."""
    variant_id: str
    samples: int = 0
    conversions: int = 0
    conversion_rate: float = 0.0
    quality_score: float = 0.0
    latency_ms: float = 0.0
    cost: float = 0.0
    errors: int = 0
    error_rate: float = 0.0


@dataclass
class Experiment:
    """A/B test experiment."""
    experiment_id: str
    name: str
    variants: List[Variant]
    status: ExperimentStatus = ExperimentStatus.DRAFT
    min_samples: int = 100
    confidence_level: float = 0.95
    created_at: datetime = field(default_factory=datetime.utcnow)
    results: Dict[str, ExperimentResult] = field(default_factory=dict)
    winner: Optional[str] = None
    is_significant: bool = False


class ABTestingFramework:
    """
    A/B testing framework for preview generation.
    
    Features:
    - Experiment tracking
    - Statistical significance
    - Automatic winner selection
    - Multi-variant testing
    """
    
    def __init__(self):
        """Initialize A/B testing framework."""
        self.experiments: Dict[str, Experiment] = {}
        self.logger = logging.getLogger(__name__)
    
    def create_experiment(
        self,
        name: str,
        variants: List[Dict[str, Any]],
        min_samples: int = 100,
        confidence_level: float = 0.95
    ) -> Experiment:
        """
        Create a new A/B test experiment.
        
        Args:
            name: Experiment name
            variants: List of variant configurations
            min_samples: Minimum samples per variant
            confidence_level: Confidence level (0.95 = 95%)
            
        Returns:
            Created Experiment
        """
        experiment_id = str(uuid.uuid4())
        
        variant_objects = []
        traffic_per_variant = 100.0 / len(variants)
        
        for i, variant_config in enumerate(variants):
            variant = Variant(
                variant_id=f"variant_{i+1}",
                name=variant_config.get("name", f"Variant {i+1}"),
                config=variant_config.get("config", {}),
                traffic_percentage=traffic_per_variant
            )
            variant_objects.append(variant)
        
        experiment = Experiment(
            experiment_id=experiment_id,
            name=name,
            variants=variant_objects,
            min_samples=min_samples,
            confidence_level=confidence_level
        )
        
        self.experiments[experiment_id] = experiment
        
        self.logger.info(
            f"Created experiment: {name} ({experiment_id}), "
            f"{len(variants)} variants, "
            f"min_samples: {min_samples}"
        )
        
        return experiment
    
    def assign_variant(
        self,
        experiment_id: str,
        user_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Assign a variant to a user/request.
        
        Args:
            experiment_id: Experiment identifier
            user_id: User/request identifier
            
        Returns:
            Variant ID or None if experiment not active
        """
        if experiment_id not in self.experiments:
            return None
        
        experiment = self.experiments[experiment_id]
        
        if experiment.status != ExperimentStatus.RUNNING:
            return None
        
        # Deterministic assignment based on user_id
        import hashlib
        identifier = user_id or str(time.time())
        hash_value = int(hashlib.md5(identifier.encode()).hexdigest(), 16)
        
        # Assign based on traffic percentage
        cumulative = 0.0
        for variant in experiment.variants:
            cumulative += variant.traffic_percentage
            if (hash_value % 100) < cumulative:
                return variant.variant_id
        
        # Fallback to first variant
        return experiment.variants[0].variant_id if experiment.variants else None
    
    def record_result(
        self,
        experiment_id: str,
        variant_id: str,
        success: bool,
        quality_score: Optional[float] = None,
        latency_ms: Optional[float] = None,
        cost: Optional[float] = None
    ) -> None:
        """
        Record a test result.
        
        Args:
            experiment_id: Experiment identifier
            variant_id: Variant identifier
            success: Whether request succeeded
            quality_score: Quality score
            latency_ms: Latency in milliseconds
            cost: Cost in USD
        """
        if experiment_id not in self.experiments:
            return
        
        experiment = self.experiments[experiment_id]
        
        if variant_id not in experiment.results:
            experiment.results[variant_id] = ExperimentResult(variant_id=variant_id)
        
        result = experiment.results[variant_id]
        result.samples += 1
        
        if success:
            result.conversions += 1
        
        if quality_score is not None:
            # Update average quality score
            if result.samples == 1:
                result.quality_score = quality_score
            else:
                result.quality_score = (
                    (result.quality_score * (result.samples - 1) + quality_score) /
                    result.samples
                )
        
        if latency_ms is not None:
            if result.samples == 1:
                result.latency_ms = latency_ms
            else:
                result.latency_ms = (
                    (result.latency_ms * (result.samples - 1) + latency_ms) /
                    result.samples
                )
        
        if cost is not None:
            result.cost += cost
        
        result.conversion_rate = result.conversions / result.samples if result.samples > 0 else 0.0
        result.error_rate = (result.samples - result.conversions) / result.samples if result.samples > 0 else 0.0
        
        # Check if experiment is complete
        if all(result.samples >= experiment.min_samples for result in experiment.results.values()):
            self._analyze_experiment(experiment)
    
    def _analyze_experiment(
        self,
        experiment: Experiment
    ) -> None:
        """
        Analyze experiment results and determine winner.
        
        Args:
            experiment: Experiment to analyze
        """
        if len(experiment.results) < 2:
            return
        
        results = list(experiment.results.values())
        
        # Compare conversion rates
        conversion_rates = [r.conversion_rate for r in results]
        quality_scores = [r.quality_score for r in results]
        
        # Determine winner based on conversion rate and quality
        best_variant = max(results, key=lambda r: r.conversion_rate * 0.7 + r.quality_score * 0.3)
        
        # Check statistical significance (simplified)
        if len(conversion_rates) >= 2:
            mean_diff = abs(conversion_rates[0] - conversion_rates[1])
            pooled_std = statistics.stdev(conversion_rates) if len(conversion_rates) > 1 else 0
            
            if pooled_std > 0:
                z_score = mean_diff / (pooled_std / (len(results[0].samples) ** 0.5))
                p_value = max(0.0, 1.0 - abs(z_score) / 3.0)
                experiment.is_significant = p_value < (1 - experiment.confidence_level)
        
        experiment.winner = best_variant.variant_id
        experiment.status = ExperimentStatus.COMPLETED
        
        self.logger.info(
            f"Experiment {experiment.experiment_id} completed: "
            f"winner={experiment.winner}, "
            f"significant={experiment.is_significant}"
        )
    
    def get_experiment_results(
        self,
        experiment_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get experiment results.
        
        Args:
            experiment_id: Experiment identifier
            
        Returns:
            Results dictionary or None
        """
        if experiment_id not in self.experiments:
            return None
        
        experiment = self.experiments[experiment_id]
        
        return {
            "experiment_id": experiment.experiment_id,
            "name": experiment.name,
            "status": experiment.status.value,
            "variants": [
                {
                    "variant_id": v.variant_id,
                    "name": v.name,
                    "traffic_percentage": v.traffic_percentage,
                    "results": experiment.results.get(v.variant_id, {}).__dict__ if v.variant_id in experiment.results else {}
                }
                for v in experiment.variants
            ],
            "winner": experiment.winner,
            "is_significant": experiment.is_significant
        }

