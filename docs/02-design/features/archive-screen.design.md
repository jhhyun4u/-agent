---
feature: archive-screen
phase: do
version: 1.0
status: implemented
date: 2026-04-11
---

# Archive Screen (종료프로젝트) — Design Document

## Overview

Archive (종료프로젝트) 화면은 완료된 제안서 프로젝트를 테이블 중심으로 관리하는 읽기 전용 대시보드입니다. 최근 종료순으로 정렬된 프로젝트 리스트, 필터링, 페이지네이션, 상세 모달을 통한 산출물 다운로드를 지원합니다.

---

## 1. User Stories

### As a Sales/PM
- I want to view a list of all completed proposals sorted by deadline (most recent first)
- I want to filter proposals by scope (company-wide / my team / personal)
- I want to filter proposals by win result (all / won / lost / pending)
- I want to see key project metadata in the table: project name, client, result, team, participants, hours worked, token cost
- I want to click on a project to view detailed information and download deliverables

### As a Project Manager
- I want to see token cost for each project for cost tracking
- I want to see bid amount and win rate for performance analysis
- I want to access all artifacts (proposal, supporting docs, presentation) in one place
- I want to understand which team completed each project

---

## 2. Requirements

### Functional Requirements

#### F1: Document List (GET /api/archive/list)
- Display paginated list of completed projects
- Fetch with filters: `scope` (company/team/personal), `win_result` (won/lost/pending)
- Sort by deadline DESC (client-side)
- Display 11-column table with metadata

#### F2: Table Columns (11 total)
```
1. 연도          (year extracted from deadline)
2. 과제명        (title)
3. 키워드        (positioning/keyword)
4. 발주처        (client_name)
5. 결과          (win_result badge: won/lost/pending)
6. 작업시간      (elapsed_seconds formatted)
7. 토큰비용      (total_token_cost formatted)
8. 팀           (team_name)
9. 참여자        (participants joined)
10. 낙찰가       (bid_amount formatted)
11. 낙찰율      (win_rate calculated)
```

#### F3: Filtering
- Scope tabs: 전체 / 우리팀 / 나의
- Win result filters: 전체 / 수주 / 낙찰실패 / 대기
- Reset pagination to page 1 on filter change

#### F4: Pagination
- Display current page / total pages
- Previous/Next buttons with disabled state on boundaries
- Show total count of items

#### F5: Detail Modal
- Click table row → open Modal (size="xl")
- Modal title: project title
- Overview section: 2-column grid with 8 metadata fields:
  - Row 1: client_name, deadline
  - Row 2: win_result badge, team_name
  - Row 3: participants, elapsed_seconds
  - Row 4: token_cost, bid_amount
- Artifacts section: ProjectArchivePanel for file downloads

#### F6: Data Formatting
- Year: extract from deadline (YYYY-MM-DD → YYYY)
- Currency: format as "50억원" (₩50B) or "500만원" (₩5M)
- Time: format as "45h 30m" or "120m"
- Token cost: "$12.34" USD
- Win rate: percentage (bid / budget * 100)

### Non-Functional Requirements

#### N1: Performance
- Pagination limit: 20-50 items per page (API configured)
- Client-side sorting does not block render (useMemo)
- Modal opens instantly (selectedItem state)

#### N2: Accessibility
- Table has `role="table"` + proper `<thead>/<tbody>`
- Table has `<caption>` for screen readers
- Column headers have `scope="col"`
- Badge colors meet WCAG AA contrast

#### N3: Error Handling
- API error: display error banner with message
- Empty state: "완료된 제안서가 없습니다"
- Loading state: 5 skeleton rows with pulse animation

---

## 3. Data Model

### ArchiveItem (from api.ts)
```typescript
interface ArchiveItem {
  id: string
  title: string
  client_name: string | null
  deadline: string | null      // ISO date
  win_result: "won" | "lost" | "pending" | null
  team_name: string | null
  participants: string[]        // array of names
  elapsed_seconds: number | null
  total_token_cost: number | null
  bid_amount: number | null
  budget: number | null
  positioning: string | null
  created_at: string
}
```

### API Response
```typescript
interface ArchiveListResponse {
  data: ArchiveItem[]
  meta: {
    total: number
    pages: number
    page: number
    limit: number
  }
}
```

---

## 4. Component Architecture

```
archive/page.tsx (447 lines)
├── Imports
│   ├── React hooks (useState, useEffect, useCallback, useMemo)
│   ├── api (ArchiveItem type, list endpoint)
│   ├── Modal (detail panel)
│   └── ProjectArchivePanel (artifacts)
│
├── Constants
│   ├── SCOPE_TABS (전체/우리팀/나의)
│   └── WIN_RESULT_FILTERS (전체/수주/낙찰실패/대기)
│
├── Formatting Functions
│   ├── extractYear(iso: string) → "2025"
│   ├── formatCurrency(value) → "50억원"
│   ├── formatElapsedTime(seconds) → "45h 30m"
│   ├── formatTokenCost(cost) → "$12.34"
│   ├── formatWinRate(bid, budget) → "85%"
│   └── WinResultBadge (component)
│
├── Main Component (ArchivePage)
│   ├── State
│   │   ├── items: ArchiveItem[]
│   │   ├── loading: boolean
│   │   ├── error: string
│   │   ├── scope: string
│   │   ├── winResult: string
│   │   ├── page: number
│   │   ├── totalPages: number
│   │   ├── total: number
│   │   ├── selectedItem: ArchiveItem | null
│   │   └── detailOpen: boolean
│   │
│   ├── Effects
│   │   ├── loadItems() [scope, winResult, page]
│   │   └── useCallback: changeScope, changeWinResult
│   │
│   ├── Computed
│   │   └── sortedItems (deadline DESC, useMemo)
│   │
│   └── Render
│       ├── Header
│       ├── Filter Bar
│       │   ├── Scope tabs (button group)
│       │   └── Win result filters (button group)
│       ├── Table Area
│       │   ├── Error banner
│       │   ├── 11-column table
│       │   │   ├── Thead: headers + scopes
│       │   │   └── Tbody: data rows
│       │   │       ├── Loading skeletons
│       │   │       ├── Empty state
│       │   │       └── Data rows (clickable)
│       │   └── Pagination
│       └── Detail Modal (size="xl")
│           ├── Overview (2-col grid)
│           ├── Divider
│           └── ProjectArchivePanel
```

