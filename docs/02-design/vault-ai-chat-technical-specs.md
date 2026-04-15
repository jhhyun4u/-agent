# Vault AI Chat 기술 스펙 — 통합 자료 검색 및 대화 시스템

**문서**: TENOPA Vault AI Chat 기술 설계 명세서  
**버전**: 1.0  
**작성일**: 2026-04-14  
**대상**: 백엔드(Python/FastAPI) + 프론트엔드(Next.js/React) 개발팀  

---

## 1. 시스템 아키텍처 개요

### 1.1 3-Layer Architecture

```
┌──────────────────────────────────────────────────────────┐
│  Layer 1: Presentation (Frontend)                         │
│  VaultChatUI Component → ConversationHistory + SearchBar │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│  Layer 2: API Gateway (FastAPI)                           │
│  POST /api/vault/chat → Context Assembly + Route Selection│
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│  Layer 3: Intelligence (LLM + Vector + SQL)              │
│  ┌──────────────────┬────────────────┬─────────────────┐ │
│  │ Claude Sonnet 4.5│ pgvector Search│ SQL Direct Query│ │
│  │ (Reasoning)      │ (Semantic Match)│ (Factual Truth)│ │
│  └──────────────────┴────────────────┴─────────────────┘ │
│         │                    │                 │          │
│         ▼                    ▼                 ▼          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ Supabase (PostgreSQL + pgvector)                    │ │
│  │ - vault_documents (embeddings)                       │ │
│  │ - completed_projects, clients_db, research_materials │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

### 1.2 Request Flow

```
User Query
    │
    ▼
[Frontend] VaultChatUI
    │ POST /api/vault/chat
    │ { message: "...", scope: "all"|section, conversation_id: "..." }
    │
    ▼
[API Layer] route_vault_chat()
    ├─ Load conversation context
    ├─ Detect intent (section + query type)
    ├─ Route to appropriate handler
    │
    ▼
[Query Execution]
    │
    ├─ Vector Search (pgvector)
    │  └─ Semantic context retrieval
    │
    ├─ SQL Direct Query
    │  ├─ Fact checking (completed_projects, clients_db)
    │  ├─ Exact matches (government guidelines, salary rates)
    │  └─ Aggregation (team statistics, performance metrics)
    │
    ├─ LLM Reasoning (Claude Sonnet)
    │  ├─ Multi-source synthesis
    │  ├─ Contradiction detection
    │  ├─ Confidence assessment
    │  └─ Source attribution
    │
    ▼
[Response Assembly]
    ├─ Main answer (with sources)
    ├─ Related documents (5-10 items)
    ├─ Confidence score (0-100%)
    └─ Metadata (query execution time, data freshness)
    │
    ▼
[Frontend] DisplayChatMessage
    ├─ Render answer with source highlights
    ├─ Show related documents
    └─ Track conversation history
```

---

## 2. Core Components

### 2.1 LLM + Vector Search + SQL Triad

#### LLM 역할
- **사용 모델**: Claude Sonnet 4.6 (또는 최신 Haiku 4.5 for cost optimization)
- **역할**:
  - 자연어 쿼리 의도 파악 (section inference)
  - 다중 데이터소스 종합
  - 맥락 기반 추론
  - 신뢰도 평가
  - 할루시네이션 감지 및 방지

#### Vector Search 역할
- **사용**: Supabase pgvector (OpenAI Embeddings API 또는 로컬 임베딩)
- **용도**:
  - 의미론적 검색 (semantic similarity)
  - 문서 컨텍스트 검색
  - 다중 섹션 횡단 검색
  - 성공사례 관련 학습자료 추천

#### SQL Direct Query 역할
- **용도**:
  - 팩트 기반 정보 (프로젝트 메타데이터, 인건비, 정부지침)
  - 정확한 일치 검색 (발주처명, 담당자, 실적증명서)
  - 집계 및 통계 (팀 성과, 낙찰률, 비용)
  - 데이터 무결성 검증

---

### 2.2 Hallucination Prevention Strategy

#### 2.2.1 3-Point Validation Gate

```python
class HallucinationGate:
    """
    Detects hallucinations before LLM response is sent to user
    """
    
    async def validate(self, 
                      query: str,
                      response: str,
                      source_facts: List[Dict],
                      confidence: float) -> ValidationResult:
        """
        3-point validation:
        1. Source coherence: Response must cite actual sources
        2. Fact alignment: No contradictions with SQL truth
        3. Confidence threshold: Only deliver if confidence >= 80%
        """
        
        # Point 1: Extract citations from LLM response
        citations = extract_citations(response)
        missing_citations = check_source_alignment(citations, source_facts)
        
        if missing_citations:
            # Hallucination detected: unsourced claims
            return ValidationResult(
                passed=False,
                reason="Unsourced claims detected",
                unsourced=missing_citations,
                suggested_fix="Requery with explicit source constraints"
            )
        
        # Point 2: Fact-check against SQL truth
        contradictions = check_fact_alignment(
            response, source_facts, query
        )
        
        if contradictions:
            return ValidationResult(
                passed=False,
                reason="Factual contradiction with SQL sources",
                contradictions=contradictions
            )
        
        # Point 3: Confidence threshold
        if confidence < 0.80:
            return ValidationResult(
                passed=False,
                reason="Low confidence (< 80%)",
                confidence=confidence,
                suggested_message="I found relevant information but with low confidence. Please verify with primary sources."
            )
        
        return ValidationResult(passed=True, confidence=confidence)
