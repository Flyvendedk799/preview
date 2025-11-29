"""add description to preview

Revision ID: 20250201_add_desc
Revises: 20241123_01_add_user_id_columns
Create Date: 2025-02-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250201_add_desc'
down_revision: Union[str, None] = '20241123_01_add_user_id_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add description column to previews table (idempotent - check if exists first)
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('previews')]

    if 'description' not in columns:
        op.add_column('previews', sa.Column('description', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove description column from previews table
    op.drop_column('previews', 'description')

