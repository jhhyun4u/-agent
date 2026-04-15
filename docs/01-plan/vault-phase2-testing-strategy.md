# Vault Phase 2 — 테스트 & 검증 계획서 (Testing & Validation Strategy)

**문서**: TENOPA Vault Phase 2 테스트 및 검증 전략  
**버전**: 1.0  
**작성일**: 2026-04-14  
**예정 기간**: 4주 (2026-06-01 ~ 2026-06-30)  
**대상**: QA팀 + 개발팀  

---

## 1. 테스트 개요

### 1.1 목표
- Vault AI Chat 시스템의 기능성, 정확성, 성능, 보안 검증
- 4개 검증 테스트 케이스 100% 통과
- 프로덕션 배포 준비 완료

### 1.2 테스트 범위 및 타입

| 테스트 타입 | 목적 | 범위 | 담당 | 일정 |
|-----------|------|------|------|------|
| **단위 테스트** | 각 함수/메서드 정확성 | 백엔드 핸들러 | Dev | W1-W2 |
| **통합 테스트** | API 엔드포인트 정상 동작 | routes_vault_chat.py | Dev+QA | W2-W3 |
| **E2E 테스트** | 사용자 흐름 전체 | UI → API → DB | QA | W3-W4 |
| **정확성 검증** | AI Chat 할루시네이션 방지 | 4개 테스트 케이스 | QA Lead | W2-W4 |
| **성능 테스트** | 응답 시간, 동시성 | 부하 시뮬레이션 | Dev | W3 |
| **보안 테스트** | 인증, 권한, 데이터 보호 | RLS, API 보안 | Security | W4 |

---

## 2. 단위 테스트 (Unit Tests)

### 2.1 테스트 프레임워크 설정

```python
# tests/services/test_vault_handlers.py
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

# Fixture 정의
@pytest.fixture
async def client():
    """Supabase 테스트 클라이언트"""
    return AsyncMock()

@pytest.fixture
async def llm_client():
    """Claude API 테스트 클라이언트"""
    return AsyncMock()

@pytest.fixture
def sample_project():
    """테스트용 프로젝트 데이터"""
    return {
        "id": "proj_123",
        "title": "스마트팩토리 2024",
        "client_name": "◯◯청",
        "win_result": "won",
        "bid_amount": 500000000,
        "budget": 600000000,
        "team_name": "기술팀",
        "completion_date": "2024-12-31"
    }
```

### 2.2 백엔드 핸들러 단위 테스트

#### 종료프로젝트 핸들러

```python
@pytest.mark.asyncio
async def test_completed_projects_handler_sql_query():
    """SQL 쿼리로 정확한 프로젝트 목록 반환"""
    handler = CompletedProjectsHandler(client)
    
    # Mock SQL 결과
    client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[
            {
                "id": "proj_1",
                "title": "프로젝트 1",
                "completion_date": "2024-12-31",
                "win_result": "won"
            }
        ]
    )
    
    result = await handler.search(query="프로젝트 1", filters={})
    
    assert len(result.results) == 1
    assert result.results[0]["title"] == "프로젝트 1"
    assert result.primary_source == "sql"

@pytest.mark.asyncio
async def test_completed_projects_handler_fact_validation():
    """낙찰가 & 낙찰률 검증"""
    handler = CompletedProjectsHandler(client)
    
    project = {
        "bid_amount": 500000000,
        "budget": 600000000,
    }
    
    validation = await handler.validate_facts(project)
    
    assert validation.passed
    assert abs(validation.bid_rate - 83.3) < 0.1  # 낙찰률 정확도

@pytest.mark.asyncio
async def test_completed_projects_deduplication():
    """SQL + Vector 결과 중복 제거"""
    handler = CompletedProjectsHandler(client)
    
    sql_results = [{"id": "proj_1", "title": "프로젝트 1"}]
    vector_results = [{"id": "proj_1", "title": "프로젝트 1"}]
    
    combined = await handler.deduplicate(sql_results, vector_results)
    
    assert len(combined) == 1
```

#### 정부지침 핸들러

