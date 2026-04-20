"""
Teams Bot Service - 3 Modes Integration (Adaptive, Digest, Matching)
Phase 2 DO Phase: Day 3-4 Implementation
Design Ref: §3.4, Vault Chat Phase 2 Technical Design
"""

import aiohttp
import logging
from datetime import datetime, time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from app.models.vault_schemas import DocumentSource
from app.utils.supabase_client import SupabaseAsyncClient

logger = logging.getLogger(__name__)


class BotMode(str, Enum):
    """Teams Bot operating modes"""
    ADAPTIVE = "adaptive"      # Real-time response to mentions
    DIGEST = "digest"          # Daily KB summary
    MATCHING = "matching"      # RFP auto-recommendation


@dataclass
class TeamsBotConfig:
    """Teams Bot Configuration"""
    id: str
    team_id: str
    bot_enabled: bool
    bot_modes: List[str]
    webhook_url: str
    webhook_validated_at: Optional[str]
    digest_time: str  # "09:00"
    digest_keywords: List[str]
    digest_enabled: bool
    matching_enabled: bool
    matching_threshold: float


@dataclass
class BotMessage:
    """Bot message metadata"""
    id: str
    team_id: str
    mode: str
    query: str
    response: str
    delivery_status: str
    teams_message_id: Optional[str]
    created_at: str


