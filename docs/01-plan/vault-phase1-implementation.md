# Vault Phase 1 — 구현 계획서 (Implementation Plan)

**문서**: TENOPA Vault Phase 1 상세 구현 계획  
**버전**: 1.0  
**작성일**: 2026-04-14  
**예정 기간**: 6주 (2026-05-01 ~ 2026-06-12)  
**대상**: 백엔드(Python/FastAPI) + 프론트엔드(Next.js/React) 개발팀  

---

## 1. Phase 1 개요

### 1.1 목표
- Vault AI Chat 시스템 전체 구현
- 모든 8개 섹션 데이터 적재
- AI Chat 정확성 검증 (테스트 케이스 통과)
- 프로덕션 배포 준비

### 1.2 범위

| 항목 | 내용 | 소유자 | 예상시간 |
|------|------|--------|----------|
| 백엔드 | routes_vault_chat.py, 섹션 핸들러 8개, 검증 엔진 | Backend Lead | 3주 |
| 프론트엔드 | VaultLayout, 섹션 뷰, AI Chat UI, 경력기술서 | Frontend Lead | 3주 |
| 데이터베이스 | 마이그레이션, 초기 데이터 로드, 벡터 임베딩 | Data Engineer | 2주 |
| QA & 테스트 | 단위/통합/E2E 테스트, 검증 테스트 케이스 | QA Lead | 1.5주 |

---

## 2. 백엔드 구현 (Backend)

### 2.1 파일 구조

```
app/
├── api/
│   └── routes_vault_chat.py          # 메인 AI Chat 라우터
│
├── services/
│   ├── vault_chat_service.py         # AI Chat 비즈니스 로직
│   ├── vault_query_router.py         # 의도 감지 & 라우팅
│   ├── vault_handlers/
│   │   ├── completed_projects.py     # 종료프로젝트 핸들러
│   │   ├── company_internal.py       # 회사내부자료 핸들러
│   │   ├── credentials.py            # 실적증명서 핸들러
│   │   ├── government_guidelines.py  # 정부지침 핸들러
│   │   ├── competitors.py            # 경쟁사정보 핸들러
│   │   ├── success_cases.py          # 성공사례 핸들러
│   │   ├── clients_db.py             # 발주처정보 핸들러
│   │   └── research_materials.py     # 리서치자료 핸들러
│   ├── vault_validation.py           # 검증 엔진 (hallucination prevention)
│   ├── vault_context.py              # 대화 문맥 관리
│   └── vault_embedding.py            # 벡터 임베딩 관리
│
├── models/
│   └── vault_schemas.py              # Vault 관련 Pydantic 스키마
│
└── prompts/
    └── vault_prompts.py              # Vault 섹션별 시스템 프롬프트
```

### 2.2 주요 구현 항목

#### 2.2.1 routes_vault_chat.py (핵심 라우터)

```python
# 기본 구조
@router.post("/api/vault/chat")
async def vault_chat(request: VaultChatRequest, current_user: User = Depends(get_current_user)):
    """
    Main entry point for Vault AI Chat
    
    Workflow:
    1. Load conversation context
    2. Detect intent & section
    3. Route to appropriate handler
    4. Retrieve sources (SQL + Vector)
    5. Generate LLM response
    6. Validate response
    7. Save conversation
    8. Return response with metadata
    """
    pass

@router.get("/api/vault/conversations")
async def list_conversations(current_user: User = Depends(get_current_user)):
    """대화 목록 조회"""
    pass

@router.get("/api/vault/conversations/{conv_id}")
async def get_conversation(conv_id: str, current_user: User = Depends(get_current_user)):
    """대화 상세 조회"""
    pass
```

**구현 체크리스트**:
- [ ] VaultChatRequest/Response 스키마 정의
- [ ] Conversation 모델 생성 (CRUD)
- [ ] Authorization 검증 (사용자 팀 권한)
- [ ] Error handling 정의
- [ ] Rate limiting 설정 (100 req/min per user)

