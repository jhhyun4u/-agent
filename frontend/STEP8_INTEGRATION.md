# STEP 8 Frontend Integration Guide

## Overview

STEP 8 is the final proposal review and optimization stage with 6 nodes (8A-8F). The frontend provides a comprehensive review interface with AI-powered issue flagging, version tracking, and approval workflow.

## Architecture

### Page Structure

```
/proposals/[id]/step8-review
├── Header (Navigation + Refresh)
├── NodeStatusDashboard (6-node grid + overall progress)
├── ReviewPanelEnhanced (AI issue review + approval)
├── VersionHistoryViewer (Version comparison for each node)
└── FeedbackSummary (Key findings + next steps)
```

### Component Hierarchy

```
Step8ReviewPage
├── useStep8Data (custom hook)
├── NodeStatusDashboard
│   ├── Progress bar (0-100%)
│   ├── 6 node cards (status indicators)
│   └── Validate All button
├── ReviewPanelEnhanced
│   ├── Issue summary grid (critical/major/minor)
│   ├── Issue category grouping
│   ├── Major issues list (expandable)
│   ├── Minor issues (collapsible)
│   └── Action buttons (Approve/Rewrite/Request Changes)
├── VersionHistoryViewer (x6)
│   ├── Version timeline
│   ├── Comparison selector
│   └── Diff viewer
└── FeedbackSummary
    ├── Key findings
    ├── Score improvement projection
    └── Next phase guidance
```

## Components

### 1. NodeStatusDashboard.tsx

**Purpose**: Overview of all 6 node statuses with progress tracking

**Props**:
```typescript
interface NodeStatusDashboardProps {
  proposal_id: string;
  status: Step8Status | null;
  isLoading?: boolean;
  error?: Error | null;
  onValidateAll?: () => void;
  onValidateNode?: (node_id: string) => void;
  onRevalidate?: () => void;
}
```

**Features**:
- Overall progress percentage with color coding
- 6 node cards showing status (pending/running/completed/failed)
- Manual validation triggers per node
- Displays full node details when expanded

**Usage**:
```tsx
<NodeStatusDashboard
  proposal_id={id}
  status={status}
  isLoading={isLoading}
  onValidateAll={() => validateAllNodes()}
  onValidateNode={(nodeId) => validateNode(nodeId)}
  onRevalidate={refresh}
/>
```

### 2. ReviewPanelEnhanced.tsx

**Purpose**: AI-powered review interface with issue flagging and approval workflow

**Props**:
```typescript
interface ReviewPanelEnhancedProps {
  proposal_id: string;
  issues: AIIssueFlag[];
  total_issues: number;
  critical_count: number;
  can_proceed: boolean;
  onApprove?: () => void;
  onRequestChanges?: (feedback: string) => void;
  onRewrite?: () => void;
  isLoading?: boolean;
}
```

**Features**:
- Issue summary grid (critical/major/minor counts)
- Category-based grouping (compliance/clarity/consistency/style/strategy)
- Major issues list with expandable details
- Collapsible minor issues section
- Inline feedback form for change requests
- Status indicator (✓ Ready / ⚠ Issues)
- Approve button (disabled if critical issues exist)

**Usage**:
```tsx
<ReviewPanelEnhanced
  proposal_id={id}
  issues={reviewData.issues}
  total_issues={reviewData.total_issues}
  critical_count={reviewData.critical_count}
  can_proceed={reviewData.can_proceed}
  onApprove={handleApprove}
  onRequestChanges={handleFeedback}
  onRewrite={handleRewrite}
/>
```

### 3. VersionHistoryViewer.tsx

**Purpose**: Track and compare artifact versions across iterations

**Props**:
```typescript
interface VersionHistoryViewerProps {
  node_name: string;
  versions: VersionMetadata[];
  onSelectVersion?: (version_id: string) => void;
  isLoading?: boolean;
  error?: Error | null;
  onRevalidate?: () => void;
}
```

