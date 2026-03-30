# Design: 이메일 알림 + 개인 설정 (email-notification)

> **Version**: 2.0
> **Date**: 2026-03-26
> **Plan**: `docs/01-plan/features/email-notification.plan.md` v2.0
> **Status**: Design

---

## 1. 아키텍처 개요

```
                        ┌──────────────────────────┐
                        │  /settings (개인 설정)    │
                        │  ├─ 프로필 탭 (읽기 전용) │
                        │  ├─ 알림 탭 (4카테고리)   │
                        │  └─ 표시 탭 (테마)        │
                        └────────┬─────────────────┘
                                 │ PUT /api/notifications/settings
                                 ▼
                        users.notification_settings (JSONB)
                        ┌──────────────────────────────────┐
                        │ teams: true                      │
                        │ in_app: true                     │
                        │ email_monitoring: false           │
                        │ email_proposal: false             │
                        │ email_bidding: false              │
                        │ email_learning: false             │
                        └──────────────┬───────────────────┘
                                       │
        ┌──────────────────────────────┼─────────────────────────────────┐
        │                              │                                 │
  notification_service.py      feedback_loop.py              scheduled_monitor.py
  (7개 알림 함수)              (4개 알림 호출)               (신규 공고 + 일일 요약)
        │                              │                                 │
        └──────────────────────────────┼─────────────────────────────────┘
                                       │
                              _try_send_email()
                              ├─ _should_send_email() → 옵트인 확인
                              └─ email_service.py → Graph API 발송
```

---

## 2. DB 마이그레이션

### 2.1 파일: `database/migrations/012_email_notification_settings.sql` (재작성)

```sql
-- v2.0: 6키→4키 마이그레이션 (기존 v1 6키가 있는 경우 OR 매핑 후 제거)

-- Step 1: 기존 6키 사용자 → 4키로 매핑
-- email_approval OR email_deadline → email_monitoring 중 하나라도 true면 true
UPDATE users
SET notification_settings = notification_settings
  || jsonb_build_object(
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

-- Step 2: 6키 제거
UPDATE users
SET notification_settings = notification_settings
  - 'email_approval' - 'email_deadline' - 'email_ai_complete'
  - 'email_bid' - 'email_new_bids' - 'email_daily_summary'
WHERE notification_settings ? 'email_approval';

-- Step 3: 6키가 없는 사용자 (기존 또는 신규) → 4키 추가
UPDATE users
SET notification_settings = notification_settings
  || '{"email_monitoring": false, "email_proposal": false, "email_bidding": false, "email_learning": false}'::jsonb
WHERE notification_settings IS NOT NULL
  AND NOT (notification_settings ? 'email_monitoring');

-- Step 4: NULL 사용자 → 전체 기본값
UPDATE users
SET notification_settings = '{"teams": true, "in_app": true, "email_monitoring": false, "email_proposal": false, "email_bidding": false, "email_learning": false}'::jsonb
WHERE notification_settings IS NULL;
```

### 2.2 확장 후 JSONB

```json
{
  "teams": true,
  "in_app": true,
  "email_monitoring": false,
  "email_proposal": false,
  "email_bidding": false,
  "email_learning": false
}
```

---

## 3. 백엔드 변경

### 3.1 `notification_schemas.py`

```python
class NotificationSettingsResponse(BaseModel):
    teams: bool = True
    in_app: bool = True
    email_monitoring: bool = False
    email_proposal: bool = False
    email_bidding: bool = False
    email_learning: bool = False
    email_enabled: bool = False  # 서버 설정 (읽기 전용)
```

### 3.2 `routes_notification.py`

```python
_EMAIL_SETTING_KEYS = [
    "email_monitoring", "email_proposal", "email_bidding", "email_learning",
]

class NotificationSettingsUpdate(BaseModel):
    teams: bool | None = None
    in_app: bool | None = None
    email_monitoring: bool | None = None
    email_proposal: bool | None = None
    email_bidding: bool | None = None
    email_learning: bool | None = None
```

GET/PUT 핸들러는 기존 v1 로직 동일 (키 목록만 변경).

### 3.3 `notification_service.py` — 키 매핑 변경

| 함수 | Before (6키) | After (4키) |
|------|-------------|-------------|
| `notify_approval_request` | `email_approval` | `email_proposal` |
| `notify_approval_result` | `email_approval` | `email_proposal` |
| `notify_deadline_alert` | `email_deadline` | `email_monitoring` |
| `notify_ai_complete` | `email_ai_complete` | `email_proposal` |
| `notify_agent_error` | `email_ai_complete` | `email_proposal` |
| `notify_bid_confirmed` | `email_bid` | `email_bidding` |
| `notify_bid_submitted` | `email_bid` | `email_bidding` |

