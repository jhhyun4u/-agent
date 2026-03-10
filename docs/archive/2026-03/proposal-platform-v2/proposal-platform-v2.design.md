# Design: proposal-platform-v2

## 메타 정보
| 항목 | 내용 |
|------|------|
| Feature | proposal-platform-v2 |
| 작성일 | 2026-03-08 |
| 기반 Plan | docs/01-plan/features/proposal-platform-v2.plan.md |
| 구현 순서 | Phase A → B → C → D |

---

## Phase A: 섹션 라이브러리 + 아카이브

### A-1. DB 스키마

```sql
-- 섹션 라이브러리
CREATE TABLE sections (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id     UUID REFERENCES teams(id) ON DELETE CASCADE,
  owner_id    UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title       TEXT NOT NULL,
  category    TEXT NOT NULL CHECK (category IN (
                'company_intro',   -- 회사소개
                'track_record',    -- 수행실적
                'methodology',     -- 기술방법론
                'organization',    -- 조직/인력
                'schedule',        -- 추진일정
                'cost',            -- 원가/예산
                'other'
              )),
  content     TEXT NOT NULL,       -- 마크다운
  tags        TEXT[] DEFAULT '{}',
  is_public   BOOLEAN NOT NULL DEFAULT false,  -- 전체 공개
  use_count   INT NOT NULL DEFAULT 0,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX sections_category_idx ON sections(category);
CREATE INDEX sections_team_idx ON sections(team_id);

-- 회사 자료 (PDF/DOCX 업로드 → AI 분석 → sections 자동 추출)
CREATE TABLE company_assets (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id      UUID REFERENCES teams(id) ON DELETE CASCADE,
  owner_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  filename     TEXT NOT NULL,
  storage_path TEXT NOT NULL,
  file_type    TEXT NOT NULL,
  status       TEXT NOT NULL DEFAULT 'pending'
                 CHECK (status IN ('pending','processing','done','failed')),
  extracted_sections UUID[],  -- 추출된 section ids
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- proposals 테이블에 섹션 연결 컬럼 추가
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS section_ids UUID[] DEFAULT '{}';
```

### A-2. 백엔드 API

```
GET    /api/resources/sections    목록 (category, q, scope 필터)
POST   /api/resources/sections    생성
PUT    /api/resources/sections/{id}    수정
DELETE /api/resources/sections/{id}   삭제

POST   /api/assets                회사 자료 업로드
GET    /api/assets                목록
DELETE /api/assets/{id}           삭제

GET    /api/archive               제안서 아카이브 (scope: company|team|personal)
```

**섹션 컨텍스트 주입 (phase_executor 수정):**
```python
# phase_executor._build_context() 에 추가
if proposal.section_ids:
    sections = await get_sections(proposal.section_ids)
    context += "\n\n## 우리 회사 참고 자료\n"
    for s in sections:
        context += f"\n### {s.title}\n{s.content}\n"
```

### A-3. 프론트엔드

**신규 페이지:**
- `/resources` — 탭: [섹션 라이브러리 | 회사 자료]
  - 섹션 카드 그리드 (카테고리 필터, 검색)
  - 섹션 생성/편집 모달
  - 회사 자료 업로드 + 추출 상태 표시

- `/archive` — 아카이브 뷰어
  - 스코프 탭: [전체 | 우리 팀 | 나]
  - 수주결과 필터 (수주/낙찰실패/대기)
  - 테이블: 제목, 발주처, 날짜, 결과, 팀

**수정 페이지:**
- `/proposals/new` — 스텝 2 추가: "관련 섹션 선택 (선택사항)"
  - 카테고리별 섹션 체크박스
  - 선택된 섹션은 AI 컨텍스트에 포함됨

**사이드바 네비게이션 추가:**
```
제안서        /proposals
자료 관리     /resources    ← 신규
아카이브      /archive      ← 신규
팀 관리       /admin
```

---

## Phase B: 작업 단계 + 버전관리

### B-1. DB 스키마

```sql
-- proposals 테이블: 버전 관리 컬럼 추가
ALTER TABLE proposals
  ADD COLUMN IF NOT EXISTS version      INT NOT NULL DEFAULT 1,
  ADD COLUMN IF NOT EXISTS parent_id    UUID REFERENCES proposals(id) ON DELETE SET NULL;

-- 버전 인덱스
CREATE INDEX proposals_parent_idx ON proposals(parent_id);
```

### B-2. 백엔드 API

```
POST /api/proposals/{id}/retry-from/{phase_num}   특정 Phase부터 재시작
GET  /api/proposals/{id}/versions                  버전 목록 (parent_id 기반)
POST /api/proposals/{id}/new-version               새 버전 생성 (기존 복사)
```

### B-3. 프론트엔드

**`/proposals/[id]` 개선:**

```
┌─────────────────────────────────────────────────┐
│ 제안서명               상태 배지    버전: v2 ▼  │
├─────────────────────────────────────────────────┤
│                                                 │
│  Phase 진행 대시보드                            │
│  ① RFP 분석  ② 경쟁사  ③ 전략  ④ 본문  ⑤ 검증│
│  ✅ 완료    ✅ 완료  🔄 진행중  ⏳      ⏳      │
│                       ████░░░░ 45%              │
│                                                 │
├─────────────────────────────────────────────────┤
│ [결과물] [댓글] [수주결과] [버전 비교]           │
│                                                 │
│ Phase 3 결과물 (전략 수립)                      │
│  ├── 핵심 차별화 전략: ...                      │
│  └── 가격 전략: ...                             │
└─────────────────────────────────────────────────┘
```

