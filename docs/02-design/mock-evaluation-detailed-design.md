# 모의평가 상세 설계
## RFP 기반 평가항목 + 6명의 평가위원 시뮬레이션

> **설계일**: 2026-03-29
> **방식**: 산학연 2명씩 총 6명 평가위원
> **기준**: RFP 평가항목/배점 (실제 기준)
> **목표**: 실제 평가 시나리오에 가장 근접한 시뮬레이션

---

## 📋 구조 개요

```
RFP 분석
  │
  ├─ eval_items 추출 (예: 기술 40점, 가격 30점, 관리 20점, 기타 10점)
  ├─ eval_criteria 추출 (예: 요구사항 충족도, 기술혁신성, 가격경쟁력 등)
  │
  ▼
평가위원 구성 (6명)
  │
  ├─ 산업계 평가위원 2명
  │  ├─ 산1: 발주기관 유사 분야 경험자 (PM/기술이사 관점)
  │  └─ 산2: 경쟁사 대표/전문가 (경쟁 관점)
  │
  ├─ 학계 평가위원 2명
  │  ├─ 학1: 대학교수 (기술 혁신성 중심)
  │  └─ 학2: 연구소 책임자 (실현가능성 중심)
  │
  └─ 연구계/공공 평가위원 2명
     ├─ 연1: 정부 R&D 담당자 (정책 부합도)
     └─ 연2: 관련 학회/협회 전문가 (표준/법규 준수)

  ▼
각 평가위원이 평가항목별 점수 산출
  │
  ├─ 평가위원별 채점 기준 정의
  │  ├─ 산업계: 실현 가능성, 비용 효율성 중심
  │  ├─ 학계: 기술 혁신성, 이론적 근거 중심
  │  └─ 연구계: 표준 준수, 사회적 영향 중심
  │
  ├─ 평가항목별 세부 평가
  │  ├─ 각 평가항목 (예: 기술혁신성)을 6명이 독립적으로 평가
  │  ├─ 점수 분포 생성 (낙관/중도/보수적 관점)
  │  └─ 평가위원별 의견/우려사항 기록
  │
  ▼
종합 평가 결과 생성
  │
  ├─ 평가항목별 평균점수 (6명 평균)
  ├─ 평가항목별 점수 분포 (표준편차)
  ├─ 평가위원별 총점 (개별 점수)
  ├─ 최종 종합점수 (가중평균)
  ├─ 평가위원별 의견 요약
  └─ 합의 불일치 분야 (표준편차 큰 항목)
```

---

## 🎯 RFP 평가항목 추출

### RFPAnalysis 구조 (기존)
```python
class RFPAnalysis(BaseModel):
    eval_method: str  # 예: "기술 40점 + 가격 30점 + 관리 20점 + 기타 10점"
    eval_items: list[dict]  # 평가항목 목록
    # [
    #   {
    #     "item_id": "T1",
    #     "category": "기술",
    #     "title": "기술혁신성",
    #     "score": 20,  # 배점
    #     "criteria": [
    #       "신규 기술 적용도",
    #       "차별화된 해결방안",
    #       "기술 완성도"
    #     ]
    #   },
    #   {
    #     "item_id": "T2",
    #     "category": "기술",
    #     "title": "요구사항 충족도",
    #     "score": 20,
    #     "criteria": [...]
    #   },
    #   ...
    # ]
```

### STEP 10A 수정: eval_items 기반 평가

