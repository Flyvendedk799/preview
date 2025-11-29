"""add composited image to preview

Revision ID: 20250229_add_composited_image_to_preview
Revises: 20250222_create_newsletter_subscribers
Create Date: 2025-02-29 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250229_add_composited_image_to_preview'
down_revision: Union[str, None] = '20250222_create_newsletter_subscribers'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add composited_image_url to previews table
    # This stores the designed UI card image (screenshot + typography overlay)
    op.add_column('previews', sa.Column('composited_image_url', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove composited_image_url column from previews table
    op.drop_column('previews', 'composited_image_url')

