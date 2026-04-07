# ARTIFACT_VERSION System 설계서

> **작성일**: 2026-03-30
> **목표**: 산출물 버전 관리 + 의존성 해결의 상세 설계
> **설계 대상**: Phase 1 + Phase 2 (기본 버전화 + 버전 선택)
> **다음 단계**: Do Phase (Phase 1 구현)

---

## 🎯 설계 목표

### 3가지 핵심 설계 결정

```
1️⃣ 자동 버전화
   모든 노드 산출물 → v1, v2, v3... 생성
   → 히스토리 추적, Rollback 가능

2️⃣ 스마트 버전 선택 (의존성 기반)
   버전 충돌 시에만 Human 개입
   → 자동 추천 + 경고 + 선택 강제

3️⃣ 완전한 추적성
   DB 기록 + State 저장 + Audit Log
   → 누가 언제 어느 버전을 선택했는가 기록
```

---

## 📊 DB 스키마 상세 설계

### 테이블 1: proposal_artifacts

**목적**: 모든 산출물의 버전을 저장하고 메타데이터 추적

```sql
CREATE TABLE proposal_artifacts (
    -- 기본 식별자
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,

    -- 산출물 식별
    node_name VARCHAR(255) NOT NULL,
    -- 예: "strategy_generate", "proposal_write_next", "mock_evaluation"

    output_key VARCHAR(255) NOT NULL,
    -- 예: "strategy", "proposal_sections", "mock_evaluation_result"

    version INT NOT NULL,
    -- v1, v2, v3... (노드별 자동 증가)

    -- 버전 메타데이터
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES users(id),
    -- Human이 노드를 재실행한 사용자

    is_active BOOLEAN DEFAULT TRUE,
    -- 현재 active 버전인가? (한 output_key당 최대 1개)

    is_deprecated BOOLEAN DEFAULT FALSE,
    -- 사용을 권장하지 않는가? (Rollback 대상)

    -- 의존성 추적
    parent_node_name VARCHAR(255),
    -- 이 산출물을 생성한 노드 (이전 버전의 경우)

    parent_version INT,
    -- 부모 노드의 어느 버전에서 생성되었는가?

    -- 산출물 저장
    artifact_data JSONB NOT NULL,
    -- 실제 산출물 데이터
    -- 예: { "positioning": "offensive", "win_theme": "..." }

    artifact_size INT,
    -- 저장 용량 (byte), 용량 관리/아카이빙 판단용

    checksum VARCHAR(64),
    -- SHA256 해시, 중복 감지 및 변경 추적용

    -- 후행 노드 추적
    used_by JSONB DEFAULT '[]'::jsonb,
    -- [
    --   { "node": "proposal_write_next", "version": 1, "used_at": "2026-03-30T10:00Z" },
    --   { "node": "ppt_toc", "version": 1, "used_at": "2026-03-30T11:00Z" }
    -- ]

    -- 메모
    created_reason VARCHAR(255),
    -- "first_run" | "rerun_after_strategy_change" | "manual_rerun"

    notes TEXT,
    -- Human이 남긴 노트 (예: "Strategy 변경으로 재작성함")

    -- 제약
    UNIQUE(proposal_id, node_name, output_key, version),
    CONSTRAINT version_positive CHECK (version > 0)
);

CREATE INDEX idx_artifact_active
ON proposal_artifacts(proposal_id, output_key, is_active)
WHERE is_active = true;
-- 현재 active 버전을 빠르게 조회

CREATE INDEX idx_artifact_used_by
ON proposal_artifacts USING GIN (used_by)
WHERE is_deprecated = false;
-- 후행 노드 추적

CREATE INDEX idx_artifact_created
ON proposal_artifacts(proposal_id, created_at DESC);
-- 최근 버전 조회
```

### 테이블 2: proposal_artifact_choices

**목적**: Human이 버전을 선택한 이력을 완전히 기록

