"""add metadata fields to preview

Revision ID: 20250213_add_metadata_fields_to_preview
Revises: 20250201_add_desc
Create Date: 2025-02-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250213_add_metadata_fields_to_preview'
down_revision: Union[str, None] = '20250201_add_desc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new metadata fields to previews table
    op.add_column('previews', sa.Column('keywords', sa.String(), nullable=True))
    op.add_column('previews', sa.Column('tone', sa.String(), nullable=True))
    op.add_column('previews', sa.Column('ai_reasoning', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove metadata fields from previews table
    op.drop_column('previews', 'ai_reasoning')
    op.drop_column('previews', 'tone')
    op.drop_column('previews', 'keywords')

