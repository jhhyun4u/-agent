"""
Vault Chat Search Service — 자연어 기반 Vault 데이터 검색
Chat 인터페이스를 통한 의도 인식, 검색, 결과 포맷팅
"""

from datetime import datetime
from uuid import UUID
from typing import Optional, List, Dict, Any
import logging
import re

from app.utils.supabase_client import supabase

logger = logging.getLogger(__name__)


class VaultChatSearch:
    """자연어 기반 Vault 데이터 검색 및 의도 분석"""

    # ============================================
    # Intent Recognition
    # ============================================

    @staticmethod
    def recognize_intent(query: str, org_id: UUID) -> Dict[str, Any]:
        """
        자연어 질문을 분석하여 의도를 인식

        패턴 분류:
        - expertise_query: "제안서 작성 전문가는?"
        - client_query: "발주처 정보", "OOO와의 거래 현황"
        - project_query: "유사 프로젝트", "낙찰 가능성"
        - personnel_query: "가용 인력", "팀 구성"
        - bidding_query: "입찰 전략", "가격 추천"

        Args:
            query: 사용자 자연어 질문
            org_id: Organization ID

        Returns:
            Intent analysis with recognized keywords and search parameters
        """
        query_lower = query.lower()

        result = {
            "original_query": query,
            "intent": "unknown",
            "confidence": 0.0,
            "keywords": [],
            "search_params": {},
            "recommended_method": None
        }

        # Expertise queries
        if any(word in query_lower for word in ["전문가", "역량", "기술", "스킬", "능력"]):
            result["intent"] = "expertise_search"
            result["confidence"] = 0.8
            result["keywords"] = [w for w in query_lower.split() if w in ["전문가", "역량", "기술", "스킬"]]
            # Extract skill name
            for skill in ["제안서 작성", "기술평가", "마케팅", "성능분석"]:
                if skill in query_lower:
                    result["search_params"]["skill"] = skill
            result["recommended_method"] = "search_personnel_by_expertise"

        # Client queries
        elif any(word in query_lower for word in ["발주처", "고객", "클라이언트", "거래처", "의뢰처"]):
            result["intent"] = "client_search"
            result["confidence"] = 0.85
            result["keywords"] = ["발주처", "고객", "거래처"]
            # Extract client name
            client_match = re.search(r'([가-힣\w]+)\s*(발주처|고객|거래처)', query)
            if client_match:
                result["search_params"]["client_name"] = client_match.group(1)
            result["recommended_method"] = "search_vault_clients"

        # Personnel/Availability queries
        elif any(word in query_lower for word in ["인력", "팀원", "담당자", "가용", "현황"]):
            result["intent"] = "personnel_search"
            result["confidence"] = 0.8
            result["keywords"] = ["인력", "팀원", "담당자"]
            if "가용" in query_lower:
                result["search_params"]["available"] = True
            result["recommended_method"] = "search_available_personnel"

        # Project/Bidding queries
        elif any(word in query_lower for word in ["입찰", "낙찰", "가격", "비용", "경쟁", "프로젝트"]):
            result["intent"] = "bidding_search"
            result["confidence"] = 0.85
            result["keywords"] = ["입찰", "낙찰", "가격", "경쟁"]
            if "가격" in query_lower or "비용" in query_lower:
                result["search_params"]["search_type"] = "pricing"
            elif "경쟁" in query_lower:
                result["search_params"]["search_type"] = "competitiveness"
            result["recommended_method"] = "search_bidding_analysis"

        # Performance/Track record queries
        elif any(word in query_lower for word in ["성과", "낙찰률", "실적", "경험", "이력"]):
            result["intent"] = "performance_search"
            result["confidence"] = 0.8
            result["keywords"] = ["성과", "낙찰률", "실적"]
            result["recommended_method"] = "search_personnel_performance"

        # Credential/Evidence queries
        elif any(word in query_lower for word in ["증명", "증빙", "서류", "인증", "자격", "실적"]):
            result["intent"] = "credential_search"
            result["confidence"] = 0.75
            result["keywords"] = ["증명", "증빙", "서류"]
            result["recommended_method"] = "search_credentials"

        return result

    # ============================================
    # Search Methods
    # ============================================

    @staticmethod
    async def search_personnel_by_expertise(
        org_id: UUID,
        skill: Optional[str] = None,
        proficiency_level: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        역량별 인력 검색

        Args:
            org_id: Organization ID
            skill: 기술명 (e.g., "제안서 작성")
            proficiency_level: 숙련도 (beginner, intermediate, advanced, expert)
            limit: 결과 수 제한

        Returns:
            List of personnel with matching expertise
        """
        try:
            query = supabase.table("vault_personnel").select(
                "id, name, email, role, department, primary_expertise, skills, "
                "win_rate, total_proposals, is_active"
            ).eq("org_id", str(org_id)).eq("is_active", True).eq("employment_status", "employed")

            response = query.order("win_rate", desc=True).limit(limit).execute()
            personnel = response.data or []

            # Filter by skill if specified
            if skill:
                personnel = [
                    p for p in personnel
                    if any(
                        s.get("skill", "").lower() == skill.lower()
                        for s in p.get("skills", [])
                    )
                ]

            # Filter by proficiency if specified
            if proficiency_level:
                personnel = [
                    p for p in personnel
                    if any(
                        s.get("proficiency", "").lower() == proficiency_level.lower()
                        for s in p.get("skills", [])
                    )
                ]

            return personnel

        except Exception as e:
            logger.error(f"Failed to search personnel by expertise: {str(e)}")
            raise

    @staticmethod
    async def search_vault_clients(
        org_id: UUID,
        client_name: Optional[str] = None,
        min_win_rate: float = 0.0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        발주처 검색

        Args:
            org_id: Organization ID
            client_name: 발주처명 (부분 일치)
            min_win_rate: 최소 낙찰률
            limit: 결과 수 제한

        Returns:
            List of matching clients
        """
        try:
            query = supabase.table("vault_clients").select(
                "id, name, win_rate, total_bid_count, avg_bid_amount, "
                "last_bid_date, lessons_learned, relationship_notes, department"
            ).eq("org_id", str(org_id)).eq("deleted_at", None)

            if client_name:
                query = query.filter("name", "ilike", f"%{client_name}%")

            response = query.order("win_rate", desc=True).limit(limit).execute()

            clients = response.data or []

            # Filter by min win rate
            if min_win_rate > 0:
                clients = [
                    c for c in clients
                    if float(c.get("win_rate", 0)) >= min_win_rate
                ]

            return clients

        except Exception as e:
            logger.error(f"Failed to search clients: {str(e)}")
            raise

    @staticmethod
    async def search_available_personnel(
        org_id: UUID,
        skill: Optional[str] = None,
        max_utilization: float = 80.0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        가용 인력 검색

        Args:
            org_id: Organization ID
            skill: 필요한 기술
            max_utilization: 최대 활용률 (%)
            limit: 결과 수 제한

        Returns:
            List of available personnel
        """
        try:
            response = supabase.table("vault_personnel").select(
                "id, name, email, role, primary_expertise, skills, "
                "current_project_count, max_concurrent_projects, win_rate, "
                "available_from, available_until"
            ).eq("org_id", str(org_id)).eq("is_active", True).eq(
                "employment_status", "employed"
            ).execute()

            personnel = response.data or []

            # Filter by availability window
            now = datetime.utcnow()
            personnel = [
                p for p in personnel
                if (p.get("available_from") is None or datetime.fromisoformat(p["available_from"]) <= now)
                and (p.get("available_until") is None or datetime.fromisoformat(p["available_until"]) >= now)
            ]

            # Calculate utilization and filter
            available = []
            for p in personnel:
                util = (
                    (p.get("current_project_count", 0) * 100.0) /
                    p.get("max_concurrent_projects", 3)
                ) if p.get("max_concurrent_projects", 0) > 0 else 0

                if util <= max_utilization:
                    # Filter by skill if specified
                    if skill:
                        if not any(
                            s.get("skill", "").lower() == skill.lower()
                            for s in p.get("skills", [])
                        ):
                            continue

                    available.append({**p, "utilization_percent": round(util, 1)})

            return sorted(
                available,
                key=lambda p: float(p.get("win_rate", 0)),
                reverse=True
            )[:limit]

        except Exception as e:
            logger.error(f"Failed to search available personnel: {str(e)}")
            raise

    @staticmethod
    async def search_bidding_analysis(
        org_id: UUID,
        industry: Optional[str] = None,
        budget_range: Optional[str] = None,
        search_type: str = "general",
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        입찰 분석 검색

        search_type: general, pricing, competitiveness, risk

        Args:
            org_id: Organization ID
            industry: Industry type
            budget_range: Budget range (<100M, 100M-500M, 500M-1B, 1B+)
            search_type: Type of search (general, pricing, competitiveness, risk)
            limit: Result limit

        Returns:
            Bidding analyses matching criteria
        """
        try:
            query = supabase.table("vault_bidding_analysis").select(
                "id, proposal_id, industry, budget, budget_range, similar_projects, "
                "analysis_result, confidence_score, created_at"
            ).eq("deleted_at", None)

            if industry:
                query = query.eq("industry", industry)

            if budget_range:
                query = query.eq("budget_range", budget_range)

            response = query.order("created_at", desc=True).limit(limit).execute()
            analyses = response.data or []

            # Filter by search type
            if search_type == "pricing":
                # Return analyses with high confidence
                analyses = [
                    a for a in analyses
                    if float(a.get("analysis_result", {}).get("confidence_score", 0)) >= 0.7
                ]
            elif search_type == "competitiveness":
                # Return analyses with market competitiveness info
                analyses = [
                    a for a in analyses
                    if a.get("analysis_result", {}).get("market_competitiveness")
                ]
            elif search_type == "risk":
                # Return high-risk analyses
                analyses = [
                    a for a in analyses
                    if a.get("analysis_result", {}).get("risk_level") in ["high", "medium"]
                ]

            return analyses

        except Exception as e:
            logger.error(f"Failed to search bidding analysis: {str(e)}")
            raise

    @staticmethod
    async def search_personnel_performance(
        org_id: UUID,
        min_win_rate: float = 0.0,
        min_projects: int = 0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        인력 성과 검색

        Args:
            org_id: Organization ID
            min_win_rate: 최소 낙찰률 (%)
            min_projects: 최소 프로젝트 수
            limit: 결과 수 제한

        Returns:
            Top performers
        """
        try:
            response = supabase.table("vault_personnel_top_contributors").select(
                "id, name, email, role, primary_expertise, total_proposals, "
                "won_proposals, win_rate, years_in_company"
            ).eq("org_id", str(org_id)).limit(limit).execute()

            personnel = response.data or []

            # Filter by criteria
            personnel = [
                p for p in personnel
                if float(p.get("win_rate", 0)) >= min_win_rate
                and p.get("total_proposals", 0) >= min_projects
            ]

            return personnel

        except Exception as e:
            logger.error(f"Failed to search personnel performance: {str(e)}")
            raise

    @staticmethod
    async def search_credentials(
        org_id: UUID,
        quality_threshold: float = 70.0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        증명 서류 검색

        Args:
            org_id: Organization ID
            quality_threshold: 최소 품질 점수
            limit: 결과 수 제한

        Returns:
            High-quality credentials
        """
        try:
            response = supabase.table("vault_credentials").select(
                "id, credential_type, project_name, project_amount, issue_date, "
                "quality_score, extracted_text"
            ).eq("deleted_at", None).gte(
                "quality_score", quality_threshold
            ).order("quality_score", desc=True).limit(limit).execute()

            return response.data or []

        except Exception as e:
            logger.error(f"Failed to search credentials: {str(e)}")
            raise

    # ============================================
    # Unified Chat Search
    # ============================================

    @staticmethod
    async def search_vault(
        query: str,
        org_id: UUID,
        conversation_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        통합 Vault 검색 (의도 인식 후 자동 라우팅)

        사용자의 자연어 질문을 분석하여 적절한 Vault 데이터를 검색

        Args:
            query: 사용자 질문
            org_id: Organization ID
            conversation_context: 대화 맥락 (이전 질문 등)

        Returns:
            Search results with intent analysis
        """
        try:
            result = {
                "query": query,
                "timestamp": datetime.utcnow().isoformat(),
                "intent": {},
                "results": [],
                "natural_response": "",
                "followup_suggestions": []
            }

            # Step 1: Recognize intent
            intent = VaultChatSearch.recognize_intent(query, org_id)
            result["intent"] = intent

            if intent["confidence"] < 0.5:
                result["natural_response"] = (
                    "죄송합니다. 질문이 명확하지 않습니다. "
                    "다음과 같이 질문해주세요:\n"
                    "- '제안서 작성 전문가는?'\n"
                    "- '발주처A와의 거래 현황은?'\n"
                    "- '가용한 인력은?'\n"
                    "- '적절한 입찰 가격은?'"
                )
                return result

            # Step 2: Route to appropriate search method
            method = intent["recommended_method"]

            if method == "search_personnel_by_expertise":
                results = await VaultChatSearch.search_personnel_by_expertise(
                    org_id,
                    skill=intent["search_params"].get("skill"),
                    limit=10
                )
                result["results"] = results
                if results:
                    result["natural_response"] = (
                        f"찾은 인력 {len(results)}명:\n" +
                        "\n".join(
                            f"- {p['name']} ({p.get('department', '부서미정')}): "
                            f"낙찰률 {p.get('win_rate', 0):.0f}%, "
                            f"경험 {p.get('total_proposals', 0)}건"
                            for p in results[:5]
                        )
                    )

            elif method == "search_vault_clients":
                results = await VaultChatSearch.search_vault_clients(
                    org_id,
                    client_name=intent["search_params"].get("client_name"),
                    limit=10
                )
                result["results"] = results
                if results:
                    result["natural_response"] = (
                        f"찾은 발주처 {len(results)}명:\n" +
                        "\n".join(
                            f"- {c['name']}: 낙찰률 {c.get('win_rate', 0):.0f}%, "
                            f"입찰 {c.get('total_bid_count', 0)}건"
                            for c in results[:5]
                        )
                    )

            elif method == "search_available_personnel":
                results = await VaultChatSearch.search_available_personnel(
                    org_id,
                    skill=intent["search_params"].get("skill"),
                    limit=10
                )
                result["results"] = results
                if results:
                    result["natural_response"] = (
                        f"현재 가용한 인력 {len(results)}명:\n" +
                        "\n".join(
                            f"- {p['name']} ({p.get('role', 'N/A')}): "
                            f"활용률 {p.get('utilization_percent', 0):.0f}%"
                            for p in results[:5]
                        )
                    )

            elif method == "search_bidding_analysis":
                results = await VaultChatSearch.search_bidding_analysis(
                    org_id,
                    search_type=intent["search_params"].get("search_type", "general"),
                    limit=10
                )
                result["results"] = results
                if results:
                    result["natural_response"] = (
                        f"입찰 분석 {len(results)}건:\n" +
                        "\n".join(
                            f"- {r.get('industry', 'N/A')} / 예정가 {r.get('budget', 0):,.0f}원: "
                            f"신뢰도 {r.get('analysis_result', {}).get('confidence_score', 0):.0%}"
                            for r in results[:5]
                        )
                    )

            elif method == "search_personnel_performance":
                results = await VaultChatSearch.search_personnel_performance(
                    org_id,
                    limit=10
                )
                result["results"] = results
                if results:
                    result["natural_response"] = (
                        f"상위 인력 {len(results)}명:\n" +
                        "\n".join(
                            f"- {p['name']}: 낙찰률 {p.get('win_rate', 0):.0f}%, "
                            f"경험 {p.get('total_proposals', 0)}건"
                            for p in results[:5]
                        )
                    )

            elif method == "search_credentials":
                results = await VaultChatSearch.search_credentials(org_id)
                result["results"] = results
                if results:
                    result["natural_response"] = (
                        f"품질 높은 증명서 {len(results)}건:\n" +
                        "\n".join(
                            f"- {c.get('project_name', 'N/A')}: "
                            f"품질점수 {c.get('quality_score', 0):.0f}/100"
                            for c in results[:5]
                        )
                    )

            # Add follow-up suggestions
            if not results:
                search_key = (
                    intent["search_params"].get("client_name") or
                    intent["search_params"].get("skill") or
                    query
                )
                result["natural_response"] = f"'{search_key}' 관련 데이터를 찾을 수 없습니다."
                result["followup_suggestions"] = [
                    "다른 검색 조건을 시도해보세요",
                    "부서별 인력 현황 조회",
                    "최근 입찰 분석 조회"
                ]
            else:
                result["followup_suggestions"] = [
                    f"'{results[0].get('name', 'N/A')}' 상세 정보 보기",
                    "추가 필터링",
                    "다른 검색 시도"
                ]

            return result

        except Exception as e:
            logger.error(f"Failed to search vault: {str(e)}")
            raise