---

#### 2.2.2 vault_query_router.py (의도 감지)

```python
class QueryRouter:
    """
    Detects query intent and routes to appropriate handler
    
    Task:
    - Parse natural language query
    - Identify section(s)
    - Identify query type (project_search, team_performance, etc.)
    - Extract filters (date range, team, client, etc.)
    - Route to handler
    """
    
    async def route(self, query: str, conversation_context: List[Dict]) -> RoutingDecision:
        """
        Returns:
        {
            "sections": ["completed_projects", "research_materials"],
            "query_type": "multi_section_synthesis",
            "filters": {...},
            "confidence": 0.92
        }
        """
        pass
```

**구현 디테일**:
- LLM을 사용한 의도 감지 (Claude Haiku로 비용 절감)
- 대화 문맥 활용 (이전 질문과의 연관성)
- 섹션별 쿼리 타입 카테고리화
- 필터 추출 (날짜, 팀, 키워드 등)

---

#### 2.2.3 Section Handlers (8개 섹션별)

```python
# 예: completed_projects.py
class CompletedProjectsHandler:
    """
    Handles queries for completed projects
    
    Primary: SQL (exact facts)
    Secondary: Vector (semantic search)
    """
    
    async def search(self, query: str, filters: Dict) -> QueryResult:
        """
        1. SQL 쿼리 실행 (프로젝트 메타데이터)
        2. Vector 검색 (유사 프로젝트)
        3. 결과 병합 & 중복 제거
        4. 신뢰도 계산
        """
        pass
    
    async def validate_facts(self, project: Dict) -> ValidationReport:
        """
        Validate:
        - 낙찰가와 예산 일치도
        - 낙찰률 계산 정확도
        - 참여인력 정보 완성도
        """
        pass
```

**8개 핸들러 구현 순서** (우선순위):
1. `completed_projects.py` — 데이터 가장 풍부
2. `government_guidelines.py` — SQL only, 정확도 필수
3. `company_internal.py` — 조직 데이터
4. `credentials.py` — 실적증명서
5. `clients_db.py` — 발주처 정보
6. `competitors.py` — 경쟁 분석
7. `success_cases.py` — Vector 중심
8. `research_materials.py` — TTL 관리

---

#### 2.2.4 vault_validation.py (검증 엔진)

```python
class HallucinationValidator:
    """
    3-Point Validation Gate
    """
    
    async def validate(self, response: str, sources: List[Dict], confidence: float) -> ValidationResult:
        """
        Point 1: Source Coherence (출처 일치도)
        - 응답의 모든 주장이 출처에 있는가?
        
        Point 2: Fact Alignment (팩트 검증)
        - SQL 데이터와 모순되지 않는가?
        
        Point 3: Confidence Threshold (신뢰도)
        - 신뢰도 >= 80%인가?
        """
        pass
    
    async def extract_citations(self, response: str) -> List[str]:
        """응답에서 인용문 추출"""
        pass
    
    async def check_fact_alignment(self, response: str, sources: List[Dict]) -> List[Contradiction]:
        """팩트 기반 모순 감지"""
        pass
```

---

### 2.3 Database 변경사항

```sql
-- 새로운 테이블
CREATE TABLE vault_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE vault_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES vault_conversations(id),
    role TEXT NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    sources JSONB, -- 출처 메타데이터
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE vault_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    section TEXT NOT NULL, -- 섹션명
    title TEXT NOT NULL,
    content TEXT,
    embedding vector(1536), -- pgvector 임베딩
    metadata JSONB, -- 메타데이터
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 기존 테이블 확장
ALTER TABLE proposals ADD COLUMN vault_master_file TEXT; -- 마스터파일 경로
```

---

### 2.4 API 통합

#### 기존 Claude API 설정 확인

