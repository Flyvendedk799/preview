"""
Migration Manager - Handles System Migrations and Rollbacks

Manages migrations between system versions with:
- Feature flags
- Shadow mode
- Canary deployments
- Rollback mechanism
- Dual mode support
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from backend.services.feature_flags import FeatureFlagManager

logger = logging.getLogger(__name__)


class MigrationStatus(str, Enum):
    """Migration status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"


@dataclass
class MigrationConfig:
    """Migration configuration."""
    migration_id: str
    from_version: str
    to_version: str
    status: MigrationStatus = MigrationStatus.NOT_STARTED
    canary_percentage: float = 0.0  # 0-100
    shadow_mode: bool = False
    dual_mode: bool = False
    rollback_threshold: float = 0.10  # Rollback if error rate > 10%
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class MigrationManager:
    """
    Manages system migrations and rollbacks.
    """
    
    def __init__(self, feature_flags: Optional[FeatureFlagManager] = None):
        """
        Initialize migration manager.
        
        Args:
            feature_flags: Feature flag manager instance
        """
        self.feature_flags = feature_flags or FeatureFlagManager()
        self.migrations: Dict[str, MigrationConfig] = {}
        self.logger = logging.getLogger(__name__)
    
    def start_migration(
        self,
        migration_id: str,
        from_version: str,
        to_version: str,
        canary_percentage: float = 10.0,
        shadow_mode: bool = True
    ) -> MigrationConfig:
        """
        Start a migration.
        
        Args:
            migration_id: Migration identifier
            from_version: Current version
            to_version: Target version
            canary_percentage: Canary deployment percentage
            shadow_mode: Whether to run in shadow mode first
            
        Returns:
            MigrationConfig
        """
        migration = MigrationConfig(
            migration_id=migration_id,
            from_version=from_version,
            to_version=to_version,
            status=MigrationStatus.IN_PROGRESS,
            canary_percentage=canary_percentage,
            shadow_mode=shadow_mode,
            dual_mode=True,  # Always support both during migration
            started_at=datetime.utcnow()
        )
        
        self.migrations[migration_id] = migration
        
        self.logger.info(
            f"Started migration: {migration_id} "
            f"({from_version} -> {to_version}), "
            f"canary: {canary_percentage}%, "
            f"shadow: {shadow_mode}"
        )
        
        return migration
    
    def should_use_new_system(
        self,
        migration_id: str,
        user_id: Optional[int] = None,
        domain: Optional[str] = None
    ) -> bool:
        """
        Determine if new system should be used for a request.
        
        Args:
            migration_id: Migration identifier
            user_id: User ID
            domain: Domain
            
        Returns:
            True if new system should be used
        """
        if migration_id not in self.migrations:
            return False
        
        migration = self.migrations[migration_id]
        
        if migration.status != MigrationStatus.IN_PROGRESS:
            return migration.status == MigrationStatus.COMPLETED
        
        # Check canary percentage
        import hashlib
        identifier = f"{user_id or domain or 'default'}"
        hash_value = int(hashlib.md5(identifier.encode()).hexdigest(), 16)
        percentage = (hash_value % 100) + 1
        
        return percentage <= migration.canary_percentage
    
    def record_result(
        self,
        migration_id: str,
        success: bool,
        error: Optional[str] = None
    ) -> None:
        """
        Record migration result for monitoring.
        
        Args:
            migration_id: Migration identifier
            success: Whether request succeeded
            error: Error message if failed
        """
        if migration_id not in self.migrations:
            return
        
        migration = self.migrations[migration_id]
        
        # Track results (simplified - would use proper metrics)
        if not hasattr(migration, 'results'):
            migration.results = {"success": 0, "failure": 0}
        
        if success:
            migration.results["success"] += 1
        else:
            migration.results["failure"] += 1
            if error:
                self.logger.warning(f"Migration {migration_id} error: {error}")
        
        # Check if rollback threshold exceeded
        total = migration.results["success"] + migration.results["failure"]
        if total > 0:
            error_rate = migration.results["failure"] / total
            if error_rate > migration.rollback_threshold:
                self.logger.error(
                    f"Migration {migration_id} error rate {error_rate:.2%} "
                    f"exceeds threshold {migration.rollback_threshold:.2%}, "
                    f"considering rollback"
                )
    
    def complete_migration(
        self,
        migration_id: str
    ) -> None:
        """
        Mark migration as completed.
        
        Args:
            migration_id: Migration identifier
        """
        if migration_id not in self.migrations:
            return
        
        migration = self.migrations[migration_id]
        migration.status = MigrationStatus.COMPLETED
        migration.completed_at = datetime.utcnow()
        
        self.logger.info(f"Completed migration: {migration_id}")
    
    def rollback_migration(
        self,
        migration_id: str
    ) -> None:
        """
        Rollback a migration.
        
        Args:
            migration_id: Migration identifier
        """
        if migration_id not in self.migrations:
            return
        
        migration = self.migrations[migration_id]
        migration.status = MigrationStatus.ROLLED_BACK
        
        self.logger.warning(f"Rolled back migration: {migration_id}")