```

#### 2.2.2 Enforced Source Attribution

```python
# System Prompt Injection
SYSTEM_PROMPT = """
당신은 TENOPA의 자료검색 AI어시스턴트입니다.

다음 규칙을 반드시 따르세요:

1. **출처 명시의무**: 모든 주장은 반드시 출처를 명시하세요
   - 좋음: "...이는 완료된 프로젝트 '스마트팩토리 2024'에서 확인됨"
   - 나쁨: "...이는 일반적으로 알려져 있습니다"

2. **데이터 신뢰도**: SQL 쿼리 결과를 정부지침보다 우선시하세요
   - SQL truth: 실제 수행했던 프로젝트 데이터 (100% 신뢰)
   - Vector context: 문서의 의미론적 맥락 (80% 신뢰)
   - LLM reasoning: 추론 및 해석 (60% 신뢰)

3. **할루시네이션 방지**:
   - 확실하지 않으면 "확인할 수 없습니다"라고 말하세요
   - 예상이나 추측은 명확히 표시하세요
   - 반박 자료가 있으면 반드시 언급하세요

4. **신뢰도 점수**: 항상 응답 끝에 신뢰도를 표시하세요
   - 확신 (95~100%): 여러 SQL source로 검증됨
   - 높음 (80~95%): SQL + Vector search 모두 일치
   - 중간 (60~80%): Vector search만 확인됨
   - 낮음 (40~60%): 추론만 가능
   - 매우낮음 (<40%): 답변 제공 불가

5. **다중 답변 금지**: 같은 쿼리에 여러 가지 상충하는 답변을 주지 마세요
"""
```

#### 2.2.3 Query Constraint Enforcement

```python
# For each section, enforce strict query constraints
SECTION_QUERY_CONSTRAINTS = {
    "completed_projects": {
        "allowed_fields": [
            "project_id", "title", "client_name", "win_result",
            "bid_amount", "team_name", "completion_date"
        ],
        "disallowed_claims": [
            # 추측 금지
            "future_projects", "lost_projects_reason",
            # 개인정보 금지
            "individual_salaries", "negotiation_prices"
        ],
        "verify_before_cite": [
            "낙찰가 (반드시 제안액과 일치 확인)",
            "낙찰률 (반드시 예산과 비율 검증)"
        ]
    },
    
    "government_guidelines": {
        "allowed_fields": [
            "guideline_year", "labor_rate", "budget_rules",
            "submission_deadline", "form_template"
        ],
        "disallowed_claims": [
            # 예측 금지
            "future_rate_changes"
        ]
    },
    
    "research_materials": {
        "allowed_fields": [
            "technology_trend", "industry_report", "lesson_learned"
        ],
        "disallowed_claims": [
            # 검증 불가능한 기술
            "unverified_patents"
        ]
    }
}
```

---

## 3. Section-Specific Query Logic

### 3.1 Section Routing Matrix

| 섹션 | 쿼리 타입 | 데이터소스 | 검색방식 | 우선순위 |
|------|-----------|----------|--------|---------|
| **종료프로젝트** | 프로젝트명, 발주처, 결과, 팀 | `proposals` | SQL + Vector | SQL 우선 |
| **회사내부자료** | 조직도, 인력, 재무, 인증 | `team_members`, `company_assets` | SQL | SQL only |
| **실적증명서** | 수행과제목록, 계약서 | `completed_projects`, `contracts` | SQL + Document | SQL 우선 |
| **정부지침** | 인건비, 예산, 서식 | `government_guidelines`, `form_templates` | SQL | SQL only |
| **경쟁사정보** | 유사기관, 낙찰정보 | `competitors`, `market_analysis` | SQL + Vector | SQL 우선 |
| **성공사례** | 발표자료, 학습자료, Q&A | `lessons_learned`, `presentations` | Vector + LLM | Vector 우선 |
| **발주처정보** | 담당자, 경험, 관계DB | `clients_db` | SQL | SQL only |
| **리서치자료** | 기술동향, 논문, 보고서 | `research_materials` | Vector | Vector only |

### 3.2 Section-Specific Implementation

#### 3.2.1 종료프로젝트 (Completed Projects)

```python
async def query_completed_projects(
    query: str,
    filters: Optional[Dict] = None
) -> QueryResult:
    """
    전략: SQL 우선 + Vector 보강
    - SQL: 정확한 프로젝트 메타데이터 (프로젝트명, 발주처, 결과)
    - Vector: 유사 프로젝트 추천 (주제 기반)
    """
    
    # Step 1: Intent Detection (LLM)
    intent = await detect_query_intent(query)
    # Returns: {query_type: "project_search"|"team_performance"|"lesson_learned",
    #           filters: {project_name, client_name, win_result, team, date_range}}
    
    # Step 2: SQL Direct Query (Primary Source of Truth)
    sql_results = await execute_sql(f"""
        SELECT 
            id, title, client_name, win_result, bid_amount, budget,
            team_name, participants, completion_date, lessons_summary,
            storage_path_docx, storage_path_pptx
        FROM completed_projects
        WHERE 
            (title ILIKE %{intent.filters.project_name}% OR
             client_name ILIKE %{intent.filters.client_name}% OR
             participants @> ARRAY[%{intent.filters.team_member}%])
            AND completion_date BETWEEN %{intent.filters.date_range}%
        ORDER BY completion_date DESC
        LIMIT 20
    """)
    
    # Step 3: Vector Search (Supplemental Context)
    vector_results = await search_vectors(
        query=query,
        section="completed_projects",
        limit=10,
        min_similarity=0.7
    )
    
    # Step 4: Deduplication & Ranking
    combined = deduplicate_by_id(sql_results, vector_results)
    ranked = rank_by_relevance(combined, intent.query_type)
    
    # Step 5: Validation
    for result in ranked:
        validate_project_facts(result)  # 낙찰가, 낙찰률 검증
    
    return QueryResult(
        primary_source="sql",
        results=ranked[:10],
        total_count=len(combined),
        metadata={
            "sql_matches": len(sql_results),
            "vector_matches": len(vector_results),
            "deduped": len(combined)
        }
    )
