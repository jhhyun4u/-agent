# 테스트 가이드

## 테스트 구조

```
tests/
├── unit/                   # 단위 테스트
│   ├── test_document_builders.py    # DOCX/PPTX 빌더 테스트 (API 키 불필요)
│   ├── test_rfp_agent.py            # RFP 분석 에이전트 테스트
│   └── test_mcp_server.py           # MCP 서버 메모리 모드 테스트
├── integration/            # 통합 테스트
│   ├── test_agent_pipeline.py       # 전체 5개 에이전트 파이프라인
│   └── test_workflow.py             # 입력→생성→문서 전체 워크플로우
├── api/                    # API 테스트
│   └── test_v31_endpoints.py        # API v3.1 HTTP 테스트
├── fixtures/               # 테스트 데이터
│   └── test_request.json            # API 테스트 데이터
└── conftest.py             # pytest 공통 설정 및 fixtures
```

## 테스트 실행

### 전체 테스트 실행
```bash
uv run pytest
```

### 단위 테스트만 실행 (API 키 불필요)
```bash
uv run pytest tests/unit/test_document_builders.py
uv run pytest tests/unit/test_mcp_server.py
```

### 통합 테스트 실행 (API 키 필요)
```bash
uv run pytest tests/integration/
```

### API 테스트 실행 (서버 실행 필요)
```bash
# 터미널 1: 서버 실행
uv run uvicorn app.main:app --reload

# 터미널 2: API 테스트
uv run python tests/api/test_v31_endpoints.py
```

### 특정 테스트만 실행
```bash
uv run pytest tests/unit/test_document_builders.py::test_document_builders
```

### 커버리지 포함 실행
```bash
uv run pytest --cov=app --cov-report=html
```

## 테스트 분류

### ✅ API 키 불필요 (즉시 실행 가능)
- `tests/unit/test_document_builders.py` - DOCX/PPTX 빌더
- `tests/unit/test_mcp_server.py` - MCP 서버 메모리 모드

### 🔑 API 키 필요 (.env 설정 필요)
- `tests/unit/test_rfp_agent.py` - RFP 분석 에이전트
- `tests/integration/test_agent_pipeline.py` - 전체 에이전트 파이프라인
- `tests/integration/test_workflow.py` - 전체 워크플로우

### 🌐 서버 실행 필요
- `tests/api/test_v31_endpoints.py` - API v3.1 엔드포인트

## 환경 설정

### API 키 설정
```bash
# .env 파일에 추가
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

### 테스트 출력 디렉토리
생성된 테스트 파일은 `output/` 디렉토리에 저장됩니다.

## 주의사항

- 통합 테스트는 실제 Claude API를 호출하므로 비용이 발생할 수 있습니다
- API 테스트 실행 전 서버가 실행 중인지 확인하세요
- 테스트 실행 전 의존성을 설치하세요: `uv sync`
