"""
v4.0: 모의 평가 + 평가결과 + Closing 노드 (6A, 7, 8)

6A — mock_evaluation: 제안서 + PPT 완성 후 모의 평가 시뮬레이션 (RFP 기반, 6명 평가위원)
7  — eval_result: 실제 평가 결과 기록 (입력 대기)
8  — project_closing: 프로젝트 종료 처리 (KB 업데이트, 아카이브)

v6.0: 상세한 평가위원 프로필 + 평가항목별 세부 점수 산출 + 분포 분석
"""

import asyncio
import logging
import statistics

from app.graph.state import ProposalState
from app.services.claude_client import claude_generate

logger = logging.getLogger(__name__)


# ── 평가위원 프로필 정의 ──

def _create_evaluator_profiles() -> list[dict]:
    """산학연 2명씩 총 6명 평가위원 프로필 생성"""
    return [
        {
            "id": "evaluator_1",
            "name": "이산업",
            "title": "OOO 회사 개발이사",
            "type": "산업계",
            "subtype": "발주유사",
            "experience_years": 15,
            "background": "유사 프로젝트 5건 경험, PM 역할",
            "perspective": ["사업 실현가능성", "비용 효율성", "시간 내 납기 가능성"],
            "evaluation_bias": {
                "tendency": "보수적",
                "scoring_range": (0, 90),
                "weight": 1.0
            }
        },
        {
            "id": "evaluator_2",
            "name": "박경쟁",
            "title": "경쟁사 대표",
            "type": "산업계",
            "subtype": "경쟁",
            "experience_years": 20,
            "background": "동일 분야 경쟁사 CEO, 제안 경험 다수",
            "perspective": ["차별화 정도", "경쟁우위 분석", "시장 영향도"],
            "evaluation_bias": {
                "tendency": "중도",
                "scoring_range": (30, 95),
                "weight": 1.0
            }
        },
        {
            "id": "evaluator_3",
            "name": "최교수",
            "title": "OOO대학교 공학과 교수",
            "type": "학계",
            "subtype": "혁신성",
            "experience_years": 25,
            "background": "기술 혁신 논문 200편 이상, 정부 R&D 평가위원",
            "perspective": ["기술 혁신성", "이론적 근거", "새로운 접근방식"],
            "evaluation_bias": {
                "tendency": "낙관적",
                "scoring_range": (40, 98),
                "weight": 1.1
            }
        },
        {
            "id": "evaluator_4",
            "name": "정소장",
            "title": "OOO 연구소 소장",
            "type": "학계",
            "subtype": "실현가능성",
            "experience_years": 18,
            "background": "프로토타입 개발 경험 다수, 현장 기술 전문",
            "perspective": ["실현가능성", "기술 완성도", "리스크 관리"],
            "evaluation_bias": {
                "tendency": "중도",
                "scoring_range": (25, 85),
                "weight": 1.0
            }
        },
        {
            "id": "evaluator_5",
            "name": "홍정책",
            "title": "과학기술정보통신부 과장",
            "type": "연구계/공공",
            "subtype": "정책",
            "experience_years": 12,
            "background": "정부 R&D 정책 담당, 사업 심사 경험 많음",
            "perspective": ["정부 정책 부합도", "법규 준수", "공공성 및 파급효과"],
            "evaluation_bias": {
                "tendency": "보수적",
                "scoring_range": (0, 88),
                "weight": 0.9
            }
        },
        {
            "id": "evaluator_6",
            "name": "강협회",
            "title": "한국OOO협회 부회장",
            "type": "연구계/공공",
            "subtype": "표준",
            "experience_years": 22,
            "background": "산업표준 위원, 협회 기술위원장",
            "perspective": ["산업표준 준수", "산업계 요구도", "기술 확산 가능성"],
            "evaluation_bias": {
                "tendency": "중도",
                "scoring_range": (35, 90),
                "weight": 1.0
            }
        }
    ]


# ── 6A: 모의 평가 ──

