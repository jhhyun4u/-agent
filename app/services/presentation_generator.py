"""발표 자료 슬라이드 JSON 생성 서비스 — 2-step 파이프라인 (TOC → 스토리보드)"""

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
평가위원이 배점표에 따라 채점하는 발표 심사를 위해 최적의 슬라이드 목차를 구성합니다.
응답은 반드시 JSON 형식으로만 제공합니다.

목차 설계 규칙:
1. 고정 슬라이드(표지 cover, 이기는전략 key_message, 마무리 closing)는 반드시 포함하라.
2. 평가항목 슬라이드는 score_weight 내림차순으로 배치하라.
3. score_weight >= 15점: 전용 슬라이드 1장
4. score_weight 10-14점: 전용 슬라이드 1장 (내용 압축)
5. score_weight <= 9점: 유사 섹션과 병합 (한 슬라이드에 2개)
6. 추진일정/타임라인은 timeline 레이아웃 사용
7. 인력투입계획은 team 레이아웃 사용
8. 슬라이드 title은 반드시 "주어 + 서술어" 형식의 완결 주장 문장(assertion)으로 작성하라.
   예: ❌ "사업 이해도" → ✅ "당사는 현장 경험 5년으로 발주처 핵심 요구사항을 정확히 이해함"
   예: ❌ "기술 역량"   → ✅ "3개 특허 기반 고유 기술로 경쟁사 대비 처리 속도 40% 우위 확보"
   단, cover(표지)와 closing 슬라이드 title은 예외 (사업명, "왜 우리인가" 유지)"""

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
            "layout": "key_message",
            "title": "이기는 전략",
            "eval_badge": "",
            "target_section": "",
            "score_weight": 0
        }},
        {{
            "slide_num": 3,
            "layout": "eval_section",
            "title": "슬라이드 제목 (평가항목 반영)",
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
    "total_slides": 8
}}

규칙:
- layout 값: cover | key_message | eval_section | comparison | timeline | team | closing
- slide_num은 1부터 연속 정수 (99 사용 금지, 마지막 슬라이드도 실제 번호 사용)
- eval_badge: "평가항목명 | XX점" 형식 (eval_section/timeline/team만)
- target_section: section_plan의 section_name 값 그대로"""


# ── Step 2: 스토리보드 생성 프롬프트 ────────────────────────────────────────

STORYBOARD_SYSTEM = """당신은 공공 입찰 발표 자료의 슬라이드 내용을 작성하는 전문가입니다.
확정된 목차(TOC)를 기반으로 각 슬라이드의 본문을 작성합니다.
응답은 반드시 JSON 형식으로만 제공합니다.

스토리보드 작성 규칙:
1. 모든 bullet의 근거는 반드시 proposal_sections에서 찾아라. 새 내용을 창작하지 말라.
2. 각 슬라이드의 bullet은 해당 섹션 evaluator_check_points를 순서대로 커버하라.
3. 정량 수치(%, 기간, 비용 절감액)가 포함된 bullet을 슬라이드당 최소 1개 포함하라.
4. win_theme.primary_message는 표지 subtitle, 슬라이드 2 headline, 마지막 슬라이드 headline에 명시하라.
5. 나머지 슬라이드의 speaker_notes 마지막 문장에서 Win Theme과 연결하라.
6. speaker_notes는 "평가위원이 이 항목에서 확인하는 것은" 형식으로 시작하라.
7. 각 슬라이드의 title은 TOC의 assertion title을 그대로 유지하라. 임의로 변경 금지.
8. comparison 레이아웃: table 필드를 반드시 포함하라. dimension/competitor/ours 값은 differentiation_strategy에서 추출하라.
9. team 레이아웃: team_rows 필드를 반드시 포함하라. role/grade/duration/task 값은 team_plan에서 추출하라. team_plan이 없으면 proposal_sections의 인력투입계획 섹션을 참조하라."""