```python
async def run_mock_evaluation(state: ProposalState) -> dict:
    """모의평가 - RFP 평가항목 기반, 6명 평가위원 시뮬레이션"""

    rfp = state.get("rfp_analysis")
    proposal_sections = state.get("proposal_sections")
    strategy = state.get("selected_strategy")

    # 1️⃣ RFP에서 평가항목 추출
    eval_items = rfp.get("eval_items", [])
    # [
    #   {"item_id": "T1", "category": "기술", "title": "...", "score": 20},
    #   ...
    # ]

    # 2️⃣ 평가위원 6명 구성
    evaluators = await _create_evaluators(rfp, strategy)
    # [
    #   {
    #     "id": "evaluator_1",
    #     "name": "김산업 이사",
    #     "type": "산업계",
    #     "background": "발주기관 유사분야 경험",
    #     "perspective": "실현가능성, 사업성",
    #     "bias": "보수적 (80%)"
    #   },
    #   ...
    # ]

    # 3️⃣ 각 평가항목별로 6명이 점수 산출
    evaluation_results = {}
    for item in eval_items:
        item_id = item.get("item_id")
        item_scores = {}

        for evaluator in evaluators:
            score = await _score_evaluation_item(
                item,
                evaluator,
                proposal_sections,
                strategy,
            )
            item_scores[evaluator["id"]] = score
            # {
            #   "score": 18,  # 0~20점 (배점 범위)
            #   "comment": "요구사항 충족도 우수하나 혁신성 부족",
            #   "strengths": ["항목 1", "항목 2"],
            #   "weaknesses": ["항목 A"],
            #   "concerns": ["우려사항"],
            # }

        evaluation_results[item_id] = {
            "item": item,
            "scores_by_evaluator": item_scores,
            "average_score": sum([s["score"] for s in item_scores.values()]) / len(evaluators),
            "score_distribution": _calculate_distribution([s["score"] for s in item_scores.values()]),
            "consensus": _assess_consensus(item_scores),  # 평가위원 의견 일치도
        }

    # 4️⃣ 평가위원별 총점 계산
    evaluator_total_scores = {}
    for evaluator in evaluators:
        total = 0
        for item_id, result in evaluation_results.items():
            total += result["scores_by_evaluator"][evaluator["id"]]["score"]

        evaluator_total_scores[evaluator["id"]] = {
            "evaluator": evaluator,
            "total_score": total,
            "rank": None,  # 나중에 계산
        }

    # 순위 계산
    sorted_scores = sorted(
        evaluator_total_scores.items(),
        key=lambda x: x[1]["total_score"],
        reverse=True
    )
    for rank, (evaluator_id, result) in enumerate(sorted_scores, 1):
        result["rank"] = rank

    # 5️⃣ 최종 종합점수 (배점 가중)
    final_score = 0
    category_scores = {}
    for item_id, result in evaluation_results.items():
        item_avg = result["average_score"]
        item_weight = result["item"]["score"]
        final_score += item_avg * (item_weight / 100)

        category = result["item"]["category"]
        if category not in category_scores:
            category_scores[category] = []
        category_scores[category].append(item_avg)

    category_averages = {
        cat: sum(scores) / len(scores)
        for cat, scores in category_scores.items()
    }

    # 6️⃣ 평가위원 의견 요약
    evaluation_summary = {
        "strengths": await _summarize_strengths(evaluation_results),
        "weaknesses": await _summarize_weaknesses(evaluation_results),
        "concerns": await _extract_common_concerns(evaluation_results),
        "high_consensus_items": _find_high_consensus_items(evaluation_results),
        "low_consensus_items": _find_low_consensus_items(evaluation_results),
    }

    return {
        "mock_evaluation": {
            "evaluation_items": eval_items,
            "evaluators": evaluators,
            "item_evaluation_results": evaluation_results,
            "evaluator_total_scores": evaluator_total_scores,
            "category_scores": category_averages,
            "final_score": final_score,
            "evaluation_summary": evaluation_summary,
            "detailed_breakdown": {
                "by_item": evaluation_results,
                "by_evaluator": evaluator_total_scores,
                "by_category": category_averages,
            }
        },
        "current_phase": "mock_evaluation_complete",
    }
```

---

## 👥 평가위원 6명 상세 정의

### 구성 원칙

