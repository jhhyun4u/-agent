# 용역 제안서 자동 생성 에이전트

## 프로젝트 개요
RFP(제안요청서) 문서를 업로드하거나 프로젝트 정보를 직접 입력하면, Claude API를 활용하여 DOCX 제안서 + PPTX 요약본을 자동 생성하는 AI 에이전트.

## 기술 스택
- Python 3.11+ / FastAPI
- Anthropic Claude API (claude-sonnet-4-5-20250929)
- Supabase (PostgreSQL 호환 데이터베이스)
- PyPDF2, python-docx, python-pptx
- 패키지 관리: uv

## 주요 명령어
```bash
uv sync                              # 의존성 설치
uv run uvicorn app.main:app --reload  # 개발 서버 실행
uv run pytest                         # 테스트 실행
```

## 구조
- `app/api/routes.py` — API 엔드포인트
- `app/services/rfp_parser.py` — RFP 문서 파싱
- `app/services/proposal_generator.py` — Claude 기반 제안서 생성
- `app/services/docx_builder.py` — Word 문서 빌더
- `app/services/pptx_builder.py` — PPT 문서 빌더
- `app/models/schemas.py` — Pydantic 스키마
- `app/prompts/proposal.py` — 프롬프트 템플릿

## 코드 컨벤션
- 한국어 docstring 및 주석
- Pydantic v2 스타일 사용
- async/await 패턴 (FastAPI)
