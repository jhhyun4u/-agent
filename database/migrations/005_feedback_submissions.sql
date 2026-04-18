-- STEP 4A Gap 3: 주간 피드백 분석 & 가중치 조정
-- 피드백 제출 테이블 (섹션별 리뷰 피드백)

CREATE TABLE feedback_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    section_type TEXT NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('APPROVE', 'REJECT')),
    ratings JSONB,
    comment TEXT,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스
CREATE INDEX idx_feedback_proposal ON feedback_submissions(proposal_id);
CREATE INDEX idx_feedback_created_at ON feedback_submissions(created_at DESC);
CREATE INDEX idx_feedback_section ON feedback_submissions(section_type);

-- RLS (Row Level Security)
ALTER TABLE feedback_submissions ENABLE ROW LEVEL SECURITY;

-- Policy: 해당 제안서 조직의 멤버만 피드백 조회 가능
CREATE POLICY "Feedback - Read for org members"
    ON feedback_submissions FOR SELECT
    USING (
        proposal_id IN (
            SELECT id FROM proposals
            WHERE org_id IN (
                SELECT org_id FROM organization_members
                WHERE user_id = auth.uid()
            )
        )
    );

-- Policy: 인증된 사용자만 피드백 추가 가능
CREATE POLICY "Feedback - Create for authenticated"
    ON feedback_submissions FOR INSERT
    WITH CHECK (auth.uid() = created_by);

-- Policy: 자신의 피드백만 수정/삭제 가능
CREATE POLICY "Feedback - Update own"
    ON feedback_submissions FOR UPDATE
    USING (auth.uid() = created_by)
    WITH CHECK (auth.uid() = created_by);

CREATE POLICY "Feedback - Delete own"
    ON feedback_submissions FOR DELETE
    USING (auth.uid() = created_by);

-- 트리거: updated_at 자동 업데이트
CREATE TRIGGER update_feedback_submissions_updated_at
BEFORE UPDATE ON feedback_submissions
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
