"""
Node 8A: proposal_customer_analysis
Prompt templates for customer intelligence extraction.
"""

CUSTOMER_INTELLIGENCE_PROMPT = """
당신은 제안서를 위해 발주처 조직을 분석하는 비즈니스 전략가입니다.

RFP 정보:
{rfp_analysis}

우리의 전략:
{strategy}

알려진 고객 인텔리전스:
{kb_references}

다음 항목을 포함하는 상세한 고객 프로필을 작성하세요:

1. **의사결정 동인**: 그들의 의사결정에 가장 큰 영향을 미칠 3-5가지 요소는?
2. **예산 승인 권한**: 예산은 어떻게 통제되고 승인되는가?
3. **조직 내 정치**: 핵심 조직 역학 관계와 권력 구조 (2-3문장)
4. **통증점**: 해결하려는 구체적인 문제는 무엇인가? (3-5개 나열)
5. **성공 지표**: 프로젝트 성공을 어떻게 측정할 것인가? (3-5개 나열)
6. **핵심 이해관계자**: 의사결정자, 영향력자, 예산 담당자, 사용자는 누구인가?
   - 각각: 이름, 직책, 역할, 관심사, 영향력 수준 (1-5)
7. **위험 인식**: 이 유형의 프로젝트에 대한 가장 큰 우려사항은?
8. **시간 압박**: 이들에게 얼마나 긴급한가? (low/medium/high/critical)
9. **조달 프로세스**: 정식인가 비정식인가? 어떤 승인 게이트가 있는가?
10. **경쟁 환경**: 누가 추가로 입찰할 수 있는가?
11. **선행 경험**: 언급된 유사 프로젝트나 벤더 이력이 있는가?

Respond in valid JSON format matching this schema:
{{
  "client_org": "string",
  "market_segment": "string",
  "organization_size": "string",
  "decision_drivers": ["string"],
  "budget_authority": "string",
  "budget_range": "string or null",
  "internal_politics": "string",
  "pain_points": ["string"],
  "success_metrics": ["string"],
  "key_stakeholders": [
    {{
      "name": "string",
      "title": "string",
      "role": "string",
      "interests": ["string"],
      "influence_level": 1-5,
      "contact_info": "string or null"
    }}
  ],
  "risk_perception": "string",
  "timeline_pressure": "string",
  "procurement_process": "string",
  "competitive_landscape": "string",
  "prior_experience": "string or null",
  "created_at": "ISO timestamp"
}}

구체적이고 실행 가능해야 합니다. RFP 내용과 문맥 단서를 바탕으로 분석하세요.
"""