async def mock_evaluation(state: ProposalState) -> dict:
    """RFP 평가항목 기반 6명 평가위원 모의 평가 시뮬레이션.

    - RFP의 eval_items 추출
    - 6명의 평가위원 프로필 로드
    - 평가항목별로 각 평가위원이 점수 산출
    - 평가위원별 총점 계산
    - 분포 분석 및 합의도 평가
    - 종합 보고서 생성
    """
    rfp = state.get("rfp_analysis")
    rfp_dict = rfp.model_dump() if hasattr(rfp, "model_dump") else (rfp if isinstance(rfp, dict) else {})
    strategy = state.get("strategy")
    strategy_dict = strategy.model_dump() if hasattr(strategy, "model_dump") else (strategy if isinstance(strategy, dict) else {})
    sections = state.get("proposal_sections", [])

    try:
        # 1️⃣ RFP에서 평가항목 추출
        eval_items = rfp_dict.get("eval_items", [])
        if not eval_items:
            logger.warning("RFP에 평가항목이 없어서 모의평가 스킵")
            return {
                "mock_evaluation_result": {"status": "skipped", "reason": "no_eval_items"},
                "current_phase": "mock_evaluation_complete",
            }

        # 2️⃣ 평가위원 프로필 로드
        evaluators = _create_evaluator_profiles()

        # 3️⃣ 섹션 요약 (토큰 절약)
        section_summaries = []
        for s in sections[:12]:
            sd = s.model_dump() if hasattr(s, "model_dump") else (s if isinstance(s, dict) else {})
            section_summaries.append({
                "title": sd.get("title", ""),
                "content_preview": sd.get("content", "")[:400],
            })

        # 4️⃣ 각 평가항목별로 6명이 점수 산출
        evaluation_results = {}

        for item in eval_items:
            item_id = item.get("item_id", item.get("id", ""))
            item_title = item.get("title", "")
            max_score = item.get("score", 20)

            item_scores_by_evaluator = {}

            for evaluator in evaluators:
                score_result = await _score_evaluation_item(
                    item=item,
                    evaluator=evaluator,
                    sections=section_summaries,
                    strategy=strategy_dict,
                )
                item_scores_by_evaluator[evaluator["id"]] = score_result

            # 항목별 분포 계산
            scores_list = [s["score"] for s in item_scores_by_evaluator.values()]
            distribution = _calculate_distribution(scores_list)

            evaluation_results[item_id] = {
                "item_id": item_id,
                "item_title": item_title,
                "max_score": max_score,
                "scores_by_evaluator": item_scores_by_evaluator,
                "average_score": distribution["mean"],
                "distribution": distribution,
                "consensus": _assess_consensus(scores_list),
            }

        # 5️⃣ 평가위원별 총점 계산
        evaluator_results = {}
        for evaluator in evaluators:
            total_score = 0
            for item_id, result in evaluation_results.items():
                eval_score = result["scores_by_evaluator"][evaluator["id"]]["score"]
                total_score += eval_score

            evaluator_results[evaluator["id"]] = {
                "evaluator_id": evaluator["id"],
                "name": evaluator["name"],
                "title": evaluator["title"],
                "type": evaluator["type"],
                "total_score": total_score,
            }

        # 순위 지정
        sorted_results = sorted(
            evaluator_results.items(),
            key=lambda x: x[1]["total_score"],
            reverse=True
        )
        for rank, (eval_id, result) in enumerate(sorted_results, 1):
            result["rank"] = rank

        # 6️⃣ 최종 종합점수 (배점 가중)
        final_score = 0
        category_scores = {}

        for item_id, result in evaluation_results.items():
            item_avg = result["average_score"]
            item_weight = result["max_score"]
            final_score += item_avg * (item_weight / 100)

            category = result["item_title"].split("_")[0] if "_" in result["item_title"] else "기타"
            if category not in category_scores:
                category_scores[category] = []
            category_scores[category].append(item_avg)

        category_averages = {
            cat: sum(scores) / len(scores)
            for cat, scores in category_scores.items()
        }

        # 7️⃣ 종합 평가 결과 생성
        mock_eval_report = {
            "evaluation_metadata": {
                "total_evaluators": len(evaluators),
                "evaluators_by_type": {
                    "산업계": 2,
                    "학계": 2,
                    "연구계/공공": 2,
                },
                "total_evaluation_items": len(eval_items),
                "total_score": final_score,
                "max_total_score": 100,
                "percentage": (final_score / 100) * 100,
            },
            "evaluators": [
                {
                    "id": e["id"],
                    "name": e["name"],
                    "title": e["title"],
                    "type": e["type"],
                    "experience_years": e["experience_years"],
                }
                for e in evaluators
            ],
            "evaluation_items": evaluation_results,
            "evaluator_scores": evaluator_results,
            "category_scores": category_averages,
            "final_score": final_score,
            "win_probability": _assess_win_probability(final_score),
            "strengths": await _summarize_strengths(evaluation_results),
            "weaknesses": await _summarize_weaknesses(evaluation_results),
            "high_consensus_items": _find_high_consensus_items(evaluation_results),
            "low_consensus_items": _find_low_consensus_items(evaluation_results),
        }

        return {
            "mock_evaluation_result": mock_eval_report,
            "current_phase": "mock_evaluation_complete",
        }

    except Exception as e:
        logger.error(f"mock_evaluation 실패: {e}", exc_info=True)
        return {
            "mock_evaluation_result": {"error": str(e)},
            "current_phase": "mock_evaluation_error",
        }


