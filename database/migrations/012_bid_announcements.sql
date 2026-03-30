-- 나라장터 공고 저장 테이블
CREATE TABLE IF NOT EXISTS bid_announcements (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bid_no          TEXT NOT NULL UNIQUE,           -- 공고번호
    bid_title       TEXT NOT NULL,                  -- 공고명
    agency          TEXT,                           -- 발주기관
    budget_amount   BIGINT,                         -- 예산금액
    deadline_date   TIMESTAMPTZ,                    -- 마감일
    days_remaining  INT,                            -- 남은 일수
    bid_type        TEXT,                           -- 입찰공고|사전규격|발주계획
    bid_stage       TEXT,                           -- 본공고|재공고
    classification  TEXT,                           -- 분류
    raw_data        JSONB,                          -- G2B 원본 응답 (전체)
    proposal_status TEXT,                           -- 제안상태 (제안중|제안완료|수주|패찰)
    decided_by      UUID REFERENCES users(id),      -- 결정자
    is_bookmarked   BOOLEAN DEFAULT false,          -- 즐겨찾기
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_bid_announcements_created_at ON bid_announcements(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_bid_announcements_bid_no ON bid_announcements(bid_no);
CREATE INDEX IF NOT EXISTS idx_bid_announcements_deadline ON bid_announcements(deadline_date);
CREATE INDEX IF NOT EXISTS idx_bid_announcements_proposal_status ON bid_announcements(proposal_status);