---

## 5. Styling Notes

### Color Palette
- Background: `bg-[#111111]` (dark)
- Borders: `border-[#262626]`
- Text primary: `text-[#ededed]`
- Text secondary: `text-[#8c8c8c]`
- Badges:
  - Won: green `bg-[#3ecf8e]/15 text-[#3ecf8e]`
  - Lost: red `bg-red-500/15 text-red-400`
  - Pending: gray `bg-[#262626] text-[#8c8c8c]`

### Table Widths
- Year: `w-16` (center)
- Result: `w-16` (center)
- Hours: `w-20` (right)
- Cost: `w-20` (right)
- Bid: `w-24` (right)
- Rate: `w-16` (center)
- Others: `min-w-[80px]` to `min-w-[200px]` with truncate

### Responsiveness
- Table: horizontal overflow on mobile
- Modal: `size="xl"` → `max-w-4xl`
- Filter buttons: wrap on small screens

---

## 6. States & Transitions

### Page States
```
LOADING
  ↓ (API response)
LOADED (with data)
  ↓ (filter change / pagination)
LOADING (spinner)
  ↓
LOADED (new data)

Empty State
  ← when data.length === 0

Error State
  ← when API fails
  → retry (filter change)
```

### Modal States
```
CLOSED (detailOpen: false)
  ↓ (click row)
OPENING (selectedItem set)
  ↓
OPEN (modal visible)
  ↓ (click close / backdrop)
CLOSED

Row Click Handler:
  setSelectedItem(item)
  setDetailOpen(true)
```

---

## 7. API Integration

### Endpoint: GET /api/archive/list

**Query Parameters:**
```
scope: "company" | "team" | "personal"
win_result?: "won" | "lost" | "pending" (optional, empty = all)
page: number (1-indexed)
limit?: number (default 20)
```

**Success Response (200):**
```json
{
  "data": [
    {
      "id": "proposal-abc123",
      "title": "AI 제안서 작성 플랫폼",
      "client_name": "OOO 주식회사",
      "deadline": "2025-01-15T00:00:00Z",
      "win_result": "won",
      "team_name": "AI팀",
      "participants": ["김철수", "이영희"],
      "elapsed_seconds": 164700,
      "total_token_cost": 12.34,
      "bid_amount": 500000000,
      "budget": 600000000,
      "positioning": "NLP 기술",
      "created_at": "2024-12-01T10:00:00Z"
    }
  ],
  "meta": {
    "total": 24,
    "pages": 2,
    "page": 1,
    "limit": 20
  }
}
```

**Error Response (400):**
```json
{
  "error": "Invalid scope parameter"
}
```

**No Data (200):**
```json
{
  "data": [],
  "meta": { "total": 0, "pages": 0, "page": 1, "limit": 20 }
}
```

---

## 8. Testing Strategy

### Unit Tests
- formatYear, formatCurrency, formatElapsedTime
- WinResultBadge rendering (4 badge types)

### Integration Tests
- Archive list fetch + filter + pagination
- Table sorting (deadline DESC)
- Modal open/close
- Error handling

### E2E Tests
- Load archive page → see table
- Filter by scope → table updates
- Filter by win_result → table updates
- Click row → modal opens + overview visible
- Download file from ProjectArchivePanel

---

## 9. File References

### Frontend
- **Page:** `frontend/app/(app)/archive/page.tsx` (447 lines)
- **Components:**
  - `frontend/components/ui/Modal.tsx` (generic)
  - `frontend/components/ProjectArchivePanel.tsx` (artifacts)

### Backend
- **Endpoint:** `app/api/routes.py` (archive router)
- **Database:** `archive` view + RLS

---

## 10. Success Criteria

1. ✅ Display 11-column table with all metadata
2. ✅ Sort by deadline DESC (most recent first)
3. ✅ Filter by scope (company/team/personal)
4. ✅ Filter by win_result (won/lost/pending)
5. ✅ Pagination (page/totalPages)
6. ✅ Click row → modal with overview + artifacts
7. ✅ Download files from modal
8. ✅ Error handling + empty state

---

## Notes

- **Decision:** 11 columns retained (vs 7-column reduced version) for information richness
- **Sorting:** Client-side sort via useMemo (not API)
- **Modal:** Uses existing Modal + ProjectArchivePanel components
- **No statistics dashboard:** Removed KPI cards, charts, team performance widgets
