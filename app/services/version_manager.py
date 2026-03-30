"""
Artifact Versioning Service — Phase 1
관리자 노드별 산출물 자동 버전화 및 버전 선택 관리.

Features:
- Auto-create versions after node execution
- Checksum-based duplicate detection
- Dependency-based version conflict detection
- Smart version recommendation
- Human decision tracking (audit trail)
"""

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.graph.state import ArtifactVersion, ProposalState
from app.utils.supabase_client import get_async_client


class DependencyLevel(str, Enum):
    """버전 충돌 시 심각도 분류."""
    NONE = "none"  # 의존성 없음
    LOW = "low"  # 경고만 필요
    MEDIUM = "medium"  # 선택 권고
    HIGH = "high"  # 선택 필수
    CRITICAL = "critical"  # 이동 불가능


class VersionConflict(BaseModel):
    """버전 충돌 정보."""
    input_key: str
    versions: Optional[list[int]] = None
    status: str  # "SINGLE" | "MULTIPLE" | "MISSING"
    dependency_level: DependencyLevel = DependencyLevel.LOW


class MoveValidationResult(BaseModel):
    """노드 이동 검증 결과."""
    can_move: bool
    conflicts: list[VersionConflict] = []
    dependency_level: DependencyLevel = DependencyLevel.NONE
    recommendation: str = ""
    downstream_impact: list[str] = []
    message: str = ""


# ── 핵심 함수 ──


async def execute_node_and_create_version(
    proposal_id: UUID,
    node_name: str,
    output_key: str,
    artifact_data: dict,
    user_id: UUID,
    parent_node_name: Optional[str] = None,
    state: Optional[ProposalState] = None,
) -> tuple[int, ArtifactVersion]:
    """
    노드 실행 후 산출물 버전 자동 생성.

    Returns:
        (version_number, ArtifactVersion object)

    Process:
    1. Checksum 계산
    2. 중복 여부 확인 (checksum 기반)
    3. 다음 버전 번호 결정
    4. 버전 생성 사유 분류
    5. DB 저장
    6. State 업데이트
    """

    # 1. Checksum 계산
    checksum = _calculate_checksum(artifact_data)

    # 2. 중복 확인 (checksum 기반)
    try:
        supabase = await get_async_client()
        existing_query = (
            await supabase.table("proposal_artifacts")
            .select("version, is_deprecated")
            .match({
                "proposal_id": str(proposal_id),
                "node_name": node_name,
                "output_key": output_key,
                "checksum": checksum,
            })
            .order("version", desc=True)
            .limit(1)
            .execute()
        )

        if existing_query.data and not existing_query.data[0]["is_deprecated"]:
            # 중복 발견 — 기존 버전 반환
            existing_version = existing_query.data[0]["version"]

            # 기존 artifact 조회하여 ArtifactVersion 생성
            fetch_query = (
                await supabase.table("proposal_artifacts")
                .select("*")
                .match({
                    "proposal_id": str(proposal_id),
                    "node_name": node_name,
                    "output_key": output_key,
                    "version": existing_version,
                })
                .single()
                .execute()
            )

            artifact_obj = ArtifactVersion(**fetch_query.data)
            return existing_version, artifact_obj
    except Exception as e:
        print(f"Warning: checksum 중복 확인 실패: {e}")

    # 3. 다음 버전 번호 결정
    try:
        supabase = await get_async_client()
        max_query = (
            await supabase.table("proposal_artifacts")
            .select("version")
            .match({
                "proposal_id": str(proposal_id),
                "node_name": node_name,
                "output_key": output_key,
            })
            .order("version", desc=True)
            .limit(1)
            .execute()
        )

        next_version = (max_query.data[0]["version"] + 1 if max_query.data else 1)
    except Exception as e:
        print(f"Warning: max version 조회 실패: {e}")
        next_version = 1

    # 4. 버전 생성 사유 분류
    reason = _determine_reason(node_name, next_version, state)

    # 5. Artifact 저장
    artifact_record = {
        "proposal_id": str(proposal_id),
        "node_name": node_name,
        "output_key": output_key,
        "version": next_version,
        "artifact_data": artifact_data,
        "created_by": str(user_id),
        "parent_node_name": parent_node_name,
        "checksum": checksum,
        "artifact_size": len(json.dumps(artifact_data, default=str)),
        "is_active": True,
        "created_reason": reason,
    }

    supabase = await get_async_client()
    result = (
        await supabase.table("proposal_artifacts")
        .insert(artifact_record)
        .execute()
    )

    artifact_obj = ArtifactVersion(**result.data[0])

    # 6. State 업데이트
    if state:
        key = f"{node_name}_{output_key}"
        if "artifact_versions" not in state:
            state["artifact_versions"] = {}
        if "active_versions" not in state:
            state["active_versions"] = {}

        if key not in state["artifact_versions"]:
            state["artifact_versions"][key] = []

        state["artifact_versions"][key].append(artifact_obj)
        state["active_versions"][key] = next_version

    return next_version, artifact_obj


