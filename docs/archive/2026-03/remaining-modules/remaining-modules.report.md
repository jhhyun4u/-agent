# remaining-modules PDCA 완료 보고서

> **Summary**: Phase 5 서비스 모듈 6종 — 토큰 관리, AI 상태 추적, 섹션 잠금, 스케줄 모니터링, 데이터 신뢰성, 출처 태깅
>
> **Project**: TENOPA Proposer (내부 용역제안 플랫폼)
> **Feature**: remaining-modules (Phase 5 서비스 모듈 6종)
> **Created**: 2026-03-16
> **Last Modified**: 2026-03-16
> **Status**: ✅ Completed
> **Match Rate**: 93% → 96% → **99%**

---

## 1. 실행 개요

### 1.1 완료 현황

메인 피처 `proposal-agent-v1` (Phase 0~4.5)에서 다루지 못한 **서비스 계층 6개 모듈**을 구현 완료하였다. 설계 문서 `14-services-v3.md` (§21-25)과 `12-prompts.md` (§16-3)에 정의된 사양을 기반으로 구현하였으며, 2회 iteration을 거쳐 최종 **99% 매칭률**을 달성하였다.

| 모듈 | 설계 섹션 | v1.0 | v2.0 | v3.0 (최종) | 상태 |
|------|----------|:----:|:----:|:----------:|:----:|
| token_manager.py | §21 | 90% | 95% | 100% | ✅ |
| ai_status_manager.py | §22 | 92% | 97% | 100% | ✅ |
| section_lock.py | §24 | 95% | 95% | 96% | ✅ |
| scheduled_monitor.py | §25-2 | 96% | 96% | 100% | ✅ |
| trustworthiness.py | §16-3-1 | 93% | 97% | 100% | ✅ |
| source_tagger.py | §16-3-2 | 91% | 96% | 100% | ✅ |
| **전체** | | **93%** | **96%** | **99%** | ✅ |

### 1.2 핵심 성과

- **토큰 예산 관리**: STEP별 16개 예산 엔트리 + KB 절단 + 피드백 윈도잉 + Prompt Caching + 구조화 출력 스키마
- **AI 작업 추적**: 6종 상태 + 하트비트 + 서브태스크 진행률 + DB 로깅 + 상태 변경 리스너 + abort/retry/logs API
- **동시 편집 보호**: 5분 자동 해제 잠금 + 갱신 + 관리자 강제 해제
- **G2B 정기 모니터링**: 매일 09:00 팀별 키워드 검색 + Teams 알림 + 인앱 알림 + 설정 가능 링크
- **데이터 신뢰성 6대 규칙**: 할루시네이션 금지, 출처 태그(참조 ID 포함), 과장 금지, RFP 용어 우선 등
- **출처 태깅 분석**: 9종 태그 패턴(ID 캡처) + 근거 비율 산출 + 미근거 주장 탐지 + 신뢰성 평가 25점 + 교차 섹션 숫자 일관성

---

## 2. PDCA 사이클 기록

### 2.1 Plan → Design

설계 문서는 메인 피처 `proposal-agent-v1`에 포함되어 있으며, 현재 아카이브에 보관 중이다.

| 설계 파일 | 섹션 | 아카이브 경로 |
|----------|------|-------------|
| 14-services-v3.md | §21 (token_manager), §22 (ai_status_manager), §24 (section_lock), §25-2 (scheduled_monitor) | `docs/archive/2026-03/proposal-agent-v1/design/` |
| 12-prompts.md | §16-3-1 (trustworthiness), §16-3-2 (source_tagger) | `docs/archive/2026-03/proposal-agent-v1/design/` |

### 2.2 Do (구현)

6개 모듈 신규 구현 + 3개 API 엔드포인트 추가 + 1개 DB 마이그레이션.

### 2.3 Check → Act (2회 Iteration)

