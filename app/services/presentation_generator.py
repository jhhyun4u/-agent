"""발표 자료 슬라이드 JSON 생성 서비스 — 3-step 파이프라인 (TOC → Visual Brief → 스토리보드)

발표 시간 기준: 15분 내외 → 슬라이드 25~35장 (슬라이드당 약 30~35초)
필요 시 구체적 사례(case_study) 또는 참고 슬라이드를 중간에 삽입 가능.
"""

import json
import logging
from typing import Optional

import anthropic

from app.config import settings
from app.models.phase_schemas import Phase2Artifact, Phase3Artifact, Phase4Artifact
from app.models.schemas import RFPData
from app.utils.claude_utils import extract_json_from_response

logger = logging.getLogger(__name__)

# ── Step 1: TOC 생성 프롬프트 ────────────────────────────────────────────────

TOC_SYSTEM = """당신은 공공 입찰 발표 자료의 목차를 설계하는 전문가입니다.
평가위원이 배점표에 따라 채점하는 발표 심사(15분)를 위해 최적의 슬라이드 목차를 구성합니다.
응답은 반드시 JSON 형식으로만 제공합니다.

목차 설계 규칙:
1. 고정 슬라이드(표지 cover, 목차 agenda, 이기는전략 key_message, 마무리 closing)는 반드시 포함하라.
2. 평가항목 슬라이드는 score_weight 내림차순으로 배치하라.
3. score_weight >= 20점: 전용 슬라이드 3~4장 (문제→솔루션→증거→기대효과 분리)
4. score_weight 15-19점: 전용 슬라이드 2~3장
5. score_weight 10-14점: 전용 슬라이드 1~2장
6. score_weight <= 9점: 전용 슬라이드 1장
7. 추진일정/타임라인은 timeline 레이아웃 사용
8. 인력투입계획은 team 레이아웃 사용
9. 슬라이드 title은 반드시 "주어 + 서술어" 형식의 완결 주장 문장(assertion)으로 작성하라.
   예: ❌ "사업 이해도" → ✅ "당사는 현장 경험 5년으로 발주처 핵심 요구사항을 정확히 이해함"
   예: ❌ "기술 역량"   → ✅ "3개 특허 기반 고유 기술로 경쟁사 대비 처리 속도 40% 우위 확보"
   단, cover(표지)와 closing 슬라이드 title은 예외 (사업명, "왜 우리인가" 유지)
10. 핵심 수치/실적 강조가 필요한 경우 numbers_callout 레이아웃 사용 (최대 2회)
11. 방법론/수행절차 설명 슬라이드는 process_flow 레이아웃 사용
12. 발주처 현황·문제 공감이 필요한 경우 problem_sync 레이아웃 사용 (key_message 직후)
    - 평가 1순위는 Q&A이므로, 발주처 문제를 먼저 공감시켜 신뢰를 형성하는 것이 핵심
13. 비전/미션/핵심 슬로건 강조에는 quote_highlight 레이아웃 사용 (선택적)
14. 차별화 비교가 필요한 경우 comparison 레이아웃 사용
15. 유사 사례/레퍼런스로 신뢰를 높여야 할 때 case_study 레이아웃 사용:
    - 배점 높은 평가항목의 "증거" 슬라이드로 활용
    - 수치 성과가 명확한 사례에만 사용 (추상적 사례 금지)
16. 전체 발표 흐름은 기승전결 서사 구조를 따르라:
    - 도입(cover→agenda→key_message→problem_sync): 문제 공감 → Win Theme 선언
    - 전개(평가항목 슬라이드들): 배점 높은 순 / 주장→근거→사례→기대효과
    - 결론(closing): Win Theme 재확인 + 행동 촉구
17. 슬라이드 총 수는 최소 25장, 최대 35장으로 제한하라.
    (발표 15분 기준: 슬라이드당 약 30~35초 배분)
18. 앞 슬라이드가 다음 슬라이드의 질문을 자연스럽게 유도하도록 흐름을 설계하라.
    예: "문제 현황" → "왜 기존 방법론은 안 되는가?" → "우리의 해결책은?" → "증거는?" 순서"""

