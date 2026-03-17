"""
산출물 + 다운로드 + Compliance Matrix API (§12-4)

GET  /api/proposals/{id}/artifacts/{step}                          — 산출물 조회
PUT  /api/proposals/{id}/artifacts/{step}                          — 산출물 저장 (에디터)
POST /api/proposals/{id}/artifacts/{step}/sections/{sid}/regenerate — 섹션 AI 재생성
POST /api/proposals/{id}/ai-assist                                 — AI 인라인 제안
GET  /api/proposals/{id}/download/docx                             — DOCX 다운로드
GET  /api/proposals/{id}/download/hwpx                             — HWPX 다운로드
GET  /api/proposals/{id}/download/pptx                             — PPTX 다운로드
GET  /api/proposals/{id}/compliance                                — Compliance Matrix
POST /api/proposals/{id}/compliance/check                          — Compliance AI 체크 실행
"""

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import Response
from pydantic import BaseModel

from app.api.deps import get_current_user, require_project_access
from app.exceptions import PropNotFoundError

router = APIRouter(prefix="/api/proposals", tags=["artifacts"])
logger = logging.getLogger(__name__)


async def _upload_to_storage_with_tracking(
    proposal_id: str,
    file_bytes: bytes,
    file_key: str,
    content_type: str,
) -> None:
    """Storage 업로드 + proposals.storage_upload_failed 추적 (설계 §8 finally 패턴).

    업로드 성공 시 storage_path 업데이트, 실패 시 storage_upload_failed=True 설정.
    """
    from app.utils.supabase_client import get_async_client

    bucket = "proposal-files"
    storage_path = f"{proposal_id}/proposal.{file_key}"
    col_map = {"docx": "storage_path_docx", "pptx": "storage_path_pptx", "hwpx": "storage_path_hwpx"}
    db_col = col_map.get(file_key)

    try:
        client = await get_async_client()
        await client.storage.from_(bucket).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": content_type, "upsert": "true"},
        )
        # 성공: DB에 경로 기록
        if db_col:
            await (
                client.table("proposals")
                .update({db_col: storage_path, "storage_upload_failed": False})
                .eq("id", proposal_id)
                .execute()
            )
        logger.info(f"[{proposal_id}] Storage 업로드 완료: {storage_path}")
    except Exception as e:
        logger.warning(f"[{proposal_id}] {file_key} Storage 업로드 실패: {e}")
        # 실패: storage_upload_failed 플래그 설정
        try:
            client = await get_async_client()
            await (
                client.table("proposals")
                .update({"storage_upload_failed": True})
                .eq("id", proposal_id)
                .execute()
            )
        except Exception:
            pass


@router.get("/{proposal_id}/artifacts/{step}")
async def get_artifacts(
    proposal_id: str,
    step: str,
    user=Depends(get_current_user),
):
    """단계별 산출물 조회 (그래프 상태에서 추출)."""
    from app.api.routes_workflow import _get_graph

    graph = await _get_graph()
    config = {"configurable": {"thread_id": proposal_id}}

    try:
        snapshot = await graph.aget_state(config)
        if not snapshot:
            raise PropNotFoundError(proposal_id)

        state = snapshot.values
        artifact_map = {
            "search": state.get("search_results"),
            "rfp_fetch": state.get("bid_detail"),
            "rfp_analyze": state.get("rfp_analysis"),
            "research": state.get("research_brief"),
            "go_no_go": state.get("go_no_go"),
            "strategy": state.get("strategy"),
            "plan": state.get("plan"),
            "proposal": state.get("proposal_sections"),
            "self_review": state.get("parallel_results", {}).get("_self_review_score"),
            "presentation_strategy": state.get("presentation_strategy"),
            "ppt": state.get("ppt_slides"),
        }

        artifact = artifact_map.get(step)
        if artifact is None:
            return {"step": step, "artifact": None, "message": "해당 단계 산출물 없음"}

        # Pydantic 모델 직렬화
        if hasattr(artifact, "model_dump"):
            data = artifact.model_dump()
        elif isinstance(artifact, list):
            data = [a.model_dump() if hasattr(a, "model_dump") else a for a in artifact]
        else:
            data = artifact

        return {"step": step, "artifact": data}
    except PropNotFoundError:
        raise
    except Exception as e:
        logger.error(f"산출물 조회 실패: {e}")
        return {"step": step, "artifact": None, "error": str(e)}


