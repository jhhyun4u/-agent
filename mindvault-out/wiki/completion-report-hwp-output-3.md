# Completion Report: hwp-output & 3. 구현 완료 기능
Cohesion: 0.12 | Nodes: 18

## Key Nodes
- **Completion Report: hwp-output** (C:\project\tenopa proposer\-agent-master\docs\04-report\hwp-output.report.md) -- 8 connections
  - -> contains -> [[1]]
  - -> contains -> [[2-pdca]]
  - -> contains -> [[3]]
  - -> contains -> [[4-act]]
  - -> contains -> [[5]]
  - -> contains -> [[6]]
  - -> contains -> [[7-v2]]
  - -> contains -> [[8]]
- **3. 구현 완료 기능** (C:\project\tenopa proposer\-agent-master\docs\04-report\hwp-output.report.md) -- 6 connections
  - -> contains -> [[3-1-appserviceshwpxbuilderpy-act-2]]
  - -> contains -> [[3-2-appservicesphaseexecutorpy]]
  - -> contains -> [[3-3-appapiroutesv31py]]
  - -> contains -> [[3-4-frontendappproposalsidpagetsx]]
  - -> contains -> [[3-5-db-databaseschemasql]]
  - <- contains <- [[completion-report-hwp-output]]
- **4. Act 수정 내역** (C:\project\tenopa proposer\-agent-master\docs\04-report\hwp-output.report.md) -- 3 connections
  - -> contains -> [[act-1-db]]
  - -> contains -> [[act-2]]
  - <- contains <- [[completion-report-hwp-output]]
- **2. PDCA 흐름 요약** (C:\project\tenopa proposer\-agent-master\docs\04-report\hwp-output.report.md) -- 2 connections
  - -> has_code_example -> [[text]]
  - <- contains <- [[completion-report-hwp-output]]
- **3-1. `app/services/hwpx_builder.py` (신규 + Act-2 서식 표준화)** (C:\project\tenopa proposer\-agent-master\docs\04-report\hwp-output.report.md) -- 2 connections
  - -> contains -> [[act-2]]
  - <- contains <- [[3]]
- **8. 다음 단계** (C:\project\tenopa proposer\-agent-master\docs\04-report\hwp-output.report.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[completion-report-hwp-output]]
- **Act-2: 서식 표준화 상세 (샘플 분석 기반)** (C:\project\tenopa proposer\-agent-master\docs\04-report\hwp-output.report.md) -- 2 connections
  - <- contains <- [[3-1-appserviceshwpxbuilderpy-act-2]]
  - <- contains <- [[4-act]]
- **bash** (C:\project\tenopa proposer\-agent-master\docs\04-report\hwp-output.report.md) -- 1 connections
  - <- has_code_example <- [[8]]
- **text** (C:\project\tenopa proposer\-agent-master\docs\04-report\hwp-output.report.md) -- 1 connections
  - <- has_code_example <- [[2-pdca]]
- **1. 개요** (C:\project\tenopa proposer\-agent-master\docs\04-report\hwp-output.report.md) -- 1 connections
  - <- contains <- [[completion-report-hwp-output]]
- **3-2. `app/services/phase_executor.py` — 파이프라인 통합** (C:\project\tenopa proposer\-agent-master\docs\04-report\hwp-output.report.md) -- 1 connections
  - <- contains <- [[3]]
- **3-3. `app/api/routes_v31.py` — 다운로드 엔드포인트** (C:\project\tenopa proposer\-agent-master\docs\04-report\hwp-output.report.md) -- 1 connections
  - <- contains <- [[3]]
- **3-4. `frontend/app/proposals/[id]/page.tsx` — 다운로드 버튼** (C:\project\tenopa proposer\-agent-master\docs\04-report\hwp-output.report.md) -- 1 connections
  - <- contains <- [[3]]
- **3-5. DB 스키마 (`database/schema.sql`)** (C:\project\tenopa proposer\-agent-master\docs\04-report\hwp-output.report.md) -- 1 connections
  - <- contains <- [[3]]
- **5. 성공 기준 달성 현황** (C:\project\tenopa proposer\-agent-master\docs\04-report\hwp-output.report.md) -- 1 connections
  - <- contains <- [[completion-report-hwp-output]]