TOC_USER = """다음 정보를 바탕으로 발표 자료 목차를 설계해주세요.

## 사업명
{project_name}

## 평가항목 배점 (score_weight 내림차순 정렬됨)
{section_plan}

## Win Theme
{win_theme}

반드시 아래 JSON 형식으로 응답하세요:
{{
    "toc": [
        {{
            "slide_num": 1,
            "layout": "cover",
            "title": "사업명",
            "eval_badge": "",
            "target_section": "",
            "score_weight": 0
        }},
        {{
            "slide_num": 2,
            "layout": "agenda",
            "title": "발표 순서",
            "eval_badge": "",
            "target_section": "",
            "score_weight": 0
        }},
        {{
            "slide_num": 3,
            "layout": "key_message",
            "title": "이기는 전략",
            "eval_badge": "",
            "target_section": "",
            "score_weight": 0
        }},
        {{
            "slide_num": 4,
            "layout": "problem_sync",
            "title": "발주처 핵심 과제를 당사는 가장 정확히 이해함",
            "eval_badge": "",
            "target_section": "",
            "score_weight": 0
        }},
        {{
            "slide_num": 5,
            "layout": "eval_section",
            "title": "슬라이드 제목 (assertion 형식)",
            "eval_badge": "평가항목명 | XX점",
            "target_section": "section_plan의 section_name 값",
            "score_weight": 25
        }},
        {{
            "slide_num": 6,
            "layout": "case_study",
            "title": "유사 사업 수행으로 동일 과제를 이미 해결한 실적 보유",
            "eval_badge": "평가항목명 | XX점",
            "target_section": "section_plan의 section_name 값",
            "score_weight": 25
        }},
        {{
            "slide_num": 99,
            "layout": "closing",
            "title": "왜 우리인가",
            "eval_badge": "",
            "target_section": "",
            "score_weight": 0
        }}
    ],
    "total_slides": 28
}}

규칙:
- layout 값: cover | agenda | key_message | eval_section | comparison | timeline | team | closing | numbers_callout | process_flow | problem_sync | quote_highlight | split_panel | numbered_strategy | case_study
- slide_num은 1부터 연속 정수 (마지막 슬라이드도 실제 번호 사용)
- eval_badge: "평가항목명 | XX점" 형식 (eval_section/timeline/team/comparison/process_flow/numbers_callout/split_panel/case_study만)
- target_section: section_plan의 section_name 값 그대로
- 총 슬라이드: 25~35장"""


# ── Step 2: Visual Brief 생성 프롬프트 ──────────────────────────────────────

VISUAL_BRIEF_SYSTEM = """당신은 컨설팅급 발표 자료의 시각 설계를 담당하는 전문가입니다.
확정된 목차(TOC)의 각 슬라이드에 대해 "이 assertion을 가장 강력하게 증명하는 시각 전략"을 설계합니다.

핵심 원칙:
1. Message → Logic → Structure → Design 순서: 시각은 메시지를 증명하기 위해 존재
2. F-Pattern 시선 흐름: 가장 중요한 요소(숫자/차트)가 슬라이드에서 가장 먼저 눈에 들어와야 함
   - 시선 순서: 큰 숫자/아이콘 → 차트/다이어그램 → 제목 → 본문
3. 하이라이트 1개 원칙: 슬라이드 전체에서 강조 요소는 반드시 1개만 지정
4. 차트 제목은 반드시 결론형 문장: "비교 데이터" ❌ → "당사 처리속도 경쟁사 대비 40% 우위" ✅
5. 30% 여백 설계: 정보를 가득 채우지 말고 핵심 요소만 배치

proof_type 선택 기준:
- comparative_data: 수치 비교로 우위를 증명해야 할 때 → composition: split_panel (차트+전략)
- trend_analysis: 추세/성장/변화를 보여야 할 때 → composition: split_panel (라인차트+해석)
- key_metrics: 3~4개 핵심 수치가 assertion을 직접 증명할 때 → composition: numbers_callout
- problem_evidence: 발주처 문제 공감이 필요할 때 → composition: problem_sync
- differentiation: 경쟁 대비 우월성을 구조적으로 보여야 할 때 → composition: comparison
- sequential_steps: 단계적 프로세스/방법론 설명 → composition: process_flow
- bold_statement: 비전/미션/핵심 선언 → composition: quote_highlight
- team_credentials: 인력 역량 증명 → composition: team
- timeline_execution: 추진 일정 → composition: timeline
- reference_proof: 유사 사례/레퍼런스로 실적 증명 → composition: case_study
- narrative_bullets: 논리적 주장을 텍스트로 전개 → composition: eval_section
- numbered_argument: 3~4개 번호형 논점 전개 → composition: numbered_strategy

응답은 반드시 JSON 형식으로만 제공합니다."""

