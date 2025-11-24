"""create errors table

Revision ID: 20250216_create_errors_table
Revises: 20250216_add_is_admin_to_user
Create Date: 2025-02-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250216_create_errors_table'
down_revision: Union[str, None] = '20250216_add_is_admin_to_user'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create errors table
    op.create_table(
        'errors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_errors_timestamp'), 'errors', ['timestamp'], unique=False)
    op.create_index(op.f('ix_errors_source'), 'errors', ['source'], unique=False)


def downgrade() -> None:
    # Drop errors table
    op.drop_index(op.f('ix_errors_source'), table_name='errors')
    op.drop_index(op.f('ix_errors_timestamp'), table_name='errors')
    op.drop_table('errors')