```
산업계 (2명): 현업 경험 기반 평가
├─ 산1: 발주기관/유사기업 경험자
│  └─ 관점: 사업성, 실현가능성, ROI
│
├─ 산2: 경쟁사 대표/전문가
│  └─ 관점: 경쟁우위, 차별성, 시장성

학계 (2명): 학문적 근거 기반 평가
├─ 학1: 대학교수 (정부 R&D 검증자 역)
│  └─ 관점: 기술혁신성, 이론적 근거, 새로움
│
├─ 학2: 연구소 책임자 (구현 검증자 역)
│  └─ 관점: 실현가능성, 기술완성도, 리스크

연구계/공공 (2명): 사회적 가치 기반 평가
├─ 연1: 정부 부처 담당자 (정책 부합도)
│  └─ 관점: 법규준수, 정책부합, 공공성
│
└─ 연2: 협회/학회 전문가 (산업표준)
   └─ 관점: 표준준수, 산업 요구도, 확산성
```

### 평가위원별 프로필 예시

```python
evaluators = [
    {
        "id": "evaluator_1",
        "name": "이산업",
        "title": "OOO 회사 개발이사",
        "type": "산업계",
        "subtype": "발주유사",
        "experience_years": 15,
        "background": "유사 프로젝트 5건 경험, PM 역할",
        "perspective": [
            "사업 실현가능성",
            "비용 효율성",
            "시간 내 납기 가능성"
        ],
        "evaluation_bias": {
            "tendency": "보수적",  # 보수적/중도/낙관적
            "scoring_range": (0, 90),  # 거의 만점 안 줌
            "weight": 1.0
        },
        "scoring_criteria": {
            "기술혁신성": {
                "weight": 0.8,  # 다른 항목보다 덜 중시
                "threshold": 60  # 60점 이상이면 충분
            },
            "요구사항충족도": {
                "weight": 1.2,  # 더 중시
                "threshold": 80  # 80점 이상 기준
            },
            ...
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
        "perspective": [
            "차별화 정도",
            "경쟁우위 분석",
            "시장 영향도"
        ],
        "evaluation_bias": {
            "tendency": "중도",
            "scoring_range": (30, 95),  # 보통 40~90점 범위
            "weight": 1.0
        }
    },
    {
        "id": "evaluator_3",
        "name": "최교수",
        "title": "000대학교 공학과 교수",
        "type": "학계",
        "subtype": "혁신성",
        "experience_years": 25,
        "background": "기술 혁신 논문 200편 이상, 정부 R&D 평가위원",
        "perspective": [
            "기술 혁신성",
            "이론적 근거",
            "새로운 접근방식"
        ],
        "evaluation_bias": {
            "tendency": "낙관적",  # 새로운 시도 선호
            "scoring_range": (40, 98),  # 높은 점수 경향
            "weight": 1.1  # 영향도 높음
        }
    },
    {
        "id": "evaluator_4",
        "name": "정소장",
        "title": "000 연구소 소장",
        "type": "학계",
        "subtype": "실현가능성",
        "experience_years": 18,
        "background": "프로토타입 개발 경험 다수, 현장 기술 전문",
        "perspective": [
            "실현가능성",
            "기술 완성도",
            "리스크 관리"
        ],
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
        "perspective": [
            "정부 정책 부합도",
            "법규 준수",
            "공공성 및 파급효과"
        ],
        "evaluation_bias": {
            "tendency": "보수적",
            "scoring_range": (0, 88),
            "weight": 0.9
        }
    },
    {
        "id": "evaluator_6",
        "name": "강협회",
        "title": "한국000협회 부회장",
        "type": "연구계/공공",
        "subtype": "표준",
        "experience_years": 22,
        "background": "산업표준 위원, 협회 기술위원장",
        "perspective": [
            "산업표준 준수",
            "산업계 요구도",
            "기술 확산 가능성"
        ],
        "evaluation_bias": {
            "tendency": "중도",
            "scoring_range": (35, 90),
            "weight": 1.0
        }
    }
]
```

