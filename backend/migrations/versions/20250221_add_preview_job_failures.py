"""add preview job failures table

Revision ID: 20250221_add_preview_job_failures
Revises: 20250221_add_performance_indexes
Create Date: 2025-02-21 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250221_add_preview_job_failures'
down_revision: Union[str, None] = '20250221_add_performance_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'preview_job_failures',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.String(), nullable=True),
        sa.Column('preview_id', sa.Integer(), nullable=True),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('stacktrace', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['preview_id'], ['previews.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_preview_job_failures_id'), 'preview_job_failures', ['id'], unique=False)
    op.create_index(op.f('ix_preview_job_failures_job_id'), 'preview_job_failures', ['job_id'], unique=False)
    op.create_index(op.f('ix_preview_job_failures_preview_id'), 'preview_job_failures', ['preview_id'], unique=False)
    op.create_index(op.f('ix_preview_job_failures_organization_id'), 'preview_job_failures', ['organization_id'], unique=False)
    op.create_index(op.f('ix_preview_job_failures_created_at'), 'preview_job_failures', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_preview_job_failures_created_at'), table_name='preview_job_failures')
    op.drop_index(op.f('ix_preview_job_failures_organization_id'), table_name='preview_job_failures')
    op.drop_index(op.f('ix_preview_job_failures_preview_id'), table_name='preview_job_failures')
    op.drop_index(op.f('ix_preview_job_failures_job_id'), table_name='preview_job_failures')
    op.drop_index(op.f('ix_preview_job_failures_id'), table_name='preview_job_failures')
    op.drop_table('preview_job_failures')

