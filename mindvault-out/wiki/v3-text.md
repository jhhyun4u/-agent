# 제안발표 자료 자동 생성 기능 계획서 (v3) & text
Cohesion: 0.12 | Nodes: 22

## Key Nodes
- **제안발표 자료 자동 생성 기능 계획서 (v3)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\presentation-generator\presentation-generator.plan.md) -- 10 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4-claude]]
  - -> contains -> [[5]]
  - -> contains -> [[6]]
  - -> contains -> [[7]]
  - -> contains -> [[8]]
  - -> contains -> [[9-definition-of-done]]
  - -> contains -> [[10]]
- **text** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\presentation-generator\presentation-generator.plan.md) -- 6 connections
  - <- has_code_example <- [[2]]
  - <- has_code_example <- [[32]]
  - <- has_code_example <- [[33]]
  - <- has_code_example <- [[4-claude]]
  - <- has_code_example <- [[51]]
  - <- has_code_example <- [[52-api]]
- **5. 신규 컴포넌트** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\presentation-generator\presentation-generator.plan.md) -- 5 connections
  - -> contains -> [[51]]
  - -> contains -> [[52-api]]
  - -> contains -> [[53-presentationgeneratorpy]]
  - -> contains -> [[54-presentationpptxbuilderpy]]
  - <- contains <- [[v3]]
- **3. 슬라이드 목차 구성 로직** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\presentation-generator\presentation-generator.plan.md) -- 4 connections
  - -> contains -> [[31-3]]
  - -> contains -> [[32]]
  - -> contains -> [[33]]
  - <- contains <- [[v3]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\presentation-generator\presentation-generator.plan.md) -- 3 connections
  - <- has_code_example <- [[53-presentationgeneratorpy]]
  - <- has_code_example <- [[6]]
  - <- has_code_example <- [[7]]
- **4. Claude 프롬프트 설계** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\presentation-generator\presentation-generator.plan.md) -- 3 connections
  - -> has_code_example -> [[text]]
  - -> contains -> [[json]]
  - <- contains <- [[v3]]
- **2. 데이터 흐름** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\presentation-generator\presentation-generator.plan.md) -- 2 connections
  - -> has_code_example -> [[text]]
  - <- contains <- [[v3]]
- **3.2 가변 슬라이드 — 평가항목 기반 자동 생성** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\presentation-generator\presentation-generator.plan.md) -- 2 connections
  - -> has_code_example -> [[text]]
  - <- contains <- [[3]]
- **3.3 각 슬라이드의 구성 규칙** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\presentation-generator\presentation-generator.plan.md) -- 2 connections
  - -> has_code_example -> [[text]]
  - <- contains <- [[3]]
- **5.1 파일 목록** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\presentation-generator\presentation-generator.plan.md) -- 2 connections
  - -> has_code_example -> [[text]]
  - <- contains <- [[5]]
- **5.2 API 엔드포인트** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\presentation-generator\presentation-generator.plan.md) -- 2 connections
  - -> has_code_example -> [[text]]
  - <- contains <- [[5]]
- **5.3 presentation_generator.py** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\presentation-generator\presentation-generator.plan.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[5]]
- **6. 라우터 등록** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\presentation-generator\presentation-generator.plan.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[v3]]
- **7. 세션 상태 관리** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\presentation-generator\presentation-generator.plan.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[v3]]
- **입력 JSON 구조** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\presentation-generator\presentation-generator.plan.md) -- 2 connections
  - -> has_code_example -> [[json]]
  - <- contains <- [[4-claude]]
- **json** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\presentation-generator\presentation-generator.plan.md) -- 1 connections
  - <- has_code_example <- [[json]]
- **1. 개요** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\presentation-generator\presentation-generator.plan.md) -- 1 connections
  - <- contains <- [[v3]]
- **10. 참조 파일** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\presentation-generator\presentation-generator.plan.md) -- 1 connections
  - <- contains <- [[v3]]
- **3.1 고정 슬라이드 (3장)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\presentation-generator\presentation-generator.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **5.4 presentation_pptx_builder.py — 레이아웃 타입** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\presentation-generator\presentation-generator.plan.md) -- 1 connections
  - <- contains <- [[5]]
- **8. 리스크 & 대응** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\presentation-generator\presentation-generator.plan.md) -- 1 connections
  - <- contains <- [[v3]]
- **9. 완료 기준 (Definition of Done)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\presentation-generator\presentation-generator.plan.md) -- 1 connections
  - <- contains <- [[v3]]