**Features**:
- Version timeline with metadata (creator, date, size)
- Comparison modes (vs previous / vs original)
- Diff viewer showing additions/deletions
- Version selection with metadata details
- Size tracking for each version

**Usage**:
```tsx
<VersionHistoryViewer
  node_name="step_8a"
  versions={versionsList}
  onSelectVersion={(versionId) => handleVersionSelect(versionId)}
  onRevalidate={refresh}
/>
```

## Custom Hook: useStep8Data

**Purpose**: Unified data fetching for all STEP 8 nodes with polling and error handling

**Usage**:
```typescript
const {
  status,
  customerProfile,
  validationReport,
  consolidatedProposal,
  mockEvalResult,
  feedbackSummary,
  rewriteHistory,
  reviewPanelData,
  isLoading,
  error,
  refresh,
  validateNode,
} = useStep8Data({
  proposalId: id,
  pollingInterval: 5000,  // Poll every 5 seconds
  autoFetch: true,        // Auto-fetch on mount
});
```

**Features**:
- Automatic data fetching from multiple endpoints
- Polling with configurable interval
- Fallback to artifact API if dedicated endpoints unavailable
- Error handling and recovery
- Manual refresh capability
- Per-node validation triggering

## API Endpoints

The frontend expects the following endpoints:

### Status Endpoints

```http
GET /api/proposals/{proposal_id}/step8/status
GET /api/proposals/{proposal_id}/step8/customer-profile
GET /api/proposals/{proposal_id}/step8/validation-report
GET /api/proposals/{proposal_id}/step8/consolidated-proposal
GET /api/proposals/{proposal_id}/step8/mock-eval
GET /api/proposals/{proposal_id}/step8/feedback-summary
GET /api/proposals/{proposal_id}/step8/rewrite-history
GET /api/proposals/{proposal_id}/step8/review-panel
```

### Action Endpoints

```http
POST /api/proposals/{proposal_id}/step8/validate/{node_id}
POST /api/proposals/{proposal_id}/step8/approve
POST /api/proposals/{proposal_id}/step8/feedback
POST /api/proposals/{proposal_id}/step8/rewrite
```

### Version Endpoints

```http
GET /api/proposals/{proposal_id}/step8/versions/{node_id}
```

## Response Types

### Step8Status
```typescript
{
  proposal_id: string;
  nodes: NodeStatus[];           // 6 nodes
  overall_progress: number;      // 0-100
  last_updated: string;          // ISO datetime
}
```

### ReviewPanelData
```typescript
{
  proposal_id: string;
  issues: AIIssueFlag[];         // Array of flagged issues
  total_issues: number;
  critical_count: number;
  can_proceed: boolean;          // true if no critical issues
}
```

### AIIssueFlag
```typescript
{
  issue_id: string;
  section_id: string;
  severity: "critical" | "major" | "minor";
  category: "compliance" | "clarity" | "consistency" | "style" | "strategy";
  description: string;
  suggestion: string;
  flagged_text?: string;         // Optional inline text snippet
}
```

## Integration Points

### 1. Proposal Detail Page Integration

Add STEP 8 tab to proposal detail page:

```tsx
// In proposals/[id]/page.tsx
import { Step8ReviewPage } from "@/app/(app)/proposals/[id]/step8-review/page";

// Add to tab bar
<StreamTabBar
  tabs={[
    { id: "proposal", label: "정성제안서", icon: "📄" },
    { id: "step8", label: "STEP 8 검토", icon: "🔍" },  // NEW
    { id: "bidding", label: "비딩관리", icon: "💰" },
  ]}
/>

// Render in tab content
{activeTab === "step8" && <Step8ReviewPage />}
```

### 2. Workflow State Integration

Connect to existing workflow state for STEP 8 progress:

```tsx
// In DetailCenterPanel or workflow components
if (workflowState?.current_node?.startsWith("step_8")) {
  // Show STEP 8 specific UI
  return <Step8WorkflowView />;
}
```

### 3. Artifact Viewer Integration

Embed STEP 8 artifact viewer for detailed section review:

