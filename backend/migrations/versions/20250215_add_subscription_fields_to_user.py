"""add subscription fields to user

Revision ID: 20250215_add_subscription_fields_to_user
Revises: 20250214_add_verification_fields_to_domain
Create Date: 2025-02-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250215_add_subscription_fields_to_user'
down_revision: Union[str, None] = '20250214_add_verification_fields_to_domain'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add subscription fields to users table
    op.add_column('users', sa.Column('stripe_customer_id', sa.String(), nullable=True))
    op.add_column('users', sa.Column('stripe_subscription_id', sa.String(), nullable=True))
    op.add_column('users', sa.Column('subscription_status', sa.String(), nullable=False, server_default='inactive'))
    op.add_column('users', sa.Column('subscription_plan', sa.String(), nullable=True))
    op.add_column('users', sa.Column('trial_ends_at', sa.DateTime(), nullable=True))
    # Create index on stripe_customer_id
    op.create_index(op.f('ix_users_stripe_customer_id'), 'users', ['stripe_customer_id'], unique=False)


def downgrade() -> None:
    # Remove subscription fields from users table
    op.drop_index(op.f('ix_users_stripe_customer_id'), table_name='users')
    op.drop_column('users', 'trial_ends_at')
    op.drop_column('users', 'subscription_plan')
    op.drop_column('users', 'subscription_status')
    op.drop_column('users', 'stripe_subscription_id')
    op.drop_column('users', 'stripe_customer_id')

