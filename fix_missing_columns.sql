-- SQL script to add missing columns to fix database errors
-- Run this directly against your PostgreSQL database if migrations haven't been applied
-- This script is idempotent and safe to run multiple times

-- Add composited_image_url to previews table (if it doesn't exist)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'previews' 
        AND column_name = 'composited_image_url'
    ) THEN
        ALTER TABLE previews ADD COLUMN composited_image_url VARCHAR;
        RAISE NOTICE 'Added composited_image_url column to previews table';
    ELSE
        RAISE NOTICE 'Column composited_image_url already exists in previews table';
    END IF;
END $$;

-- Add site_id to domains table (if it doesn't exist)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'domains' 
        AND column_name = 'site_id'
    ) THEN
        ALTER TABLE domains ADD COLUMN site_id INTEGER;
        RAISE NOTICE 'Added site_id column to domains table';
        
        -- Add foreign key constraint if published_sites table exists
        IF EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'published_sites'
        ) THEN
            -- Check if constraint already exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'fk_domains_site'
            ) THEN
                ALTER TABLE domains 
                ADD CONSTRAINT fk_domains_site 
                FOREIGN KEY (site_id) REFERENCES published_sites(id);
                RAISE NOTICE 'Added foreign key constraint fk_domains_site';
            END IF;
        END IF;
        
        -- Add index if it doesn't exist
        IF NOT EXISTS (
            SELECT 1 FROM pg_indexes 
            WHERE tablename = 'domains' 
            AND indexname = 'ix_domains_site_id'
        ) THEN
            CREATE INDEX ix_domains_site_id ON domains(site_id);
            RAISE NOTICE 'Added index ix_domains_site_id';
        END IF;
    ELSE
        RAISE NOTICE 'Column site_id already exists in domains table';
    END IF;
END $$;

-- Verify columns were added
SELECT 
    table_name, 
    column_name, 
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name IN ('previews', 'domains') 
AND column_name IN ('composited_image_url', 'site_id')
ORDER BY table_name, column_name;

