"""Fix 6 issues in plan and design documents."""
from pathlib import Path

BASE = Path(__file__).parent

# ─── Design Document ──────────────────────────────────────────────
design_path = BASE / "docs/02-design/features/proposal-platform-v1.design.md"
design = design_path.read_text(encoding="utf-8")

# Fix 1: Add RLS for teams, team_members, invitations + comments INSERT WITH CHECK
OLD_RLS = """ALTER TABLE usage_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY usage_logs_access ON usage_logs
  USING (owner_id = auth.uid()
    OR team_id IN (SELECT team_id FROM team_members WHERE user_id = auth.uid()));
```"""

NEW_RLS = """ALTER TABLE usage_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY usage_logs_access ON usage_logs
  USING (owner_id = auth.uid()
    OR team_id IN (SELECT team_id FROM team_members WHERE user_id = auth.uid()));

-- teams: 소속 팀 또는 직접 생성한 팀만 접근
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
CREATE POLICY teams_access ON teams
  USING (
    id IN (SELECT team_id FROM team_members WHERE user_id = auth.uid())
    OR created_by = auth.uid()
  );

-- team_members: 같은 팀 소속 사용자만 접근
ALTER TABLE team_members ENABLE ROW LEVEL SECURITY;
CREATE POLICY team_members_access ON team_members
  USING (team_id IN (
    SELECT team_id FROM team_members WHERE user_id = auth.uid()
  ));

-- invitations: admin만 조회/관리 (초대 수락 콜백은 service_role_key 사용)
ALTER TABLE invitations ENABLE ROW LEVEL SECURITY;
CREATE POLICY invitations_access ON invitations
  USING (team_id IN (
    SELECT team_id FROM team_members
    WHERE user_id = auth.uid() AND role = 'admin'
  ));

-- comments INSERT: 본인이 작성하는 댓글 + 접근 권한 있는 proposal만 허용
CREATE POLICY comments_insert ON comments FOR INSERT
  WITH CHECK (
    user_id = auth.uid()
    AND proposal_id IN (
      SELECT p.id FROM proposals p
      JOIN team_members tm ON p.team_id = tm.team_id
      WHERE tm.user_id = auth.uid()
      UNION
      SELECT id FROM proposals WHERE owner_id = auth.uid()
    )
  );
```"""

assert OLD_RLS in design, "RLS 섹션을 찾지 못했습니다"
design = design.replace(OLD_RLS, NEW_RLS)

# Fix 2: Invitation accept flow — token → team_id + email lookup
OLD_INVITE = """팀원 초대 흐름:
```
1. POST /invite (admin only)
   -> invitations upsert (on_conflict team_id,email → status=pending, expires_at 갱신)
   -> supabase.auth.admin.invite_user_by_email()
2. 사용자 이메일 클릭 -> Supabase 인증 완료
3. GET /invitations/accept?token=...
   -> invitations 조회 (status=pending, expires_at > now())
   -> team_members INSERT
   -> invitations status='accepted'
```"""

NEW_INVITE = """팀원 초대 흐름:
```
1. POST /invite (admin only)
   -> invitations upsert (on_conflict team_id,email → status=pending, expires_at 갱신)
   -> supabase.auth.admin.invite_user_by_email(
        email=target_email,
        redirectTo=f"{FRONTEND_URL}/invitations/accept?team_id={team_id}"
      )
2. 사용자 이메일 클릭 -> Supabase 인증 완료 -> redirectTo URL로 리다이렉트
3. GET /invitations/accept?team_id=...
   -> JWT에서 user.email 추출 (get_current_user)
   -> invitations 조회 (team_id=?, email=user.email, status='pending', expires_at > now())
   -> team_members INSERT ON CONFLICT (team_id, user_id) DO NOTHING
   -> invitations UPDATE status='accepted'
```
주의: ?token= 파라미터 사용 금지 — Supabase가 관리하는 내부 토큰과 혼동됨.
      team_id를 redirectTo에 포함하고, 이메일은 JWT(user.email)에서 추출."""

assert OLD_INVITE in design, "초대 흐름 섹션을 찾지 못했습니다"
design = design.replace(OLD_INVITE, NEW_INVITE)

# Update metadata
design = design.replace(
    "최종 수정 | 2026-03-05 (기술 이슈 검토 v5 반영)",
    "최종 수정 | 2026-03-06 (RLS 누락 + 초대 토큰 패턴 수정 v6 반영)"
)

design_path.write_text(design, encoding="utf-8")
print("✅ Design document updated")

# ─── Plan Document ────────────────────────────────────────────────
plan_path = BASE / "docs/01-plan/features/proposal-platform-v1.plan.md"
plan = plan_path.read_text(encoding="utf-8")

# Fix 3: proposals columns in section 4 — add missing columns
OLD_PROPOSALS_COL = """  ├─ proposals           (id UUID4, title, status, owner_id, team_id,
  │                       current_phase, phases_completed, failed_phase,
  │                       win_result, storage_path_docx, storage_path_pptx)"""

NEW_PROPOSALS_COL = """  ├─ proposals           (id UUID4, title, status, owner_id, team_id,
  │                       current_phase, phases_completed, failed_phase,
  │                       rfp_filename, rfp_content, rfp_content_truncated,
  │                       storage_path_docx, storage_path_pptx, storage_path_rfp,
  │                       storage_upload_failed, win_result, bid_amount, notes)"""

assert OLD_PROPOSALS_COL in plan, "proposals 컬럼 섹션을 찾지 못했습니다"
plan = plan.replace(OLD_PROPOSALS_COL, NEW_PROPOSALS_COL)

# Fix 4: Add F10 middleware.ts to Phase F
OLD_PHASE_F = """| F9 | lib/api.ts | 401 감지 -> 세션 만료 처리 + /login 리다이렉트 |"""

NEW_PHASE_F = """| F9 | lib/api.ts | 401 감지 -> 세션 만료 처리 + /login 리다이렉트 |
| F10 | frontend/middleware.ts | Next.js 인증 보호 라우트 (@supabase/ssr 기반) |"""

assert OLD_PHASE_F in plan, "F9 항목을 찾지 못했습니다"
plan = plan.replace(OLD_PHASE_F, NEW_PHASE_F)

# Fix 5: Section 9 next step
OLD_NEXT = """```
/pdca do proposal-platform-v1
```"""

NEW_NEXT = """```
/pdca analyze proposal-platform-v1
```"""

assert OLD_NEXT in plan, "다음 단계 섹션을 찾지 못했습니다"
plan = plan.replace(OLD_NEXT, NEW_NEXT)

# Update metadata
plan = plan.replace(
    "최종 수정 | 2026-03-05 (설계 검토 최종 동기화)",
    "최종 수정 | 2026-03-06 (proposals 컬럼, F10, 다음 단계 업데이트)"
)

plan_path.write_text(plan, encoding="utf-8")
print("✅ Plan document updated")
print("\n수정 완료:")
print("  [Design] 1. teams/team_members/invitations RLS 추가")
print("  [Design] 2. comments INSERT WITH CHECK 추가")
print("  [Design] 3. 초대 수락 흐름: ?token= → ?team_id= + email 조회")
print("  [Plan]   4. proposals 컬럼 목록 완성 (storage_upload_failed 등)")
print("  [Plan]   5. F10 middleware.ts 작업 추가")
print("  [Plan]   6. 섹션 9 다음 단계: /pdca do → /pdca analyze")