```tsx
// In StepArtifactViewer
import { Step8ArtifactViewer } from "@/components/step8";

if (stepIndex === 7) {  // STEP 8 index
  return (
    <Step8ArtifactViewer
      proposalId={proposalId}
      onNavigateToReview={() => router.push(`/proposals/${proposalId}/step8-review`)}
    />
  );
}
```

## Testing

### Unit Tests

Run individual component tests:

```bash
npm test -- step8-phase1.test --run
```

### Integration Tests

Run full integration test suite:

```bash
npm test -- step8-integration.test --run
npm test -- step8-page-integration.test --run
```

### E2E Tests (Future)

```bash
npm run test:e2e -- step8-review.spec.ts
```

## Development Workflow

### 1. Local Development

```bash
# Start dev server
npm run dev

# Navigate to STEP 8 page
# http://localhost:3000/proposals/[id]/step8-review
```

### 2. Mock Data

The components use MSW (Mock Service Worker) for API mocking in tests:

```typescript
// See __tests__/step8-integration.test.ts for mock setup
server.use(
  http.get("/api/proposals/:proposal_id/step8/status", () => {
    return HttpResponse.json(mockStep8Status);
  })
);
```

### 3. API Fallback

If dedicated STEP 8 endpoints aren't available, the hook falls back to fetching from artifact API:

```typescript
// Automatic fallback in useStep8Data hook
const artifact = await api.artifacts.get(proposalId, "step_8a");
if (artifact?.data) {
  setCustomerProfile(artifact.data);
}
```

## Known Limitations & TODOs

### Current Limitations

1. **Mock Version History**: Version comparison uses mock data; backend should provide actual diff
2. **Polling Interval**: Fixed 5-second interval; could be optimized with WebSocket
3. **Concurrent Editing**: No lock mechanism for simultaneous reviews
4. **Offline Mode**: Requires network; no offline caching

### TODOs

- [ ] Implement actual diff viewer using Diff Match Patch library
- [ ] Add WebSocket support for real-time updates
- [ ] Create section lock mechanism for concurrent editing
- [ ] Add offline fallback with IndexedDB cache
- [ ] Implement AI suggestion caching
- [ ] Add undo/redo for inline feedback edits
- [ ] Create custom hooks for approval workflow
- [ ] Add keyboard shortcuts for power users
- [ ] Implement batch operations (approve/reject multiple issues)
- [ ] Add export functionality (PDF/DOCX with highlighted issues)

## Performance Considerations

1. **Lazy Loading**: Components only fetch data when visible
2. **Debounced Polling**: Reduces unnecessary API calls
3. **Memoization**: Use React.memo for expensive components
4. **Code Splitting**: STEP 8 page is lazy-loaded on demand

```typescript
// In app router
const Step8ReviewPage = dynamic(() => import('./step8-review/page'), {
  loading: () => <div>Loading...</div>,
});
```

## Accessibility

All components follow WCAG 2.1 AA standards:

- ✅ Keyboard navigation (Tab, Arrow keys, Enter)
- ✅ Screen reader support (ARIA labels, roles, live regions)
- ✅ Color contrast (WCAG AA minimum)
- ✅ Focus indicators (visible on all interactive elements)
- ✅ Form validation messages (programmatic association)

## Browser Support

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## Troubleshooting

### Issue: Components Not Rendering

**Solution**: Check that `@/components/step8` exports are correct:
```bash
grep -n "export" frontend/components/step8/index.ts
```

### Issue: Data Not Loading

**Solution**: Verify API endpoints are accessible:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/proposals/[id]/step8/status
```

### Issue: Version History Empty

**Solution**: Check backend is populating version data and returning in response

## References

- [STEP 8 Type Definitions](./lib/types/step8.ts)
- [Component Implementation](./components/step8/)
- [Test Coverage](./\_\_tests\_\_/step8-*.test.ts)
- [Integration Tests](./\_\_tests\_\_/step8-page-integration.test.tsx)
