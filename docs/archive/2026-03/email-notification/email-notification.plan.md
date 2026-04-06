# Plan: 이메일 알림 + 개인 설정 (email-notification)

> **Version**: 2.0
> **Date**: 2026-03-26
> **Status**: Plan
> **Priority**: HIGH

---

## 1. 배경 및 목표

### 1.1 현재 상태
- 알림 채널: **Teams Webhook + 인앱** (2가지만 구현)
- 이메일 발송 기능: **미구현**
- `users.notification_settings`: `{"teams": true, "in_app": true}` — email 키 없음
- 알림 발송 시 `notification_settings` 확인 로직 **미적용** (항상 발송)
- 개인 설정 페이지 **없음** — 알림 설정이 팀 설정(`/monitoring/settings`)에 혼재
- 알림 함수 12종이 3개 파일에 산재 (notification_service.py 7종, feedback_loop.py 4종, scheduled_monitor.py 1종)

### 1.2 목표

1. **이메일 알림 채널 추가** — 옵트인 방식으로 사용자가 직접 선택
2. **전체 12종 알림을 4개 카테고리로 통합 관리** — 모니터링뿐 아니라 제안서 작성·입찰·학습 과정 전체 포함
3. **개인 설정 페이지(`/settings`) 신설** — 프로필, 알림, 표시 설정을 한 곳에서 관리

### 1.3 대상 사용자
- **옵트인 방식**: 이메일 알림을 원하는 사용자만 직접 `/settings` 에서 활성화
- 역할 무관 — 본부장, 팀장, 일반 멤버 누구나 설정 가능
- 기본값: 모든 이메일 카테고리 `false`

---

## 2. 전체 알림 유형 (12종 → 4카테고리)

### 2.1 알림 인벤토리

| # | 알림 type | 발생 시점 | 발생 파일 | 현재 채널 |
|:-:|-----------|----------|----------|----------|
| 1 | `g2b_monitor` | 신규 추천 공고 발견 | scheduled_monitor.py | Teams + 인앱 |
| 2 | `deadline` | 마감 D-7/D-3/D-1 | notification_service.py | Teams + 인앱 |
| 3 | *(daily_summary)* | 매일 09:00 요약 | scheduled_monitor.py | 이메일 전용 (신규) |
| 4 | `approval_request` | 검토 및 승인 요청 | notification_service.py | Teams + 인앱 |
| 5 | `approval_result` | 검토 및 승인 결과 | notification_service.py | 인앱 |
| 6 | `ai_complete` | AI 생성 완료 | notification_service.py | 인앱 |
| 7 | `ai_error` | AI 작업 오류 | notification_service.py | Teams + 인앱 |
| 8 | `bid_confirmed` | 입찰가 확정 | notification_service.py | Teams + 인앱 |
| 9 | `bid_submitted` | 투찰 완료 | notification_service.py | Teams + 인앱 |
| 10 | `project_result` | 수주/패찰 결과 등록 | feedback_loop.py | 인앱 |
| 11 | `retrospect_reminder` | 회고 작성 요청 | feedback_loop.py | 인앱 |
| 12 | `content_suggestion` | 콘텐츠 등록 추천 | feedback_loop.py | 인앱 |
| - | `kb_update_suggestion` | 발주기관 관계 업데이트 | feedback_loop.py | 인앱 |

> `kb_update_suggestion`은 `content_suggestion`과 동일 카테고리로 묶어 13→12+1종.

### 2.2 4카테고리 매핑

| 카테고리 | 설정 키 | 포함 알림 | UI 설명 |
|----------|--------|----------|---------|
| **공고 모니터링** | `email_monitoring` | #1 신규 공고, #2 마감 임박, #3 일일 요약 | 추천 공고·마감 알림·일일 요약 |
| **제안서 작성** | `email_proposal` | #4 검토 및 승인 요청, #5 승인 결과, #6 AI 완료, #7 AI 오류 | 검토 및 승인 요청·AI 작업 결과 |
| **입찰·성과** | `email_bidding` | #8 입찰가 확정, #9 투찰 완료, #10 수주/패찰 결과 | 비딩·수주 결과 |
| **지식·학습** | `email_learning` | #11 회고 요청, #12 콘텐츠 등록 추천, kb_update | 회고·KB 환류 알림 |

---

## 3. 기술 방식: Microsoft Graph API

### 3.1 선택 이유
- TENOPA가 이미 Azure AD (MS365) 사용 중 → 추가 비용 없음
- Outlook 보낸편지함에 기록 → 감사 추적 가능
- 기존 `azure_ad_tenant_id`, `azure_ad_client_id`, `azure_ad_client_secret` 재활용

