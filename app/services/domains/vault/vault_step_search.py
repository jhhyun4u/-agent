"""
Vault Step Search Service — Step별 최적화된 검색 및 데이터 라우팅
각 PDCA 단계에서 필요한 Vault 데이터를 효율적으로 검색하고 제공
"""

from datetime import datetime
from uuid import UUID
from typing import Optional, List, Dict, Any
import logging

from app.utils.supabase_client import supabase

logger = logging.getLogger(__name__)


class VaultStepSearch:
    """
    Step별 최적화 검색 및 데이터 라우팅

    Step 1 (Go/No-Go): 고객 정보, 유사 프로젝트, 팀 역량
    Step 2 (Strategy): 경쟁사 분석, 입찰 추천, 고객 선호도
    Step 3 (Plan): 인력 가용성, 팀 구성 추천, 스케줄
    Step 4 (Proposal): 신뢰성 있는 사례, 가격 결정, 섹션별 콘텐츠
    Step 5 (Presentation): 발표 전략, 고객 맞춤화, 팀 역할
    """

    # ============================================
    # Step 1: Go/No-Go Analysis
    # ============================================

    @staticmethod
    async def search_for_step1_go_no_go(
        proposal_id: UUID,
        industry: str,
        budget: int,
        estimated_client: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Step 1 (Go/No-Go) 의사결정을 위한 통합 데이터 조회

        조회 항목:
        1. 고객 정보 (발주처 이력, 낙찰률)
        2. 유사 프로젝트 (같은 산업, 예산 범위의 과거 프로젝트)
        3. 팀 역량 평가 (이 산업에서의 경험과 성과)
        4. 위험도 평가 (경쟁 강도, 요구사항 난이도)

        Args:
            proposal_id: Proposal UUID
            industry: 산업 분류 (건설, IT, 방위사업 등)
            budget: 예정가
            estimated_client: 예상 발주처명

        Returns:
            Integrated data for Go/No-Go decision
        """
        try:
            result = {
                "proposal_id": str(proposal_id),
                "step": 1,
                "timestamp": datetime.utcnow().isoformat(),
                "client_info": {},
                "similar_projects": [],
                "team_capability": {},
                "risk_assessment": {}
            }

            # 1. 고객 정보 조회
            if estimated_client:
                client_response = supabase.table("vault_clients").select(
                    "id, name, win_rate, total_bid_count, avg_bid_amount, "
                    "last_bid_date, lessons_learned, relationship_notes"
                ).eq("name", estimated_client).eq("deleted_at", None).execute()

                if client_response.data:
                    client = client_response.data[0]
                    result["client_info"] = {
                        "client_id": client["id"],
                        "name": client["name"],
                        "win_rate": float(client.get("win_rate", 0)),
                        "total_bids": client.get("total_bid_count", 0),
                        "relationship": client.get("relationship_notes", ""),
                        "lessons_learned": client.get("lessons_learned", "")
                    }

            # 2. 유사 프로젝트 조회 (같은 산업, 예산 ±40%)
            min_budget = int(budget * 0.6)
            max_budget = int(budget * 1.4)

            similar_response = supabase.table("vault_bidding_analysis").select(
                "id, proposal_id, industry, budget, similar_projects, "
                "analysis_result, created_at"
            ).eq("industry", industry).gte("budget", min_budget).lte(
                "budget", max_budget
            ).eq("deleted_at", None).order("created_at", desc=True).limit(5).execute()

            if similar_response.data:
                result["similar_projects"] = [
                    {
                        "analysis_id": p["id"],
                        "industry": p["industry"],
                        "budget": p["budget"],
                        "comparable_projects": len(p.get("similar_projects", [])),
                        "avg_bid_ratio": p.get("analysis_result", {}).get("avg_bid_ratio"),
                        "market_competitiveness": p.get("analysis_result", {}).get("market_competitiveness"),
                        "risk_level": p.get("analysis_result", {}).get("risk_level")
                    }
                    for p in similar_response.data
                ]

            # 3. 팀 역량 평가 (이 산업에서의 경험)
            dept_stats_response = supabase.table("vault_personnel_by_department").select(
                "department, total_count, active_count, avg_win_rate, "
                "avg_tenure, key_skills"
            ).execute()

            if dept_stats_response.data:
                team_capability = {
                    "total_active_personnel": sum(d.get("active_count", 0) for d in dept_stats_response.data),
                    "average_win_rate": sum(d.get("avg_win_rate", 0) for d in dept_stats_response.data) / len(dept_stats_response.data),
                    "departments": [
                        {
                            "name": d.get("department", "Unknown"),
                            "personnel": d.get("active_count", 0),
                            "win_rate": d.get("avg_win_rate", 0),
                            "key_skills": d.get("key_skills", "")
                        }
                        for d in dept_stats_response.data
                    ]
                }
                result["team_capability"] = team_capability

            # 4. 위험도 평가 (분석 결과에서 추출)
            if similar_response.data:
                risk_levels = [
                    p.get("analysis_result", {}).get("risk_level")
                    for p in similar_response.data
                ]
                high_risk_count = sum(1 for r in risk_levels if r == "high")

                result["risk_assessment"] = {
                    "similar_projects_analyzed": len(similar_response.data),
                    "high_risk_percentage": (high_risk_count / len(similar_response.data) * 100) if similar_response.data else 0,
                    "recommendation": (
                        "고위험도 프로젝트 다수. 신중한 검토 필요"
                        if high_risk_count > len(similar_response.data) * 0.5
                        else "적절한 난이도. 진행 권장"
                    )
                }

            return result

        except Exception as e:
            logger.error(f"Failed to search for Step 1: {str(e)}")
            raise

    # ============================================
    # Step 2: Strategy Development
    # ============================================

    @staticmethod
    async def search_for_step2_strategy(
        proposal_id: UUID,
        industry: str,
        budget: int,
        client_name: Optional[str] = None,
        team_lead_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Step 2 (제안전략) 수립을 위한 경쟁 분석 및 입찰 추천

        조회 항목:
        1. 경쟁사 분석 (같은 산업에서의 경쟁 현황)
        2. 입찰 가격 추천 (낙찰률, 전략 가이드)
        3. 고객 선호도 (과거 학습한 고객 특성)
        4. 리더 역량 (팀 리더의 전문성과 경험)

        Args:
            proposal_id: Proposal UUID
            industry: Industry type
            budget: Estimated budget
            client_name: Client name (for preferences)
            team_lead_id: Team lead personnel ID

        Returns:
            Data for strategy development
        """
        try:
            result = {
                "proposal_id": str(proposal_id),
                "step": 2,
                "timestamp": datetime.utcnow().isoformat(),
                "bidding_recommendation": {},
                "competitive_analysis": {},
                "client_preferences": {},
                "team_lead_expertise": {}
            }

            # 1. 입찰 가격 추천 (같은 산업의 최근 분석)
            bidding_response = supabase.table("vault_bidding_analysis").select(
                "id, industry, budget_range, analysis_result, confidence_score, "
                "created_at"
            ).eq("industry", industry).eq("deleted_at", None).order(
                "created_at", desc=True
            ).limit(3).execute()

            if bidding_response.data:
                analyses = bidding_response.data
                avg_confidence = sum(
                    float(a.get("analysis_result", {}).get("confidence_score", 0))
                    for a in analyses
                ) / len(analyses) if analyses else 0

                result["bidding_recommendation"] = {
                    "industry": industry,
                    "avg_recommended_bid_ratio": sum(
                        float(a.get("analysis_result", {}).get("avg_bid_ratio", 0))
                        for a in analyses
                    ) / len(analyses) if analyses else 0,
                    "recommended_strategy": analyses[0].get("analysis_result", {}).get("pricing_strategy", "moderate"),
                    "confidence_score": round(avg_confidence, 2),
                    "market_competitiveness": analyses[0].get("analysis_result", {}).get("market_competitiveness"),
                    "recent_analyses": len(analyses)
                }

            # 2. 경쟁사 분석 (산업별 경쟁 강도)
            industry_stats_response = supabase.table("vault_bidding_by_industry").select(
                "industry, total_projects, avg_bid_ratio, avg_confidence, "
                "high_risk_count, medium_risk_count, low_risk_count"
            ).eq("industry", industry).execute()

            if industry_stats_response.data:
                stats = industry_stats_response.data[0]
                total_projects = stats.get("total_projects", 1)

                result["competitive_analysis"] = {
                    "industry": industry,
                    "total_projects_analyzed": total_projects,
                    "average_bid_ratio": stats.get("avg_bid_ratio", 0),
                    "competitiveness_level": (
                        "intense" if stats.get("high_risk_count", 0) / max(total_projects, 1) > 0.5
                        else "moderate" if stats.get("medium_risk_count", 0) / max(total_projects, 1) > 0.5
                        else "weak"
                    ),
                    "market_trend": "경쟁 심화" if stats.get("high_risk_count", 0) > stats.get("low_risk_count", 0) else "기회 시장"
                }

            # 3. 고객 선호도
            if client_name:
                client_response = supabase.table("vault_clients").select(
                    "id, preferences, lessons_learned, avg_bid_amount"
                ).eq("name", client_name).eq("deleted_at", None).execute()

                if client_response.data:
                    client = client_response.data[0]
                    result["client_preferences"] = {
                        "client_name": client_name,
                        "preferences": client.get("preferences", {}),
                        "past_lessons": client.get("lessons_learned", ""),
                        "average_bid_amount": client.get("avg_bid_amount", 0),
                        "bidding_pattern": "낮은 가격 선호" if client.get("avg_bid_amount", 0) < budget * 0.85 else "중상 가격대"
                    }

            # 4. 팀 리더 역량
            if team_lead_id:
                leader_response = supabase.table("vault_personnel").select(
                    "id, name, primary_expertise, win_rate, total_proposals, "
                    "years_in_company, skills"
                ).eq("id", str(team_lead_id)).execute()

                if leader_response.data:
                    leader = leader_response.data[0]
                    result["team_lead_expertise"] = {
                        "name": leader.get("name"),
                        "primary_expertise": leader.get("primary_expertise"),
                        "win_rate": leader.get("win_rate", 0),
                        "experience": leader.get("total_proposals", 0),
                        "tenure_years": leader.get("years_in_company", 0),
                        "skills": leader.get("skills", [])[:3]  # Top 3 skills
                    }

            return result

        except Exception as e:
            logger.error(f"Failed to search for Step 2: {str(e)}")
            raise

    # ============================================
    # Step 3: Plan & Team Composition
    # ============================================

    @staticmethod
    async def search_for_step3_planning(
        proposal_id: UUID,
        team_size: int = 3,
        required_expertise: Optional[List[str]] = None,
        org_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Step 3 (제안 계획) 수립을 위한 인력 검색 및 팀 구성

        조회 항목:
        1. 가용 인력 (역량 기반)
        2. 최적 팀 구성 추천
        3. 일정 계획 데이터
        4. 과거 유사 팀의 성과

        Args:
            proposal_id: Proposal UUID
            team_size: 필요한 팀 규모
            required_expertise: 필요한 기술 [e.g. "제안서 작성", "기술평가"]
            org_id: Organization ID

        Returns:
            Personnel and team composition recommendations
        """
        try:
            result = {
                "proposal_id": str(proposal_id),
                "step": 3,
                "timestamp": datetime.utcnow().isoformat(),
                "available_personnel": [],
                "recommended_team": [],
                "capacity_analysis": {},
                "schedule_recommendations": {}
            }

            if not org_id:
                return result

            # 1. 가용 인력 검색
            available_response = supabase.table("vault_personnel").select(
                "id, name, email, role, primary_expertise, skills, "
                "total_proposals, won_proposals, win_rate, "
                "current_project_count, max_concurrent_projects, department"
            ).eq("org_id", str(org_id)).eq("is_active", True).eq(
                "employment_status", "employed"
            ).execute()

            available_personnel = available_response.data or []

            # Filter by required expertise if specified
            if required_expertise:
                filtered = []
                for person in available_personnel:
                    person_skills = [s.get("skill") for s in person.get("skills", [])]
                    if any(req_skill in person_skills for req_skill in required_expertise):
                        filtered.append(person)
                available_personnel = filtered

            # 2. 추천 팀 구성 (높은 낙찰률 순서)
            recommended = sorted(
                available_personnel,
                key=lambda p: (
                    float(p.get("win_rate", 0)),
                    p.get("total_proposals", 0)
                ),
                reverse=True
            )[:team_size]

            result["available_personnel"] = [
                {
                    "id": p["id"],
                    "name": p["name"],
                    "expertise": p.get("primary_expertise"),
                    "win_rate": p.get("win_rate", 0),
                    "utilization": (
                        p.get("current_project_count", 0) * 100.0 /
                        p.get("max_concurrent_projects", 3)
                    ),
                    "available": p.get("current_project_count", 0) < p.get("max_concurrent_projects", 3)
                }
                for p in available_personnel[:10]
            ]

            result["recommended_team"] = [
                {
                    "id": p["id"],
                    "name": p["name"],
                    "role": p.get("role"),
                    "expertise": p.get("primary_expertise"),
                    "win_rate": p.get("win_rate", 0),
                    "proposed_role": "리더" if i == 0 else "멤버"
                }
                for i, p in enumerate(recommended)
            ]

            # 3. 용량 분석
            total_available_capacity = sum(
                p.get("max_concurrent_projects", 3) - p.get("current_project_count", 0)
                for p in available_personnel
            )

            result["capacity_analysis"] = {
                "total_active_personnel": len(available_personnel),
                "team_availability": len(recommended),
                "total_capacity": total_available_capacity,
                "capacity_status": (
                    "여유" if total_available_capacity >= team_size * 2
                    else "적정" if total_available_capacity >= team_size
                    else "긴급"
                )
            }

            # 4. 일정 권장사항
            avg_proposals_per_person = (
                sum(p.get("total_proposals", 0) for p in recommended) / len(recommended)
                if recommended else 0
            )

            result["schedule_recommendations"] = {
                "team_experience_level": (
                    "고경험" if avg_proposals_per_person > 20
                    else "중경험" if avg_proposals_per_person > 10
                    else "저경험"
                ),
                "estimated_working_days": (
                    14 if avg_proposals_per_person > 20
                    else 21 if avg_proposals_per_person > 10
                    else 28
                ),
                "milestone_days": {
                    "strategy_review": 3,
                    "draft_completion": 10,
                    "internal_review": 5,
                    "final_submission": 2
                }
            }

            return result

        except Exception as e:
            logger.error(f"Failed to search for Step 3: {str(e)}")
            raise

    # ============================================
    # Step 4: Proposal Writing
    # ============================================

    @staticmethod
    async def search_for_step4_proposal_writing(
        proposal_id: UUID,
        client_name: Optional[str] = None,
        industry: Optional[str] = None,
        budget: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Step 4 (제안서 작성) 단계 지원 데이터

        조회 항목:
        1. 신뢰성 있는 사례 (인증서, 성공 사례)
        2. 가격 결정 가이드 (입찰 분석 결과)
        3. 고객별 맞춤 사항
        4. 섹션별 콘텐츠 템플릿

        Args:
            proposal_id: Proposal UUID
            client_name: Client name for customization
            industry: Industry for content reference
            budget: Budget for pricing guidance

        Returns:
            Content and pricing guidance for proposal writing
        """
        try:
            result = {
                "proposal_id": str(proposal_id),
                "step": 4,
                "timestamp": datetime.utcnow().isoformat(),
                "credibility_evidence": [],
                "pricing_guidance": {},
                "client_customization": {},
                "content_references": {}
            }

            # 1. 신뢰성 있는 사례 (발주처 관련 증빙)
            if client_name:
                credentials_response = supabase.table("vault_credentials").select(
                    "id, credential_type, extracted_text, quality_score, "
                    "project_name, project_amount, issue_date, issuer"
                ).eq("is_active", True).eq("deleted_at", None).order(
                    "quality_score", desc=True
                ).limit(5).execute()

                if credentials_response.data:
                    result["credibility_evidence"] = [
                        {
                            "id": c["id"],
                            "type": c.get("credential_type", "인증서"),
                            "project": c.get("project_name", ""),
                            "amount": c.get("project_amount", 0),
                            "date": c.get("issue_date", ""),
                            "quality_score": c.get("quality_score", 0)
                        }
                        for c in credentials_response.data
                    ]

            # 2. 가격 결정 가이드
            if industry and budget:
                bidding_response = supabase.table("vault_bidding_analysis").select(
                    "id, analysis_result"
                ).eq("industry", industry).eq("deleted_at", None).order(
                    "created_at", desc=True
                ).limit(1).execute()

                if bidding_response.data:
                    analysis = bidding_response.data[0].get("analysis_result", {})
                    result["pricing_guidance"] = {
                        "recommended_bid": analysis.get("recommended_bid", 0),
                        "bid_ratio": analysis.get("avg_bid_ratio", 0),
                        "pricing_strategy": analysis.get("pricing_strategy", "moderate"),
                        "confidence": analysis.get("confidence_score", 0),
                        "market_notes": analysis.get("recommendation", "")
                    }

            # 3. 고객 맞춤 정보
            if client_name:
                client_response = supabase.table("vault_clients").select(
                    "id, preferences, lessons_learned, relationship_notes, "
                    "win_rate, avg_bid_amount"
                ).eq("name", client_name).eq("deleted_at", None).execute()

                if client_response.data:
                    client = client_response.data[0]
                    result["client_customization"] = {
                        "client_name": client_name,
                        "relationship_notes": client.get("relationship_notes", ""),
                        "lessons_learned": client.get("lessons_learned", ""),
                        "preferences": client.get("preferences", {}),
                        "win_rate_with_client": client.get("win_rate", 0),
                        "typical_bid_amount": client.get("avg_bid_amount", 0)
                    }

            # 4. 섹션별 콘텐츠 참고
            if industry:
                result["content_references"] = {
                    "industry": industry,
                    "common_sections": [
                        "기술 우수성 (T/S 차별성)",
                        "조직 및 인력 (경험, 역량)",
                        "가격 경쟁력 (ROI, 비용 대비 효과)",
                        "사업 관리 계획 (일정, 품질)",
                        "과거 수행 실적 (참고 사례)"
                    ],
                    "recommended_length": 50 if budget and budget > 1000000000 else 30,
                    "emphasis_areas": (
                        ["기술 차별성", "비용 효율"] if industry == "IT"
                        else ["경험과 신뢰", "기술력"] if industry == "건설"
                        else ["기술력", "조직역량"]
                    )
                }

            return result

        except Exception as e:
            logger.error(f"Failed to search for Step 4: {str(e)}")
            raise

    # ============================================
    # Step 5: Presentation
    # ============================================

    @staticmethod
    async def search_for_step5_presentation(
        proposal_id: UUID,
        client_name: Optional[str] = None,
        team_lead_id: Optional[UUID] = None,
        presentation_duration_minutes: int = 20
    ) -> Dict[str, Any]:
        """
        Step 5 (발표) 전략 수립 지원 데이터

        조회 항목:
        1. 고객 맞춤화 전략
        2. 팀 구성 및 역할 배정
        3. 발표 구성 권장사항
        4. 청중 분석

        Args:
            proposal_id: Proposal UUID
            client_name: Client name
            team_lead_id: Team lead for presentation
            presentation_duration_minutes: Presentation time available

        Returns:
            Presentation strategy and team composition
        """
        try:
            result = {
                "proposal_id": str(proposal_id),
                "step": 5,
                "timestamp": datetime.utcnow().isoformat(),
                "client_strategy": {},
                "team_composition": {},
                "presentation_structure": {},
                "audience_analysis": {}
            }

            # 1. 고객 맞춤 전략
            if client_name:
                client_response = supabase.table("vault_clients").select(
                    "id, preferences, relationship_notes, lessons_learned"
                ).eq("name", client_name).eq("deleted_at", None).execute()

                if client_response.data:
                    client = client_response.data[0]
                    prefs = client.get("preferences", {})

                    result["client_strategy"] = {
                        "client_name": client_name,
                        "decision_maker_focus": prefs.get("decision_maker", "기술적 우수성"),
                        "emphasis": prefs.get("emphasis", "비용 대비 가치"),
                        "relationship_level": "기존 고객" if client.get("relationship_notes") else "신규 고객",
                        "past_feedback": client.get("lessons_learned", "")
                    }

            # 2. 팀 구성 및 역할
            if team_lead_id:
                leader_response = supabase.table("vault_personnel").select(
                    "id, name, role, primary_expertise, skills"
                ).eq("id", str(team_lead_id)).execute()

                if leader_response.data:
                    leader = leader_response.data[0]
                    result["team_composition"] = {
                        "leader": {
                            "name": leader.get("name"),
                            "role": leader.get("role"),
                            "expertise": leader.get("primary_expertise"),
                            "speaking_topics": ["전략", "개요", "마무리"]
                        },
                        "team_size": 2,  # Leader + 1 additional
                        "recommended_members": [
                            {
                                "position": "기술담당",
                                "topics": ["기술 차별성", "구현 방안"],
                                "skill_required": "기술평가"
                            },
                            {
                                "position": "사업담당",
                                "topics": ["경영 방안", "리스크 관리"],
                                "skill_required": "기술평가"
                            }
                        ]
                    }

            # 3. 발표 구성
            time_per_section = presentation_duration_minutes / 5  # 5 main sections

            result["presentation_structure"] = {
                "total_duration_minutes": presentation_duration_minutes,
                "sections": [
                    {
                        "title": "오프닝 (Executive Summary)",
                        "duration_minutes": time_per_section,
                        "key_messages": ["차별성", "고객 이해", "전략"],
                        "slides": 3
                    },
                    {
                        "title": "기술 솔루션",
                        "duration_minutes": time_per_section,
                        "key_messages": ["차별성", "구현 접근", "리스크 대응"],
                        "slides": 4
                    },
                    {
                        "title": "조직 및 팀",
                        "duration_minutes": time_per_section,
                        "key_messages": ["경험", "역량", "신뢰성"],
                        "slides": 3
                    },
                    {
                        "title": "가격 및 일정",
                        "duration_minutes": time_per_section,
                        "key_messages": ["가치", "비용 효율", "합리성"],
                        "slides": 2
                    },
                    {
                        "title": "클로징 (Q&A 준비)",
                        "duration_minutes": time_per_section,
                        "key_messages": ["핵심 가치", "질의 대응", "재확인"],
                        "slides": 2
                    }
                ],
                "recommended_slides": 14
            }

            # 4. 청중 분석
            result["audience_analysis"] = {
                "expected_attendees": [
                    "발주처 담당자 (기술, 사업)",
                    "평가위원 (3-5명)",
                    "발주처 상급자"
                ],
                "decision_criteria": [
                    "기술적 우수성 (40%)",
                    "비용 경쟁력 (30%)",
                    "조직역량 (20%)",
                    "사업이해도 (10%)"
                ],
                "engagement_strategy": "상호작용형, Q&A 시간 확보",
                "visual_approach": "차트 위주, 시각적 임팩트"
            }

            return result

        except Exception as e:
            logger.error(f"Failed to search for Step 5: {str(e)}")
            raise

    # ============================================
    # Utility: Multi-Step Integrated Search
    # ============================================

    @staticmethod
    async def search_integrated_vault_data(
        proposal_id: UUID,
        industry: str,
        budget: int,
        client_name: Optional[str] = None,
        org_id: Optional[UUID] = None,
        team_lead_id: Optional[UUID] = None,
        current_step: int = 1
    ) -> Dict[str, Any]:
        """
        현재 단계에 맞는 통합 Vault 데이터 조회

        현재 Step에서 필요한 모든 데이터를 한 번에 조회

        Args:
            proposal_id: Proposal UUID
            industry: Industry type
            budget: Estimated budget
            client_name: Client name
            org_id: Organization ID
            team_lead_id: Team lead ID
            current_step: Current PDCA step (1-5)

        Returns:
            Step-specific integrated vault data
        """
        try:
            if current_step == 1:
                return await VaultStepSearch.search_for_step1_go_no_go(
                    proposal_id, industry, budget, client_name
                )
            elif current_step == 2:
                return await VaultStepSearch.search_for_step2_strategy(
                    proposal_id, industry, budget, client_name, team_lead_id
                )
            elif current_step == 3:
                return await VaultStepSearch.search_for_step3_planning(
                    proposal_id, team_size=3, org_id=org_id
                )
            elif current_step == 4:
                return await VaultStepSearch.search_for_step4_proposal_writing(
                    proposal_id, client_name, industry, budget
                )
            elif current_step == 5:
                return await VaultStepSearch.search_for_step5_presentation(
                    proposal_id, client_name, team_lead_id
                )
            else:
                raise ValueError(f"Invalid step: {current_step}. Expected 1-5.")

        except Exception as e:
            logger.error(f"Failed integrated search for step {current_step}: {str(e)}")
            raise
