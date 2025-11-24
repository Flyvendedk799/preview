"""add is_admin field to user

Revision ID: 20250216_add_is_admin_to_user
Revises: 20250215_add_subscription_fields_to_user
Create Date: 2025-02-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250216_add_is_admin_to_user'
down_revision: Union[str, None] = '20250215_add_subscription_fields_to_user'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_admin column to users table
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='0'))


def downgrade() -> None:
    # Remove is_admin column from users table
    op.drop_column('users', 'is_admin')

