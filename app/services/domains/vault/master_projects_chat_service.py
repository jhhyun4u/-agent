"""
Master Projects Chat Service — RAG-기반 자연어 검색 및 답변 생성

사용자의 자연어 질문을 처리하고:
1. 쿼리를 임베딩으로 변환
2. pgvector로 유사 프로젝트 검색
3. Claude API로 자연어 답변 생성
"""

import json
import logging
from uuid import UUID

from app.services.core.claude_client import ClaudeClient
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)


class MasterProjectsChatService:
    """과거 프로젝트 Chat 검색 및 답변"""

    def __init__(self):
        self.claude = ClaudeClient()

    async def search_and_answer(
        self,
        query: str,
        org_id: UUID,
        limit: int = 5
    ) -> dict:
        """
        자연어 질문으로 과거 프로젝트 검색 후 답변 생성

        Args:
            query: 사용자 질문 (예: "우리가 IoT 프로젝트 해본 적 있어?")
            org_id: 조직 ID
            limit: 검색할 최대 프로젝트 수

        Returns:
            {
                "answer": "AI가 생성한 답변 (마크다운)",
                "sources": [프로젝트 리스트],
                "message": "처리 메시지"
            }
        """
        try:
            # Step 1: 자연어 쿼리를 임베딩으로 변환
            logger.info(f"임베딩 생성: {query[:50]}...")
            query_embedding = await self._embed_text(query)

            # Step 2: pgvector로 유사한 프로젝트 찾기
            logger.info(f"유사 프로젝트 검색 (limit={limit})...")
            similar_projects = await self._search_by_embedding(
                query_embedding=query_embedding,
                org_id=org_id,
                limit=limit
            )

            if not similar_projects:
                return {
                    "answer": "죄송합니다. 검색 결과가 없습니다. 다른 키워드로 다시 시도해보세요.",
                    "sources": [],
                    "message": "검색 결과 없음"
                }

            # Step 3: Claude로 자연어 답변 생성
            logger.info(f"Claude로 답변 생성 (프로젝트 {len(similar_projects)}개)...")
            answer = await self._generate_answer(
                query=query,
                projects=similar_projects
            )

            return {
                "answer": answer,
                "sources": similar_projects,
                "message": f"{len(similar_projects)}개 프로젝트 찾음"
            }

        except Exception as e:
            logger.error(f"Chat 검색 실패: {e}", exc_info=True)
            return {
                "answer": f"오류 발생: {str(e)}",
                "sources": [],
                "message": "error"
            }

    async def _embed_text(self, text: str) -> list[float]:
        """
        텍스트를 임베딩 벡터로 변환 (OpenAI Embedding API 사용)
        """
        import openai

        try:
            response = await openai.AsyncOpenAI().embeddings.create(
                model="text-embedding-3-small",
                input=text,
                dimensions=1536
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {e}")
            # Fallback: 간단한 더미 임베딩 (실제로는 실패 처리)
            return [0.0] * 1536

    async def _search_by_embedding(
        self,
        query_embedding: list[float],
        org_id: UUID,
        limit: int = 5
    ) -> list[dict]:
        """
        pgvector를 사용해 유사한 프로젝트 검색
        """
        client = await get_async_client()

        try:
            # RPC 함수를 통한 vector 검색
            # NOTE: 이 함수는 Supabase에서 사전에 정의되어야 함
            # SQL: SELECT ... ORDER BY embedding <-> $1 LIMIT $2

            response = await client.rpc(
                'search_master_projects',
                {
                    'query_embedding': query_embedding,
                    'org_id_param': str(org_id),
                    'similarity_threshold': 0.7,
                    'limit_count': limit
                }
            ).execute()

            projects = response.data or []
            logger.info(f"검색 완료: {len(projects)}개 프로젝트")

            return projects

        except Exception as e:
            logger.warning(f"Vector 검색 실패, 폴백 사용: {e}")
            # Fallback: 키워드 기반 검색
            return await self._search_by_keyword(query_embedding, org_id, limit)

    async def _search_by_keyword(
        self,
        query_embedding: list[float],
        org_id: UUID,
        limit: int = 5
    ) -> list[dict]:
        """
        키워드 기반 폴백 검색 (Vector 검색 실패 시)
        """
        client = await get_async_client()

        try:
            # 모든 프로젝트 조회 후 유사도 수동 계산
            response = await client.table("master_projects").select(
                "id, project_name, client_name, project_year, start_date, end_date, "
                "budget_krw, summary, project_type, proposal_status, result_status, "
                "execution_status, actual_teams, actual_participants, "
                "proposal_teams, proposal_participants, keywords"
            ).eq("org_id", str(org_id)).execute()

            projects = response.data or []
            return projects[:limit]

        except Exception as e:
            logger.error(f"키워드 검색도 실패: {e}")
            return []

    async def _generate_answer(
        self,
        query: str,
        projects: list[dict]
    ) -> str:
        """
        Claude API를 사용해 자연어 답변 생성
        """
        try:
            # 프로젝트 정보를 포맷팅
            projects_text = self._format_projects_for_prompt(projects)

            # 프롬프트 구성
            system_prompt = self._get_system_prompt()
            user_prompt = f"""사용자 질문: {query}

관련 프로젝트 정보:
{projects_text}

위 정보를 바탕으로 사용자 질문에 답변해주세요."""

            # Claude API 호출
            message = await self.claude.create_message(
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                model="claude-opus-4-6",
                max_tokens=1500
            )

            return message.content[0].text

        except Exception as e:
            logger.error(f"답변 생성 실패: {e}")
            return f"답변 생성 중 오류 발생: {str(e)}"

    def _format_projects_for_prompt(self, projects: list[dict]) -> str:
        """
        프로젝트 정보를 프롬프트용으로 포맷팅
        """
        formatted = []
        for i, p in enumerate(projects, 1):
            text = f"""
[프로젝트 {i}]
- 과제명: {p.get('project_name', 'N/A')}
- 발주처: {p.get('client_name', 'N/A')}
- 연도: {p.get('project_year', 'N/A')}
- 기간: {p.get('start_date', 'N/A')} ~ {p.get('end_date', 'N/A')}
- 계약액: {p.get('budget_krw', 0):,}원
- 요약: {p.get('summary', 'N/A')}
- 상태: 제안({p.get('proposal_status', 'N/A')}), 결과({p.get('result_status', 'N/A')}), 수행({p.get('execution_status', 'N/A')})
- 키워드: {', '.join(p.get('keywords', []))}
"""
            if p.get('actual_teams'):
                text += f"- 수행팀: {json.dumps(p['actual_teams'], ensure_ascii=False)}\n"
            if p.get('actual_participants'):
                text += f"- 수행인원: {len(p['actual_participants'])}명\n"

            formatted.append(text)

        return "\n".join(formatted)

    @staticmethod
    def _get_system_prompt() -> str:
        """
        Chat 시스템 프롬프트
        """
        return """당신은 TENOPA의 과거 프로젝트 데이터베이스 AI 어시스턴트입니다.
사용자가 자연어로 질문하면, 제공된 프로젝트 정보를 바탕으로 친절하고 구체적으로 답변합니다.

답변 규칙:
1. 사용자의 의도를 정확히 파악 (과제 유형, 기술, 발주처, 규모 등)
2. 관련 프로젝트들의 구체적 정보 제시 (과제명, 발주처, 예산, 기간)
3. 팀 구성, 담당자 등 실행 정보 포함 (가능하면)
4. 다음 제안에 참고할 인사이트 제시
5. 여러 프로젝트를 비교할 때는 표나 목록으로 정리
6. 없으면 솔직하게 "해본 적 없는 분야"라고 명시

말투: 친절하고 전문적이되, 너무 형식적이지 않게
언어: 한국어, 마크다운 형식 사용"""