```

#### 3.2.2 정부지침 (Government Guidelines)

```python
async def query_government_guidelines(
    query: str,
    specific_field: Optional[str] = None
) -> QueryResult:
    """
    전략: SQL 전용 (정확성 필수)
    - 벡터 검색 금지 (법규는 추측 불가)
    - 연도별 최신 지침만 반환
    """
    
    # Intent: Extract field (labor_rate, budget_rule, form_template)
    field_intent = await extract_guideline_field(query)
    
    # SQL-only Query
    sql_results = await execute_sql(f"""
        SELECT 
            id, guideline_year, field_type, content, document_url,
            effective_date, expiration_date, last_updated
        FROM government_guidelines
        WHERE 
            field_type = %{field_intent}
            AND guideline_year = (SELECT MAX(guideline_year) FROM government_guidelines)
        ORDER BY effective_date DESC
        LIMIT 5
    """)
    
    # Validation: Check recency
    for result in sql_results:
        if result.expiration_date < today():
            mark_as_expired(result)
    
    return QueryResult(
        primary_source="sql",
        results=sql_results,
        confidence=1.0,  # 100% SQL 기반
        warnings=["Vector search not used (legal accuracy required)"]
    )
```

#### 3.2.3 성공사례 & 시사점 (Success Cases & Lessons)

```python
async def query_success_cases(
    query: str,
    conversation_context: List[Dict]
) -> QueryResult:
    """
    전략: Vector 우선 + LLM 종합
    - Vector: 의미론적 유사 학습자료 검색
    - LLM: 다중 자료 종합 및 해석
    - SQL: 출처 검증 (어느 프로젝트에서 나온 사례인가)
    """
    
    # Step 1: Enrich query with conversation context
    enriched_query = await enrich_with_context(query, conversation_context)
    
    # Step 2: Vector Search (Primary)
    vector_results = await search_vectors(
        query=enriched_query,
        section="success_cases",
        limit=15,
        min_similarity=0.65  # 낮은 threshold (해석의 여지 있음)
    )
    
    # Step 3: Source Verification (SQL)
    for result in vector_results:
        source_project = await get_source_project(result.source_id)
        result.verified_source = source_project  # 어느 프로젝트인지 명시
    
    # Step 4: LLM Synthesis
    synthesized = await synthesize_with_llm(
        documents=vector_results,
        query=enriched_query,
        conversation=conversation_context,
        system_prompt=SYSTEM_PROMPT_SUCCESS_CASES
    )
    
    # Step 5: Confidence Scoring
    confidence = calculate_confidence(
        vector_similarity=vector_results[0].similarity,
        source_count=len(set(r.source_id for r in vector_results)),
        context_alignment=synthesized.context_score
    )
    
    return QueryResult(
        primary_source="vector+llm",
        results=synthesized,
        confidence=confidence,
        sources=list(set(r.verified_source for r in vector_results))
    )
