# email-notification v2.0 — 갭 분석

| 항목 | 내용 |
|------|------|
| 분석일 | 2026-03-26 |
| Design 참조 | docs/02-design/features/email-notification.design.md (v2.0) |
| Match Rate | **97%** (38/39) |

---

## Match Rate

| Section | Items | Matched | Gap | Rate |
|---------|:-----:|:-------:|:---:|:----:|
| §2 DB Migration | 4 | 4 | 0 | 100% |
| §3.1-3.2 Schemas + Routes | 5 | 5 | 0 | 100% |
| §3.3 notification_service.py | 7 | 7 | 0 | 100% |
| §3.4 feedback_loop.py | 4 | 3 | 1 | 75% |
| §3.5 scheduled_monitor.py | 2 | 2 | 0 | 100% |
| §4 Frontend /settings | 8 | 8 | 0 | 100% |
| §5 AppSidebar | 1 | 1 | 0 | 100% |
| §6 monitoring/settings | 5 | 5 | 0 | 100% |
| §7 Error handling | 3 | 3 | 0 | 100% |
| **Total** | **39** | **38** | **1** | **97%** |

---

## GAP 목록

| ID | Severity | 파일 | 설명 |
|----|----------|------|------|
| BUG-1 | **MEDIUM** | `feedback_loop.py` | `create_notification()` 호출 시 `notification_type=` (잘못된 키워드) 사용 + `proposal_id` 매개변수 누락. 런타임 TypeError 발생. `type=`으로 변경 + `proposal_id` 추가 필요. (기존 코드의 pre-existing bug, 이메일 연동 추가와 무관) |

---

## 결론

**PASS (97% >= 90%)**. Design v2.0의 39개 체크 항목 중 38개 완전 일치. 1건 기존 코드 버그(feedback_loop.py의 잘못된 키워드 인자) 발견 — 즉시 수정 권장.

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-26 | v1.0 분석 (98%) |
| 2.0 | 2026-03-26 | v2.0 전면 재분석 (97%) — feedback_loop BUG-1 발견 |