```python
# app/config.py에서 확인
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = "claude-sonnet-4-6"

# Vault Chat용 설정
VAULT_CHAT_CONFIG = {
    "model": "claude-sonnet-4-6",
    "max_tokens": 2000,
    "temperature": 0.7,
    "timeout_seconds": 30
}

# Vector 임베딩용
EMBEDDING_MODEL = "text-embedding-3-small"  # OpenAI API 필요
EMBEDDING_DIMENSION = 1536
```

---

## 3. 프론트엔드 구현 (Frontend)

### 3.1 파일 구조

```
components/
├── Vault/
│   ├── VaultLayout.tsx              # 메인 레이아웃
│   ├── VaultSidebar.tsx             # 네비게이션
│   ├── VaultSearchBar.tsx           # 통합 검색
│   │
│   ├── sections/
│   │   ├── CompletedProjects.tsx    # 종료프로젝트
│   │   ├── CompanyInternal.tsx      # 회사내부자료
│   │   ├── Credentials.tsx          # 실적증명서
│   │   ├── GovernmentGuidelines.tsx # 정부지침
│   │   ├── Competitors.tsx          # 경쟁사정보
│   │   ├── SuccessCases.tsx         # 성공사례
│   │   ├── ClientsDB.tsx            # 발주처정보
│   │   └── ResearchMaterials.tsx    # 리서치자료
│   │
│   ├── chat/
│   │   ├── VaultChatUI.tsx          # AI Chat 메인
│   │   ├── ConversationHistory.tsx  # 대화 히스토리
│   │   ├── ChatMessage.tsx          # 메시지 렌더
│   │   ├── SourceHighlighter.tsx    # 출처 강조
│   │   ├── RelatedDocuments.tsx     # 관련 자료
│   │   └── ChatInput.tsx            # 입력 필드
│   │
│   ├── modals/
│   │   ├── ProjectDetailModal.tsx   # 프로젝트 상세
│   │   ├── CareerResumeModal.tsx    # 경력기술서 생성
│   │   └── FiltersModal.tsx         # 고급 필터
│   │
│   └── common/
│       ├── DocumentTable.tsx        # 문서 테이블
│       ├── SectionGrid.tsx          # 섹션 카드 그리드
│       ├── ConfidenceBadge.tsx      # 신뢰도 배지
│       └── LoadingState.tsx         # 로딩 상태

app/(app)/vault/
├── page.tsx                         # Vault 메인 페이지
├── [section]/
│   └── page.tsx                     # 섹션별 페이지
└── chat/
    └── page.tsx                     # AI Chat 페이지

lib/
├── api.ts                           # Vault API 호출
├── hooks/
│   ├── useVaultChat.ts              # Chat 상태 관리
│   ├── useVaultSearch.ts            # 검색 상태 관리
│   └── useVaultFilters.ts           # 필터 상태 관리
└── utils/
    ├── formatters.ts                # 데이터 포맷팅
    └── validators.ts                # 유효성 검증
```

### 3.2 주요 구현 항목

#### 3.2.1 VaultLayout (메인 레이아웃)

```typescript
export function VaultLayout({ children }: { children: React.ReactNode }) {
  const [activeSection, setActiveSection] = useState('all')
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  
  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <VaultSidebar 
        activeSection={activeSection}
        onSelectSection={setActiveSection}
      />
      
      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <VaultHeader 
          activeSection={activeSection}
          onMobileMenuToggle={setIsMobileMenuOpen}
        />
        {children}
      </main>
    </div>
  )
}
```

**구현 체크리스트**:
- [ ] 반응형 레이아웃 (데스크톱/태블릿/모바일)
- [ ] 다크 모드 지원
- [ ] 키보드 네비게이션
- [ ] 접근성 (ARIA 라벨)

---

#### 3.2.2 VaultChatUI (AI Chat)

