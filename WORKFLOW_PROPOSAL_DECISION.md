# 제안결정 완전 워크플로 (from-bid)

## 📊 엔드-투-엔드 흐름

```
┌─ Frontend (공고 모니터링) ────────────────────────────────────────────┐
│                                                                       │
│  [공고 목록]                                                         │
│  • 공고-001: OO시 도시재정사업                                       │
│  • 공고-002: XX구청 정보화사업                                       │
│  • [제안결정] ← 사용자 클릭                                          │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
              POST /api/proposals/from-bid
                    { "bid_no": "2026-001" }
                            ↓
┌─ Backend (routes_proposal.py) ─────────────────────────────────────┐
│                                                                     │
│ Step 1️⃣ 공고 정보 조회 (bid_announcements)                        │
│  └─ bid_no="2026-001" → 공고명, 부서, 구분 획득                  │
│                                                                     │
│ Step 2️⃣ 사용자 정보 확정 (로그인된 사용자 = 조직/팀 기 소속)    │
│  ├─ owner_id = auth.user.id                                       │
│  ├─ team_id = auth.user.team_id                                   │
│  └─ org_id = auth.user.org_id                                     │
│                                                                     │
│ Step 3️⃣ 제안 프로젝트 생성 (proposals INSERT)                      │
│  ├─ go_decision: TRUE  ✅ (제안결정)                              │
│  ├─ bid_tracked: FALSE ✅ (공고 목록에서 숨김)                    │
│  ├─ owner_id: (사용자 ID)                                        │
│  ├─ team_id: (담당팀 - 사용자 소속팀)                            │
│  └─ status: "initialized"                                        │
│                                                                     │
│ Step 4️⃣ 작업 목록 생성 (proposal_tasks INSERT)                    │
│  ├─ proposal_id: (위 제안 ID)                                    │
│  ├─ assigned_team_id: (사용자 팀)                                │
│  ├─ status: "waiting"   ⏳ (대기 상태)                           │
│  ├─ priority: "normal"                                           │
│  └─ description: "공고-001 제안 프로젝트: ..."                   │
│                                                                     │
│ Step 5️⃣ 워크플로 자동 시작 (LangGraph 백그라운드)               │
│  └─ graph.ainvoke() → STEP_0 → STEP_1 → ...                     │
│                                                                     │
│ Response: 201 Created                                             │
│ {                                                                  │
│   "proposal_id": "xxxxxxxx-xxxx-...",                            │
│   "title": "공고-001",                                           │
│   "status": "initialized",                                       │
│   "workflow_started": true                                       │
│ }                                                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─ Database (Supabase PostgreSQL) ──────────────────────────────────┐
│                                                                    │
│ proposals 테이블:                                                │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ id      │ title     │ go_decision │ bid_tracked │ team_id  │ │
│ ├─────────┼───────────┼─────────────┼─────────────┼──────────┤ │
│ │ abc-123 │ 공고-001  │    TRUE ✅  │   FALSE ✅  │ team-01  │ │
│ └─────────┴───────────┴─────────────┴─────────────┴──────────┘ │
│                                                                    │
│ proposal_tasks 테이블:                                          │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ id      │ proposal  │ assigned_team │ status  │ priority   │ │
│ ├─────────┼───────────┼───────────────┼─────────┼────────────┤ │
│ │ def-456 │ abc-123   │ team-01       │ waiting │ normal     │ │
│ └─────────┴───────────┴───────────────┴─────────┴────────────┘ │
│                                                                    │
│ ai_task_logs 테이블: (워크플로 진행 추적)                        │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ id      │ proposal  │ step    │ status  │ created_at       │ │
│ ├─────────┼───────────┼─────────┼─────────┼──────────────────┤ │
│ │ ghi-789 │ abc-123   │ STEP_0  │ running │ 2026-04-10 ...   │ │
│ └─────────┴───────────┴─────────┴─────────┴──────────────────┘ │
│                                                                    │
└────────────────────────────────────────────────────────────────┘
                            ↓
┌─ Frontend UI 변화 ────────────────────────────────────────────┐
│                                                                  │
│ 1️⃣ 공고 모니터링 화면                                         │
│    (bid_tracked=FALSE로 제안결정된 항목 자동으로 숨김)        │
│    ┌──────────────────────────────────────┐                   │
│    │ 공고 목록                             │                   │
│    │ • 공고-002: XX구청 ...               │                   │
│    │ • 공고-003: YY시청 ...               │                   │
│    │ (공고-001은 숨김 ✓)                 │                   │
│    └──────────────────────────────────────┘                   │
│                                                                  │
│ 2️⃣ 제안 작업 목록 (새로운 탭/페이지)                          │
│    (proposal_tasks 테이블 기반)                               │
│    ┌──────────────────────────────────────┐                   │
│    │ 제안 작업 현황                        │                   │
│    │ ┌─ 공고-001 제안 프로젝트           │                   │
│    │ │ ├─ 담당팀: A팀 (team-01)         │                   │
│    │ │ ├─ 상태: 대기 ⏳                 │                   │
│    │ │ ├─ 우선순위: 일반                  │                   │
│    │ │ ├─ 마감: 2026-04-24 (2주)        │                   │
│    │ │ └─ [진행중] [완료] [재작업]       │                   │
│    │ └─ AI 워크플로: 진행 중... (STEP_0) │                   │
│    └──────────────────────────────────────┘                   │
│                                                                  │
│ 3️⃣ 제안 상세 페이지                                           │
│    (proposals 테이블 기반)                                    │
│    ┌──────────────────────────────────────┐                   │
│    │ 제안 프로젝트: 공고-001              │                   │
│    │ • 제안결정: ✅ YES (2026-04-10)    │                   │
│    │ • 담당팀: A팀                        │                   │
│    │ • 상태: 초기화 (AI 작업 중...)      │                   │
│    │ • 현재 단계: STEP_0                 │                   │
│    │ • AI 워크플로: 자동 진행 중 🚀     │                   │
│    └──────────────────────────────────────┘                   │
│                                                                  │
└──────────────────────────────────────────────────────────────┘
```