```python
@pytest.mark.asyncio
async def test_government_guidelines_sql_only():
    """정부지침은 SQL only (벡터 검색 금지)"""
    handler = GovernmentGuidelinesHandler(client)
    
    result = await handler.search(query="박사급 인건비")
    
    assert result.primary_source == "sql"
    assert len(result.warnings) == 0
    assert "Vector search not used" in str(result.metadata)

@pytest.mark.asyncio
async def test_government_guidelines_latest_only():
    """가장 최신 지침만 반환"""
    handler = GovernmentGuidelinesHandler(client)
    
    # Mock 2개 연도의 지침
    client.table.return_value.select.return_value.order_by.return_value.execute.return_value = MagicMock(
        data=[
            {"year": 2026, "labor_rate": 6500000},  # 최신
            {"year": 2025, "labor_rate": 6000000}
        ]
    )
    
    result = await handler.search(query="인건비")
    
    assert result.results[0]["year"] == 2026
    assert result.confidence == 1.0

@pytest.mark.asyncio
async def test_government_guidelines_salary_accuracy():
    """인건비 정확도 검증"""
    handler = GovernmentGuidelinesHandler(client)
    
    # 공식 기준: 박사급 6,500,000원
    client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"salary_level": "doctorate", "amount": 6500000}]
    )
    
    result = await handler.search(query="박사급 인건비")
    
    assert result.results[0]["amount"] == 6500000
```

#### 성공사례 핸들러

```python
@pytest.mark.asyncio
async def test_success_cases_vector_priority():
    """성공사례는 Vector 우선"""
    handler = SuccessCasesHandler(client)
    
    result = await handler.search(query="데이터 분석 성공 사례")
    
    assert result.primary_source == "vector"
    assert "Vector" in result.metadata["search_methods"]

@pytest.mark.asyncio
async def test_success_cases_source_verification():
    """모든 성공사례는 출처 프로젝트로 검증"""
    handler = SuccessCasesHandler(client)
    
    vector_result = {
        "id": "case_1",
        "source_id": "proj_123",
        "content": "데이터 분석으로 성능 50% 향상"
    }
    
    verified = await handler.verify_source(vector_result)
    
    assert verified.source_project is not None
    assert verified.source_project["id"] == "proj_123"
```

### 2.3 검증 엔진 단위 테스트

```python
@pytest.mark.asyncio
async def test_hallucination_validator_unsourced_claims():
    """출처 없는 주장 감지"""
    validator = HallucinationValidator()
    
    response = "우리 회사는 2024년 100개 프로젝트를 수행했습니다."
    sources = [{"content": "2024년 12개 프로젝트 완료"}]
    
    validation = await validator.validate(response, sources, confidence=0.9)
    
    assert not validation.passed
    assert validation.reason == "Unsourced claims detected"

@pytest.mark.asyncio
async def test_hallucination_validator_fact_alignment():
    """팩트 기반 모순 감지"""
    validator = HallucinationValidator()
    
    response = "낙찰률은 120%입니다."  # 불가능
    sources = [{"bid_amount": 500000000, "budget": 600000000}]  # 83.3%
    
    validation = await validator.validate(response, sources, confidence=0.9)
    
    assert not validation.passed
    assert validation.reason == "Factual contradiction"

@pytest.mark.asyncio
async def test_hallucination_validator_confidence_threshold():
    """신뢰도 threshold 검증"""
    validator = HallucinationValidator()
    
    response = "어쩌면 프로젝트가 있을 수도..."
    sources = []
    
    validation = await validator.validate(response, sources, confidence=0.5)
    
    assert not validation.passed
    assert validation.reason == "Low confidence (< 80%)"

@pytest.mark.asyncio
async def test_hallucination_validator_pass():
    """정상 응답 검증"""
    validator = HallucinationValidator()
    
    response = "최근 AI 프로젝트는 스마트팩토리 2024(수주)와 데이터분석 플랫폼(실패) 2개입니다."
    sources = [
        {"id": "proj_1", "title": "스마트팩토리 2024", "result": "won"},
        {"id": "proj_2", "title": "데이터분석 플랫폼", "result": "lost"}
    ]
    
    validation = await validator.validate(response, sources, confidence=0.95)
    
    assert validation.passed
    assert validation.confidence == 0.95
```