```typescript
export function VaultChatUI({ conversationId }: { conversationId?: string }) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [searchScope, setSearchScope] = useState('all')
  
  const handleSendMessage = async (query: string) => {
    setIsLoading(true)
    try {
      const response = await api.vault.chat({
        message: query,
        conversation_id: conversationId,
        scope: searchScope
      })
      
      setMessages(prev => [
        ...prev,
        { role: 'user', content: query },
        { 
          role: 'assistant', 
          content: response.response,
          sources: response.sources,
          confidence: response.confidence
        }
      ])
    } finally {
      setIsLoading(false)
    }
  }
  
  return (
    <div className="flex flex-col h-full">
      {/* Chat History */}
      <ConversationHistory 
        messages={messages}
        isLoading={isLoading}
      />
      
      {/* Chat Input */}
      <ChatInput 
        onSendMessage={handleSendMessage}
        scope={searchScope}
        onScopeChange={setSearchScope}
      />
    </div>
  )
}
```

**구현 체크리스트**:
- [ ] 메시지 렌더링 (유저/AI)
- [ ] 스트리밍 응답 (선택사항)
- [ ] 출처 표시 (클릭 가능)
- [ ] 관련 자료 사이드바
- [ ] 신뢰도 스코어 표시
- [ ] 대화 저장 및 로드

---

#### 3.2.3 Section Components (8개)

```typescript
// 예: CompletedProjects.tsx
export function CompletedProjects() {
  const [documents, setDocuments] = useState<Project[]>([])
  const [filters, setFilters] = useState<FilterState>({})
  const [viewMode, setViewMode] = useState<'table' | 'grid'>('table')
  const [selectedProject, setSelectedProject] = useState<Project | null>(null)
  
  useEffect(() => {
    const loadProjects = async () => {
      const data = await api.vault.completedProjects(filters)
      setDocuments(data)
    }
    loadProjects()
  }, [filters])
  
  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">종료프로젝트</h1>
        <div className="flex gap-2">
          <button onClick={() => setViewMode('table')}>테이블</button>
          <button onClick={() => setViewMode('grid')}>카드</button>
        </div>
      </div>
      
      <VaultSearchBar onFilter={setFilters} />
      
      {viewMode === 'table' ? (
        <DocumentTable 
          documents={documents}
          onSelect={setSelectedProject}
        />
      ) : (
        <SectionGrid 
          documents={documents}
          onSelect={setSelectedProject}
        />
      )}
      
      {selectedProject && (
        <ProjectDetailModal
          project={selectedProject}
          onClose={() => setSelectedProject(null)}
        />
      )}
    </div>
  )
}
```

---

### 3.3 API 클라이언트 (lib/api.ts)

```typescript
// 기존 api.ts 확장
export const vault = {
  // Chat
  chat: (request: VaultChatRequest): Promise<VaultChatResponse> =>
    apiCall('POST', '/vault/chat', request),
  
  conversations: (): Promise<Conversation[]> =>
    apiCall('GET', '/vault/conversations'),
  
  getConversation: (id: string): Promise<Conversation> =>
    apiCall('GET', `/vault/conversations/${id}`),
  
  // Sections
  completedProjects: (filters?: FilterState): Promise<Project[]> =>
    apiCall('GET', '/vault/completed-projects', { params: filters }),
  
  getProject: (id: string): Promise<Project> =>
    apiCall('GET', `/vault/completed-projects/${id}`),
  
  // 나머지 7개 섹션 API...
  
  // Search
  search: (query: string, scope?: string): Promise<SearchResult[]> =>
    apiCall('GET', '/vault/search', { params: { q: query, scope } }),
  
  // Export
  exportProjects: (projectIds: string[]): Promise<Blob> =>
    apiCall('POST', '/vault/export', { ids: projectIds }, { responseType: 'blob' })
}
```

---

## 4. 데이터 로드 계획 (Data Loading)

### 4.1 마이그레이션 순서

| Step | 작업 | 데이터소스 | 예상시간 |
|------|------|----------|---------|
| 1 | 종료프로젝트 (completed_projects) | proposals 테이블 | 2시간 |
| 2 | 회사내부자료 메타데이터 | intranet_data | 4시간 |
| 3 | 정부지침 데이터 | government_db | 1시간 |
| 4 | 경쟁사 정보 분석 | market_research | 3시간 |
| 5 | 발주처 정보 데이터베이스 | clients_metadata | 2시간 |
| 6 | 성공사례 & 교훈 | project_archive | 1시간 |
| 7 | 실적증명서 마스터파일 | contracts_db | 2시간 |
| 8 | 벡터 임베딩 생성 | all documents | 4시간 |