변경 범위: 각 `_try_send_email` 호출의 두 번째 인자만 변경.

### 3.4 `feedback_loop.py` — 이메일 연동 추가

`process_project_completion` 함수 내 4곳에 `_try_send_email` 호출 추가:

```python
from app.services.notification_service import _try_send_email

# #10 프로젝트 결과 알림 (참여자) → email_bidding
await _try_send_email(
    pt["user_id"], "email_bidding",
    f"[프로젝트 결과] {project_name}",
    f"프로젝트 결과: {project_name}",
    f"'{project_name}' 프로젝트가 '{result}' 처리되었습니다.",
    f"{settings.frontend_url}/projects/{proposal_id}",
)

# #11 회고 작성 요청 → email_learning
await _try_send_email(
    created_by, "email_learning",
    f"[회고 요청] {project_name}",
    f"회고 작성 요청: {project_name}",
    "7일 이내에 회고 워크시트를 작성해 주세요.",
    f"{settings.frontend_url}/projects/{proposal_id}/retrospect",
)

# #12 콘텐츠 등록 추천 (수주 시) → email_learning
await _try_send_email(
    created_by, "email_learning",
    f"[콘텐츠 등록 추천] {project_name}",
    f"콘텐츠 등록 후보: {project_name}",
    f"수주 제안서 '{project_name}'의 섹션을 콘텐츠 라이브러리에 등록하시겠습니까?",
    f"{settings.frontend_url}/projects/{proposal_id}/artifacts/proposal",
)

# kb_update_suggestion → email_learning
await _try_send_email(
    created_by, "email_learning",
    f"[발주기관 업데이트] {client_name}",
    f"발주기관 관계 업데이트 제안: {client_name}",
    f"수주 성공! 관계 수준을 '{current_rel}' → '{suggested}'로 변경하시겠습니까?",
    f"{settings.frontend_url}/kb/clients",
)
```

### 3.5 `scheduled_monitor.py` — 키 변경

```python
# 신규 공고 이메일: email_new_bids → email_monitoring
if _should_send_email(user_data, "email_monitoring"):

# 일일 요약: email_daily_summary → email_monitoring
# send_daily_summary_email 내 옵트인 필터:
(u.get("notification_settings") or {}).get("email_monitoring", False)
```

---

## 4. 프론트엔드: `/settings` 개인 설정 페이지

### 4.1 라우트: `frontend/app/(app)/settings/page.tsx`

### 4.2 데이터 소스

| 탭 | API | 비고 |
|----|-----|------|
| 프로필 | `GET /api/auth/me` | 읽기 전용 (name, email, team, division, role) |
| 알림 | `GET/PUT /api/notifications/settings` | 기존 API 재사용 |
| 표시 | localStorage `theme` | API 불필요 |

### 4.3 프로필 탭

```typescript
interface UserProfile {
  id: string;
  name: string;
  email: string;
  role: string;
  team_name?: string;
  division_name?: string;
}

// GET /api/auth/me 로 조회
// 모든 필드 읽기 전용 (Azure AD 동기화)
// [비밀번호 변경] 버튼 → router.push("/change-password")
```

**UI 구조:**

```
┌─────────────────────────────────────┐
│  프로필                              │
│  ┌─────────────────────────────────┐│
│  │ 이름     이팀장                 ││
│  │ 이메일   lead@tenopa.co.kr     ││
│  │ 소속     전략기획본부 > 기획팀  ││
│  │ 역할     팀장                   ││
│  └─────────────────────────────────┘│
│  [비밀번호 변경]                     │
│                                     │
│  ※ 프로필 정보는 조직 계정에서      │
│    자동 동기화됩니다.                │
└─────────────────────────────────────┘
```

### 4.4 알림 탭

```typescript
const EMAIL_CATEGORIES = [
  {
    key: "email_monitoring",
    label: "공고 모니터링",
    desc: "추천 공고·마감 임박·일일 요약",
  },
  {
    key: "email_proposal",
    label: "제안서 작성",
    desc: "검토 및 승인 요청·AI 작업 결과",
  },
  {
    key: "email_bidding",
    label: "입찰·성과",
    desc: "비딩·수주 결과",
  },
  {
    key: "email_learning",
    label: "지식·학습",
    desc: "회고·KB 환류 알림",
  },
] as const;
```

**UI 구조:**