```sql
CREATE TABLE proposal_artifact_choices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,

    -- 선택이 발생한 상황
    choice_point VARCHAR(255) NOT NULL,
    -- "moving_to_proposal_write_next" | "moving_to_ppt_toc" | ...

    from_node VARCHAR(255) NOT NULL,
    -- 현재 노드 (선택을 강요한 노드)

    to_node VARCHAR(255) NOT NULL,
    -- 이동하려는 노드

    -- 선택 대상 산출물
    required_input VARCHAR(255) NOT NULL,
    -- "strategy" (input key)

    available_versions JSONB NOT NULL,
    -- [
    --   { "version": 1, "created_at": "...", "used_count": 2, "created_by": "user1" },
    --   { "version": 2, "created_at": "...", "used_count": 0, "created_by": "user2" }
    -- ]

    selected_version INT NOT NULL,
    -- Human이 선택한 버전 (1, 2, 3 등)

    -- 선택 기록
    decision_at TIMESTAMP DEFAULT NOW(),
    decided_by UUID NOT NULL REFERENCES users(id),
    -- 누가 선택했는가

    reason TEXT,
    -- Human의 선택 이유 (선택)
    -- 예: "Strategy v2를 써야 최신 내용 반영됨"

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_choice_proposal
ON proposal_artifact_choices(proposal_id, to_node, decision_at DESC);
-- 노드별 선택 이력 추적
```

### 마이그레이션 SQL

```sql
-- database/migrations/015_artifact_versioning.sql
-- 실행: uv run alembic upgrade head

BEGIN;

-- 1️⃣ proposal_artifacts 테이블 생성
CREATE TABLE IF NOT EXISTS proposal_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    node_name VARCHAR(255) NOT NULL,
    output_key VARCHAR(255) NOT NULL,
    version INT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE,
    is_deprecated BOOLEAN DEFAULT FALSE,
    parent_node_name VARCHAR(255),
    parent_version INT,
    artifact_data JSONB NOT NULL,
    artifact_size INT,
    checksum VARCHAR(64),
    used_by JSONB DEFAULT '[]'::jsonb,
    created_reason VARCHAR(255),
    notes TEXT,
    UNIQUE(proposal_id, node_name, output_key, version),
    CONSTRAINT version_positive CHECK (version > 0)
);

CREATE INDEX IF NOT EXISTS idx_artifact_active
ON proposal_artifacts(proposal_id, output_key, is_active)
WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_artifact_used_by
ON proposal_artifacts USING GIN (used_by);

CREATE INDEX IF NOT EXISTS idx_artifact_created
ON proposal_artifacts(proposal_id, created_at DESC);

-- 2️⃣ proposal_artifact_choices 테이블 생성
CREATE TABLE IF NOT EXISTS proposal_artifact_choices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    choice_point VARCHAR(255) NOT NULL,
    from_node VARCHAR(255) NOT NULL,
    to_node VARCHAR(255) NOT NULL,
    required_input VARCHAR(255) NOT NULL,
    available_versions JSONB NOT NULL,
    selected_version INT NOT NULL,
    decision_at TIMESTAMP DEFAULT NOW(),
    decided_by UUID NOT NULL REFERENCES users(id),
    reason TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_choice_proposal
ON proposal_artifact_choices(proposal_id, to_node, decision_at DESC);

-- 3️⃣ proposals 테이블 확장 (선택)
ALTER TABLE proposals
ADD COLUMN IF NOT EXISTS artifact_versioning_enabled BOOLEAN DEFAULT TRUE;

COMMIT;
```

---

## 🔌 API 엔드포인트 설계

### 1️⃣ 버전 조회 API

**GET** `/proposals/{proposal_id}/artifact-versions`

```python
# 요청
GET /proposals/{proposal_id}/artifact-versions?output_key=strategy

# 응답
{
    "proposal_id": "proj-123",
    "artifact_versions": {
        "strategy": [
            {
                "version": 1,
                "created_at": "2026-03-30T09:00Z",
                "created_by": "user1",
                "is_active": false,
                "created_reason": "first_run",
                "checksum": "abc123...",
                "used_by": [
                    {"node": "proposal_write_next", "version": 1, "used_at": "2026-03-30T10:00Z"}
                ]
            },
            {
                "version": 2,
                "created_at": "2026-03-30T10:00Z",
                "created_by": "user2",
                "is_active": true,
                "created_reason": "rerun_after_change",
                "checksum": "def456...",
                "used_by": []
            }
        ],
        "proposal_sections": [
            {"version": 1, "is_active": true, ...}
        ]
    },
    "active_versions": {
        "strategy": 2,
        "proposal_sections": 1
    }
}
```

