"""add verification fields to domain

Revision ID: 20250214_add_verification_fields_to_domain
Revises: 20250213_add_metadata_fields_to_preview
Create Date: 2025-02-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250214_add_verification_fields_to_domain'
down_revision: Union[str, None] = '20250213_add_metadata_fields_to_preview'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add verification fields to domains table
    op.add_column('domains', sa.Column('verification_method', sa.String(), nullable=True))
    op.add_column('domains', sa.Column('verification_token', sa.String(), nullable=True))
    op.add_column('domains', sa.Column('verified_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove verification fields from domains table
    op.drop_column('domains', 'verified_at')
    op.drop_column('domains', 'verification_token')
    op.drop_column('domains', 'verification_method')

