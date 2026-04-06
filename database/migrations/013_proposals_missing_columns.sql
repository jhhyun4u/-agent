-- 013: proposals 테이블 누락 컬럼 추가
-- list_proposals, create_from_bid 등에서 참조하지만 DB에 미존재

-- 마감일 (bid_announcements.deadline_date에서 복사)
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS deadline TIMESTAMPTZ;

-- 발주처명
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS client_name TEXT;

-- 조직 계층 (스코프 필터용, schema_v3.4.sql에 인덱스는 있으나 컬럼 누락)
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS org_id UUID REFERENCES organizations(id);
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS division_id UUID REFERENCES divisions(id);
