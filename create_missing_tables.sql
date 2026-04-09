-- Create g2b_bids table
CREATE TABLE IF NOT EXISTS g2b_bids (
    bid_no VARCHAR(50) PRIMARY KEY,
    name TEXT NOT NULL,
    client VARCHAR(255),
    budget DECIMAL(15, 2),
    deadline TIMESTAMP,
    project_type VARCHAR(100),
    bid_status VARCHAR(50) DEFAULT 'open',
    proposal_status VARCHAR(50) DEFAULT 'not_started',
    announcement_date TIMESTAMP,
    bid_open_date TIMESTAMP,
    bid_close_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_g2b_bids_status ON g2b_bids(bid_status);
CREATE INDEX IF NOT EXISTS idx_g2b_bids_proposal_status ON g2b_bids(proposal_status);
CREATE INDEX IF NOT EXISTS idx_g2b_bids_deadline ON g2b_bids(deadline);

-- Create proposal_status table
CREATE TABLE IF NOT EXISTS proposal_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bid_no VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'not_started',
    current_step INT DEFAULT 0,
    progress_pct INT DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    FOREIGN KEY (bid_no) REFERENCES g2b_bids(bid_no) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_proposal_status_bid_no ON proposal_status(bid_no);
CREATE INDEX IF NOT EXISTS idx_proposal_status_status ON proposal_status(status);
