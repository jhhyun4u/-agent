-- 008: 사용자 비밀번호 변경 필요 플래그 (인증 단순화)
ALTER TABLE users ADD COLUMN must_change_password BOOLEAN DEFAULT false;
