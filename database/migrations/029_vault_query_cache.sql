-- Migration: Create vault_query_cache table for caching search results
-- Phase: Vault Phase 1 Week 3 - B.1 Caching Strategy

-- Create cache table
CREATE TABLE IF NOT EXISTS vault_query_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cache_key TEXT UNIQUE NOT NULL,  -- SHA256 hash of query+sections+filters
    sections TEXT[] NOT NULL,         -- Array of section names for filtering
    response_json JSONB NOT NULL,    -- Serialized List[SearchResult]
    hit_count INT DEFAULT 0,         -- Track cache hit frequency
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL  -- Auto-expiration timestamp
);

-- Indexes for efficient lookups
CREATE INDEX idx_vault_query_cache_key ON vault_query_cache(cache_key);
CREATE INDEX idx_vault_query_cache_expires ON vault_query_cache(expires_at);

-- Partial index for active cache entries (performance optimization)
CREATE INDEX idx_vault_query_cache_active
ON vault_query_cache(cache_key, created_at)
WHERE expires_at > NOW();

-- Function: Auto-cleanup of expired cache entries
CREATE OR REPLACE FUNCTION cleanup_vault_query_cache()
RETURNS TABLE(deleted_count INT) AS $$
BEGIN
    DELETE FROM vault_query_cache
    WHERE expires_at < NOW();

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

-- Create job for periodic cleanup (runs daily at 2 AM UTC)
-- Note: This requires pg_cron extension. Install with: CREATE EXTENSION IF NOT EXISTS pg_cron;
-- SELECT cron.schedule('cleanup-vault-cache', '0 2 * * *', 'SELECT cleanup_vault_query_cache()');

-- Enable RLS (optional - if multi-tenant security is needed)
ALTER TABLE vault_query_cache ENABLE ROW LEVEL SECURITY;

-- Policy: No RLS policy needed as this is system-wide cache
-- The cache is shared across users (not tenant-specific)