```

#### 3.2.4 리서치자료 (Research Materials)

```python
async def query_research_materials(
    query: str,
    ttl_check: bool = True
) -> QueryResult:
    """
    전략: Vector 전용 + TTL 검증
    - Vector: 기술 동향, 논문, 보고서 의미론적 검색
    - SQL: 만료 여부 확인 (3개월 TTL)
    """
    
    # Step 1: Vector Search
    vector_results = await search_vectors(
        query=query,
        section="research_materials",
        limit=20,
        min_similarity=0.60
    )
    
    # Step 2: TTL Filter
    if ttl_check:
        valid_results = [
            r for r in vector_results
            if r.created_at > (now() - timedelta(days=90))
            or r.retention_policy == "permanent"
        ]
        expired_results = [
            r for r in vector_results
            if r.created_at <= (now() - timedelta(days=90))
            and r.retention_policy == "ttl"
        ]
    else:
        valid_results = vector_results
        expired_results = []
    
    # Step 3: Return with TTL metadata
    return QueryResult(
        primary_source="vector",
        results=valid_results,
        expired_count=len(expired_results),
        warnings=[
            f"{len(expired_results)} expired research materials not shown"
        ] if expired_results else None
    )
```

---

## 4. Multi-Section Context Management

### 4.1 Conversation State

```python
class VaultConversation(BaseModel):
    """Conversation state across multiple turns"""
    
    id: str  # conversation_id
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    # Conversation history
    messages: List[Message] = []  # (role, content, sources, timestamp)
    
    # Context management
    current_section: Optional[str] = None  # active section (or "all")
    section_stack: List[str] = []  # navigation history
    
    # Multi-section memory
    resolved_facts: Dict[str, Any] = {}  # Facts established in conversation
    open_questions: List[str] = []  # Unanswered questions
    
    # Token tracking
    token_count_used: int = 0
    token_budget_remaining: int = 10000
```

### 4.2 Context Injection into LLM

```python
async def build_llm_prompt(
    user_query: str,
    conversation_state: VaultConversation,
    retrieved_sources: List[Dict]
) -> str:
    """
    Construct LLM prompt with proper context hierarchy
    """
    
    # 1. System Prompt (enforced rules)
    system = SYSTEM_PROMPT_VAULT_CHAT
    
    # 2. Previous conversation context (last 5 turns)
    conversation_context = "\n".join([
        f"User: {msg.content}" if msg.role == "user" else f"Assistant: {msg.content}"
        for msg in conversation_state.messages[-10:]
    ])
    
    # 3. Established facts (prevent contradiction)
    facts_context = "\n".join([
        f"[ESTABLISHED FACT] {k}: {v}"
        for k, v in conversation_state.resolved_facts.items()
    ])
    
    # 4. Retrieved sources (primary data)
    sources_context = "\n".join([
        f"[SOURCE {i+1}] {s['section']} | {s['title']}\n{s['content'][:500]}"
        for i, s in enumerate(retrieved_sources[:5])
    ])
    
    # 5. Open questions (context of unsolved queries)
    questions_context = "\n".join([
        f"[OPEN QUESTION] {q}"
        for q in conversation_state.open_questions
    ])
    
    final_prompt = f"""
{system}

## 이전 대화 내용
{conversation_context}

## 확인된 사실들 (모순 방지)
{facts_context}

## 검색된 자료 (출처 명시 필수)
{sources_context}

## 해결되지 않은 질문들
{questions_context}

## 현재 질문
User: {user_query}

Please answer the question based on retrieved sources. If you cannot answer with confidence >= 80%, say so.
"""
    
    return final_prompt
