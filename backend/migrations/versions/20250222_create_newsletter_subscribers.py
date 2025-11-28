"""create newsletter subscribers table

Revision ID: 20250222_create_newsletter_subscribers
Revises: 20250221_add_preview_job_failures
Create Date: 2025-02-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250222_create_newsletter_subscribers'
down_revision: Union[str, None] = '20250221_add_preview_job_failures'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create newsletter_subscribers table
    op.create_table(
        'newsletter_subscribers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=False, server_default='demo'),
        sa.Column('subscribed_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('consent_given', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_newsletter_subscribers_email'), 'newsletter_subscribers', ['email'], unique=True)
    op.create_index(op.f('ix_newsletter_subscribers_id'), 'newsletter_subscribers', ['id'], unique=False)


def downgrade() -> None:
    # Drop newsletter_subscribers table
    op.drop_index(op.f('ix_newsletter_subscribers_id'), table_name='newsletter_subscribers')
    op.drop_index(op.f('ix_newsletter_subscribers_email'), table_name='newsletter_subscribers')
    op.drop_table('newsletter_subscribers')