VISUAL_BRIEF_USER = """확정된 목차를 기반으로 각 슬라이드의 시각 설계 전략을 작성해주세요.

## 확정된 목차 (TOC)
{toc}

## Win Theme
{win_theme}

## 차별화 포인트
{differentiation_strategy}

반드시 아래 JSON 형식으로 응답하세요:
{{
    "visual_briefs": [
        {{
            "slide_num": 1,
            "layout": "cover",
            "proof_type": "bold_statement",
            "composition": "cover",
            "f_pattern_anchor": "Win Theme 핵심 문구",
            "highlight_element": "핵심 선언 문구 1개",
            "highlight_type": "phrase",
            "left_panel": null,
            "right_panel": null,
            "chart_title": "",
            "key_stat": "",
            "visual_rationale": "표지는 Win Theme을 강렬하게 각인"
        }},
        {{
            "slide_num": 5,
            "layout": "split_panel",
            "proof_type": "comparative_data",
            "composition": "split_panel",
            "f_pattern_anchor": "40%",
            "highlight_element": "40% 속도 향상",
            "highlight_type": "number",
            "left_panel": {{
                "type": "bar_chart",
                "chart_title": "당사 처리속도 경쟁사 대비 40% 우위 (동일 조건 기준)",
                "data_hint": "처리속도 수치 추출 필요"
            }},
            "right_panel": {{
                "type": "numbered_strategy",
                "count": 3,
                "style": "bold_headline + sub_description"
            }},
            "chart_title": "당사 처리속도 경쟁사 대비 40% 우위 (동일 조건 기준)",
            "key_stat": "",
            "visual_rationale": "수치 비교가 우위를 가장 직관적으로 증명"
        }},
        {{
            "slide_num": 6,
            "layout": "case_study",
            "proof_type": "reference_proof",
            "composition": "case_study",
            "f_pattern_anchor": "97점",
            "highlight_element": "납기 준수율 100%",
            "highlight_type": "number",
            "left_panel": null,
            "right_panel": null,
            "chart_title": "",
            "key_stat": "97점",
            "visual_rationale": "유사 사례의 수치 성과가 assertion을 직접 증명"
        }},
        {{
            "slide_num": 7,
            "layout": "eval_section",
            "proof_type": "narrative_bullets",
            "composition": "eval_section",
            "f_pattern_anchor": "핵심 수치 또는 키워드",
            "highlight_element": "가장 강력한 근거 문구 1개",
            "highlight_type": "phrase",
            "left_panel": null,
            "right_panel": null,
            "chart_title": "",
            "key_stat": "강조할 대형 수치 (예: 97%)",
            "visual_rationale": "논리적 근거를 순서대로 전달"
        }}
    ]
}}

규칙:
- TOC의 모든 슬라이드에 대해 visual_brief 생성
- composition은 TOC의 layout을 따르되, comparative_data/trend_analysis는 split_panel로 변경 가능
- f_pattern_anchor: 슬라이드에서 가장 크게 표시될 1개 요소 (숫자, 수치, 핵심어)
- highlight_element: 슬라이드 전체에서 bold+색상 강조할 1개 문구만 지정
- highlight_type: number | phrase | icon
- key_stat: eval_section/case_study 레이아웃에서 우상단 대형 수치 callout (선택적)
- chart_title: 차트가 있는 경우 반드시 결론형 문장으로 작성"""


# ── Step 3: 스토리보드 생성 프롬프트 ────────────────────────────────────────

