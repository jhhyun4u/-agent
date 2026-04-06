# ARTIFACT_VERSION UI 통합 설계

> **작성일**: 2026-03-30
> **목표**: ARTIFACT_VERSION System을 기존 3-Panel 레이아웃에 통합
> **범위**: VersionSelectionModal 배치 + 노드 이동 UI + 산출물 버전 표시

---

## 🎯 기존 레이아웃 분석

### 현재 3-Panel 구조

```
┌─────────────────────────────────────────────────────────────────┐
│                      Proposals/[id] Page                        │
├──────┬────────────────────────────────────────────────────────┬─┤
│      │  DetailCenterPanel                   │ DetailRightPanel  │
│AppSi │  ┌────────────────────────────────┐  │ ┌──────────────┐  │
│debar │  │ ProjectContextHeader            │  │ │ 탭 (6개)     │  │
│      │  ├────────────────────────────────┤  │ │              │  │
│      │  │ PhaseGraph (시각화)            │  │ │ • result     │  │
│      │  │ ├─ STEP 0~11 노드             │  │ │ • comments   │  │
│      │  │ └─ active 노드 강조 표시       │  │ │ • win        │  │
│      │  ├────────────────────────────────┤  │ │ • compare ⭐ │  │
│      │  │ WorkflowPanel                  │  │ │ • qa         │  │
│      │  │ ├─ 현재 노드 정보             │  │ │ • files      │  │
│      │  │ ├─ 다음 노드 목록             │  │ │              │  │
│      │  │ └─ Action 버튼 (승인/거부)   │  │ │ StepArtifact │  │
│      │  ├────────────────────────────────┤  │ │ Viewer       │  │
│      │  │ WorkflowLogPanel (실시간 로그) │  │ │              │  │
│      │  └────────────────────────────────┘  │ └──────────────┘  │
│      │                                       │   리사이즈 가능   │
└──────┴───────────────────────────────────────┴──────────────────┘
  w:240                 flex-1                    w:420 (default)
```

### 현재 각 패널의 역할

| 패널 | 구성 | 용도 |
|-----|------|------|
| **AppSidebar** | 메뉴 + 프로필 | 전체 네비게이션 |
| **DetailCenterPanel** | PhaseGraph + WorkflowPanel + LogPanel | 워크플로우 진행상황 시각화 + 작업 지시 |
| **DetailRightPanel** | 6개 탭 + 산출물 뷰어 | 선택 노드의 산출물 확인 + 메타정보 |

---

## 📊 ARTIFACT_VERSION 통합 설계

### 1️⃣ VersionSelectionModal의 배치

**위치**: DetailCenterPanel 최상단 (ProjectContextHeader 아래)

```tsx
// DetailCenterPanel.tsx

export default function DetailCenterPanel({
  ...
}: DetailCenterPanelProps) {
  // 🆕 버전 선택 모달 상태
  const [versionConflicts, setVersionConflicts] = useState<VersionConflict[]>([]);
  const [showVersionModal, setShowVersionModal] = useState(false);
  const [pendingTargetNode, setPendingTargetNode] = useState<string | null>(null);

  // 🆕 노드 이동 핸들러
  async function handleMoveToNode(targetNode: string) {
    try {
      // 1단계: 버전 충돌 검증
      const resolution = await api.workflow.validateMove(proposalId, targetNode);

      if (resolution.requires_version_selection && resolution.conflicts.length > 0) {
        // 버전 선택 필요 → Modal 표시
        setVersionConflicts(resolution.conflicts);
        setPendingTargetNode(targetNode);
        setShowVersionModal(true);
        return;
      }

      // 버전 선택 불필요 → 바로 이동
      await api.workflow.moveToNode(proposalId, targetNode, {});
      onStateChange();
    } catch (err) {
      alert(`이동 실패: ${err.message}`);
    }
  }

  // 🆕 버전 선택 완료 핸들러
  async function handleVersionSelected(selections: Record<string, number>) {
    if (!pendingTargetNode) return;

    try {
      await api.workflow.moveToNode(proposalId, pendingTargetNode, {
        selected_versions: selections,
      });
      setShowVersionModal(false);
      setPendingTargetNode(null);
      onStateChange();
    } catch (err) {
      alert(`이동 실패: ${err.message}`);
    }
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <ProjectContextHeader />

      {/* 🆕 버전 선택 모달 */}
      {showVersionModal && (
        <VersionSelectionModal
          conflicts={versionConflicts}
          onConfirm={handleVersionSelected}
          onCancel={() => setShowVersionModal(false)}
        />
      )}

      <PhaseGraph ... />
      <WorkflowPanel ... />
      <WorkflowLogPanel ... />
    </div>
  );
}
```