async def validate_move_and_resolve_versions(
    proposal_id: UUID,
    target_node: str,
    state: ProposalState,
) -> MoveValidationResult:
    """
    노드 이동 검증 및 버전 충돌 감지.

    Process:
    1. 목표 노드의 필수 입력 조회 (의존성 맵)
    2. 각 입력별 사용 가능한 버전 확인
    3. 의존성 수준 분류
    4. 후행 노드 영향도 분석
    5. 버전 추천
    """

    # 1. 목표 노드 의존성 조회
    required_inputs = _get_node_dependencies(target_node)

    # 2. 버전 충돌 감지
    conflicts: list[VersionConflict] = []
    missing_inputs: list[str] = []

    for input_key in required_inputs:
        # State에서 현재 활성 버전 확인
        active_version = state.get("active_versions", {}).get(input_key)

        if active_version is None:
            # 필수 입력이 없음
            conflicts.append(
                VersionConflict(
                    input_key=input_key,
                    status="MISSING",
                    dependency_level=DependencyLevel.HIGH,
                )
            )
            missing_inputs.append(input_key)
        else:
            # 단일 버전 사용 중 — 충돌 없음
            conflicts.append(
                VersionConflict(
                    input_key=input_key,
                    versions=[active_version],
                    status="SINGLE",
                    dependency_level=DependencyLevel.NONE,
                )
            )

    # 3. 의존성 수준 분류
    dependency_level = _classify_dependency_level(conflicts, target_node)

    # 4. 후행 노드 영향도 분석
    downstream = await _get_downstream_nodes(target_node, proposal_id, state)

    # 5. 메시지 생성
    can_move = dependency_level != DependencyLevel.CRITICAL
    message = _generate_validation_message(
        can_move, conflicts, dependency_level, downstream
    )

    return MoveValidationResult(
        can_move=can_move,
        conflicts=conflicts,
        dependency_level=dependency_level,
        downstream_impact=downstream,
        message=message,
    )


async def check_node_move_feasibility(
    proposal_id: UUID,
    target_node: str,
    state: ProposalState,
) -> dict:
    """
    노드 이동 가능 여부 사전 확인 (모달 표시 전).

    Returns:
        {
            "can_move": bool,
            "needs_modal": bool,  # 버전 선택 필요 여부
            "message": str,
            "conflicts": list[dict]
        }
    """
    result = await validate_move_and_resolve_versions(proposal_id, target_node, state)

    needs_modal = len(result.conflicts) > 0 and any(
        c.status == "MULTIPLE" for c in result.conflicts
    )

    return {
        "can_move": result.can_move,
        "needs_modal": needs_modal,
        "message": result.message,
        "conflicts": [c.dict() for c in result.conflicts],
    }


def _recommend_version(
    input_key: str,
    available_versions: list[int],
    state: ProposalState,
) -> int:
    """
    스마트 버전 추천: 활성 > 최신 > 가장 많이 사용된.

    Args:
        input_key: "{node_name}_{output_key}"
        available_versions: 사용 가능한 버전 번호 리스트
        state: 현재 workflow state

    Returns:
        추천 버전 번호
    """

    # 1. 활성 버전이 있으면 우선
    active = state.get("active_versions", {}).get(input_key)
    if active and active in available_versions:
        return active

    # 2. 없으면 최신 버전
    if available_versions:
        return max(available_versions)

    # 3. 그것도 없으면 첫 번째 버전
    return available_versions[0] if available_versions else 1


def _calculate_checksum(data: dict) -> str:
    """
    Artifact data의 SHA256 checksum 계산.
    중복 감지에 사용됨.
    """
    data_str = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(data_str.encode()).hexdigest()


def _determine_reason(node_name: str, version: int, state: Optional[ProposalState]) -> str:
    """
    버전 생성 사유 분류.

    Returns:
        "first_run" | "rerun_after_change" | "manual_rerun"
    """

    if version == 1:
        return "first_run"

    # State에서 이전 버전 확인
    if state:
        active = state.get("active_versions", {})
        if active:
            return "manual_rerun"

    return "rerun_after_change"


