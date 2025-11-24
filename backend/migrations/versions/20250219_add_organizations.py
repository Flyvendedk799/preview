"""add organizations and organization members

Revision ID: 20250219_add_organizations
Revises: 20250218_create_analytics_tables
Create Date: 2025-02-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250219_add_organizations'
down_revision: Union[str, None] = '20250218_create_analytics_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('owner_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('stripe_customer_id', sa.String(), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(), nullable=True),
        sa.Column('subscription_status', sa.String(), nullable=False, server_default='inactive'),
        sa.Column('subscription_plan', sa.String(), nullable=True),
        sa.Column('trial_ends_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['owner_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organizations_name'), 'organizations', ['name'], unique=False)
    op.create_index(op.f('ix_organizations_owner_user_id'), 'organizations', ['owner_user_id'], unique=False)
    op.create_index(op.f('ix_organizations_stripe_customer_id'), 'organizations', ['stripe_customer_id'], unique=False)
    
    # Create organization_members table
    op.create_table(
        'organization_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.Enum('owner', 'admin', 'editor', 'viewer', name='organizationrole'), nullable=False, server_default='viewer'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organization_members_organization_id'), 'organization_members', ['organization_id'], unique=False)
    op.create_index(op.f('ix_organization_members_user_id'), 'organization_members', ['user_id'], unique=False)
    
    # Add organization_id columns to existing tables
    op.add_column('domains', sa.Column('organization_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_domains_organization', 'domains', 'organizations', ['organization_id'], ['id'])
    op.create_index(op.f('ix_domains_organization_id'), 'domains', ['organization_id'], unique=False)
    
    op.add_column('previews', sa.Column('organization_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_previews_organization', 'previews', 'organizations', ['organization_id'], ['id'])
    op.create_index(op.f('ix_previews_organization_id'), 'previews', ['organization_id'], unique=False)
    
    op.add_column('brand_settings', sa.Column('organization_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_brand_settings_organization', 'brand_settings', 'organizations', ['organization_id'], ['id'])
    op.create_index(op.f('ix_brand_settings_organization_id'), 'brand_settings', ['organization_id'], unique=False)
    
    op.add_column('analytics_events', sa.Column('organization_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_analytics_events_organization', 'analytics_events', 'organizations', ['organization_id'], ['id'])
    op.create_index(op.f('ix_analytics_events_organization_id'), 'analytics_events', ['organization_id'], unique=False)
    
    op.add_column('analytics_daily_aggregates', sa.Column('organization_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_analytics_daily_aggregates_organization', 'analytics_daily_aggregates', 'organizations', ['organization_id'], ['id'])
    op.create_index(op.f('ix_analytics_daily_aggregates_organization_id'), 'analytics_daily_aggregates', ['organization_id'], unique=False)
    
    # Backfill: Create default organization for each existing user and migrate data
    # This is done via Python code in the migration
    from sqlalchemy import text
    
    # Create default organizations for all existing users
    op.execute(text("""
        INSERT INTO organizations (name, owner_user_id, created_at, stripe_customer_id, stripe_subscription_id, subscription_status, subscription_plan, trial_ends_at)
        SELECT 
            email || '''s Organization' as name,
            id as owner_user_id,
            created_at,
            stripe_customer_id,
            stripe_subscription_id,
            subscription_status,
            subscription_plan,
            trial_ends_at
        FROM users
    """))
    
    # Create organization memberships (owner role) for all users
    op.execute(text("""
        INSERT INTO organization_members (organization_id, user_id, role, created_at)
        SELECT id, owner_user_id, 'owner', created_at
        FROM organizations
    """))
    
    # Migrate domains to organizations
    op.execute(text("""
        UPDATE domains
        SET organization_id = (
            SELECT o.id
            FROM organizations o
            WHERE o.owner_user_id = domains.user_id
            LIMIT 1
        )
    """))
    
    # Migrate previews to organizations
    op.execute(text("""
        UPDATE previews
        SET organization_id = (
            SELECT o.id
            FROM organizations o
            WHERE o.owner_user_id = previews.user_id
            LIMIT 1
        )
    """))
    
    # Migrate brand_settings to organizations
    op.execute(text("""
        UPDATE brand_settings
        SET organization_id = (
            SELECT o.id
            FROM organizations o
            WHERE o.owner_user_id = brand_settings.user_id
            LIMIT 1
        )
    """))
    
    # Migrate analytics_events to organizations (via preview/domain)
    op.execute(text("""
        UPDATE analytics_events
        SET organization_id = (
            SELECT COALESCE(p.organization_id, d.organization_id)
            FROM analytics_events ae
            LEFT JOIN previews p ON ae.preview_id = p.id
            LEFT JOIN domains d ON ae.domain_id = d.id
            WHERE ae.id = analytics_events.id
            LIMIT 1
        )
    """))
    
    # Migrate analytics_daily_aggregates to organizations
    op.execute(text("""
        UPDATE analytics_daily_aggregates
        SET organization_id = (
            SELECT o.id
            FROM organizations o
            WHERE o.owner_user_id = analytics_daily_aggregates.user_id
            LIMIT 1
        )
    """))


def downgrade() -> None:
    # Drop organization_id columns
    op.drop_index(op.f('ix_analytics_daily_aggregates_organization_id'), table_name='analytics_daily_aggregates')
    op.drop_constraint('fk_analytics_daily_aggregates_organization', 'analytics_daily_aggregates', type_='foreignkey')
    op.drop_column('analytics_daily_aggregates', 'organization_id')
    
    op.drop_index(op.f('ix_analytics_events_organization_id'), table_name='analytics_events')
    op.drop_constraint('fk_analytics_events_organization', 'analytics_events', type_='foreignkey')
    op.drop_column('analytics_events', 'organization_id')
    
    op.drop_index(op.f('ix_brand_settings_organization_id'), table_name='brand_settings')
    op.drop_constraint('fk_brand_settings_organization', 'brand_settings', type_='foreignkey')
    op.drop_column('brand_settings', 'organization_id')
    
    op.drop_index(op.f('ix_previews_organization_id'), table_name='previews')
    op.drop_constraint('fk_previews_organization', 'previews', type_='foreignkey')
    op.drop_column('previews', 'organization_id')
    
    op.drop_index(op.f('ix_domains_organization_id'), table_name='domains')
    op.drop_constraint('fk_domains_organization', 'domains', type_='foreignkey')
    op.drop_column('domains', 'organization_id')
    
    # Drop organization_members table
    op.drop_index(op.f('ix_organization_members_user_id'), table_name='organization_members')
    op.drop_index(op.f('ix_organization_members_organization_id'), table_name='organization_members')
    op.drop_table('organization_members')
    
    # Drop organizations table
    op.drop_index(op.f('ix_organizations_stripe_customer_id'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_owner_user_id'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_name'), table_name='organizations')
    op.drop_table('organizations')
    
    # Drop enum type
    op.execute('DROP TYPE IF EXISTS organizationrole')

