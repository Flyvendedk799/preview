#!/usr/bin/env python
"""
Script to fix missing database columns.
This script connects to your database and adds the missing columns.
Safe to run multiple times (idempotent).
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Run SQL commands to fix missing columns."""
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    except ImportError:
        print("ERROR: psycopg2 not found. Installing...")
        print("Please install it with: pip install psycopg2-binary")
        print("\nOr run this script in your Railway environment where dependencies are installed.")
        sys.exit(1)
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        print("Please set DATABASE_URL or run this script in your Railway environment")
        sys.exit(1)
    
    print("Connecting to database...")
    print(f"Database URL: {database_url.split('@')[1] if '@' in database_url else 'hidden'}")
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        print("\n" + "="*60)
        print("Fixing missing database columns...")
        print("="*60 + "\n")
        
        # Check and add composited_image_url to previews table
        print("1. Checking previews.composited_image_url...")
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'previews' 
            AND column_name = 'composited_image_url'
        """)
        
        if cur.fetchone():
            print("   ✓ Column composited_image_url already exists")
        else:
            print("   + Adding composited_image_url column...")
            cur.execute("ALTER TABLE previews ADD COLUMN composited_image_url VARCHAR")
            print("   ✓ Column composited_image_url added successfully")
        
        # Check and add site_id to domains table
        print("\n2. Checking domains.site_id...")
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'domains' 
            AND column_name = 'site_id'
        """)
        
        if cur.fetchone():
            print("   ✓ Column site_id already exists")
        else:
            print("   + Adding site_id column...")
            cur.execute("ALTER TABLE domains ADD COLUMN site_id INTEGER")
            print("   ✓ Column site_id added successfully")
            
            # Check if published_sites table exists before adding foreign key
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'published_sites'
            """)
            
            if cur.fetchone():
                # Check if foreign key constraint already exists
                cur.execute("""
                    SELECT constraint_name 
                    FROM information_schema.table_constraints 
                    WHERE constraint_name = 'fk_domains_site'
                """)
                
                if not cur.fetchone():
                    print("   + Adding foreign key constraint...")
                    cur.execute("""
                        ALTER TABLE domains 
                        ADD CONSTRAINT fk_domains_site 
                        FOREIGN KEY (site_id) REFERENCES published_sites(id)
                    """)
                    print("   ✓ Foreign key constraint added successfully")
                else:
                    print("   ✓ Foreign key constraint already exists")
            else:
                print("   ⚠ published_sites table doesn't exist yet, skipping foreign key")
            
            # Add index
            cur.execute("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'domains' 
                AND indexname = 'ix_domains_site_id'
            """)
            
            if not cur.fetchone():
                print("   + Adding index...")
                cur.execute("CREATE INDEX ix_domains_site_id ON domains(site_id)")
                print("   ✓ Index added successfully")
            else:
                print("   ✓ Index already exists")
        
        # Verify columns
        print("\n" + "="*60)
        print("Verifying columns...")
        print("="*60)
        cur.execute("""
            SELECT 
                table_name, 
                column_name, 
                data_type,
                is_nullable
            FROM information_schema.columns 
            WHERE table_name IN ('previews', 'domains') 
            AND column_name IN ('composited_image_url', 'site_id')
            ORDER BY table_name, column_name
        """)
        
        results = cur.fetchall()
        if results:
            print("\nColumns found:")
            for table, column, data_type, nullable in results:
                print(f"  ✓ {table}.{column} ({data_type}, nullable={nullable})")
        else:
            print("\n⚠ No columns found (this shouldn't happen)")
        
        cur.close()
        conn.close()
        
        print("\n" + "="*60)
        print("✓ Database fix completed successfully!")
        print("="*60)
        print("\nYou can now restart your application. The errors should be resolved.")
        
    except psycopg2.Error as e:
        print(f"\n✗ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