### 2️⃣ 의존성 검증 API

**POST** `/proposals/{proposal_id}/validate-move`

```python
# 요청
POST /proposals/{proposal_id}/validate-move
{
    "target_node": "proposal_write_next"
}

# 응답 (버전 충돌 없음)
{
    "can_move": true,
    "requires_version_selection": false,
    "conflicts": [],
    "auto_resolved": {
        "rfp_analysis": 1,
        "strategy": 2,
        "plan": 1
    },
    "message": "proposal_write_next로 이동 가능합니다."
}

# 응답 (버전 충돌 있음)
{
    "can_move": true,
    "requires_version_selection": true,
    "conflicts": [
        {
            "input_key": "strategy",
            "available_versions": [1, 2, 3],
            "current_active": 2,
            "dependency_mismatch": {
                "downstream_usage": [
                    {
                        "key": "proposal_sections",
                        "version": 1,
                        "parent_input_version": 1
                    }
                ],
                "warning": "기존 proposal_sections v1은 strategy v1 기반입니다"
            },
            "recommendation": 2
        }
    ],
    "auto_resolved": {
        "rfp_analysis": 1,
        "plan": 1
    },
    "message": "버전을 선택해주세요. (strategy는 추천 v2 선택)"
}

# 응답 (이동 불가)
{
    "can_move": false,
    "reason": "proposal_sections 산출물이 없습니다. 제안서를 먼저 작성해야 합니다."
}
```

### 3️⃣ 노드 이동 API (1단계: 검증)

**POST** `/proposals/{proposal_id}/check-node-move/{target_node}`

```python
# 요청
POST /proposals/{proposal_id}/check-node-move/proposal_write_next

# 응답
{
    "move_check": {
        "can_move": true,
        "requires_version_selection": true,
        "conflicts": [
            {"input_key": "strategy", "available_versions": [1, 2], ...}
        ]
    },
    "next_action": "POST /move-to-node/proposal_write_next with selected_versions"
}
```

### 4️⃣ 노드 이동 API (2단계: 실행)

**POST** `/proposals/{proposal_id}/move-to-node/{target_node}`

```python
# 요청 (1단계: 검증만)
POST /proposals/{proposal_id}/move-to-node/proposal_write_next
{ }

# 응답 (버전 선택 필요)
{
    "success": false,
    "requires_selection": true,
    "conflicts": [
        {
            "input_key": "strategy",
            "available_versions": [1, 2],
            "recommendation": 2,
            ...
        }
    ],
    "message": "버전을 선택해주세요.",
    "next_action": "POST /move-to-node/proposal_write_next with selected_versions={\"strategy\": 2}"
}

# 요청 (2단계: 버전 선택 후)
POST /proposals/{proposal_id}/move-to-node/proposal_write_next
{
    "selected_versions": {
        "strategy": 2
    },
    "reason": "최신 전략으로 제안서 재작성"
}

# 응답 (성공)
{
    "success": true,
    "current_node": "proposal_write_next",
    "selected_versions": {
        "strategy": 2,
        "rfp_analysis": 1,
        "plan": 1
    },
    "invalidated_steps": ["self_review", "ppt_toc", ...],
    "message": "proposal_write_next로 이동했습니다. 선택된 버전: {strategy: v2}"
}
```

### 5️⃣ 버전 비교 API (Phase 3)

**GET** `/proposals/{proposal_id}/artifact-compare`

```python
# 요청
GET /proposals/{proposal_id}/artifact-compare?key=proposal_sections&v1=1&v2=2

# 응답
{
    "output_key": "proposal_sections",
    "version1": 1,
    "version2": 2,
    "diff": {
        "sections": [
            {
                "index": 0,
                "section_name": "기술적 수행방안",
                "status": "modified",
                "changes": {
                    "content": "... diff output ..."
                }
            }
        ]
    },
    "summary": {
        "added_sections": 0,
        "modified_sections": 1,
        "removed_sections": 0
    }
}
```

---

## 🔧 State 모델 설계

### State 확장 필드

