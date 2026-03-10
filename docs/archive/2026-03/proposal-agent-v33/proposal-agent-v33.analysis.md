# Gap 분석: proposal-agent-v33

## 메타 정보
- Feature: proposal-agent-v33
- 분석일: 2026-03-05
- Match Rate: 60%
- 판정: iterate 필요 (< 90%)

## Design vs Implementation 비교표

| 설계 항목 | 구현 상태 | 심각도 |
|-----------|-----------|--------|
| main.py 불필요 import 제거 | 완료 | - |
| phase_schemas.py PhaseArtifact 1~5 | 완료 | - |
| phase_prompts.py Phase 2~5 프롬프트 | 완료 | - |
| phase_executor.py PhaseExecutor | 완료 | - |
| /execute PhaseExecutor 연결 | 완료 | - |
| /download 엔드포인트 추가 | 완료 | - |
| /generate 레거시 import 제거 | 미수정 | Critical |
| Phase 4 섹션별 병렬 처리 | 순차 처리 | Medium |
| HITL Gate #3, #5 | 미구현 | Medium |
| Phase별 토큰 예산 제어 | 미구현 | Low |

Match Rate: 6 / 10 = 60%

## Critical Gap: /generate 엔드포인트 런타임 에러

위치: app/api/routes_v31.py L44-45, L69-84

현재 코드 (런타임 ImportError 발생):
- from graph import build_phased_supervisor_graph  # 존재 X
- from state.phased_state import initialize_phased_supervisor_state  # 존재 X
- state = initialize_phased_supervisor_state(...)  # 존재 X
- graph = build_phased_supervisor_graph()  # 존재 X

영향: /generate 호출 시 즉시 500 에러 -> 전체 워크플로 차단

수정 방향: generate_proposal_v31 함수를 v3.3 방식으로 단순화
- 없는 모듈 import 제거
- proposal_state dict 직접 구성
- graph 저장 불필요 (PhaseExecutor 대체)

## Medium Gap

1. Phase 4 병렬 처리 미구현
   - 설계: asyncio.gather() 병렬 생성
   - 현재: 단일 Claude 호출로 순차 처리
   - 영향: 성능 저하 (기능은 동작)

2. HITL Gate 미구현
   - 설계: Phase 3, 5 완료 후 사람 승인 대기
   - 현재: 5 Phase 연속 자동 실행
   - 영향: 사람 검토 기회 없음

## 코드 품질 이슈
- routes_v31.py: asyncio, BackgroundTasks import 미사용
- phase_executor.py: 메서드별 docstring 없음

## 결론

Match Rate: 60% -> iterate 필요

즉시 수정: /generate 엔드포인트 (Critical)
수정 후 예상 Match Rate: ~85%

다음 단계: /pdca iterate proposal-agent-v33
