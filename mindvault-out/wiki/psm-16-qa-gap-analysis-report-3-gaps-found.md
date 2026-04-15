# PSM-16 Q&A 검색 가능 저장 — Gap Analysis Report & 3. Gaps Found
Cohesion: 0.25 | Nodes: 8

## Key Nodes
- **PSM-16 Q&A 검색 가능 저장 — Gap Analysis Report** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.analysis.md) -- 5 connections
  - -> contains -> [[1-overall-match-rate-98]]
  - -> contains -> [[2-verification-checklist-design-10]]
  - -> contains -> [[3-gaps-found]]
  - -> contains -> [[4-file-coverage]]
  - -> contains -> [[5-summary]]
- **3. Gaps Found** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.analysis.md) -- 3 connections
  - -> contains -> [[gap-1-medium-knowledgesearchpy-orgid]]
  - -> contains -> [[gap-2-low-qa]]
  - <- contains <- [[psm-16-qa-gap-analysis-report]]
- **1. Overall Match Rate: 98%** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.analysis.md) -- 1 connections
  - <- contains <- [[psm-16-qa-gap-analysis-report]]
- **2. Verification Checklist (Design §10)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.analysis.md) -- 1 connections
  - <- contains <- [[psm-16-qa-gap-analysis-report]]
- **4. File Coverage** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.analysis.md) -- 1 connections
  - <- contains <- [[psm-16-qa-gap-analysis-report]]
- **5. Summary** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.analysis.md) -- 1 connections
  - <- contains <- [[psm-16-qa-gap-analysis-report]]
- **GAP-1 (MEDIUM): knowledge_search.py 키워드 폴백에 org_id 필터 누락** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.analysis.md) -- 1 connections
  - <- contains <- [[3-gaps-found]]
- **GAP-2 (LOW): Q&A 탭 상태 조건 미적용** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\psm-16-qa-search\psm-16-qa-search.analysis.md) -- 1 connections
  - <- contains <- [[3-gaps-found]]

## Internal Relationships
- 3. Gaps Found -> contains -> GAP-1 (MEDIUM): knowledge_search.py 키워드 폴백에 org_id 필터 누락 [EXTRACTED]
- 3. Gaps Found -> contains -> GAP-2 (LOW): Q&A 탭 상태 조건 미적용 [EXTRACTED]
- PSM-16 Q&A 검색 가능 저장 — Gap Analysis Report -> contains -> 1. Overall Match Rate: 98% [EXTRACTED]
- PSM-16 Q&A 검색 가능 저장 — Gap Analysis Report -> contains -> 2. Verification Checklist (Design §10) [EXTRACTED]
- PSM-16 Q&A 검색 가능 저장 — Gap Analysis Report -> contains -> 3. Gaps Found [EXTRACTED]
- PSM-16 Q&A 검색 가능 저장 — Gap Analysis Report -> contains -> 4. File Coverage [EXTRACTED]
- PSM-16 Q&A 검색 가능 저장 — Gap Analysis Report -> contains -> 5. Summary [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 PSM-16 Q&A 검색 가능 저장 — Gap Analysis Report, 3. Gaps Found, 1. Overall Match Rate: 98%를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 psm-16-qa-search.analysis.md이다.

### Key Facts
- > **Feature**: psm-16-qa-search > **Date**: 2026-03-18 > **Design Doc**: `docs/02-design/features/psm-16-qa-search.design.md` (v1.0)
- GAP-1 (MEDIUM): knowledge_search.py 키워드 폴백에 org_id 필터 누락
- | Category | Score | Status | |----------|:-----:|:------:| | DB Migration | 100% | PASS | | Pydantic Schemas | 100% | PASS | | Service Layer | 100% | PASS | | API Endpoints | 100% | PASS | | Workflow Integration | 100% | PASS | | KB Search Integration | 95% | WARN | | Frontend (QaPanel) | 100% |…
- | # | Checklist Item | Status | |---|---------------|:------:| | 1 | POST /api/proposals/{id}/qa — presentation_qa + content_library + embedding | PASS | | 2 | GET /api/proposals/{id}/qa — 시간순 조회 | PASS | | 3 | PUT /api/proposals/{id}/qa/{qa_id} — 임베딩 재생성 + content_library 동기화 | PASS | | 4 | DELETE…
- | 유형 | 파일 | 매칭 | |------|------|:----:| | 신규 | `database/migrations/005_qa_search.sql` | 100% | | 신규 | `app/services/qa_service.py` | 100% | | 신규 | `app/api/routes_qa.py` | 100% | | 신규 | `frontend/components/QaPanel.tsx` | 100% | | 신규 | `frontend/app/kb/qa/page.tsx` | 100% | | 수정 |…
