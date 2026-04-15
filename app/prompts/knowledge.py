"""
지식 관리 시스템 (llm-wiki) 프롬프트.

지식 분류, 추천, 건강도 대시보드 관련 프롬프트.
토큰 예산: Classification 5,000 | Search 3,000 | Recommendation 8,000
"""

# ============================================================================
# KNOWLEDGE CLASSIFICATION PROMPT (§3.1-1)
# ============================================================================

KNOWLEDGE_CLASSIFICATION_SYSTEM_PROMPT = """당신은 조직의 지식 자산을 자동으로 분류하는 AI 전문가입니다.

문서 청크를 다음 4가지 지식 유형으로 정확하게 분류합니다:

1. **capability** (역량/기술 전문성)
   - 기술 스택, 도메인 전문성, 구현 경험, 설계 패턴
   - 예: "IoT 플랫폼 개발 경험 5년, 실시간 데이터 처리"

2. **client_intel** (고객/발주기관 정보)
   - 고객 조직 구조, 의사결정 프로세스, 과거 발주 행태
   - 예: "A사는 2개월마다 검토 회의, CFO와 CTO가 의결"

3. **market_price** (시장 가격/낙찰 정보)
   - 시장 평균 가격, 경쟁사 낙찰가, 가격 책정 기준
   - 예: "유사 규모 프로젝트 평균 낙찰률 75%, 단가 500K"

4. **lesson_learned** (프로젝트 교훈)
   - 성공 요인, 실패 원인, 리스크 사항, 개선점
   - 예: "초기 요구사항 분석 부족으로 2주 지연, 상세 검증 필요"

분류 규칙:
- 한 청크가 여러 유형에 해당할 수 있음 (multi-type)
- 신뢰도(confidence)는 LLM 확신도 (0.0~1.0)
- <0.6 confidence는 "unclassified"로 표시"""

KNOWLEDGE_CLASSIFICATION_USER_TEMPLATE = """문서 제목: {document_title}
문서 작성일: {created_date}
문서 출처: {document_source}

---청크 내용---
{chunk_content}

---

JSON 형식으로 다음을 응답하세요:
{{
  "primary_type": "capability|client_intel|market_price|lesson_learned|unclassified",
  "confidence": <0.0 ~ 1.0>,
  "reasoning": "분류 근거 1문장",
  "secondary_types": [
    {{
      "type": "capability|client_intel|market_price|lesson_learned",
      "confidence": <0.0 ~ 1.0>,
      "reasoning": "복수 분류 근거"
    }}
  ],
  "tags": ["tag1", "tag2"],
  "should_deprecate": false,
  "deprecation_reason": null
}}

**중요**:
- JSON만 응답 (설명 제외)
- confidence < 0.6인 경우만 "unclassified" 사용
- secondary_types는 confidence >= 0.5인 경우만 포함"""

# ============================================================================
# KNOWLEDGE SEARCH RELEVANCE RANKING (§3.2)
# ============================================================================

KNOWLEDGE_SEARCH_RANKING_PROMPT = """당신은 제안 작성 맥락에서 조직 지식의 관련성을 평가하는 전문가입니다.

주어진 검색 쿼리와 제안 맥락에 대해, 여러 지식 청크의 관련성을 0~100으로 점수화합니다.

평가 기준:
1. **직접 관련성** (40점): 쿼리와 정확한 매칭도
2. **맥락 적합성** (30점): 제안 상황(고객 유형, 예산, 전략)과의 시너지
3. **시간 효율성** (20점): 지식의 최신성과 실용성
4. **증거 강도** (10점): 구체적 데이터/수치/사례 포함 여부"""

KNOWLEDGE_SEARCH_RANKING_TEMPLATE = """검색 쿼리: {query}

제안 맥락:
- 고객 유형: {client_type}
- 입찰 규모: {bid_amount}
- 선택 전략: {selected_strategy}

---후보 지식 청크---
{ranked_chunks}

각 청크의 관련성 점수(0~100)를 JSON 배열로 응답하세요:
[
  {{
    "chunk_id": "...",
    "relevance_score": <0~100>,
    "match_reason": "관련성 설명"
  }}
]"""

# ============================================================================
# KNOWLEDGE RECOMMENDATION ENGINE (§3.3)
# ============================================================================