STORYBOARD_SYSTEM = """당신은 공공 입찰 발표 자료의 슬라이드 내용을 작성하는 전문가입니다.
확정된 목차(TOC)와 시각 설계(Visual Brief)를 기반으로 각 슬라이드의 본문을 작성합니다.
응답은 반드시 JSON 형식으로만 제공합니다.

스토리보드 작성 규칙:
1. 모든 bullet의 근거는 반드시 proposal_sections에서 찾아라. 새 내용을 창작하지 말라.
2. Visual Brief의 composition(레이아웃)을 반드시 따르라. 임의 변경 금지.
3. highlight 필드: Visual Brief의 highlight_element를 그대로 사용, 슬라이드 전체에서 1개만.
4. 각 슬라이드의 bullet은 해당 섹션 evaluator_check_points를 순서대로 커버하라.
5. 정량 수치(%, 기간, 비용 절감액)가 포함된 bullet을 슬라이드당 최소 1개 포함하라.
6. win_theme.primary_message는 표지 subtitle, 이기는전략 headline, 마지막 슬라이드 headline에 명시하라.
7. speaker_notes는 3개 섹션으로 구성하라:
   [발표 스크립트] 평가위원이 이 항목에서 확인하는 것은 ~입니다. (2~3문장)
   [예상 질문] 평가위원이 물어볼 수 있는 질문 1~2개 (Q: 형식)
   [답변 구조] 결론 → 근거 2개 → 재확인 순서로 30초 답변 준비
   [전환 멘트] 다음 슬라이드로 자연스럽게 연결하는 한 문장
8. 각 슬라이드의 title은 TOC의 assertion title을 그대로 유지하라. 임의로 변경 금지.
9. comparison 레이아웃: table 필드 + competitor_label 필드 필수.
10. team 레이아웃: team_rows 필드 필수.
11. 6×6 규칙: bullets는 슬라이드당 최대 6개, 각 bullet은 핵심 키워드 중심 30자 이내.
    단, sub 필드를 활용해 중요 세부 내용은 생략하지 말라.
12. numbers_callout 레이아웃: numbers 필드 필수 [{value, label, description}] 3~4개.
13. process_flow 레이아웃: steps 필드 필수 [{name, description, outputs}] 3~5단계.
14. problem_sync 레이아웃: current_state + pain_points + problem_statement 필수.
15. quote_highlight 레이아웃: quote + source + context 필수.
16. split_panel 레이아웃: chart_data + chart_title + f_pattern_anchor + points 필드 필수.
    - chart_data: {"chart_type": "bar|line", "categories": [...], "series": [{"name": "...", "values": [...]}]}
    - points: [{"headline": "...", "sub_text": "...", "emphasis_value": "강조수치"}] 2~4개
17. numbered_strategy 레이아웃: points 필드 필수.
    - points: [{"num": 1, "headline": "...", "sub_text": "...", "emphasis_value": "수치"}]
18. case_study 레이아웃: cases 필드 필수.
    - cases: [{"client": "발주처/기관명", "project": "사업명", "challenge": "핵심 과제",
               "solution": "당사 해결 방법", "result": "정량 성과", "relevance": "이번 사업과의 연관성"}]
    - 2~3개 사례, 정량 성과 필수, proposal_sections에서 실제 수행 실적만 사용
19. 앞 슬라이드가 다음 슬라이드에 대한 자연스러운 질문을 유발하는 흐름을 유지하라.
20. bullets는 str 또는 {"text": "...", "sub": "..."} 혼합 가능:
    - str: 단순 bullet
    - dict: text(주요 메시지 30자 이내) + sub(보조 설명, 들여쓰기로 표시)"""

