"""
Prompt Tester - A/B Testing and Validation for AI Prompts

Tests prompt variations and tracks performance to determine optimal prompts.
"""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics

from backend.services.prompt_manager import PromptManager, PromptVersion

logger = logging.getLogger(__name__)


class TestStatus(str, Enum):
    """Test status."""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PromptTestResult:
    """Result from testing a prompt."""
    prompt_id: str
    version: str
    quality_score: float
    latency_ms: float
    cost: float
    success_rate: float
    test_count: int = 0
    errors: List[str] = field(default_factory=list)


@dataclass
class ABTestResult:
    """Result from A/B test."""
    test_id: str
    variant_a: PromptTestResult
    variant_b: PromptTestResult
    winner: Optional[str] = None  # "a" or "b" or None
    confidence: float = 0.0
    status: TestStatus = TestStatus.RUNNING


class PromptTester:
    """
    Tests prompt variations and tracks performance.
    
    Features:
    - A/B testing
    - Performance comparison
    - Statistical significance
    - Automatic winner selection
    """
    
    def __init__(self, prompt_manager: PromptManager):
        """
        Initialize prompt tester.
        
        Args:
            prompt_manager: Prompt manager instance
        """
        self.prompt_manager = prompt_manager
        self.logger = logging.getLogger(__name__)
        self.active_tests: Dict[str, ABTestResult] = {}
    
    def run_ab_test(
        self,
        test_id: str,
        prompt_id: str,
        variant_a_version: str,
        variant_b_version: str,
        test_cases: List[Dict[str, Any]],
        min_samples: int = 10
    ) -> ABTestResult:
        """
        Run A/B test between two prompt versions.
        
        Args:
            test_id: Test identifier
            prompt_id: Prompt identifier
            variant_a_version: Version A
            variant_b_version: Version B
            test_cases: Test cases to run
            min_samples: Minimum samples for statistical significance
            
        Returns:
            ABTestResult
        """
        self.logger.info(
            f"Starting A/B test: {test_id} "
            f"({variant_a_version} vs {variant_b_version})"
        )
        
        # Initialize test result
        ab_test = ABTestResult(
            test_id=test_id,
            variant_a=PromptTestResult(
                prompt_id=prompt_id,
                version=variant_a_version,
                quality_score=0.0,
                latency_ms=0.0,
                cost=0.0,
                success_rate=0.0
            ),
            variant_b=PromptTestResult(
                prompt_id=prompt_id,
                version=variant_b_version,
                quality_score=0.0,
                latency_ms=0.0,
                cost=0.0,
                success_rate=0.0
            ),
            status=TestStatus.RUNNING
        )
        
        self.active_tests[test_id] = ab_test
        
        # Run tests
        variant_a_results = []
        variant_b_results = []
        
        for test_case in test_cases[:min_samples]:
            # Test variant A
            try:
                result_a = self._test_prompt_version(
                    prompt_id,
                    variant_a_version,
                    test_case
                )
                variant_a_results.append(result_a)
            except Exception as e:
                self.logger.error(f"Variant A test failed: {e}")
                ab_test.variant_a.errors.append(str(e))
            
            # Test variant B
            try:
                result_b = self._test_prompt_version(
                    prompt_id,
                    variant_b_version,
                    test_case
                )
                variant_b_results.append(result_b)
            except Exception as e:
                self.logger.error(f"Variant B test failed: {e}")
                ab_test.variant_b.errors.append(str(e))
        
        # Calculate aggregate metrics
        if variant_a_results:
            ab_test.variant_a.quality_score = statistics.mean([r.get("quality", 0.0) for r in variant_a_results])
            ab_test.variant_a.latency_ms = statistics.mean([r.get("latency_ms", 0.0) for r in variant_a_results])
            ab_test.variant_a.cost = sum([r.get("cost", 0.0) for r in variant_a_results])
            ab_test.variant_a.success_rate = len([r for r in variant_a_results if r.get("success", False)]) / len(variant_a_results)
            ab_test.variant_a.test_count = len(variant_a_results)
        
        if variant_b_results:
            ab_test.variant_b.quality_score = statistics.mean([r.get("quality", 0.0) for r in variant_b_results])
            ab_test.variant_b.latency_ms = statistics.mean([r.get("latency_ms", 0.0) for r in variant_b_results])
            ab_test.variant_b.cost = sum([r.get("cost", 0.0) for r in variant_b_results])
            ab_test.variant_b.success_rate = len([r for r in variant_b_results if r.get("success", False)]) / len(variant_b_results)
            ab_test.variant_b.test_count = len(variant_b_results)
        
        # Determine winner
        if variant_a_results and variant_b_results:
            # Compare quality scores
            quality_diff = ab_test.variant_a.quality_score - ab_test.variant_b.quality_score
            
            # Calculate confidence (simplified - would use proper statistical test)
            if abs(quality_diff) > 0.05:  # 5% difference threshold
                ab_test.winner = "a" if quality_diff > 0 else "b"
                ab_test.confidence = min(abs(quality_diff) * 10, 1.0)  # Simplified confidence
            else:
                # No clear winner
                ab_test.winner = None
                ab_test.confidence = 0.0
        
        ab_test.status = TestStatus.COMPLETED
        
        self.logger.info(
            f"A/B test complete: {test_id}, "
            f"winner: {ab_test.winner}, "
            f"confidence: {ab_test.confidence:.2f}"
        )
        
        return ab_test
    
    def _test_prompt_version(
        self,
        prompt_id: str,
        version: str,
        test_case: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Test a prompt version with a test case.
        
        Args:
            prompt_id: Prompt identifier
            version: Version to test
            test_case: Test case data
            
        Returns:
            Test result dictionary
        """
        # This is a placeholder - real implementation would:
        # 1. Get prompt content
        # 2. Substitute variables
        # 3. Call AI API
        # 4. Measure quality, latency, cost
        # 5. Return metrics
        
        start_time = time.time()
        
        # Placeholder implementation
        prompt_content = self.prompt_manager.get_prompt(
            prompt_id,
            version,
            test_case.get("variables", {})
        )
        
        # Simulate API call
        time.sleep(0.1)  # Simulate latency
        
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            "success": True,
            "quality": 0.8,  # Placeholder
            "latency_ms": latency_ms,
            "cost": 0.001  # Placeholder
        }
    
    def is_statistically_significant(
        self,
        variant_a_scores: List[float],
        variant_b_scores: List[float],
        confidence_level: float = 0.95
    ) -> Tuple[bool, float]:
        """
        Check if A/B test results are statistically significant.
        
        Args:
            variant_a_scores: Scores for variant A
            variant_b_scores: Scores for variant B
            confidence_level: Confidence level (0.95 = 95%)
            
        Returns:
            Tuple of (is_significant, p_value)
        """
        # Simplified statistical test
        # Real implementation would use proper t-test or similar
        
        if len(variant_a_scores) < 10 or len(variant_b_scores) < 10:
            return (False, 1.0)
        
        mean_a = statistics.mean(variant_a_scores)
        mean_b = statistics.mean(variant_b_scores)
        
        # Simple difference test
        diff = abs(mean_a - mean_b)
        std_a = statistics.stdev(variant_a_scores) if len(variant_a_scores) > 1 else 0
        std_b = statistics.stdev(variant_b_scores) if len(variant_b_scores) > 1 else 0
        
        # Simplified p-value calculation
        pooled_std = ((std_a ** 2 + std_b ** 2) / 2) ** 0.5
        if pooled_std == 0:
            return (False, 1.0)
        
        # Z-score approximation
        z_score = diff / (pooled_std / (len(variant_a_scores) ** 0.5))
        
        # Simplified p-value (would use proper statistical distribution)
        p_value = max(0.0, 1.0 - abs(z_score) / 3.0)
        
        is_significant = p_value < (1 - confidence_level)
        
        return (is_significant, p_value)

