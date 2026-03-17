-- 007_storage_upload_tracking.sql
-- proposals 테이블에 Storage 업로드 경로 + 실패 추적 컬럼 추가 (설계 §8)

ALTER TABLE proposals
    ADD COLUMN IF NOT EXISTS storage_path_docx  TEXT,
    ADD COLUMN IF NOT EXISTS storage_path_pptx  TEXT,
    ADD COLUMN IF NOT EXISTS storage_path_hwpx  TEXT,
    ADD COLUMN IF NOT EXISTS storage_upload_failed BOOLEAN NOT NULL DEFAULT false;

COMMENT ON COLUMN proposals.storage_path_docx IS 'Supabase Storage 경로: {id}/proposal.docx';
COMMENT ON COLUMN proposals.storage_path_pptx IS 'Supabase Storage 경로: {id}/proposal.pptx';
COMMENT ON COLUMN proposals.storage_path_hwpx IS 'Supabase Storage 경로: {id}/proposal.hwpx';
COMMENT ON COLUMN proposals.storage_upload_failed IS 'Storage 업로드 부분/전체 실패 플래그 (부분 실패 추적용)';