```python
from typing import Annotated, Optional, TypedDict
from pydantic import BaseModel


class ArtifactVersion(BaseModel):
    """산출물 버전 정보"""
    node_name: str                    # "strategy_generate"
    output_key: str                   # "strategy"
    version: int                      # 1, 2, 3
    created_at: str                   # ISO8601
    created_by: str                   # user_id
    is_active: bool
    parent_version: Optional[int] = None
    used_by: list[dict] = Field(default_factory=list)
    # [{"node": "proposal_write_next", "version": 1, "used_at": "..."}]
    created_reason: str = "first_run"


class VersionSelection(BaseModel):
    """버전 선택 기록"""
    timestamp: str                    # ISO8601
    target_node: str
    selected_versions: dict[str, int] # {"strategy": 2, "plan": 1}
    user_id: str
    reason: Optional[str] = None


class ProposalState(TypedDict):
    # ... (기존 필드들)

    # 🆕 버전 관리 필드
    artifact_versions: Annotated[
        dict[str, list[ArtifactVersion]],
        lambda a, b: {
            **a,
            **{k: v for k, v in b.items()}  # 최신 버전 유지
        }
    ]
    # {
    #   "strategy": [v1_info, v2_info, v3_info],
    #   "proposal_sections": [v1_info, v2_info],
    #   "ppt_slides": [v1_info],
    # }

    active_versions: Annotated[
        dict[str, int],
        lambda a, b: {
            **a,
            **{k: v for k, v in b.items()}  # 최신 active 버전
        }
    ]
    # {
    #   "strategy": 2,           # strategy의 active 버전은 v2
    #   "proposal_sections": 1,
    #   "ppt_slides": 1,
    # }

    version_selection_history: Annotated[
        list[VersionSelection],
        lambda a, b: a + b  # 이력 추가
    ]
    # Human이 버전을 선택한 이력

    selected_versions: dict[str, int] = {}
    # 현재 이동 시 선택된 버전들
    # {"strategy": 2}
```

---

## 🛠️ 서비스 계층 설계

### version_manager.py (신규 파일)

