# Frontend Design Preview Guide

## 📋 Overview

This guide shows you all the available HTML preview pages demonstrating the **Proposal Coworker** frontend design system. These are static HTML mockups that showcase the design, layout, responsive behavior, and interactive elements across the entire application.

---

## 🎨 Preview Pages

### 1. **Dashboard** — PREVIEW_DASHBOARD.html
**Main landing page showing KPI metrics and proposal overview**

**Features:**
- 📊 6 KPI cards (win rate, monthly rate, active proposals, recent activity, deadlines, team performance)
- 📌 Recently worked proposals section with status indicators
- 🎯 D-Day deadline tracking with color-coded urgency (red/amber/gray)
- 📱 Fully responsive sidebar (collapsible on desktop, slide-in overlay on mobile)
- 🌓 Dark mode styling with CSS variables

**When to use:**
- First landing page after login
- Overview of current project status
- Quick access to recent work

---

### 2. **Proposals List** — PREVIEW_PROPOSALS_LIST.html
**Grid view of all proposals in different states**

**Features:**
- 🏠 6 project cards showing:
  - Project title with status badge (진행 중, 완료됨, 준비 중, 실패)
  - Client/contractor info
  - D-Day countdown with color coding
  - Budget amount (예정가격)
  - Progress bar with phase indicator (e.g., Phase 3/5)
- 🔍 Filter chips (전체, 진행 중, 완료됨, 일시 정지, ⚠️ 주의 필요)
- 📲 Responsive grid layout (1-3 columns based on screen size)
- 🎬 Hover effects on cards with border and shadow enhancement

**Status Badges:**
- **진행 중** (Processing) — Green accent
- **완료됨** (Completed) — Light green
- **준비 중** (Initialized) — Amber/orange
- **실패** (Failed) — Red

**When to use:**
- Browse all proposals across the team
- Filter by status or completion stage
- Quick actions (Continue writing, Preview, Download)

---

### 3. **Proposal Editor** — PREVIEW_PROPOSAL_EDITOR.html
**Multi-column editor interface for writing proposals**

**Layout:**
```
┌─────────────────────────────────────────────┐
│ Header: Project Title + Actions             │
├──────────┬─────────────────────┬────────────┤
│   TOC    │   Editor Content    │ AI Panel   │
│  Panel   │      (Main)         │  (Right)   │
│          │                     │            │
└──────────┴─────────────────────┴────────────┘
```

**Components:**

**Left Panel — Table of Contents (TOC)**
- 8 sections with completion indicators (✓ done, × todo)
- Progress bar showing 4/8 sections completed (50%)
- Click to navigate between sections
- Visual indicator of active section with green left border

**Center Panel — Editor**
- Section number and title
- Last modified info and author
- Rich text formatting toolbar (B, I, U, H1-H3, bullets, links, attachments)
- Editor content area with Markdown preview
- Previous/Next section navigation buttons

**Right Panel — AI Assistant**
- 3 types of suggestions:
  1. **구조 개선 제안** (Structure improvement) — Recommendations to enhance credibility
  2. **경쟁사 비교** (Competitor comparison) — Tips to differentiate from competitors
  3. **데이터 신뢰성** (Data credibility) — Flags unsupported claims with evidence requirements
- "자세히 보기" (Details) and "적용" (Apply) buttons
- Loading spinner showing active AI analysis

**When to use:**
- Write and edit proposal sections
- Get AI-powered suggestions in real-time
- Track progress across all sections
- Review and refine with AI guidance

---

### 4. **Knowledge Base Search** — PREVIEW_KB_SEARCH.html
**Unified search and discovery of organizational knowledge**

**Features:**

**Search Interface:**
- 🔍 Search box with query: "터널 운영"
- 6 filter chips (모든 타입, 사례, 발주처, 경쟁사, 교훈, Q&A)
- Left sidebar with faceted filters:
  - Content type (사례, 모범사례, 템플릿)
  - Client/contractor (K 공사, 서울시, 인천항만)
  - Category (기술 제안, 가격 전략)

**Search Results (6 cards shown):**
1. **사례** (Case Study)
   - K 공사 터널 운영 사업
   - Budget, award year metadata

2. **Q&A**
   - 터널 안전 관리 기준의 변경
   - Recent update information

3. **발주처** (Client Profile)
   - K 공사 발주 특성 분석
   - Statistics on bidding history

4. **교훈** (Lessons Learned)
   - 터널 안전 시스템 - 기술 신뢰도 중요성
   - Warning indicator, actionable insights

5. **경쟁사** (Competitor)
   - A 엔지니어링 - 터널 사업 포지셔닝
   - Strengths and weaknesses

6. **모범사례** (Best Practices)
   - 기술 제안의 신뢰도 입증 방식
   - Success indicators

