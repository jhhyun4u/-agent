-- 012: notification_settings JSONB — 이메일 알림 4카테고리 키 추가 (v2.0)
-- email_monitoring, email_proposal, email_bidding, email_learning (모두 기본 false)

-- Step 1: 기존 v1 6키 사용자 → 4키로 OR 매핑 후 6키 제거
UPDATE users
SET notification_settings = (
  notification_settings
  - 'email_approval' - 'email_deadline' - 'email_ai_complete'
  - 'email_bid' - 'email_new_bids' - 'email_daily_summary'
) || jsonb_build_object(
  'email_monitoring', COALESCE(
    (notification_settings->>'email_deadline')::boolean
    OR (notification_settings->>'email_new_bids')::boolean
    OR (notification_settings->>'email_daily_summary')::boolean, false),
  'email_proposal', COALESCE(
    (notification_settings->>'email_approval')::boolean
    OR (notification_settings->>'email_ai_complete')::boolean, false),
  'email_bidding', COALESCE(
    (notification_settings->>'email_bid')::boolean, false),
  'email_learning', false
)
WHERE notification_settings ? 'email_approval';

-- Step 2: 6키 없는 기존 사용자 → 4키 추가
UPDATE users
SET notification_settings = notification_settings
  || '{"email_monitoring": false, "email_proposal": false, "email_bidding": false, "email_learning": false}'::jsonb
WHERE notification_settings IS NOT NULL
  AND NOT (notification_settings ? 'email_monitoring');

-- Step 3: NULL 사용자 → 전체 기본값
UPDATE users
SET notification_settings = '{"teams": true, "in_app": true, "email_monitoring": false, "email_proposal": false, "email_bidding": false, "email_learning": false}'::jsonb
WHERE notification_settings IS NULL;