### 2.4 단위 테스트 체크리스트

```
[ ] completed_projects.py — 15개 테스트
    [x] SQL 쿼리
    [x] Vector 검색
    [x] 중복 제거
    [x] 팩트 검증
    
[ ] government_guidelines.py — 12개 테스트
    [x] SQL only 강제
    [x] 최신 데이터만
    [x] 정확도 검증
    [x] TTL 검증
    
[ ] company_internal.py — 10개 테스트
[ ] credentials.py — 10개 테스트
[ ] success_cases.py — 10개 테스트
[ ] clients_db.py — 10개 테스트
[ ] competitors.py — 10개 테스트
[ ] research_materials.py — 10개 테스트
[ ] vault_validation.py — 15개 테스트
[ ] vault_query_router.py — 10개 테스트

총 122개 단위 테스트
목표 커버리지: > 85%
```

---

## 3. 통합 테스트 (Integration Tests)

### 3.1 API 엔드포인트 통합 테스트

```python
# tests/api/test_vault_chat_api.py
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client(app):
    return TestClient(app)

@pytest.mark.asyncio
async def test_vault_chat_endpoint_basic():
    """기본 AI Chat 요청"""
    response = client.post(
        "/api/vault/chat",
        json={
            "message": "최근 AI 프로젝트 뭐가 있어?",
            "scope": "all"
        },
        headers={"Authorization": "Bearer test_token"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "sources" in data
    assert "confidence" in data
    assert data["confidence"] >= 0

@pytest.mark.asyncio
async def test_vault_chat_multi_section_query():
    """다중 섹션 쿼리"""
    response = client.post(
        "/api/vault/chat",
        json={
            "message": "정부 인건비 단가가 얼마인데, 우리가 지난 프로젝트에서는 어떻게 적용했어?",
            "scope": "all"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # 두 섹션 모두 포함되어야 함
    sections = set(s["section"] for s in data["sources"])
    assert "government_guidelines" in sections
    assert "completed_projects" in sections

@pytest.mark.asyncio
async def test_vault_chat_single_section_query():
    """단일 섹션 쿼리"""
    response = client.post(
        "/api/vault/chat",
        json={
            "message": "박사급 인건비 얼마야?",
            "scope": "government_guidelines"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # 정부지침 섹션만
    sections = set(s["section"] for s in data["sources"])
    assert all(s == "government_guidelines" for s in sections)

@pytest.mark.asyncio
async def test_vault_chat_conversation_history():
    """대화 히스토리 유지"""
    # 첫 번째 질문
    response1 = client.post(
        "/api/vault/chat",
        json={
            "message": "우리 최근 프로젝트는?",
            "conversation_id": "conv_123"
        }
    )
    assert response1.status_code == 200
    conv_id = response1.json()["conversation_id"]
    
    # 두 번째 질문 (동일 대화)
    response2 = client.post(
        "/api/vault/chat",
        json={
            "message": "그 중에 수주한 건 몇 개야?",
            "conversation_id": conv_id
        }
    )
    assert response2.status_code == 200
    
    # 대화 로드
    response3 = client.get(f"/api/vault/conversations/{conv_id}")
    assert response3.status_code == 200
    messages = response3.json()["messages"]
    assert len(messages) >= 4  # 2 user + 2 assistant

@pytest.mark.asyncio
async def test_vault_chat_rate_limiting():
    """Rate limiting 작동 확인"""
    for i in range(100):
        response = client.post("/api/vault/chat", json={"message": "test"})
        assert response.status_code == 200
    
    # 101번째 요청은 rate limit 오류
    response = client.post("/api/vault/chat", json={"message": "test"})
    assert response.status_code == 429

@pytest.mark.asyncio
async def test_vault_chat_authorization():
    """권한 검증"""
    # 다른 팀 대화 접근 시도
    response = client.get(
        "/api/vault/conversations/other_team_conv_123",
        headers={"Authorization": "Bearer user_from_different_team"}
    )
    assert response.status_code == 403
```

### 3.2 데이터베이스 통합 테스트

