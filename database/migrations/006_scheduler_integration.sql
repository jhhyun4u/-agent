-- Migration 006: Scheduler Integration Tables
-- Created: 2026-04-20
-- Purpose: Add tables for document migration scheduling and batch tracking

-- 1. Migration Schedules Table
CREATE TABLE IF NOT EXISTS migration_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    cron_expression VARCHAR(50) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT true,
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    CONSTRAINT valid_cron CHECK (cron_expression ~ '^\d+ \d+ \d+ \d+ \d+$')
);

CREATE INDEX idx_migration_schedules_enabled ON migration_schedules(enabled);
CREATE INDEX idx_migration_schedules_created ON migration_schedules(created_at DESC);

-- 2. Migration Batches Table
CREATE TABLE IF NOT EXISTS migration_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_id UUID NOT NULL REFERENCES migration_schedules(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL,
    total_documents INT NOT NULL DEFAULT 0,
    processed_documents INT NOT NULL DEFAULT 0,
    failed_documents INT NOT NULL DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'success', 'partial', 'failed')),
    CONSTRAINT valid_counts CHECK (
        total_documents >= 0 AND
        processed_documents >= 0 AND
        failed_documents >= 0 AND
        processed_documents + failed_documents <= total_documents
    )
);

CREATE INDEX idx_migration_batches_schedule ON migration_batches(schedule_id);
CREATE INDEX idx_migration_batches_status ON migration_batches(status);
CREATE INDEX idx_migration_batches_created ON migration_batches(created_at DESC);

-- 3. Migration Logs Table
CREATE TABLE IF NOT EXISTS migration_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL REFERENCES migration_batches(id) ON DELETE CASCADE,
    source_document_id VARCHAR(100) NOT NULL,
    document_name VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    retry_count INT NOT NULL DEFAULT 0,
    processed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    CONSTRAINT valid_status CHECK (status IN ('success', 'failed', 'skipped'))
);

CREATE INDEX idx_migration_logs_batch ON migration_logs(batch_id);
CREATE INDEX idx_migration_logs_status ON migration_logs(status);
CREATE INDEX idx_migration_logs_document ON migration_logs(source_document_id);

-- Add comments for documentation
COMMENT ON TABLE migration_schedules IS 'Stores schedule configurations for automatic document migration';
COMMENT ON TABLE migration_batches IS 'Tracks batch execution results and status';
COMMENT ON TABLE migration_logs IS 'Records individual document processing results per batch';

-- Commit confirmation
SELECT NOW() as migration_completed;
