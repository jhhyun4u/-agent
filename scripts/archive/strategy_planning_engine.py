"""
전략 수립 모듈 상세 구현
Winning Point 결정 및 가격 전략 수립
"""

from typing import Dict, List, Any, Tuple, Optional
import math
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

class WinningStrategy(Enum):
    # Defence 전략 (강점 분야)
    DEFENCE_TECHNICAL = "defence_technical"              # 기술 강점 분야 방어 전략
    DEFENCE_TRACK_RECORD = "defence_track_record"        # 실적 강점 분야 방어 전략
    DEFENCE_RELATIONSHIP = "defence_relationship"        # 관계 강점 분야 방어 전략

    # Offence 전략 (약점 분야)
    OFFENCE_INNOVATION = "offence_innovation"            # 혁신으로 신규 진입
    OFFENCE_DIFFERENTIATION = "offence_differentiation"  # 차별화로 시장 공략
    OFFENCE_AGGRESSIVE_PRICING = "offence_aggressive_pricing"  # 공격적 가격 전략

    # 일반 전략
    TECHNICAL_SUPERIORITY = "technical_superiority"      # 기술 우위 전략
    COST_LEADERSHIP = "cost_leadership"                  # 원가 경쟁력 전략
    PARTNERSHIP = "partnership"                          # 파트너십 전략

class PriceStrategy(Enum):
    PENETRATION = "penetration"          # 시장 침투 가격
    SKIMMING = "skimming"               # 시장 착취 가격
    COMPETITIVE = "competitive"          # 경쟁 가격
    VALUE_BASED = "value_based"          # 가치 기반 가격
    COST_PLUS = "cost_plus"             # 원가 플러스 가격

@dataclass
class WinningPoint:
    """승점 요소"""
    factor: str
    score: float  # 0.0 ~ 1.0
    impact: float  # 영향도
    description: str
    evidence: List[str]

@dataclass
class CompetitiveAnalysis:
    """경쟁사 분석"""
    competitor_name: str
    strength_score: float
    weakness_score: float
    estimated_price: Optional[int]
    key_differentiators: List[str]

@dataclass
class StrategyRecommendation:
    """전략 추천"""
    primary_strategy: WinningStrategy
    secondary_strategies: List[WinningStrategy]
    price_strategy: PriceStrategy
    target_price_range: Tuple[int, int]
    winning_points: List[WinningPoint]
    competitive_advantages: List[str]
    risk_mitigation: List[str]
    action_items: List[str]
    strategy_type: str  # "defence" or "offence"
    track_record_strength: float  # 0.0 ~ 1.0 (해당 분야 track record 강도)