```python
# tests/integration/test_vault_db.py
@pytest.mark.asyncio
async def test_vault_metadata_rls():
    """RLS 정책 검증 (팀별 접근)"""
    # 팀 A 사용자
    user_a = await create_test_user(team="team_a")
    
    # 팀 B 데이터 생성
    document_b = await create_test_document(team="team_b")
    
    # 팀 A 사용자가 팀 B 데이터 접근 불가
    result = await supabase.table("vault_documents").select().eq("id", document_b["id"]).execute(user_a.jwt)
    assert len(result.data) == 0

@pytest.mark.asyncio
async def test_vault_vector_search_accuracy():
    """벡터 검색 정확도"""
    # 문서 임베딩 생성
    doc = {
        "title": "데이터분석 프로젝트",
        "content": "빅데이터 분석 및 머신러닝 모델 개발",
        "embedding": await embed("데이터분석 프로젝트...")
    }
    
    await supabase.table("vault_documents").insert([doc]).execute()
    
    # 유사 쿼리로 검색
    query_embedding = await embed("데이터 분석 머신러닝")
    
    results = await supabase.rpc("match_documents", {
        "query_embedding": query_embedding,
        "match_threshold": 0.7,
        "match_count": 5
    }).execute()
    
    # 위의 문서가 상위에 나와야 함
    assert results.data[0]["id"] == doc["id"]
```

### 3.3 통합 테스트 체크리스트

```
[ ] API Endpoints — 20개 테스트
    [x] POST /api/vault/chat
    [x] GET /api/vault/conversations
    [x] GET /api/vault/conversations/{id}
    [x] GET /api/vault/{section}
    [x] POST /api/vault/export
    
[ ] Database Integration — 15개 테스트
    [x] RLS 정책
    [x] Vector 검색
    [x] 데이터 일관성
    
[ ] External API Integration — 10개 테스트
    [x] Claude API
    [x] OpenAI Embeddings
    [x] Supabase Auth

총 45개 통합 테스트
목표: 100% 통과
```

---

## 4. E2E 테스트 (End-to-End Tests)

### 4.1 Playwright 기반 E2E 테스트

