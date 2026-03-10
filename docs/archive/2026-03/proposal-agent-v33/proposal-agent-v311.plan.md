# Plan: 용역 제안서 자동 생성 에이전트 v3.1.1 완성

## 메타 정보

| 항목 | 내용 |
|------|------|
| Feature | proposal-agent-v311 |
| 작성일 | 2026-03-05 |
| 현재 버전 | v3.1.1 (Phase 기반 Multi-Agent) |
| 상태 | 구현 진행 중 — Phase 실행 로직 미완성 |
| 우선순위 | High |

---

## 1. 현황 분석 (CLAUDE.md vs 실제 코드 비교)

### 1.1 CLAUDE.md 문제점

CLAUDE.md는 **v1.0 기준**으로 작성되어 실제 코드와 큰 괴리가 있음.

| 항목 | CLAUDE.md 기술 내용 | 실제 코드 상태 |
|------|---------------------|----------------|
| 모델 | claude-sonnet-4-5-20250929 | 동일 (일치) |
| DB | 미기재 | Supabase 연동 완료 |
| 구조 | routes.py 단일 라우터 | routes.py / routes_v3.py / routes_v31.py / routes_legacy.py 4개 버전 |
| 아키텍처 | 단순 DOCX/PPTX 생성 | v3.1.1 Phase 기반 5단계 Multi-Agent |
| 핵심 패키지 | PyPDF2, python-docx, python-pptx | + LangGraph, Supabase, claude-optimizer |
| 서버 실행 | uv run uvicorn app.main:app | main.py에 외부 모듈 import 오류 발생 가능 |

### 1.2 실제 구현 완료 항목

- [x] FastAPI 기본 서버 구조 (`app/main.py`)
- [x] RFP 파서 (`app/services/rfp_parser.py`)
- [x] Claude 기반 제안서 생성기 (`app/services/proposal_generator.py`)
- [x] DOCX 빌더 (`app/services/docx_builder.py`)
- [x] PPTX 빌더 (`app/services/pptx_builder.py`)
- [x] 세션 매니저 (`app/services/session_manager.py`)
- [x] Supabase 클라이언트 (`app/utils/supabase_client.py`)
- [x] v3.1.1 API 엔드포인트 골격 (`app/api/routes_v31.py`)
- [x] 5-Phase 설계 문서 (`docs/PHASE_CONTEXT_MANAGEMENT_v3.1.1.md`)
- [x] Pydantic 스키마 (`app/models/schemas.py`)
- [x] 설정 관리 (`app/config.py`) — 토큰 최적화, HITL, Supabase 포함

### 1.3 미완성 / 문제 항목

- [ ] **main.py import 오류**: `from graph import build_supervisor_graph`, `from tools import create_default_registry`, `from config.claude_optimizer import TokenUsageTracker` — 해당 모듈 존재 여부 불확실
- [ ] **Phase 실행 로직이 Mock**: `/execute` 엔드포인트가 단순 카운터만 올리고 Claude API 실제 호출 없음
- [ ] **routes 버전 혼재**: legacy, v3, v3.1, routes_test 4개 공존 — 어떤 것을 사용해야 하는지 불명확
- [ ] **CLAUDE.md 미갱신**: v3.1.1 실제 구조 반영 안 됨
- [ ] **LangGraph 그래프 미구현**: `build_phased_supervisor_graph()` 호출하나 실제 그래프 로직 불확실
- [ ] **Sub-agent 미구현**: 5개 Sub-agent (RFP 분석, 전략, 섹션, 품질, 문서) 구현 상태 불확실

---

## 2. 목표

### 2.1 최종 목표
RFP를 입력하면 5-Phase 파이프라인을 통해 **실제 Claude API를 호출**하여 고품질 제안서(DOCX + PPTX)를 자동 생성한다.

### 2.2 단계별 목표

#### Phase A — 기반 안정화 (즉시)
1. `main.py` import 오류 해결 — 서버가 정상 기동되도록
2. routes 버전 정리 — 단일 진입점 확립
3. CLAUDE.md 갱신 — 현재 v3.1.1 구조 반영

#### Phase B — Phase 실행 로직 구현 (핵심)
1. Phase 1 (Research): RFP 파싱 + Supabase 이력 조회
2. Phase 2 (Analysis): Claude API로 RFP 구조화 분석
3. Phase 3 (Plan): 전략 메시지 + 섹션 계획 생성
4. Phase 4 (Implement): 섹션별 본문 생성 (병렬)
5. Phase 5 (Test): 품질 검증 + 최종 문서 생성