### 2️⃣ 노드 이동 UI (PhaseGraph 강화)

**PhaseGraph.tsx**에서 각 노드에 이동 버튼 추가:

```tsx
// PhaseGraph.tsx 내 노드 렌더링 부분

function renderNode(node: Node, index: number) {
  const isActive = currentNode === node.id;
  const isFuture = index > currentStepIndex;

  return (
    <div key={node.id} className="relative">
      <button
        onClick={() => {
          if (!isFuture) {
            // 이전 노드로만 이동 가능? (아니, 모든 노드 이동 가능)
            onNodeClick?.(node.id);
          }
        }}
        className={`
          px-4 py-2 rounded-lg font-semibold transition
          ${isActive
            ? 'bg-blue-500 text-white ring-2 ring-blue-300'
            : isFuture
            ? 'bg-gray-300 cursor-not-allowed'
            : 'bg-gray-100 hover:bg-blue-100 cursor-pointer'
          }
        `}
      >
        {node.label}
      </button>

      {/* 🆕 노드 이동 드롭다운 메뉴 */}
      {!isFuture && (
        <div className="absolute top-full mt-1 opacity-0 hover:opacity-100 z-50">
          <button
            className="text-xs text-blue-600 hover:underline"
            onClick={() => onMoveToNode?.(node.id)}
          >
            → 이동
          </button>
        </div>
      )}
    </div>
  );
}
```

### 3️⃣ DetailRightPanel의 "버전" 탭 강화

**현재 상황**: `compare` 탭에 VersionCompareModal이 있음

**개선안**: 버전 선택 + 버전 비교를 통합

```tsx
// DetailRightPanel.tsx

// 🆕 활성 버전 선택 UI
const [activeVersionsByKey, setActiveVersionsByKey] = useState<Record<string, number>>({});
// {"strategy": 2, "proposal_sections": 1}

// 🆕 버전 히스토리 조회
useEffect(() => {
  if (!selectedStep) return;

  (async () => {
    const versions = await api.artifacts.getVersions(proposalId, selectedStep);
    // 각 output_key별 버전 목록 받음
  })();
}, [selectedStep, proposalId]);

return (
  <div className="flex-1 flex flex-col overflow-hidden">
    {/* 탭 헤더 */}
    <div className="flex border-b border-[#262626] h-12">
      <TabButton active={activeTab === "result"} onClick={() => setActiveTab("result")}>
        결과물
      </TabButton>
      <TabButton active={activeTab === "comments"} onClick={() => setActiveTab("comments")}>
        댓글
      </TabButton>
      <TabButton active={activeTab === "win"} onClick={() => setActiveTab("win")}>
        수주결과
      </TabButton>
      {/* 🆕 버전 탭 */}
      <TabButton active={activeTab === "version"} onClick={() => setActiveTab("version")}>
        버전 ({Object.keys(artifactVersions || {}).length})
      </TabButton>
      <TabButton active={activeTab === "compare"} onClick={() => setActiveTab("compare")}>
        비교
      </TabButton>
      <TabButton active={activeTab === "qa"} onClick={() => setActiveTab("qa")}>
        Q&A
      </TabButton>
    </div>

    {/* 탭 콘텐츠 */}
    <div className="flex-1 overflow-auto">
      {activeTab === "result" && <StepArtifactViewer ... />}
      {activeTab === "comments" && <CommentsPanel ... />}
      {activeTab === "win" && <WinResultPanel ... />}

      {/* 🆕 버전 탭 콘텐츠 */}
      {activeTab === "version" && (
        <ArtifactVersionPanel
          proposalId={proposalId}
          selectedStep={selectedStep}
          artifactVersions={artifactVersions}
          activeVersions={activeVersionsByKey}
          onVersionSelect={handleVersionSelect}
        />
      )}

      {activeTab === "compare" && <VersionCompareModal ... />}
      {activeTab === "qa" && <QaPanel ... />}
    </div>
  </div>
);
```

### 4️⃣ ArtifactVersionPanel (신규 컴포넌트)

