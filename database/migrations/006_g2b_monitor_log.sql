-- G2B 모니터링 알림 이력 (§25-2)
-- scheduled_monitor.py가 이미 알림 발송한 공고를 기록하여 중복 방지

CREATE TABLE IF NOT EXISTS g2b_monitor_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id         UUID NOT NULL,
    bid_notice_no   TEXT NOT NULL,
    title           TEXT,
    notified_at     TIMESTAMPTZ DEFAULT now(),
    UNIQUE(team_id, bid_notice_no)
);

CREATE INDEX IF NOT EXISTS idx_g2b_monitor_team ON g2b_monitor_log(team_id);

-- teams 테이블에 monitor_keywords 컬럼 추가 (없는 경우)
ALTER TABLE teams ADD COLUMN IF NOT EXISTS monitor_keywords TEXT[] DEFAULT '{}';