# ── 헬퍼 함수 ──

async def _score_evaluation_item(
    item: dict,
    evaluator: dict,
    sections: list[dict],
    strategy: dict
) -> dict:
    """평가위원이 특정 평가항목에 대해 점수를 산출"""

    item_title = item.get("title", "")
    max_score = item.get("score", 20)
    item_criteria = item.get("criteria", [])

    # 제안서 콘텐츠 요약
    section_content = "\n".join([
        f"## {s['title']}\n{s['content_preview']}"
        for s in sections[:3]
    ])

    prompt = f"""당신은 다음의 평가위원입니다:
이름: {evaluator['name']}
직책: {evaluator['title']}
경력: {evaluator['experience_years']}년
유형: {evaluator['type']}
평가 관점: {', '.join(evaluator['perspective'])}

당신의 평가 성향: {evaluator['evaluation_bias']['tendency']}

다음 평가항목에 대해 점수를 부여하세요:
항목명: {item_title}
배점: {max_score}점
평가기준: {', '.join(item_criteria) if item_criteria else '없음'}

제안 내용:
{section_content}

제안 전략:
- Win Theme: {strategy.get('win_theme', '')}
- 포지셔닝: {strategy.get('positioning', '')}

다음 JSON 형식으로 점수를 부여하세요:
{{
  "score": <0 ~ {max_score} 사이의 숫자>,
  "reasoning": "평가 이유 (한국어 1-2줄)",
  "strengths": ["강점 1", "강점 2"],
  "weaknesses": ["약점 1"]
}}"""

    try:
        result = await claude_generate(
            prompt=prompt,
            response_format="json",
            temperature=0.3,
        )

        # 평가위원 성향에 따른 점수 범위 제한
        score = float(result.get("score", max_score / 2))
        scoring_range = evaluator["evaluation_bias"]["scoring_range"]

        # 배점 기준의 백분율로 변환
        base_percentage = (score / 100) * max_score if score > max_score else score
        constrained_score = max(
            scoring_range[0],
            min(scoring_range[1], score)
        )
        # max_score 범위로 정규화
        final_score = (constrained_score / 100) * max_score if constrained_score > max_score else constrained_score

        return {
            "evaluator_id": evaluator["id"],
            "score": final_score,
            "max_score": max_score,
            "reasoning": result.get("reasoning", ""),
            "strengths": result.get("strengths", []),
            "weaknesses": result.get("weaknesses", []),
        }

    except Exception as e:
        logger.error(f"평가항목 점수 산출 실패 ({item_title}, {evaluator['name']}): {e}")
        # 폴백: 중간값 반환
        return {
            "evaluator_id": evaluator["id"],
            "score": max_score / 2,
            "max_score": max_score,
            "reasoning": f"오류로 인해 중간값 부여: {str(e)}",
            "strengths": [],
            "weaknesses": [],
        }


def _calculate_distribution(scores: list[float]) -> dict:
    """점수 분포 계산"""
    if not scores:
        return {}

    return {
        "mean": statistics.mean(scores),
        "median": statistics.median(scores),
        "stdev": statistics.stdev(scores) if len(scores) > 1 else 0,
        "variance": statistics.variance(scores) if len(scores) > 1 else 0,
        "min": min(scores),
        "max": max(scores),
        "range": (min(scores), max(scores)),
        "scores": scores,
    }


def _assess_consensus(scores: list[float]) -> dict:
    """평가위원 의견 일치도 평가"""
    if not scores or len(scores) < 2:
        return {"consensus_level": "불명확", "stdev": 0}

    distribution = _calculate_distribution(scores)
    stdev = distribution["stdev"]

    if stdev < 3:
        consensus_level = "높음 (강한 합의)"
    elif stdev < 6:
        consensus_level = "중간 (약한 합의)"
    else:
        consensus_level = "낮음 (의견 분분)"

    return {
        "consensus_level": consensus_level,
        "stdev": round(stdev, 2),
        "interpretation": f"평가위원들의 의견이 {'일치' if stdev < 6 else '분분'}합니다.",
    }