class ArtifactSaveRequest(BaseModel):
    """에디터에서 수정된 산출물 저장 요청."""
    content: Any  # 저장할 데이터 (HTML 문자열, dict, list 등)
    change_source: str = "human_edit"  # 변경 출처


@router.put("/{proposal_id}/artifacts/{step}")
async def save_artifact(
    proposal_id: str,
    step: str,
    body: ArtifactSaveRequest,
    user=Depends(get_current_user),
):
    """에디터에서 수정한 산출물을 그래프 상태에 저장."""
    from app.api.routes_workflow import _get_graph

    graph = await _get_graph()
    config = {"configurable": {"thread_id": proposal_id}}

    snapshot = await graph.aget_state(config)
    if not snapshot:
        raise PropNotFoundError(proposal_id)

    state = snapshot.values

    # step → state key 매핑
    step_to_key = {
        "proposal": "proposal_sections",
        "strategy": "strategy",
        "plan": "plan",
        "ppt": "ppt_slides",
    }

    state_key = step_to_key.get(step)
    if not state_key:
        return {"error": f"수정 불가능한 단계: {step}", "saved": False}

    # proposal 섹션: content가 HTML 문자열이면 기존 섹션에 html_content 필드로 병합
    if step == "proposal" and isinstance(body.content, str):
        existing = state.get("proposal_sections", [])
        # 전체 HTML로 저장: 기존 리스트 유지 + _edited_html 추가
        update = {
            state_key: existing,
            "_edited_html": body.content,
            "_last_editor": user.get("name", user.get("id", "unknown")),
        }
    else:
        update = {state_key: body.content}

    await graph.aupdate_state(config, update)

    logger.info(
        f"산출물 저장: proposal={proposal_id}, step={step}, "
        f"source={body.change_source}, user={user.get('id')}"
    )

    return {
        "saved": True,
        "step": step,
        "message": f"{step} 산출물이 저장되었습니다.",
    }


class SectionRegenerateRequest(BaseModel):
    """섹션 AI 재생성 요청."""
    instructions: str = ""  # 재생성 시 추가 지시사항


