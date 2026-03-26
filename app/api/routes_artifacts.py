"""
산출물 + 다운로드 + Compliance Matrix API (§12-4)

GET  /api/proposals/{id}/artifacts/{step}                          — 산출물 조회
PUT  /api/proposals/{id}/artifacts/{step}                          — 산출물 저장 (에디터)
POST /api/proposals/{id}/artifacts/{step}/sections/{sid}/regenerate — 섹션 AI 재생성
POST /api/proposals/{id}/ai-assist                                 — AI 인라인 제안
GET  /api/proposals/{id}/download/docx                             — DOCX 다운로드
GET  /api/proposals/{id}/download/hwpx                             — HWPX 다운로드
GET  /api/proposals/{id}/download/pptx                             — PPTX 다운로드
GET  /api/proposals/{id}/download/cost-sheet                       — 산출내역서 DOCX 다운로드 (기본)
GET  /api/proposals/{id}/cost-sheet/draft                          — 산출내역서 초안 데이터 (편집용)
POST /api/proposals/{id}/cost-sheet/generate                       — 편집된 데이터로 DOCX 생성
GET  /api/proposals/{id}/compliance                                — Compliance Matrix
POST /api/proposals/{id}/compliance/check                          — Compliance AI 체크 실행
"""

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import Response
from pydantic import BaseModel

