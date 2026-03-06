import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
import anthropic
from app.config import settings
from app.models.phase_schemas import Phase1Artifact, Phase2Artifact, Phase3Artifact, Phase4Artifact, Phase5Artifact
from app.services.rfp_parser import parse_rfp_text
from app.services.docx_builder import build_docx
from app.services.pptx_builder import build_pptx
from app.services.g2b_service import G2BService
from app.services.bid_calculator import BidCalculator, PersonnelInput, ProcurementMethod, parse_budget_string
from app.services.phase_prompts import PHASE2_SYSTEM, PHASE2_USER, PHASE3_SYSTEM, PHASE3_USER, PHASE4_SYSTEM, PHASE4_USER, PHASE5_SYSTEM, PHASE5_USER
from app.utils.claude_utils import extract_json_from_response
from app.services.template_service import get_template_toc
from app.utils.edge_functions import notify_proposal_complete
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)


class PhaseExecutor:
    def __init__(self, proposal_id, session_manager):
        self.proposal_id = proposal_id
        self.session_manager = session_manager
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model
        self._bg_tasks: set = set()

    def _bg_task(self, coro):
        """백그라운드 Task 생성 + 참조 저장 (GC 방지)"""
        task = asyncio.create_task(coro)
        self._bg_tasks.add(task)
        task.add_done_callback(self._bg_tasks.discard)
        return task

    def _update_status(self, phase_name):
        """세션 메모리 상태 업데이트 + Supabase proposals 테이블 업데이트"""
        self.session_manager.update_session(self.proposal_id, {"current_phase": phase_name, "status": "processing"})
        logger.info("[%s] %s" % (self.proposal_id, phase_name))
        self._bg_task(self._db_update_status(phase_name))

    async def _db_update_status(self, phase_name: str):
        """Supabase proposals 테이블에 현재 phase 상태 업데이트"""
        try:
            client = await get_async_client()
            await (
                client.table("proposals")
                .update({"current_phase": phase_name, "status": "processing"})
                .eq("id", self.proposal_id)
                .execute()
            )
        except Exception as e:
            logger.warning(f"[{self.proposal_id}] DB 상태 업데이트 실패 (무시): {e}")

    def _save_artifact(self, n, artifact):
        """세션 메모리 아티팩트 저장 + Supabase proposal_phases 테이블 upsert"""
        self.session_manager.update_session(self.proposal_id,
            {f"phase_artifact_{n}": artifact.model_dump(), "phases_completed": n})
        self._bg_task(self._db_save_artifact(n, artifact))

    async def _db_save_artifact(self, n: int, artifact):
        """Supabase proposal_phases 테이블에 아티팩트 upsert"""
        try:
            client = await get_async_client()
            phase_names = {
                1: "phase_1_research",
                2: "phase_2_analysis",
                3: "phase_3_plan",
                4: "phase_4_implement",
                5: "phase_5_test",
            }
            await (
                client.table("proposal_phases")
                .upsert({
                    "proposal_id": self.proposal_id,
                    "phase_number": n,
                    "phase_name": phase_names.get(n, f"phase_{n}"),
                    "artifact": artifact.model_dump(),
                    "status": "completed",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                })
                .execute()
            )
            # proposals 테이블 phases_completed 업데이트
            await (
                client.table("proposals")
                .update({"phases_completed": n})
                .eq("id", self.proposal_id)
                .execute()
            )
        except Exception as e:
            logger.warning(f"[{self.proposal_id}] DB 아티팩트 저장 실패 (무시): {e}")

    async def _log_usage(self, phase_num: int, model: str, input_tokens: int, output_tokens: int):
        """Supabase usage_logs 테이블에 토큰 사용량 기록"""
        try:
            client = await get_async_client()
            await (
                client.table("usage_logs")
                .insert({
                    "proposal_id": self.proposal_id,
                    "phase_number": phase_num,
                    "model": model,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens,
                    "logged_at": datetime.now(timezone.utc).isoformat(),
                })
                .execute()
            )
        except Exception as e:
            logger.warning(f"[{self.proposal_id}] 토큰 사용량 기록 실패 (무시): {e}")

    async def _handle_failure(self, phase_num: int, error_msg: str):
        """실패 시 Supabase proposals + proposal_phases 상태 업데이트"""
        try:
            client = await get_async_client()
            await (
                client.table("proposals")
                .update({
                    "status": "failed",
                    "failed_phase": str(phase_num),
                    "notes": f"Phase {phase_num} 실패: {error_msg[:500]}",
                })
                .eq("id", self.proposal_id)
                .execute()
            )
            await (
                client.table("proposal_phases")
                .upsert({
                    "proposal_id": self.proposal_id,
                    "phase_number": phase_num,
                    "status": "failed",
                    "error_msg": error_msg[:500],
                })
                .execute()
            )
        except Exception as e:
            logger.warning(f"[{self.proposal_id}] DB 실패 상태 업데이트 실패 (무시): {e}")

    async def _upload_to_storage(self, docx_path: str, pptx_path: str) -> dict:
        """
        DOCX/PPTX 파일을 Supabase Storage에 업로드

        버킷: proposal-files
        경로: {proposal_id}/proposal.docx, {proposal_id}/proposal.pptx

        Returns:
            {"docx_url": ..., "pptx_url": ..., "docx_storage_path": ..., "pptx_storage_path": ...}
        """
        result = {}
        try:
            client = await get_async_client()
            bucket = "proposal-files"

            uploads = [
                (docx_path, f"{self.proposal_id}/proposal.docx",
                 "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                 "docx"),
                (pptx_path, f"{self.proposal_id}/proposal.pptx",
                 "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                 "pptx"),
            ]

            for local_path, storage_path, content_type, key in uploads:
                if not local_path:
                    continue
                try:
                    import os
                    if not os.path.exists(local_path):
                        logger.warning(f"[{self.proposal_id}] 파일 없음: {local_path}")
                        continue

                    file_bytes = await asyncio.to_thread(lambda p=local_path: open(p, "rb").read())

                    await client.storage.from_(bucket).upload(
                        path=storage_path,
                        file=file_bytes,
                        file_options={
                            "content-type": content_type,
                            "upsert": "true",
                        },
                    )

                    public_url = client.storage.from_(bucket).get_public_url(storage_path)
                    result[f"{key}_url"] = public_url
                    result[f"{key}_storage_path"] = storage_path
                    logger.info(f"[{self.proposal_id}] Storage 업로드 완료: {storage_path}")

                except Exception as e:
                    logger.warning(f"[{self.proposal_id}] {key} 업로드 실패 (무시): {e}")

            # proposals 테이블 storage path 업데이트
            if result:
                update_payload = {}
                if "docx_storage_path" in result:
                    update_payload["storage_path_docx"] = result["docx_storage_path"]
                if "pptx_storage_path" in result:
                    update_payload["storage_path_pptx"] = result["pptx_storage_path"]
                if update_payload:
                    await (
                        client.table("proposals")
                        .update(update_payload)
                        .eq("id", self.proposal_id)
                        .execute()
                    )
                    logger.info(f"[{self.proposal_id}] DB storage 경로 업데이트 완료")

        except Exception as e:
            logger.warning(f"[{self.proposal_id}] Storage 업로드 전체 실패 (무시): {e}")

        return result

    def _parse(self, text):
        try:
            return extract_json_from_response(text)
        except Exception:
            import re
            m = re.search(r"[{].*[}]", text, re.DOTALL)
            if m:
                return json.loads(m.group())
            raise ValueError("JSON 파싱 실패")

    def _build_improvement_prompt(self, improvement_instructions, phase_num):
        if not improvement_instructions:
            return ""
        relevant = [i for i in improvement_instructions if i.get("phase") == phase_num]
        if not relevant:
            return ""
        parts = ["이전 피드백 개선 작업:"]
        for inst in relevant:
            fb = inst.get("feedback", {})
            actions = "\n".join("- " + a for a in fb.get("suggested_actions", []))
            parts.append(
                "개선 지침 #" + str(inst.get("instruction_id", "")) + "\n"
                + "우선순위: " + fb.get("priority", "medium") + "\n"
                + "설명: " + fb.get("description", "") + "\n"
                + "개선 방향:\n" + actions + "\n"
                + "기대 결과: " + fb.get("expected_outcome", "")
            )
        parts.append("위 지침을 반영하여 더 나은 결과를 만들어주세요.")
        return "\n\n".join(parts)

    async def _enhance_with_feedback(self, context: str, task_description: str) -> str:
        prompt = (task_description + "를 수행해주세요.\n\n"
                  + context + "\n\n결과를 간결한 텍스트로 반환해주세요.")
        r = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        return r.content[0].text.strip()

    async def phase1_research(self, rfp_content, improvement_instructions=None):
        self._update_status("phase_1_research")
        improvement_prompt = self._build_improvement_prompt(improvement_instructions, 1)

        rfp_data = await parse_rfp_text(rfp_content)
        summary = (
            "사업명: " + rfp_data.title + "\n"
            + "발주처: " + rfp_data.client_name + "\n"
            + "범위: " + rfp_data.project_scope[:200]
        )

        if improvement_prompt:
            summary = await self._enhance_with_feedback(
                "기존 분석: " + summary + "\n\n개선 지침: " + improvement_prompt,
                "RFP 분석 개선"
            )

        g2b_data = {}
        try:
            async with G2BService() as g2b:
                keywords = rfp_data.requirements[:3] if rfp_data.requirements else []
                contracts = await g2b.search_similar_contracts(
                    rfp_title=rfp_data.title,
                    rfp_description=rfp_data.project_scope,
                    keywords=keywords,
                )
                competitors = await g2b.identify_competitors(contracts, min_contracts=1)
                our_profile = {"overall_strength": 0.75, "strength_areas": ["AI", "빅데이터", "클라우드"]}
                strategy = await g2b.get_competitor_strategy_recommendations(competitors, our_profile)
                g2b_data = {
                    "similar_contracts": [
                        {
                            "title": c.title, "agency": c.agency, "contractor": c.contractor,
                            "amount": c.contract_amount, "similarity": round(c.similarity_score, 2)
                        }
                        for c in contracts[:5]
                    ],
                    "competitor_strategy": strategy,
                }
                logger.info(f"[{self.proposal_id}] G2B: 유사계약 {len(contracts)}건, 경쟁사 {len(competitors)}개사 식별")
        except Exception as e:
            logger.warning(f"[{self.proposal_id}] G2B 조회 실패 (무시): {e}")

        artifact = Phase1Artifact(
            summary=summary,
            structured_data=rfp_data.model_dump(),
            rfp_data=rfp_data,
            history_summary="이력 없음",
            g2b_competitor_data=g2b_data,
        )
        self._save_artifact(1, artifact)
        return artifact

    async def phase2_analysis(self, a1, improvement_instructions=None):
        self._update_status("phase_2_analysis")
        improvement_prompt = self._build_improvement_prompt(improvement_instructions, 2)
        g2b_summary = (
            json.dumps(a1.g2b_competitor_data, ensure_ascii=False)
            if a1.g2b_competitor_data else "나라장터 데이터 없음"
        )
        user_prompt = PHASE2_USER.format(
            rfp_summary=a1.summary,
            structured_data=json.dumps(a1.structured_data, ensure_ascii=False),
            g2b_data=g2b_summary
        )
        if improvement_prompt:
            user_prompt += "\n\n개선 지침을 반영해주세요:\n" + improvement_prompt

        r = await self.client.messages.create(
            model=self.model, max_tokens=4096, system=PHASE2_SYSTEM,
            messages=[{"role": "user", "content": user_prompt}]
        )
        d = self._parse(r.content[0].text)
        artifact = Phase2Artifact(
            summary=d.get("summary", ""),
            structured_data=d,
            token_count=r.usage.input_tokens + r.usage.output_tokens,
            key_requirements=d.get("key_requirements", []),
            evaluation_weights=d.get("evaluation_weights", {}),
            hidden_intent=d.get("hidden_intent", ""),
            risk_factors=d.get("risk_factors", []),
            competitor_landscape=d.get("competitor_landscape", {}),
            price_analysis=d.get("price_analysis", {})
        )
        self._save_artifact(2, artifact)
        self._bg_task(self._log_usage(2, self.model, r.usage.input_tokens, r.usage.output_tokens))
        return artifact

    async def phase3_plan(self, a2, improvement_instructions=None):
        self._update_status("phase_3_plan")
        improvement_prompt = self._build_improvement_prompt(improvement_instructions, 3)
        user_prompt = PHASE3_USER.format(
            analysis_summary=a2.summary,
            key_requirements=json.dumps(a2.key_requirements, ensure_ascii=False),
            evaluation_weights=json.dumps(a2.evaluation_weights, ensure_ascii=False),
            competitor_landscape=json.dumps(a2.competitor_landscape, ensure_ascii=False),
            evaluator_perspective=json.dumps(a2.structured_data.get("evaluator_perspective", {}), ensure_ascii=False),
            our_advantage_opportunities=json.dumps(a2.structured_data.get("our_advantage_opportunities", []), ensure_ascii=False),
            price_analysis=json.dumps(a2.price_analysis, ensure_ascii=False)
        )
        if improvement_prompt:
            user_prompt += "\n\n개선 지침을 반영해주세요:\n" + improvement_prompt

        r = await self.client.messages.create(
            model=self.model, max_tokens=8192, system=PHASE3_SYSTEM,
            messages=[{"role": "user", "content": user_prompt}]
        )
        d = self._parse(r.content[0].text)
        artifact = Phase3Artifact(
            summary=d.get("summary", ""),
            structured_data=d,
            token_count=r.usage.input_tokens + r.usage.output_tokens,
            win_strategy=d.get("win_strategy", ""),
            section_plan=d.get("section_plan", []),
            page_allocation=d.get("page_allocation", {}),
            team_plan=d.get("team_plan", ""),
            differentiation_strategy=d.get("differentiation_strategy", []),
            bid_price_strategy=d.get("bid_price_strategy", {}),
            win_theme=d.get("win_theme", {})
        )

        bid_calc_result = {}
        try:
            team_comp = d.get("team_composition", [])
            if team_comp:
                personnel = [
                    PersonnelInput(
                        role=p.get("role", "개발자"),
                        grade=p.get("grade", "중급"),
                        person_months=float(p.get("person_months", 1)),
                        labor_type=p.get("labor_type", "SW")
                    ) for p in team_comp
                ]
                method_str = d.get("procurement_method", "적격심사")
                method_map = {
                    "최저가": ProcurementMethod.LOWEST_PRICE,
                    "적격심사": ProcurementMethod.ADEQUATE_REVIEW,
                    "종합평가": ProcurementMethod.COMPREHENSIVE,
                    "수의계약": ProcurementMethod.NEGOTIATED,
                }
                method = method_map.get(method_str, ProcurementMethod.ADEQUATE_REVIEW)
                budget_int = parse_budget_string(a2.price_analysis.get("budget_range"))
                price_weight = int(a2.evaluation_weights.get("가격", 20))
                competitor_count = int(d.get("estimated_competitor_count", 5))
                calc = BidCalculator()
                cost = calc.calculate_cost(personnel)
                bid_result = calc.optimize_bid(
                    cost, method, budget=budget_int,
                    price_weight=price_weight, competitor_count=competitor_count
                )
                bid_calc_result = calc.to_dict(bid_result)
                artifact.bid_price_strategy.update({
                    "recommended_bid_fmt": bid_calc_result["recommended_bid_fmt"],
                    "recommended_ratio": bid_calc_result["recommended_ratio"],
                    "total_cost_fmt": bid_calc_result["cost_breakdown"]["total_cost_fmt"],
                    "price_competitiveness_message": bid_calc_result["price_competitiveness_message"],
                    "win_probability_note": bid_calc_result["win_probability_note"],
                })
                logger.info(f"[{self.proposal_id}] BidCalculator: 추천 입찰가={bid_calc_result['recommended_bid_fmt']}")
        except Exception as e:
            logger.warning(f"[{self.proposal_id}] BidCalculator 오류 (무시): {e}")

        artifact.bid_calculation = bid_calc_result
        self._save_artifact(3, artifact)
        self._bg_task(self._log_usage(3, self.model, r.usage.input_tokens, r.usage.output_tokens))
        return artifact

    async def phase4_implement(self, a3, a1, improvement_instructions=None):
        self._update_status("phase_4_implement")
        improvement_prompt = self._build_improvement_prompt(improvement_instructions, 4)
        rfp = a1.rfp_data
        toc = rfp.table_of_contents if rfp and rfp.table_of_contents else []
        if not toc:
            toc = await get_template_toc()
            logger.info(f"[{self.proposal_id}] RFP 목차 없음 — 템플릿 TOC 사용: {len(toc)}개 섹션")
        toc_text = json.dumps(toc, ensure_ascii=False)
        user_prompt = PHASE4_USER.format(
            project_name=rfp.title if rfp else "미정",
            client_name=rfp.client_name if rfp else "미정",
            project_scope=rfp.project_scope if rfp else "미정",
            duration=rfp.duration if rfp else "미정",
            budget=rfp.budget or "미정",
            requirements=json.dumps(rfp.requirements if rfp else [], ensure_ascii=False),
            win_theme=json.dumps(a3.win_theme, ensure_ascii=False),
            win_strategy=a3.win_strategy,
            section_plan=json.dumps(a3.section_plan, ensure_ascii=False),
            business_understanding_strategy=json.dumps(a3.structured_data.get("business_understanding_strategy", {}), ensure_ascii=False),
            differentiation_strategy=json.dumps(a3.differentiation_strategy, ensure_ascii=False),
            price_competitiveness_message=a3.bid_price_strategy.get("price_competitiveness_message", ""),
            table_of_contents=toc_text
        )
        if improvement_prompt:
            user_prompt += "\n\n개선 지침을 반영해주세요:\n" + improvement_prompt

        r = await self.client.messages.create(
            model=self.model, max_tokens=8192, system=PHASE4_SYSTEM,
            messages=[{"role": "user", "content": user_prompt}]
        )
        d = self._parse(r.content[0].text)
        # 동적 섹션 추출: Claude가 반환한 sections dict 사용, 없으면 최상위 키 폴백
        sections = d.get("sections")
        if not sections or not isinstance(sections, dict):
            sections = {k: v for k, v in d.items() if k not in ("summary", "sections") and isinstance(v, str)}
        project_name = rfp.title if rfp else "용역 제안서"
        artifact = Phase4Artifact(
            summary=d.get("summary", "완료"),
            structured_data={**d, "_project_name": project_name},
            token_count=r.usage.input_tokens + r.usage.output_tokens,
            sections=sections,
        )
        self._save_artifact(4, artifact)
        self._bg_task(self._log_usage(4, self.model, r.usage.input_tokens, r.usage.output_tokens))
        return artifact

    async def phase5_test(self, a4, a2, improvement_instructions=None):
        self._update_status("phase_5_test")
        improvement_prompt = self._build_improvement_prompt(improvement_instructions, 5)
        preview = json.dumps(
            {k: v[:1000] if isinstance(v, str) else v for k, v in a4.sections.items()},
            ensure_ascii=False
        )
        user_prompt = PHASE5_USER.format(
            key_requirements=json.dumps(a2.key_requirements, ensure_ascii=False),
            evaluation_weights=json.dumps(a2.evaluation_weights, ensure_ascii=False),
            sections_preview=preview
        )
        if improvement_prompt:
            user_prompt += "\n\n개선 지침을 반영해주세요:\n" + improvement_prompt

        r = await self.client.messages.create(
            model=self.model, max_tokens=2048, system=PHASE5_SYSTEM,
            messages=[{"role": "user", "content": user_prompt}]
        )
        d = self._parse(r.content[0].text)
        score = float(d.get("quality_score", 70))
        docx_path = pptx_path = ""
        if a4.sections:
            os.makedirs(settings.output_dir, exist_ok=True)
            docx_path = os.path.join(settings.output_dir, self.proposal_id + ".docx")
            pptx_path = os.path.join(settings.output_dir, self.proposal_id + ".pptx")
            project_name = a4.structured_data.get("_project_name", "용역 제안서")
            await asyncio.to_thread(build_docx, a4.sections, Path(docx_path), project_name)
            await asyncio.to_thread(build_pptx, a4.sections, Path(pptx_path), project_name)
        artifact = Phase5Artifact(
            summary=d.get("summary", ""),
            structured_data=d,
            token_count=r.usage.input_tokens + r.usage.output_tokens,
            quality_score=score,
            issues=d.get("issues", []),
            docx_path=docx_path,
            pptx_path=pptx_path,
            executive_summary=d.get("executive_summary", ""),
            win_probability=d.get("win_probability", ""),
            detailed_scores=d.get("detailed_scores", {})
        )
        self._save_artifact(5, artifact)
        self._bg_task(self._log_usage(5, self.model, r.usage.input_tokens, r.usage.output_tokens))
        return artifact

    async def execute_all(self, rfp_content, improvement_instructions=None):
        try:
            a1 = await self.phase1_research(rfp_content, improvement_instructions)
            a2 = await self.phase2_analysis(a1, improvement_instructions)
            a3 = await self.phase3_plan(a2, improvement_instructions)
            a4 = await self.phase4_implement(a3, a1, improvement_instructions)
            a5 = await self.phase5_test(a4, a2, improvement_instructions)
            self.session_manager.update_session(self.proposal_id, {"status": "completed", "phases_completed": 5})
            # DB 최종 상태 업데이트
            try:
                client = await get_async_client()
                await (
                    client.table("proposals")
                    .update({"status": "completed", "phases_completed": 5})
                    .eq("id", self.proposal_id)
                    .execute()
                )
            except Exception as db_err:
                logger.warning(f"[{self.proposal_id}] 완료 상태 DB 업데이트 실패 (무시): {db_err}")
            # Storage 업로드 (fire-and-forget)
            self._bg_task(self._upload_to_storage(
                docx_path=a5.docx_path or "",
                pptx_path=a5.pptx_path or "",
            ))
            session = self.session_manager.get_session(self.proposal_id)
            self._bg_task(notify_proposal_complete(
                proposal_id=self.proposal_id,
                proposal_title=session.get("rfp_title", ""),
            ))
            return a5
        except Exception as e:
            self.session_manager.update_session(self.proposal_id, {"status": "failed", "error": str(e)})
            self._bg_task(self._handle_failure(0, str(e)))
            raise

    async def execute_from_phase(self, start_phase: int, improvement_instructions=None):
        """특정 phase부터 재실행 (개선 지침 적용)"""
        if start_phase not in range(1, 6):
            raise ValueError(f"start_phase는 1~5여야 합니다: {start_phase}")
        try:
            session = self.session_manager.get_session(self.proposal_id)
            rfp_content = session["proposal_state"]["rfp_content"]

            def _load(artifact_cls, key):
                data = session.get(key, {})
                return artifact_cls(**{k: v for k, v in data.items() if k in artifact_cls.model_fields})

            # 재실행 시작 phase 이전 아티팩트는 세션에서 로드
            a1 = _load(Phase1Artifact, "phase_artifact_1") if start_phase > 1 else None
            a2 = _load(Phase2Artifact, "phase_artifact_2") if start_phase > 2 else None
            a3 = _load(Phase3Artifact, "phase_artifact_3") if start_phase > 3 else None
            a4 = _load(Phase4Artifact, "phase_artifact_4") if start_phase > 4 else None
            a5 = None

            if start_phase <= 1:
                a1 = await self.phase1_research(rfp_content, improvement_instructions)
            if start_phase <= 2:
                a2 = await self.phase2_analysis(a1, improvement_instructions)
            if start_phase <= 3:
                a3 = await self.phase3_plan(a2, improvement_instructions)
            if start_phase <= 4:
                a4 = await self.phase4_implement(a3, a1, improvement_instructions)
            if start_phase <= 5:
                a5 = await self.phase5_test(a4, a2, improvement_instructions)

            if a5 is None:
                raise RuntimeError("phase5_test가 실행되지 않았습니다.")

            self.session_manager.update_session(
                self.proposal_id, {"status": "completed", "phases_completed": 5}
            )
            # Storage 업로드 (fire-and-forget)
            self._bg_task(self._upload_to_storage(
                docx_path=a5.docx_path or "",
                pptx_path=a5.pptx_path or "",
            ))
            session = self.session_manager.get_session(self.proposal_id)
            self._bg_task(notify_proposal_complete(
                proposal_id=self.proposal_id,
                proposal_title=session.get("rfp_title", ""),
            ))
            return a5

        except Exception as e:
            self.session_manager.update_session(
                self.proposal_id, {"status": "failed", "error": str(e)}
            )
            raise