| Iteration | 대상 | 변경 | 결과 |
|-----------|------|------|------|
| **v1→v2** (P1 수정) | 7건 P1 | 코드 수정 7건 — T2(피드백 요약), A2(abort paused 전환), A3(API 3건), A4(리스너 패턴), R2(출처 ID), S1(패턴 ID 캡처), S6(숫자 일관성) | 93% → 96% |
| **v2→v3** (P2 정리) | 12건 P2 | 코드 수정 3건(T3, M1, A5) + 설계 업데이트 6건(T1, T4, A1, S3, S4, S5) + No-action 3건(R1, R3, S2) | 96% → 99% |

---

## 3. 모듈별 최종 상태

### 3.1 token_manager.py (§21) — 100%

**파일**: `app/services/token_manager.py`

| 구현 항목 | 상태 |
|----------|:----:|
| STEP_TOKEN_BUDGETS (16 entries, v3.5 확장) | ✅ |
| KB_TOP_K=5, KB_MAX_BODY_LENGTH=500 | ✅ |
| FEEDBACK_WINDOW_SIZE=3 | ✅ |
| build_context() (content blocks + cache config) | ✅ |
| Prompt Caching (ephemeral) | ✅ |
| truncate_kb_results() | ✅ |
| trim_feedback_history() + _summarize_feedbacks() | ✅ |
| build_structured_output_schema() (3 STEP 스키마) | ✅ (v3.0) |

### 3.2 ai_status_manager.py (§22) — 100%

**파일**: `app/services/ai_status_manager.py` + `app/api/routes_workflow.py`

| 구현 항목 | 상태 |
|----------|:----:|
| 6종 StatusType | ✅ |
| start_task, update_sub_task, heartbeat, check_heartbeat | ✅ |
| abort_task (paused 전환, 완료 서브태스크 보존) | ✅ |
| get_composite_status | ✅ |
| persist_log (DB 로깅) | ✅ |
| _emit_status_change + add/remove_listener | ✅ |
| _recalculate_progress (complete만 카운트) | ✅ (v3.0) |
| API 4종 (ai-status, ai-abort, ai-retry, ai-logs) | ✅ |

### 3.3 section_lock.py (§24) — 96%

**파일**: `app/services/section_lock.py`

| 구현 항목 | 상태 |
|----------|:----:|
| 5분 잠금 + 자동 만료 정리 | ✅ |
| acquire/release/force_release | ✅ |
| 충돌 감지 + 에러 코드 SECT_001 | ✅ |
| API 3종 (POST/DELETE/GET) | ✅ |

**Deferred**: L1 — SSE lock/unlock 이벤트 (SSE 버스 인프라 구축 시 처리)

### 3.4 scheduled_monitor.py (§25-2) — 100%

**파일**: `app/services/scheduled_monitor.py`

| 구현 항목 | 상태 |
|----------|:----:|
| Daily 09:00 CronTrigger | ✅ |
| 팀별 키워드 검색 | ✅ |
| 중복 필터링 (g2b_monitor_log) | ✅ |
| Teams + 인앱 알림 | ✅ |
| 알림 링크: settings.frontend_url 기반 | ✅ (v3.0) |

### 3.5 trustworthiness.py (§16-3-1) — 100%

**파일**: `app/prompts/trustworthiness.py`

| 구현 항목 | 상태 |
|----------|:----:|
| 6대 규칙 | ✅ |
| SOURCE_TAG_FORMAT (참조 ID 포함) | ✅ |
| FORBIDDEN_EXPRESSIONS (10종) | ✅ |
| TRUSTWORTHINESS_SCORING (25점) | ✅ |
| claude_client.py COMMON_SYSTEM_RULES 주입 | ✅ |

### 3.6 source_tagger.py (§16-3-2) — 100%

**파일**: `app/services/source_tagger.py`