```python
# app/services/version_manager.py

from typing import Optional, NamedTuple
from datetime import datetime
from enum import Enum
import json
import hashlib

from app.graph.state import ProposalState, ArtifactVersion
from app.utils.supabase_client import get_async_client
import logging

logger = logging.getLogger(__name__)


class VersionConflict(Enum):
    """버전 선택 필요 상황"""
    NO_CONFLICT = "no_conflict"
    SINGLE_NEWER = "single_newer"
    MULTIPLE_VERSIONS = "multiple_versions"
    DEPENDENCY_MISMATCH = "dependency_mismatch"


class MoveCheckResult(NamedTuple):
    """노드 이동 검증 결과"""
    can_move: bool
    requires_version_selection: bool
    conflicts: list[dict]
    auto_resolved: dict[str, int]
    message: str


async def execute_node_and_create_version(
    state: ProposalState,
    node_name: str,
    node_result: dict,
    user_id: str,
) -> dict:
    """
    노드 실행 후 산출물 버전 생성.

    Args:
        state: 현재 상태
        node_name: 실행한 노드명
        node_result: 노드 실행 결과
        user_id: 실행 사용자

    Returns:
        {"success": bool, "new_versions": dict[str, int], "message": str}
    """

    if not node_result.get("success"):
        return {"success": False, "message": "노드 실행 실패"}

    # 1️⃣ 노드의 출력물 확인
    node_outputs = NODE_DEPENDENCIES.get(node_name, {}).get("outputs", [])
    if not node_outputs:
        return {"success": True, "new_versions": {}, "message": "산출물 없음"}

    new_versions = {}
    client = await get_async_client()

    for output_key in node_outputs:
        # output이 state에 있는가?
        output_data = state.get(output_key)
        if output_data is None:
            continue

        # 새 버전 번호 결정
        existing = state.get("artifact_versions", {}).get(output_key, [])
        new_version_num = len(existing) + 1

        # checksum 계산
        data_str = json.dumps(output_data, sort_keys=True, default=str)
        checksum = hashlib.sha256(data_str.encode()).hexdigest()

        # 중복 확인 (같은 데이터이면 버전 생성 안 함)
        if existing and existing[-1].get("checksum") == checksum:
            logger.info(f"[VERSION] {output_key}: 데이터 변경 없음 (중복 방지)")
            continue

        # DB에 artifact 저장
        artifact = await client.table("proposal_artifacts").insert({
            "proposal_id": state["proposal_id"],
            "node_name": node_name,
            "output_key": output_key,
            "version": new_version_num,
            "artifact_data": output_data,
            "artifact_size": len(data_str),
            "checksum": checksum,
            "created_by": user_id,
            "created_reason": _determine_reason(state, output_key),
            "is_active": True,  # 새로 생성된 것이 active
        }).execute()

        # 기존 active 버전을 inactive로 변경
        if existing:
            await client.table("proposal_artifacts").update({
                "is_active": False
            }).eq("proposal_id", state["proposal_id"]).eq(
                "output_key", output_key
            ).neq("version", new_version_num).execute()

        # State 업데이트
        state.setdefault("artifact_versions", {})[output_key] = (
            state.get("artifact_versions", {}).get(output_key, []) +
            [ArtifactVersion(
                node_name=node_name,
                output_key=output_key,
                version=new_version_num,
                created_at=datetime.utcnow().isoformat(),
                created_by=user_id,
                is_active=True,
                checksum=checksum,
            )]
        )
        state["active_versions"][output_key] = new_version_num

        new_versions[output_key] = new_version_num
        logger.info(f"[VERSION] {output_key} v{new_version_num} 생성 ({node_name})")

    return {
        "success": True,
        "new_versions": new_versions,
        "message": f"새 버전 생성: {list(new_versions.keys())}",
    }


async def validate_move_and_resolve_versions(
    state: ProposalState,
    target_node: str,
) -> MoveCheckResult:
    """
    노드로 이동 가능한지 검증하고 버전 충돌 감지.

    Args:
        state: 현재 상태
        target_node: 이동할 노드명

    Returns:
        MoveCheckResult (can_move, requires_selection, conflicts, auto_resolved)
    """

    if target_node not in NODE_DEPENDENCIES:
        return MoveCheckResult(
            can_move=False,
            requires_version_selection=False,
            conflicts=[],
            auto_resolved={},
            message=f"'{target_node}'은 존재하지 않는 노드입니다.",
        )

    # 1️⃣ 필수 선행 산출물 확인
    target_requires = NODE_DEPENDENCIES[target_node]["requires"]
    missing = []
    conflicts = []
    auto_resolved = {}

    for input_key, dep_level in target_requires.items():
        versions = state.get("artifact_versions", {}).get(input_key, [])

        if not versions:
            # 산출물이 없음
            if dep_level == DependencyLevel.REQUIRED:
                missing.append(input_key)
            continue

        if len(versions) == 1:
            # 버전이 1개만 있음 → 자동 선택
            auto_resolved[input_key] = versions[0].version
            continue

        # 여러 버전이 있음 → 버전 선택 필요
        mismatch = await _check_dependency_mismatch(
            state, target_node, input_key
        )

        conflicts.append({
            "input_key": input_key,
            "available_versions": [v.version for v in versions],
            "current_active": state.get("active_versions", {}).get(input_key),
            "dependency_mismatch": mismatch,
            "recommendation": _recommend_version(versions),
        })

    # 2️⃣ 판정
    if missing:
        return MoveCheckResult(
            can_move=False,
            requires_version_selection=False,
            conflicts=[],
            auto_resolved={},
            message=f"필수 선행 작업이 없습니다: {', '.join(missing)}",
        )

    return MoveCheckResult(
        can_move=True,
        requires_version_selection=len(conflicts) > 0,
        conflicts=conflicts,
        auto_resolved=auto_resolved,
        message="이동 가능합니다" if not conflicts else "버전을 선택해주세요",
    )


async def _check_dependency_mismatch(
    state: ProposalState,
    target_node: str,
    input_key: str,
) -> Optional[dict]:
    """
    의존성 불일치 확인.

    예: proposal_write_next가 strategy v2를 필요하는데,
        기존 proposal_sections v1은 strategy v1 기반이면 경고.
    """

    versions = state.get("artifact_versions", {}).get(input_key, [])
    downstream_usages = []

    # 이 input_key를 사용하는 후행 노드들 확인
    for key, v_list in state.get("artifact_versions", {}).items():
        for v in v_list:
            # used_by에서 input_key를 사용하는 노드 찾기
            for usage in v.used_by or []:
                if usage.get("node") != target_node:
                    continue

                # 이전 버전이 사용한 input_key의 버전과 비교
                if key != input_key:
                    continue

                # parent_version이 있으면 기록
                # (이것은 생성 시에 저장되어야 함)
                downstream_usages.append({
                    "key": key,
                    "version": v.version,
                })

    if downstream_usages:
        return {
            "downstream_usage": downstream_usages,
            "warning": f"기존 산출물들이 {input_key}의 이전 버전을 기반으로 할 수 있습니다",
        }

    return None


def _recommend_version(versions: list[ArtifactVersion]) -> int:
    """
    추천 버전 선택 로직.

    우선순위:
    1. is_active인 버전 (현재 사용 중)
    2. 가장 최신 버전
    3. 가장 많이 사용된 버전
    """

    # 현재 active 버전이 있으면 추천
    for v in versions:
        if v.is_active:
            return v.version

    # 없으면 가장 최신 버전 추천
    return max(versions, key=lambda v: v.version).version


def _determine_reason(state: ProposalState, output_key: str) -> str:
    """재실행 이유 파악."""

    existing = state.get("artifact_versions", {}).get(output_key, [])

    if not existing:
        return "first_run"

    # 최근 버전 선택 이력 확인
    history = state.get("version_selection_history", [])

    if history:
        last = history[-1]
        if output_key in last.get("selected_versions", {}):
            return "rerun_after_upstream_change"

    return "manual_rerun"


# 의존성 레벨
class DependencyLevel(Enum):
    REQUIRED = "required"
    STRONGLY_RECOMMENDED = "strongly_recommended"
    OPTIONAL = "optional"


# NODE_DEPENDENCIES는 edges.py에서 import
from app.graph.edges import NODE_DEPENDENCIES
```

