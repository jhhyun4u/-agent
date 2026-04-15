# PSM-16: Q&A 기록 검색 가능 저장 & 3. 기존 자산 분석
Cohesion: 0.09 | Nodes: 23

## Key Nodes
- **PSM-16: Q&A 기록 검색 가능 저장** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.plan.md) -- 9 connections
  - -> contains -> [[1]]
  - -> contains -> [[2-scope]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
  - -> contains -> [[5]]
  - -> contains -> [[6]]
  - -> contains -> [[7]]
  - -> contains -> [[8]]
  - -> contains -> [[9]]
- **3. 기존 자산 분석** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.plan.md) -- 5 connections
  - -> contains -> [[3-1-db]]
  - -> contains -> [[3-2]]
  - -> contains -> [[3-3]]
  - -> contains -> [[3-4]]
  - <- contains <- [[psm-16-qa]]
- **4. 구현 항목** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.plan.md) -- 5 connections
  - -> contains -> [[phase-a-db]]
  - -> contains -> [[phase-b-api]]
  - -> contains -> [[phase-c]]
  - -> contains -> [[phase-d]]
  - <- contains <- [[psm-16-qa]]
- **1. 배경 및 목적** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.plan.md) -- 4 connections
  - -> contains -> [[1-1]]
  - -> contains -> [[1-2]]
  - -> contains -> [[1-3]]
  - <- contains <- [[psm-16-qa]]
- **2. 범위 (Scope)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.plan.md) -- 3 connections
  - -> contains -> [[2-1-in-scope]]
  - -> contains -> [[2-2-out-of-scope]]
  - <- contains <- [[psm-16-qa]]
- **1-1. 배경** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.plan.md) -- 1 connections
  - <- contains <- [[1]]
- **1-2. 목적** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.plan.md) -- 1 connections
  - <- contains <- [[1]]
- **1-3. 요구사항 원문** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.plan.md) -- 1 connections
  - <- contains <- [[1]]
- **2-1. In-Scope** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.plan.md) -- 1 connections
  - <- contains <- [[2-scope]]
- **2-2. Out-of-Scope** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.plan.md) -- 1 connections
  - <- contains <- [[2-scope]]
- **3-1. DB (이미 존재)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **3-2. 서비스 (확장 필요)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **3-3. 설계 초안 (아카이브)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **3-4. 프론트엔드 (신규 필요)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **5. 구현 순서** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.plan.md) -- 1 connections
  - <- contains <- [[psm-16-qa]]
- **6. 기술 결정** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.plan.md) -- 1 connections
  - <- contains <- [[psm-16-qa]]
- **7. 리스크** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.plan.md) -- 1 connections
  - <- contains <- [[psm-16-qa]]
- **8. 성공 기준** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.plan.md) -- 1 connections
  - <- contains <- [[psm-16-qa]]
- **9. 관련 요구사항** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.plan.md) -- 1 connections
  - <- contains <- [[psm-16-qa]]
- **Phase A: DB 마이그레이션** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.plan.md) -- 1 connections
  - <- contains <- [[4]]
- **Phase B: 백엔드 서비스 + API** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.plan.md) -- 1 connections
  - <- contains <- [[4]]
- **Phase C: 워크플로 연동** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.plan.md) -- 1 connections
  - <- contains <- [[4]]
- **Phase D: 프론트엔드** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.plan.md) -- 1 connections
  - <- contains <- [[4]]