```

### 4.3 Contradiction Detection

```python
async def detect_contradiction(
    current_response: str,
    established_facts: Dict[str, Any],
    retrieved_sources: List[Dict]
) -> List[Contradiction]:
    """
    Detects contradictions between:
    1. Current response vs. established facts
    2. Current response vs. retrieved sources
    3. Retrieved sources vs. each other
    """
    
    contradictions = []
    
    # Check against established facts
    for fact_key, fact_value in established_facts.items():
        if contradicts_fact(current_response, fact_key, fact_value):
            contradictions.append(
                Contradiction(
                    type="established_fact",
                    fact_key=fact_key,
                    expected=fact_value,
                    found=extract_claim(current_response, fact_key)
                )
            )
    
    # Check sources consistency
    for i, source in enumerate(retrieved_sources):
        for j in range(i+1, len(retrieved_sources)):
            if contradicts_sources(retrieved_sources[i], retrieved_sources[j]):
                contradictions.append(
                    Contradiction(
                        type="source_conflict",
                        source1=retrieved_sources[i],
                        source2=retrieved_sources[j]
                    )
                )
    
    return contradictions
```

---

## 5. Accuracy Validation Framework

### 5.1 Test Cases (from Phase 0 Plan)

#### Test Case 1: Exact 5-Year AI Project Query

```python
async def test_ai_project_query():
    """
    Query: "최근 5년 수행한 AI 프로젝트 목록을 리스트해줘"
    
    Expected Behavior:
    - 100% 정확한 리스트 (할루시네이션 0%)
    - 모든 프로젝트는 completed_projects 테이블에서 직접 검증
    - 프로젝트명, 발주처, 완료일, 팀 명시
    """
    
    query = "최근 5년 수행한 AI 프로젝트 목록을 리스트해줘"
    
    # Step 1: Query execution
    response = await vault_chat(
        user_id="test_user",
        query=query,
        scope="all"
    )
    
    # Step 2: Ground truth from SQL
    ground_truth = await execute_sql("""
        SELECT id, title, client_name, completion_date, team_name
        FROM completed_projects
        WHERE 
            tags @> ARRAY['AI']
            AND completion_date > NOW() - INTERVAL '5 years'
        ORDER BY completion_date DESC
    """)
    
    # Step 3: Validation
    projects_in_response = parse_project_list(response.content)
    
    assert len(projects_in_response) == len(ground_truth), \
        f"Expected {len(ground_truth)} projects, got {len(projects_in_response)}"
    
    # Check each project
    for expected in ground_truth:
        assert find_project_in_response(expected, projects_in_response), \
            f"Project '{expected.title}' not found in response"
    
    # Confidence must be 100%
    assert response.confidence >= 0.95, \
        f"Low confidence: {response.confidence}"
    
    # All claims must be sourced
    assert all_claims_sourced(response), \
        "Unsourced claims found"
```

#### Test Case 2: Multi-Section Search Context

```python
async def test_multi_section_context():
    """
    Query: "정부 인건비 단가가 최근 얼마인데, 우리 그동안 수행한 
            유사 프로젝트에서는 어떻게 반영했어?"
    
    Expected Behavior:
    - Section 1 (정부지침): 최신 인건비 단가 (SQL only)
    - Section 2 (종료프로젝트): 유사 프로젝트 목록 (SQL + Vector)
    - Integration: 두 정보를 연관지어 설명
    """
    
    query = "정부 인건비 단가가 최근 얼마인데, 우리 그동안 수행한 유사 프로젝트에서는 어떻게 반영했어?"
    
    response = await vault_chat(
        user_id="test_user",
        query=query,
        scope="all"
    )
    
    # Validation
    assert has_section_government_guidelines(response), \
        "Government guidelines section missing"
    assert has_section_completed_projects(response), \
        "Completed projects section missing"
    assert has_integration_statement(response), \
        "Integration between sections missing"
    
    # Specific data validation
    latest_rate = extract_labor_rate(response)
    assert latest_rate >= 0, "Invalid labor rate"
    
    projects_cited = extract_cited_projects(response)
    for project_id in projects_cited:
        project = await get_project(project_id)
        assert project exists
```

#### Test Case 3: Hallucination Prevention

```python
async def test_hallucination_prevention():
    """
    Query: "수행한 적 없는 프로젝트 어떻게 처리하나?"
    Example: "스마트팩토리 2025 프로젝트는 어떻게 진행되었어?"
    
    Expected: "확인할 수 없습니다" (with validation that project doesn't exist)
    """
    
    query = "스마트팩토리 2025 프로젝트는 어떻게 진행되었어?"
    
    response = await vault_chat(
        user_id="test_user",
        query=query,
        scope="completed_projects"
    )
    
    # Verify project doesn't exist
    project = await execute_sql("""
        SELECT id FROM completed_projects 
        WHERE title ILIKE '%스마트팩토리 2025%'
    """)
    
    assert project is None, "Project should not exist"
    
    # Response should indicate unavailability
    assert "확인할 수 없습니다" in response.content or \
           "발견되지 않았습니다" in response.content, \
        f"Hallucinated response: {response.content}"
    
    # Confidence must be low
    assert response.confidence < 0.3, \
        "Confidence should be low for non-existent project"