---

## 🎨 프론트엔드 설계

### VersionSelectionModal.tsx

```typescript
// frontend/components/VersionSelectionModal.tsx

interface VersionConflict {
  input_key: string;
  available_versions: number[];
  current_active: number;
  recommendation: number;
  dependency_mismatch?: {
    downstream_usage: Array<{
      key: string;
      version: number;
    }>;
    warning: string;
  };
}

export function VersionSelectionModal({
  conflicts,
  onConfirm,
  onCancel,
}: {
  conflicts: VersionConflict[];
  onConfirm: (selections: Record<string, number>) => Promise<void>;
  onCancel: () => void;
}) {
  const [selections, setSelections] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(false);

  const handleSelectVersion = (key: string, version: number) => {
    setSelections(prev => ({ ...prev, [key]: version }));
  };

  const handleConfirm = async () => {
    setLoading(true);
    try {
      await onConfirm(selections);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog
      isOpen
      title="산출물 버전 선택 필요"
      description="이동하려는 노드가 필요한 선행 작업의 버전을 선택해주세요."
      onClose={onCancel}
    >
      <div className="space-y-6">
        {conflicts.map(conflict => (
          <ConflictCard
            key={conflict.input_key}
            conflict={conflict}
            selected={selections[conflict.input_key]}
            onSelect={(v) => handleSelectVersion(conflict.input_key, v)}
          />
        ))}
      </div>

      <div className="flex gap-3 mt-6">
        <button
          onClick={onCancel}
          disabled={loading}
          className="btn btn-secondary flex-1"
        >
          취소
        </button>
        <button
          onClick={handleConfirm}
          disabled={loading || Object.keys(selections).length !== conflicts.length}
          className="btn btn-primary flex-1"
        >
          {loading ? "진행 중..." : "선택 완료 및 이동"}
        </button>
      </div>
    </Dialog>
  );
}

function ConflictCard({
  conflict,
  selected,
  onSelect,
}: {
  conflict: VersionConflict;
  selected?: number;
  onSelect: (version: number) => void;
}) {
  return (
    <div className="border rounded-lg p-4 space-y-3">
      {/* 제목 */}
      <h3 className="font-semibold text-sm">
        {conflict.input_key} 버전 선택
      </h3>

      {/* 버전 선택 버튼 */}
      <div className="flex gap-2">
        {conflict.available_versions.map(v => (
          <button
            key={v}
            onClick={() => onSelect(v)}
            className={`
              px-3 py-2 rounded font-mono text-sm
              ${selected === v
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 hover:bg-gray-200'
              }
              ${v === conflict.recommendation ? 'ring-2 ring-blue-400' : ''}
            `}
          >
            {v === conflict.recommendation && '⭐ '}
            v{v}
            {v === conflict.current_active && ' (현재)'}
          </button>
        ))}
      </div>

      {/* 의존성 경고 */}
      {conflict.dependency_mismatch && (
        <div className="bg-yellow-50 border border-yellow-200 rounded p-3 space-y-2">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-yellow-600 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-yellow-800">
              <p className="font-semibold">의존성 경고</p>
              <p>{conflict.dependency_mismatch.warning}</p>
            </div>
          </div>

          {conflict.dependency_mismatch.downstream_usage.length > 0 && (
            <details className="text-xs text-yellow-700">
              <summary className="cursor-pointer font-semibold">
                영향받는 산출물 ({conflict.dependency_mismatch.downstream_usage.length}개)
              </summary>
              <ul className="list-disc list-inside mt-1 space-y-0.5">
                {conflict.dependency_mismatch.downstream_usage.map(usage => (
                  <li key={`${usage.key}-${usage.version}`}>
                    {usage.key} v{usage.version}
                  </li>
                ))}
              </ul>
            </details>
          )}
        </div>
      )}
    </div>
  );
}
```