### 3.2 사전 조건 (Azure 포털)
1. Azure AD 앱 등록 → **API 권한** → Microsoft Graph → `Mail.Send` (애플리케이션 권한) 추가
2. **관리자 동의** 부여
3. 발신 이메일 계정 준비 (예: `noreply@tenopa.co.kr` 또는 공유 사서함)

---

## 4. `notification_settings` JSONB 재설계

```json
// Before
{"teams": true, "in_app": true}

// After — 4카테고리
{
  "teams": true,
  "in_app": true,
  "email_monitoring": false,
  "email_proposal": false,
  "email_bidding": false,
  "email_learning": false
}
```

- **모든 사용자 기본값: `false`** (옵트인)
- 마이그레이션: 기존 JSONB에 4키 추가 (기본 `false`)
- 기존 6키(`email_approval` 등)가 이미 들어간 사용자 → 4키로 재매핑 후 6키 제거

---

## 5. 구현 범위

### 5.1 백엔드

| 파일 | 변경 | 설명 |
|------|------|------|
| `app/config.py` | MODIFY | `email_enabled`, `email_sender`, `email_graph_scope` (이미 구현) |
| `app/services/email_service.py` | MODIFY | XSS 수정 + asyncio.Lock (이미 구현, 코드 품질 수정 완료) |
| `app/services/notification_service.py` | MODIFY | 6키 → 4키 매핑 변경 |
| `app/services/feedback_loop.py` | MODIFY | 4종 알림에 이메일 연동 추가 (`email_bidding`, `email_learning`) |
| `app/services/scheduled_monitor.py` | MODIFY | `email_new_bids` → `email_monitoring` 키 변경 |
| `app/api/routes_notification.py` | MODIFY | 스키마 6키 → 4키 |
| `app/models/notification_schemas.py` | MODIFY | 응답 스키마 6키 → 4키 |
| `database/migrations/012_*.sql` | REWRITE | 4키 마이그레이션으로 재작성 |

### 5.2 프론트엔드 — `/settings` 페이지 신설

| 파일 | 변경 | 설명 |
|------|------|------|
| `frontend/app/(app)/settings/page.tsx` | NEW | 개인 설정 페이지 (프로필 + 알림 + 표시) |
| `frontend/components/AppSidebar.tsx` | MODIFY | 하단 이메일 → `/settings` 링크 |
| `frontend/app/(app)/monitoring/settings/page.tsx` | MODIFY | 탭 3 "알림 설정" 제거 → 탭 2개만 유지 |

### 5.3 `/settings` 페이지 구조

```
내 설정
─────────────────────────────────────────
[프로필]  [알림]  [표시]

── 프로필 탭 ──
  이름: 이팀장 (읽기 전용, Azure AD)
  이메일: lead@tenopa.co.kr (읽기 전용)
  소속: 전략기획본부 > 기획팀
  역할: 팀장
  [비밀번호 변경]

── 알림 탭 ──
  채널 설정
    Teams 알림      [ON]
    인앱 알림       [ON]

  이메일 알림 (카테고리별)
  ┌─────────────────────────────────────┐
  │ [ ] 공고 모니터링                    │
  │     추천 공고·마감 임박·일일 요약     │
  │                                     │
  │ [ ] 제안서 작성                      │
  │     검토 및 승인 요청·AI 작업 결과    │
  │                                     │
  │ [ ] 입찰·성과                        │
  │     비딩·수주 결과                    │
  │                                     │
  │ [ ] 지식·학습                        │
  │     회고·KB 환류 알림                 │
  └─────────────────────────────────────┘

  * email_enabled=false → 토글 비활성 + "관리자에게 문의하세요"

── 표시 탭 ──
  테마: 다크 / 라이트
```

---

## 6. 알림 함수 ↔ 카테고리 매핑 (최종)