---

## 📊 평가항목별 점수 산출 로직

### _score_evaluation_item 함수

```python
async def _score_evaluation_item(
    item: dict,
    evaluator: dict,
    proposal_sections: list,
    strategy: dict
) -> dict:
    """
    특정 평가항목에 대해 평가위원이 점수를 산출

    item: {"item_id": "T1", "category": "기술", "title": "기술혁신성", "score": 20, "criteria": [...]}
    evaluator: 평가위원 프로필
    """

    item_id = item.get("item_id")
    item_title = item.get("title")
    item_criteria = item.get("criteria", [])
    max_score = item.get("score")  # 배점 (예: 20점)

    # 1️⃣ 제안서에서 해당 평가항목 관련 콘텐츠 추출
    relevant_content = await _extract_relevant_content(
        proposal_sections,
        item_title,
        item_criteria
    )
    # 예: 기술혁신성 항목 → 기술 섹션에서 신규 기술 관련 내용 추출

    # 2️⃣ 평가위원의 평가 기준 적용
    evaluation_criteria = evaluator["scoring_criteria"].get(item_title, {})
    weight = evaluation_criteria.get("weight", 1.0)
    threshold = evaluation_criteria.get("threshold", 50)

    # 3️⃣ 항목별 세부 평가 (AI 시뮬레이션)
    sub_scores = {}
    for criteria in item_criteria:
        # 예: 기술혁신성 → "신규기술 적용도", "차별화", "완성도" 각각 평가
        sub_score = await _score_sub_criteria(
            criteria,
            relevant_content,
            evaluator,
            max_score
        )
        sub_scores[criteria] = sub_score

    # 4️⃣ 평가위원 성향에 따른 점수 조정
    base_score = sum(sub_scores.values()) / len(sub_scores)

    # 평가위원 성향 (보수/중도/낙관)에 따른 조정
    if evaluator["evaluation_bias"]["tendency"] == "보수적":
        # 보수적: 평균 -10점
        adjusted_score = base_score * 0.85
    elif evaluator["evaluation_bias"]["tendency"] == "낙관적":
        # 낙관적: 평균 +8점
        adjusted_score = base_score * 1.08
    else:
        # 중도: 그대로
        adjusted_score = base_score

    # 평가위원별 점수 범위 제한
    scoring_range = evaluator["evaluation_bias"]["scoring_range"]
    adjusted_score = max(
        scoring_range[0],
        min(scoring_range[1], adjusted_score)
    )

    # 5️⃣ 배점 범위로 정규화 (0~max_score)
    final_score = (adjusted_score / 100) * max_score

    # 6️⃣ 평가위원 의견 생성
    comments = await _generate_evaluator_comment(
        item_title,
        sub_scores,
        final_score,
        evaluator,
        relevant_content
    )

    return {
        "evaluator_id": evaluator["id"],
        "evaluator_name": evaluator["name"],
        "item_id": item_id,
        "item_title": item_title,
        "score": final_score,
        "max_score": max_score,
        "percentage": (final_score / max_score) * 100,
        "sub_scores": sub_scores,  # 세부 항목별 점수
        "comment": comments["overall"],
        "strengths": comments["strengths"],
        "weaknesses": comments["weaknesses"],
        "concerns": comments["concerns"],
    }
```

### 세부 기준별 점수 산출 예시

```python
async def _score_sub_criteria(
    criteria_name: str,
    content: str,
    evaluator: dict,
    max_score: int
) -> float:
    """
    예: "신규 기술 적용도" 항목을 100점 만점으로 평가
    """

    # AI가 평가위원 관점에서 평가
    prompt = f"""
    당신은 {evaluator['title']}이고, {evaluator['perspective']}를 중시하는 평가위원입니다.

    다음 기준에 대해 0~100점을 부여하세요:
    기준: {criteria_name}

    제안 내용:
    {content}

    평가위원 관점:
    - 성향: {evaluator['evaluation_bias']['tendency']}
    - 강조점: {evaluator['perspective']}

    다음 형식으로 답변하세요:
    {{
      "score": XX,
      "reasoning": "..."
    }}
    """

    response = await claude.generate(prompt)
    return response["score"]
```