## Internal Relationships
- 2. 데이터 흐름 -> has_code_example -> text [EXTRACTED]
- 3. 슬라이드 목차 구성 로직 -> contains -> 3.1 고정 슬라이드 (3장) [EXTRACTED]
- 3. 슬라이드 목차 구성 로직 -> contains -> 3.2 가변 슬라이드 — 평가항목 기반 자동 생성 [EXTRACTED]
- 3. 슬라이드 목차 구성 로직 -> contains -> 3.3 각 슬라이드의 구성 규칙 [EXTRACTED]
- 3.2 가변 슬라이드 — 평가항목 기반 자동 생성 -> has_code_example -> text [EXTRACTED]
- 3.3 각 슬라이드의 구성 규칙 -> has_code_example -> text [EXTRACTED]
- 4. Claude 프롬프트 설계 -> has_code_example -> text [EXTRACTED]
- 4. Claude 프롬프트 설계 -> contains -> 입력 JSON 구조 [EXTRACTED]
- 5. 신규 컴포넌트 -> contains -> 5.1 파일 목록 [EXTRACTED]
- 5. 신규 컴포넌트 -> contains -> 5.2 API 엔드포인트 [EXTRACTED]
- 5. 신규 컴포넌트 -> contains -> 5.3 presentation_generator.py [EXTRACTED]
- 5. 신규 컴포넌트 -> contains -> 5.4 presentation_pptx_builder.py — 레이아웃 타입 [EXTRACTED]
- 5.1 파일 목록 -> has_code_example -> text [EXTRACTED]
- 5.2 API 엔드포인트 -> has_code_example -> text [EXTRACTED]
- 5.3 presentation_generator.py -> has_code_example -> python [EXTRACTED]
- 6. 라우터 등록 -> has_code_example -> python [EXTRACTED]
- 7. 세션 상태 관리 -> has_code_example -> python [EXTRACTED]
- 입력 JSON 구조 -> has_code_example -> json [EXTRACTED]
- 제안발표 자료 자동 생성 기능 계획서 (v3) -> contains -> 1. 개요 [EXTRACTED]
- 제안발표 자료 자동 생성 기능 계획서 (v3) -> contains -> 2. 데이터 흐름 [EXTRACTED]
- 제안발표 자료 자동 생성 기능 계획서 (v3) -> contains -> 3. 슬라이드 목차 구성 로직 [EXTRACTED]
- 제안발표 자료 자동 생성 기능 계획서 (v3) -> contains -> 4. Claude 프롬프트 설계 [EXTRACTED]
- 제안발표 자료 자동 생성 기능 계획서 (v3) -> contains -> 5. 신규 컴포넌트 [EXTRACTED]
- 제안발표 자료 자동 생성 기능 계획서 (v3) -> contains -> 6. 라우터 등록 [EXTRACTED]
- 제안발표 자료 자동 생성 기능 계획서 (v3) -> contains -> 7. 세션 상태 관리 [EXTRACTED]
- 제안발표 자료 자동 생성 기능 계획서 (v3) -> contains -> 8. 리스크 & 대응 [EXTRACTED]
- 제안발표 자료 자동 생성 기능 계획서 (v3) -> contains -> 9. 완료 기준 (Definition of Done) [EXTRACTED]
- 제안발표 자료 자동 생성 기능 계획서 (v3) -> contains -> 10. 참조 파일 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 제안발표 자료 자동 생성 기능 계획서 (v3), text, 5. 신규 컴포넌트를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 presentation-generator.plan.md이다.

### Key Facts
- ```text [Phase 2]  evaluation_weights       ← 평가항목별 배점 (예: 기술능력:40, 수행계획:30, 가격:30) evaluator_perspective     ← 평가위원 판단 기준, 선호 도급사 프로파일
- ```python async def generate_presentation_slides( phase2: Phase2Artifact, phase3: Phase3Artifact, phase4: Phase4Artifact, rfp_data: RFPData, ) -> dict: """ 평가항목(Phase2) + 전략(Phase3) + 제안서 본문(Phase4) → 평가항목 배점 순 슬라이드 JSON 반환 """ ```
- ```text [Phase 2]  evaluation_weights       ← 평가항목별 배점 (예: 기술능력:40, 수행계획:30, 가격:30) evaluator_perspective     ← 평가위원 판단 기준, 선호 도급사 프로파일
- ```text section_plan[]을 score_weight 내림차순 정렬 → 배점 15점 이상: 전용 슬라이드 1장 → 배점 10~14점 : 전용 슬라이드 1장 (bullet 압축) → 배점 9점 이하 : 유사 섹션과 병합하여 1장 공유 ```
- ```text 슬라이드 제목 헤더에 표기: [평가항목명 | 배점 XX점]
