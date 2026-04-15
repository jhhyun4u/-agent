---
feature: archive-screen
phase: plan
version: 1.0
status: complete
date: 2026-04-11
---

# Archive Screen — Plan Document

## Executive Summary

| Perspective | Description |
|-------------|-------------|
| **Problem** | Sales/PM teams need to view and manage completed proposal projects with full metadata and downloadable artifacts |
| **Solution** | Implement table-centric dashboard with filtering (scope/win_result), pagination, detailed modal with overview + file downloads |
| **Effect** | Enables historical project tracking, performance analysis (win rates, team metrics), and artifact retrieval |
| **Value** | Organizational knowledge capture + operational efficiency in post-project review process |

---

## 1. Problem Statement

### As-Is
- Completed proposals scattered across different storage locations
- Limited visibility into project metrics (team performance, costs, win rates)
- No centralized archive or historical tracking
- Manual process for retrieving project artifacts and deliverables

### To-Be
- Unified archive screen showing all completed proposals
- Rich metadata per project (client, result, team, hours, costs, bid info)
- One-click access to all project artifacts (proposals, presentations, supporting docs)
- Enables performance analytics and lessons learned capture

---

## 2. User Stories & Acceptance Criteria

### US1: View Completed Projects
**As a** Sales/PM  
**I want to** see a list of all completed proposals sorted by deadline  
**So that** I can track project history and outcomes

**Acceptance Criteria:**
- ✅ Table displays 11 columns with all metadata
- ✅ Sorted by deadline descending (most recent first)
- ✅ Shows title, client, result, team, hours, costs, bid info
- ✅ Responsive design (horizontal scroll on mobile)

### US2: Filter by Scope
**As a** PM  
**I want to** filter projects by scope (company-wide / my team / personal)  
**So that** I can focus on relevant projects

**Acceptance Criteria:**
- ✅ 3 scope tabs: 전체 / 우리팀 / 나의
- ✅ Filter updates table immediately
- ✅ Pagination resets to page 1
- ✅ Clear visual indication of active filter

### US3: Filter by Win Result
**As a** PM  
**I want to** filter by outcome (all / won / lost / pending)  
**So that** I can analyze win/loss patterns

**Acceptance Criteria:**
- ✅ 4 filter buttons with toggle states
- ✅ Multiple filters can be combined with scope
- ✅ Applied instantly to table
- ✅ Disabled state on inactive buttons

### US4: Paginate Results
**As a** PM  
**I want to** navigate through multiple pages of projects  
**So that** I can browse larger datasets efficiently

**Acceptance Criteria:**
- ✅ Previous/Next buttons with disabled states
- ✅ Current page indicator (e.g., "1 / 5")
- ✅ Total count display
- ✅ 20 items per page (configurable)

### US5: View Project Details
**As a** PM  
**I want to** click a project to view full details and metadata  
**So that** I can understand project specifics and decision context

**Acceptance Criteria:**
- ✅ Click table row → modal opens
- ✅ Modal shows overview section (2-column grid)
- ✅ 8 metadata fields: client, deadline, result, team, participants, hours, cost, bid
- ✅ Modal size consistent with other screens (max-w-4xl)

### US6: Download Project Artifacts
**As a** PM  
**I want to** download proposals, presentations, and supporting documents  
**So that** I can reference or reuse project materials

**Acceptance Criteria:**
- ✅ Modal includes ProjectArchivePanel component
- ✅ Shows categorized file list (proposals, presentations, etc.)
- ✅ Individual file download + ZIP bundle option
- ✅ File sizes and metadata visible

---

## 3. Requirements

### Functional Requirements

#### FR1: Document List API
- Endpoint: `GET /api/archive/list`
- Query params: `scope` (company/team/personal), `win_result` (optional), `page` (1-indexed)
- Response: paginated list of ArchiveItem objects
- Sorting: server-side by `deadline DESC` OR client-side sort after fetch

#### FR2: Data Display — 11 Columns
1. 연도 (year extracted from deadline)
2. 과제명 (project title)
3. 키워드 (positioning/keyword)
4. 발주처 (client name)
5. 결과 (win result badge: won/lost/pending)
6. 작업시간 (elapsed seconds formatted as "45h 30m")
7. 토큰비용 (total token cost as "$12.34")
8. 팀 (team name)
9. 참여자 (participants list, comma-separated)
10. 낙찰가 (bid amount formatted as currency)
11. 낙찰율 (win rate percentage: bid/budget*100)