STORYBOARD_USER = """확정된 목차를 기반으로 각 슬라이드의 내용을 작성해주세요.

## 확정된 목차 (TOC)
{toc}

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

반드시 아래 JSON 형식으로 응답하세요 (TOC의 모든 슬라이드 포함):
{{
    "slides": [
        {{
            "slide_num": 1,
            "layout": "cover",
            "title": "사업명",
            "subtitle": "win_theme.primary_message 그대로",
            "speaker_notes": "발표 시작 스크립트 (3문장 이상)"
        }},
        {{
            "slide_num": 2,
            "layout": "key_message",
            "title": "이기는 전략",
            "headline": "win_theme.primary_message 그대로",
            "bullets": ["근거 pillar 1", "근거 pillar 2", "근거 pillar 3"],
            "speaker_notes": "평가위원이 이 항목에서 확인하는 것은 우리의 핵심 강점입니다. ..."
        }},
        {{
            "slide_num": 3,
            "layout": "eval_section",
            "title": "TOC의 title 그대로",
            "eval_badge": "TOC의 eval_badge 그대로",
            "bullets": [
                "evaluator_check_point1 기반 압축 문장 (proposal_sections 근거)",
                "evaluator_check_point2 기반 압축 문장",
                "정량 수치 포함 문장 (처리 속도 40% 향상 등)"
            ],
            "speaker_notes": "평가위원이 이 항목에서 확인하는 것은 ~입니다. [근거]. [Win Theme 연결]"
        }},
        {{
            "slide_num": 5,
            "layout": "comparison",
            "title": "당사 기술은 경쟁사 대비 처리 속도 40% 우위를 갖춤",
            "eval_badge": "TOC의 eval_badge 그대로",
            "table": [
                {{"dimension": "응답 속도", "competitor": "평균 3초", "ours": "평균 1.8초 (40% 향상)"}},
                {{"dimension": "정확도", "competitor": "92%", "ours": "97% (5pp 향상)"}},
                {{"dimension": "운영 비용", "competitor": "월 500만원", "ours": "월 320만원 (36% 절감)"}}
            ],
            "speaker_notes": "평가위원이 이 항목에서 확인하는 것은 기술 차별성의 실질적 근거입니다. ..."
        }},
        {{
            "slide_num": 6,
            "layout": "team",
            "title": "검증된 전문 인력 5명으로 납기 내 완수 체계를 갖춤",
            "eval_badge": "TOC의 eval_badge 그대로",
            "team_rows": [
                {{"role": "PM", "grade": "특급", "duration": "12개월", "task": "전체 일정·품질 관리"}},
                {{"role": "수석 개발자", "grade": "고급", "duration": "10개월", "task": "핵심 모듈 설계·구현"}},
                {{"role": "UI/UX", "grade": "중급", "duration": "6개월", "task": "화면 설계 및 사용성 검증"}}
            ],
            "speaker_notes": "평가위원이 이 항목에서 확인하는 것은 투입 인력의 적정성입니다. ..."
        }},
        {{
            "slide_num": 7,
            "layout": "timeline",
            "title": "추진 계획",
            "eval_badge": "TOC의 eval_badge 그대로",
            "phases": [
                {{"name": "1단계", "duration": "1개월", "deliverables": ["산출물1", "산출물2"]}}
            ],
            "speaker_notes": "평가위원이 이 항목에서 확인하는 것은 일정 실현가능성입니다. ..."
        }},
        {{
            "slide_num": 8,
            "layout": "closing",
            "title": "왜 우리인가",
            "headline": "win_theme.primary_message 그대로",
            "bullets": ["차별화포인트1", "차별화포인트2", "차별화포인트3"],
            "speaker_notes": "..."
        }}
    ],
    "eval_coverage": {{
        "평가항목명1": "slide_3",
        "평가항목명2": "slide_4"
    }}
}}

규칙:
- TOC에 있는 모든 슬라이드를 포함하고 slide_num, layout, title, eval_badge는 TOC 값 그대로 유지
- bullets: 슬라이드당 3~5개, proposal_sections에서만 근거 추출
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
    2-step 파이프라인:
      Step 1 — TOC 생성: 평가항목 배점 기준 목차 설계
      Step 2 — 스토리보드: TOC 기반 슬라이드별 본문/화자노트 작성

    Returns:
        {slides: [...], total_slides: N, eval_coverage: {...}}
    """
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    inp = _build_input(phase2, phase3, phase4, rfp_data)

    # ── Step 1: TOC 생성 ──────────────────────────────────────────────────────
    logger.info(f"[Step 1] TOC 생성 요청 — 섹션 수: {len(inp['section_plan'])}")
    toc_response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=2048,
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

    # ── Step 2: 스토리보드 생성 ───────────────────────────────────────────────
    logger.info(f"[Step 2] 스토리보드 생성 요청 — {len(toc)}개 슬라이드")
    storyboard_response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=8192,
        system=STORYBOARD_SYSTEM,
        messages=[{
            "role": "user",
            "content": STORYBOARD_USER.format(
                toc=json.dumps(toc, ensure_ascii=False),
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
            ),
        }],
    )
    result = extract_json_from_response(storyboard_response.content[0].text)

    # total_slides는 TOC 기준으로 보정
    result["total_slides"] = toc_result.get("total_slides", len(toc))

    logger.info(
        f"[Step 2] 스토리보드 완료 — {result.get('total_slides', '?')}장 "
        f"/ eval_coverage: {list(result.get('eval_coverage', {}).keys())}"
    )
    return result
