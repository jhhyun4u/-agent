"""워크플로우 시작/종료 시간 및 토큰 비용 추적.

제안작업 시작 시점부터 종료 시점까지 다음을 추적:
- workflow_started_at: 워크플로우 시작 시간
- workflow_completed_at: 워크플로우 완료 시간
- elapsed_seconds: 소요 시간 (초)
- total_token_usage: 총 토큰 사용량
- total_token_cost: 총 토큰 비용 (USD)

참여자 정보도 함께 저장:
- proposal_members 테이블에 선택된 멤버들 기록
"""

from datetime import datetime, timezone
import logging
from app.utils.supabase_client import get_async_client
from app.services.token_pricing import TokenCostTracker, calculate_cost

logger = logging.getLogger(__name__)


class WorkflowTimer:
    """워크플로우 실행 시간 및 비용 추적."""

    @staticmethod
    async def start_workflow(proposal_id: str, participants: list[str]) -> dict:
        """워크플로우 시작.

        Args:
            proposal_id: 제안서 ID
            participants: 참여자 user_id 리스트

        Returns:
            {
                "proposal_id": str,
                "started_at": datetime,
                "members_added": int
            }
        """
        try:
            client = await get_async_client()
            now = datetime.now(timezone.utc).isoformat()

            # 1. proposals 테이블 업데이트
            await client.table("proposals").update({
                "workflow_started_at": now,
                "workflow_completed_at": None,
                "elapsed_seconds": 0,
                "total_token_usage": 0,
                "total_token_cost": 0.0
            }).eq("id", proposal_id).execute()

            # 2. proposal_members에 참여자 추가
            members_data = [
                {
                    "proposal_id": proposal_id,
                    "user_id": user_id,
                    "role": "contributor"
                }
                for user_id in participants
            ]

            if members_data:
                result = await client.table("proposal_members").insert(members_data).execute()
                members_added = len(result.data) if result.data else 0
            else:
                members_added = 0

            logger.info(
                f"Workflow started for proposal {proposal_id} "
                f"with {members_added} participants"
            )

            return {
                "proposal_id": proposal_id,
                "started_at": now,
                "members_added": members_added
            }

        except Exception as e:
            logger.error(f"Error starting workflow for {proposal_id}: {str(e)}")
            raise

    @staticmethod
    async def end_workflow(proposal_id: str) -> dict:
        """워크플로우 종료.

        Args:
            proposal_id: 제안서 ID

        Returns:
            {
                "proposal_id": str,
                "elapsed_seconds": int,
                "elapsed_formatted": str (e.g., "2h 30m")
            }
        """
        try:
            client = await get_async_client()

            # 1. 기존 데이터 조회
            result = await client.table("proposals").select(
                "workflow_started_at, workflow_completed_at"
            ).eq("id", proposal_id).single().execute()

            proposal = result.data
            started_at = datetime.fromisoformat(proposal["workflow_started_at"])
            now = datetime.now(timezone.utc)

            # 2. 경과 시간 계산
            elapsed_seconds = int((now - started_at).total_seconds())

            # 3. 업데이트
            now_iso = now.isoformat()
            await client.table("proposals").update({
                "workflow_completed_at": now_iso,
                "elapsed_seconds": elapsed_seconds
            }).eq("id", proposal_id).execute()

            elapsed_formatted = TokenCostTracker.format_elapsed_time(elapsed_seconds)

            logger.info(
                f"Workflow ended for proposal {proposal_id}. "
                f"Elapsed: {elapsed_formatted}"
            )

            return {
                "proposal_id": proposal_id,
                "elapsed_seconds": elapsed_seconds,
                "elapsed_formatted": elapsed_formatted
            }

        except Exception as e:
            logger.error(f"Error ending workflow for {proposal_id}: {str(e)}")
            raise

    @staticmethod
    async def track_token_usage(
        proposal_id: str,
        input_tokens: int,
        output_tokens: int,
        model: str = "claude-sonnet-4-5-20250929"
    ) -> dict:
        """토큰 사용량 실시간 추적.

        Args:
            proposal_id: 제안서 ID
            input_tokens: 입력 토큰 수
            output_tokens: 출력 토큰 수
            model: 모델 이름

        Returns:
            {
                "proposal_id": str,
                "total_tokens": int,
                "total_cost_usd": float,
                "total_cost_formatted": str
            }
        """
        try:
            client = await get_async_client()

            # 1. 기존 토큰 사용량 조회
            result = await client.table("proposals").select(
                "total_token_usage, total_token_cost"
            ).eq("id", proposal_id).single().execute()

            proposal = result.data
            prev_total_tokens = proposal.get("total_token_usage", 0) or 0
            prev_total_cost = proposal.get("total_token_cost", 0.0) or 0.0

            # 2. 현재 비용 계산
            current_cost = calculate_cost(input_tokens, output_tokens, 0, 0, model)

            # 3. 누적 값 계산
            new_total_tokens = prev_total_tokens + input_tokens + output_tokens
            new_total_cost = prev_total_cost + current_cost

            # 4. DB 업데이트
            await client.table("proposals").update({
                "total_token_usage": new_total_tokens,
                "total_token_cost": round(new_total_cost, 2)
            }).eq("id", proposal_id).execute()

            cost_formatted = TokenCostTracker.format_cost(new_total_cost)

            logger.debug(
                f"Token usage tracked for proposal {proposal_id}: "
                f"+{input_tokens + output_tokens} tokens (${current_cost:.4f}), "
                f"Total: {new_total_tokens} tokens ({cost_formatted})"
            )

            return {
                "proposal_id": proposal_id,
                "total_tokens": new_total_tokens,
                "total_cost_usd": new_total_cost,
                "total_cost_formatted": cost_formatted
            }

        except Exception as e:
            logger.error(f"Error tracking token usage for {proposal_id}: {str(e)}")
            raise

    @staticmethod
    async def get_workflow_stats(proposal_id: str) -> dict:
        """워크플로우 통계 조회.

        Args:
            proposal_id: 제안서 ID

        Returns:
            {
                "proposal_id": str,
                "elapsed_seconds": int,
                "elapsed_formatted": str,
                "total_tokens": int,
                "total_cost_usd": float,
                "total_cost_formatted": str,
                "members": list
            }
        """
        try:
            client = await get_async_client()

            # 1. 제안서 통계
            proposal_result = await client.table("proposals").select(
                "elapsed_seconds, total_token_usage, total_token_cost"
            ).eq("id", proposal_id).single().execute()

            proposal = proposal_result.data

            elapsed_seconds = proposal.get("elapsed_seconds", 0) or 0
            total_tokens = proposal.get("total_token_usage", 0) or 0
            total_cost = proposal.get("total_token_cost", 0.0) or 0.0

            # 2. 참여자 목록
            members_result = await client.table("proposal_members").select(
                "user_id, role, joined_at, users(name, email)"
            ).eq("proposal_id", proposal_id).execute()

            members = members_result.data or []

            return {
                "proposal_id": proposal_id,
                "elapsed_seconds": elapsed_seconds,
                "elapsed_formatted": TokenCostTracker.format_elapsed_time(elapsed_seconds),
                "total_tokens": total_tokens,
                "total_cost_usd": total_cost,
                "total_cost_formatted": TokenCostTracker.format_cost(total_cost),
                "members": members
            }

        except Exception as e:
            logger.error(f"Error getting workflow stats for {proposal_id}: {str(e)}")
            raise
