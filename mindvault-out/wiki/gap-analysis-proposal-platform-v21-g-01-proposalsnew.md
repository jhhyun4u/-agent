# Gap Analysis: proposal-platform-v2.1 & G-01: proposals/new 섹션 선택 스텝
Cohesion: 0.50 | Nodes: 4

## Key Nodes
- **Gap Analysis: proposal-platform-v2.1** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2.1\proposal-platform-v2.1.analysis.md) -- 3 connections
  - -> contains -> [[g-01-proposalsnew]]
  - -> contains -> [[g-09-assetextractorpy-ai]]
  - -> contains -> [[g-03-ui]]
- **G-01: proposals/new 섹션 선택 스텝** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2.1\proposal-platform-v2.1.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-proposal-platform-v21]]
- **G-03: 버전 비교 UI** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2.1\proposal-platform-v2.1.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-proposal-platform-v21]]
- **G-09: asset_extractor.py AI 섹션 자동 추출** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-platform-v2.1\proposal-platform-v2.1.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-proposal-platform-v21]]

## Internal Relationships
- Gap Analysis: proposal-platform-v2.1 -> contains -> G-01: proposals/new 섹션 선택 스텝 [EXTRACTED]
- Gap Analysis: proposal-platform-v2.1 -> contains -> G-09: asset_extractor.py AI 섹션 자동 추출 [EXTRACTED]
- Gap Analysis: proposal-platform-v2.1 -> contains -> G-03: 버전 비교 UI [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Gap Analysis: proposal-platform-v2.1, G-01: proposals/new 섹션 선택 스텝, G-03: 버전 비교 UI를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 proposal-platform-v2.1.analysis.md이다.

### Key Facts
- 메타 정보 | 항목 | 내용 | |------|------| | Feature | proposal-platform-v2.1 | | 분석일 | 2026-03-08 | | Plan 문서 | docs/01-plan/features/proposal-platform-v2.1.plan.md | | Match Rate | **97%** | | 상태 | Check 완료 (≥90%) |
- | 항목 | 파일 | 상태 | |------|------|------| | `api.sections.list()` 호출 | `frontend/app/proposals/new/page.tsx:61` | ✅ | | 카테고리별 필터 chips | `frontend/app/proposals/new/page.tsx:287-328` | ✅ | | 섹션 카드 다중 선택 toggle | `frontend/app/proposals/new/page.tsx:347-381` | ✅ | | FormData `section_ids` 제출 |…
- | 항목 | 파일 | 상태 | |------|------|------| | "버전 비교" 탭 추가 | `frontend/app/proposals/[id]/page.tsx:465` | ✅ | | 비교 대상 버전 선택 드롭다운 | `[id]/page.tsx:706-724` | ✅ | | 2-column 레이아웃 | `[id]/page.tsx:745` | ✅ | | Phase별 탭 전환 (양쪽 동시) | `[id]/page.tsx:727-742` | ✅ | | 비교 버전 result 로드 | `[id]/page.tsx:143-153`…
- | 항목 | 파일 | 상태 | |------|------|------| | `extract_sections_from_asset()` async 함수 | `app/services/asset_extractor.py` | ✅ | | Claude API 호출 → 카테고리별 섹션 생성 | `asset_extractor.py:_USER_PROMPT_TEMPLATE` | ✅ | | `sections` 테이블 INSERT | `asset_extractor.py:210-229` | ✅ | |…