STORYBOARD_USER = """확정된 목차와 시각 설계를 기반으로 각 슬라이드의 내용을 작성해주세요.

## 확정된 목차 (TOC)
{toc}

## 시각 설계 전략 (Visual Brief)
{visual_brief}

## Win Theme
{win_theme}

## 차별화 포인트
{differentiation_strategy}

## 평가위원 관점
{evaluator_perspective}

## 제안서 본문 (섹션별)
{proposal_sections}

## 추진 계획
{implementation_checklist}

## 투입 인력 계획
{team_plan}

반드시 아래 JSON 형식으로 응답하세요 (TOC의 모든 슬라이드 포함):
{{
    "slides": [
        {{
            "slide_num": 1,
            "layout": "cover",
            "title": "사업명",
            "subtitle": "win_theme.primary_message 그대로",
            "highlight": {{"phrase": "핵심 선언 문구"}},
            "speaker_notes": "[발표 스크립트] ...\n[전환 멘트] 먼저 발표 순서를 말씀드리겠습니다."
        }},
        {{
            "slide_num": 3,
            "layout": "key_message",
            "title": "이기는 전략",
            "headline": "win_theme.primary_message 그대로",
            "bullets": [
                "근거 pillar 1",
                {{"text": "근거 pillar 2 핵심 메시지", "sub": "보조 설명 또는 수치"}},
                "근거 pillar 3"
            ],
            "highlight": {{"phrase": "가장 강력한 pillar 문구"}},
            "speaker_notes": "[발표 스크립트] ...\n[예상 질문] Q: ...\n[답변 구조] 결론: ...\n[전환 멘트] ..."
        }},
        {{
            "slide_num": 5,
            "layout": "split_panel",
            "title": "TOC의 title 그대로",
            "eval_badge": "TOC의 eval_badge 그대로",
            "chart_title": "당사 처리속도 경쟁사 대비 40% 우위 (동일 조건 기준)",
            "chart_data": {{
                "chart_type": "bar",
                "categories": ["일반적 접근", "당사"],
                "series": [{{"name": "처리속도(초)", "values": [3.0, 1.8]}}]
            }},
            "f_pattern_anchor": "40%",
            "points": [
                {{"headline": "특허 기반 알고리즘 최적화", "sub_text": "3건 특허 적용으로 처리 효율 극대화", "emphasis_value": "3건 특허"}},
                {{"headline": "클라우드 네이티브 아키텍처", "sub_text": "자동 스케일링으로 부하 분산 처리", "emphasis_value": "99.9% 가용성"}},
                {{"headline": "실시간 모니터링 체계", "sub_text": "24/7 이상 감지 및 자동 복구", "emphasis_value": "MTTR < 5분"}}
            ],
            "highlight": {{"phrase": "40% 속도 향상"}},
            "speaker_notes": "[발표 스크립트] ...\n[예상 질문] Q: ...\n[답변 구조] 결론: ...\n[전환 멘트] ..."
        }},
        {{
            "slide_num": 6,
            "layout": "case_study",
            "title": "TOC의 title 그대로",
            "eval_badge": "TOC의 eval_badge 그대로",
            "key_stat": "97점",
            "cases": [
                {{
                    "client": "○○부처",
                    "project": "행정정보 통합 시스템 구축",
                    "challenge": "레거시 시스템 통합 및 무중단 전환",
                    "solution": "당사 마이그레이션 프레임워크 적용",
                    "result": "납기 100% 준수, 만족도 97점, 오류 발생 0건",
                    "relevance": "이번 사업과 동일한 레거시 통합 과제 해결 선례"
                }}
            ],
            "highlight": {{"phrase": "납기 100% 준수"}},
            "speaker_notes": "[발표 스크립트] ...\n[예상 질문] Q: ...\n[답변 구조] 결론: ...\n[전환 멘트] ..."
        }},
        {{
            "slide_num": 7,
            "layout": "eval_section",
            "title": "TOC의 title 그대로",
            "eval_badge": "TOC의 eval_badge 그대로",
            "key_stat": "97%",
            "bullets": [
                {{"text": "evaluator_check_point1 기반 압축 문장", "sub": "proposal_sections 근거 수치"}},
                "evaluator_check_point2 기반 문장",
                "정량 수치 포함 문장 (처리 속도 40% 향상 등)"
            ],
            "highlight": {{"phrase": "가장 강력한 근거 문구 1개"}},
            "speaker_notes": "[발표 스크립트] ...\n[예상 질문] Q: ...\n[답변 구조] 결론: ...\n[전환 멘트] ..."
        }},
        {{
            "slide_num": 8,
            "layout": "numbered_strategy",
            "title": "TOC의 title 그대로",
            "eval_badge": "TOC의 eval_badge 그대로",
            "points": [
                {{"num": 1, "headline": "직접 배포 역량 강화", "sub_text": "R-Power BI 출시 전 역량 확보", "emphasis_value": "2024 Q1"}},
                {{"num": 2, "headline": "R-Solution 중심 시장 점유 확대", "sub_text": "R-App에서 R-Solution으로 전환 가속", "emphasis_value": "점유율 3배↑"}},
                {{"num": 3, "headline": "MS 파트너십 시너지 극대화", "sub_text": "R-Power BI와 판매·비용 시너지", "emphasis_value": "영업이익 60%↑"}}
            ],
            "highlight": {{"phrase": "가장 핵심 포인트 문구"}},
            "speaker_notes": "[발표 스크립트] ...\n[예상 질문] Q: ...\n[답변 구조] 결론: ...\n[전환 멘트] ..."
        }},
        {{
            "slide_num": 9,
            "layout": "comparison",
            "title": "TOC의 title 그대로",
            "eval_badge": "TOC의 eval_badge 그대로",
            "competitor_label": "일반적 접근",
            "table": [
                {{"dimension": "응답 속도", "competitor": "평균 3초", "ours": "평균 1.8초 (40% 향상)"}},
                {{"dimension": "정확도", "competitor": "92%", "ours": "97% (5pp 향상)"}}
            ],
            "highlight": {{"phrase": "가장 강력한 차별점 문구"}},
            "speaker_notes": "[발표 스크립트] ...\n[예상 질문] Q: ...\n[답변 구조] 결론: ...\n[전환 멘트] ..."
        }},
        {{
            "slide_num": 99,
            "layout": "closing",
            "title": "왜 우리인가",
            "headline": "win_theme.primary_message 그대로",
            "bullets": ["차별화포인트1", "차별화포인트2", "차별화포인트3"],
            "highlight": {{"phrase": "최종 선택을 유도하는 핵심 문구"}},
            "speaker_notes": "[발표 스크립트] ...\n[예상 질문] Q: ...\n[답변 구조] 결론: ..."
        }}
    ],
    "eval_coverage": {{
        "평가항목명1": "slide_3",
        "평가항목명2": "slide_4"
    }}
}}

규칙:
- TOC에 있는 모든 슬라이드를 포함하고 slide_num, layout, title, eval_badge는 TOC 값 그대로 유지
- Visual Brief의 composition(레이아웃)을 반드시 따를 것
- highlight: Visual Brief의 highlight_element 그대로 (슬라이드 전체 1개만)
- bullets: str 또는 {{"text":..., "sub":...}} 혼합 가능, 슬라이드당 최대 6개
- split_panel: chart_data + chart_title + f_pattern_anchor + points 필수
- numbered_strategy: points 필드 필수
- eval_section: key_stat 필드 선택적 (우상단 대형 수치 callout)
- case_study: cases 필드 필수 (2~3개, 정량 성과 포함, proposal_sections 실적에서 추출)
- speaker_notes: 4섹션 구조 ([발표 스크립트] / [예상 질문] / [답변 구조] / [전환 멘트])
- eval_coverage: 각 평가항목명이 몇 번 슬라이드에서 다뤄지는지 매핑"""