@router.post("/{proposal_id}/artifacts/{step}/sections/{section_id}/regenerate")
async def regenerate_section(
    proposal_id: str,
    step: str,
    section_id: str,
    body: SectionRegenerateRequest,
    user=Depends(get_current_user),
):
    """특정 섹션만 AI로 재생성 (§12-4-1).

    기존 proposal_write_next 로직을 단일 섹션에 대해 실행한다.
    """
    if step != "proposal":
        return {"error": "재생성은 proposal 단계만 지원합니다.", "regenerated": False}

    from app.api.routes_workflow import _get_graph
    from app.prompts.section_prompts import classify_section_type, get_section_prompt
    from app.services.claude_client import claude_generate

    graph = await _get_graph()
    config = {"configurable": {"thread_id": proposal_id}}

    snapshot = await graph.aget_state(config)
    if not snapshot:
        raise PropNotFoundError(proposal_id)

    state = snapshot.values
    sections = state.get("proposal_sections", [])
    dynamic_sections = state.get("dynamic_sections", [])

    # 섹션 ID로 대상 찾기
    target_idx = None
    for i, sec in enumerate(sections):
        sec_id = sec.get("id") if isinstance(sec, dict) else getattr(sec, "id", None)
        if sec_id == section_id:
            target_idx = i
            break

    if target_idx is None:
        # dynamic_sections에서 인덱스로 시도
        if section_id.isdigit() and int(section_id) < len(sections):
            target_idx = int(section_id)
        else:
            return {"error": f"섹션 '{section_id}'을(를) 찾을 수 없습니다.", "regenerated": False}

    # 섹션 유형 분류 + 프롬프트 조립
    section_title = dynamic_sections[target_idx] if target_idx < len(dynamic_sections) else section_id
    section_type = classify_section_type(section_title)
    prompt_template = get_section_prompt(section_type)

    # 컨텍스트 구성 (간소화)
    rfp = state.get("rfp_analysis")
    rfp_dict = {}
    if rfp:
        rfp_dict = rfp.model_dump() if hasattr(rfp, "model_dump") else (rfp if isinstance(rfp, dict) else {})

    strategy = state.get("strategy")
    s_dict = {}
    if strategy:
        s_dict = strategy.model_dump() if hasattr(strategy, "model_dump") else (strategy if isinstance(strategy, dict) else {})

    context = f"""사업명: {rfp_dict.get('project_name', '')}
섹션 제목: {section_title}
포지셔닝: {state.get('positioning', 'defensive')}
전략 요약: {s_dict.get('executive_summary', '')}"""

    if body.instructions:
        context += f"\n\n추가 지시사항: {body.instructions}"

    user_prompt = prompt_template.format(
        section_title=section_title,
        context=context,
        storyline_context="",
        previous_sections_context="",
    )

    try:
        result = await claude_generate(
            prompt=user_prompt,
            system_prompt="제안서 섹션을 재생성합니다. JSON 형식으로 {\"title\": str, \"content\": str} 반환.",
            max_tokens=4096,
        )

        # 기존 섹션 업데이트
        updated_sections = list(sections)
        if isinstance(updated_sections[target_idx], dict):
            updated_sections[target_idx] = {
                **updated_sections[target_idx],
                "content": result.get("content", result.get("text", "")),
                "title": result.get("title", section_title),
            }
        else:
            sec = updated_sections[target_idx]
            if hasattr(sec, "content"):
                sec.content = result.get("content", result.get("text", ""))

        await graph.aupdate_state(config, {"proposal_sections": updated_sections})

        logger.info(f"섹션 재생성: proposal={proposal_id}, section={section_id}, user={user.get('id')}")

        return {
            "regenerated": True,
            "section_id": section_id,
            "section_title": section_title,
            "message": f"'{section_title}' 섹션이 재생성되었습니다.",
        }
    except Exception as e:
        logger.error(f"섹션 재생성 실패: {e}")
        return {"regenerated": False, "error": str(e)}


class AiAssistRequest(BaseModel):
    """AI 인라인 제안 요청 (§12-4-2)."""
    text: str  # 선택된 텍스트
    mode: str = "improve"  # improve | shorten | expand | formalize
    context: str = ""  # 주변 컨텍스트 (선택)


@router.post("/{proposal_id}/ai-assist")
async def ai_assist(
    proposal_id: str,
    body: AiAssistRequest,
    user=Depends(get_current_user),
):
    """에디터에서 선택한 텍스트에 대한 AI 개선 제안 (§12-4-2)."""
    from app.services.claude_client import claude_generate

    mode_prompts = {
        "improve": "다음 텍스트를 품질, 명확성, 설득력 면에서 개선하세요.",
        "shorten": "다음 텍스트를 핵심 내용을 유지하면서 간결하게 줄이세요.",
        "expand": "다음 텍스트를 구체적인 사례, 근거, 세부 내용을 추가하여 확장하세요.",
        "formalize": "다음 텍스트를 공공기관 제안서에 적합한 격식체로 변환하세요.",
    }

    instruction = mode_prompts.get(body.mode, mode_prompts["improve"])

    prompt = f"""{instruction}

원문:
{body.text}
"""
    if body.context:
        prompt += f"\n문맥:\n{body.context}\n"

    prompt += "\nJSON 형식으로 응답: {\"suggestion\": \"개선된 텍스트\", \"explanation\": \"변경 사유 (1줄)\"}"

    try:
        result = await claude_generate(
            prompt=prompt,
            system_prompt="제안서 텍스트 개선 어시스턴트. 한국어 공공 제안서 스타일을 유지합니다.",
            max_tokens=2048,
            temperature=0.4,
        )

        return {
            "suggestion": result.get("suggestion", result.get("text", "")),
            "explanation": result.get("explanation", ""),
            "mode": body.mode,
            "original_length": len(body.text),
            "suggestion_length": len(result.get("suggestion", "")),
        }
    except Exception as e:
        logger.error(f"AI 어시스트 실패: {e}")
        return {"suggestion": "", "error": str(e), "mode": body.mode}


