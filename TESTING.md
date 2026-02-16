# 테스트 가이드

## 📋 개요

이 프로젝트는 여러 레벨의 테스트를 제공합니다:
- **단위 테스트**: 개별 에이전트 테스트
- **통합 테스트**: 전체 시스템 통합 테스트
- **빌더 테스트**: 문서 생성 기능 테스트

## 🧪 테스트 파일 목록

### 1. 통합 Supervisor 테스트

#### `test_integrated_supervisor_auto.py` ⭐ 추천
**비대화형 자동 테스트** - CI/CD 및 자동화에 적합

```bash
# 기본 모드 (시스템 검증만)
uv run python test_integrated_supervisor_auto.py

# 전체 모드 (API 호출 포함)
uv run python test_integrated_supervisor_auto.py --full
```

**특징:**
- ✅ 자동 실행 (사용자 입력 불필요)
- ✅ 종료 코드 반환 (0=성공, 1=실패)
- ✅ 선택적 API 테스트
- ✅ 환경 변수로 API 키 감지

**테스트 단계:**
1. 시스템 빌드 (5개 Sub-agent + Supervisor)
2. 상태 확인 (노드, 에이전트, HITL 게이트)
3. Mock 데이터 준비
4. 초기 상태 생성
5. (옵션) 전체 워크플로우 실행

---

#### `test_integrated_supervisor.py`
**대화형 테스트** - 수동 테스트 및 디버깅용

```bash
uv run python test_integrated_supervisor.py
```

**특징:**
- 🔄 대화형 실행 확인
- 🔍 단계별 진행 상황 확인
- 💡 사용자가 API 테스트 실행 여부 선택

---

### 2. 전체 에이전트 파이프라인 테스트

#### `test_all_agents.py`
**5개 Sub-agent 순차 실행 테스트**

```bash
uv run python test_all_agents.py
```

**테스트 순서:**
1. RFP 분석 에이전트
2. 전략 수립 에이전트
3. 섹션 생성 에이전트
4. 품질 관리 에이전트
5. 문서 출력 에이전트

**주의:** 실제 Claude API를 호출하므로 유효한 `ANTHROPIC_API_KEY` 필요

---

### 3. 문서 빌더 테스트

#### `test_builders_only.py`
**DOCX/PPTX 생성 기능만 테스트** (API 불필요)

```bash
uv run python test_builders_only.py
```

**특징:**
- ✅ API 키 불필요
- ✅ Mock 데이터 사용
- ✅ 빠른 실행 (수초)
- 📄 실제 DOCX, PPTX 파일 생성

**생성 파일:**
- `output/test_proposal_YYYYMMDD_HHMMSS.docx`
- `output/test_proposal_YYYYMMDD_HHMMSS.pptx`

---

## 🔑 환경 설정

### API 키 설정

전체 워크플로우 테스트를 위해서는 Claude API 키가 필요합니다:

```bash
# .env 파일에 추가
ANTHROPIC_API_KEY=your-api-key-here
```

또는:

```bash
# 환경 변수로 설정
export ANTHROPIC_API_KEY=your-api-key-here  # Linux/Mac
set ANTHROPIC_API_KEY=your-api-key-here     # Windows CMD
$env:ANTHROPIC_API_KEY="your-api-key-here"  # Windows PowerShell
```

---

## 📊 테스트 결과 해석

### ✅ 성공 지표

통합 테스트 성공 시 다음 출력을 확인:

```
[SUCCESS] 통합 Supervisor 시스템 준비 완료!
   - Sub-agent: 5개
   - HITL Gate: 3개
   - 체크포인트: 활성화

[2단계] 시스템 상태 확인
상태: operational
노드: 11개
Sub-agent: 5개
HITL Gate: 3개
체크포인터: memory

[SUCCESS] 테스트 완료!
```

### ❌ 실패 원인

일반적인 실패 원인:

1. **ImportError**: 의존성 설치 필요
   ```bash
   uv sync
   ```

2. **AuthenticationError**: API 키 확인
   ```bash
   # .env 파일 확인
   cat .env | grep ANTHROPIC_API_KEY
   ```

3. **UnicodeEncodeError**: Windows 콘솔 인코딩 문제
   - 해결: 비대화형 테스트(`test_integrated_supervisor_auto.py`) 사용

---

## 🚀 CI/CD 통합

### GitHub Actions 예시

```yaml
name: Test Integrated Supervisor

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: uv sync

      - name: Run integration tests
        run: uv run python test_integrated_supervisor_auto.py
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

---

## 📝 테스트 추가 가이드

새로운 에이전트를 추가했을 때:

1. **개별 에이전트 테스트 작성**
   ```python
   # test_new_agent.py
   from agents import build_new_agent_graph

   async def test_new_agent():
       graph = build_new_agent_graph()
       result = await graph.ainvoke(test_state)
       assert result["status"] == "completed"
   ```

2. **통합 테스트에 추가**
   - `graph/integrated_supervisor.py`에 에이전트 추가
   - `test_integrated_supervisor_auto.py`에 검증 로직 추가

3. **테스트 실행 확인**
   ```bash
   uv run python test_integrated_supervisor_auto.py
   ```

---

## 🐛 디버깅 팁

### 1. 상세 로그 활성화

```bash
# 환경 변수 설정
export LANGCHAIN_VERBOSE=true
export LANGCHAIN_TRACING_V2=true
```

### 2. 개별 노드 테스트

```python
# 특정 노드만 테스트
from agents.rfp_analysis_agent import extract_document_node

state = {"raw_document": "..."}
result = await extract_document_node(state)
print(result)
```

### 3. 그래프 구조 시각화

```python
from graph.integrated_supervisor import build_integrated_supervisor

graph = build_integrated_supervisor()
print(graph.get_graph().draw_ascii())
```

---

## 📈 성능 벤치마크

참고용 실행 시간 (테스트 환경):

| 테스트 | 예상 시간 | API 호출 |
|--------|-----------|----------|
| `test_integrated_supervisor_auto.py` | 2-5초 | ❌ |
| `test_integrated_supervisor_auto.py --full` | 2-5분 | ✅ |
| `test_all_agents.py` | 3-10분 | ✅ |
| `test_builders_only.py` | 1-3초 | ❌ |

---

## 🎯 베스트 프랙티스

1. **로컬 개발**: `test_builders_only.py`로 빠른 검증
2. **통합 검증**: `test_integrated_supervisor_auto.py`로 시스템 확인
3. **전체 테스트**: API 키 설정 후 `--full` 옵션 사용
4. **CI/CD**: 비대화형 테스트만 사용

---

## 📞 문제 해결

문제 발생 시:

1. **의존성 재설치**
   ```bash
   uv sync --reinstall
   ```

2. **캐시 삭제**
   ```bash
   # Python 캐시 삭제
   find . -type d -name __pycache__ -exec rm -rf {} +
   find . -type f -name "*.pyc" -delete
   ```

3. **로그 확인**
   ```bash
   uv run python test_integrated_supervisor_auto.py > test.log 2>&1
   cat test.log
   ```

4. **이슈 리포트**: 문제가 지속되면 로그와 함께 이슈 등록

---

**마지막 업데이트**: 2026-02-16
**테스트 프레임워크**: LangGraph + pytest
**지원 플랫폼**: Windows, Linux, macOS