#### FR3: Filtering
- Scope: Company-wide / Team / Personal (3 options)
- Win Result: All / Won / Lost / Pending (4 options)
- Filters apply independently
- Filter changes reset pagination to page 1

#### FR4: Pagination
- Previous/Next buttons
- Current page indicator (e.g., "1 / 5")
- Total item count
- Items per page: 20 (configurable in API)

#### FR5: Detail Modal
- Triggered by clicking table row
- Size: `"xl"` (max-w-4xl in Tailwind)
- Title: Project title
- Content sections:
  - Overview (2-column grid with 8 fields)
  - Divider
  - Artifacts (ProjectArchivePanel)

#### FR6: Data Formatting
- **Year:** Extract from deadline ISO string (YYYY-MM-DD → YYYY)
- **Currency:** ≥₩1B = "50억원" | <₩1B = "500만원"
- **Time:** 3600+ sec = "45h 30m" | else = "120m"
- **Token Cost:** "$12.34" USD format
- **Win Rate:** "(bid/budget)*100" → "85%"

#### FR7: States & Errors
- Loading: 5 skeleton rows with pulse animation
- Empty: "완료된 제안서가 없습니다" centered message
- Error: Red banner with error message + retry option
- Sorting: Deadline DESC (useMemo, not blocking render)

### Non-Functional Requirements

#### NFR1: Performance
- Table rendering: <100ms (no blocking)
- Pagination: Instant page change (no refetch on client-side sort)
- Modal open: <50ms (instant show)
- API call: <2s (standard timeouts)

#### NFR2: Accessibility
- Semantic HTML: `<table>`, `<thead>`, `<tbody>`, `<caption>`
- WCAG AA contrast for all text and badges
- Keyboard navigation support (tab through buttons)
- Screen reader: caption describes table purpose

#### NFR3: Styling
- Dark theme: `bg-[#111111]`, `text-[#ededed]`, `border-[#262626]`
- Badge colors: Green (won), Red (lost), Gray (pending)
- Button states: active, hover, disabled
- Responsive: Horizontal scroll on mobile (<768px)

#### NFR4: Error Handling
- API timeout: Display error message + allow retry
- Network error: Show error banner
- Invalid filters: Silently ignore or show validation error
- No data: Show empty state (not error)

---

## 4. Scope & Constraints

### In Scope
✅ Display archive table with 11 columns  
✅ Scope filter (company/team/personal)  
✅ Win result filter (won/lost/pending)  
✅ Pagination (previous/next)  
✅ Detail modal with overview section  
✅ ProjectArchivePanel (artifacts download)  
✅ Error handling and empty state  
✅ Responsive design  

### Out of Scope
❌ Historical analytics/charts (removed in this iteration)  
❌ Bulk operations (delete, export)  
❌ Edit/update project metadata  
❌ Custom column configuration  
❌ Advanced search/text filter  

### Constraints
- **Time:** 1 session
- **Dependencies:** ProjectArchivePanel already built
- **API:** `/api/archive/list` endpoint must exist
- **Database:** `archive` table with RLS security
- **Browser:** Modern browsers (Chrome, Safari, Firefox)

---

## 5. Technical Architecture

### Frontend Components
```
archive/page.tsx
├── Constants: SCOPE_TABS, WIN_RESULT_FILTERS
├── Formatting functions: extractYear, formatCurrency, etc.
├── WinResultBadge component
├── State management: 8 variables (items, loading, scope, etc.)
├── Effects: loadItems on mount + filter change
├── Computed: sortedItems (deadline DESC)
└── JSX: header, filter bar, table, pagination, modal
```

### Imports
```typescript
import Modal from "@/components/ui/Modal";
import ProjectArchivePanel from "@/components/ProjectArchivePanel";
import { api, ArchiveItem } from "@/lib/api";
```

### State Shape
```typescript
{
  items: ArchiveItem[],
  loading: boolean,
  error: string,
  scope: "company" | "team" | "personal",
  winResult: string,
  page: number,
  totalPages: number,
  total: number,
  selectedItem: ArchiveItem | null,
  detailOpen: boolean
}
```

