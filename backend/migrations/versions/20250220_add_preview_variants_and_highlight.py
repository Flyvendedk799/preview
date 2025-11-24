"""add preview variants and highlight image

Revision ID: 20250220_add_preview_variants_and_highlight
Revises: 20250219_add_organizations
Create Date: 2025-02-20 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250220_add_preview_variants_and_highlight'
down_revision: Union[str, None] = '20250219_add_organizations'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add highlight_image_url to previews table
    op.add_column('previews', sa.Column('highlight_image_url', sa.String(), nullable=True))
    
    # Create preview_variants table
    op.create_table(
        'preview_variants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('preview_id', sa.Integer(), nullable=False),
        sa.Column('variant_key', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('tone', sa.String(), nullable=True),
        sa.Column('keywords', sa.String(), nullable=True),
        sa.Column('image_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['preview_id'], ['previews.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_preview_variants_id'), 'preview_variants', ['id'], unique=False)
    op.create_index(op.f('ix_preview_variants_preview_id'), 'preview_variants', ['preview_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_preview_variants_preview_id'), table_name='preview_variants')
    op.drop_index(op.f('ix_preview_variants_id'), table_name='preview_variants')
    op.drop_table('preview_variants')
    op.drop_column('previews', 'highlight_image_url')