KNOWLEDGE_RECOMMENDATION_SYSTEM_PROMPT = """당신은 제안서 작성 중인 컨설턴트를 위해 최고의 지식을 추천하는 AI입니다.

제안 맥락(RFP 요약, 고객 유형, 전략)을 이해하고,
조직의 지식 베이스에서 즉시 활용 가능한 상위 5개 지식을 추천합니다.

각 추천에는:
- 순위 (1~5)
- 지식 유형
- 관련성 이유 (구체적, 액션 가능)
- 신뢰도 점수"""

KNOWLEDGE_RECOMMENDATION_USER_TEMPLATE = """제안 맥락:
- RFP 요약: {rfp_summary}
- 고객 유형: {client_type}
- 입찰 규모: {bid_amount}
- 선택 전략: {selected_strategy}

---이용 가능한 지식---
{available_knowledge_chunks}

JSON 형식으로 상위 5개 지식을 추천하세요:
{{
  "recommendations": [
    {{
      "rank": 1,
      "chunk_id": "...",
      "knowledge_type": "capability|client_intel|market_price|lesson_learned",
      "relevance_reason": "구체적 활용 방안",
      "confidence": <0.0~1.0>,
      "suggested_action": "제안서 어느 섹션에서 활용할지"
    }}
  ],
  "context_matched": ["dimension1", "dimension2"],
  "overall_confidence": <0.0~1.0>
}}"""

# ============================================================================
# KNOWLEDGE HEALTH SUMMARY PROMPT (§3.4)
# ============================================================================

KNOWLEDGE_HEALTH_ANALYSIS_PROMPT = """당신은 조직 지식 베이스의 건강도를 평가하는 분석가입니다.

지식 커버리지, 신선도, 활용 수준을 종합 평가하고
개선 권고안을 제시합니다."""

KNOWLEDGE_HEALTH_ANALYSIS_TEMPLATE = """지식 베이스 통계:
- 총 문서: {total_documents}
- 총 청크: {total_chunks}
- 역량(capability): {capability_count}개
- 고객정보(client_intel): {client_intel_count}개
- 가격정보(market_price): {market_price_count}개
- 교훈(lesson_learned): {lesson_learned_count}개

신선도 분포:
- 1년 이내: {freshness_lt_1yr}개 ({freshness_lt_1yr_pct}%)
- 1~2년: {freshness_1_2yr}개 ({freshness_1_2yr_pct}%)
- 2년 이상: {freshness_gt_2yr}개 ({freshness_gt_2yr_pct}%)

활용 현황:
- 지난 30일 검색: {searches_30d}회
- 결과 없는 검색: {zero_result_searches}회
- 추천 승인률: {acceptance_rate}%

JSON 형식으로 평가 결과를 제시하세요:
{{
  "health_score": <0~100>,
  "coverage_assessment": "역량|고객정보|가격정보|교훈 중 부족한 영역",
  "freshness_concern": "신선도 우려 수준",
  "usage_insight": "활용 패턴 분석",
  "top_recommendations": [
    {{
      "priority": "HIGH|MEDIUM|LOW",
      "action": "구체적 개선 조치",
      "expected_impact": "기대 효과"
    }}
  ]
}}"""

# ============================================================================
# KNOWLEDGE TYPE DEFINITIONS (for reference)
# ============================================================================

KNOWLEDGE_TYPE_DEFINITIONS = {
    "capability": {
        "description": "Technical expertise and domain knowledge",
        "examples": [
            "IoT platform development experience",
            "Real-time data processing implementation",
            "Kubernetes orchestration patterns",
            "AWS migration best practices"
        ],
        "keywords": ["experience", "expertise", "technology", "implementation", "method", "pattern"]
    },
    "client_intel": {
        "description": "Client organization and decision-making information",
        "examples": [
            "Client organizational structure and stakeholders",
            "Decision approval process (timeline, approvers)",
            "Past procurement behavior and preferences",
            "Risk tolerance and budget constraints"
        ],
        "keywords": ["client", "organization", "stakeholder", "decision", "process", "approval"]
    },
    "market_price": {
        "description": "Market pricing and competitive intelligence",
        "examples": [
            "Average winning bid rates for similar projects",
            "Market pricing for comparable services",
            "Competitor win/loss analysis",
            "Cost benchmarking by industry/region"
        ],
        "keywords": ["price", "cost", "bid", "rate", "market", "competitive", "winning"]
    },
    "lesson_learned": {
        "description": "Project lessons, risks, and improvement insights",
        "examples": [
            "Success factors from past projects",
            "Root cause analysis of failures",
            "Risk mitigation strategies",
            "Process improvements and lessons"
        ],
        "keywords": ["lesson", "learned", "risk", "failure", "success", "improvement", "insight"]
    }
}
