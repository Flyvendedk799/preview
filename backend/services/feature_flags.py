"""
Feature Flags - Gradual Rollout and A/B Testing Support

Manages feature flags for gradual rollout and A/B testing.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class FeatureStatus(str, Enum):
    """Feature status."""
    DISABLED = "disabled"
    ENABLED = "enabled"
    ROLLING_OUT = "rolling_out"  # Gradual rollout
    TESTING = "testing"  # A/B testing


@dataclass
class FeatureFlag:
    """Feature flag configuration."""
    name: str
    status: FeatureStatus
    rollout_percentage: float = 0.0  # 0-100, for gradual rollout
    enabled_for_users: list = field(default_factory=list)  # Specific user IDs
    enabled_for_domains: list = field(default_factory=list)  # Specific domains
    metadata: Dict[str, Any] = field(default_factory=dict)


class FeatureFlagManager:
    """
    Manages feature flags for gradual rollout and A/B testing.
    """
    
    def __init__(self):
        """Initialize feature flag manager."""
        self.flags: Dict[str, FeatureFlag] = {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize default flags
        self._setup_default_flags()
    
    def _setup_default_flags(self):
        """Setup default feature flags."""
        # Multi-agent system flag
        self.flags["multi_agent_system"] = FeatureFlag(
            name="multi_agent_system",
            status=FeatureStatus.ENABLED,
            rollout_percentage=100.0
        )
        
        # Quality orchestrator flag
        self.flags["quality_orchestrator"] = FeatureFlag(
            name="quality_orchestrator",
            status=FeatureStatus.ENABLED,
            rollout_percentage=100.0
        )
        
        # Enhanced Design DNA flag
        self.flags["enhanced_design_dna"] = FeatureFlag(
            name="enhanced_design_dna",
            status=FeatureStatus.ENABLED,
            rollout_percentage=100.0
        )
        
        # Cost optimization flag
        self.flags["cost_optimization"] = FeatureFlag(
            name="cost_optimization",
            status=FeatureStatus.ENABLED,
            rollout_percentage=100.0
        )
    
    def is_enabled(
        self,
        flag_name: str,
        user_id: Optional[int] = None,
        domain: Optional[str] = None
    ) -> bool:
        """
        Check if a feature flag is enabled.
        
        Args:
            flag_name: Feature flag name
            user_id: Optional user ID for user-specific flags
            domain: Optional domain for domain-specific flags
            
        Returns:
            True if feature is enabled
        """
        if flag_name not in self.flags:
            self.logger.warning(f"Unknown feature flag: {flag_name}")
            return False
        
        flag = self.flags[flag_name]
        
        # Check status
        if flag.status == FeatureStatus.DISABLED:
            return False
        
        if flag.status == FeatureStatus.ENABLED:
            return True
        
        # Check user-specific enablement
        if user_id and user_id in flag.enabled_for_users:
            return True
        
        # Check domain-specific enablement
        if domain and domain in flag.enabled_for_domains:
            return True
        
        # Check rollout percentage
        if flag.status == FeatureStatus.ROLLING_OUT:
            # Simple hash-based rollout (deterministic per user/domain)
            import hashlib
            identifier = f"{user_id or domain or 'default'}"
            hash_value = int(hashlib.md5(identifier.encode()).hexdigest(), 16)
            percentage = (hash_value % 100) + 1
            return percentage <= flag.rollout_percentage
        
        # Testing status - check A/B test assignment
        if flag.status == FeatureStatus.TESTING:
            # Would check A/B test assignment here
            return False
        
        return False
    
    def enable_feature(
        self,
        flag_name: str,
        rollout_percentage: float = 100.0
    ) -> None:
        """
        Enable a feature flag.
        
        Args:
            flag_name: Feature flag name
            rollout_percentage: Rollout percentage (0-100)
        """
        if flag_name not in self.flags:
            self.flags[flag_name] = FeatureFlag(
                name=flag_name,
                status=FeatureStatus.ENABLED if rollout_percentage >= 100 else FeatureStatus.ROLLING_OUT,
                rollout_percentage=rollout_percentage
            )
        else:
            flag = self.flags[flag_name]
            flag.status = FeatureStatus.ENABLED if rollout_percentage >= 100 else FeatureStatus.ROLLING_OUT
            flag.rollout_percentage = rollout_percentage
        
        self.logger.info(f"Enabled feature flag: {flag_name} ({rollout_percentage}%)")
    
    def disable_feature(
        self,
        flag_name: str
    ) -> None:
        """
        Disable a feature flag.
        
        Args:
            flag_name: Feature flag name
        """
        if flag_name in self.flags:
            self.flags[flag_name].status = FeatureStatus.DISABLED
            self.logger.info(f"Disabled feature flag: {flag_name}")

