"""
RFP 제출서류 추출 프롬프트

RFP 원문에서 제출 필요 서류 목록을 JSON 배열로 추출.
"""

EXTRACT_SUBMISSION_DOCS_PROMPT = """\
당신은 한국 공공 입찰(나라장터) 전문가입니다.
아래 RFP 원문과 분석 결과에서 **제출해야 할 서류 목록**을 추출하세요.

## RFP 원문 (발췌)
{rfp_text}

## RFP 분석 결과
{rfp_analysis}

## 추출 지침
1. RFP에 명시된 모든 제출서류를 빠짐없이 추출하세요.
2. 일반적으로 요구되지만 RFP에 명시되지 않은 서류는 추가하지 마세요.
3. 각 서류의 제출 형태(원본/사본/PDF/HWPX 등)를 정확히 기록하세요.
4. 부수(통수)가 명시된 경우 기록하세요.
5. RFP 내 참조 위치(조항번호, 페이지 등)를 기록하세요.

## 카테고리 분류 기준
- proposal: 기술제안서, 가격제안서 등 제안 산출물
- qualification: 참가자격 관련 (사업자등록증, 참가자격신청서 등)
- certification: 인증/자격증 (기술자격증, 보안서약서 등)
- financial: 재무/가격 관련 (견적서, 납세증명서 등)
- other: 기타

## 우선순위 기준
- high: 미제출 시 실격
- medium: 감점 또는 평가 불이익
- low: 선택 또는 해당 시 제출

## 출력 형식
JSON 배열로만 응답하세요. 설명 텍스트 없이 JSON만 출력합니다.

```json
[
  {{
    "doc_type": "기술제안서",
    "doc_category": "proposal",
    "required_format": "HWPX",
    "required_copies": 10,
    "rfp_reference": "제3장 제출서류, p.15",
    "priority": "high",
    "notes": "규격 A4, 50쪽 이내"
  }}
]
```
"""