### Data Flow
```
Page Load
  ↓
useEffect(loadItems, [scope, winResult, page])
  ↓
api.archive.list({ scope, win_result, page })
  ↓
setItems(res.data)
  ↓
useMemo(sortedItems, [items])
  ↓
Render table with sortedItems
```

---

## 6. Success Criteria

| # | Criterion | Definition | Verification |
|---|-----------|-----------|--------------|
| 1 | 11-column table | All metadata columns present | Code review + visual |
| 2 | Sort by deadline | DESC order (most recent first) | useMemo sort test |
| 3 | Scope filter | 3 tabs working correctly | Filter state test |
| 4 | Win result filter | 4 buttons working correctly | Filter state test |
| 5 | Pagination | Previous/next + page indicator | Button click test |
| 6 | Detail modal | Opens on row click + shows overview | Modal visibility test |
| 7 | Artifacts access | ProjectArchivePanel renders in modal | Component render test |
| 8 | Error handling | Errors display, empty state shows | Error scenario test |

**Definition of Done:** All 8 criteria passed + code review + no console errors

---

## 7. Implementation Strategy

### Phase A: Setup (30 min)
1. Create archive/page.tsx with imports
2. Define constants (SCOPE_TABS, WIN_RESULT_FILTERS)
3. Add formatting functions
4. Set up state variables

### Phase B: Table Rendering (45 min)
1. Create header section
2. Create filter bar (scope tabs + win result buttons)
3. Build table structure (11 columns)
4. Add loading skeleton + empty state
5. Implement row click handler → modal state

### Phase C: Data Fetching (30 min)
1. Create loadItems() async function
2. Add useEffect for mount + filter changes
3. Implement error handling
4. Update pagination state

### Phase D: Sorting & Pagination (30 min)
1. Implement useMemo for sortedItems (deadline DESC)
2. Create pagination buttons + page indicator
3. Test previous/next navigation
4. Verify page 1 reset on filter change

### Phase E: Modal & Details (30 min)
1. Create detail modal component
2. Build overview grid (2 columns, 8 fields)
3. Integrate ProjectArchivePanel
4. Test modal open/close

### Phase F: Testing & Polish (30 min)
1. Test all filters
2. Test pagination
3. Test error handling
4. Verify accessibility
5. Final styling adjustments

---

## 8. Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| API endpoint delayed | Blocks feature | Low | Use mock data temporarily |
| ProjectArchivePanel broken | Modal incomplete | Low | Code already tested |
| Performance issues (slow sort) | UX degradation | Low | useMemo + pagination |
| RLS security gaps | Data leak | Low | Rely on existing archive view |
| Accessibility failures | WCAG violation | Low | Semantic HTML + testing |

---

## 9. Dependencies

### External
- ✅ `api.archive.list()` endpoint (must exist)
- ✅ `ProjectArchivePanel` component (already built)
- ✅ `Modal` component (already built)
- ✅ `ArchiveItem` type definition

### Internal
- React (hooks, state management)
- TypeScript
- Tailwind CSS
- Next.js (routing context)

---

## 10. Rollout Plan

### Phase 1: QA (Internal)
- Deploy to staging
- Test all filters, pagination, modal
- Verify performance on large datasets
- Check accessibility

### Phase 2: UAT (Sales/PM Team)
- Gather feedback on column selection
- Verify data accuracy
- Test file downloads

### Phase 3: Production
- Deploy to prod
- Monitor error rates
- Gather usage metrics

---

## Notes & Decisions

### Decision: 11 Columns (vs 7)
- **Rationale:** Information richness outweighs screen complexity
- **Tradeoff:** Horizontal scroll on mobile vs detail modal for 11 items
- **User Feedback:** Sales/PM teams prefer visibility over minimalism

### Decision: Client-Side Sort (vs Server)
- **Rationale:** Pagination already handled; avoids additional API call
- **Tradeoff:** Usable only for current page
- **Benefit:** Instant sort response

### Decision: No Statistics Dashboard
- **Rationale:** Removed per user request; focus on list + detail view
- **Alternative:** Can be added later as separate analytics screen

---

## References

- Design: `docs/02-design/features/archive-screen.design.md`
- Backend API: `/api/archive/list` endpoint
- Components: `ProjectArchivePanel.tsx`, `Modal.tsx`
- Types: `ArchiveItem` from `lib/api.ts`

---

**Plan Created:** 2026-04-11  
**Status:** Complete (Implementation Verified)