---

## 📈 평가 결과 분석

### 평가위원별 점수 분포

```python
def _calculate_distribution(scores: list) -> dict:
    """평가위원 6명의 점수 분포 분석"""

    import statistics

    return {
        "mean": statistics.mean(scores),           # 평균
        "median": statistics.median(scores),       # 중앙값
        "stdev": statistics.stdev(scores),         # 표준편차
        "range": (min(scores), max(scores)),       # 범위
        "variance": statistics.variance(scores),   # 분산
        "scores": scores,                          # 개별 점수
    }

    # 예:
    # {
    #   "mean": 72.5,
    #   "stdev": 8.3,
    #   "range": (62, 85),
    #   "scores": [68, 75, 78, 62, 80, 85]
    # }
```

### 평가위원 의견 일치도 (Consensus)

```python
def _assess_consensus(item_scores: dict) -> dict:
    """
    평가위원들의 의견 일치도 평가

    표준편차가 작으면 → 의견 일치 (합의)
    표준편차가 크면 → 의견 불일치 (논쟁 여지)
    """

    scores = [s["score"] for s in item_scores.values()]
    distribution = _calculate_distribution(scores)

    stdev = distribution["stdev"]

    if stdev < 3:
        consensus_level = "높음 (매우 합의)"  # 거의 모두 같은 점수
    elif stdev < 6:
        consensus_level = "중간"
    else:
        consensus_level = "낮음 (의견 분분)"

    return {
        "consensus_level": consensus_level,
        "stdev": stdev,
        "interpretation": f"평가위원들의 의견이 {'일치' if stdev < 6 else '분분'}합니다",
        "disagreement_details": {
            "high_scorers": [name for name, score in item_scores.items() if score > distribution["mean"] + stdev],
            "low_scorers": [name for name, score in item_scores.items() if score < distribution["mean"] - stdev],
        }
    }
```

---

## 🔍 평가 결과 해석 예시

### 최종 보고서 구조

```python
mock_evaluation_report = {
    "평가위원 구성": {
        "총 6명": [
            "산업계 2명 (사업성 중심)",
            "학계 2명 (혁신성/실현가능성)",
            "연구계 2명 (정책/표준)",
        ]
    },

    "평가항목별 결과": {
        "기술혁신성 (20점)": {
            "평가위원별 점수": [
                {"이산업": 16, "박경쟁": 15, "최교수": 19, "정소장": 17, "홍정책": 14, "강협회": 16}
            ],
            "평균": 16.2,
            "표준편차": 1.8,
            "합의도": "높음",
            "의견": [
                "✅ 강점: 신규 AI 기술 적용, 차별화된 접근",
                "⚠️ 약점: 리스크 관리 계획 미흡",
                "💡 우려: 기술 완성도 (프로토타입 단계)",
            ]
        },
        "요구사항 충족도 (20점)": {
            "평가위원별 점수": [18, 19, 17, 20, 18, 19],
            "평균": 18.5,
            "표준편차": 1.0,
            "합의도": "매우 높음",
            "의견": [
                "✅ 강점: RFP 요구사항 명확히 반영",
                "✅ 강점: 모든 필수 기능 포함",
            ]
        },
        ...
    },

    "평가위원별 총점": {
        "1순위 (최교수)": 92,  # 낙관적, 혁신성 강조
        "2순위 (정소장)": 89,  # 균형잡힌 평가
        "3순위 (강협회)": 87,
        "4순위 (박경쟁)": 86,
        "5순위 (홍정책)": 84,  # 보수적, 리스크 강조
        "6순위 (이산업)": 82,  # 가장 보수적
        "평균": 86.7,
        "표준편차": 3.9,
    },

    "최종 종합점수": 86.7,

    "자가진단 vs 모의평가": {
        "자가진단": 85,
        "모의평가": 86.7,
        "차이": +1.7,
        "해석": "자체 평가가 합리적 (큰 차이 없음)",
    },

    "의견 불일치 항목": {
        "기술혁신성": {
            "표준편차": 1.8,
            "불일치 사유": "낙관적 평가위원(최교수)이 높게, 보수적 평가위원(이산업)이 낮게",
            "권장": "리스크 관리 계획 보강 권고",
        }
    },

    "주요 강점": [
        "요구사항 충족도 우수 (18.5/20)",
        "신규 기술 적용 우수 (16.2/20)",
        "가격 경쟁력 양호",
    ],

    "주요 약점": [
        "기술 완성도 미흡 (프로토타입)",
        "리스크 관리 계획 상세도 부족",
        "사후관리 계획 구체성 부족",
    ],

    "개선 우선순위": [
        "1순위: 기술 리스크 관리 계획 상세화",
        "2순위: 사후관리 계획 강화",
        "3순위: 프로토타입 완성도 향상",
    ]
}
```