```

#### Test Case 4: Salary Data Accuracy

```python
async def test_salary_data_accuracy():
    """
    Query: "박사급 인건비는 월 얼마야?"
    
    Expected: 정부 공식 기준 (100% 정확)
    """
    
    query = "박사급 인건비는 월 얼마야?"
    
    response = await vault_chat(
        user_id="test_user",
        query=query,
        scope="government_guidelines"
    )
    
    # Ground truth from official government guidelines
    official_rate = await execute_sql("""
        SELECT salary_amount, effective_date 
        FROM government_guidelines
        WHERE field_type = 'labor_rate'
        AND salary_level = 'doctorate'
        ORDER BY effective_date DESC
        LIMIT 1
    """)
    
    # Extract rate from response
    extracted_rate = extract_salary(response.content)
    
    assert extracted_rate == official_rate.salary_amount, \
        f"Expected {official_rate.salary_amount}, got {extracted_rate}"
    
    # Must cite source
    assert has_source_attribution(response), \
        "Must cite government guideline document"
    
    # Confidence must be high
    assert response.confidence >= 0.95, \
        "SQL-sourced data must have high confidence"
```

### 5.2 Validation Framework

```python
class AccuracyValidator:
    """Framework for validating AI Chat responses"""
    
    async def validate_response(
        self,
        query: str,
        response: str,
        sources: List[Dict],
        conversation: VaultConversation
    ) -> ValidationReport:
        """
        Multi-point validation
        """
        
        report = ValidationReport(
            query=query,
            response=response,
            timestamp=now(),
            checks={}
        )
        
        # Check 1: All claims are sourced
        report.checks["source_attribution"] = \
            await check_source_attribution(response, sources)
        
        # Check 2: No contradictions
        report.checks["contradiction"] = \
            await check_contradiction(response, sources, conversation.resolved_facts)
        
        # Check 3: Confidence scoring
        report.checks["confidence"] = \
            await calculate_confidence_score(response, sources)
        
        # Check 4: Hallucination detection
        report.checks["hallucination"] = \
            await detect_hallucination(response, sources)
        
        # Check 5: Data freshness
        report.checks["data_freshness"] = \
            await check_data_freshness(sources)
        
        # Overall verdict
        report.passed = all(
            check.passed for check in report.checks.values()
        )
        
        return report
```

---

## 6. API Contract

### 6.1 Frontend → Backend

#### POST /api/vault/chat

```python
# Request
{
    "message": str,           # User query
    "conversation_id": str,   # Existing or new
    "scope": "all" | "section_name",  # Search scope
    "section_filter": Optional[str],   # Explicit section hint
    "include_sources": bool = True,
    "max_tokens": int = 2000
}

# Response
{
    "conversation_id": str,
    "response": str,           # LLM-generated answer
    "sources": [
        {
            "id": str,
            "section": str,
            "title": str,
            "excerpt": str,
            "relevance_score": float,  # 0-1
            "document_url": str,
            "source_type": "sql" | "vector" | "llm"
        }
    ],
    "metadata": {
        "execution_time_ms": int,
        "sql_queries": int,
        "vector_searches": int,
        "models_used": ["claude-sonnet-4.6", "pgvector"],
        "data_freshness": {
            "completed_projects": "2026-04-14T10:30:00Z",
            "government_guidelines": "2026-03-20T00:00:00Z"
        }
    },
    "confidence": float,       # 0-1
    "validation_status": "passed" | "warning" | "failed",
    "related_documents": [     # Additional recommendations
        {"id": str, "title": str, "relevance": float}
    ]
}
```

### 6.2 Backend Components

#### route_vault_chat()

```python
@router.post("/api/vault/chat", response_model=VaultChatResponse)
async def route_vault_chat(
    request: VaultChatRequest,
    current_user: User = Depends(get_current_user)
) -> VaultChatResponse:
    """
    Main entry point for Vault AI Chat
    """
    
    # 1. Load conversation
    conversation = await load_conversation(
        request.conversation_id, current_user.id
    )
    
    # 2. Detect intent & section
    intent = await detect_intent(
        query=request.message,
        history=conversation.messages,
        explicit_section=request.section_filter
    )
    
    # 3. Route to handler
    if intent.section == "all":
        sources = await multi_section_search(request.message)
    else:
        sources = await section_specific_search(
            query=request.message,
            section=intent.section
        )
    
    # 4. Generate LLM response
    llm_response = await generate_response(
        query=request.message,
        sources=sources,
        conversation=conversation
    )
    
    # 5. Validate
    validation = await validator.validate_response(
        query=request.message,
        response=llm_response,
        sources=sources,
        conversation=conversation
    )
    
    if not validation.passed:
        # Return with warnings or request clarification
        llm_response = await regenerate_with_constraints(
            original_query=request.message,
            validation_issues=validation.checks
        )
    
    # 6. Save conversation
    conversation.messages.append(Message(
        role="user",
        content=request.message
    ))
    conversation.messages.append(Message(
        role="assistant",
        content=llm_response,
        sources=sources,
        confidence=validation.checks["confidence"].score
    ))
    await save_conversation(conversation)
    
    # 7. Return response
    return VaultChatResponse(
        conversation_id=conversation.id,
        response=llm_response,
        sources=sources,
        confidence=validation.checks["confidence"].score,
        validation_status="passed" if validation.passed else "warning"
    )