```
┌─────────────────────────────────────┐
│  채널 설정                           │
│  Teams 알림    ─────────────── [ON] │
│  인앱 알림     ─────────────── [ON] │
├─────────────────────────────────────┤
│  이메일 알림                         │
│  ┌─────────────────────────────────┐│
│  │ [ ] 공고 모니터링               ││
│  │     추천 공고·마감 임박·일일 요약││
│  │                                 ││
│  │ [ ] 제안서 작성                  ││
│  │     검토 및 승인 요청·AI 작업 결과│
│  │                                 ││
│  │ [ ] 입찰·성과                    ││
│  │     비딩·수주 결과               ││
│  │                                 ││
│  │ [ ] 지식·학습                    ││
│  │     회고·KB 환류 알림            ││
│  └─────────────────────────────────┘│
│  * email_enabled=false 시:          │
│    토글 비활성 + 안내 문구           │
└─────────────────────────────────────┘
```

토글 변경 → 즉시 `PUT /api/notifications/settings` 호출, 실패 시 롤백.

### 4.5 표시 탭

```
┌─────────────────────────────────────┐
│  테마                                │
│  ◉ 다크  ○ 라이트  ○ 시스템 설정    │
└─────────────────────────────────────┘
```

기존 `ThemeToggle` 로직 재사용 (localStorage `theme` 키).

### 4.6 API 호출 — 기존 `api` 클라이언트 사용

```typescript
// lib/api.ts에 추가
notifications: {
  getSettings() {
    return request<NotificationSettings>("GET", "/notifications/settings");
  },
  updateSettings(body: Partial<NotificationSettings>) {
    return request<NotificationSettings>("PUT", "/notifications/settings", body);
  },
},
```

---

## 5. `AppSidebar.tsx` 수정

### 5.1 하단 이메일 영역 → `/settings` 링크

```tsx
// Before
<p className="text-xs text-[#5c5c5c] truncate flex-1">{email}</p>

// After
<Link href="/settings" className="text-xs text-[#5c5c5c] truncate flex-1 hover:text-[#ededed]">
  {email}
</Link>
```

변경 최소 — `<p>` → `<Link>` 교체 1줄.

---

## 6. `/monitoring/settings` 정리

### 6.1 제거 대상

- `NotificationSettingsTab` 컴포넌트 (~100줄)
- `ToggleRow` 컴포넌트 (~40줄)
- `EMAIL_TOGGLES` 상수
- 탭 3 "알림 설정" 관련 state/UI
- `getToken` 헬퍼 (raw fetch용)

### 6.2 유지

- 탭 1 "팀 프로필" (ProfileTab)
- 탭 2 "검색 조건 프리셋" (PresetsTab)
- `Field` 공통 래퍼
- `TagInput` 컴포넌트
- 온보딩 스텝 (2단계로 축소)

### 6.3 변경

```typescript
// tab 타입: "profile" | "presets" | "notifications" → "profile" | "presets"
const [tab, setTab] = useState<"profile" | "presets">("profile");
```

---

## 7. 에러 처리

| 시나리오 | 처리 |
|----------|------|
| `email_enabled=false` | `_should_send_email()` → False, UI 토글 비활성 + 안내 |
| Graph API 토큰 실패 | `asyncio.Lock` 보호, 로그 + False 반환 |
| 개별 발송 실패 | fire-and-forget, 다른 채널 정상 |
| feedback_loop 이메일 실패 | 기존 인앱 알림은 정상, 이메일만 스킵 |
| `/settings` 프로필 로드 실패 | "프로필 정보를 불러올 수 없습니다" + 알림/표시 탭은 정상 |

---

## 8. 구현 순서 (Implementation Order)

| 단계 | 파일 | 작업 | 의존 |
|:----:|------|------|:----:|
| 1 | `database/migrations/012_*.sql` | 6키→4키 마이그레이션 재작성 | - |
| 2 | `notification_schemas.py` | 6키 → 4키 변경 | - |
| 3 | `routes_notification.py` | 스키마 + _EMAIL_SETTING_KEYS 4키 | §2 |
| 4 | `notification_service.py` | 7개 함수 키 매핑 변경 | §2 |
| 5 | `feedback_loop.py` | 4종 이메일 연동 추가 | §4 |
| 6 | `scheduled_monitor.py` | 키 변경 (`email_monitoring`) | §2 |
| 7 | `lib/api.ts` | notifications 객체 추가 | - |
| 8 | `settings/page.tsx` | 개인 설정 페이지 신규 생성 | §7 |
| 9 | `AppSidebar.tsx` | 이메일 → `/settings` 링크 | §8 |
| 10 | `monitoring/settings/page.tsx` | 알림 탭 제거 + 정리 | §8 |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-26 | Initial design (6키, /monitoring/settings 탭 3) |
| 2.0 | 2026-03-26 | **전면 재설계**: 4카테고리, `/settings` 개인 설정 페이지, feedback_loop 연동, monitoring 알림 탭 제거, "결재"→"검토 및 승인" |