## 📋 기술 명세

### 1️⃣ 필요한 컬럼 추가 (proposals 테이블)

```sql
-- 마이그레이션: 005_proposal_decision_and_tasks.sql 참고
ALTER TABLE proposals 
  ADD COLUMN go_decision BOOLEAN DEFAULT false,
  ADD COLUMN decision_date TIMESTAMPTZ,
  ADD COLUMN bid_tracked BOOLEAN DEFAULT true;
```

### 2️⃣ 새 테이블 생성 (proposal_tasks)

```sql
CREATE TABLE proposal_tasks (
    id              UUID PRIMARY KEY,
    proposal_id     UUID REFERENCES proposals(id),
    assigned_team_id UUID REFERENCES teams(id),
    description     TEXT,
    status          TEXT DEFAULT 'waiting',  -- waiting | in_progress | completed | blocked
    priority        TEXT DEFAULT 'normal',
    due_date        TIMESTAMPTZ,
    created_by_id   UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);
```

### 3️⃣ Backend 로직 (routes_proposal.py)

```python
# from-bid 엔드포인트
POST /api/proposals/from-bid

# 입력
{
  "bid_no": "2026-001"
}

# 처리 순서
1. 공고 정보 조회
2. 사용자 정보 확정 (이미 로그인 = 조직/팀 기보유)
3. proposals INSERT
   - go_decision = TRUE
   - bid_tracked = FALSE
   - owner_id = 사용자 ID
   - team_id = 사용자 팀
   
4. proposal_tasks INSERT
   - assigned_team_id = 사용자 팀
   - status = 'waiting'
   - description = 공고 정보 기반
   - due_date = 현재 + 14일
   
5. LangGraph 워크플로 시작 (백그라운드)
```

### 4️⃣ Frontend 조회 엔드포인트

```
GET /api/proposals          → go_decision, bid_tracked 표시
GET /api/proposals/{id}     → 제안 상세 + 작업 목록
GET /api/proposal-tasks     → 작업 목록 조회 (추가 구현)
```

## ✅ 검증 체크리스트

- [ ] 마이그레이션 실행: `005_proposal_decision_and_tasks.sql`
- [ ] Supabase RLS 정책 적용 (proposal_tasks)
- [ ] Backend 코드 배포 (routes_proposal.py 수정)
- [ ] Pydantic 스키마 업데이트 (ProposalTaskResponse 추가)
- [ ] Frontend: 공고 목록에서 bid_tracked=false 필터 추가
- [ ] Frontend: 새로운 "제안 작업 목록" 탭 추가
- [ ] E2E 테스트: 제안결정 → 작업 목록 생성 → 워크플로 시작

## 🔍 기대 효과

| 항목 | 변화 |
|------|------|
| **공고 모니터링** | 제안결정된 항목 자동 숨김 (정리) |
| **작업 추적** | proposal_tasks로 팀별 제안 작업 시각화 |
| **워크플로** | 자동 시작 + 진행 상황 ai_task_logs 기록 |
| **데이터 일관성** | 제안결정 = 즉시 작업 목록 생성 |
| **팀 협업** | 담당팀이 자신의 작업 목록에서 진행 상황 추적 |
