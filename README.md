# 용역제안 Coworker

> 프로젝트 수주 성공률을 높이는 AI Coworker

RFP(제안요청서) 분석부터 전략 수립, 제안서 작성까지 — AI 동료와 함께하는 용역 제안 플랫폼입니다.

## 기능

- **RFP 업로드 분석**: PDF/DOCX 형식의 RFP 파일을 업로드하면 자동으로 핵심 정보를 추출합니다.
- **직접 입력**: 프로젝트명, 범위, 기간 등을 직접 입력하여 제안서를 생성할 수 있습니다.
- **DOCX 제안서 생성**: 섹션별로 구조화된 Word 제안서를 생성합니다.
- **PPTX 요약본 생성**: 프레젠테이션용 PPT 요약본을 함께 생성합니다.

## 설치 및 실행

### 사전 요구사항
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) 패키지 매니저

### 설치
```bash
# 의존성 설치
uv sync
```

### 환경 설정
```bash
cp .env.example .env
# .env 파일에 ANTHROPIC_API_KEY 설정
```

### 실행
```bash
uv run uvicorn app.main:app --reload
```

서버 실행 후 http://localhost:8000/docs 에서 Swagger UI를 확인할 수 있습니다.

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/proposals/from-rfp` | RFP 파일 업로드 기반 제안서 생성 |
| POST | `/api/proposals/from-input` | 직접 입력 기반 제안서 생성 |
| GET | `/api/proposals/{id}/download` | 생성된 문서 다운로드 |
| GET | `/health` | 헬스 체크 |
