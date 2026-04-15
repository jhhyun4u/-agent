# Gap Analysis: Bidding 모듈 리스트럭처링 (bidding-restructure) & 1. Directory Structure — 24/24 파일 존재 (100%)
Cohesion: 0.22 | Nodes: 9

## Key Nodes
- **Gap Analysis: Bidding 모듈 리스트럭처링 (bidding-restructure)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\bidding-restructure.analysis.md) -- 8 connections
  - -> contains -> [[overall-scores]]
  - -> contains -> [[1-directory-structure-2424-100]]
  - -> contains -> [[2-compatibility-wrappers-2020-100]]
  - -> contains -> [[3-internal-import-fixes-1111-100]]
  - -> contains -> [[4-2727-100]]
  - -> contains -> [[5]]
  - -> contains -> [[6]]
  - -> contains -> [[7]]
- **1. Directory Structure — 24/24 파일 존재 (100%)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\bidding-restructure.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-bidding-bidding-restructure]]
- **2. Compatibility Wrappers — 20/20 래퍼 (100%)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\bidding-restructure.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-bidding-bidding-restructure]]
- **3. Internal Import Fixes — 11/11 변경 (100%)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\bidding-restructure.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-bidding-bidding-restructure]]
- **4. 외부 참조 호환 — 27/27 작동 (100%)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\bidding-restructure.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-bidding-bidding-restructure]]
- **5. 변경 사항 (설계 != 구현)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\bidding-restructure.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-bidding-bidding-restructure]]
- **6. 잔여 이슈: **없음**** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\bidding-restructure.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-bidding-bidding-restructure]]
- **7. 권장 사항** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\bidding-restructure.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-bidding-bidding-restructure]]
- **Overall Scores** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\bidding-restructure.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-bidding-bidding-restructure]]

## Internal Relationships
- Gap Analysis: Bidding 모듈 리스트럭처링 (bidding-restructure) -> contains -> Overall Scores [EXTRACTED]
- Gap Analysis: Bidding 모듈 리스트럭처링 (bidding-restructure) -> contains -> 1. Directory Structure — 24/24 파일 존재 (100%) [EXTRACTED]
- Gap Analysis: Bidding 모듈 리스트럭처링 (bidding-restructure) -> contains -> 2. Compatibility Wrappers — 20/20 래퍼 (100%) [EXTRACTED]
- Gap Analysis: Bidding 모듈 리스트럭처링 (bidding-restructure) -> contains -> 3. Internal Import Fixes — 11/11 변경 (100%) [EXTRACTED]
- Gap Analysis: Bidding 모듈 리스트럭처링 (bidding-restructure) -> contains -> 4. 외부 참조 호환 — 27/27 작동 (100%) [EXTRACTED]
- Gap Analysis: Bidding 모듈 리스트럭처링 (bidding-restructure) -> contains -> 5. 변경 사항 (설계 != 구현) [EXTRACTED]
- Gap Analysis: Bidding 모듈 리스트럭처링 (bidding-restructure) -> contains -> 6. 잔여 이슈: **없음** [EXTRACTED]
- Gap Analysis: Bidding 모듈 리스트럭처링 (bidding-restructure) -> contains -> 7. 권장 사항 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Gap Analysis: Bidding 모듈 리스트럭처링 (bidding-restructure), 1. Directory Structure — 24/24 파일 존재 (100%), 2. Compatibility Wrappers — 20/20 래퍼 (100%)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 bidding-restructure.analysis.md이다.

### Key Facts
- **분석일**: 2026-03-24 **설계 기준**: `docs/02-design/features/bidding-restructure.design.md` **계획 기준**: `docs/01-plan/features/bidding-restructure.plan.md` **Match Rate**: **98%**
- | # | 설계 경로 | 존재 | |---|----------|:----:| | 1 | `bidding/__init__.py` | PASS | | 2 | `bidding/calculator.py` | PASS | | 3-8 | `bidding/monitor/` (6파일) | PASS | | 9-18 | `bidding/pricing/` (10파일) | PASS | | 19-22 | `bidding/submission/` (4파일) | PASS | | 23-24 | `bidding/artifacts/` (2파일) | PASS |
- 서비스 래퍼 10개 + pricing 래퍼 10개 전부 `sys.modules` redirect 방식으로 구현.
- pricing 내부 8건 + monitor 내부 2건 + submission 내부 1건 전부 새 경로로 수정. `app/services/bidding/` 내부에서 구 경로 사용: 0건.
- 13개 파일의 27개 import문이 래퍼를 경유하여 정상 작동.
