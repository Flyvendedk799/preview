"""add user_id columns

Revision ID: 20241123_01_add_user_id_columns
Revises: 
Create Date: 2024-11-23 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '20241123_01_add_user_id_columns'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    if not table_exists(table_name):
        return False
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    # Create users table if it doesn't exist
    if not table_exists('users'):
        op.create_table(
            'users',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('email', sa.String(), nullable=False),
            sa.Column('hashed_password', sa.String(), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_users_id', 'users', ['id'])
        op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Create domains table if it doesn't exist, otherwise add user_id column
    if not table_exists('domains'):
        op.create_table(
            'domains',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('environment', sa.String(), nullable=False),
            sa.Column('status', sa.String(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('monthly_clicks', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_domains_user_id_users'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_domains_id', 'domains', ['id'])
        op.create_index('ix_domains_name', 'domains', ['name'], unique=True)
        op.create_index('ix_domains_user_id', 'domains', ['user_id'])
    else:
        # Table exists, add user_id column if it doesn't exist
        if not column_exists('domains', 'user_id'):
            op.add_column('domains', sa.Column('user_id', sa.Integer(), nullable=True))
            op.create_index('ix_domains_user_id', 'domains', ['user_id'])
            op.create_foreign_key(
                'fk_domains_user_id_users',
                'domains', 'users',
                ['user_id'], ['id']
            )

    # Create brand_settings table if it doesn't exist, otherwise add user_id column
    if not table_exists('brand_settings'):
        op.create_table(
            'brand_settings',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('primary_color', sa.String(), nullable=False),
            sa.Column('secondary_color', sa.String(), nullable=False),
            sa.Column('accent_color', sa.String(), nullable=False),
            sa.Column('font_family', sa.String(), nullable=False),
            sa.Column('logo_url', sa.String(), nullable=True),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_brand_settings_user_id_users'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_brand_settings_id', 'brand_settings', ['id'])
        op.create_index('ix_brand_settings_user_id', 'brand_settings', ['user_id'])
    else:
        # Table exists, add user_id column if it doesn't exist
        if not column_exists('brand_settings', 'user_id'):
            op.add_column('brand_settings', sa.Column('user_id', sa.Integer(), nullable=True))
            op.create_index('ix_brand_settings_user_id', 'brand_settings', ['user_id'])
            op.create_foreign_key(
                'fk_brand_settings_user_id_users',
                'brand_settings', 'users',
                ['user_id'], ['id']
            )

    # Create previews table if it doesn't exist, otherwise add user_id column
    if not table_exists('previews'):
        op.create_table(
            'previews',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('url', sa.String(), nullable=False),
            sa.Column('domain', sa.String(), nullable=False),
            sa.Column('title', sa.String(), nullable=False),
            sa.Column('type', sa.String(), nullable=False),
            sa.Column('image_url', sa.String(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('monthly_clicks', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_previews_user_id_users'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_previews_id', 'previews', ['id'])
        op.create_index('ix_previews_domain', 'previews', ['domain'])
        op.create_index('ix_previews_type', 'previews', ['type'])
        op.create_index('ix_previews_user_id', 'previews', ['user_id'])
    else:
        # Table exists, add user_id column if it doesn't exist
        if not column_exists('previews', 'user_id'):
            op.add_column('previews', sa.Column('user_id', sa.Integer(), nullable=True))
            op.create_index('ix_previews_user_id', 'previews', ['user_id'])
            op.create_foreign_key(
                'fk_previews_user_id_users',
                'previews', 'users',
                ['user_id'], ['id']
            )


def downgrade() -> None:
    # Only downgrade if tables exist and columns exist
    if table_exists('previews') and column_exists('previews', 'user_id'):
        op.drop_constraint('fk_previews_user_id_users', 'previews', type_='foreignkey')
        op.drop_index('ix_previews_user_id', table_name='previews')
        op.drop_column('previews', 'user_id')

    if table_exists('brand_settings') and column_exists('brand_settings', 'user_id'):
        op.drop_constraint('fk_brand_settings_user_id_users', 'brand_settings', type_='foreignkey')
        op.drop_index('ix_brand_settings_user_id', table_name='brand_settings')
        op.drop_column('brand_settings', 'user_id')

    if table_exists('domains') and column_exists('domains', 'user_id'):
        op.drop_constraint('fk_domains_user_id_users', 'domains', type_='foreignkey')
        op.drop_index('ix_domains_user_id', table_name='domains')
        op.drop_column('domains', 'user_id')