---

## 📋 구현 순서 및 파일 목록

### Phase 1: 기본 버전화 (2일)

**필수 파일**:

```
1. database/migrations/
   └─ 015_artifact_versioning.sql

2. app/services/
   ├─ version_manager.py (신규)
   │  ├─ execute_node_and_create_version()
   │  ├─ validate_move_and_resolve_versions()
   │  ├─ _check_dependency_mismatch()
   │  ├─ _recommend_version()
   │  └─ _determine_reason()
   └─ artifact_controller.py (신규, 선택)

3. app/graph/
   ├─ state.py (수정)
   │  ├─ ArtifactVersion 모델 추가
   │  ├─ artifact_versions 필드
   │  ├─ active_versions 필드
   │  └─ version_selection_history 필드
   └─ nodes/ (모든 노드)
      └─ 각 노드에 execute_node_and_create_version() 호출 추가

4. app/api/
   └─ routes_artifacts.py (수정)
      └─ GET /artifacts/versions 엔드포인트
      └─ POST /artifacts/compare (Phase 3)
```

### Phase 2: 버전 선택 (2일)

**필수 파일**:

```
1. app/api/
   └─ routes_workflow.py (수정)
      ├─ POST /move-to-node/{target_node}
      ├─ POST /validate-move/{target_node}
      └─ GET /node-dependencies

2. frontend/components/
   └─ VersionSelectionModal.tsx (신규)

3. frontend/pages/
   └─ proposals/[id]/page.tsx (수정)
      └─ 이동 메뉴 통합
```

---

## ✅ 검증 기준

### Phase 1 검증

- [ ] 노드 재실행 시 자동 v2 생성
- [ ] active_versions 올바르게 업데이트
- [ ] checksum 중복 감지
- [ ] used_by 필드 추적
- [ ] DB 조회 응답 시간 < 100ms

### Phase 2 검증

- [ ] 1개 버전: 자동 선택
- [ ] 3개 버전: 모달 표시
- [ ] 의존성 충돌 감지
- [ ] 선택 이력 DB 저장
- [ ] 선택 후 올바른 버전 사용

---

## 📊 성능 예상

| 항목 | 목표 | 예상 |
|-----|------|------|
| 버전 조회 | < 100ms | 50-80ms |
| 이동 검증 | < 500ms | 200-400ms |
| DB 저장 | per node | ~50ms |
| State 크기 증가 | < 20% | 15-18% |

---

## 🔗 다음 단계

**Do Phase (구현)**:
- Phase 1: DB 마이그레이션 + version_manager.py 구현
- Phase 2: API 엔드포인트 + Modal UI 구현

---

**설계 완료 일시**: 2026-03-30
**상태**: ✅ Design 완료, Do Phase 대기 중