# ── 입력 조립 ────────────────────────────────────────────────────────────────

def _build_input(
    phase2: Phase2Artifact,
    phase3: Phase3Artifact,
    phase4: Phase4Artifact,
    rfp_data: Optional[RFPData],
) -> dict:
    """Phase 2/3/4 Artifact → Claude 입력 dict 조립"""
    sorted_plan = sorted(
        phase3.section_plan,
        key=lambda s: s.get("score_weight", 0) if isinstance(s, dict) else 0,
        reverse=True,
    )
    return {
        "project_name": (rfp_data.project_name if rfp_data else "") or "",
        "evaluation_weights": phase2.evaluation_weights,
        "evaluator_perspective": phase2.structured_data.get("evaluator_perspective", {}),
        "section_plan": sorted_plan,
        "win_theme": phase3.win_theme,
        "win_strategy": phase3.win_strategy,
        "differentiation_strategy": phase3.differentiation_strategy,
        "implementation_checklist": phase3.implementation_checklist,
        "proposal_sections": phase4.sections,
        "team_plan": phase3.team_plan,
    }


# ── 공개 인터페이스 ───────────────────────────────────────────────────────────

async def generate_presentation_slides(
    phase2: Phase2Artifact,
    phase3: Phase3Artifact,
    phase4: Phase4Artifact,
    rfp_data: Optional[RFPData] = None,
) -> dict:
    """
    3-step 파이프라인:
      Step 1 — TOC 생성: 평가항목 배점 기준 목차 설계 (25~35장)
      Step 2 — Visual Brief: 슬라이드별 시각 증명 전략 결정 (F-Pattern, 하이라이트 1개)
      Step 3 — 스토리보드: Visual Brief 기반 슬라이드별 본문/화자노트 작성

    Returns:
        {slides: [...], total_slides: N, eval_coverage: {...}}
    """
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    inp = _build_input(phase2, phase3, phase4, rfp_data)

    # ── Step 1: TOC 생성 ──────────────────────────────────────────────────────
    logger.info(f"[Step 1] TOC 생성 요청 — 섹션 수: {len(inp['section_plan'])}")
    toc_response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=4096,
        system=TOC_SYSTEM,
        messages=[{
            "role": "user",
            "content": TOC_USER.format(
                project_name=inp["project_name"],
                section_plan=json.dumps(inp["section_plan"], ensure_ascii=False),
                win_theme=json.dumps(inp["win_theme"], ensure_ascii=False),
            ),
        }],
    )
    toc_result = extract_json_from_response(toc_response.content[0].text)
    toc = toc_result.get("toc", [])
    logger.info(f"[Step 1] TOC 완료 — {len(toc)}개 슬라이드: {[s['title'] for s in toc]}")

    # ── Step 2: Visual Brief 생성 ──────────────────────────────────────────────
    logger.info(f"[Step 2] Visual Brief 생성 요청 — {len(toc)}개 슬라이드")
    vb_response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=4096,
        system=VISUAL_BRIEF_SYSTEM,
        messages=[{
            "role": "user",
            "content": VISUAL_BRIEF_USER.format(
                toc=json.dumps(toc, ensure_ascii=False),
                win_theme=json.dumps(inp["win_theme"], ensure_ascii=False),
                differentiation_strategy=json.dumps(
                    inp["differentiation_strategy"], ensure_ascii=False
                ),
            ),
        }],
    )
    vb_result = extract_json_from_response(vb_response.content[0].text)
    visual_briefs = vb_result.get("visual_briefs", [])
    logger.info(f"[Step 2] Visual Brief 완료 — {len(visual_briefs)}개 슬라이드 시각 전략 확정")

    # ── Step 3: 스토리보드 생성 ───────────────────────────────────────────────
    logger.info(f"[Step 3] 스토리보드 생성 요청 — {len(toc)}개 슬라이드")
    storyboard_response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=16384,
        system=STORYBOARD_SYSTEM,
        messages=[{
            "role": "user",
            "content": STORYBOARD_USER.format(
                toc=json.dumps(toc, ensure_ascii=False),
                visual_brief=json.dumps(visual_briefs, ensure_ascii=False),
                win_theme=json.dumps(inp["win_theme"], ensure_ascii=False),
                differentiation_strategy=json.dumps(
                    inp["differentiation_strategy"], ensure_ascii=False
                ),
                evaluator_perspective=json.dumps(
                    inp["evaluator_perspective"], ensure_ascii=False
                ),
                proposal_sections=json.dumps(inp["proposal_sections"], ensure_ascii=False),
                implementation_checklist=json.dumps(
                    inp["implementation_checklist"], ensure_ascii=False
                ),
                team_plan=json.dumps(inp["team_plan"], ensure_ascii=False),
            ),
        }],
    )
    result = extract_json_from_response(storyboard_response.content[0].text)

    # total_slides는 TOC 기준으로 보정
    result["total_slides"] = toc_result.get("total_slides", len(toc))

    logger.info(
        f"[Step 3] 스토리보드 완료 — {result.get('total_slides', '?')}장 "
        f"/ eval_coverage: {list(result.get('eval_coverage', {}).keys())}"
    )
    return result
