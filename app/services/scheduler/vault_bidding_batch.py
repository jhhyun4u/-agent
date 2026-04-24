"""
Vault 낙찰가 분석 배치 처리 스케줄러
매일 정오 또는 수동 트리거로 실행
"""

import asyncio
import logging
from datetime import datetime, time
from typing import Optional, Dict, Any
from uuid import UUID

from app.services.domains.bidding.g2b_bidding_collector import G2BBiddingCollector
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)


class VaultBiddingBatchScheduler:
    """낙찰가 분석 배치 처리 스케줄러"""

    def __init__(self):
        self.collector = G2BBiddingCollector()
        self.batch_schedule_time = time(12, 0)  # 매일 정오
        self.is_running = False

    async def start_scheduler(self):
        """배치 처리 스케줄러 시작"""
        if self.is_running:
            logger.warning("Scheduler already running")
            return

        self.is_running = True
        logger.info("Starting Vault Bidding Batch Scheduler")

        while self.is_running:
            try:
                now = datetime.now()
                current_time = now.time()

                # 정해진 시간에 배치 실행
                if (
                    current_time.hour == self.batch_schedule_time.hour
                    and current_time.minute == self.batch_schedule_time.minute
                ):
                    logger.info("Running daily batch at scheduled time")
                    await self.run_daily_batch()

                # 1분마다 체크
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(60)

    async def stop_scheduler(self):
        """배치 처리 스케줄러 중지"""
        self.is_running = False
        logger.info("Stopping Vault Bidding Batch Scheduler")

    async def run_daily_batch(self) -> Dict[str, Any]:
        """
        매일 배치: 활성 제안서들의 낙찰가 분석 자동 실행

        Returns:
            배치 실행 결과
            {
                "success": True,
                "processed_count": 5,
                "success_count": 4,
                "failure_count": 1,
                "details": [...]
            }
        """
        try:
            logger.info("Starting daily bidding analysis batch")

            client = await get_async_client()

            # 활성 제안서 조회 (Step 3-4 진행 중)
            proposals = await client.table("proposals").select(
                "id, industry, budget, org_id"
            ).in_("status", ["step3_planning", "step4_proposal"]).execute()

            if not proposals.data:
                logger.info("No active proposals to process")
                return {
                    "success": True,
                    "processed_count": 0,
                    "success_count": 0,
                    "failure_count": 0,
                    "details": [],
                }

            # 병렬 처리 (최대 5개 동시)
            details = []
            semaphore = asyncio.Semaphore(5)

            async def process_proposal(proposal):
                async with semaphore:
                    try:
                        result = await self.collector.analyze_and_save(
                            proposal_id=UUID(proposal["id"]),
                            industry=proposal.get("industry"),
                            budget=proposal.get("budget"),
                            org_id=UUID(proposal["org_id"]) if proposal.get("org_id") else None,
                        )

                        detail = {
                            "proposal_id": proposal["id"],
                            "success": result.get("success", False),
                            "sample_size": result.get("sample_size", 0),
                            "recommended_bid": result.get("recommended_bid"),
                        }

                        if result.get("success"):
                            logger.info(
                                f"Processed proposal {proposal['id']}: "
                                f"{result.get('sample_size')} samples, "
                                f"recommended bid {result.get('recommended_bid'):,}"
                            )
                        else:
                            logger.warning(
                                f"Failed to process proposal {proposal['id']}: "
                                f"{result.get('error')}"
                            )

                        return detail
                    except Exception as e:
                        logger.error(f"Error processing proposal {proposal['id']}: {e}")
                        return {
                            "proposal_id": proposal["id"],
                            "success": False,
                            "error": str(e),
                        }

            # 모든 제안서 병렬 처리
            details = await asyncio.gather(
                *[process_proposal(p) for p in proposals.data]
            )

            success_count = sum(1 for d in details if d.get("success"))
            failure_count = len(details) - success_count

            result = {
                "success": True,
                "timestamp": datetime.utcnow().isoformat(),
                "processed_count": len(details),
                "success_count": success_count,
                "failure_count": failure_count,
                "details": details,
            }

            logger.info(
                f"Daily batch completed: {success_count}/{len(details)} successful"
            )

            return result

        except Exception as e:
            logger.error(f"Error in daily batch: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def trigger_analysis(
        self,
        proposal_id: UUID,
        industry: str,
        budget: int,
        org_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        수동 트리거: 특정 제안서의 분석 즉시 실행 (Step 4 진입 시)

        Args:
            proposal_id: 제안 ID
            industry: 산업 분류
            budget: 예정가
            org_id: 조직 ID

        Returns:
            분석 결과
        """
        try:
            logger.info(f"Manually triggering analysis for proposal {proposal_id}")

            result = await self.collector.analyze_and_save(
                proposal_id=proposal_id,
                industry=industry,
                budget=budget,
                org_id=org_id,
            )

            if result.get("success"):
                logger.info(
                    f"Manual analysis completed: {result.get('sample_size')} samples"
                )
            else:
                logger.warning(f"Manual analysis failed: {result.get('error')}")

            return result

        except Exception as e:
            logger.error(f"Error in manual trigger: {e}")
            return {
                "success": False,
                "error": str(e),
            }


# 싱글톤 인스턴스
_scheduler_instance: Optional[VaultBiddingBatchScheduler] = None


async def get_scheduler() -> VaultBiddingBatchScheduler:
    """배치 스케줄러 싱글톤 획득"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = VaultBiddingBatchScheduler()
    return _scheduler_instance


async def start_batch_scheduler():
    """배치 스케줄러 시작 (애플리케이션 시작 시 호출)"""
    scheduler = await get_scheduler()
    await scheduler.start_scheduler()


async def stop_batch_scheduler():
    """배치 스케줄러 중지 (애플리케이션 종료 시 호출)"""
    if _scheduler_instance:
        await _scheduler_instance.stop_scheduler()
