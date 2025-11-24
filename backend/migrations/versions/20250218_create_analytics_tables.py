"""create analytics tables

Revision ID: 20250218_create_analytics_tables
Revises: 20250217_create_activity_logs_table
Create Date: 2025-02-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250218_create_analytics_tables'
down_revision: Union[str, None] = '20250217_create_activity_logs_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create analytics_events table
    op.create_table(
        'analytics_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('domain_id', sa.Integer(), nullable=True),
        sa.Column('preview_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('referrer', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['domain_id'], ['domains.id'], ),
        sa.ForeignKeyConstraint(['preview_id'], ['previews.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analytics_events_user_id'), 'analytics_events', ['user_id'], unique=False)
    op.create_index(op.f('ix_analytics_events_domain_id'), 'analytics_events', ['domain_id'], unique=False)
    op.create_index(op.f('ix_analytics_events_preview_id'), 'analytics_events', ['preview_id'], unique=False)
    op.create_index(op.f('ix_analytics_events_event_type'), 'analytics_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_analytics_events_created_at'), 'analytics_events', ['created_at'], unique=False)
    
    # Create analytics_daily_aggregates table
    op.create_table(
        'analytics_daily_aggregates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('domain_id', sa.Integer(), nullable=True),
        sa.Column('preview_id', sa.Integer(), nullable=True),
        sa.Column('impressions', sa.Integer(), nullable=False),
        sa.Column('clicks', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['domain_id'], ['domains.id'], ),
        sa.ForeignKeyConstraint(['preview_id'], ['previews.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date', 'user_id', 'domain_id', 'preview_id', name='uq_daily_aggregate')
    )
    op.create_index(op.f('ix_analytics_daily_aggregates_date'), 'analytics_daily_aggregates', ['date'], unique=False)
    op.create_index(op.f('ix_analytics_daily_aggregates_user_id'), 'analytics_daily_aggregates', ['user_id'], unique=False)
    op.create_index(op.f('ix_analytics_daily_aggregates_domain_id'), 'analytics_daily_aggregates', ['domain_id'], unique=False)
    op.create_index(op.f('ix_analytics_daily_aggregates_preview_id'), 'analytics_daily_aggregates', ['preview_id'], unique=False)


def downgrade() -> None:
    # Drop analytics_daily_aggregates table
    op.drop_index(op.f('ix_analytics_daily_aggregates_preview_id'), table_name='analytics_daily_aggregates')
    op.drop_index(op.f('ix_analytics_daily_aggregates_domain_id'), table_name='analytics_daily_aggregates')
    op.drop_index(op.f('ix_analytics_daily_aggregates_user_id'), table_name='analytics_daily_aggregates')
    op.drop_index(op.f('ix_analytics_daily_aggregates_date'), table_name='analytics_daily_aggregates')
    op.drop_table('analytics_daily_aggregates')
    
    # Drop analytics_events table
    op.drop_index(op.f('ix_analytics_events_created_at'), table_name='analytics_events')
    op.drop_index(op.f('ix_analytics_events_event_type'), table_name='analytics_events')
    op.drop_index(op.f('ix_analytics_events_preview_id'), table_name='analytics_events')
    op.drop_index(op.f('ix_analytics_events_domain_id'), table_name='analytics_events')
    op.drop_index(op.f('ix_analytics_events_user_id'), table_name='analytics_events')
    op.drop_table('analytics_events')

