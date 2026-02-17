-- ============================================
-- Supabase 데이터베이스 스키마
-- 용역 제안서 자동 생성 에이전트
-- ============================================

-- UUID 확장 활성화
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 1. 제안서 테이블 (proposals)
-- ============================================
CREATE TABLE IF NOT EXISTS proposals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    client TEXT NOT NULL,
    year INTEGER NOT NULL,
    pages INTEGER,
    status TEXT,
    key_messages TEXT[],
    sections JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 제안서 검색을 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_proposals_title ON proposals USING GIN (to_tsvector('simple', title));
CREATE INDEX IF NOT EXISTS idx_proposals_client ON proposals USING GIN (to_tsvector('simple', client));
CREATE INDEX IF NOT EXISTS idx_proposals_year ON proposals (year);
CREATE INDEX IF NOT EXISTS idx_proposals_status ON proposals (status);

-- 샘플 데이터 삽입
INSERT INTO proposals (id, title, client, year, pages, status, key_messages, sections)
VALUES
    ('11111111-1111-1111-1111-111111111111', '클라우드 마이그레이션 프로젝트', '삼성전자', 2023, 150, '수주',
     ARRAY['보안 강화', '비용 절감', '운영 효율화'],
     '{"1": {"title": "회사개요", "pages": 15}, "2": {"title": "솔루션개요", "pages": 25}, "3": {"title": "구현계획", "pages": 40}}'::jsonb),
    ('22222222-2222-2222-2222-222222222222', 'AI/ML 플랫폼 구축', '현대모비스', 2023, 120, '수주',
     ARRAY['AI 자동화', '예측 분석', '실시간 처리'],
     '{"1": {"title": "회사개요", "pages": 12}, "2": {"title": "솔루션개요", "pages": 30}, "3": {"title": "구현계획", "pages": 35}}'::jsonb)
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 2. 인력 테이블 (personnel)
-- ============================================
CREATE TABLE IF NOT EXISTS personnel (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    grade TEXT NOT NULL,
    role TEXT NOT NULL,
    expertise TEXT[],
    available BOOLEAN DEFAULT TRUE,
    projects INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인력 검색을 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_personnel_role ON personnel (role);
CREATE INDEX IF NOT EXISTS idx_personnel_available ON personnel (available);
CREATE INDEX IF NOT EXISTS idx_personnel_expertise ON personnel USING GIN (expertise);

-- 샘플 데이터 삽입
INSERT INTO personnel (id, name, grade, role, expertise, available, projects)
VALUES
    ('33333333-3333-3333-3333-333333333333', '김철수', '상무', 'PM',
     ARRAY['Project Management', 'Cloud Architecture'], TRUE, 2),
    ('44444444-4444-4444-4444-444444444444', '이영희', '이사', 'CTO',
     ARRAY['AWS', 'Azure', 'Kubernetes'], TRUE, 1),
    ('55555555-5555-5555-5555-555555555555', '박민준', '차장', '개발리더',
     ARRAY['Python', 'Java', 'DevOps'], FALSE, 3),
    ('66666666-6666-6666-6666-666666666666', '최수진', '대리', 'QA',
     ARRAY['Test Automation', 'Performance Testing'], TRUE, 1)
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 3. 참고 자료 테이블 (reference_materials)
-- ============================================
CREATE TABLE IF NOT EXISTS reference_materials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    content TEXT,
    topics TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 참고 자료 검색을 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_reference_materials_title ON reference_materials USING GIN (to_tsvector('simple', title));
CREATE INDEX IF NOT EXISTS idx_reference_materials_content ON reference_materials USING GIN (to_tsvector('simple', content));
CREATE INDEX IF NOT EXISTS idx_reference_materials_topics ON reference_materials USING GIN (topics);

-- 샘플 데이터 삽입
INSERT INTO reference_materials (id, title, content, topics)
VALUES
    ('77777777-7777-7777-7777-777777777777', 'AWS 마이그레이션 Best Practices',
     '클라우드 마이그레이션 시 보안 고려사항...', ARRAY['AWS', 'Security', 'Migration']),
    ('88888888-8888-8888-8888-888888888888', 'Kubernetes 운영 가이드',
     '컨테이너 오케스트레이션의 기본 개념...', ARRAY['Kubernetes', 'DevOps', 'Container']),
    ('99999999-9999-9999-9999-999999999999', 'AI 시스템 아키텍처',
     '머신러닝 시스템 설계의 핵심 원칙...', ARRAY['AI', 'ML', 'Architecture']),
    ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '해외 클라우드 규정',
     '다국가 클라우드 서비스 준수사항...', ARRAY['Compliance', 'Security', 'Global'])
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 4. 문서 메타데이터 테이블 (documents)
-- ============================================
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename TEXT NOT NULL,
    path TEXT,
    size INTEGER,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 문서 검색을 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_documents_filename ON documents (filename);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents (created_at DESC);

-- ============================================
-- 자동 업데이트 트리거 함수
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 각 테이블에 트리거 적용
CREATE TRIGGER update_proposals_updated_at BEFORE UPDATE ON proposals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_personnel_updated_at BEFORE UPDATE ON personnel
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reference_materials_updated_at BEFORE UPDATE ON reference_materials
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Row Level Security (RLS) 정책
-- ============================================

-- RLS 활성화
ALTER TABLE proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE personnel ENABLE ROW LEVEL SECURITY;
ALTER TABLE reference_materials ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- 모든 테이블에 대해 인증된 사용자는 모든 작업 가능
CREATE POLICY "Enable all operations for authenticated users" ON proposals
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Enable all operations for authenticated users" ON personnel
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Enable all operations for authenticated users" ON reference_materials
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Enable all operations for authenticated users" ON documents
    FOR ALL USING (auth.role() = 'authenticated');

-- Service Role은 모든 작업 가능
CREATE POLICY "Enable all operations for service role" ON proposals
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Enable all operations for service role" ON personnel
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Enable all operations for service role" ON reference_materials
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Enable all operations for service role" ON documents
    FOR ALL USING (auth.role() = 'service_role');
