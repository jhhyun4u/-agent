# Plan: 제안서작성 서비스 플랫폼 v1 & 7. 작업 목록
Cohesion: 0.10 | Nodes: 20

## Key Nodes
- **Plan: 제안서작성 서비스 플랫폼 v1** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-platform-v1.plan.md) -- 9 connections
  - -> contains -> [[1-plan-plus-phase-1]]
  - -> contains -> [[2-plan-plus-phase-2]]
  - -> contains -> [[3-yagni-plan-plus-phase-3]]
  - -> contains -> [[4-v1]]
  - -> contains -> [[5-api]]
  - -> contains -> [[6]]
  - -> contains -> [[7]]
  - -> contains -> [[8]]
  - -> contains -> [[9]]
- **7. 작업 목록** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-platform-v1.plan.md) -- 7 connections
  - -> contains -> [[phase-a-db]]
  - -> contains -> [[phase-b]]
  - -> contains -> [[phase-c]]
  - -> contains -> [[phase-d-api]]
  - -> contains -> [[phase-e-api]]
  - -> contains -> [[phase-f-nextjs]]
  - <- contains <- [[plan-v1]]
- **3. YAGNI 검토 (Plan Plus Phase 3)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-platform-v1.plan.md) -- 3 connections
  - -> contains -> [[v1]]
  - -> contains -> [[v2]]
  - <- contains <- [[plan-v1]]
- **2. 탐색된 대안 (Plan Plus Phase 2)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-platform-v1.plan.md) -- 2 connections
  - -> contains -> [[approach-a]]
  - <- contains <- [[plan-v1]]
- **5. 나라장터 API 연동 설계** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-platform-v1.plan.md) -- 2 connections
  - -> contains -> [[4]]
  - <- contains <- [[plan-v1]]
- **1. 사용자 의도 발견 (Plan Plus Phase 1)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-platform-v1.plan.md) -- 1 connections
  - <- contains <- [[plan-v1]]
- **활용 흐름 (4단계)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-platform-v1.plan.md) -- 1 connections
  - <- contains <- [[5-api]]
- **4. v1 아키텍처** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-platform-v1.plan.md) -- 1 connections
  - <- contains <- [[plan-v1]]
- **6. 핵심 기술 결정사항** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-platform-v1.plan.md) -- 1 connections
  - <- contains <- [[plan-v1]]
- **8. 성공 기준 (최종)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-platform-v1.plan.md) -- 1 connections
  - <- contains <- [[plan-v1]]
- **9. 다음 단계** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-platform-v1.plan.md) -- 1 connections
  - <- contains <- [[plan-v1]]
- **선택: Approach A — 단일 앱 확장** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-platform-v1.plan.md) -- 1 connections
  - <- contains <- [[2-plan-plus-phase-2]]
- **Phase A — DB + 기반 인프라** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-platform-v1.plan.md) -- 1 connections
  - <- contains <- [[7]]
- **Phase B — 세션 영속성 + 핵심 파이프라인 수정** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-platform-v1.plan.md) -- 1 connections
  - <- contains <- [[7]]
- **Phase C — 파일 저장소 + 다운로드** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-platform-v1.plan.md) -- 1 connections
  - <- contains <- [[7]]
- **Phase D — 나라장터 실제 API 연동** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-platform-v1.plan.md) -- 1 connections
  - <- contains <- [[7]]
- **Phase E — 팀 협업 API + 알림** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-platform-v1.plan.md) -- 1 connections
  - <- contains <- [[7]]
- **Phase F — 프론트엔드 (Next.js)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-platform-v1.plan.md) -- 1 connections
  - <- contains <- [[7]]
- **v1 포함 (필수)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-platform-v1.plan.md) -- 1 connections
  - <- contains <- [[3-yagni-plan-plus-phase-3]]
- **v2 이후 (보류)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\proposal-platform-v1.plan.md) -- 1 connections
  - <- contains <- [[3-yagni-plan-plus-phase-3]]