**Results Display:**
- 12 total results across 3 pages
- Result highlights in accent color (#3ecf8e)
- Metadata (budget, year, stats, tags)
- Pagination with current page indicator

**When to use:**
- Discover past similar projects
- Research client preferences and bidding history
- Learn from competitor positioning
- Find lessons learned and best practices
- Search Q&A for common proposal writing questions

---

## 🎯 Design System Components

### Color Palette
```
Dark Mode (default):
  Background (--bg)        #0f0f0f    (Pure black)
  Surface (--surface)      #111111    (Very dark gray)
  Card (--card)            #1c1c1c    (Dark gray)
  Border (--border)        #262626    (Medium gray)
  Text (--text)            #ededed    (Off-white)
  Muted (--muted)          #8c8c8c    (Medium gray for secondary text)
  Accent (--accent)        #3ecf8e    (Green - primary brand color)
```

### Typography
- **Headers**: 20-28px, bold (600-700 weight)
- **Body**: 13-14px, regular (400 weight)
- **Labels**: 11-12px, uppercase, semi-bold
- **Captions**: 11px, gray, small details

### Spacing System
- **xs**: 6px (tight)
- **sm**: 8px (normal)
- **md**: 16px (section spacing)
- **lg**: 24px (major sections)
- **xl**: 32px (page padding)

### Interactive Elements
- **Buttons**: Primary (green accent), Secondary (gray card), Ghost (outline)
- **Hover effects**: 150ms color transition, subtle shadow/border highlight
- **Focus states**: Ring with 2px accent color + 2px offset
- **Status badges**: Background color @ 10% opacity + saturated text

---

## 📱 Responsive Behavior

### Desktop (lg ≥ 1024px)
- ✅ Sidebar always visible (208px width, or 48px when collapsed)
- ✅ Full 3-column layouts in editor
- ✅ Grid layouts with multiple columns
- ✅ Hover effects on interactive elements

### Tablet (640px - 1023px)
- ✅ Sidebar hidden by default, slide-in overlay on hamburger click
- ✅ Editor: 2-column layout (no AI panel initially)
- ✅ Grid layouts collapse to 1-2 columns
- ✅ All touch targets ≥ 44px height

### Mobile (< 640px)
- ✅ Sidebar hidden, overlay only
- ✅ Single column layouts
- ✅ Stacked components
- ✅ Touch-friendly spacing and buttons
- ✅ Simplified modals and panels

---

## 🖱️ Interactive Elements

### Sidebar Interactions
```
Desktop:
  - PA logo click → Toggle collapse/expand
  - Right edge drag → Resize (180px-360px)

Mobile:
  - Hamburger icon → Slide-in overlay
  - Background click → Close sidebar
  - Escape key → Close sidebar
  - Nav item click → Navigate + close sidebar
```

### Editor Interactions
```
  - TOC item click → Scroll/navigate to section
  - Toolbar button click → Toggle text formatting
  - AI suggestion "적용" button → Apply recommendation
  - Section buttons → Navigate to previous/next sections
```

### Search Interactions
```
  - Chip click → Filter by category
  - Facet checkbox → Toggle filter
  - Sort button → Change sort order
  - Pagination → Navigate results pages
```

---

## 🚀 How to View

### Option 1: Direct File Open
```bash
# Navigate to project root
cd c:\project\tenopa proposer\-agent-master\frontend

# Open any HTML file directly in browser:
#   - PREVIEW_DASHBOARD.html
#   - PREVIEW_PROPOSALS_LIST.html
#   - PREVIEW_PROPOSAL_EDITOR.html
#   - PREVIEW_KB_SEARCH.html
```

### Option 2: Local Web Server
```bash
# Using Python
python -m http.server 8000

# Using Node.js
npx http-server

# Then visit: http://localhost:8000/frontend/PREVIEW_DASHBOARD.html
```

### Option 3: VS Code Live Server
- Install "Live Server" extension
- Right-click any HTML file
- Select "Open with Live Server"

---

## 📊 Design Validation Checklist

- ✅ All pages use consistent color palette (CSS variables)
- ✅ Typography scales properly across screen sizes
- ✅ Sidebar responsive: full → 48px → overlay
- ✅ Touch targets minimum 44px height on mobile
- ✅ All interactive elements have hover/focus states
- ✅ Loading states and error states represented
- ✅ Accessibility: semantic HTML, proper heading hierarchy
- ✅ Spacing consistent with design tokens (6px, 8px, 16px, 24px, 32px)
- ✅ Status colors distinct and accessible (green, amber, red)
- ✅ Progress indicators clear and understandable

---

## 🔄 Component Usage Pattern

Each preview demonstrates a complete workflow:

1. **Navigation**: User starts on Dashboard
2. **Discovery**: Browses Proposals List
3. **Composition**: Opens Proposal Editor to write
4. **Research**: Uses KB Search to find reference materials
5. **Submission**: Returns to list to track status

---

## 📝 Implementation Notes

These HTML files are **static mockups** demonstrating:
- Layout and spacing
- Component interactions
- Responsive breakpoints
- Color and typography usage
- Status and state indicators

For actual implementation, use:
- **Framework**: Next.js 15 + React 19
- **Styling**: Tailwind CSS 4 + custom configuration
- **Components**: shadcn/ui + custom components
- **Rich Text**: Tiptap for editor
- **Charts**: Recharts for analytics
- **Icons**: Custom SVG icons

---

## 🎓 Next Steps

1. ✅ **Review** all preview pages in browser
2. ✅ **Validate** layout and spacing match design
3. ✅ **Test** responsive behavior at different breakpoints
4. ✅ **Verify** color contrast meets accessibility (WCAG AA)
5. ✅ **Implement** components in Next.js using previews as reference
6. ✅ **Connect** to real data from FastAPI backend
7. ✅ **Add** animations and micro-interactions
8. ✅ **Test** across devices and browsers

---

**Last Updated**: 2026-03-29
**Design System Version**: v4.0
**Frontend Framework**: Next.js 15 + React 19 + TypeScript
**Styling**: Tailwind CSS 4 + Custom CSS Variables
