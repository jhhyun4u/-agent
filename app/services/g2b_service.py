"""
나라장터 연동 서비스
나라장터에서 유사 용역을 수행했던 경쟁자를 식별하고 분석
"""

from typing import Dict, List, Any, Optional
import asyncio
import aiohttp
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
import re

@dataclass
class G2BContract:
    """나라장터 계약 정보"""
    contract_id: str
    title: str
    agency: str  # 발주처
    contractor: str  # 수주업체
    contract_date: str
    contract_amount: int
    category: str
    description: str
    similarity_score: float = 0.0

@dataclass
class CompetitorProfile:
    """경쟁사 프로필"""
    company_name: str
    contract_history: List[G2BContract]
    specialization_areas: List[str]
    avg_contract_amount: int
    success_rate: float
    market_share: float
    strength_score: float
    weakness_score: float

class G2BService:
    """나라장터 API 연동 서비스"""

    def __init__(self):
        self.base_url = "https://apis.data.go.kr/1230000/BidPublicInfoService04"
        self.api_key = None  # 환경변수에서 가져와야 함
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def search_similar_contracts(self, rfp_title: str, rfp_description: str,
                                     keywords: List[str], budget_range: tuple = None,
                                     date_range_months: int = 24) -> List[G2BContract]:
        """
        RFP와 유사한 나라장터 계약 검색

        Args:
            rfp_title: RFP 제목
            rfp_description: RFP 설명
            keywords: 검색 키워드
            budget_range: 예산 범위 (min, max)
            date_range_months: 검색 기간 (개월)

        Returns:
            유사 계약 목록
        """

        # 검색 쿼리 구성
        search_query = self._build_search_query(rfp_title, rfp_description, keywords)

        # 날짜 범위 설정
        end_date = datetime.now()
        start_date = end_date - timedelta(days=date_range_months * 30)

        contracts = []

        try:
            # 나라장터 API 호출 (실제로는 API 키 필요)
            # 여기서는 모의 데이터로 대체
            contracts = await self._mock_search_contracts(search_query, start_date, end_date, budget_range)

        except Exception as e:
            print(f"나라장터 검색 중 오류: {e}")
            contracts = []

        return contracts

    def _build_search_query(self, title: str, description: str, keywords: List[str]) -> str:
        """검색 쿼리 구성"""
        query_parts = []

        # 제목에서 핵심 키워드 추출
        title_keywords = self._extract_keywords(title)
        query_parts.extend(title_keywords)

        # 설명에서 키워드 추출
        desc_keywords = self._extract_keywords(description)
        query_parts.extend(desc_keywords[:3])  # 상위 3개만

        # 추가 키워드
        query_parts.extend(keywords)

        # 중복 제거 및 조합
        unique_keywords = list(set(query_parts))
        return " ".join(unique_keywords)

    def _extract_keywords(self, text: str) -> List[str]:
        """텍스트에서 키워드 추출"""
        # 불용어 제거 및 명사 추출 (간단한 구현)
        stopwords = ['및', '등', '의', '을', '를', '이', '가', '은', '는', '에', '에서', '으로', '로', '과', '와']

        words = re.findall(r'\b\w+\b', text)
        keywords = [word for word in words if len(word) > 1 and word not in stopwords]

        # 빈도수 기반 상위 키워드 선택
        from collections import Counter
        word_freq = Counter(keywords)
        return [word for word, _ in word_freq.most_common(5)]

    async def _mock_search_contracts(self, query: str, start_date: datetime,
                                   end_date: datetime, budget_range: tuple = None) -> List[G2BContract]:
        """모의 나라장터 검색 (실제 구현 시 API 호출로 대체)"""

        # 모의 데이터 생성
        mock_contracts = [
            G2BContract(
                contract_id="20240001",
                title="AI 기반 데이터 분석 시스템 구축",
                agency="과학기술정보통신부",
                contractor="(주)테크노솔루션",
                contract_date="2024-01-15",
                contract_amount=150000000,
                category="정보통신",
                description="AI 및 빅데이터 분석 시스템 개발 및 구축"
            ),
            G2BContract(
                contract_id="20240002",
                title="머신러닝 플랫폼 개발",
                agency="교육부",
                contractor="(주)데이터인사이트",
                contract_date="2024-02-20",
                contract_amount=200000000,
                category="정보통신",
                description="교육 데이터 분석을 위한 머신러닝 플랫폼"
            ),
            G2BContract(
                contract_id="20240003",
                title="클라우드 기반 AI 서비스 개발",
                agency="행정안전부",
                contractor="(주)클라우드테크",
                contract_date="2024-03-10",
                contract_amount=180000000,
                category="정보통신",
                description="공공 클라우드 AI 서비스 구축"
            ),
            G2BContract(
                contract_id="20240004",
                title="빅데이터 분석 솔루션",
                agency="보건복지부",
                contractor="(주)헬스데이터",
                contract_date="2024-04-05",
                contract_amount=120000000,
                category="정보통신",
                description="의료 빅데이터 분석 시스템"
            ),
            G2BContract(
                contract_id="20240005",
                title="AI 챗봇 시스템 구축",
                agency="문화체육관광부",
                contractor="(주)AI솔루션",
                contract_date="2024-05-12",
                contract_amount=90000000,
                category="정보통신",
                description="민원 응대 AI 챗봇 개발"
            )
        ]

        # 유사도 계산 및 필터링
        relevant_contracts = []
        for contract in mock_contracts:
            similarity = self._calculate_similarity(query, contract.title + " " + contract.description)
            if similarity > 0.3:  # 유사도 30% 이상
                contract.similarity_score = similarity
                relevant_contracts.append(contract)

        # 예산 범위 필터링
        if budget_range:
            min_budget, max_budget = budget_range
            relevant_contracts = [
                c for c in relevant_contracts
                if min_budget <= c.contract_amount <= max_budget
            ]

        return sorted(relevant_contracts, key=lambda x: x.similarity_score, reverse=True)

    def _calculate_similarity(self, query: str, text: str) -> float:
        """단순 텍스트 유사도 계산"""
        query_words = set(query.lower().split())
        text_words = set(text.lower().split())

        intersection = query_words & text_words
        union = query_words | text_words

        return len(intersection) / len(union) if union else 0.0

    async def identify_competitors(self, contracts: List[G2BContract],
                                 min_contracts: int = 2) -> List[CompetitorProfile]:
        """
        유사 계약에서 경쟁사 식별 및 프로필 생성

        Args:
            contracts: 유사 계약 목록
            min_contracts: 최소 계약 건수 (이상인 업체만 경쟁사로 간주)

        Returns:
            경쟁사 프로필 목록
        """

        # 업체별 계약 그룹화
        company_contracts = {}
        for contract in contracts:
            if contract.contractor not in company_contracts:
                company_contracts[contract.contractor] = []
            company_contracts[contract.contractor].append(contract)

        # 경쟁사 필터링 (최소 계약 건수 이상)
        competitors = []
        for company_name, contracts_list in company_contracts.items():
            if len(contracts_list) >= min_contracts:
                profile = await self._create_competitor_profile(company_name, contracts_list)
                competitors.append(profile)

        return sorted(competitors, key=lambda x: x.market_share, reverse=True)

    async def _create_competitor_profile(self, company_name: str,
                                       contracts: List[G2BContract]) -> CompetitorProfile:
        """경쟁사 프로필 생성"""

        # 전문 분야 분석
        specialization_areas = self._analyze_specialization(contracts)

        # 평균 계약 금액
        avg_amount = sum(c.contract_amount for c in contracts) / len(contracts)

        # 성공률 (모의 데이터)
        success_rate = 0.85 + (len(contracts) - 2) * 0.05  # 계약 건수가 많을수록 성공률 높음
        success_rate = min(success_rate, 0.95)

        # 시장 점유율 (모의 계산)
        total_market = sum(c.contract_amount for c in contracts)
        market_share = min(total_market / 1000000000, 0.15)  # 최대 15%로 제한

        # 강점/약점 점수 계산
        strength_score = self._calculate_competitor_strength(contracts, specialization_areas)
        weakness_score = 1.0 - strength_score

        return CompetitorProfile(
            company_name=company_name,
            contract_history=contracts,
            specialization_areas=specialization_areas,
            avg_contract_amount=int(avg_amount),
            success_rate=success_rate,
            market_share=market_share,
            strength_score=strength_score,
            weakness_score=weakness_score
        )

    def _analyze_specialization(self, contracts: List[G2BContract]) -> List[str]:
        """전문 분야 분석"""
        categories = {}
        for contract in contracts:
            cat = contract.category
            categories[cat] = categories.get(cat, 0) + 1

        # 상위 카테고리 추출
        sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        return [cat for cat, _ in sorted_cats[:3]]

    def _calculate_competitor_strength(self, contracts: List[G2BContract],
                                     specialization_areas: List[str]) -> float:
        """경쟁사 강점 점수 계산"""
        base_score = 0.5

        # 계약 건수 보너스
        contract_bonus = min(len(contracts) * 0.1, 0.3)

        # 전문성 보너스
        specialization_bonus = min(len(specialization_areas) * 0.05, 0.15)

        # 평균 계약 금액 보너스
        avg_amount = sum(c.contract_amount for c in contracts) / len(contracts)
        amount_bonus = min(avg_amount / 500000000 * 0.1, 0.1)  # 5억 이상 시 보너스

        return min(base_score + contract_bonus + specialization_bonus + amount_bonus, 0.95)

    async def get_competitor_strategy_recommendations(self, competitors: List[CompetitorProfile],
                                                    our_company_profile: Dict) -> Dict[str, Any]:
        """
        경쟁사 분석 기반 전략 추천

        Args:
            competitors: 경쟁사 프로필 목록
            our_company_profile: 우리 회사 프로필

        Returns:
            전략 추천 정보
        """

        if not competitors:
            return {
                "strategy_type": "defence",
                "reasoning": "경쟁사가 식별되지 않아 방어 전략 권장",
                "key_competitors": [],
                "differentiation_opportunities": ["시장 리더십 확보"]
            }

        # 주요 경쟁사 식별
        key_competitors = competitors[:3]  # 상위 3개사

        # 경쟁 강도 분석
        avg_strength = sum(c.strength_score for c in key_competitors) / len(key_competitors)

        # 우리 회사 강점 비교
        our_strength = our_company_profile.get("overall_strength", 0.7)

        # 전략 결정
        if our_strength > avg_strength + 0.2:
            strategy_type = "defence"
            reasoning = f"우리 회사 강점({our_strength:.2f})이 경쟁사 평균({avg_strength:.2f})보다 우월하여 방어 전략 적합"
        elif our_strength < avg_strength - 0.2:
            strategy_type = "offence"
            reasoning = f"경쟁사 강점이 우월하여 혁신/가격 차별화 전략 필요"
        else:
            strategy_type = "balanced"
            reasoning = f"경쟁 강도가 유사하여 균형 전략 적용"

        # 차별화 기회 식별
        differentiation_opportunities = self._identify_differentiation_opportunities(
            key_competitors, our_company_profile
        )

        return {
            "strategy_type": strategy_type,
            "reasoning": reasoning,
            "key_competitors": [
                {
                    "name": c.company_name,
                    "strength_score": c.strength_score,
                    "specialization": c.specialization_areas,
                    "avg_contract": c.avg_contract_amount
                }
                for c in key_competitors
            ],
            "differentiation_opportunities": differentiation_opportunities,
            "market_insights": {
                "total_competitors": len(competitors),
                "avg_market_share": sum(c.market_share for c in competitors) / len(competitors),
                "dominant_categories": self._get_dominant_categories(competitors)
            }
        }

    def _identify_differentiation_opportunities(self, competitors: List[CompetitorProfile],
                                              our_profile: Dict) -> List[str]:
        """차별화 기회 식별"""

        opportunities = []

        # 경쟁사 약점 분석
        competitor_weaknesses = []
        for comp in competitors:
            if comp.weakness_score > 0.6:
                competitor_weaknesses.extend(comp.specialization_areas)

        # 우리 회사 강점
        our_strengths = our_profile.get("strength_areas", [])

        # 차별화 포인트 도출
        if "AI" in our_strengths and "AI" not in competitor_weaknesses:
            opportunities.append("AI 기술력 차별화")

        if "빅데이터" in our_strengths:
            opportunities.append("데이터 분석 전문성 강조")

        if "클라우드" in our_strengths:
            opportunities.append("클라우드 네이티브 아키텍처")

        if "가격 경쟁력" in our_strengths:
            opportunities.append("합리적 가격 제시")

        if not opportunities:
            opportunities = ["기술 혁신", "고객 맞춤 솔루션", "빠른 구축 기간"]

        return opportunities

    def _get_dominant_categories(self, competitors: List[CompetitorProfile]) -> List[str]:
        """주요 카테고리 식별"""
        all_categories = []
        for comp in competitors:
            all_categories.extend(comp.specialization_areas)

        from collections import Counter
        category_counts = Counter(all_categories)
        return [cat for cat, _ in category_counts.most_common(3)]