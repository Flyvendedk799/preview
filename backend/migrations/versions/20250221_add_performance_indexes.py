"""add performance indexes

Revision ID: 20250221_add_performance_indexes
Revises: 20250220_add_preview_variants_and_highlight
Create Date: 2025-02-21 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250221_add_performance_indexes'
down_revision: Union[str, None] = '20250220_add_preview_variants_and_highlight'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add created_at index on previews (if not already exists)
    # Note: Some indexes may already exist from model definitions, but we ensure they're all present
    try:
        op.create_index('ix_previews_created_at', 'previews', ['created_at'], unique=False)
    except Exception:
        pass  # Index may already exist
    
    # Add composite index on previews (organization_id, created_at) for common queries
    try:
        op.create_index('ix_previews_org_created', 'previews', ['organization_id', 'created_at'], unique=False)
    except Exception:
        pass
    
    # Add composite index on analytics_events (organization_id, created_at)
    try:
        op.create_index('ix_analytics_events_org_created', 'analytics_events', ['organization_id', 'created_at'], unique=False)
    except Exception:
        pass
    
    # Add composite index on analytics_daily_aggregates (organization_id, date)
    try:
        op.create_index('ix_analytics_daily_org_date', 'analytics_daily_aggregates', ['organization_id', 'date'], unique=False)
    except Exception:
        pass
    
    # Add composite index on activity_logs (organization_id, created_at)
    try:
        op.create_index('ix_activity_logs_org_created', 'activity_logs', ['organization_id', 'created_at'], unique=False)
    except Exception:
        pass
    
    # Ensure preview_id index exists on preview_variants (should already exist, but ensure it)
    try:
        op.create_index('ix_preview_variants_preview_id', 'preview_variants', ['preview_id'], unique=False)
    except Exception:
        pass


def downgrade() -> None:
    op.drop_index('ix_preview_variants_preview_id', table_name='preview_variants')
    op.drop_index('ix_activity_logs_org_created', table_name='activity_logs')
    op.drop_index('ix_analytics_daily_org_date', table_name='analytics_daily_aggregates')
    op.drop_index('ix_analytics_events_org_created', table_name='analytics_events')
    op.drop_index('ix_previews_org_created', table_name='previews')
    op.drop_index('ix_previews_created_at', table_name='previews')