## Internal Relationships
- 1. 배경 및 목적 -> contains -> 1-1. 배경 [EXTRACTED]
- 1. 배경 및 목적 -> contains -> 1-2. 목적 [EXTRACTED]
- 1. 배경 및 목적 -> contains -> 1-3. 요구사항 원문 [EXTRACTED]
- 2. 범위 (Scope) -> contains -> 2-1. In-Scope [EXTRACTED]
- 2. 범위 (Scope) -> contains -> 2-2. Out-of-Scope [EXTRACTED]
- 3. 기존 자산 분석 -> contains -> 3-1. DB (이미 존재) [EXTRACTED]
- 3. 기존 자산 분석 -> contains -> 3-2. 서비스 (확장 필요) [EXTRACTED]
- 3. 기존 자산 분석 -> contains -> 3-3. 설계 초안 (아카이브) [EXTRACTED]
- 3. 기존 자산 분석 -> contains -> 3-4. 프론트엔드 (신규 필요) [EXTRACTED]
- 4. 구현 항목 -> contains -> Phase A: DB 마이그레이션 [EXTRACTED]
- 4. 구현 항목 -> contains -> Phase B: 백엔드 서비스 + API [EXTRACTED]
- 4. 구현 항목 -> contains -> Phase C: 워크플로 연동 [EXTRACTED]
- 4. 구현 항목 -> contains -> Phase D: 프론트엔드 [EXTRACTED]
- PSM-16: Q&A 기록 검색 가능 저장 -> contains -> 1. 배경 및 목적 [EXTRACTED]
- PSM-16: Q&A 기록 검색 가능 저장 -> contains -> 2. 범위 (Scope) [EXTRACTED]
- PSM-16: Q&A 기록 검색 가능 저장 -> contains -> 3. 기존 자산 분석 [EXTRACTED]
- PSM-16: Q&A 기록 검색 가능 저장 -> contains -> 4. 구현 항목 [EXTRACTED]
- PSM-16: Q&A 기록 검색 가능 저장 -> contains -> 5. 구현 순서 [EXTRACTED]
- PSM-16: Q&A 기록 검색 가능 저장 -> contains -> 6. 기술 결정 [EXTRACTED]
- PSM-16: Q&A 기록 검색 가능 저장 -> contains -> 7. 리스크 [EXTRACTED]
- PSM-16: Q&A 기록 검색 가능 저장 -> contains -> 8. 성공 기준 [EXTRACTED]
- PSM-16: Q&A 기록 검색 가능 저장 -> contains -> 9. 관련 요구사항 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 PSM-16: Q&A 기록 검색 가능 저장, 3. 기존 자산 분석, 4. 구현 항목를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 psm-16-qa-search.plan.md이다.

### Key Facts
- > **요구사항 ID**: PSM-16 (Must) > **기능명**: psm-16-qa-search > **버전**: v1.0 > **작성일**: 2026-03-18 > **상태**: Plan
- 3-1. DB (이미 존재) - `presentation_qa` 테이블: `id, proposal_id, question, answer, evaluator_reaction, memo, created_at` - `content_library` 테이블: `type` 컬럼에 `qa_record` 이미 정의됨 - `lessons_learned` 테이블: 교훈 저장 (임베딩 포함)
- Phase A: DB 마이그레이션 - **A-1**: `presentation_qa` 테이블 확장 - `embedding vector(1536)` 컬럼 추가 - `content_library_id UUID REFERENCES content_library(id)` 컬럼 추가 - `category TEXT DEFAULT 'general'` 컬럼 추가 - `created_by UUID REFERENCES users(id)` 컬럼 추가 - IVFFlat 인덱스: `idx_presentation_qa_embedding` - B-tree…
- 1-1. 배경 - PSM-16은 v1 요구사항 중 유일한 HIGH 잔여 갭 항목 - 현재 `presentation_qa` 테이블이 DB 스키마에 존재하나, 임베딩·콘텐츠 라이브러리 연결·검색 API가 없음 - 발표 현장 Q&A 기록이 체계적으로 축적·검색되지 않아, 다음 제안서 작성 시 활용 불가
- 1-2. 목적 발표 후 Q&A 기록을 **콘텐츠 라이브러리** 및 **교훈 아카이브**에 검색 가능하게 저장하여: 1. 과거 Q&A를 시맨틱 검색으로 빠르게 찾기 2. 유사 프로젝트 제안 시 예상 질문/답변 참고 3. 조직 지식 선순환 구조 완성