from app.api.deps import get_current_user, require_project_access
from app.config import settings
from app.exceptions import PropNotFoundError
from app.models.auth_schemas import CurrentUser
from app.models.artifact_schemas import (
    ArtifactResponse, ArtifactSaveResponse,
    SectionRegenerateResponse, AiAssistResponse, CostSheetDraftResponse,
    ComplianceMatrixResponse, ComplianceCheckResponse,
)

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
    아카이브 테이블에도 바이너리 산출물 등록.
    """
    from app.utils.supabase_client import get_async_client

    bucket = settings.storage_bucket_proposals
    storage_path = f"{proposal_id}/proposal.{file_key}"
    col_map = {"docx": "storage_path_docx", "pptx": "storage_path_pptx", "hwpx": "storage_path_hwpx"}
    db_col = col_map.get(file_key)

    # 아카이브 등록 (바이너리 산출물)
    archive_map = {
        "docx": ("proposal_docx", "proposal", "제안서 DOCX", "proposal/proposal.docx"),
        "hwpx": ("proposal_hwpx", "proposal", "제안서 HWPX", "proposal/proposal.hwpx"),
        "pptx": ("ppt_pptx", "presentation", "발표자료 PPTX", "presentation/proposal.pptx"),
    }
    archive_info = archive_map.get(file_key)
    if archive_info:
        try:
            from app.services.project_archive_service import archive_binary_artifact
            await archive_binary_artifact(
                proposal_id,
                doc_type=archive_info[0],
                category=archive_info[1],
                title=archive_info[2],
                file_format=file_key,
                file_bytes=file_bytes,
                storage_subpath=archive_info[3],
                graph_step="download",
                source="ai",
            )
        except Exception as e:
            logger.warning(f"[{proposal_id}] archive 등록 실패 ({file_key}): {e}")

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


@router.get("/{proposal_id}/artifacts/{step}", response_model=ArtifactResponse)
async def get_artifacts(
    proposal_id: str,
    step: str,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
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
            "bid_plan": state.get("bid_plan"),
            "bid_budget_constraint": state.get("bid_budget_constraint"),
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
        logger.error(f"산출물 조회 실패: {e}", exc_info=True)
        return {"step": step, "artifact": None, "error": "산출물 조회 중 오류가 발생했습니다."}


class ArtifactSaveRequest(BaseModel):
    """에디터에서 수정된 산출물 저장 요청."""
    content: Any  # 저장할 데이터 (HTML 문자열, dict, list 등)
    change_source: str = "human_edit"  # 변경 출처


@router.put("/{proposal_id}/artifacts/{step}", response_model=ArtifactSaveResponse)
async def save_artifact(
    proposal_id: str,
    step: str,
    body: ArtifactSaveRequest,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
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
            "_last_editor": user.name or user.id,
        }

        # Phase C: 사람 수정 추적
        try:
            from app.services.human_edit_tracker import record_action
            old_html = state.get("_edited_html", "")
            if not old_html:
                # 섹션 content를 이전 버전으로 사용
                for sec in existing:
                    sd = sec.model_dump() if hasattr(sec, "model_dump") else (sec if isinstance(sec, dict) else {})
                    old_html += sd.get("content", "")
            await record_action(
                proposal_id=proposal_id,
                section_id="full_proposal",
                action="edit",
                original=old_html[:10000],
                edited=body.content[:10000],
                user_id=user.id,
            )
        except Exception as e:
            logger.debug(f"수정 추적 실패 (무시): {e}")
    else:
        update = {state_key: body.content}

    await graph.aupdate_state(config, update)

    logger.info(
        f"산출물 저장: proposal={proposal_id}, step={step}, "
        f"source={body.change_source}, user={user.id}"
    )

    # GAP-4: artifacts 테이블에 버전 기록
    try:
        import json
        from app.utils.supabase_client import get_async_client as _get_client
        db = await _get_client()
        ver_res = await db.table("artifacts") \
            .select("version").eq("proposal_id", proposal_id).eq("step", step) \
            .order("version", desc=True).limit(1).execute()
        next_ver = (ver_res.data[0]["version"] + 1) if ver_res.data else 1

        content_str = json.dumps(body.content, ensure_ascii=False) if not isinstance(body.content, str) else body.content
        await db.table("artifacts").insert({
            "proposal_id": proposal_id,
            "step": step,
            "version": next_ver,
            "content": content_str[:50000],
            "change_source": body.change_source,
            "change_summary": f"{step} v{next_ver}",
            "created_by": user.id,
        }).execute()
    except Exception as e:
        logger.warning(f"아티팩트 버전 저장 실패 (무시): {e}")

    return {
        "saved": True,
        "step": step,
        "message": f"{step} 산출물이 저장되었습니다.",
    }


class SectionRegenerateRequest(BaseModel):
    """섹션 AI 재생성 요청."""
    instructions: str = ""  # 재생성 시 추가 지시사항


@router.post("/{proposal_id}/artifacts/{step}/sections/{section_id}/regenerate", response_model=SectionRegenerateResponse)
async def regenerate_section(
    proposal_id: str,
    step: str,
    section_id: str,
    body: SectionRegenerateRequest,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
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

        # Phase C: 재생성 추적
        try:
            from app.services.human_edit_tracker import record_action
            await record_action(
                proposal_id=proposal_id,
                section_id=section_id,
                action="regenerate",
                user_id=user.id,
            )
        except Exception:
            pass

        logger.info(f"섹션 재생성: proposal={proposal_id}, section={section_id}, user={user.id}")

        # GAP-4: artifacts 버전 기록 (ai_regenerate)
        try:
            import json
            from app.utils.supabase_client import get_async_client as _get_client
            db = await _get_client()
            ver_res = await db.table("artifacts") \
                .select("version").eq("proposal_id", proposal_id).eq("step", step) \
                .order("version", desc=True).limit(1).execute()
            next_ver = (ver_res.data[0]["version"] + 1) if ver_res.data else 1

            await db.table("artifacts").insert({
                "proposal_id": proposal_id,
                "step": step,
                "version": next_ver,
                "content": json.dumps(result, ensure_ascii=False)[:50000],
                "change_source": "ai_regenerate",
                "change_summary": f"{section_title} AI 재생성 v{next_ver}",
                "created_by": user.id,
            }).execute()
        except Exception as e:
            logger.warning(f"아티팩트 버전 저장 실패 (무시): {e}")

        return {
            "regenerated": True,
            "section_id": section_id,
            "section_title": section_title,
            "message": f"'{section_title}' 섹션이 재생성되었습니다.",
        }
    except Exception as e:
        logger.error(f"섹션 재생성 실패: {e}", exc_info=True)
        return {"regenerated": False, "error": "섹션 재생성 중 오류가 발생했습니다."}


class AiAssistRequest(BaseModel):
    """AI 인라인 제안 요청 (§12-4-2)."""
    text: str  # 선택된 텍스트
    mode: str = "improve"  # improve | shorten | expand | formalize
    context: str = ""  # 주변 컨텍스트 (선택)


@router.post("/{proposal_id}/ai-assist", response_model=AiAssistResponse)
async def ai_assist(
    proposal_id: str,
    body: AiAssistRequest,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
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
        logger.error(f"AI 어시스트 실패: {e}", exc_info=True)
        return {"suggestion": "", "error": "AI 어시스트 처리 중 오류가 발생했습니다.", "mode": body.mode}


@router.get("/{proposal_id}/download/docx")
async def download_docx(
    proposal_id: str,
    background_tasks: BackgroundTasks,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
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
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
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
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
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


@router.get("/{proposal_id}/download/cost-sheet")
async def download_cost_sheet(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """산출내역서 DOCX 다운로드 — bid_plan + plan_price 데이터 기반."""
    from app.api.routes_workflow import _get_graph
    from app.config import settings
    from app.services.cost_sheet_builder import build_cost_sheet

    graph = await _get_graph()
    config = {"configurable": {"thread_id": proposal_id}}

    snapshot = await graph.aget_state(config)
    if not snapshot:
        raise PropNotFoundError(proposal_id)

    state = snapshot.values
    bid_plan = state.get("bid_plan")
    plan = state.get("plan") or {}
    rfp = state.get("rfp_analysis")
    proposal_name = state.get("project_name", "제안서")

    bid_plan_data = bid_plan.model_dump() if hasattr(bid_plan, "model_dump") else (bid_plan or {})
    plan_price_data = plan.get("bid_price", {}) if isinstance(plan, dict) else {}

    # RFP 정보
    client = ""
    if rfp:
        client = rfp.client if hasattr(rfp, "client") else rfp.get("client", "") if isinstance(rfp, dict) else ""

    cost_standard = bid_plan_data.get("cost_breakdown", {}).get("cost_standard", "KOSA")
    if not cost_standard:
        cost_standard = "KOSA"

    buf = build_cost_sheet(
        project_name=proposal_name,
        client=client,
        proposer_name=settings.proposer_name or "TENOPA",
        bid_plan_data=bid_plan_data,
        plan_price_data=plan_price_data,
        cost_standard=cost_standard,
    )

    cost_bytes = buf.read()

    # 아카이브 등록 (산출내역서)
    try:
        from app.services.project_archive_service import archive_binary_artifact
        await archive_binary_artifact(
            proposal_id,
            doc_type="cost_sheet",
            category="bidding",
            title="산출내역서",
            file_format="docx",
            file_bytes=cost_bytes,
            storage_subpath="bidding/cost_sheet.docx",
            graph_step="cost_sheet",
            source="ai",
        )
    except Exception as e:
        logger.warning(f"[{proposal_id}] 산출내역서 archive 등록 실패: {e}")

    filename = f"{proposal_name}_산출내역서.docx"
    return Response(
        content=cost_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{proposal_id}/cost-sheet/draft", response_model=CostSheetDraftResponse)
async def get_cost_sheet_draft(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """산출내역서 초안 데이터 — 프론트엔드 편집용 JSON 반환."""
    from app.api.routes_workflow import _get_graph
    from app.config import settings

    graph = await _get_graph()
    config = {"configurable": {"thread_id": proposal_id}}
    snapshot = await graph.aget_state(config)
    if not snapshot:
        raise PropNotFoundError(proposal_id)

    state = snapshot.values
    bid_plan = state.get("bid_plan")
    plan = state.get("plan") or {}
    rfp = state.get("rfp_analysis")

    bid_plan_data = bid_plan.model_dump() if hasattr(bid_plan, "model_dump") else (bid_plan or {})
    plan_price = plan.get("bid_price", {}) if isinstance(plan, dict) else {}

    cost_breakdown = bid_plan_data.get("cost_breakdown", {})
    labor_cost = plan_price.get("labor_cost", {})
    labor_breakdown = labor_cost.get("breakdown", [])
    direct_expenses = plan_price.get("direct_expenses", {})
    overhead = plan_price.get("overhead", {})
    profit = plan_price.get("profit", {})

    client = ""
    if rfp:
        client = rfp.client if hasattr(rfp, "client") else rfp.get("client", "") if isinstance(rfp, dict) else ""

    cost_standard = cost_breakdown.get("cost_standard", plan_price.get("cost_standard", "KOSA")) or "KOSA"

    return {
        "project_name": state.get("project_name", ""),
        "client": client,
        "proposer_name": settings.proposer_name or "TENOPA",
        "cost_standard": cost_standard,
        "labor_breakdown": labor_breakdown,
        "labor_total": labor_cost.get("total", cost_breakdown.get("direct_labor", 0)),
        "expense_items": direct_expenses.get("items", []),
        "expense_total": direct_expenses.get("total", 0),
        "overhead_rate": overhead.get("rate", 1.10) if isinstance(overhead, dict) else 1.10,
        "overhead_total": overhead.get("total", 0) if isinstance(overhead, dict) else 0,
        "profit_rate": profit.get("rate", 0.22) if isinstance(profit, dict) else 0.22,
        "profit_total": profit.get("total", 0) if isinstance(profit, dict) else 0,
        "total_cost": plan_price.get("total_cost", bid_plan_data.get("recommended_bid", 0)),
        "budget_narrative": plan_price.get("budget_narrative", []),
    }


class CostSheetGenerateRequest(BaseModel):
    """산출내역서 편집 후 DOCX 생성 요청."""
    project_name: str = ""
    client: str = ""
    proposer_name: str = ""
    cost_standard: str = "KOSA"
    labor_breakdown: list[dict] = []
    expense_items: list[dict] = []
    overhead_rate: float = 1.10
    profit_rate: float = 0.22
    budget_narrative: list[dict] = []


@router.post("/{proposal_id}/cost-sheet/generate")
async def generate_cost_sheet(
    proposal_id: str,
    body: CostSheetGenerateRequest,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """편집된 산출내역서 데이터로 DOCX 생성·다운로드."""
    from app.services.cost_sheet_builder import build_cost_sheet

    # 편집된 데이터에서 합계 재계산
    labor_total = sum(
        item.get("subtotal", item.get("amount", 0)) for item in body.labor_breakdown
    )
    expense_total = sum(item.get("amount", 0) for item in body.expense_items)

    overhead_rate = body.overhead_rate if body.overhead_rate < 2 else body.overhead_rate - 1
    overhead_total = int(labor_total * overhead_rate)
    profit_total = int((labor_total + overhead_total) * body.profit_rate)

    subtotal = labor_total + expense_total + overhead_total + profit_total
    vat = int(subtotal * 0.10)
    total_cost = subtotal + vat

    plan_price_data = {
        "cost_standard": body.cost_standard,
        "labor_cost": {
            "breakdown": body.labor_breakdown,
            "total": labor_total,
        },
        "direct_expenses": {
            "items": body.expense_items,
            "total": expense_total,
        },
        "overhead": {"rate": body.overhead_rate, "total": overhead_total},
        "profit": {"rate": body.profit_rate, "total": profit_total},
        "total_cost": total_cost,
        "budget_narrative": body.budget_narrative,
    }

    buf = build_cost_sheet(
        project_name=body.project_name,
        client=body.client,
        proposer_name=body.proposer_name,
        bid_plan_data={},
        plan_price_data=plan_price_data,
        cost_standard=body.cost_standard,
    )

    filename = f"{body.project_name or '제안서'}_산출내역서.docx"
    return Response(
        content=buf.read(),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{proposal_id}/compliance", response_model=ComplianceMatrixResponse)
async def get_compliance_matrix(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
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


@router.post("/{proposal_id}/compliance/check", response_model=ComplianceCheckResponse)
async def run_compliance_check(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
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
