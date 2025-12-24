"""create published sites tables

Revision ID: 20250301_create_published_sites_tables
Revises: 20250230_fix_alembic_version_column_length
Create Date: 2025-03-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250301_create_published_sites_tables'
down_revision: Union[str, None] = '20250230_fix_alembic_version_column_length'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create published_sites table
    op.create_table(
        'published_sites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('slug', sa.String(length=200), nullable=False),
        sa.Column('domain_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.String(length=100), nullable=False, server_default='default'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('meta_title', sa.String(length=70), nullable=True),
        sa.Column('meta_description', sa.String(length=160), nullable=True),
        sa.Column('meta_keywords', sa.String(length=300), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['domain_id'], ['domains.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
        sa.UniqueConstraint('domain_id')
    )
    op.create_index('ix_published_sites_domain', 'published_sites', ['domain_id'], unique=False)
    op.create_index('ix_published_sites_org_status', 'published_sites', ['organization_id', 'status'], unique=False)
    op.create_index(op.f('ix_published_sites_slug'), 'published_sites', ['slug'], unique=True)
    
    # Create site_categories table
    op.create_table(
        'site_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('site_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=20), nullable=False, server_default='#f97316'),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('meta_title', sa.String(length=70), nullable=True),
        sa.Column('meta_description', sa.String(length=160), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['site_id'], ['published_sites.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_site_categories_site_slug', 'site_categories', ['site_id', 'slug'], unique=False)
    op.create_index(op.f('ix_site_categories_slug'), 'site_categories', ['slug'], unique=False)
    
    # Create site_posts table
    op.create_table(
        'site_posts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('site_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('slug', sa.String(length=250), nullable=False),
        sa.Column('excerpt', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('featured_image', sa.String(length=500), nullable=True),
        sa.Column('featured_image_alt', sa.String(length=200), nullable=True),
        sa.Column('og_image', sa.String(length=500), nullable=True),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('author_name', sa.String(length=100), nullable=True),
        sa.Column('author_bio', sa.Text(), nullable=True),
        sa.Column('author_avatar', sa.String(length=500), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('is_featured', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('read_time_minutes', sa.Integer(), nullable=True),
        sa.Column('views_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('meta_title', sa.String(length=70), nullable=True),
        sa.Column('meta_description', sa.String(length=160), nullable=True),
        sa.Column('meta_keywords', sa.String(length=300), nullable=True),
        sa.Column('canonical_url', sa.String(length=500), nullable=True),
        sa.Column('no_index', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('schema_type', sa.String(length=50), nullable=False, server_default='Article'),
        sa.Column('twitter_title', sa.String(length=70), nullable=True),
        sa.Column('twitter_description', sa.String(length=200), nullable=True),
        sa.Column('twitter_image', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['category_id'], ['site_categories.id'], ),
        sa.ForeignKeyConstraint(['site_id'], ['published_sites.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_site_posts_featured_published', 'site_posts', ['is_featured', 'published_at'], unique=False)
    op.create_index('ix_site_posts_site_slug', 'site_posts', ['site_id', 'slug'], unique=False)
    op.create_index('ix_site_posts_status_published', 'site_posts', ['status', 'published_at'], unique=False)
    op.create_index(op.f('ix_site_posts_category_id'), 'site_posts', ['category_id'], unique=False)
    op.create_index(op.f('ix_site_posts_site_id'), 'site_posts', ['site_id'], unique=False)
    op.create_index(op.f('ix_site_posts_slug'), 'site_posts', ['slug'], unique=False)
    
    # Create site_pages table
    op.create_table(
        'site_pages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('site_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('slug', sa.String(length=250), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('is_homepage', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('meta_title', sa.String(length=70), nullable=True),
        sa.Column('meta_description', sa.String(length=160), nullable=True),
        sa.Column('meta_keywords', sa.String(length=300), nullable=True),
        sa.Column('no_index', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['site_id'], ['published_sites.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_site_pages_site_slug', 'site_pages', ['site_id', 'slug'], unique=False)
    op.create_index('ix_site_pages_status', 'site_pages', ['status'], unique=False)
    op.create_index(op.f('ix_site_pages_site_id'), 'site_pages', ['site_id'], unique=False)
    op.create_index(op.f('ix_site_pages_slug'), 'site_pages', ['slug'], unique=False)
    
    # Create site_menus table
    op.create_table(
        'site_menus',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('site_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('location', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['site_id'], ['published_sites.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_site_menus_site_location', 'site_menus', ['site_id', 'location'], unique=False)
    op.create_index(op.f('ix_site_menus_location'), 'site_menus', ['location'], unique=False)
    op.create_index(op.f('ix_site_menus_site_id'), 'site_menus', ['site_id'], unique=False)
    
    # Create site_menu_items table
    op.create_table(
        'site_menu_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('menu_id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('label', sa.String(length=100), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=True),
        sa.Column('type', sa.String(length=20), nullable=False, server_default='link'),
        sa.Column('target_id', sa.Integer(), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('css_class', sa.String(length=200), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['menu_id'], ['site_menus.id'], ),
        sa.ForeignKeyConstraint(['parent_id'], ['site_menu_items.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_site_menu_items_menu_order', 'site_menu_items', ['menu_id', 'sort_order'], unique=False)
    op.create_index('ix_site_menu_items_parent', 'site_menu_items', ['parent_id'], unique=False)
    op.create_index(op.f('ix_site_menu_items_menu_id'), 'site_menu_items', ['menu_id'], unique=False)
    
    # Create site_media table
    op.create_table(
        'site_media',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('site_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('alt_text', sa.String(length=200), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('caption', sa.Text(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False),
        sa.Column('uploaded_by_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['site_id'], ['published_sites.id'], ),
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_site_media_site_uploaded', 'site_media', ['site_id', 'uploaded_at'], unique=False)
    op.create_index(op.f('ix_site_media_site_id'), 'site_media', ['site_id'], unique=False)
    
    # Create site_branding table
    op.create_table(
        'site_branding',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('site_id', sa.Integer(), nullable=False),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('logo_alt', sa.String(length=200), nullable=True),
        sa.Column('favicon_url', sa.String(length=500), nullable=True),
        sa.Column('primary_color', sa.String(length=7), nullable=False, server_default='#f97316'),
        sa.Column('secondary_color', sa.String(length=7), nullable=True),
        sa.Column('accent_color', sa.String(length=7), nullable=True),
        sa.Column('background_color', sa.String(length=7), nullable=False, server_default='#ffffff'),
        sa.Column('text_color', sa.String(length=7), nullable=False, server_default='#1f2937'),
        sa.Column('font_family', sa.String(length=200), nullable=True),
        sa.Column('heading_font', sa.String(length=200), nullable=True),
        sa.Column('body_font', sa.String(length=200), nullable=True),
        sa.Column('custom_css', sa.Text(), nullable=True),
        sa.Column('theme_config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['site_id'], ['published_sites.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('site_id')
    )
    op.create_index(op.f('ix_site_branding_site_id'), 'site_branding', ['site_id'], unique=True)
    
    # Create site_settings table
    op.create_table(
        'site_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('site_id', sa.Integer(), nullable=False),
        sa.Column('site_description', sa.Text(), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=False, server_default='en'),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default='UTC'),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('contact_phone', sa.String(length=50), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('social_links', sa.JSON(), nullable=True),
        sa.Column('google_analytics_id', sa.String(length=50), nullable=True),
        sa.Column('google_tag_manager_id', sa.String(length=50), nullable=True),
        sa.Column('facebook_pixel_id', sa.String(length=50), nullable=True),
        sa.Column('robots_txt', sa.Text(), nullable=True),
        sa.Column('sitemap_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('comments_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('newsletter_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('search_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('header_code', sa.Text(), nullable=True),
        sa.Column('footer_code', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['site_id'], ['published_sites.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('site_id')
    )
    op.create_index(op.f('ix_site_settings_site_id'), 'site_settings', ['site_id'], unique=True)
    
    # Add site_id column to domains table (idempotent - check if exists first)
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    domains_columns = [col['name'] for col in inspector.get_columns('domains')]
    
    if 'site_id' not in domains_columns:
        op.add_column('domains', sa.Column('site_id', sa.Integer(), nullable=True))
        op.create_foreign_key('fk_domains_site', 'domains', 'published_sites', ['site_id'], ['id'])
        op.create_index(op.f('ix_domains_site_id'), 'domains', ['site_id'], unique=False)


def downgrade() -> None:
    # Drop site_id from domains
    op.drop_index(op.f('ix_domains_site_id'), table_name='domains')
    op.drop_constraint('fk_domains_site', 'domains', type_='foreignkey')
    op.drop_column('domains', 'site_id')
    
    # Drop site_settings table
    op.drop_index(op.f('ix_site_settings_site_id'), table_name='site_settings')
    op.drop_table('site_settings')
    
    # Drop site_branding table
    op.drop_index(op.f('ix_site_branding_site_id'), table_name='site_branding')
    op.drop_table('site_branding')
    
    # Drop site_media table
    op.drop_index(op.f('ix_site_media_site_id'), table_name='site_media')
    op.drop_index('ix_site_media_site_uploaded', table_name='site_media')
    op.drop_table('site_media')
    
    # Drop site_menu_items table
    op.drop_index(op.f('ix_site_menu_items_menu_id'), table_name='site_menu_items')
    op.drop_index('ix_site_menu_items_parent', table_name='site_menu_items')
    op.drop_index('ix_site_menu_items_menu_order', table_name='site_menu_items')
    op.drop_table('site_menu_items')
    
    # Drop site_menus table
    op.drop_index(op.f('ix_site_menus_site_id'), table_name='site_menus')
    op.drop_index(op.f('ix_site_menus_location'), table_name='site_menus')
    op.drop_index('ix_site_menus_site_location', table_name='site_menus')
    op.drop_table('site_menus')
    
    # Drop site_pages table
    op.drop_index(op.f('ix_site_pages_slug'), table_name='site_pages')
    op.drop_index(op.f('ix_site_pages_site_id'), table_name='site_pages')
    op.drop_index('ix_site_pages_status', table_name='site_pages')
    op.drop_index('ix_site_pages_site_slug', table_name='site_pages')
    op.drop_table('site_pages')
    
    # Drop site_posts table
    op.drop_index(op.f('ix_site_posts_slug'), table_name='site_posts')
    op.drop_index(op.f('ix_site_posts_site_id'), table_name='site_posts')
    op.drop_index(op.f('ix_site_posts_category_id'), table_name='site_posts')
    op.drop_index('ix_site_posts_status_published', table_name='site_posts')
    op.drop_index('ix_site_posts_site_slug', table_name='site_posts')
    op.drop_index('ix_site_posts_featured_published', table_name='site_posts')
    op.drop_table('site_posts')
    
    # Drop site_categories table
    op.drop_index(op.f('ix_site_categories_slug'), table_name='site_categories')
    op.drop_index('ix_site_categories_site_slug', table_name='site_categories')
    op.drop_table('site_categories')
    
    # Drop published_sites table
    op.drop_index(op.f('ix_published_sites_slug'), table_name='published_sites')
    op.drop_index('ix_published_sites_org_status', table_name='published_sites')
    op.drop_index('ix_published_sites_domain', table_name='published_sites')
    op.drop_table('published_sites')