```typescript
// frontend/components/ArtifactVersionPanel.tsx

interface ArtifactVersionPanelProps {
  proposalId: string;
  selectedStep: number | null;
  artifactVersions: Record<string, ArtifactVersion[]>;
  activeVersions: Record<string, number>;
  onVersionSelect: (outputKey: string, version: number) => void;
}

export function ArtifactVersionPanel({
  proposalId,
  selectedStep,
  artifactVersions,
  activeVersions,
  onVersionSelect,
}: ArtifactVersionPanelProps) {
  return (
    <div className="p-4 space-y-4">
      {Object.entries(artifactVersions || {}).map(([outputKey, versions]) => (
        <div key={outputKey} className="border rounded-lg p-3 space-y-2">
          {/* 제목 */}
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold">{outputKey}</h4>
            <span className="text-xs text-gray-500">
              {versions.length}개 버전
            </span>
          </div>

          {/* 버전 선택 버튼들 */}
          <div className="flex flex-wrap gap-2">
            {versions.map(v => (
              <button
                key={v.version}
                onClick={() => onVersionSelect(outputKey, v.version)}
                className={`
                  px-3 py-1 rounded text-sm font-mono
                  ${activeVersions[outputKey] === v.version
                    ? 'bg-blue-500 text-white'
                    : v.is_active
                    ? 'bg-green-100 text-green-800 border border-green-300'
                    : 'bg-gray-100 hover:bg-gray-200'
                  }
                `}
              >
                v{v.version}
                {v.is_active && ' ⭐'}
              </button>
            ))}
          </div>

          {/* 버전 상세 정보 */}
          <details className="text-xs text-gray-600 mt-2">
            <summary className="cursor-pointer">상세정보</summary>
            <div className="mt-2 space-y-1">
              {versions.map(v => (
                <div key={v.version} className="ml-2 py-1 border-t">
                  <div>v{v.version}: {v.created_at}</div>
                  <div className="text-[#5c5c5c]">
                    생성자: {v.created_by} | 사유: {v.parent_version ? 'rerun' : 'first'}
                  </div>
                  {v.used_by && v.used_by.length > 0 && (
                    <div className="text-[#5c5c5c]">
                      사용처: {v.used_by.map(u => u.node).join(', ')}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </details>
        </div>
      ))}
    </div>
  );
}
```

---

## 🎨 UI 배치 시뮬레이션

### 노드 이동 시나리오 1: PhaseGraph에서 이동

```
1️⃣ 사용자가 PhaseGraph의 노드를 클릭
   ↓
2️⃣ 버전 충돌 검증 (validate-move API)
   ↓
3️⃣ 충돌 없음 → 바로 이동
   또는
   충돌 있음 → VersionSelectionModal 표시
   ↓
4️⃣ 모달에서 버전 선택 후 "선택 완료 및 이동"
   ↓
5️⃣ move-to-node API 호출
   ↓
6️⃣ PhaseGraph 업데이트 + 우측 패널 산출물 변경
```

### 노드 이동 시나리오 2: WorkflowPanel에서 이동

```
WorkflowPanel (중앙)에 "다른 노드로 이동" 메뉴 추가:
┌─────────────────────────────────────────┐
│ 현재 노드: proposal_write_next          │
├─────────────────────────────────────────┤
│ 다음 노드:                              │
│ • self_review                           │
│ • [더보기 ▼]                           │
│                                         │
│ Action:                                 │
│ [승인]  [거부]  [다른 노드로...] ⭐    │
└─────────────────────────────────────────┘
        ↓ 클릭
┌─────────────────────────────────────────┐
│ 작업 노드 선택                          │
├─────────────────────────────────────────┤
│ ✅ 이동 가능:                           │
│ • proposal_customer_analysis            │
│ • strategy_generate                     │
│                                         │
│ ⚠️  경고 후 이동:                      │
│ • plan_team (일부 누락)                 │
│                                         │
│ ❌ 이동 불가:                          │
│ • rfp_analyze (선행 작업 없음)          │
└─────────────────────────────────────────┘
```

---

## 🔌 API 호출 흐름

### DetailCenterPanel 에서 노드 이동 시

