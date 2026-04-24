"""
Vault Query Router - Detects user intent and routes to appropriate handler
Uses Claude Haiku for cost-effective intent detection
Phase 1 implementation
"""

import logging
import json
from typing import List, Dict, Optional, Any
from app.models.vault_schemas import (
    VaultSection,
    QueryType,
    RoutingDecision,
    ChatMessage
)
from app.services.core.claude_client import claude_generate

logger = logging.getLogger(__name__)


class VaultQueryRouter:
    """
    Routes user queries to appropriate Vault sections
    Uses Claude Haiku for intent detection
    """

    # System prompt for intent detection
    ROUTING_PROMPT = """
    You are a query router for TENOPA Vault - a knowledge management system with 8 sections:
    
    1. completed_projects - 종료프로젝트 (closed proposals with budgets, teams, outcomes)
    2. company_internal - 회사내부자료 (company overview, org chart, team bios)
    3. credentials - 실적증명서 (certifications, licenses, awards)
    4. government_guidelines - 정부지침 (salary standards, bidding rules, government rates)
    5. competitors - 경쟁사정보 (competitor analysis, market research)
    6. success_cases - 성공사례 (past project outcomes, lessons learned)
    7. clients_db - 발주처정보 (client contact info, relationship history)
    8. research_materials - 리서치자료 (temporary research documents, market reports)
    
    Given a user query, determine:
    1. Which section(s) are relevant (0-2 sections usually)
    2. Query type (project_search, budget_estimate, team_performance, etc.)
    3. Confidence in routing (0-1)
    4. Any filters to apply (date range, team, client, keyword, etc.)
    
    Return valid JSON only:
    {
        "sections": ["section1", "section2"],  // Use lowercase with underscore
        "query_type": "query_type",
        "confidence": 0.85,
        "filters": {
            "date_from": "2024-01-01",
            "keywords": ["AI", "project"],
            "client": "client_name"
        },
        "reasoning": "Brief explanation of routing decision"
    }
    
    Guidelines:
    - If unsure, include completed_projects (most comprehensive data)
    - government_guidelines is only for salary/bidding rules/government rates
    - research_materials is only for ad-hoc uploaded documents
    - Be specific about filters (client name, date range, keywords)
    - Confidence should reflect how clear the intent is
    """

    @staticmethod
    async def route(
        query: str,
        conversation_context: Optional[List[ChatMessage]] = None
    ) -> RoutingDecision:
        """
        Route query to appropriate section(s)
        
        Args:
            query: User query
            conversation_context: Previous messages for context (optional)
        
        Returns:
            RoutingDecision with sections, query_type, confidence, filters
        """

        try:
            # Build context from conversation if provided
            context_text = ""
            if conversation_context:
                context_text = "\n\nConversation context:\n"
                for msg in conversation_context[-5:]:  # Last 5 messages
                    context_text += f"{msg.role}: {msg.content}\n"

            # Call Claude Haiku for routing
            user_message = f"""
{context_text}

Current query: {query}

Analyze this query and provide routing decision in valid JSON format.
"""

            response = await claude_generate(
                prompt=user_message,
                system_prompt=VaultQueryRouter.ROUTING_PROMPT,
                model="claude-haiku-4-5-20251001",
                max_tokens=500,
                temperature=0.3,  # Lower temperature for consistent routing
                response_format="json"
            )

            # Parse response
            response_text = response.get("text", "") or json.dumps(response)

            # Extract JSON from response
            try:
                # Try to find JSON in response
                start_idx = response_text.find("{")
                end_idx = response_text.rfind("}") + 1

                if start_idx >= 0 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    routing_json = json.loads(json_str)
                else:
                    raise ValueError("No JSON found in response")

            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse routing response: {str(e)}")
                # Fallback to completed_projects
                routing_json = {
                    "sections": ["completed_projects"],
                    "query_type": "project_search",
                    "confidence": 0.5,
                    "filters": {},
                    "reasoning": "Fallback routing"
                }

            # Convert section strings to enum
            sections = []
            for section_str in routing_json.get("sections", ["completed_projects"]):
                try:
                    sections.append(VaultSection(section_str))
                except ValueError:
                    logger.warning(f"Invalid section: {section_str}")
                    sections.append(VaultSection.COMPLETED_PROJECTS)

            # Convert query type
            try:
                query_type = QueryType(routing_json.get("query_type", "other"))
            except ValueError:
                query_type = QueryType.OTHER

            return RoutingDecision(
                sections=sections or [VaultSection.COMPLETED_PROJECTS],
                query_type=query_type,
                confidence=min(1.0, max(0.0, float(routing_json.get("confidence", 0.5)))),
                filters=routing_json.get("filters", {}),
                reasoning=routing_json.get("reasoning")
            )

        except Exception as e:
            logger.error(f"Error in query routing: {str(e)}")
            # Fallback to safe default
            return RoutingDecision(
                sections=[VaultSection.COMPLETED_PROJECTS],
                query_type=QueryType.OTHER,
                confidence=0.3,
                filters={},
                reasoning="Routing error - using fallback"
            )

    @staticmethod
    async def extract_filters(
        query: str,
        routing: RoutingDecision
    ) -> Dict[str, Any]:
        """
        Extract specific filters from query
        Useful for refining searches
        
        Examples:
        - "AI projects from 2024" → {"keywords": ["AI"], "date_from": "2024-01-01"}
        - "Samsung's projects" → {"client": "Samsung"}
        - "projects over 500만원" → {"budget_min": 5000000}
        """

        try:
            prompt = f"""
Extract specific search filters from this query:

Query: {query}

Return valid JSON with these fields (only include if mentioned):
{{
    "date_from": "YYYY-MM-DD",
    "date_to": "YYYY-MM-DD",
    "client": "client name",
    "team_member": "person name",
    "budget_min": 1000000,
    "budget_max": 5000000,
    "status": ["won", "lost"],
    "keywords": ["keyword1", "keyword2"],
    "category": "category"
}}

Only return JSON, no explanation.
"""

            response = await claude_generate(
                prompt=prompt,
                model="claude-haiku-4-5-20251001",
                max_tokens=300,
                temperature=0.2,
                response_format="json"
            )

            response_text = response.get("text", "") or json.dumps(response)

            # Extract JSON
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)

            return {}

        except Exception as e:
            logger.warning(f"Error extracting filters: {str(e)}")
            return {}

    @staticmethod
    def suggest_follow_up(
        query: str,
        routing: RoutingDecision
    ) -> List[str]:
        """
        Suggest follow-up questions for the user
        Helps guide Vault exploration
        """

        suggestions = []

        # Based on query type
        if routing.query_type == QueryType.BUDGET_ESTIMATE:
            suggestions.extend([
                "유사한 프로젝트의 실제 예산은?",
                "예산별 프로젝트 분포는?"
            ])

        elif routing.query_type == QueryType.CLIENT_HISTORY:
            suggestions.extend([
                "이 클라이언트와의 성공률은?",
                "최근 이 클라이언트의 프로젝트는?"
            ])

        elif routing.query_type == QueryType.TEAM_PERFORMANCE:
            suggestions.extend([
                "이 팀이 수행한 대형 프로젝트는?",
                "팀별 성공률 비교"
            ])

        elif routing.query_type == QueryType.COMPETITIVE_ANALYSIS:
            suggestions.extend([
                "경쟁사 대비 우리의 강점은?",
                "유사 시장에서 우리의 입찰 기록은?"
            ])

        return suggestions[:3]  # Return top 3


# Singleton instance
vault_router = VaultQueryRouter()
