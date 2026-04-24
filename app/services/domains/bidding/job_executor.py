"""
Job Executor — 실제 작업을 실행하는 엔진 (STEP 8)

역할:
- 작업 타입별 실행 (STEP 4A/4B/5A/5B/6)
- 각 STEP별 서비스 호출
- 타임아웃 처리
- 에러 로깅
"""

import asyncio
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class JobExecutor:
    """실제 작업을 실행하는 엔진"""

    # 작업 타입별 타임아웃 (초)
    TASK_TIMEOUTS = {
        "step4a_diagnosis": 120,      # 정확도 검증
        "step4a_regenerate": 120,     # 섹션 재작성
        "step4b_pricing": 120,        # 입찰가 산정
        "step5a_pptx": 180,           # PPT 생성
        "step5b_submission": 150,     # 제출서류
        "step6_evaluation": 150,      # 모의평가
    }

    def __init__(
        self,
        proposal_service: Optional["ProposalService"] = None,
        document_ingestion_service: Optional["DocumentIngestionService"] = None,
        hwpx_service: Optional["HwpxService"] = None,
        pptx_builder: Optional["PptxBuilder"] = None,
    ):
        self.proposal_svc = proposal_service
        self.ingestion_svc = document_ingestion_service
        self.hwpx_svc = hwpx_service
        self.pptx = pptx_builder
        self.logger = logger

    async def execute(self, job_dict: dict) -> dict:
        """Job 실행"""
        job_type = job_dict.get("type")
        payload = job_dict.get("payload", {})
        proposal_id = job_dict.get("proposal_id")

        self.logger.info(f"Executing job {job_dict['id']} (type={job_type})")

        # 타임아웃 설정
        timeout = self.TASK_TIMEOUTS.get(job_type, 120)

        try:
            if job_type == "step4a_diagnosis":
                result = await asyncio.wait_for(
                    self._step4a_diagnosis(proposal_id, payload),
                    timeout=timeout
                )
            elif job_type == "step4a_regenerate":
                result = await asyncio.wait_for(
                    self._step4a_regenerate(proposal_id, payload),
                    timeout=timeout
                )
            elif job_type == "step4b_pricing":
                result = await asyncio.wait_for(
                    self._step4b_pricing(proposal_id, payload),
                    timeout=timeout
                )
            elif job_type == "step5a_pptx":
                result = await asyncio.wait_for(
                    self._step5a_pptx(proposal_id, payload),
                    timeout=timeout
                )
            elif job_type == "step5b_submission":
                result = await asyncio.wait_for(
                    self._step5b_submission(proposal_id, payload),
                    timeout=timeout
                )
            elif job_type == "step6_evaluation":
                result = await asyncio.wait_for(
                    self._step6_evaluation(proposal_id, payload),
                    timeout=timeout
                )
            else:
                raise ValueError(f"Unknown job type: {job_type}")

            return {"success": True, "data": result}

        except asyncio.TimeoutError:
            error_msg = f"Job execution timeout after {timeout}s (type={job_type})"
            self.logger.error(error_msg)
            raise TimeoutError(error_msg)
        except Exception as e:
            self.logger.error(f"Job execution failed: {e}", exc_info=True)
            raise

    # ── Task Handlers ──

    async def _step4a_diagnosis(self, proposal_id: str, payload: dict) -> dict:
        """
        STEP 4A: 정확도 검증

        payload:
          - section_ids: list[str]  # 검증할 섹션 목록 (선택)
          - model: str              # 사용할 모델 (기본값: sonnet)
        """
        section_ids = payload.get("section_ids", [])
        model = payload.get("model", "sonnet")

        self.logger.info(f"Running STEP 4A diagnosis for {len(section_ids)} sections")

        if not self.ingestion_svc:
            raise RuntimeError("DocumentIngestionService not available")

        # Document Ingestion의 정확도 검증 엔진 호출
        result = await self.ingestion_svc.run_accuracy_validator(
            proposal_id=proposal_id,
            section_ids=section_ids,
            model=model,
        )

        return result

    async def _step4a_regenerate(self, proposal_id: str, payload: dict) -> dict:
        """
        STEP 4A: 섹션 재작성

        payload:
          - section_ids: list[str]
          - feedback: str           # 사용자 피드백
        """
        section_ids = payload.get("section_ids", [])
        feedback = payload.get("feedback", "")

        self.logger.info(f"Regenerating {len(section_ids)} sections")

        if not self.proposal_svc:
            raise RuntimeError("ProposalService not available")

        # LangGraph에서 proposal_nodes.py의 재작성 로직 호출
        result = await self.proposal_svc.regenerate_sections(
            proposal_id=proposal_id,
            section_ids=section_ids,
            feedback=feedback,
        )

        return result

    async def _step4b_pricing(self, proposal_id: str, payload: dict) -> dict:
        """
        STEP 4B: 입찰가 산정

        payload:
          - 가격 산정 파라미터
        """
        self.logger.info("Calculating pricing")

        if not self.proposal_svc:
            raise RuntimeError("ProposalService not available")

        # bid_plan.py의 로직 호출
        result = await self.proposal_svc.calculate_pricing(
            proposal_id=proposal_id,
            **payload
        )

        return result

    async def _step5a_pptx(self, proposal_id: str, payload: dict) -> dict:
        """
        STEP 5A: PPT 생성

        payload:
          - 프레젠테이션 생성 파라미터
        """
        self.logger.info("Building PPTX presentation")

        if not self.pptx:
            raise RuntimeError("PptxBuilder not available")

        # pptx_builder.py의 로직 호출
        pptx_bytes = await self.pptx.build(
            proposal_id=proposal_id,
            **payload
        )

        if not self.proposal_svc:
            raise RuntimeError("ProposalService not available")

        # S3에 저장
        s3_url = await self.proposal_svc.save_artifact(
            proposal_id=proposal_id,
            name="presentation.pptx",
            content=pptx_bytes,
            mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )

        return {"pptx_url": s3_url}

    async def _step5b_submission(self, proposal_id: str, payload: dict) -> dict:
        """
        STEP 5B: 제출서류 준비

        payload:
          - 제출 서류 생성 파라미터
        """
        self.logger.info("Preparing submission documents")

        if not self.proposal_svc:
            raise RuntimeError("ProposalService not available")

        result = await self.proposal_svc.prepare_submission(
            proposal_id=proposal_id,
            **payload
        )

        return result

    async def _step6_evaluation(self, proposal_id: str, payload: dict) -> dict:
        """
        STEP 6: 모의평가

        payload:
          - 평가 파라미터
        """
        self.logger.info("Running evaluation")

        if not self.proposal_svc:
            raise RuntimeError("ProposalService not available")

        result = await self.proposal_svc.run_evaluation(
            proposal_id=proposal_id,
            **payload
        )

        return result