```typescript
// 1단계: 버전 충돌 검증
const resolution = await api.workflow.validateMove(proposalId, targetNode);
// Response:
// {
//   "can_move": true,
//   "requires_version_selection": true,
//   "conflicts": [
//     {
//       "input_key": "strategy",
//       "available_versions": [1, 2],
//       "recommendation": 2,
//       ...
//     }
//   ]
// }

// 2단계: 사용자 버전 선택 (모달에서)
const selections = { "strategy": 2 };

// 3단계: 노드 이동 실행
const result = await api.workflow.moveToNode(proposalId, targetNode, {
  selected_versions: selections
});
// Response:
// {
//   "success": true,
//   "current_node": "proposal_write_next",
//   "selected_versions": {"strategy": 2},
//   "invalidated_steps": ["self_review", "ppt_toc", ...],
//   "message": "..."
// }

// 4단계: UI 업데이트
onStateChange(); // 워크플로우 상태 재로드
```

---

## 📋 구현 파일 목록

### 신규 생성

```
frontend/components/
├─ VersionSelectionModal.tsx (이미 설계됨)
├─ ArtifactVersionPanel.tsx (신규)
└─ ArtifactVersionItem.tsx (신규, 선택)

frontend/lib/
└─ hooks/useArtifactVersions.ts (신규)
```

### 수정

```
frontend/components/
├─ DetailCenterPanel.tsx
│  ├─ handleMoveToNode() 추가
│  ├─ VersionSelectionModal 통합
│  └─ PhaseGraph onNodeClick 강화
├─ DetailRightPanel.tsx
│  ├─ "version" 탭 추가
│  └─ ArtifactVersionPanel 통합
├─ PhaseGraph.tsx
│  └─ 노드 이동 UI 추가
└─ WorkflowPanel.tsx
   └─ "다른 노드로 이동" 옵션 추가

frontend/lib/api.ts
├─ artifacts.getVersions() 추가
├─ workflow.validateMove() 추가
└─ workflow.moveToNode() 추가
```

---

## ✅ 검증 기준

### UI 통합 검증

- [ ] VersionSelectionModal이 DetailCenterPanel 최상단에 표시됨
- [ ] 버전 충돌 시 모달이 자동 표시됨
- [ ] 버전 선택 후 "선택 완료 및 이동" 버튼이 이동 실행함
- [ ] DetailRightPanel에 "버전" 탭이 추가됨
- [ ] 버전별 상세 정보 표시 (생성일, 생성자, 사용처 등)
- [ ] PhaseGraph 노드 클릭 시 이동 메뉴 표시

### API 통합 검증

- [ ] validateMove API 응답 형식 맞음
- [ ] moveToNode API 호출 후 상태 업데이트
- [ ] 버전 선택 이력 DB 저장 확인
- [ ] 의존성 경고 정확성

### UX 검증

- [ ] 사용자가 이동 불가 이유를 명확히 이해함
- [ ] 버전 추천이 합리적 (최신 또는 많이 사용)
- [ ] 모달 닫기 시 이전 상태로 복구

---

## 🎯 구현 우선순위

### Phase 1: 핵심 기능 (필수)

1. VersionSelectionModal을 DetailCenterPanel에 통합
2. PhaseGraph onNodeClick → validateMove → moveToNode 연쇄
3. DetailRightPanel "버전" 탭 추가 (버전 목록 표시)
4. API 메서드 추가 (validateMove, moveToNode)

### Phase 2: UX 개선 (권장)

1. ArtifactVersionPanel 상세 정보 표시
2. WorkflowPanel에 "다른 노드로 이동" 옵션 추가
3. 버전 비교 UI 개선 (VersionCompareModal과 통합)

### Phase 3: 고급 기능 (선택)

1. 버전별 차이 시각화 (Diff view)
2. 자동 버전 추천 UI
3. 버전 Rollback 기능

---

## 💡 설계 핵심 원칙

| 원칙 | 설명 |
|------|------|
| **발견성** | 노드 이동이 PhaseGraph와 WorkflowPanel 두 곳에서 가능 |
| **명확성** | 버전 충돌 시 "왜 불가한가"를 사용자가 이해함 |
| **일관성** | 기존 3-Panel 레이아웃을 유지하며 강화 |
| **점진성** | Phase 1 필수 → Phase 2 권장 → Phase 3 선택 |

---

**설계 완료**: 기존 UI 구조와의 완벽한 호환성 확보 ✅
**다음 단계**: Phase 1 구현 (DetailCenterPanel + VersionSelectionModal 통합)