@router.get("/{proposal_id}/download/docx")
async def download_docx(
    proposal_id: str,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
):
    """DOCX 다운로드 (중간 버전 포함) + Storage 업로드 (§8 finally 패턴)."""
    from app.api.routes_workflow import _get_graph
    from app.services.docx_builder import build_docx

    graph = await _get_graph()
    config = {"configurable": {"thread_id": proposal_id}}

    snapshot = await graph.aget_state(config)
    if not snapshot:
        raise PropNotFoundError(proposal_id)

    state = snapshot.values
    sections = state.get("proposal_sections", [])
    rfp = state.get("rfp_analysis")
    proposal_name = state.get("project_name", "제안서")

    if not sections:
        return Response(
            content=b"",
            status_code=204,
            headers={"X-Message": "No sections available"},
        )

    docx_bytes = await build_docx(sections, rfp, proposal_name)

    # Storage 비동기 업로드 (finally 패턴: 다운로드 응답은 즉시 반환)
    background_tasks.add_task(
        _upload_to_storage_with_tracking,
        proposal_id, docx_bytes, "docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    filename = f"{proposal_name}_제안서.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{proposal_id}/download/hwpx")
async def download_hwpx(
    proposal_id: str,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
):
    """HWPX 다운로드 (hwpxskill 기반 템플릿 조립)."""
    import tempfile
    from pathlib import Path

    from app.api.routes_workflow import _get_graph
    from app.services.hwpx_service import build_proposal_hwpx_async

    graph = await _get_graph()
    config = {"configurable": {"thread_id": proposal_id}}

    snapshot = await graph.aget_state(config)
    if not snapshot:
        raise PropNotFoundError(proposal_id)

    state = snapshot.values
    sections = state.get("proposal_sections", [])
    proposal_name = state.get("project_name", "제안서")

    if not sections:
        return Response(
            content=b"",
            status_code=204,
            headers={"X-Message": "No sections available"},
        )

    rfp = state.get("rfp_analysis")
    rfp_dict = {}
    if rfp:
        rfp_dict = rfp.model_dump() if hasattr(rfp, "model_dump") else (rfp if isinstance(rfp, dict) else {})

    metadata = {
        "project_name": proposal_name,
        "client_name": rfp_dict.get("client", ""),
        "bid_notice_number": rfp_dict.get("bid_notice_number", ""),
    }

    output_path = Path(tempfile.gettempdir()) / f"tenopa_{proposal_id}" / "proposal.hwpx"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    await build_proposal_hwpx_async(sections, output_path, metadata)
    hwpx_bytes = output_path.read_bytes()

    # Storage 비동기 업로드 (§8 finally 패턴)
    background_tasks.add_task(
        _upload_to_storage_with_tracking,
        proposal_id, hwpx_bytes, "hwpx", "application/zip",
    )

    filename = f"{proposal_name}_제안서.hwpx"
    return Response(
        content=hwpx_bytes,
        media_type="application/hwp+zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{proposal_id}/download/pptx")
async def download_pptx(
    proposal_id: str,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
):
    """PPTX 다운로드 — 컨설팅급(ppt_storyboard) 또는 경량(ppt_slides) 폴백 + Storage 업로드."""
    from app.api.routes_workflow import _get_graph

    graph = await _get_graph()
    config = {"configurable": {"thread_id": proposal_id}}

    snapshot = await graph.aget_state(config)
    if not snapshot:
        raise PropNotFoundError(proposal_id)

    state = snapshot.values
    storyboard = state.get("ppt_storyboard")
    slides = state.get("ppt_slides", [])
    proposal_name = state.get("project_name", "제안서")
    pres_strategy = state.get("presentation_strategy")

    if storyboard and storyboard.get("slides"):
        # 컨설팅급 렌더링 (presentation_pptx_builder)
        import asyncio
        import tempfile
        from pathlib import Path

        from app.services.presentation_pptx_builder import build_presentation_pptx

        output_path = Path(tempfile.gettempdir()) / f"tenopa_{proposal_id}" / "presentation.pptx"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(build_presentation_pptx, storyboard, output_path, proposal_name)
        pptx_bytes = output_path.read_bytes()
    elif slides:
        # 폴백: 경량 빌더
        from app.services.pptx_builder import build_pptx

        slide_dicts = [s.model_dump() if hasattr(s, "model_dump") else s for s in slides]
        pres_dict = pres_strategy.model_dump() if hasattr(pres_strategy, "model_dump") else pres_strategy
        pptx_bytes = await build_pptx(slide_dicts, proposal_name, pres_dict)
    else:
        return Response(
            content=b"",
            status_code=204,
            headers={"X-Message": "No slides available"},
        )

    # Storage 비동기 업로드 (§8 finally 패턴)
    background_tasks.add_task(
        _upload_to_storage_with_tracking,
        proposal_id, pptx_bytes, "pptx",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )

    filename = f"{proposal_name}_발표자료.pptx"
    return Response(
        content=pptx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{proposal_id}/compliance")
async def get_compliance_matrix(
    proposal_id: str,
    user=Depends(get_current_user),
):
    """Compliance Matrix 현재 상태."""
    from app.api.routes_workflow import _get_graph

    graph = await _get_graph()
    config = {"configurable": {"thread_id": proposal_id}}

    snapshot = await graph.aget_state(config)
    if not snapshot:
        raise PropNotFoundError(proposal_id)

    matrix = snapshot.values.get("compliance_matrix", [])
    data = [m.model_dump() if hasattr(m, "model_dump") else m for m in matrix]

    # 통계
    total = len(data)
    met = sum(1 for d in data if d.get("status") == "충족")
    unmet = sum(1 for d in data if d.get("status") == "미충족")
    unchecked = sum(1 for d in data if d.get("status") == "미확인")

    return {
        "items": data,
        "stats": {
            "total": total,
            "met": met,
            "unmet": unmet,
            "unchecked": unchecked,
            "compliance_rate": round(met / total * 100, 1) if total else 0,
        },
    }


@router.post("/{proposal_id}/compliance/check")
async def run_compliance_check(
    proposal_id: str,
    user=Depends(get_current_user),
):
    """Compliance Matrix AI 체크 실행."""
    from app.api.routes_workflow import _get_graph
    from app.services.compliance_tracker import ComplianceTracker

    graph = await _get_graph()
    config = {"configurable": {"thread_id": proposal_id}}

    snapshot = await graph.aget_state(config)
    if not snapshot:
        raise PropNotFoundError(proposal_id)

    state = snapshot.values
    sections = state.get("proposal_sections", [])
    matrix = state.get("compliance_matrix", [])

    if not sections or not matrix:
        return {"message": "섹션 또는 Compliance Matrix가 없습니다.", "checked": 0}

    updated = await ComplianceTracker.check_compliance(sections, matrix)
    data = [m.model_dump() if hasattr(m, "model_dump") else m for m in updated]

    return {
        "items": data,
        "checked": len(data),
        "message": f"Compliance 체크 완료: {len(data)}개 항목",
    }