```

---

## 7. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

- [ ] Database schemas (vault_metadata, embeddings)
- [ ] Vector search setup (pgvector + OpenAI Embeddings)
- [ ] Supabase RLS policies
- [ ] Basic SQL query handlers

### Phase 2: Core Features (Week 3-4)

- [ ] LLM integration (Claude Sonnet)
- [ ] Section-specific handlers
- [ ] Hallucination prevention mechanisms
- [ ] Conversation state management

### Phase 3: Validation & Polish (Week 5-6)

- [ ] Validation framework
- [ ] Error handling & edge cases
- [ ] Performance optimization
- [ ] Frontend integration

### Phase 4: Testing & Deployment (Week 7-8)

- [ ] Unit tests
- [ ] Integration tests
- [ ] E2E testing (using playwright)
- [ ] Production deployment

---

## 8. Error Handling

```python
class VaultChatError(Exception):
    """Base exception for Vault Chat errors"""
    
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        recoverable: bool = False
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.recoverable = recoverable

# Specific error types
class DataNotFoundException(VaultChatError):
    """Requested data not found in any section"""
    
class ConfidenceTooLowError(VaultChatError):
    """Cannot generate response with sufficient confidence"""
    
class HallucinationDetectedError(VaultChatError):
    """Response validation failed - hallucination detected"""
    
class MultipleContradictionsError(VaultChatError):
    """Multiple sources contradict each other"""

# Error response format
{
    "error": {
        "code": "HALLUCINATION_DETECTED",
        "message": "Cannot provide answer with confidence >= 80%",
        "details": {
            "actual_confidence": 0.65,
            "required_confidence": 0.80,
            "suggestions": [
                "Search specific section instead of 'all'",
                "Refine your question with more specific terms"
            ]
        },
        "recoverable": True
    }
}
```

---

## 9. Data Freshness & TTL Management

### 9.1 Section-Specific TTL Policies

| 섹션 | TTL | Refresh Interval | Freshness Check |
|------|-----|------------------|-----------------|
| 종료프로젝트 | ∞ | Manual | DB trigger |
| 회사내부자료 | ∞ | Quarterly | Last update |
| 실적증명서 | ∞ | Manual | Contract date |
| 정부지침 | 6개월 | New guideline | Effective date |
| 경쟁사정보 | 1년 | Quarterly | Analysis date |
| 성공사례 | ∞ | Manual | Reference date |
| 발주처정보 | 3개월 | Monthly | Contact update |
| 리서치자료 | 3개월 | Manual | Created date |

### 9.2 Data Freshness Metadata

```python
# Every response includes freshness info
"metadata": {
    "data_freshness": {
        "completed_projects": {
            "last_updated": "2026-04-14T10:30:00Z",
            "freshness_status": "current",  # current | stale | expired
            "days_old": 0
        },
        "government_guidelines": {
            "last_updated": "2026-03-20T00:00:00Z",
            "freshness_status": "current",
            "days_old": 25,
            "expires_at": "2026-09-20T00:00:00Z"
        }
    }
}
```

---

## 10. Security & Access Control

### 10.1 Supabase RLS

```sql
-- vault_documents: Users can only see documents in their team/scope
CREATE POLICY "user_team_access" ON vault_documents
  FOR SELECT
  USING (
    team_id IN (SELECT team_id FROM team_members WHERE user_id = auth.uid())
  );

