# Plan: hwp-output & 옵션 A — HWPX XML 직접 생성 (권장 후보)
Cohesion: 0.33 | Nodes: 6

## Key Nodes
- **Plan: hwp-output** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\hwp-output.plan.md) -- 5 connections
  - -> contains -> [[a-hwpx-xml]]
  - -> contains -> [[b-libreoffice]]
  - -> contains -> [[c-python-hwpx]]
  - -> contains -> [[in-scope]]
  - -> contains -> [[out-of-scope]]
- **옵션 A — HWPX XML 직접 생성 (권장 후보)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\hwp-output.plan.md) -- 1 connections
  - <- contains <- [[plan-hwp-output]]
- **옵션 B — LibreOffice 변환** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\hwp-output.plan.md) -- 1 connections
  - <- contains <- [[plan-hwp-output]]
- **옵션 C — python-hwpx 재도입 (개선 버전)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\hwp-output.plan.md) -- 1 connections
  - <- contains <- [[plan-hwp-output]]
- **In Scope** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\hwp-output.plan.md) -- 1 connections
  - <- contains <- [[plan-hwp-output]]
- **Out of Scope** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\hwp-output.plan.md) -- 1 connections
  - <- contains <- [[plan-hwp-output]]

## Internal Relationships
- Plan: hwp-output -> contains -> 옵션 A — HWPX XML 직접 생성 (권장 후보) [EXTRACTED]
- Plan: hwp-output -> contains -> 옵션 B — LibreOffice 변환 [EXTRACTED]
- Plan: hwp-output -> contains -> 옵션 C — python-hwpx 재도입 (개선 버전) [EXTRACTED]
- Plan: hwp-output -> contains -> In Scope [EXTRACTED]
- Plan: hwp-output -> contains -> Out of Scope [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Plan: hwp-output, 옵션 A — HWPX XML 직접 생성 (권장 후보), 옵션 B — LibreOffice 변환를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 hwp-output.plan.md이다.

### Key Facts
- 옵션 B — LibreOffice 변환 - DOCX 생성 후 `libreoffice --headless --convert-to hwp` 명령어로 변환 - 신뢰도 높음, 추가 구현 거의 없음 - 단점: 서버에 LibreOffice 설치 필요 (~300MB), Docker 이미지 용량 증가
- 옵션 C — python-hwpx 재도입 (개선 버전) - 이전 구현의 문제점을 파악 후 올바르게 재사용 - 단점: 이전 실패 이유가 라이브러리 자체 문제일 경우 동일 문제 재발
- Out of Scope - HWP 바이너리(.hwp) 형식 지원 (HWPX XML만 대상) - 복잡한 표/이미지/차트 레이아웃 (텍스트 + 제목 구조만) - HWP 템플릿 기반 스타일링 (2차 작업)