class StrategyPlanningEngine:
    """전략 수립 엔진"""

    def __init__(self):
        self.strategy_weights = {
            "technical_capability": 0.25,
            "past_performance": 0.20,
            "price_competitiveness": 0.20,
            "innovation": 0.15,
            "relationship": 0.10,
            "compliance": 0.10
        }

    async def develop_strategy(self, rfp_analysis: Dict, company_profile: Dict,
                             market_analysis: Dict, past_proposals: List[Dict]) -> StrategyRecommendation:
        """
        종합 전략 수립

        Args:
            rfp_analysis: RFP 분석 결과
            company_profile: 회사 프로필
            market_analysis: 시장 분석 데이터
            past_proposals: 과거 제안 실적

        Returns:
            StrategyRecommendation: 전략 추천
        """

        # 경쟁사 분석
        competitors = await self._analyze_competition(rfp_analysis, market_analysis)

        # Defence vs Offence 전략 분석
        strategy_analysis = await self._analyze_defence_offence_strategy(
            rfp_analysis, company_profile, past_proposals
        )

        # 승점 분석 (전략 타입에 따라 조정)
        winning_points = await self._identify_winning_points(
            rfp_analysis, company_profile, competitors, past_proposals, strategy_analysis
        )

        # 전략 우선순위 결정 (defence/offence 고려)
        strategy_priorities = self._determine_strategy_priorities(
            winning_points, company_profile, competitors, strategy_analysis
        )

        # 가격 전략 수립 (전략 타입에 따라 조정)
        price_strategy = await self._develop_pricing_strategy(
            rfp_analysis, competitors, company_profile, strategy_analysis
        )

        # 최종 전략 추천 생성
        recommendation = StrategyRecommendation(
            primary_strategy=strategy_priorities[0],
            secondary_strategies=strategy_priorities[1:3],
            price_strategy=price_strategy["strategy"],
            target_price_range=price_strategy["price_range"],
            winning_points=winning_points,
            competitive_advantages=self._identify_competitive_advantages(
                company_profile, competitors, strategy_analysis
            ),
            risk_mitigation=self._develop_risk_mitigation_plan(
                rfp_analysis, strategy_priorities[0], strategy_analysis
            ),
            action_items=self._create_action_items(strategy_priorities[0], price_strategy, strategy_analysis),
            strategy_type=strategy_analysis["strategy_type"],
            track_record_strength=strategy_analysis["track_record_strength"]
        )

        return recommendation

    async def _analyze_defence_offence_strategy(self, rfp_analysis: Dict, company_profile: Dict,
                                              past_proposals: List[Dict]) -> Dict[str, Any]:
        """
        Defence vs Offence 전략 분석

        Defence 전략: 해당 분야에서 track record가 강한 경우
        Offence 전략: 신규 진입 또는 track record가 약한 경우

        Returns:
            Dict: 전략 분석 결과
        """

        # RFP 분야 분석
        rfp_category = rfp_analysis["basic_info"].get("category", "")
        rfp_technical_reqs = rfp_analysis["requirements"].get("technical_requirements", [])

        # 회사 역량 분석
        company_expertise = company_profile.get("expertise_areas", [])
        company_tech_stack = company_profile.get("technology_stack", [])

        # 과거 실적 분석
        relevant_experience = self._analyze_relevant_experience(past_proposals, rfp_category, rfp_technical_reqs)

        # Track record 강도 계산 (0.0 ~ 1.0)
        track_record_strength = self._calculate_track_record_strength(
            relevant_experience, rfp_category, company_expertise
        )

        # 경쟁사 분석 (나라장터 기반)
        competitors = await self._search_g2b_competitors(rfp_analysis)

        # 경쟁 강도 분석
        competitor_strength = self._analyze_competitor_strength(competitors)

        # Defence/Offence 전략 결정 (경쟁사 정보 반영)
        if track_record_strength >= 0.7 and competitor_strength < 0.6:
            strategy_type = "defence"
            reasoning = f"강력한 track record 보유하고 경쟁 강도가 낮아 방어 전략 최적 (track record: {track_record_strength:.2f}, 경쟁 강도: {competitor_strength:.2f})"
        elif track_record_strength >= 0.4 and competitor_strength < 0.7:
            strategy_type = "balanced"
            reasoning = f"적정 경험 보유하고 경쟁이 치열하지 않아 균형 전략 적합 (track record: {track_record_strength:.2f}, 경쟁 강도: {competitor_strength:.2f})"
        else:
            strategy_type = "offence"
            reasoning = f"경쟁이 치열하거나 track record 부족으로 공격 전략 필요 (track record: {track_record_strength:.2f}, 경쟁 강도: {competitor_strength:.2f})"

        return {
            "strategy_type": strategy_type,
            "track_record_strength": track_record_strength,
            "relevant_experience": relevant_experience,
            "competitor_strength": competitor_strength,
            "reasoning": reasoning,
            "rfp_category": rfp_category,
            "company_expertise_match": self._calculate_expertise_match(company_expertise, rfp_technical_reqs),
            "key_competitors": [c.company_name for c in competitors[:3]] if competitors else []
        }

    def _analyze_competitor_strength(self, competitors: List[Any]) -> float:
        """
        나라장터 기반 경쟁사 강도 분석

        Args:
            competitors: CompetitorProfile 목록

        Returns:
            평균 경쟁 강도 (0.0 ~ 1.0)
        """
        if not competitors:
            return 0.3  # 경쟁사가 없으면 낮은 강도로 가정

        # 평균 강점 점수 계산
        avg_strength = sum(c.strength_score for c in competitors) / len(competitors)

        # 경쟁사 수에 따른 조정 (경쟁사 많을수록 강도 상승)
        competitor_count_factor = min(len(competitors) * 0.1, 0.3)

        # 시장 점유율 고려
        total_market_share = sum(c.market_share for c in competitors)
        market_concentration = min(total_market_share * 2, 0.4)  # 시장 집중도

        return min(avg_strength + competitor_count_factor + market_concentration, 0.95)

    def _analyze_relevant_experience(self, past_proposals: List[Dict], rfp_category: str,
                                   rfp_technical_reqs: List[str]) -> Dict[str, Any]:
        """관련 경험 분석"""

        relevant_projects = []
        total_projects = len(past_proposals)

        for proposal in past_proposals:
            project_category = proposal.get("category", "")
            project_technologies = proposal.get("technologies", [])
            project_result = proposal.get("result", "")

            # 카테고리 매칭
            category_match = self._calculate_category_similarity(rfp_category, project_category)

            # 기술 매칭
            tech_match = len(set(rfp_technical_reqs) & set(project_technologies)) / max(len(rfp_technical_reqs), 1)

            # 종합 관련성 점수
            relevance_score = (category_match * 0.6) + (tech_match * 0.4)

            if relevance_score >= 0.3:  # 30% 이상 관련성
                relevant_projects.append({
                    "project": proposal,
                    "relevance_score": relevance_score,
                    "category_match": category_match,
                    "tech_match": tech_match,
                    "result": project_result
                })

        # 성공률 계산
        successful_projects = sum(1 for p in relevant_projects if p["result"] == "won")
        success_rate = successful_projects / max(len(relevant_projects), 1)

        return {
            "relevant_projects": relevant_projects,
            "total_relevant": len(relevant_projects),
            "total_past": total_projects,
            "success_rate": success_rate,
            "avg_relevance": sum(p["relevance_score"] for p in relevant_projects) / max(len(relevant_projects), 1)
        }

    def _calculate_track_record_strength(self, relevant_experience: Dict, rfp_category: str,
                                       company_expertise: List[str]) -> float:
        """Track record 강도 계산"""

        # 관련 프로젝트 수 기반 점수
        project_score = min(relevant_experience["total_relevant"] / 5, 1.0)  # 5개 이상이면 최대

        # 성공률 기반 점수
        success_score = relevant_experience["success_rate"]

        # 평균 관련성 기반 점수
        relevance_score = relevant_experience["avg_relevance"]

        # 전문성 매칭 점수
        expertise_score = len([exp for exp in company_expertise if exp.lower() in rfp_category.lower()]) / max(len(company_expertise), 1)

        # 종합 점수 (가중치 적용)
        final_score = (
            project_score * 0.4 +      # 프로젝트 경험
            success_score * 0.3 +      # 성공률
            relevance_score * 0.2 +    # 관련성
            expertise_score * 0.1      # 전문성
        )

        return min(final_score, 1.0)

    def _calculate_category_similarity(self, category1: str, category2: str) -> float:
        """카테고리 유사도 계산"""
        if not category1 or not category2:
            return 0.0

        # 정확 매칭
        if category1.lower() == category2.lower():
            return 1.0

        # 부분 매칭
        words1 = set(category1.lower().split())
        words2 = set(category2.lower().split())

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def _calculate_expertise_match(self, company_expertise: List[str], rfp_reqs: List[str]) -> float:
        """전문성 매칭도 계산"""
        if not rfp_reqs:
            return 1.0

        matches = 0
        for req in rfp_reqs:
            req_lower = req.lower()
            for expertise in company_expertise:
                if req_lower in expertise.lower() or expertise.lower() in req_lower:
                    matches += 1
                    break

        return matches / len(rfp_reqs)

    async def _analyze_competition(self, rfp_analysis: Dict, market_analysis: Dict) -> List[CompetitiveAnalysis]:
        """경쟁사 분석 (나라장터 연동 포함)"""

        competitors = []

        # 1. 나라장터에서 유사 용역 검색 및 경쟁사 식별
        g2b_competitors = await self._search_g2b_competitors(rfp_analysis)

        # 나라장터 경쟁사를 CompetitiveAnalysis로 변환
        for comp_profile in g2b_competitors:
            competitor = CompetitiveAnalysis(
                competitor_name=comp_profile.company_name,
                strength_score=comp_profile.strength_score,
                weakness_score=comp_profile.weakness_score,
                estimated_price=comp_profile.avg_contract_amount,
                key_differentiators=[
                    f"시장점유율: {comp_profile.market_share:.1%}",
                    f"평균계약금액: {comp_profile.avg_contract_amount:,}원",
                    f"성공률: {comp_profile.success_rate:.1%}",
                    f"전문분야: {', '.join(comp_profile.specialization_areas)}"
                ]
            )
            competitors.append(competitor)

        # 2. 기존 시장 분석 데이터에서 추가 경쟁사 (fallback)
        potential_competitors = market_analysis.get("potential_competitors", [])
        for comp_data in potential_competitors:
            # 이미 나라장터에서 식별된 경쟁사는 제외
            if not any(c.competitor_name == comp_data.get("name", "") for c in competitors):
                competitor = CompetitiveAnalysis(
                    competitor_name=comp_data.get("name", "Unknown"),
                    strength_score=self._assess_competitor_strength(comp_data, rfp_analysis),
                    weakness_score=self._assess_competitor_weakness(comp_data, rfp_analysis),
                    estimated_price=comp_data.get("estimated_price"),
                    key_differentiators=comp_data.get("differentiators", [])
                )
                competitors.append(competitor)

        # 3. 경쟁사가 없는 경우 기본 분석
        if not competitors:
            competitors = [self._create_default_competitor_analysis(rfp_analysis)]

        return competitors

    async def _search_g2b_competitors(self, rfp_analysis: Dict) -> List[Any]:
        """
        나라장터에서 유사 용역 검색 및 경쟁사 식별

        Args:
            rfp_analysis: RFP 분석 결과

        Returns:
            CompetitorProfile 목록
        """
        try:
            from app.services.g2b_service import G2BService

            async with G2BService() as g2b_service:
                # RFP 정보 추출
                rfp_title = rfp_analysis.get("basic_info", {}).get("title", "")
                rfp_description = rfp_analysis.get("basic_info", {}).get("description", "")

                # 검색 키워드 추출
                requirements = rfp_analysis.get("requirements", {})
                technical_reqs = requirements.get("technical_requirements", [])
                keywords = technical_reqs[:5]  # 상위 5개 키워드

                # 예산 범위 (RFP에서 추정)
                budget_info = rfp_analysis.get("basic_info", {}).get("budget", {})
                budget_range = None
                if isinstance(budget_info, dict):
                    min_budget = budget_info.get("min_amount")
                    max_budget = budget_info.get("max_amount")
                    if min_budget and max_budget:
                        budget_range = (min_budget, max_budget)

                # 유사 계약 검색
                similar_contracts = await g2b_service.search_similar_contracts(
                    rfp_title=rfp_title,
                    rfp_description=rfp_description,
                    keywords=keywords,
                    budget_range=budget_range,
                    date_range_months=24  # 최근 2년
                )

                # 경쟁사 식별 (최소 2건 계약 이상)
                competitors = await g2b_service.identify_competitors(
                    similar_contracts, min_contracts=2
                )

                return competitors

        except ImportError:
            print("G2B 서비스를 불러올 수 없습니다. 기존 방식으로 진행합니다.")
            return []
        except Exception as e:
            print(f"나라장터 검색 중 오류 발생: {e}")
            return []

    async def _identify_winning_points(self, rfp_analysis: Dict, company_profile: Dict,
                                     competitors: List[CompetitiveAnalysis],
                                     past_proposals: List[Dict], strategy_type: str) -> List[WinningPoint]:
        """승점 요소 식별 (Defence/Offence 전략 고려)"""

        winning_points = []

        # 1. 기술 역량 승점 (전략 타입에 따라 가중치 조정)
        tech_point = await self._evaluate_technical_winning_point(
            rfp_analysis, company_profile, competitors, strategy_type
        )
        winning_points.append(tech_point)

        # 2. 실적 기반 승점 (Defence 전략에서 더 중요)
        performance_point = await self._evaluate_performance_winning_point(
            past_proposals, rfp_analysis, strategy_type
        )
        winning_points.append(performance_point)

        # 3. 가격 경쟁력 승점 (Offence 전략에서 더 중요)
        price_point = await self._evaluate_price_winning_point(
            company_profile, competitors, strategy_type
        )
        winning_points.append(price_point)

        # 4. 혁신성 승점 (Offence 전략에서 더 중요)
        innovation_point = await self._evaluate_innovation_winning_point(
            rfp_analysis, company_profile, strategy_type
        )
        winning_points.append(innovation_point)

        # 5. 관계성 승점
        relationship_point = await self._evaluate_relationship_winning_point(
            company_profile, rfp_analysis, strategy_type
        )
        winning_points.append(relationship_point)

        # 6. 준수성 승점
        compliance_point = await self._evaluate_compliance_winning_point(
            rfp_analysis, company_profile, strategy_type
        )
        winning_points.append(compliance_point)

        return winning_points

    async def _evaluate_technical_winning_point(self, rfp: Dict, company: Dict,
                                              competitors: List[CompetitiveAnalysis],
                                              strategy_type: str) -> WinningPoint:
        """기술 역량 승점 평가 (전략 타입 고려, 평가기준 세분화 적용)"""

        # RFP 요구사항 분석
        required_tech = rfp["requirements"].get("technical_requirements", [])

        # 회사 기술 역량
        company_tech = company.get("technology_stack", [])
        company_expertise = company.get("expertise_areas", [])

        # 경쟁사 기술 역량 비교
        competitor_avg_tech = sum(c.strength_score for c in competitors) / len(competitors) if competitors else 0.5

        # 상대적 우위 계산
        our_tech_score = len(set(required_tech) & set(company_tech + company_expertise)) / len(required_tech) if required_tech else 1.0
        relative_advantage = our_tech_score - competitor_avg_tech

        # === 세부 평가 항목별 점수 계산 (100점 기준) ===
        detailed_scores = {
            "기술 혁신성": min(100, company.get("innovation_capability", 0.5) * 100 * (1 + relative_advantage * 0.5)),
            "구현 가능성": our_tech_score * 100,
            "유사 실적": company.get("past_performance_score", 0.5) * 100,
            "기술 팀 역량": company.get("team_capacity", 0.5) * 100 if "team_capacity" in company else 75,
            "제안 품질": 75  # 기본값 (실제로는 제안서 품질 분석 필요)
        }
        
        # 가중치 적용 (평가기준 반영)
        weighted_technical_score = (
            detailed_scores["기술 혁신성"] * 0.25 +
            detailed_scores["구현 가능성"] * 0.25 +
            detailed_scores["유사 실적"] * 0.25 +
            detailed_scores["기술 팀 역량"] * 0.15 +
            detailed_scores["제안 품질"] * 0.10
        )

        # 0.0~1.0 범위로 정규화
        tech_score_normalized = min(1.0, weighted_technical_score / 100.0)

        # 전략 타입에 따른 점수 조정
        if strategy_type == "defence":
            # Defence: 기술 우위가 확실할 때 더 높은 점수
            score = max(0, min(1, 0.6 + relative_advantage))
            strategy_note = "기술 강점 분야 - 방어 전략 강화"
        elif strategy_type == "offence":
            # Offence: 기술 격차가 크더라도 혁신으로 극복 가능
            score = max(0, min(1, 0.4 + relative_advantage))
            strategy_note = "기술 열세 분야 - 혁신으로 차별화"
        else:  # balanced
            score = max(0, min(1, 0.5 + relative_advantage))
            strategy_note = "균형 전략 적용"

        # 최종 점수는 세부 항목 점수와 전략 점수의 혼합
        final_score = (tech_score_normalized * 0.6) + (score * 0.4)

        # 영향도 (평가기준 가중치 반영)
        impact = rfp["evaluation_criteria"].get("weights", {}).get("기술성", 0.4)

        # 평가 근거
        evidence = []
        if our_tech_score > 0.8:
            evidence.append("요구 기술 80% 이상 보유")
        if relative_advantage > 0.2:
            evidence.append("경쟁사 대비 기술 우위")
        
        # 세부 항목별 최대점 달성 현황
        gap_analysis = []
        for criterion, score_val in detailed_scores.items():
            gap = (100 - score_val) / 100
            if gap > 0.15:  # 15% 이상 차이나는 항목만 표시
                gap_analysis.append(f"{criterion}: {score_val:.0f}점 (개선 여지: {gap:.0%})")

        return WinningPoint(
            factor="기술 역량",
            score=final_score,
            impact=impact,
            description=f"세부 평가: 기술혁신({detailed_scores['기술 혁신성']:.0f}), 구현가능({detailed_scores['구현 가능성']:.0f}), 유사실적({detailed_scores['유사 실적']:.0f}), 팀역량({detailed_scores['기술 팀 역량']:.0f}), 제안품질({detailed_scores['제안 품질']:.0f})",
            evidence=evidence + gap_analysis
        )

    async def _evaluate_performance_winning_point(self, past_proposals: List[Dict],
                                                rfp: Dict, strategy_type: str) -> WinningPoint:
        """실적 기반 승점 평가 (전략 타입 고려)"""

        # 유사 프로젝트 실적 분석
        similar_projects = self._find_similar_projects(past_proposals, rfp)
        success_rate = self._calculate_success_rate(similar_projects)

        # 실적 풍부성
        performance_volume = len(similar_projects)

        # RFP 평가기준에서 실적 가중치
        performance_weight = rfp["evaluation_criteria"].get("weights", {}).get("실적", 0.2)

        # 전략 타입에 따른 점수 조정
        if strategy_type == "defence":
            # Defence: 실적 강점이 핵심 경쟁력
            score = min(1.0, (success_rate * 0.8) + (min(performance_volume / 3, 1.0) * 0.2))
            strategy_note = "실적 강점 분야 - 방어 전략 강화"
        elif strategy_type == "offence":
            # Offence: 실적 부족을 혁신/가격으로 극복
            score = min(1.0, (success_rate * 0.5) + (min(performance_volume / 10, 1.0) * 0.5))
            strategy_note = "실적 열세 분야 - 혁신으로 차별화"
        else:  # balanced
            score = min(1.0, (success_rate * 0.7) + (min(performance_volume / 5, 1.0) * 0.3))
            strategy_note = "균형 전략 적용"

        evidence = []
        if success_rate > 0.8:
            evidence.append("유사 사업 성공률 80% 이상")
        if performance_volume >= 3:
            evidence.append("3건 이상 유사 실적 보유")

        return WinningPoint(
            factor="과거 실적",
            score=score,
            impact=performance_weight,
            description=f"유사 사업 {performance_volume}건, 성공률: {success_rate:.1%}",
            evidence=evidence
        )

    async def _evaluate_price_winning_point(self, company: Dict,
                                          competitors: List[CompetitiveAnalysis],
                                          strategy_type: str) -> WinningPoint:
        """가격 경쟁력 승점 평가 (전략 타입 고려)"""

        # 회사 가격 경쟁력
        company_cost_efficiency = company.get("cost_efficiency_score", 0.7)

        # 경쟁사 가격 분석
        competitor_prices = [c.estimated_price for c in competitors if c.estimated_price]
        avg_competitor_price = sum(competitor_prices) / len(competitor_prices) if competitor_prices else 100

        # 상대적 가격 경쟁력
        our_price_advantage = company_cost_efficiency - (avg_competitor_price / 100)

        # 전략 타입에 따른 점수 조정
        if strategy_type == "defence":
            # Defence: 가격보다는 품질/실적으로 승부
            score = max(0, min(1, 0.4 + our_price_advantage))
            strategy_note = "가격보다는 품질/실적 강점 강조"
        elif strategy_type == "offence":
            # Offence: 가격 경쟁력이 핵심 차별화 요소
            score = max(0, min(1, 0.6 + our_price_advantage))
            strategy_note = "가격 경쟁력으로 시장 진입"
        else:  # balanced
            score = max(0, min(1, 0.5 + our_price_advantage))
            strategy_note = "균형 가격 전략"

        evidence = []
        if company_cost_efficiency > 0.8:
            evidence.append("낮은 원가 구조 보유")
        if our_price_advantage > 0.1:
            evidence.append("경쟁사 대비 가격 경쟁력 우위")

        return WinningPoint(
            factor="가격 경쟁력",
            score=score,
            impact=0.3,  # 일반적인 가격 가중치
            description=f"원가 효율성: {company_cost_efficiency:.1%}",
            evidence=evidence
        )

    async def _evaluate_innovation_winning_point(self, rfp: Dict, company: Dict,
                                               strategy_type: str) -> WinningPoint:
        """혁신성 승점 평가 (전략 타입 고려)"""

        # RFP 혁신 요구사항 분석
        innovation_keywords = ["혁신", "신기술", "첨단", "AI", "빅데이터", "클라우드"]
        rfp_text = str(rfp).lower()
        innovation_required = any(keyword in rfp_text for keyword in innovation_keywords)

        # 회사 혁신 역량
        company_innovation = company.get("innovation_capability", 0.6)
        company_rnd_investment = company.get("rnd_investment_ratio", 0.05)

        # 전략 타입에 따른 점수 조정
        if strategy_type == "defence":
            # Defence: 혁신보다는 안정성/실적 강조
            if innovation_required:
                score = (company_innovation * 0.6) + (company_rnd_investment * 10 * 0.4)
                score = min(1.0, score)
            else:
                score = 0.5
            strategy_note = "안정성 중심 - 혁신보다는 실적 강조"
        elif strategy_type == "offence":
            # Offence: 혁신성이 핵심 차별화 요소
            if innovation_required:
                score = (company_innovation * 0.8) + (company_rnd_investment * 10 * 0.2)
                score = min(1.0, score)
            else:
                score = 0.6  # 혁신 요구가 없어도 혁신으로 차별화
            strategy_note = "혁신성으로 시장 진입"
        else:  # balanced
            if innovation_required:
                score = (company_innovation * 0.7) + (company_rnd_investment * 10 * 0.3)
                score = min(1.0, score)
            else:
                score = 0.5
            strategy_note = "균형 혁신 전략"

        evidence = []
        if company_rnd_investment > 0.03:
            evidence.append("R&D 투자비율 3% 이상")
        if company_innovation > 0.7:
            evidence.append("혁신 역량 우수")

        return WinningPoint(
            factor="혁신성",
            score=score,
            impact=0.15 if innovation_required else 0.05,
            description=f"혁신 요구사항: {'있음' if innovation_required else '없음'}, 혁신 역량: {company_innovation:.1%}",
            evidence=evidence
        )

    async def _evaluate_relationship_winning_point(self, company: Dict, rfp: Dict, strategy_type: str) -> WinningPoint:
        """관계성 승점 평가 (전략 타입 고려)"""

        # 발주처 관계 분석
        client_name = rfp["basic_info"].get("client", "")
        past_relationships = company.get("client_relationships", [])

        relationship_score = 0.0
        for relationship in past_relationships:
            if client_name in relationship.get("client", ""):
                relationship_score = relationship.get("strength", 0.5)
                break

        # 전략 타입에 따른 점수 조정
        if strategy_type == "defence":
            # Defence: 기존 관계가 핵심 경쟁력
            if relationship_score == 0.0:
                relationship_score = 0.2  # 관계 없음 페널티
            strategy_note = "기존 관계 활용 - 방어 전략 강화"
        elif strategy_type == "offence":
            # Offence: 관계 구축 기회로 활용
            if relationship_score == 0.0:
                relationship_score = 0.4  # 관계 구축 가능성 반영
            strategy_note = "관계 구축으로 시장 진입"
        else:  # balanced
            if relationship_score == 0.0:
                relationship_score = 0.3  # 기본 점수
            strategy_note = "균형 관계 전략"

        evidence = []
        if relationship_score > 0.7:
            evidence.append("발주처와 강한 관계 보유")
        elif relationship_score > 0.5:
            evidence.append("발주처와 기존 관계 있음")

        return WinningPoint(
            factor="관계성",
            score=relationship_score,
            impact=0.1,
            description=f"발주처 관계 강도: {relationship_score:.1%}",
            evidence=evidence
        )

    async def _evaluate_compliance_winning_point(self, rfp: Dict, company: Dict,
                                               strategy_type: str) -> WinningPoint:
        """준수성 승점 평가 (전략 타입 고려)"""

        # 자격 요건 준수도
        required_qualifications = rfp["requirements"].get("qualification_requirements", [])
        company_qualifications = company.get("qualifications", [])

        compliance_score = len(set(required_qualifications) & set(company_qualifications))
        compliance_score = compliance_score / len(required_qualifications) if required_qualifications else 1.0

        # 전략 타입에 따른 점수 조정 (준수성은 필수이므로 큰 차이는 없음)
        if strategy_type == "defence":
            # Defence: 준수성이 기본 전제
            strategy_note = "준수성 확보 - 방어 전략 기반"
        elif strategy_type == "offence":
            # Offence: 준수성 부족 시 다른 요소로 보완 가능성 고려
            if compliance_score < 0.8:
                compliance_score = max(compliance_score, 0.6)  # 최소 점수 보장
            strategy_note = "준수성 보완 - 혁신으로 극복"
        else:  # balanced
            strategy_note = "균형 준수 전략"

        evidence = []
        if compliance_score > 0.9:
            evidence.append("자격 요건 90% 이상 충족")
        elif compliance_score > 0.7:
            evidence.append("자격 요건 대부분 충족")

        return WinningPoint(
            factor="준수성",
            score=compliance_score,
            impact=0.1,
            description=f"자격 요건 준수율: {compliance_score:.1%}",
            evidence=evidence
        )

    def _determine_strategy_priorities(self, winning_points: List[WinningPoint],
                                     company_profile: Dict,
                                     competitors: List[CompetitiveAnalysis],
                                     strategy_analysis: Dict) -> List[WinningStrategy]:
        """전략 우선순위 결정 (defence/offence 고려)"""

        # 승점 기반 전략 매핑
        # 승점 기반 전략 매핑
        strategy_scores = {
            WinningStrategy.TECHNICAL_SUPERIORITY: 0.0,
            WinningStrategy.COST_LEADERSHIP: 0.0,
            WinningStrategy.OFFENCE_INNOVATION: 0.0,
            WinningStrategy.PARTNERSHIP: 0.0,
            WinningStrategy.DEFENCE_TRACK_RECORD: 0.0,
            WinningStrategy.OFFENCE_AGGRESSIVE_PRICING: 0.0
        }

        # 전략 타입에 따른 가중치 조정
        strategy_type = strategy_analysis.get("strategy_type", "balanced")

        # 승점 요소 추출
        tech_point = next((p for p in winning_points if p.factor == "기술 역량"), None)
        performance_point = next((p for p in winning_points if p.factor == "과거 실적"), None)
        price_point = next((p for p in winning_points if p.factor == "가격 경쟁력"), None)
        innovation_point = next((p for p in winning_points if p.factor == "혁신성"), None)
        relationship_point = next((p for p in winning_points if p.factor == "관계성"), None)

        # Defence 전략: 실적/기술 중심 전략 우선
        if strategy_type == "defence":
            if tech_point:
                strategy_scores[WinningStrategy.TECHNICAL_SUPERIORITY] += tech_point.score * 1.3
            if performance_point:
                strategy_scores[WinningStrategy.DEFENCE_TRACK_RECORD] += performance_point.score * 1.2

        # Offence 전략: 혁신/가격 중심 전략 우선
        elif strategy_type == "offence":
            if innovation_point:
                strategy_scores[WinningStrategy.OFFENCE_INNOVATION] += innovation_point.score * 1.3
            if price_point:
                strategy_scores[WinningStrategy.OFFENCE_AGGRESSIVE_PRICING] += price_point.score * 1.2

        # Balanced 전략: 균형 잡힌 접근
        else:
            if tech_point and tech_point.score > 0.7:
                strategy_scores[WinningStrategy.TECHNICAL_SUPERIORITY] += tech_point.score
            if price_point and price_point.score > 0.7:
                strategy_scores[WinningStrategy.COST_LEADERSHIP] += price_point.score
            if innovation_point and innovation_point.score > 0.7:
                strategy_scores[WinningStrategy.OFFENCE_INNOVATION] += innovation_point.score

        # 전략 우선순위 정렬
        sorted_strategies = sorted(
            strategy_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [strategy for strategy, score in sorted_strategies if score > 0]

    async def _develop_pricing_strategy(self, rfp_analysis: Dict,
                                      competitors: List[CompetitiveAnalysis],
                                      company_profile: Dict, strategy_analysis: Dict) -> Dict:
        """가격 전략 수립 (defence/offence 고려)"""

        budget = rfp_analysis["basic_info"].get("budget", 0)
        evaluation_weights = rfp_analysis["evaluation_criteria"].get("weights", {})

        # 가격 가중치 확인
        price_weight = evaluation_weights.get("가격", 0.3)

        # 경쟁사 가격 분석
        competitor_prices = [c.estimated_price for c in competitors if c.estimated_price]
        market_avg_price = sum(competitor_prices) / len(competitor_prices) if competitor_prices else budget

        # 회사 가격 경쟁력
        cost_efficiency = company_profile.get("cost_efficiency_score", 0.7)

        # 전략 타입에 따른 가격 전략 조정
        strategy_type = strategy_analysis.get("strategy_type", "balanced")

        # Defence 전략: 안정적 가격 책정 (품질/실적 강조)
        if strategy_type == "defence":
            if cost_efficiency > 0.7:
                strategy = PriceStrategy.VALUE_BASED  # 가치 기반 가격
                price_range = (int(market_avg_price * 0.95), int(market_avg_price * 1.05))
            else:
                strategy = PriceStrategy.COMPETITIVE  # 경쟁 가격
                price_range = (int(market_avg_price * 0.92), int(market_avg_price * 0.98))

        # Offence 전략: 공격적 가격 책정 (시장 진입 우선)
        elif strategy_type == "offence":
            if cost_efficiency > 0.8:
                strategy = PriceStrategy.PENETRATION  # 시장 침투 가격
                price_range = (int(market_avg_price * 0.85), int(market_avg_price * 0.92))
            else:
                strategy = PriceStrategy.COMPETITIVE  # 경쟁 가격 (최소한의 마진 확보)
                price_range = (int(market_avg_price * 0.88), int(market_avg_price * 0.95))

        # Balanced 전략: 기존 로직 적용
        else:
            if price_weight > 0.4:  # 가격이 중요한 평가 요소
                if cost_efficiency > 0.8:  # 원가 경쟁력이 우수
                    strategy = PriceStrategy.COMPETITIVE
                    price_range = (int(market_avg_price * 0.9), int(market_avg_price * 0.95))
                else:
                    strategy = PriceStrategy.VALUE_BASED
                    price_range = (int(market_avg_price * 0.95), int(market_avg_price * 1.05))
            elif budget > 100000000:  # 고예산 사업
                strategy = PriceStrategy.SKIMMING
                price_range = (int(budget * 0.8), int(budget * 0.9))
            else:  # 일반 사업
                strategy = PriceStrategy.COST_PLUS
                price_range = (int(budget * 0.7), int(budget * 0.8))

        return {
            "strategy": strategy,
            "price_range": price_range,
            "market_avg": market_avg_price,
            "justification": f"가격 가중치: {price_weight:.1%}, 원가 효율성: {cost_efficiency:.1%}"
        }

    def _identify_competitive_advantages(self, company_profile: Dict,
                                       competitors: List[CompetitiveAnalysis],
                                       strategy_analysis: Dict) -> List[str]:
        """경쟁 우위 요소 식별"""

        advantages = []
        strategy_type = strategy_analysis.get("strategy_type", "defence")

        # Defence 전략: 안정성과 실적 중심
        if strategy_type == "defence":
            # 실적 우위
            if company_profile.get("past_performance_score", 0) > 0.7:
                advantages.append("풍부한 유사 사업 실적")

            # 안정성 우위
            if company_profile.get("stability_score", 0) > 0.8:
                advantages.append("안정적인 사업 수행 역량")

            # 신뢰성 우위
            if company_profile.get("reliability_score", 0) > 0.8:
                advantages.append("높은 고객 만족도 및 신뢰성")

        # Offence 전략: 혁신과 가격 중심
        else:
            # 혁신 역량
            if company_profile.get("innovation_capability", 0) > 0.7:
                advantages.append("높은 혁신 개발 역량")

            # 가격 경쟁력
            if company_profile.get("cost_efficiency_score", 0) > 0.8:
                advantages.append("효율적인 비용 관리 체계")

            # 기술 우위
            if company_profile.get("technology_stack"):
                advantages.append("첨단 기술 스택 보유")

        # 공통 우위 요소
        # 시장 점유율
        if company_profile.get("market_share", 0) > 0.3:
            advantages.append("시장 리더십 및 점유율 우위")

        return advantages

    def _develop_risk_mitigation_plan(self, rfp_analysis: Dict,
                                    primary_strategy: WinningStrategy,
                                    strategy_analysis: Dict) -> List[str]:
        """리스크 완화 계획 수립"""

        mitigations = []

        # 전략별 리스크 완화
        if primary_strategy == WinningStrategy.TECHNICAL_SUPERIORITY:
            mitigations.extend([
                "기술 검증 테스트 실시",
                "기술 전문가 확보",
                "기술 리스크 보험 검토"
            ])

        elif primary_strategy == WinningStrategy.COST_LEADERSHIP:
            mitigations.extend([
                "원가 분석 정확성 검증",
                "가격 변동 리스크 관리",
                "수익성 모니터링 체계 구축"
            ])

        elif primary_strategy == WinningStrategy.OFFENCE_DIFFERENTIATION:
            mitigations.extend([
                "차별화 포인트 검증",
                "시장 수용성 테스트",
                "지적재산권 보호"
            ])

        # 공통 리스크 완화
        risk_factors = rfp_analysis.get("risk_factors", [])
        if risk_factors:
            mitigations.append("식별된 리스크 요인별 대응 방안 수립")

        return mitigations

    def _create_action_items(self, primary_strategy: WinningStrategy,
                           price_strategy: Dict, strategy_analysis: Dict) -> List[str]:
        """실행 항목 생성"""

        actions = []

        # 전략별 액션 아이템
        if primary_strategy == WinningStrategy.TECHNICAL_SUPERIORITY:
            actions.extend([
                "기술 아키텍처 설계 완료",
                "기술 검증 프로토타입 개발",
                "기술 전문가 팀 구성"
            ])

        elif primary_strategy == WinningStrategy.COST_LEADERSHIP:
            actions.extend([
                "원가 분석 및 가격 결정",
                "원가 절감 방안 수립",
                "가격 전략 검증"
            ])

        elif primary_strategy == WinningStrategy.OFFENCE_DIFFERENTIATION:
            actions.extend([
                "차별화 포인트 구체화",
                "고객 니즈 검증",
                "마케팅 전략 수립"
            ])

        # 가격 전략 관련 액션
        price_range = price_strategy["price_range"]
        actions.append(f"목표 가격 범위 설정: {price_range[0]:,}원 ~ {price_range[1]:,}원")

        return actions

    # 헬퍼 메소드들
    def _assess_competitor_strength(self, competitor_data: Dict, rfp: Dict) -> float:
        """경쟁사 강점 평가"""
        # 예시 구현
        return competitor_data.get("strength_score", 0.6)

    def _assess_competitor_weakness(self, competitor_data: Dict, rfp: Dict) -> float:
        """경쟁사 약점 평가"""
        # 예시 구현
        return competitor_data.get("weakness_score", 0.4)

    def _create_default_competitor_analysis(self, rfp: Dict) -> CompetitiveAnalysis:
        """기본 경쟁사 분석 생성"""
        return CompetitiveAnalysis(
            competitor_name="시장 평균",
            strength_score=0.6,
            weakness_score=0.4,
            estimated_price=rfp["basic_info"].get("budget", 100000000),
            key_differentiators=["가격", "실적"]
        )

    def _find_similar_projects(self, past_proposals: List[Dict], rfp: Dict) -> List[Dict]:
        """유사 프로젝트 찾기"""
        category = rfp["basic_info"].get("category", "")
        return [p for p in past_proposals if p.get("category") == category]

    def _calculate_success_rate(self, projects: List[Dict]) -> float:
        """성공률 계산"""
        if not projects:
            return 0.0
        won_projects = sum(1 for p in projects if p.get("result") == "won")
        return won_projects / len(projects)