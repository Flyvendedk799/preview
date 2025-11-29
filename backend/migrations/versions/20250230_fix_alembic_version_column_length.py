"""fix alembic_version column length

Revision ID: 20250230_fix_alembic_version_column_length
Revises: 20250229_add_composited_image_to_preview
Create Date: 2025-02-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250230_fix_alembic_version_column_length'
down_revision: Union[str, None] = '20250229_add_composited_image_to_preview'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Fix alembic_version table: increase version_num column length from VARCHAR(32) to VARCHAR(255)
    # This is needed because some revision IDs are longer than 32 characters
    # Check if column exists and alter it
    from sqlalchemy import inspect, text
    
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Check if alembic_version table exists
    if 'alembic_version' in inspector.get_table_names():
        # Get current column info
        columns = inspector.get_columns('alembic_version')
        version_num_col = next((col for col in columns if col['name'] == 'version_num'), None)
        
        if version_num_col:
            # Check current type length - handle different SQLAlchemy type representations
            col_type = version_num_col['type']
            current_length = None
            
            # Try to get length from type
            if hasattr(col_type, 'length'):
                current_length = col_type.length
            elif hasattr(col_type, 'args') and len(col_type.args) > 0:
                # Some types store length in args
                if isinstance(col_type.args[0], int):
                    current_length = col_type.args[0]
            
            # Also check string representation
            type_str = str(col_type)
            
            # If it's VARCHAR(32) or similar, alter it to VARCHAR(255)
            if current_length == 32 or (current_length is None and '32' in type_str):
                # Use raw SQL to alter the column - works for PostgreSQL
                op.execute(text("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(255)"))


def downgrade() -> None:
    # Revert to VARCHAR(32) - but this might fail if there are long revision IDs
    # We'll use VARCHAR(100) as a compromise
    from sqlalchemy import text
    op.execute(text("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(100)"))