class TeamsBotService:
    """
    Teams Bot Service - Manage 3 integration modes

    Modes:
    1. Adaptive: Real-time response to @Vault mentions
    2. Digest: Daily scheduled KB summary
    3. Matching: Auto-recommend similar projects on new RFP
    """

    def __init__(self, supabase_client: SupabaseAsyncClient):
        """
        Initialize Teams Bot Service

        Args:
            supabase_client: Async Supabase client for DB operations
        """
        self.supabase = supabase_client
        self.http_session: Optional[aiohttp.ClientSession] = None

    async def initialize(self) -> None:
        """
        Initialize HTTP session for Teams API communication

        Called at application startup to establish connection pool
        """
        if not self.http_session:
            # Create session with connection pooling and timeout defaults
            timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=20)
            self.http_session = aiohttp.ClientSession(timeout=timeout)
            logger.info("Teams Bot Service initialized")

    async def close(self) -> None:
        """
        Clean up HTTP session

        Called at application shutdown
        """
        if self.http_session:
            await self.http_session.close()
            logger.info("Teams Bot Service closed")

    # ── Mode 1: Adaptive Bot (Real-time response) ──

    async def handle_adaptive_query(
        self,
        team_id: str,
        user_id: str,
        query: str,
        channel_id: str,
        response: str,
        sources: List[DocumentSource],
    ) -> bool:
        """
        Handle adaptive mode: Real-time response to @Vault mentions

        Flow:
        1. Validate team/user
        2. Get webhook URL from config
        3. Build Teams Adaptive Card
        4. Post to Teams via webhook
        5. Log delivery status

        Args:
            team_id: Team UUID
            user_id: User UUID
            query: User question/mention
            channel_id: Teams channel ID
            response: AI response text
            sources: Referenced documents

        Returns:
            bool: Success of Teams message delivery
        """
        try:
            # 1. Load team config (get webhook_url)
            config = await self._get_team_config(team_id)
            if not config:
                logger.error(f"No Teams config for team {team_id}")
                return False

            if not config.bot_enabled or BotMode.ADAPTIVE not in config.bot_modes:
                logger.debug(f"Adaptive mode disabled for team {team_id}")
                return False

            # 2. Build Teams message (Adaptive Card format)
            message = self._build_adaptive_card(query, response, sources)

            # 3. Send via webhook with retry
            teams_message_id = await self._send_webhook_with_retry(
                webhook_url=config.webhook_url,
                message=message,
                max_retries=3
            )

            if not teams_message_id:
                raise Exception("Webhook delivery failed after retries")

            # 4. Log success
            await self._log_message(
                team_id=team_id,
                user_id=user_id,
                mode=BotMode.ADAPTIVE,
                query=query,
                response=response,
                delivery_status="sent",
                teams_message_id=teams_message_id
            )

            return True

        except Exception as e:
            logger.error(f"Adaptive mode error: {e}", exc_info=True)
            # Log failure
            await self._log_message(
                team_id=team_id,
                user_id=user_id,
                mode=BotMode.ADAPTIVE,
                query=query,
                response=response,
                delivery_status="failed",
                teams_message_id=None,
                delivery_error=str(e)
            )
            return False

    def _build_adaptive_card(
        self,
        query: str,
        response: str,
        sources: List[DocumentSource]
    ) -> Dict[str, Any]:
        """
        Build Teams Adaptive Card for response

        Format:
        - Title: "Vault AI Response"
        - Body: Response text (max 1000 chars)
        - Facts: Query, Sources count

        Args:
            query: User question (truncated to 100 chars)
            response: AI response
            sources: Referenced documents

        Returns:
            dict: Teams Adaptive Card JSON
        """
        return {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": "Vault AI Response",
            "themeColor": "0078D4",
            "sections": [
                {
                    "activityTitle": "💡 Vault AI Response",
                    "activitySubtitle": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "text": response[:2000],  # Truncate to Teams limit
                    "facts": [
                        {
                            "name": "🔍 Query",
                            "value": query[:100] + ("..." if len(query) > 100 else "")
                        },
                        {
                            "name": "📄 Sources",
                            "value": f"{len(sources)} document(s)"
                        },
                        {
                            "name": "⏱️ Timestamp",
                            "value": datetime.now().isoformat()
                        }
                    ]
                }
            ]
        }

    # ── Mode 2: Digest Bot (Scheduled summary) ──

    async def generate_and_send_digest(
        self,
        team_id: str,
        config: TeamsBotConfig
    ) -> bool:
        """
        Generate and send daily digest for a team

        Process:
        1. Parse digest_keywords (G2B:*, competitor:*, tech:*)
        2. Search for results per keyword
        3. Build digest markdown
        4. Send via Teams webhook
        5. Log delivery

        Args:
            team_id: Team UUID
            config: TeamsBotConfig with digest settings

        Returns:
            bool: Success of digest delivery
        """
        if not config.digest_enabled or BotMode.DIGEST not in config.bot_modes:
            return False

        try:
            # 1. Process digest keywords
            digest_sections = await self._process_digest_keywords(
                keywords=config.digest_keywords
            )

            if not digest_sections:
                logger.debug(f"No digest content for team {team_id}")
                return False

            # 2. Build digest message
            digest_text = self._build_digest_text(digest_sections)

            # 3. Send via webhook
            teams_message_id = await self._send_webhook_with_retry(
                webhook_url=config.webhook_url,
                message={
                    "@type": "MessageCard",
                    "@context": "https://schema.org/extensions",
                    "summary": "Vault Daily Digest",
                    "themeColor": "2E7D32",
                    "sections": [
                        {
                            "activityTitle": "📊 오늘의 Vault 다이제스트",
                            "activitySubtitle": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "text": digest_text
                        }
                    ]
                },
                max_retries=3
            )

            if not teams_message_id:
                raise Exception("Digest webhook delivery failed")

            # 4. Log digest
            await self._log_message(
                team_id=team_id,
                mode=BotMode.DIGEST,
                query=f"Daily digest: {', '.join(config.digest_keywords[:5])}",
                response=digest_text,
                delivery_status="sent",
                teams_message_id=teams_message_id
            )

            return True

        except Exception as e:
            logger.error(f"Digest generation error for team {team_id}: {e}", exc_info=True)
            return False

    async def _process_digest_keywords(
        self,
        keywords: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Process digest keywords and search for results

        Keyword formats:
        - "G2B:environment" → Search G2B RFPs by keyword
        - "competitor:OOO" → Search competitor bid info
        - "tech:AI" → Search technology trends

        Args:
            keywords: List of digest keywords

        Returns:
            List of sections with results
        """
        sections = []

        for keyword in keywords:
            try:
                if keyword.startswith("G2B:"):
                    topic = keyword.split(":", 1)[1]
                    results = await self._search_g2b_keyword(topic)
                    if results:
                        sections.append({
                            "title": f"🏛️ G2B 신규공고 ({topic})",
                            "results": results[:5]
                        })

                elif keyword.startswith("competitor:"):
                    competitor = keyword.split(":", 1)[1]
                    results = await self._search_competitor_bids(competitor)
                    if results:
                        sections.append({
                            "title": f"🎯 경쟁사 입찰 ({competitor})",
                            "results": results[:5]
                        })

                elif keyword.startswith("tech:"):
                    tech = keyword.split(":", 1)[1]
                    results = await self._search_tech_trends(tech)
                    if results:
                        sections.append({
                            "title": f"🔬 기술 트렌드 ({tech})",
                            "results": results[:5]
                        })

            except Exception as e:
                logger.warning(f"Error processing keyword '{keyword}': {e}")
                continue

        return sections

    async def _search_g2b_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Search G2B RFPs by keyword

        Stub: Implementation depends on G2B service integration

        Args:
            keyword: Search keyword

        Returns:
            List of G2B RFP results with score
        """
        # TODO: Integrate with G2B service (g2b_service.py)
        # - Search for announcements containing keyword
        # - Filter by date (today)
        # - Calculate relevance score
        # - Return top 5 results
        return []

    async def _search_competitor_bids(self, competitor: str) -> List[Dict[str, Any]]:
        """
        Search competitor bid information

        Stub: Implementation depends on bid tracking

        Args:
            competitor: Competitor name

        Returns:
            List of competitor bid results
        """
        # TODO: Query vault_documents or bid_tracking
        # - Filter by competitor name
        # - Order by date DESC
        # - Return recent 5 bids
        return []

    async def _search_tech_trends(self, tech: str) -> List[Dict[str, Any]]:
        """
        Search technology trends

        Stub: Implementation depends on document indexing

        Args:
            tech: Technology/domain keyword

        Returns:
            List of technology trend results
        """
        # TODO: Vector search in vault_documents
        # - Embed keyword
        # - Find semantically similar documents
        # - Filter by date (last 30 days)
        # - Return top 5 results
        return []

    @staticmethod
    def _build_digest_text(sections: List[Dict[str, Any]]) -> str:
        """
        Build digest markdown from sections

        Format:
        ### Section Title
        - Result 1 (score: X%)
        - Result 2 (score: Y%)
        ...

        Args:
            sections: List of digest sections

        Returns:
            Markdown formatted digest text
        """
        lines = []

        for section in sections:
            lines.append(f"\n### {section['title']}")
            for result in section.get('results', [])[:5]:
                title = result.get('title', 'N/A')
                score = result.get('score', result.get('relevance', 'N/A'))
                lines.append(f"- {title} (점수: {score}%)")

        return "\n".join(lines) if lines else "오늘의 관련 항목이 없습니다."

    # ── Mode 3: RFP Matching (Auto-recommendation) ──

    async def recommend_similar_projects(
        self,
        rfp_id: str,
        rfp_title: str,
        rfp_content: str
    ) -> bool:
        """
        Recommend similar projects to relevant teams on new RFP

        Flow:
        1. Embed RFP content
        2. Search similar completed projects (vector search, threshold > 0.75)
        3. Group by team
        4. Send recommendation to each team

        Args:
            rfp_id: RFP UUID
            rfp_title: RFP title
            rfp_content: RFP content for embedding

        Returns:
            bool: Success of at least one recommendation delivery
        """
        if not self.http_session:
            logger.error("HTTP session not initialized")
            return False

        try:
            # 1. Vector embed RFP content
            embedding = await self._embed_text(rfp_content[:2000])
            if not embedding:
                logger.warning("Failed to embed RFP content")
                return False

            # 2. Search similar projects
            similar_projects = await self._vector_search_projects(
                embedding=embedding,
                threshold=0.75
            )

            if not similar_projects:
                logger.debug(f"No similar projects found for RFP {rfp_id}")
                return False

            # 3. Group by team and send recommendations
            success_count = 0
            for project in similar_projects:
                team_id = project.get("team_id")
                if not team_id:
                    continue

                try:
                    config = await self._get_team_config(team_id)
                    if not config or not config.matching_enabled:
                        continue

                    if BotMode.MATCHING not in config.bot_modes:
                        continue

                    # Build recommendation message
                    message = {
                        "@type": "MessageCard",
                        "@context": "https://schema.org/extensions",
                        "summary": "RFP Auto-Recommendation",
                        "themeColor": "FF9800",
                        "sections": [
                            {
                                "activityTitle": "🎯 신규 RFP 자동 매칭",
                                "activitySubtitle": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "text": (
                                    f"**RFP**: {rfp_title}\n\n"
                                    f"**유사 경험**: {project.get('title', 'N/A')}\n\n"
                                    f"**낙찰 가능성**: {project.get('matching_score', 0)}%"
                                ),
                                "facts": [
                                    {
                                        "name": "📅 프로젝트 완료",
                                        "value": project.get('completed_date', 'N/A')
                                    },
                                    {
                                        "name": "💰 프로젝트 규모",
                                        "value": f"₩{project.get('budget', 'N/A')}"
                                    }
                                ]
                            }
                        ]
                    }

                    # Send to team
                    result = await self._send_webhook_with_retry(
                        webhook_url=config.webhook_url,
                        message=message,
                        max_retries=2
                    )

                    if result:
                        success_count += 1

                except Exception as e:
                    logger.warning(f"Failed to send recommendation to team {team_id}: {e}")

            logger.info(f"RFP recommendations sent to {success_count}/{len(similar_projects)} teams")
            return success_count > 0

        except Exception as e:
            logger.error(f"RFP matching error: {e}", exc_info=True)
            return False

    async def _embed_text(self, text: str) -> Optional[List[float]]:
        """
        Embed text using OpenAI API

        Stub: Integration with embedding service

        Args:
            text: Text to embed

        Returns:
            Vector embedding or None
        """
        # TODO: Call OpenAI embedding API (text-embedding-3-large)
        # - Use same embedding model as VaultEmbeddingService
        # - Return 1536-dim vector
        return None

    async def _vector_search_projects(
        self,
        embedding: List[float],
        threshold: float = 0.75
    ) -> List[Dict[str, Any]]:
        """
        Search similar projects by vector embedding

        Stub: Integration with vector search

        Args:
            embedding: RFP embedding vector
            threshold: Similarity threshold (0.75)

        Returns:
            List of similar projects with matching_score
        """
        # TODO: Vector similarity search in vault_documents
        # - Filter by document_type = 'completed_project'
        # - Calculate cosine similarity
        # - Filter by similarity > threshold
        # - Order by similarity DESC
        # - Return top 10 with team_id, title, matching_score
        return []

    # ── Webhook Management ──

    async def _send_webhook_with_retry(
        self,
        webhook_url: str,
        message: Dict[str, Any],
        max_retries: int = 3
    ) -> Optional[str]:
        """
        Send message via Teams webhook with exponential backoff retry

        Retry strategy:
        - Wait: 1s, 2s, 4s (exponential backoff)
        - Retry on: connection errors, 5xx, timeout
        - No retry on: 4xx (except 429)

        Args:
            webhook_url: Teams webhook URL
            message: Message payload
            max_retries: Max retry attempts

        Returns:
            str: Teams message ID on success, None on failure
        """
        if not self.http_session:
            logger.error("HTTP session not initialized")
            return None

        last_error = None
        for attempt in range(max_retries):
            try:
                async with self.http_session.post(
                    webhook_url,
                    json=message,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        # Teams webhook returns 1 on success
                        text = await resp.text()
                        logger.debug(f"Webhook sent successfully: {resp.status}")
                        return text[:50]  # Use first 50 chars as ID

                    elif resp.status == 429:  # Rate limit
                        # Exponential backoff
                        wait_time = 2 ** attempt
                        logger.warning(f"Rate limited. Waiting {wait_time}s before retry...")
                        import asyncio
                        await asyncio.sleep(wait_time)
                        continue

                    elif 500 <= resp.status < 600:  # Server error
                        raise Exception(f"Server error {resp.status}")

                    else:  # 4xx (except 429)
                        text = await resp.text()
                        logger.error(f"Webhook error {resp.status}: {text}")
                        return None

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                    import asyncio
                    await asyncio.sleep(wait_time)
                continue

        logger.error(f"Webhook delivery failed after {max_retries} attempts: {last_error}")
        return None

    async def validate_webhook_url(self, webhook_url: str) -> bool:
        """
        Validate Teams webhook URL

        Checks:
        1. URL format (HTTPS, outlook.webhook.office.com)
        2. Webhook is live (HEAD request)

        Args:
            webhook_url: URL to validate

        Returns:
            bool: True if valid and live
        """
        # Check URL format
        if not webhook_url.startswith("https://"):
            logger.error("Webhook URL must be HTTPS")
            return False

        if "outlook.webhook.office.com" not in webhook_url:
            logger.error("Invalid Teams webhook domain")
            return False

        # Check webhook is live with HEAD request
        if not self.http_session:
            await self.initialize()

        try:
            async with self.http_session.head(
                webhook_url,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                is_valid = resp.status != 404
                logger.debug(f"Webhook validation: {resp.status} ({'valid' if is_valid else 'invalid'})")
                return is_valid

        except Exception as e:
            logger.error(f"Webhook validation failed: {e}")
            return False

    # ── Database Operations ──

    async def _get_team_config(self, team_id: str) -> Optional[TeamsBotConfig]:
        """
        Load Teams Bot config from DB

        Args:
            team_id: Team UUID

        Returns:
            TeamsBotConfig or None if not found
        """
        try:
            result = await self.supabase.table("teams_bot_config") \
                .select("*") \
                .eq("team_id", team_id) \
                .single() \
                .execute()

            if result.data:
                return TeamsBotConfig(**result.data)
            return None

        except Exception as e:
            logger.error(f"Failed to load config for team {team_id}: {e}")
            return None

    async def _log_message(
        self,
        team_id: str,
        mode: str,
        query: str,
        response: str,
        delivery_status: str,
        teams_message_id: Optional[str] = None,
        user_id: Optional[str] = None,
        delivery_error: Optional[str] = None
    ) -> None:
        """
        Log Teams bot message to DB

        Args:
            team_id: Team UUID
            mode: Bot mode (adaptive, digest, matching)
            query: User query
            response: Bot response
            delivery_status: sent, failed, pending
            teams_message_id: Teams message ID (if sent)
            user_id: User UUID (optional)
            delivery_error: Error message (if failed)
        """
        try:
            await self.supabase.table("teams_bot_messages").insert({
                "team_id": team_id,
                "user_id": user_id,
                "mode": mode,
                "query": query,
                "response": response,
                "delivery_status": delivery_status,
                "teams_message_id": teams_message_id,
                "delivery_error": delivery_error,
                "created_at": datetime.utcnow().isoformat()
            }).execute()

        except Exception as e:
            logger.error(f"Failed to log Teams message: {e}")