| 구현 항목 | 상태 |
|----------|:----:|
| SourceTag dataclass (tag_type, reference_id, text_span) | ✅ |
| TAG_PATTERNS (9종, 참조 ID 캡처) | ✅ |
| extract_source_tags() | ✅ |
| calculate_grounding_ratio() (claim-sentence 기반) | ✅ |
| find_ungrounded_claims() | ✅ |
| evaluate_trustworthiness() (standalone) | ✅ |
| check_number_consistency() | ✅ |
| 3-level judgment (KB기반/혼합/일반) | ✅ |

---

## 4. 통합 검증

| 검증 항목 | 결과 |
|----------|:----:|
| TRUSTWORTHINESS_RULES → claude_client.py import | ✅ |
| COMMON_SYSTEM_RULES에 포함 | ✅ |
| 전체 claude_generate() 호출에 적용 | ✅ |
| Prompt Caching (cache_control ephemeral) | ✅ |
| setup_scheduler() → main.py lifespan | ✅ |
| Section lock 3개 API → routes_workflow.py | ✅ |
| AI status/abort/retry/logs 4개 API → routes_workflow.py | ✅ |
| 006_g2b_monitor_log.sql 마이그레이션 | ✅ |

---

## 5. 잔여 갭

### Deferred (1건)

| ID | 모듈 | 갭 | 사유 |
|----|------|-----|------|
| L1 | section_lock | SSE lock/unlock 이벤트 미발행 | SSE 버스 인프라 미구축. 리스너 패턴은 ai_status_manager에 준비됨 |

---

## 6. 교훈

### 잘 진행된 부분
1. **모듈 독립성**: 6개 모듈이 각각 독립적으로 구현·검증·개선 가능
2. **설계 문서 상세도**: SS21~25의 함수 시그니처·상수값까지 명시되어 구현과 갭 분석 모두 가속
3. **확장적 구현**: 설계 외 긍정적 확장 (force_release, 인앱 알림, FORBIDDEN_EXPRESSIONS, claim-sentence 기반 grounding)
4. **설계 역반영 효과**: P2 갭을 설계 문서 업데이트로 해결 → 설계-구현 동기화 100% 달성 (5/6 모듈)

### 개선할 부분
1. **SSE 인프라 선행 필요**: ai_status_manager, section_lock 모두 SSE 연동 지연 — 공통 SSE 버스를 먼저 구축하면 여러 모듈에서 활용 가능
2. **API 완성도 체크리스트**: 초기 구현 시 설계된 API 엔드포인트 전체를 체크리스트로 관리했으면 P1 API 누락 방지 가능

---

## 7. 성과 지표

| 지표 | 값 | 목표 | 달성도 |
|------|:----:|:----:|:------:|
| 최종 매칭률 | 99% | 90% | ✅ 110% |
| P0 갭 | 0건 | 0건 | ✅ |
| P1 갭 | 0건 | 0건 | ✅ |
| P2 갭 (해결) | 11/12건 | - | ✅ |
| P2 갭 (Deferred) | 1건 | - | SSE 인프라 대기 |
| 구현 모듈 | 6/6 | 6/6 | ✅ 100% |
| Iteration 횟수 | 2회 | ≤5회 | ✅ |
| 통합 검증 | 8/8 | - | ✅ |

---

## 부록: 버전 이력

| 버전 | 날짜 | 변경 | 저자 |
|------|------|------|------|
| 1.0 | 2026-03-16 | 초기 완료 보고서 (93%) | report-generator |
| 2.0 | 2026-03-16 | v3.0 갭 분석 반영 — 99% 달성, P1 전수 해결, P2 11/12 해결, Iteration 2회 기록 | report-generator |

---

**관련 문서**:
- Design (archived): [14-services-v3.md](../../archive/2026-03/proposal-agent-v1/design/14-services-v3.md) (§21-25)
- Design (archived): [12-prompts.md](../../archive/2026-03/proposal-agent-v1/design/12-prompts.md) (§16-3)
- Analysis: [remaining-modules.analysis.md](../../03-analysis/remaining-modules.analysis.md) (99%)