#### Phase C — 완성도 향상
1. HITL 게이트 실제 구현 (Phase 3, Phase 5 필수)
2. 토큰 최적화 (프롬프트 캐싱, 예산 제어)
3. 오류 복구 (Phase 단위 롤백)
4. 테스트 커버리지 확보

---

## 3. 기술 스택 (갱신)

```
언어/프레임워크:
- Python 3.11+ / FastAPI (async/await)
- uv (패키지 관리)

AI:
- Anthropic Claude API (claude-sonnet-4-5-20250929)
  - Phase별 토큰 예산 제어 (max 60K/Phase)
  - 프롬프트 캐싱 활성화
  - Extended Thinking (Phase 2, 3)

오케스트레이션:
- LangGraph (Supervisor + Sub-agent 그래프)
- 5-Phase 컨텍스트 격리 모델

데이터:
- Supabase (제안 이력, 인력 DB, 세션)
- 인메모리 세션 매니저 (현재)

문서 생성:
- python-docx (DOCX)
- python-pptx (PPTX)
- PyPDF2 (RFP 파싱)
```

---

## 4. 아키텍처 구조 (현재 기준)

```
app/
├── main.py                    # FastAPI 진입점 (v3.0 lifespan)
├── config.py                  # 설정 (Supabase, 토큰, HITL)
├── exceptions.py              # 커스텀 예외
├── api/
│   ├── routes.py              # [현재 사용] 기본 라우터
│   ├── routes_v31.py          # [목표] v3.1.1 Phase API
│   ├── routes_v3.py           # [레거시]
│   └── routes_legacy.py       # [레거시]
├── services/
│   ├── proposal_generator.py  # Claude API 호출
│   ├── rfp_parser.py          # RFP 문서 파싱
│   ├── docx_builder.py        # Word 문서 생성
│   ├── pptx_builder.py        # PPT 생성
│   └── session_manager.py     # 세션 상태 관리
├── models/schemas.py          # Pydantic v2 스키마
├── prompts/proposal.py        # 프롬프트 템플릿
└── utils/
    ├── supabase_client.py     # Supabase 연결
    ├── claude_utils.py        # Claude API 유틸
    └── file_utils.py          # 파일 처리
```

---

## 5. 작업 우선순위

### 즉시 처리 (Critical)

| 순위 | 작업 | 예상 난이도 |
|------|------|-------------|
| 1 | main.py 외부 모듈 import 오류 확인 및 수정 | 중 |
| 2 | 서버 기동 테스트 (`uv run uvicorn app.main:app`) | 낮 |
| 3 | routes 버전 정리 (v3.1 단일화) | 중 |

### 핵심 구현 (High Priority)

| 순위 | 작업 | 예상 난이도 |
|------|------|-------------|
| 4 | Phase 1-2: RFP 파싱 + 분석 Claude 호출 연결 | 높 |
| 5 | Phase 3: 전략 생성 Claude 호출 연결 | 높 |
| 6 | Phase 4: 섹션 본문 생성 (병렬) | 높 |
| 7 | Phase 5: 품질 검증 + DOCX/PPTX 출력 | 높 |

### 품질 향상 (Medium Priority)

| 순위 | 작업 | 예상 난이도 |
|------|------|-------------|
| 8 | HITL 게이트 구현 (Phase 3, 5) | 중 |
| 9 | Supabase 이력 조회 연동 | 중 |
| 10 | CLAUDE.md 갱신 | 낮 |
| 11 | 테스트 커버리지 확보 | 중 |

---

## 6. 제약 조건

- 각 Phase 컨텍스트는 **60K 토큰 이하** 유지 (200K 한도의 30%)
- Phase 간 정보 전달은 **PhaseArtifact 구조체**로만 (원본 전달 금지)
- HITL Gate #3 (전략 확정), #5 (최종 제출)은 **사람 승인 필수**
- 한국어 docstring 및 주석 유지 (코드 컨벤션)
- Pydantic v2 스타일, async/await 패턴

---

## 7. 성공 기준

1. `uv run uvicorn app.main:app --reload` 오류 없이 기동
2. `/api/v3.1/proposals/generate` 호출 시 실제 Claude API 5-Phase 실행
3. DOCX + PPTX 파일 정상 생성 및 다운로드
4. Phase별 진행 상태를 `/status` API로 실시간 조회 가능
5. 테스트 통과율 80% 이상

---

## 8. 다음 단계

```
현재 상태: Plan 완료
다음 단계: /pdca design proposal-agent-v311
           (Phase 실행 로직 상세 설계)
```