-- vault_metadata: Similar RLS
CREATE POLICY "user_scope_access" ON vault_metadata
  FOR SELECT
  USING (
    owner_id = auth.uid() OR
    team_id IN (SELECT team_id FROM team_members WHERE user_id = auth.uid()) OR
    access_scope = 'public'
  );
```

### 10.2 API Rate Limiting

```python
# Per user: 100 requests/minute
# Per conversation: 10 concurrent chats max
@app.middleware("http")
async def rate_limit_vault_chat(request: Request, call_next):
    if request.url.path == "/api/vault/chat":
        user_id = get_current_user_id(request)
        rate_limiter.check_limit(
            key=f"vault_chat:{user_id}",
            limit=100,
            period=60
        )
    return await call_next(request)
```

---

## 11. Monitoring & Observability

### 11.1 Key Metrics

```python
# Metrics to track
metrics = {
    "vault_chat_requests": Counter("requests"),
    "vault_chat_latency": Histogram("latency_ms"),
    "vault_chat_confidence": Histogram("confidence_score"),
    "hallucination_rate": Counter("hallucinations"),
    "validation_pass_rate": Gauge("validation_pass_percent"),
    "section_usage": Counter("section_queries"),
    "vector_search_latency": Histogram("vector_search_ms"),
    "sql_query_latency": Histogram("sql_query_ms")
}
```

### 11.2 Logging

```python
# Log structure
{
    "timestamp": "2026-04-14T10:30:00Z",
    "user_id": "user123",
    "conversation_id": "conv456",
    "query": "최근 AI 프로젝트",
    "scope": "all",
    "sections_searched": ["completed_projects", "research_materials"],
    "sources_found": 15,
    "sql_queries": 2,
    "vector_searches": 1,
    "llm_latency_ms": 450,
    "total_latency_ms": 580,
    "confidence": 0.92,
    "validation_status": "passed",
    "hallucination_detected": False
}
```

---

## 12. 개발 체크리스트

### Backend Development
- [ ] Vault chat router (`routes_vault_chat.py`)
- [ ] Intent detection engine
- [ ] Section-specific query handlers (8개)
- [ ] LLM context builder
- [ ] Hallucination validator
- [ ] Contradiction detector
- [ ] Accuracy validator
- [ ] Database migrations (vault tables)
- [ ] API rate limiting
- [ ] Error handling middleware

### Frontend Development
- [ ] VaultChatUI component
- [ ] ConversationHistory component
- [ ] SourceHighlighter component
- [ ] RelatedDocuments sidebar
- [ ] Search/Filter UI
- [ ] Confidence indicator
- [ ] WebSocket for streaming (optional)

### Testing
- [ ] Unit tests (8+ handlers)
- [ ] Integration tests (4 test cases)
- [ ] E2E tests (critical user flows)
- [ ] Hallucination test suite
- [ ] Data freshness validation

### DevOps
- [ ] CI/CD pipeline updates
- [ ] Monitoring dashboard setup
- [ ] Alerting rules (hallucination rate > 1%)
- [ ] Performance benchmarks

---

## References & Appendix

### A. Embedding Strategy

**Option 1: OpenAI Embeddings (Recommended)**
- Model: `text-embedding-3-small` (1536 dimensions)
- Cost: $0.02 per 1M tokens
- Latency: 100-200ms

**Option 2: Local Embeddings**
- Model: `sentence-transformers/multilingual-MiniLM-L12-v2`
- Cost: Free (on-premise)
- Latency: 50-100ms
- Trade-off: Lower quality than OpenAI

### B. Vector Search Configuration

```python
# Supabase pgvector configuration
VECTOR_SEARCH_CONFIG = {
    "embedding_model": "text-embedding-3-small",
    "embedding_dimension": 1536,
    "similarity_threshold": {
        "high": 0.80,      # Highly relevant
        "medium": 0.65,    # Moderately relevant
        "low": 0.50        # Somewhat relevant
    },
    "max_results_per_section": 10,
    "total_max_results": 50
}
```

### C. Claude Sonnet 4.6 Configuration

```python
CLAUDE_CONFIG = {
    "model": "claude-sonnet-4-6",
    "max_tokens": 2000,
    "temperature": 0.7,  # Balanced creativity vs. factuality
    "top_p": 0.9,
    "system_prompt": SYSTEM_PROMPT_VAULT_CHAT,
    "timeout_seconds": 30
}
```

---

**Document Version**: 1.0  
**Last Updated**: 2026-04-14  
**Next Review**: After Phase 1 Implementation (2026-05-01)