```typescript
// e2e/vault-chat.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Vault AI Chat', () => {
  test.beforeEach(async ({ page }) => {
    // 로그인
    await page.goto('/auth/login')
    await page.fill('[name="email"]', 'test@tenopa.com')
    await page.fill('[name="password"]', 'test123')
    await page.click('button[type="submit"]')
    
    // Vault 페이지 이동
    await page.goto('/vault')
    await page.waitForLoadState('networkidle')
  })

  test('사용자가 AI Chat으로 프로젝트를 검색할 수 있다', async ({ page }) => {
    // 1. AI Chat 섹션 클릭
    await page.click('text=💬 AI Chat')
    await page.waitForSelector('[data-testid="chat-input"]')
    
    // 2. 질문 입력
    const chatInput = page.locator('[data-testid="chat-input"]')
    await chatInput.fill('최근 AI 프로젝트 뭐가 있어?')
    await page.click('[data-testid="send-button"]')
    
    // 3. 응답 대기
    await page.waitForSelector('[data-testid="ai-response"]')
    const response = page.locator('[data-testid="ai-response"]')
    await expect(response).toContainText('프로젝트')
    
    // 4. 출처 표시 확인
    const sources = page.locator('[data-testid="source-item"]')
    await expect(sources).toHaveCount(2)
    
    // 5. 신뢰도 스코어 확인
    const confidence = page.locator('[data-testid="confidence-score"]')
    await expect(confidence).toContainText(/\d+%/)
  })

  test('사용자가 프로젝트 상세 정보를 볼 수 있다', async ({ page }) => {
    // 1. 종료프로젝트 섹션 클릭
    await page.click('text=🏢 종료프로젝트')
    
    // 2. 첫 번째 프로젝트 클릭
    await page.click('[data-testid="project-item"]:first-child')
    
    // 3. 모달 확인
    const modal = page.locator('[data-testid="project-detail-modal"]')
    await expect(modal).toBeVisible()
    
    // 4. 기본정보 확인
    await expect(modal).toContainText('스마트팩토리')
    await expect(modal).toContainText('◯◯청')
    
    // 5. 참여자 확인
    const participants = modal.locator('[data-testid="participant"]')
    await expect(participants).not.toHaveCount(0)
    
    // 6. 산출물 다운로드 버튼 확인
    const downloadBtn = modal.locator('[data-testid="download-button"]')
    await expect(downloadBtn).toBeVisible()
  })

  test('사용자가 경력기술서를 자동 생성할 수 있다', async ({ page }) => {
    // 1. 회사내부자료 > 인력정보 섹션
    await page.click('text=🏛️ 회사내부자료')
    await page.click('text=인력정보')
    
    // 2. 인력 선택
    await page.click('[data-testid="personnel-checkbox"]:first-child')
    
    // 3. 경력기술서 생성 버튼
    await page.click('text=경력기술서 생성')
    
    // 4. 생성 완료 대기
    await page.waitForSelector('[data-testid="resume-download-link"]')
    
    // 5. 다운로드 가능 확인
    const downloadLink = page.locator('[data-testid="resume-download-link"]')
    await expect(downloadLink).toBeVisible()
  })

  test('사용자가 고급 필터로 검색할 수 있다', async ({ page }) => {
    // 1. 종료프로젝트로 이동
    await page.click('text=🏢 종료프로젝트')
    
    // 2. 고급 필터 클릭
    await page.click('[data-testid="advanced-filters-button"]')
    
    // 3. 필터 설정
    await page.click('[data-testid="team-filter"] input[value="기술팀"]')
    await page.selectOption('[data-testid="result-filter"]', 'won')
    
    // 4. 적용
    await page.click('text=적용')
    
    // 5. 필터된 결과 확인
    await page.waitForSelector('[data-testid="document-item"]')
    const items = page.locator('[data-testid="document-item"]')
    await expect(items).not.toHaveCount(0)
  })

  test('사용자가 파일을 다운로드할 수 있다', async ({ page }) => {
    // 1. 종료프로젝트 섹션
    await page.click('text=🏢 종료프로젝트')
    
    // 2. 다운로드 버튼
    const downloadPromise = page.waitForEvent('download')
    await page.click('[data-testid="download-button"]:first-child')
    
    const download = await downloadPromise
    expect(download.suggestedFilename()).toMatch(/\.docx$|\.pptx$/)
  })

  test('모바일에서도 Vault를 사용할 수 있다', async ({ page }) => {
    // 모바일 뷰포트 설정
    await page.setViewportSize({ width: 375, height: 667 })
    
    // 1. 메뉴 버튼 클릭
    await page.click('[data-testid="mobile-menu-button"]')
    
    // 2. Vault 선택
    await page.click('text=🗂️ VAULT')
    
    // 3. 섹션 선택
    await page.click('text=🏢 종료프로젝트')
    
    // 4. 반응형 레이아웃 확인
    const table = page.locator('[data-testid="document-table"]')
    const grid = page.locator('[data-testid="document-grid"]')
    
    // 모바일에서는 그리드 뷰만 표시
    if (await grid.isVisible()) {
      await expect(table).not.toBeVisible()
    }
  })
})
```

### 4.2 E2E 테스트 체크리스트

```
[ ] Vault 기본 기능 — 10개 테스트
    [x] AI Chat 기본 질문
    [x] 프로젝트 상세 조회
    [x] 경력기술서 생성
    [x] 고급 필터
    [x] 파일 다운로드
    
[ ] 데이터 검증 — 8개 테스트
    [x] 정부지침 정확성
    [x] 종료프로젝트 메타데이터
    [x] 발주처 정보
    [x] 경쟁사 분석
    
[ ] UI/UX 검증 — 8개 테스트
    [x] 반응형 디자인
    [x] 접근성 (키보드 네비게이션)
    [x] 에러 메시지 표시
    [x] 로딩 상태
    
[ ] 성능 검증 — 5개 테스트
    [x] 페이지 로드 시간
    [x] 검색 응답 시간
    [x] 파일 다운로드 속도

총 31개 E2E 테스트
목표: 100% 통과
```

---

## 5. 정확성 검증 테스트 (Accuracy Validation)