async def _summarize_strengths(evaluation_results: dict) -> list[str]:
    """평가 결과에서 강점 요약"""
    strengths = {}

    for item_id, result in evaluation_results.items():
        for eval_id, score_result in result["scores_by_evaluator"].items():
            for strength in score_result.get("strengths", []):
                strengths[strength] = strengths.get(strength, 0) + 1

    # 언급 횟수 상위 5개
    top_strengths = sorted(
        strengths.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

    return [s[0] for s in top_strengths]


async def _summarize_weaknesses(evaluation_results: dict) -> list[str]:
    """평가 결과에서 약점 요약"""
    weaknesses = {}

    for item_id, result in evaluation_results.items():
        for eval_id, score_result in result["scores_by_evaluator"].items():
            for weakness in score_result.get("weaknesses", []):
                weaknesses[weakness] = weaknesses.get(weakness, 0) + 1

    # 언급 횟수 상위 5개
    top_weaknesses = sorted(
        weaknesses.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

    return [w[0] for w in top_weaknesses]


def _find_high_consensus_items(evaluation_results: dict) -> list[str]:
    """높은 합의도를 보인 항목 찾기"""
    high_consensus = []

    for item_id, result in evaluation_results.items():
        if result["consensus"]["stdev"] < 3:
            high_consensus.append({
                "item_id": item_id,
                "item_title": result["item_title"],
                "consensus_level": result["consensus"]["consensus_level"],
                "average_score": round(result["average_score"], 2),
            })

    return high_consensus


def _find_low_consensus_items(evaluation_results: dict) -> list[str]:
    """낮은 합의도를 보인 항목 찾기 (논쟁 여지 있는 항목)"""
    low_consensus = []

    for item_id, result in evaluation_results.items():
        if result["consensus"]["stdev"] >= 6:
            low_consensus.append({
                "item_id": item_id,
                "item_title": result["item_title"],
                "consensus_level": result["consensus"]["consensus_level"],
                "average_score": round(result["average_score"], 2),
                "stdev": round(result["consensus"]["stdev"], 2),
            })

    return low_consensus


def _assess_win_probability(final_score: float) -> str:
    """최종 점수 기반 수주 가능성 평가"""
    if final_score >= 85:
        return "높음 (85점 이상)"
    elif final_score >= 70:
        return "보통 (70-84점)"
    else:
        return "낮음 (70점 미만)"


# ── 7: 평가결과 ──

async def eval_result_node(state: ProposalState) -> dict:
    """평가결과 기록 노드.

    실제 결과는 사용자가 리뷰 시 입력 (interrupt).
    mock_evaluation_result를 기본값으로 표시.
    """
    mock = state.get("mock_evaluation_result", {})

    # 기존 결과가 있으면 그대로 유지
    existing = state.get("eval_result")
    if existing:
        return {"current_step": "eval_result_recorded"}

    # 기본값: 모의 평가 결과 기반
    return {
        "eval_result": {
            "source": "mock_evaluation",
            "mock_average_score": mock.get("aggregate", {}).get("average_score"),
            "mock_win_probability": mock.get("aggregate", {}).get("win_probability"),
            "actual_result": None,  # 사용자가 리뷰에서 입력
            "actual_score": None,
            "actual_rank": None,
            "lessons_learned": [],
        },
        "current_step": "eval_result_pending",
    }


# ── 8: Closing ──

async def project_closing(state: ProposalState) -> dict:
    """프로젝트 종료 처리.

    - KB 업데이트 트리거 (수주/패찰 결과 기반)
    - 교훈 아카이브
    - 프로젝트 상태 → closed
    """
    proposal_id = state.get("project_id", "")
    eval_data = state.get("eval_result", {})
    actual_result = eval_data.get("actual_result")  # won / lost / None

    # KB 업데이트 (비동기 fire-and-forget)
    if actual_result and proposal_id:
        _fire_kb_update(proposal_id, actual_result, state)

    # 프로젝트 상태 업데이트
    if proposal_id:
        _fire_status_update(proposal_id, actual_result)

    return {
        "project_closing_result": {
            "status": "closed",
            "actual_result": actual_result,
            "kb_updated": actual_result is not None,
            "lessons_count": len(eval_data.get("lessons_learned", [])),
        },
        "current_step": "project_closed",
    }


def _fire_kb_update(proposal_id: str, result: str, state: ProposalState) -> None:
    """수주/패찰 결과를 KB에 반영 (fire-and-forget)."""
    async def _update():
        try:
            from app.services.kb_updater import update_from_result
            await update_from_result(proposal_id, result, state)
        except Exception as e:
            logger.warning(f"KB 업데이트 실패 (무시): {e}")

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_update())
    except RuntimeError:
        pass


def _fire_status_update(proposal_id: str, result: str | None) -> None:
    """proposals 테이블 상태를 closed/won/lost로 업데이트."""
    async def _update():
        try:
            from app.utils.supabase_client import get_async_client
            client = await get_async_client()
            status = "won" if result == "won" else "lost" if result == "lost" else "completed"
            await client.table("proposals").update({
                "status": status,
                "current_phase": "closed",
            }).eq("id", proposal_id).execute()
        except Exception as e:
            logger.warning(f"프로젝트 상태 업데이트 실패: {e}")

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_update())
    except RuntimeError:
        pass