## Internal Relationships
- 2. 탐색된 대안 (Plan Plus Phase 2) -> contains -> 선택: Approach A — 단일 앱 확장 [EXTRACTED]
- 3. YAGNI 검토 (Plan Plus Phase 3) -> contains -> v1 포함 (필수) [EXTRACTED]
- 3. YAGNI 검토 (Plan Plus Phase 3) -> contains -> v2 이후 (보류) [EXTRACTED]
- 5. 나라장터 API 연동 설계 -> contains -> 활용 흐름 (4단계) [EXTRACTED]
- 7. 작업 목록 -> contains -> Phase A — DB + 기반 인프라 [EXTRACTED]
- 7. 작업 목록 -> contains -> Phase B — 세션 영속성 + 핵심 파이프라인 수정 [EXTRACTED]
- 7. 작업 목록 -> contains -> Phase C — 파일 저장소 + 다운로드 [EXTRACTED]
- 7. 작업 목록 -> contains -> Phase D — 나라장터 실제 API 연동 [EXTRACTED]
- 7. 작업 목록 -> contains -> Phase E — 팀 협업 API + 알림 [EXTRACTED]
- 7. 작업 목록 -> contains -> Phase F — 프론트엔드 (Next.js) [EXTRACTED]
- Plan: 제안서작성 서비스 플랫폼 v1 -> contains -> 1. 사용자 의도 발견 (Plan Plus Phase 1) [EXTRACTED]
- Plan: 제안서작성 서비스 플랫폼 v1 -> contains -> 2. 탐색된 대안 (Plan Plus Phase 2) [EXTRACTED]
- Plan: 제안서작성 서비스 플랫폼 v1 -> contains -> 3. YAGNI 검토 (Plan Plus Phase 3) [EXTRACTED]
- Plan: 제안서작성 서비스 플랫폼 v1 -> contains -> 4. v1 아키텍처 [EXTRACTED]
- Plan: 제안서작성 서비스 플랫폼 v1 -> contains -> 5. 나라장터 API 연동 설계 [EXTRACTED]
- Plan: 제안서작성 서비스 플랫폼 v1 -> contains -> 6. 핵심 기술 결정사항 [EXTRACTED]
- Plan: 제안서작성 서비스 플랫폼 v1 -> contains -> 7. 작업 목록 [EXTRACTED]
- Plan: 제안서작성 서비스 플랫폼 v1 -> contains -> 8. 성공 기준 (최종) [EXTRACTED]
- Plan: 제안서작성 서비스 플랫폼 v1 -> contains -> 9. 다음 단계 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Plan: 제안서작성 서비스 플랫폼 v1, 7. 작업 목록, 3. YAGNI 검토 (Plan Plus Phase 3)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 proposal-platform-v1.plan.md이다.

### Key Facts
- Phase A — DB + 기반 인프라 | 순서 | 파일 | 작업 | |------|------|------| | A1 | database/schema.sql | 전체 DDL 작성 (8개 테이블 + RLS + 트리거 + startup 함수) | | A2 | app/config.py | G2B_API_KEY, CORS_ORIGINS 환경변수 추가, .hwp 제거 | | A3 | app/utils/supabase_client.py | AsyncClient get_async_client() 구현 | | A4 | app/main.py |…
- v1 포함 (필수) - 로그인 / 팀 관리 (Supabase Auth) - 온보딩 플로우 (신규 가입자 팀/개인 선택) - 제안서 생성 UI (RFP 업로드 → 진행상태 실시간 → 결과 뷰어 → 다운로드) - 팀 협업 (댓글/검토 상태 관리 + 댓글 알림 이메일) - 제안서 이력 DB (수주/낙찰 결과 저장) - **나라장터 API 연동** (입찰공고 검색, 낙찰결과 조회, 계약결과 조회, 업체이력 조회 — 4개) - 파일 저장소 (Supabase Storage — 로컬 저장 대체) - 완료 알림 이메일 (5~15분 대기 작업…
- 선택: Approach A — 단일 앱 확장 현재 FastAPI 백엔드를 유지하면서 Next.js 프론트엔드 추가. 가장 빠른 시작, 현재 코드 재활용 최대화.
- 현재 상태 `app/services/g2b_service.py`에 mock 데이터 기반 구현 완료. 실제 API 키만 있으면 `_mock_search_contracts` -> 실제 API 호출로 교체 가능한 구조.
- 핵심 문제 1. **사내 도구 → SaaS 전환**: 현재 내부 API만 있어 외부 고객이 직접 사용 불가 2. **팀 협업 부재**: 1인 API 호출 구조 — 여러 담당자가 함께 제안서를 검토/수정할 수 없음 3. **지식 축적 부재**: 수주/낙찰 결과가 저장되지 않아 다음 제안에 활용 불가