def _get_node_dependencies(node_name: str) -> list[str]:
    """
    노드의 필수 입력 목록 조회.

    의존성 맵 기반 (hardcoded for now, 나중에 DB로 변경 가능).
    """

    # Node Dependency Map (from COMPREHENSIVE-IMPLEMENTATION-REVIEW.md)
    dependencies: dict[str, list[str]] = {
        # STEP 8A nodes
        "proposal_section_validator": ["proposal_sections"],
        "proposal_sections_consolidation": ["proposal_sections"],
        "mock_evaluation_analysis": ["proposal_sections"],
        "mock_evaluation_feedback_processor": ["mock_evaluation_analysis"],
        "proposal_write_next": ["strategy", "customer_context"],
        # STEP 2-3 dependencies
        "strategy_generate": ["go_no_go", "rfp_analysis"],
        "plan_nodes": ["strategy"],
        "proposal_nodes": ["plan", "rfp_analysis"],
        "ppt_nodes": ["proposal_sections", "strategy"],
    }

    return dependencies.get(node_name, [])


def _classify_dependency_level(
    conflicts: list[VersionConflict], target_node: str
) -> DependencyLevel:
    """
    버전 충돌의 심각도 분류.

    Logic:
    - MISSING 필수 입력이 있으면: CRITICAL
    - MULTIPLE 버전이 있으면: HIGH
    - 모두 SINGLE이면: NONE
    """

    has_critical = any(c.status == "MISSING" for c in conflicts)
    if has_critical:
        return DependencyLevel.CRITICAL

    has_multiple = any(c.status == "MULTIPLE" for c in conflicts)
    if has_multiple:
        return DependencyLevel.HIGH

    return DependencyLevel.NONE


async def _get_downstream_nodes(
    node_name: str, proposal_id: UUID, state: ProposalState
) -> list[str]:
    """
    대상 노드의 출력을 사용하는 후행 노드 목록 조회.

    Process:
    1. Node dependency map에서 역 의존성 확인
    2. 현재 workflow state에서 활성 노드 확인
    3. 영향받을 노드 반환
    """

    # Reverse dependency map
    reverse_deps: dict[str, list[str]] = {
        "proposal_sections": [
            "proposal_section_validator",
            "proposal_sections_consolidation",
            "mock_evaluation_analysis",
            "proposal_nodes",
            "ppt_nodes",
        ],
        "strategy": ["plan_nodes", "proposal_write_next"],
        "go_no_go": ["strategy_generate"],
        "rfp_analysis": ["strategy_generate", "proposal_nodes"],
        "customer_context": ["proposal_write_next"],
    }

    downstream = reverse_deps.get(node_name, [])

    # 현재 workflow에서 실제 실행되는 노드만 필터링
    current_step = state.get("current_step", "")
    active_downstream = [
        node for node in downstream
        if node in current_step or state.get("parallel_results", {}).get(node)
    ]

    return active_downstream


def _generate_validation_message(
    can_move: bool,
    conflicts: list[VersionConflict],
    dependency_level: DependencyLevel,
    downstream: list[str],
) -> str:
    """검증 결과 메시지 생성."""

    if not can_move:
        missing = [c.input_key for c in conflicts if c.status == "MISSING"]
        return f"필수 입력이 없습니다: {', '.join(missing)}"

    if dependency_level == DependencyLevel.HIGH:
        multiple = [c.input_key for c in conflicts if c.status == "MULTIPLE"]
        return f"버전 선택이 필요합니다: {', '.join(multiple)}"

    if downstream:
        return f"이 노드의 출력을 {', '.join(downstream)}에서 사용 중입니다."

    return "노드 이동 가능합니다."


# ── 후행 함수 (Future phases) ──


async def check_dependency_mismatch(
    target_node: str, selected_versions: dict[str, int], state: ProposalState
) -> list[dict]:
    """
    선택된 버전과 후행 노드의 의존성 불일치 분석.
    (Phase 2 feature)
    """
    pass


async def compare_versions(
    proposal_id: UUID, node_name: str, output_key: str, version1: int, version2: int
) -> dict:
    """
    두 버전의 차이점 분석.
    (Phase 3 feature)
    """
    pass


async def rollback_version(
    proposal_id: UUID, node_name: str, output_key: str, target_version: int
) -> bool:
    """
    특정 버전으로 롤백.
    (Phase 3 feature)
    """
    pass