- **6. 품질 지표** (C:\project\tenopa proposer\-agent-master\docs\04-report\hwp-output.report.md) -- 1 connections
  - <- contains <- [[completion-report-hwp-output]]
- **7. 잔여 항목 (v2 이관)** (C:\project\tenopa proposer\-agent-master\docs\04-report\hwp-output.report.md) -- 1 connections
  - <- contains <- [[completion-report-hwp-output]]
- **Act-1 (DB 스키마 갭 수정)** (C:\project\tenopa proposer\-agent-master\docs\04-report\hwp-output.report.md) -- 1 connections
  - <- contains <- [[4-act]]

## Internal Relationships
- 2. PDCA 흐름 요약 -> has_code_example -> text [EXTRACTED]
- 3. 구현 완료 기능 -> contains -> 3-1. `app/services/hwpx_builder.py` (신규 + Act-2 서식 표준화) [EXTRACTED]
- 3. 구현 완료 기능 -> contains -> 3-2. `app/services/phase_executor.py` — 파이프라인 통합 [EXTRACTED]
- 3. 구현 완료 기능 -> contains -> 3-3. `app/api/routes_v31.py` — 다운로드 엔드포인트 [EXTRACTED]
- 3. 구현 완료 기능 -> contains -> 3-4. `frontend/app/proposals/[id]/page.tsx` — 다운로드 버튼 [EXTRACTED]
- 3. 구현 완료 기능 -> contains -> 3-5. DB 스키마 (`database/schema.sql`) [EXTRACTED]
- 3-1. `app/services/hwpx_builder.py` (신규 + Act-2 서식 표준화) -> contains -> Act-2: 서식 표준화 상세 (샘플 분석 기반) [EXTRACTED]
- 4. Act 수정 내역 -> contains -> Act-1 (DB 스키마 갭 수정) [EXTRACTED]
- 4. Act 수정 내역 -> contains -> Act-2: 서식 표준화 상세 (샘플 분석 기반) [EXTRACTED]
- 8. 다음 단계 -> has_code_example -> bash [EXTRACTED]
- Completion Report: hwp-output -> contains -> 1. 개요 [EXTRACTED]
- Completion Report: hwp-output -> contains -> 2. PDCA 흐름 요약 [EXTRACTED]
- Completion Report: hwp-output -> contains -> 3. 구현 완료 기능 [EXTRACTED]
- Completion Report: hwp-output -> contains -> 4. Act 수정 내역 [EXTRACTED]
- Completion Report: hwp-output -> contains -> 5. 성공 기준 달성 현황 [EXTRACTED]
- Completion Report: hwp-output -> contains -> 6. 품질 지표 [EXTRACTED]
- Completion Report: hwp-output -> contains -> 7. 잔여 항목 (v2 이관) [EXTRACTED]
- Completion Report: hwp-output -> contains -> 8. 다음 단계 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Completion Report: hwp-output, 3. 구현 완료 기능, 4. Act 수정 내역를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 hwp-output.report.md이다.

### Key Facts
- 3-1. `app/services/hwpx_builder.py` (신규 + Act-2 서식 표준화)
- ```text [Plan] ✅ → [Design] ✅ → [Do] ✅ → [Check] ✅ → [Act-1] ✅ → [Act-2] ✅ → [Report] ✅ 03-07       03-07        03-07      03-07        03-07        03-07         03-07 ```
- | 기능 | 설명 | |------|------| | `build_hwpx()` | sections dict → .hwpx 파일 동기 생성 | | `build_hwpx_async()` | `asyncio.to_thread` 기반 비동기 래퍼 | | 표지 | 사업명, 입찰공고번호, 제출일, 발주처, 제안업체 | | 평가항목 참조표 | `evaluation_weights` dict 기반 5열 동적 테이블 + 텍스트 폴백 | | 목차 | 4장(Ⅰ~Ⅳ), 7개 소절 고정 목차 | | 본문 기호 체계 | □/❍/☞/【】/- 기호 단계별…
- ```bash Supabase에 schema 적용 (schema.sql 변경사항) Dashboard > SQL Editor 또는 supabase db push
- 샘플 파일 2종 (`O-Prize 사업기획`, `국토교통R&D 파급효과`) XML 분석을 통해 도출한 표준:
