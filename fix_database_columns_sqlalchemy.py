#!/usr/bin/env python
"""
Alternative script to fix missing database columns using SQLAlchemy.
This version uses SQLAlchemy which is already in your dependencies.
Safe to run multiple times (idempotent).
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Run SQL commands to fix missing columns using SQLAlchemy."""
    from sqlalchemy import create_engine, text, inspect
    from backend.core.config import settings
    
    # Get database URL
    database_url = settings.DATABASE_URL
    
    if not database_url:
        print("ERROR: DATABASE_URL not found in settings")
        sys.exit(1)
    
    print("Connecting to database...")
    # Mask password in URL for display
    display_url = database_url
    if '@' in display_url:
        parts = display_url.split('@')
        if '://' in parts[0]:
            auth_part = parts[0].split('://')[1]
            if ':' in auth_part:
                user = auth_part.split(':')[0]
                display_url = display_url.replace(auth_part, f"{user}:***")
    
    print(f"Database: {display_url.split('@')[1] if '@' in display_url else 'local'}")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        inspector = inspect(engine)
        
        print("\n" + "="*60)
        print("Fixing missing database columns...")
        print("="*60 + "\n")
        
        with engine.connect() as conn:
            # Check and add composited_image_url to previews table
            print("1. Checking previews.composited_image_url...")
            columns = [col['name'] for col in inspector.get_columns('previews')]
            
            if 'composited_image_url' in columns:
                print("   [OK] Column composited_image_url already exists")
            else:
                print("   [+] Adding composited_image_url column...")
                conn.execute(text("ALTER TABLE previews ADD COLUMN composited_image_url VARCHAR"))
                conn.commit()
                print("   [OK] Column composited_image_url added successfully")
            
            # Check and add site_id to domains table
            print("\n2. Checking domains.site_id...")
            columns = [col['name'] for col in inspector.get_columns('domains')]
            
            if 'site_id' in columns:
                print("   [OK] Column site_id already exists")
            else:
                print("   [+] Adding site_id column...")
                conn.execute(text("ALTER TABLE domains ADD COLUMN site_id INTEGER"))
                conn.commit()
                print("   [OK] Column site_id added successfully")
                
                # Check if published_sites table exists
                tables = inspector.get_table_names()
                
                if 'published_sites' in tables:
                    # Check if foreign key constraint already exists
                    fks = inspector.get_foreign_keys('domains')
                    fk_exists = any(fk['name'] == 'fk_domains_site' for fk in fks)
                    
                    if not fk_exists:
                        print("   [+] Adding foreign key constraint...")
                        conn.execute(text("""
                            ALTER TABLE domains 
                            ADD CONSTRAINT fk_domains_site 
                            FOREIGN KEY (site_id) REFERENCES published_sites(id)
                        """))
                        conn.commit()
                        print("   [OK] Foreign key constraint added successfully")
                    else:
                        print("   [OK] Foreign key constraint already exists")
                else:
                    print("   [WARN] published_sites table doesn't exist yet, skipping foreign key")
                
                # Check if index exists
                indexes = inspector.get_indexes('domains')
                index_exists = any(idx['name'] == 'ix_domains_site_id' for idx in indexes)
                
                if not index_exists:
                    print("   [+] Adding index...")
                    conn.execute(text("CREATE INDEX ix_domains_site_id ON domains(site_id)"))
                    conn.commit()
                    print("   [OK] Index added successfully")
                else:
                    print("   [OK] Index already exists")
            
            # Refresh inspector to get latest schema
            inspector = inspect(engine)
            
            # Verify columns
            print("\n" + "="*60)
            print("Verifying columns...")
            print("="*60)
            
            previews_columns = [col['name'] for col in inspector.get_columns('previews')]
            domains_columns = [col['name'] for col in inspector.get_columns('domains')]
            
            print("\nColumns found:")
            if 'composited_image_url' in previews_columns:
                print("  [OK] previews.composited_image_url")
            else:
                print("  [ERROR] previews.composited_image_url (MISSING)")
            
            if 'site_id' in domains_columns:
                print("  [OK] domains.site_id")
            else:
                print("  [ERROR] domains.site_id (MISSING)")
        
        print("\n" + "="*60)
        print("[SUCCESS] Database fix completed successfully!")
        print("="*60)
        print("\nYou can now restart your application. The errors should be resolved.")
        
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

