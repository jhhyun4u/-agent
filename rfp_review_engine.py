"""
RFP 검토 모듈 상세 구현
GO/STOP 결정 알고리즘 및 포기 사유 정리
"""

from typing import Dict, List, Any, Tuple
import re
from dataclasses import dataclass
from enum import Enum

class FeasibilityLevel(Enum):
    EXCELLENT = "excellent"      # 0.9-1.0
    GOOD = "good"               # 0.8-0.9
    MODERATE = "moderate"       # 0.6-0.8
    POOR = "poor"              # 0.4-0.6
    CRITICAL = "critical"      # 0.0-0.4

class DecisionType(Enum):
    GO = "GO"
    CONDITIONAL_GO = "CONDITIONAL_GO"
    STOP = "STOP"

@dataclass
class FeasibilityFactor:
    """수행 가능성 평가 요소"""
    name: str
    score: float  # 0.0 ~ 1.0
    weight: float  # 가중치
    reasoning: str
    recommendations: List[str]

@dataclass
class EvaluationCriterionDetail:
    """평가 기준 세부 항목"""
    name: str  # 예: "기술 혁신성"
    max_score: float  # 이 항목의 배점
    weight: float  # 상위 항목 내 가중치
    assessment_method: str  # 평가 방법
    examples: List[str]  # 사회 사례

@dataclass
class DetailedEvaluationCriteria:
    """상세화된 평가 기준"""
    criterion_name: str  # 예: "기술성"
    total_score: float  # 전체 배점
    weight_in_total: float  # 전체 평가에서의 비중
    details: List[EvaluationCriterionDetail]  # 세부 항목들
    evaluation_method: str  # 평가 방법

@dataclass
class TechnicalScoreOptimization:
    """기술성 점수 최적화 가이드"""
    current_score: float  # 현재 예상 점수
    max_possible_score: float  # 최대 가능 점수
    gap: float  # 차이 (0.0~1.0)
    priority_improvements: List[Dict]  # [{항목, 현재_점수, 목표_점수, 개선_방법}]
    evidence_requirements: List[str]  # 필요 증거
    win_probability: float  # 승률 추정

@dataclass
class RFPReviewResult:
    """RFP 검토 결과"""
    decision: DecisionType
    feasibility_score: float
    feasibility_level: FeasibilityLevel
    factors: List[FeasibilityFactor]
    reasoning: str
    action_plan: List[str]