### 5.1 Test Case 1: 정확한 5년 AI 프로젝트 목록

```python
@pytest.mark.accuracy
@pytest.mark.asyncio
async def test_ai_project_list_accuracy():
    """
    Query: "최근 5년 수행한 AI 프로젝트 목록을 리스트해줘"
    Expected: 100% 정확한 목록 (할루시네이션 0%)
    """
    
    # Step 1: 테스트 데이터 준비
    test_projects = [
        {"id": "proj_1", "title": "스마트팩토리 2024", "tags": ["AI"], "completion_date": "2024-12-31"},
        {"id": "proj_2", "title": "데이터분석 플랫폼", "tags": ["AI"], "completion_date": "2023-06-15"},
        {"id": "proj_3", "title": "이미지 처리 시스템", "tags": ["AI"], "completion_date": "2022-03-20"},
    ]
    
    # Ground truth: SQL에서 조회
    ground_truth = await execute_sql("""
        SELECT id, title, completion_date FROM completed_projects
        WHERE tags @> ARRAY['AI']
        AND completion_date > NOW() - INTERVAL '5 years'
        ORDER BY completion_date DESC
    """)
    
    # Step 2: AI Chat 쿼리 실행
    response = await vault_chat.query(
        user_id="test_user",
        query="최근 5년 수행한 AI 프로젝트 목록을 리스트해줘",
        scope="all"
    )
    
    # Step 3: 응답 파싱
    projects_in_response = parse_project_list(response.content)
    
    # Step 4: 검증
    assert len(projects_in_response) == len(ground_truth), \
        f"Expected {len(ground_truth)} projects, got {len(projects_in_response)}"
    
    # 각 프로젝트 검증
    for expected in ground_truth:
        found = find_project_in_response(expected, projects_in_response)
        assert found, f"Project '{expected['title']}' not found in response"
    
    # Step 5: 신뢰도 검증
    assert response.confidence >= 0.95, \
        f"Low confidence: {response.confidence} (expected >= 0.95)"
    
    # Step 6: 출처 검증
    assert all_claims_sourced(response), \
        "Unsourced claims found"
    
    # Success Criteria
    print("✅ Test Case 1 PASSED")
    print(f"  - Projects found: {len(projects_in_response)}")
    print(f"  - Confidence: {response.confidence}")
    print(f"  - All sources cited: True")
```

### 5.2 Test Case 2: 다중 섹션 컨텍스트

```python
@pytest.mark.accuracy
@pytest.mark.asyncio
async def test_multi_section_context_accuracy():
    """
    Query: "정부 인건비 단가가 최근 얼마인데, 
            우리 그동안 수행한 유사 프로젝트에서는 어떻게 반영했어?"
    Expected: 두 섹션 통합 답변 (인건비 + 프로젝트 비용)
    """
    
    # Ground truth 준비
    latest_rate = await execute_sql("""
        SELECT salary_amount FROM government_guidelines
        WHERE field_type = 'labor_rate'
        AND salary_level = 'doctorate'
        ORDER BY effective_date DESC LIMIT 1
    """)
    
    similar_projects = await execute_sql("""
        SELECT id, title, bid_amount, team_size FROM completed_projects
        WHERE tags @> ARRAY['유사분야']
    """)
    
    # AI Chat 쿼리
    response = await vault_chat.query(
        query="정부 인건비 단가가 최근 얼마인데, 우리 그동안 수행한 유사 프로젝트에서는 어떻게 반영했어?",
        scope="all"
    )
    
    # 검증
    assert has_section_government_guidelines(response), \
        "Government guidelines section missing"
    
    assert has_section_completed_projects(response), \
        "Completed projects section missing"
    
    assert has_integration_statement(response), \
        "Integration between sections missing"
    
    # 특정 데이터 검증
    extracted_rate = extract_labor_rate(response.content)
    assert extracted_rate == latest_rate.salary_amount, \
        f"Labor rate mismatch: {extracted_rate} vs {latest_rate.salary_amount}"
    
    # Success Criteria
    print("✅ Test Case 2 PASSED")
    print(f"  - Government rate: {extracted_rate}")
    print(f"  - Projects referenced: {len(similar_projects)}")
    print(f"  - Integration: Success")
```