**버전 관리 UI:**
- 상단 드롭다운: v1 / v2 / v3 전환
- "새 버전 생성" 버튼 → 현재 RFP로 재생성
- v1 vs v2 결과물 비교 (나란히 표시)

**Phase별 재시작:**
- 각 Phase 카드에 "이 단계부터 재시작" 버튼 (실패 시)
- Phase 3 실패 → Phase 3부터만 재실행

---

## Phase C: 공통서식 라이브러리

### C-1. DB 스키마

```sql
CREATE TABLE form_templates (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  team_id      UUID REFERENCES teams(id) ON DELETE SET NULL,
  title        TEXT NOT NULL,
  agency       TEXT,            -- 발주 기관명 (행안부, 과기부 등)
  category     TEXT,            -- 서식 유형
  description  TEXT,
  storage_path TEXT NOT NULL,   -- proposal-files 버킷
  file_type    TEXT NOT NULL,
  is_public    BOOLEAN NOT NULL DEFAULT false,
  use_count    INT NOT NULL DEFAULT 0,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- proposals 테이블에 서식 연결
ALTER TABLE proposals
  ADD COLUMN IF NOT EXISTS form_template_id UUID REFERENCES form_templates(id);
```

### C-2. 백엔드 API

```
GET    /api/form-templates          목록 (agency, category 필터)
POST   /api/form-templates          업로드
DELETE /api/form-templates/{id}     삭제
```

**서식 적용 (phase_executor):**
```python
if proposal.form_template_id:
    template = await get_form_template(proposal.form_template_id)
    prompt += f"\n서식 요구사항: {template.description}\n"
    prompt += "위 서식의 구조와 항목에 맞춰 제안서를 작성하세요."
```

### C-3. 프론트엔드

**`/resources` 탭 추가:** [섹션 라이브러리 | 회사 자료 | **공통서식**]

**`/proposals/new` 스텝 추가:**
- 스텝 1: RFP 파일 업로드
- 스텝 2: 서식 선택 (선택사항) ← 신규
- 스텝 3: 섹션 선택 (선택사항)
- 스텝 4: 기본 정보 입력 + 제출

---

## Phase D: 수주율 대시보드 + RFP 캘린더

### D-1. DB 스키마

```sql
CREATE TABLE rfp_calendar (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id      UUID REFERENCES teams(id) ON DELETE CASCADE,
  owner_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title        TEXT NOT NULL,
  agency       TEXT,
  deadline     TIMESTAMPTZ NOT NULL,
  proposal_id  UUID REFERENCES proposals(id) ON DELETE SET NULL,
  status       TEXT NOT NULL DEFAULT 'open'
                 CHECK (status IN ('open','submitted','won','lost')),
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### D-2. 백엔드 API

```
GET /api/stats/win-rate     수주율 통계 (기관별, 팀원별, 월별)
GET /api/calendar           RFP 캘린더 목록
POST /api/calendar          일정 등록
PUT /api/calendar/{id}      일정 수정/상태 변경
```

### D-3. 프론트엔드

**`/dashboard` 신규 페이지:**
```
┌─────────────────────────────────────────┐
│ 수주율 개요                              │
│  전체 35%  |  이번 달 50%  |  내 수주 4건│
├─────────────────────────────────────────┤
│ 기관별 수주율 (막대 차트)                │
│ 월별 추이 (라인 차트)                    │
├─────────────────────────────────────────┤
│ RFP 캘린더                              │
│  D-3  국토부 스마트시티 플랫폼           │
│  D-7  행안부 AI 행정 시스템              │
│  D-15 과기부 연구개발 지원               │
└─────────────────────────────────────────┘
```

---

## 공통 사항

### RLS 정책 추가

```sql
-- sections
ALTER TABLE sections ENABLE ROW LEVEL SECURITY;
CREATE POLICY sections_access ON sections
  USING (
    is_public = true
    OR owner_id = auth.uid()
    OR team_id IN (SELECT team_id FROM team_members WHERE user_id = auth.uid())
  );

-- 나머지 신규 테이블도 동일 패턴 적용
```

### 사이드바 최종 구조

```
T  Tenopa Proposer
─────────────────
☰  제안서          /proposals
+  새 제안서       /proposals/new
─────────────────
▦  대시보드        /dashboard      ← Phase D
□  자료 관리       /resources      ← Phase A
≡  아카이브        /archive        ← Phase A
📋 공통서식        /resources?tab=templates  ← Phase C
─────────────────
◎  팀 관리         /admin
─────────────────
   user@email
↪  로그아웃
```

### 구현 파일 목록 (전체)

**백엔드:**
- `app/api/routes_resources.py` — 섹션 + 자료 API
- `app/api/routes_archive.py` — 아카이브 API
- `app/api/routes_templates.py` — 서식 API
- `app/api/routes_stats.py` — 통계 API
- `app/api/routes_calendar.py` — 캘린더 API
- `app/services/asset_extractor.py` — 자료 → 섹션 AI 추출
- `app/services/phase_executor.py` — 섹션/서식 컨텍스트 주입 수정

**프론트엔드:**
- `frontend/app/resources/page.tsx` — 자료 관리
- `frontend/app/archive/page.tsx` — 아카이브
- `frontend/app/dashboard/page.tsx` — 대시보드
- `frontend/app/proposals/new/page.tsx` — 멀티스텝 수정
- `frontend/app/proposals/[id]/page.tsx` — 단계 대시보드 개선
- `frontend/app/proposals/layout.tsx` — 사이드바 업데이트

**DB:**
- `database/schema_v2.sql` — 추가 테이블/컬럼