### 4.2 벡터 임베딩 전략

```python
# 각 문서별 임베딩 생성
async def create_embeddings():
    """
    Process:
    1. 섹션별로 모든 문서 조회
    2. 제목 + 내용 + 메타데이터 조합
    3. OpenAI Embeddings API 호출 (배치 처리)
    4. pgvector에 저장
    5. 인덱스 생성 (HNSW)
    
    Cost: ~$50 (50만 토큰)
    Time: ~4시간
    """
```

---

## 5. 구현 일정 (Timeline)

```
Week 1 (2026-05-01 ~ 2026-05-05)
─────────────────────────────────
Backend:
- [x] routes_vault_chat.py 기본 구조
- [x] vault_query_router.py 구현
- [x] 2개 핸들러 (completed_projects, government_guidelines)

Frontend:
- [x] VaultLayout, VaultSidebar
- [x] CompletedProjects, GovernmentGuidelines 섹션
- [x] VaultSearchBar 기본 구현

Database:
- [x] 마이그레이션 스크립트 작성

Week 2 (2026-05-08 ~ 2026-05-12)
─────────────────────────────────
Backend:
- [x] 6개 핸들러 추가 (company_internal, credentials, ...)
- [x] vault_validation.py 구현
- [x] vault_context.py (대화 관리)

Frontend:
- [x] 6개 섹션 뷰 추가
- [x] ProjectDetailModal 구현
- [x] VaultChatUI 기본 구조

Database:
- [x] Step 1~5 데이터 마이그레이션

Week 3 (2026-05-15 ~ 2026-05-19)
─────────────────────────────────
Backend:
- [x] AI Chat 통합 테스트
- [x] Error handling & rate limiting
- [x] Logging & monitoring

Frontend:
- [x] ChatMessage, SourceHighlighter, RelatedDocuments
- [x] CareerResume auto-generation
- [x] Advanced filters

Database:
- [x] Step 6~8 데이터 로드 및 벡터 임베딩
- [x] 인덱스 생성 및 성능 최적화

Week 4~6 (2026-05-22 ~ 2026-06-12)
────────────────────────────────────
Testing & Polish:
- [x] 단위 테스트 (백엔드)
- [x] 통합 테스트 (API)
- [x] E2E 테스트 (UI 플로우)
- [x] 정확성 검증 (4개 테스트 케이스)
- [x] 성능 최적화
- [x] 버그 수정 및 개선
- [x] 문서화 완성
```

---

## 6. 리스크 및 대응책

| 리스크 | 영향도 | 대응책 |
|--------|--------|--------|
| OpenAI Embeddings API 비용 초과 | 중 | 로컬 임베딩 모델로 대체 |
| 벡터 검색 정확도 부족 (< 80%) | 높음 | SQL 우선순위 상향, 프롬프트 개선 |
| 할루시네이션 제어 실패 | 높음 | 3-Point Validation 강화 |
| 대용량 데이터 로드 실패 | 중 | 배치 처리, 데이터 검증 |
| 프론트엔드 성능 이슈 | 중 | 가상화 스크롤, 컴포넌트 최적화 |

---

## 7. 성공 기준

- [ ] 모든 8개 섹션 구현 완료
- [ ] API 응답 시간 < 3초
- [ ] 4개 테스트 케이스 모두 통과
- [ ] 할루시네이션 검출 < 1%
- [ ] 프론트엔드 Lighthouse 점수 > 90
- [ ] 데이터 초기 로드 완료 (100% 정확도)

---

**Phase 1 구현 완료**: 2026-06-12  
**Phase 2 (테스트/배포) 시작**: 2026-06-15