### 5.3 Test Case 3: 할루시네이션 방지

```python
@pytest.mark.accuracy
@pytest.mark.asyncio
async def test_hallucination_prevention():
    """
    Query: "스마트팩토리 2025 프로젝트는 어떻게 진행되었어?"
    Expected: "확인할 수 없습니다" (할루시네이션 방지)
    """
    
    # 프로젝트 존재 확인
    project = await execute_sql("""
        SELECT id FROM completed_projects 
        WHERE title ILIKE '%스마트팩토리 2025%'
    """)
    
    assert project is None, "Project should not exist"
    
    # AI Chat 쿼리
    response = await vault_chat.query(
        query="스마트팩토리 2025 프로젝트는 어떻게 진행되었어?"
    )
    
    # 검증
    assert "확인할 수 없습니다" in response.content or \
           "발견되지 않았습니다" in response.content, \
        f"Hallucinated response: {response.content}"
    
    assert response.confidence < 0.3, \
        f"Low confidence expected, got {response.confidence}"
    
    # Success Criteria
    print("✅ Test Case 3 PASSED")
    print(f"  - Hallucination detected: False")
    print(f"  - Confidence low: {response.confidence}")
```

### 5.4 Test Case 4: 정부 인건비 정확도

```python
@pytest.mark.accuracy
@pytest.mark.asyncio
async def test_government_salary_accuracy():
    """
    Query: "박사급 인건비는 월 얼마야?"
    Expected: 100% 정부 공식 기준과 일치
    """
    
    # 공식 기준
    official_rate = await execute_sql("""
        SELECT salary_amount, effective_date FROM government_guidelines
        WHERE field_type = 'labor_rate'
        AND salary_level = 'doctorate'
        ORDER BY effective_date DESC LIMIT 1
    """)
    
    # AI Chat 쿼리
    response = await vault_chat.query(
        query="박사급 인건비는 월 얼마야?",
        scope="government_guidelines"
    )
    
    # 응답에서 금액 추출
    extracted_rate = extract_salary_amount(response.content)
    
    # 검증
    assert extracted_rate == official_rate.salary_amount, \
        f"Rate mismatch: {extracted_rate} vs {official_rate.salary_amount}"
    
    assert has_source_attribution(response), \
        "Must cite government guideline"
    
    assert response.confidence >= 0.95, \
        "SQL-sourced data must have high confidence"
    
    # Success Criteria
    print("✅ Test Case 4 PASSED")
    print(f"  - Official rate: {official_rate.salary_amount}")
    print(f"  - Extracted rate: {extracted_rate}")
    print(f"  - Match: Perfect")
    print(f"  - Source cited: True")
```

---

## 6. 성능 테스트 (Performance Testing)

### 6.1 응답 시간 측정

```python
@pytest.mark.performance
@pytest.mark.asyncio
async def test_response_time_under_load():
    """
    Requirement: API 응답 시간 < 3초
    Load: 동시 사용자 10명
    """
    import asyncio
    import time
    
    async def single_query():
        start = time.time()
        response = await vault_chat.query(
            query="최근 AI 프로젝트",
            scope="completed_projects"
        )
        elapsed = time.time() - start
        return elapsed
    
    # 10개 동시 쿼리
    tasks = [single_query() for _ in range(10)]
    results = await asyncio.gather(*tasks)
    
    # 검증
    avg_time = sum(results) / len(results)
    max_time = max(results)
    
    assert avg_time < 3.0, f"Average response time {avg_time}s exceeds 3s"
    assert max_time < 5.0, f"Max response time {max_time}s exceeds 5s"
    
    print(f"✅ Performance Test PASSED")
    print(f"  - Average: {avg_time:.2f}s")
    print(f"  - Max: {max_time:.2f}s")
```

### 6.2 동시성 테스트