| 함수 | 설정 키 | 카테고리 |
|------|--------|---------|
| `notify_deadline_alert` | `email_monitoring` | 공고 모니터링 |
| 신규 공고 (scheduled_monitor) | `email_monitoring` | 공고 모니터링 |
| `send_daily_summary_email` | `email_monitoring` | 공고 모니터링 |
| `notify_approval_request` | `email_proposal` | 제안서 작성 |
| `notify_approval_result` | `email_proposal` | 제안서 작성 |
| `notify_ai_complete` | `email_proposal` | 제안서 작성 |
| `notify_agent_error` | `email_proposal` | 제안서 작성 |
| `notify_bid_confirmed` | `email_bidding` | 입찰·성과 |
| `notify_bid_submitted` | `email_bidding` | 입찰·성과 |
| process_project_completion (#10) | `email_bidding` | 입찰·성과 |
| process_project_completion (#11) | `email_learning` | 지식·학습 |
| process_project_completion (#12) | `email_learning` | 지식·학습 |
| _update_client_history (kb_update) | `email_learning` | 지식·학습 |

---

## 7. config.py 설정

```python
# 이메일 알림 (Microsoft Graph API) — 이미 구현됨
email_enabled: bool = False
email_sender: str = ""
email_graph_scope: str = "https://graph.microsoft.com/.default"
```

---

## 8. 의존성

| 패키지 | 용도 | 비고 |
|--------|------|------|
| `httpx` | Graph API HTTP 호출 | 이미 설치됨 |

> `msal` 불필요 — `httpx`로 직접 `client_credentials` 토큰 발급 (이미 구현).

---

## 9. 구현 순서

| 단계 | 작업 | 예상 규모 |
|:----:|------|----------|
| 1 | DB 마이그레이션 재작성 — 6키 → 4키 (`email_monitoring/proposal/bidding/learning`) | ~25줄 SQL |
| 2 | `notification_schemas.py` — 6키 → 4키 | ~5줄 변경 |
| 3 | `routes_notification.py` — 스키마 + 핸들러 4키 변경 | ~10줄 변경 |
| 4 | `notification_service.py` — 7개 함수의 설정 키 매핑 변경 | ~20줄 변경 |
| 5 | `feedback_loop.py` — 4종 알림에 `_try_send_email` 연동 추가 | ~40줄 추가 |
| 6 | `scheduled_monitor.py` — `email_new_bids` → `email_monitoring` 키 변경 + daily_summary 키 변경 | ~5줄 변경 |
| 7 | `/settings/page.tsx` 신규 생성 — 프로필 + 알림(4카테고리) + 표시 | ~250줄 |
| 8 | `AppSidebar.tsx` — 하단에 `/settings` 링크 추가 | ~10줄 |
| 9 | `/monitoring/settings/page.tsx` — 알림 탭 제거, `NotificationSettingsTab` + `ToggleRow` 삭제 | 삭제 |

**총 예상**: 변경 ~60줄, 추가 ~290줄 (프론트 250 + feedback 40), SQL ~25줄, 삭제 ~100줄

---

## 10. 기존 구현 재활용 (v1.0~v1.1에서 이미 완료된 것)

| 구현 | 상태 | 비고 |
|------|:----:|------|
| `email_service.py` (토큰 + 발송 + 템플릿) | 완료 | XSS 수정 + asyncio.Lock 적용 완료 |
| `config.py` 설정 3개 | 완료 | |
| `notification_service.py` 헬퍼 (`_get_user_email_info`, `_should_send_email`, `_try_send_email`) | 완료 | 키 매핑만 변경 필요 |
| `send_daily_summary_email()` | 완료 | 키만 변경 |
| 기존 7개 알림 함수 이메일 호출 | 완료 | 키만 변경 |

→ **신규 작업은 주로 키 변경 + feedback_loop 연동 + `/settings` 페이지**

---

## 11. 범위 외 (Out of Scope)

- 이메일 템플릿 커스터마이징 UI
- 이메일 발송 이력 대시보드
- 첨부파일 포함 이메일
- 이메일 수신 확인/읽음 추적
- 관리자가 강제로 특정 사용자에게 이메일 활성화
- 개인별 알림 유형 세분화 (카테고리 내 개별 on/off)

---

## 12. 리스크

| 리스크 | 영향 | 대응 |
|--------|------|------|
| Azure AD `Mail.Send` 권한 미승인 | 이메일 발송 불가 | `email_enabled=False`로 graceful skip |
| Graph API 호출 실패/지연 | 알림 지연 | 비동기 fire-and-forget + 에러 로깅 |
| 발송 한도 초과 | 대량 알림 시 차단 | Graph API 제한: 10,000건/일 — 충분 |
| 스팸 필터 | 수신 불가 | 사내 도메인 → Exchange 허용 목록 등록 |
| 6키→4키 마이그레이션 | 기존 설정 유실 | 마이그레이션에서 6키 OR 매핑 → 4키 자동 변환 |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-26 | Initial plan |
| 1.1 | 2026-03-26 | 역할 기반 → 옵트인 방식, 유형별 6키 세분화, 설정 UI 추가 |
| 2.0 | 2026-03-26 | **전면 재설계**: 12종 알림 4카테고리 통합, 6키→4키 간소화, `/settings` 개인 설정 페이지 신설, feedback_loop 이메일 연동, /monitoring/settings 알림 탭 제거, "결재"→"검토 및 승인" 용어 변경 |