---

## 💡 구현 핵심

### 1️⃣ RFP 평가항목 기반
- RFPAnalysis.eval_items에서 실제 평가항목 추출
- 실제 배점 적용 (기술 40, 가격 30, 관리 20 등)
- 실제 평가기준 반영

### 2️⃣ 6명 평가위원 시뮬레이션
- 산/학/연 2명씩 다양성
- 각 평가위원의 고유한 관점/편향성
- 성향별 점수 범위 (보수: 0~85, 낙관: 50~98 등)

### 3️⃣ 다각도 평가
- 평가항목별 → 평가위원별 → 범주별 → 최종점수
- 점수 분포 및 표준편차 (의견 일치도)
- 강점/약점/우려사항 구분

### 4️⃣ 신뢰성
- 실제 평가에 가장 근접
- 점수 편포 현실적
- 의견 불일치 분석 가능

---

## 📝 STEP 10A 최종 함수 구조

```python
async def run_mock_evaluation(state: ProposalState) -> dict:
    """
    1. RFP 평가항목 추출
    2. 평가위원 6명 구성 (산/학/연 2명씩)
    3. 평가항목별로 각 평가위원이 점수 산출
    4. 평가위원별 의견 기록 (강점/약점/우려)
    5. 결과 종합 (항목별/평가위원별/범주별)
    6. 자가진단 vs 모의평가 비교
    7. 개선 우선순위 제시
    """

    rfp = state.get("rfp_analysis")
    eval_items = rfp.get("eval_items")  # RFP 평가항목
    evaluators = await _create_evaluators(rfp, state.get("strategy"))  # 6명 구성

    # 평가항목별 → 평가위원별 점수 산출
    evaluation_matrix = await _build_evaluation_matrix(eval_items, evaluators, state)

    # 결과 분석
    final_results = await _analyze_evaluation_results(evaluation_matrix, evaluators)

    return {
        "mock_evaluation": {
            "eval_items": eval_items,
            "evaluators": evaluators,
            "evaluation_matrix": evaluation_matrix,  # 항목 × 평가위원 매트릭스
            "summary": final_results,  # 종합 분석
        },
        "current_phase": "mock_evaluation_complete",
    }
```

---

## ✅ 이제 완성된 모의평가 설계

- ✅ RFP 평가항목 기반
- ✅ 6명 평가위원 시뮬레이션 (산/학/연)
- ✅ 다각도 평가 분석
- ✅ 점수 분포 및 의견 일치도
- ✅ 실제 평가에 가장 근접

**다음 단계**: STEP 11A review_mock_evaluation 노드에서 Human이 이 결과를 검토하고 수정보완 결정