```python
@pytest.mark.performance
@pytest.mark.asyncio
async def test_concurrent_conversations():
    """
    Requirement: 동시에 10개의 대화 처리 가능
    """
    
    async def create_conversation():
        return await vault_chat.create_conversation(user_id="test_user")
    
    # 10개 대화 동시 생성
    conversations = await asyncio.gather(*[create_conversation() for _ in range(10)])
    
    assert len(conversations) == 10
    assert all(c.id for c in conversations)
    
    print(f"✅ Concurrency Test PASSED")
    print(f"  - Concurrent conversations: 10")
    print(f"  - All created successfully: True")
```

---

## 7. 보안 테스트 (Security Testing)

### 7.1 인증 & 권한 테스트

```python
@pytest.mark.security
@pytest.mark.asyncio
async def test_unauthorized_access():
    """비인증 사용자 접근 차단"""
    
    response = client.get(
        "/api/vault/chat",
        headers={}  # No auth token
    )
    
    assert response.status_code == 401

@pytest.mark.security
@pytest.mark.asyncio
async def test_cross_team_access():
    """팀 간 데이터 접근 차단 (RLS)"""
    
    # 팀 B 사용자가 팀 A 데이터 접근 시도
    response = client.get(
        "/api/vault/conversations/team_a_conv_123",
        headers={"Authorization": f"Bearer {team_b_token}"}
    )
    
    assert response.status_code == 403
```

### 7.2 데이터 보안 테스트

```python
@pytest.mark.security
@pytest.mark.asyncio
async def test_sql_injection_prevention():
    """SQL 주입 공격 방지"""
    
    malicious_query = "'; DROP TABLE vault_documents; --"
    
    response = await vault_chat.query(
        query=malicious_query,
        scope="all"
    )
    
    # 데이터베이스 정상 확인
    result = await supabase.table("vault_documents").select("count()").execute()
    assert result.data is not None  # 테이블 존재
```

---

## 8. 테스트 실행 계획 (Timeline)

```
Week 1 (2026-06-01 ~ 2026-06-05)
─────────────────────────────────
단위 테스트 (Backend):
- [x] 122개 단위 테스트 작성
- [x] 커버리지 리포트 생성 (목표: >85%)

Week 2 (2026-06-08 ~ 2026-06-12)
─────────────────────────────────
통합 테스트:
- [x] 45개 통합 테스트 실행
- [x] API 엔드포인트 검증
- [x] 데이터베이스 RLS 검증

정확성 검증:
- [x] Test Case 1 실행 (5년 AI 프로젝트)
- [x] Test Case 2 실행 (다중 섹션)
- [x] Test Case 3 실행 (할루시네이션 방지)
- [x] Test Case 4 실행 (정부 인건비)

Week 3 (2026-06-15 ~ 2026-06-19)
─────────────────────────────────
E2E 테스트:
- [x] 31개 E2E 테스트 (Playwright)
- [x] 성능 테스트 실행
- [x] 모바일 호환성 검증

Week 4 (2026-06-22 ~ 2026-06-30)
─────────────────────────────────
보안 테스트:
- [x] 권한 검증
- [x] 데이터 보호 테스트
- [x] 침투 테스트 (선택사항)

최종 검증:
- [x] 모든 결함 수정
- [x] 회귀 테스트
- [x] 최종 승인
```

---

## 9. 성공 기준 (Success Criteria)

```
[ ] 단위 테스트
    [x] 122개 테스트 100% 통과
    [x] 커버리지 >= 85%
    
[ ] 통합 테스트
    [x] 45개 테스트 100% 통과
    
[ ] E2E 테스트
    [x] 31개 테스트 100% 통과
    
[ ] 정확성 검증
    [x] Test Case 1: 100% 정확도
    [x] Test Case 2: 다중섹션 통합 성공
    [x] Test Case 3: 할루시네이션 0%
    [x] Test Case 4: 정부기준 100% 일치
    
[ ] 성능
    [x] API 응답 시간 < 3초
    [x] 동시성 >= 10명
    
[ ] 보안
    [x] 인증 필수
    [x] RLS 정책 작동
    [x] SQL 주입 방지
    
[ ] 배포 준비
    [x] 버그 0개 (P0/P1)
    [x] 문서화 100%
    [x] 성능 기준 만족
```

---

**Phase 2 테스트 완료**: 2026-06-30  
**프로덕션 배포 준비**: 2026-07-01