class RFPReviewEngine:
    """RFP 검토 및 GO/STOP 결정 엔진"""

    def __init__(self):
        self.weights = {
            "technical_feasibility": 0.3,
            "qualification_compliance": 0.25,
            "market_competitiveness": 0.2,
            "financial_viability": 0.15,
            "risk_assessment": 0.1
        }

    async def review_rfp(self, rfp_content: str, company_profile: Dict,
                        past_proposals: List[Dict]) -> RFPReviewResult:
        """
        RFP 종합 검토 및 GO/STOP 결정

        Args:
            rfp_content: RFP 원문 텍스트
            company_profile: 회사 프로필 정보
            past_proposals: 과거 제안 실적

        Returns:
            RFPReviewResult: 검토 결과 및 결정
        """

        # RFP 분석
        rfp_analysis = await self._analyze_rfp_content(rfp_content)

        # 각 요소별 수행 가능성 평가
        factors = await self._evaluate_all_factors(rfp_analysis, company_profile, past_proposals)

        # 종합 점수 계산
        feasibility_score = self._calculate_weighted_score(factors)

        # 의사결정
        decision = self._make_decision(feasibility_score, factors)

        # 결과 생성
        result = RFPReviewResult(
            decision=decision,
            feasibility_score=feasibility_score,
            feasibility_level=self._get_feasibility_level(feasibility_score),
            factors=factors,
            reasoning=self._generate_reasoning(feasibility_score, factors, decision),
            action_plan=self._create_action_plan(decision, factors)
        )

        return result

    async def _analyze_rfp_content(self, rfp_content: str) -> Dict[str, Any]:
        """RFP 내용 심층 분석"""
        analysis = {
            "basic_info": {},
            "requirements": {},
            "constraints": {},
            "evaluation_criteria": {},
            "risk_factors": []
        }

        # 기본 정보 추출
        analysis["basic_info"] = self._extract_basic_info(rfp_content)

        # 요구사항 분석
        analysis["requirements"] = self._analyze_requirements(rfp_content)

        # 제약사항 분석
        analysis["constraints"] = self._analyze_constraints(rfp_content)

        # 평가기준 분석
        analysis["evaluation_criteria"] = self._analyze_evaluation_criteria(rfp_content)

        # 리스크 요인 식별
        analysis["risk_factors"] = self._identify_risk_factors(rfp_content)

        return analysis

    def _extract_basic_info(self, content: str) -> Dict[str, Any]:
        """기본 정보 추출"""
        return {
            "title": self._extract_pattern(content, r"사업명[:\s]*([^\n]+)"),
            "client": self._extract_pattern(content, r"발주처[:\s]*([^\n]+)"),
            "budget": self._extract_budget(content),
            "duration": self._extract_duration(content),
            "category": self._classify_project_category(content)
        }

    def _analyze_requirements(self, content: str) -> Dict[str, Any]:
        """요구사항 분석"""
        return {
            "technical_requirements": self._extract_technical_reqs(content),
            "functional_requirements": self._extract_functional_reqs(content),
            "qualification_requirements": self._extract_qualification_reqs(content),
            "compliance_requirements": self._extract_compliance_reqs(content)
        }

    def _analyze_constraints(self, content: str) -> Dict[str, Any]:
        """제약사항 분석"""
        return {
            "timeline_constraints": self._extract_timeline_constraints(content),
            "budget_constraints": self._extract_budget_constraints(content),
            "resource_constraints": self._extract_resource_constraints(content),
            "technical_constraints": self._extract_technical_constraints(content)
        }

    def _analyze_evaluation_criteria(self, content: str) -> Dict[str, Any]:
        """평가기준 분석"""
        return {
            "criteria": self._extract_evaluation_criteria(content),
            "weights": self._extract_criteria_weights(content),
            "scoring_method": self._determine_scoring_method(content)
        }

    def _identify_risk_factors(self, content: str) -> List[str]:
        """리스크 요인 식별"""
        risk_keywords = [
            "긴급", "단기", "초단기", "즉시", "시급",
            "고난도", "첨단", "혁신", "신기술",
            "경쟁심화", "입찰률높음", "경쟁률높음",
            "제한적", "한정적", "특별한",
            "변경가능성", "요구사항변경"
        ]

        found_risks = []
        content_lower = content.lower()

        for keyword in risk_keywords:
            if keyword in content_lower:
                found_risks.append(f"{keyword} 관련 리스크")

        return list(set(found_risks))  # 중복 제거

    async def _evaluate_all_factors(self, rfp_analysis: Dict, company_profile: Dict,
                                  past_proposals: List[Dict]) -> List[FeasibilityFactor]:
        """모든 수행 가능성 요소 평가"""

        factors = []

        # 1. 기술적 수행 가능성
        tech_factor = await self._evaluate_technical_feasibility(
            rfp_analysis, company_profile, past_proposals
        )
        factors.append(tech_factor)

        # 2. 자격 요건 준수
        qual_factor = await self._evaluate_qualification_compliance(
            rfp_analysis, company_profile
        )
        factors.append(qual_factor)

        # 3. 시장 경쟁력
        market_factor = await self._evaluate_market_competitiveness(
            rfp_analysis, past_proposals
        )
        factors.append(market_factor)

        # 4. 재무적 타당성
        financial_factor = await self._evaluate_financial_viability(
            rfp_analysis, company_profile
        )
        factors.append(financial_factor)

        # 5. 리스크 평가
        risk_factor = await self._evaluate_risk_assessment(rfp_analysis)
        factors.append(risk_factor)

        return factors

    async def _evaluate_technical_feasibility(self, rfp: Dict, company: Dict,
                                            past_proposals: List) -> FeasibilityFactor:
        """기술적 수행 가능성 평가"""

        # 회사 기술 역량 분석
        company_tech_stack = company.get("technology_stack", [])
        company_expertise = company.get("expertise_areas", [])

        # RFP 요구 기술 분석
        required_tech = rfp["requirements"].get("technical_requirements", [])

        # 매칭도 계산
        tech_match_score = self._calculate_technology_match(
            required_tech, company_tech_stack, company_expertise
        )

        # 과거 실적 분석
        similar_projects = self._find_similar_projects(past_proposals, rfp)
        experience_score = len(similar_projects) / max(len(past_proposals), 1)

        # 종합 점수
        final_score = (tech_match_score * 0.7) + (experience_score * 0.3)

        # 추천사항 생성
        recommendations = []
        if tech_match_score < 0.7:
            recommendations.append("기술 파트너십 또는 외주 고려")
        if experience_score < 0.5:
            recommendations.append("유사 프로젝트 경험 축적 필요")

        return FeasibilityFactor(
            name="기술적 수행 가능성",
            score=min(final_score, 1.0),
            weight=self.weights["technical_feasibility"],
            reasoning=f"기술 매칭도: {tech_match_score:.2f}, 경험 점수: {experience_score:.2f}",
            recommendations=recommendations
        )

    async def analyze_technical_scoring_optimization(self, rfp: Dict, company: Dict,
                                                    past_proposals: List) -> TechnicalScoreOptimization:
        """기술성 평가 점수 최적화 분석
        
        RFP의 평가항목과 기준을 분석하여 기술성 점수의 최대치 달성 방법 제시
        """
        
        # 상세 평가 기준 파싱
        detailed_criteria = await self._parse_detailed_evaluation_criteria(rfp)
        
        # 현재 기술성 점수 계산
        current_score = await self._calculate_detailed_technical_score(
            rfp, company, past_proposals, detailed_criteria
        )
        
        # 최대 가능 점수 (모든 세부 항목 만점)
        max_score = detailed_criteria.total_score
        
        # 점수 차이 (정규화)
        gap = (max_score - current_score) / max_score if max_score > 0 else 0
        
        # 우선순위별 개선 방안
        priority_improvements = await self._identify_priority_improvements(
            rfp, company, detailed_criteria, current_score
        )
        
        # 필요한 증거 및 보강자료
        evidence_requirements = self._identify_evidence_requirements(
            detailed_criteria, company
        )
        
        # 승률 추정
        win_probability = self._estimate_win_probability(current_score, max_score)
        
        return TechnicalScoreOptimization(
            current_score=current_score,
            max_possible_score=max_score,
            gap=gap,
            priority_improvements=priority_improvements,
            evidence_requirements=evidence_requirements,
            win_probability=win_probability
        )

    async def _parse_detailed_evaluation_criteria(self, rfp: Dict) -> DetailedEvaluationCriteria:
        """RFP 평가 기준 세부 항목 파싱"""
        
        # RFP 평가 기준 추출
        eval_criteria = rfp.get("evaluation_criteria", {})
        
        # 기술성 기준 찾기
        technical_weight = eval_criteria.get("weights", {}).get("기술성", 0.4)
        
        # 세부 평가 항목 구성 (RFP 분석 또는 기본값)
        details = [
            EvaluationCriterionDetail(
                name="기술 혁신성",
                max_score=25,
                weight=0.3,
                assessment_method="제안한 기술의 혁신 수준과 경쟁사 대비 우위 평가",
                examples=["AI/머신러닝 활용", "차세대 기술 적용", "자체 기술 개발"]
            ),
            EvaluationCriterionDetail(
                name="구현 가능성",
                max_score=20,
                weight=0.25,
                assessment_method="제안 기술의 실현 가능성과 리스크 관리 방안 평가",
                examples=["상세한 구현 계획", "리스크 완화 전략", "기술 검증 방법"]
            ),
            EvaluationCriterionDetail(
                name="유사 실적",
                max_score=20,
                weight=0.25,
                assessment_method="해당 분야 유사 사업 수행 경험",
                examples=["동일 분류 프로젝트", "고객 만족도", "성공 사례"]
            ),
            EvaluationCriterionDetail(
                name="기술 팀 역량",
                max_score=20,
                weight=0.15,
                assessment_method="기술진의 경력과 전문성",
                examples=["관련 학위/자격", "업계 경력", "논문/특허"]
            ),
            EvaluationCriterionDetail(
                name="제안 품질",
                max_score=15,
                weight=0.05,
                assessment_method="기술제안서의 명확성과 완성도",
                examples=["논리적 구성", "시각화", "상세도"]
            ),
        ]
        
        return DetailedEvaluationCriteria(
            criterion_name="기술성",
            total_score=sum(d.max_score for d in details),
            weight_in_total=technical_weight,
            details=details,
            evaluation_method="기술 혁신성, 구현 가능성, 유사 실적, 팀 역량, 제안 품질을 종합 평가"
        )

    async def _calculate_detailed_technical_score(self, rfp: Dict, company: Dict,
                                                past_proposals: List,
                                                criteria: DetailedEvaluationCriteria) -> float:
        """세부 항목별 기술성 점수 계산"""
        
        company_tech_stack = company.get("technology_stack", [])
        company_expertise = company.get("expertise_areas", [])
        required_tech = rfp.get("requirements", {}).get("technical_requirements", [])
        
        scores = {}
        
        # 1. 기술 혁신성 (기본점 50% + 경쟁사 대비 우위 50%)
        innovation_score = company.get("innovation_capability", 0.5) * 0.5
        if set(company_tech_stack) & {"AI", "ML", "빅데이터", "클라우드", "IoT", "블록체인"}:
            innovation_score += 0.25  # 차세대 기술 보유
        scores["기술 혁신성"] = min(1.0, innovation_score) * criteria.details[0].max_score
        
        # 2. 구현 가능성 (기술 매칭도 기반)
        tech_match_score = self._calculate_technology_match(
            required_tech, company_tech_stack, company_expertise
        )
        scores["구현 가능성"] = tech_match_score * criteria.details[1].max_score
        
        # 3. 유사 실적 (과거 프로젝트 경험도)
        similar_projects = self._find_similar_projects(past_proposals, rfp)
        experience_score = min(1.0, len(similar_projects) / max(5, len(past_proposals)))
        scores["유사 실적"] = experience_score * criteria.details[2].max_score
        
        # 4. 기술 팀 역량 (직원 수와 자격 기반 추정)
        team_capacity = company.get("team_capacity", 0.5)
        team_cert_score = company.get("technical_certifications", 0.5)
        scores["기술 팀 역량"] = (team_capacity * 0.6 + team_cert_score * 0.4) * criteria.details[3].max_score
        
        # 5. 제안 품질 (기본값 - 실제로는 제안서 분석 필요)
        quality_score = 0.75  # 기본 추정값
        scores["제안 품질"] = quality_score * criteria.details[4].max_score
        
        # 총점
        total_score = sum(scores.values())
        return min(total_score, criteria.total_score)

    async def _identify_priority_improvements(self, rfp: Dict, company: Dict,
                                            criteria: DetailedEvaluationCriteria,
                                            current_score: float) -> List[Dict]:
        """우선순위별 개선 방안 식별"""
        
        improvements = []
        company_tech_stack = company.get("technology_stack", [])
        current_score_pct = (current_score / criteria.total_score) * 100
        
        for detail in criteria.details:
            # 각 세부 항목의 현재 점수 추정
            if detail.name == "기술 혁신성":
                item_score = company.get("innovation_capability", 0.5) * detail.max_score
                gap_pct = (1.0 - company.get("innovation_capability", 0.5)) * 100
                if gap_pct > 20:
                    improvements.append({
                        "항목": detail.name,
                        "현재_점수": min(item_score, detail.max_score),
                        "목표_점수": detail.max_score,
                        "개선_방법": [
                            "AI/머신러닝 기반 차별화 기술 개발",
                            "최신 기술 트렌드 도입 (블록체인, IoT 등)",
                            "자체 개발 기술/솔루션 강조",
                            "업계 최고 수준의 기술 사례 제시"
                        ],
                        "우선순위": 1 if gap_pct > 30 else 2,
                        "예상_점수_향상": gap_pct * 0.0025
                    })
            
            elif detail.name == "구현 가능성":
                required_tech = rfp.get("requirements", {}).get("technical_requirements", [])
                match_score = len(set(required_tech) & set(company_tech_stack)) / len(required_tech) if required_tech else 0
                item_score = match_score * detail.max_score
                gap_pct = (1.0 - match_score) * 100
                if gap_pct > 20:
                    improvements.append({
                        "항목": detail.name,
                        "현재_점수": min(item_score, detail.max_score),
                        "목표_점수": detail.max_score,
                        "개선_방법": [
                            "상세한 기술 로드맵 작성",
                            "리스크 완화 방안 구체화",
                            "기술 검증 계획 수립",
                            "외부 파트너십/컨소시움 구성"
                        ],
                        "우선순위": 1 if gap_pct > 40 else 2,
                        "예상_점수_향상": gap_pct * 0.002
                    })
            
            elif detail.name == "유사 실적":
                similar_projects = self._find_similar_projects(
                    company.get("past_proposals", []), rfp
                )
                exp_score = len(similar_projects) / max(5, len(company.get("past_proposals", [1])))
                item_score = exp_score * detail.max_score
                gap_pct = (1.0 - exp_score) * 100
                if gap_pct > 30:
                    improvements.append({
                        "항목": detail.name,
                        "현재_점수": min(item_score, detail.max_score),
                        "목표_점수": detail.max_score,
                        "개선_방법": [
                            "유사 프로젝트 사례 발굴 및 정리",
                            "고객 추천장/만족도 자료 수집",
                            "성공 사례의 정량적 성과 제시",
                            "업계 내 평판/수상 이력 강조"
                        ],
                        "우선순위": 2,
                        "예상_점수_향상": gap_pct * 0.0015
                    })
            
            elif detail.name == "기술 팀 역량":
                team_score = company.get("team_capacity", 0.5) * detail.max_score
                gap_pct = (1.0 - company.get("team_capacity", 0.5)) * 100
                if gap_pct > 20:
                    improvements.append({
                        "항목": detail.name,
                        "현재_점수": min(team_score, detail.max_score),
                        "목표_점수": detail.max_score,
                        "개선_방법": [
                            "기술진의 학력/자격 강조",
                            "주요 인력의 경력기술서 작성",
                            "논문/특허/수상 이력 제시",
                            "전문가 추적/재직증명 확보"
                        ],
                        "우선순위": 2,
                        "예상_점수_향상": gap_pct * 0.001
                    })
        
        # 우선순위로 정렬
        improvements.sort(key=lambda x: (x["우선순위"], -x["예상_점수_향상"]))
        return improvements

    def _identify_evidence_requirements(self, criteria: DetailedEvaluationCriteria,
                                       company: Dict) -> List[str]:
        """평가 점수 확보를 위해 필요한 증거 목록"""
        
        evidence = []
        
        for detail in criteria.details:
            if detail.name == "기술 혁신성":
                evidence.extend([
                    "기술 로드맵 및 혁신 전략",
                    "자체 개발 기술/솔루션 소개 자료",
                    "관련 논문, 특허, 자격증",
                    "최신 기술 도입 사례 (AI, 빅데이터 등)"
                ])
            
            elif detail.name == "구현 가능성":
                evidence.extend([
                    "상세한 기술 구현 방안서",
                    "Work Breakdown Structure (WBS)",
                    "위험 관리 계획 (RMP)",
                    "기술 검증 계획 및 테스트 시나리오",
                    "프로토타입 또는 유사 시스템 사례"
                ])
            
            elif detail.name == "유사 실적":
                evidence.extend([
                    "유사 프로젝트 수행 사례 (최소 3건)",
                    "고객 추천장 및 만족도 증명",
                    "정량적 성과 (매출, 신뢰도, 품질) 제시",
                    "언론 보도, 수상 이력"
                ])
            
            elif detail.name == "기술 팀 역량":
                evidence.extend([
                    "주요 기술진 경력기술서", 
                    "관련 학위/자격증 사본",
                    "논문, 특허, 발표 이력",
                    "팀 구성 및 역할 분담표"
                ])
            
            elif detail.name == "제안 품질":
                evidence.extend([
                    "논리적으로 구성된 기술제안서",
                    "시각화 자료 (다이어그램, 차트)",
                    "이해하기 쉬운 표현과 상세한 설명"
                ])
        
        return list(set(evidence))

    def _estimate_win_probability(self, current_score: float, max_score: float) -> float:
        """점수 기반 승률 추정"""
        
        score_ratio = current_score / max_score if max_score > 0 else 0
        
        # 점수 비율에 따른 승률 추정 (S자 곡선)
        if score_ratio >= 0.95:
            return 0.85  # 95점 이상: 85% 승률
        elif score_ratio >= 0.85:
            return 0.65  # 85~95점: 65% 승률
        elif score_ratio >= 0.75:
            return 0.45  # 75~85점: 45% 승률
        elif score_ratio >= 0.65:
            return 0.25  # 65~75점: 25% 승률
        else:
            return 0.10  # 65점 미만: 10% 승률


    async def _evaluate_qualification_compliance(self, rfp: Dict, company: Dict) -> FeasibilityFactor:
        """자격 요건 준수 평가"""

        required_qualifications = rfp["requirements"].get("qualification_requirements", [])
        company_qualifications = company.get("qualifications", [])
        company_certifications = company.get("certifications", [])

        # 자격 요건 매칭
        qualification_score = self._calculate_qualification_match(
            required_qualifications, company_qualifications, company_certifications
        )

        recommendations = []
        if qualification_score < 0.8:
            recommendations.append("추가 자격 취득 또는 파트너십 검토")
            recommendations.append("자격 대체 방안 모색")

        return FeasibilityFactor(
            name="자격 요건 준수",
            score=qualification_score,
            weight=self.weights["qualification_compliance"],
            reasoning=f"자격 요건 준수율: {qualification_score:.1%}",
            recommendations=recommendations
        )

    async def _evaluate_market_competitiveness(self, rfp: Dict, past_proposals: List) -> FeasibilityFactor:
        """시장 경쟁력 평가"""

        # 경쟁자 수 추정
        competition_level = self._estimate_competition_level(rfp)

        # 우리 회사 경쟁력 평가
        our_competitiveness = self._assess_our_competitiveness(rfp, past_proposals)

        # 승률 예측
        estimated_win_rate = our_competitiveness / (competition_level + 1)

        recommendations = []
        if estimated_win_rate < 0.3:
            recommendations.append("가격 전략 재검토")
            recommendations.append("차별화 포인트 강화")
        if competition_level > 5:
            recommendations.append("컨소시엄 구성 고려")

        return FeasibilityFactor(
            name="시장 경쟁력",
            score=min(estimated_win_rate, 1.0),
            weight=self.weights["market_competitiveness"],
            reasoning=f"예상 승률: {estimated_win_rate:.1%}, 경쟁자 수: {competition_level}개",
            recommendations=recommendations
        )

    async def _evaluate_financial_viability(self, rfp: Dict, company: Dict) -> FeasibilityFactor:
        """재무적 타당성 평가"""

        project_budget = rfp["basic_info"].get("budget", 0)
        project_duration = rfp["basic_info"].get("duration_months", 12)

        # 비용 추정
        estimated_cost = self._estimate_project_cost(project_budget, project_duration, rfp)

        # 수익성 분석
        profitability = (project_budget - estimated_cost) / project_budget if project_budget > 0 else 0

        # 회사 재무 상태 고려
        financial_health = company.get("financial_health_score", 0.7)

        # 종합 점수
        final_score = (profitability * 0.6) + (financial_health * 0.4)

        recommendations = []
        if profitability < 0.1:
            recommendations.append("원가 절감 방안 강구")
            recommendations.append("리스크 공유 모델 검토")
        if financial_health < 0.6:
            recommendations.append("재무 상태 개선 우선")

        return FeasibilityFactor(
            name="재무적 타당성",
            score=max(0, min(final_score, 1.0)),
            weight=self.weights["financial_viability"],
            reasoning=f"수익성: {profitability:.1%}, 재무건전성: {financial_health:.1%}",
            recommendations=recommendations
        )

    async def _evaluate_risk_assessment(self, rfp: Dict) -> FeasibilityFactor:
        """리스크 평가"""

        risk_factors = rfp.get("risk_factors", [])
        risk_constraints = rfp["constraints"]

        # 리스크 점수 계산
        risk_score = len(risk_factors) * 0.1  # 각 리스크 요인당 10% 감점
        risk_score += self._assess_constraint_risks(risk_constraints)

        final_score = max(0, 1.0 - risk_score)

        recommendations = []
        if risk_score > 0.3:
            recommendations.append("리스크 완화 전략 수립")
            recommendations.append("보험 또는 담보 검토")

        return FeasibilityFactor(
            name="리스크 평가",
            score=final_score,
            weight=self.weights["risk_assessment"],
            reasoning=f"식별된 리스크 요인: {len(risk_factors)}개",
            recommendations=recommendations
        )

    def _calculate_weighted_score(self, factors: List[FeasibilityFactor]) -> float:
        """가중치 적용 종합 점수 계산"""
        total_score = 0.0
        total_weight = 0.0

        for factor in factors:
            total_score += factor.score * factor.weight
            total_weight += factor.weight

        return total_score / total_weight if total_weight > 0 else 0.0

    def _make_decision(self, score: float, factors: List[FeasibilityFactor]) -> DecisionType:
        """GO/STOP 결정"""
        if score >= 0.8:
            return DecisionType.GO
        elif score >= 0.6:
            # 조건부 GO: 특정 요소가 취약한 경우
            critical_factors = [f for f in factors if f.score < 0.5]
            if len(critical_factors) <= 1:
                return DecisionType.CONDITIONAL_GO
            else:
                return DecisionType.STOP
        else:
            return DecisionType.STOP

    def _get_feasibility_level(self, score: float) -> FeasibilityLevel:
        """수행 가능성 레벨 결정"""
        if score >= 0.9:
            return FeasibilityLevel.EXCELLENT
        elif score >= 0.8:
            return FeasibilityLevel.GOOD
        elif score >= 0.6:
            return FeasibilityLevel.MODERATE
        elif score >= 0.4:
            return FeasibilityLevel.POR
        else:
            return FeasibilityLevel.CRITICAL

    def _generate_reasoning(self, score: float, factors: List[FeasibilityFactor],
                           decision: DecisionType) -> str:
        """결정 근거 생성"""
        lines = [f"종합 수행 가능성 점수: {score:.2f} ({self._get_feasibility_level(score).value})"]

        lines.append("\n세부 평가:")
        for factor in factors:
            lines.append(f"• {factor.name}: {factor.score:.2f} (가중치: {factor.weight})")
            lines.append(f"  {factor.reasoning}")

        lines.append(f"\n결정: {decision.value}")

        if decision == DecisionType.CONDITIONAL_GO:
            lines.append("조건부 진행 가능 (특정 리스크 관리 필요)")
        elif decision == DecisionType.STOP:
            lines.append("진행 불가 (리스크가 기회보다 큼)")

        return "\n".join(lines)

    def _create_action_plan(self, decision: DecisionType, factors: List[FeasibilityFactor]) -> List[str]:
        """실행 계획 생성"""
        actions = []

        if decision == DecisionType.GO:
            actions.extend([
                "제안전략 수립 모듈로 진행",
                "팀 구성 및 일정 수립",
                "필요한 추가 정보 수집"
            ])
        elif decision == DecisionType.CONDITIONAL_GO:
            actions.extend([
                "리스크 완화 방안 수립",
                "조건부 승인 후 전략 수립 진행",
                "모니터링 포인트 설정"
            ])

            # 취약 요소별 추가 액션
            for factor in factors:
                if factor.score < 0.6:
                    actions.extend(factor.recommendations)

        else:  # STOP
            actions.extend([
                "제안 포기 결정 통보",
                "포기 사유 정리 및 보고",
                "유사 사업 기회 모니터링"
            ])

        return actions

    # 헬퍼 메소드들
    def _extract_pattern(self, text: str, pattern: str) -> str:
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def _extract_budget(self, content: str) -> int:
        # 예시 구현
        return 100000000  # 1억원

    def _extract_duration(self, content: str) -> int:
        # 예시 구현
        return 12  # 12개월

    def _classify_project_category(self, content: str) -> str:
        # 예시 구현
        return "IT 개발"

    def _extract_technical_reqs(self, content: str) -> List[str]:
        # 예시 구현
        return ["Python", "AI", "Cloud"]

    def _extract_functional_reqs(self, content: str) -> List[str]:
        # 예시 구현
        return ["사용자 관리", "데이터 분석", "보고서 생성"]

    def _extract_qualification_reqs(self, content: str) -> List[str]:
        # 예시 구현
        return ["ISO 9001", "정보통신공사업", "AI 전문가"]

    def _extract_compliance_reqs(self, content: str) -> List[str]:
        # 예시 구현
        return ["개인정보 보호법", "정보보안", "공공기관 용역"]

    def _extract_timeline_constraints(self, content: str) -> Dict:
        # 예시 구현
        return {"start_date": "2024-03-01", "end_date": "2024-12-31"}

    def _extract_budget_constraints(self, content: str) -> Dict:
        # 예시 구현
        return {"max_budget": 150000000, "currency": "KRW"}

    def _extract_resource_constraints(self, content: str) -> Dict:
        # 예시 구현
        return {"max_team_size": 10, "required_skills": ["AI", "DevOps"]}

    def _extract_technical_constraints(self, content: str) -> Dict:
        # 예시 구현
        return {"platform": "Cloud", "compliance": ["보안", "성능"]}

    def _extract_evaluation_criteria(self, content: str) -> List[str]:
        # 예시 구현
        return ["기술성", "가격", "실적", "제안서"]

    def _extract_criteria_weights(self, content: str) -> Dict[str, float]:
        # 예시 구현
        return {"기술성": 0.4, "가격": 0.3, "실적": 0.2, "제안서": 0.1}

    def _determine_scoring_method(self, content: str) -> str:
        # 예시 구현
        return "100점 만점 절대평가"

    def _calculate_technology_match(self, required: List, company_stack: List, expertise: List) -> float:
        # 예시 구현
        matches = len(set(required) & set(company_stack + expertise))
        return matches / len(required) if required else 1.0

    def _find_similar_projects(self, past_proposals: List, rfp: Dict) -> List:
        # 예시 구현
        return [p for p in past_proposals if p.get("category") == rfp["basic_info"].get("category")]

    def _calculate_qualification_match(self, required: List, company: List, certs: List) -> float:
        # 예시 구현
        matches = len(set(required) & set(company + certs))
        return matches / len(required) if required else 1.0

    def _estimate_competition_level(self, rfp: Dict) -> int:
        # 예시 구현 - 사업 규모에 따른 경쟁자 수 추정
        budget = rfp["basic_info"].get("budget", 0)
        if budget > 500000000:  # 5억원 이상
            return 8
        elif budget > 100000000:  # 1억원 이상
            return 5
        else:
            return 3

    def _assess_our_competitiveness(self, rfp: Dict, past_proposals: List) -> float:
        # 예시 구현
        win_rate = sum(1 for p in past_proposals if p.get("result") == "won") / len(past_proposals)
        return win_rate if past_proposals else 0.5

    def _estimate_project_cost(self, budget: int, duration: int, rfp: Dict) -> int:
        # 예시 구현 - 간단한 비용 추정
        base_cost = budget * 0.7  # 매출의 70%가 비용
        duration_factor = duration / 12  # 12개월 기준
        return int(base_cost * duration_factor)

    def _assess_constraint_risks(self, constraints: Dict) -> float:
        # 예시 구현
        risk_score = 0.0
        if constraints.get("timeline_constraints"):
            risk_score += 0.1  # 타이트한 일정
        if constraints.get("technical_constraints"):
            risk_score += 0.2  # 기술적 제약
        return risk_score</content>
<parameter name="filePath">c:\Users\현재호\OneDrive - 테크노베이션파트너스\바탕 화면\viveproject\tenopa proposer\rfp_review_engine.py