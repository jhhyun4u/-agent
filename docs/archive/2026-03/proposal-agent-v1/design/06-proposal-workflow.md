# 제안서 작성 워크플로

> **소속**: proposal-agent-v1 설계 문서 v3.5
> **관련 파일**: [03-graph-definition.md](03-graph-definition.md), [04-review-nodes.md](04-review-nodes.md), [12-prompts.md](12-prompts.md)
> **원본 섹션**: §8, §9, §10 (+ §32-5 유형별 프롬프트, §32-6 스토리라인 파이프라인 merged)

---

## 8. 자가진단 자동 개선 루프 — D-10 해결

```python
# app/graph/nodes/self_review.py

MAX_AUTO_IMPROVE = 2  # 자동 개선 최대 횟수

async def self_review_with_auto_improve(state: ProposalState) -> dict:
    """
    AI 자가진단 + 자동 개선 루프.
    80점 미만 → 자동으로 부족 섹션 재작성 (최대 2회) → 재진단.
    """
    sections = state.get("proposal_sections", [])
    compliance = state.get("compliance_matrix", [])
    strategy = state.get("strategy")
    auto_improve_count = state.get("parallel_results", {}).get("_auto_improve_count", 0)

    # Compliance Matrix 완성 (D-4: STEP 4에서 완성)
    updated_compliance = await check_compliance(sections, compliance)

    # ★ v3.0: 4축 평가 (기존 3축 + 근거 신뢰성)
    score = await evaluate_proposal(sections, updated_compliance, strategy)
    trustworthiness = await evaluate_trustworthiness(sections, strategy)  # §16-3-3
    score["trustworthiness"] = trustworthiness
    # 총점 재계산 (4축 가중 합산: 각 25점, 합계 100점)
    score["total"] = (
        score.get("compliance_score", 0) +
        score.get("strategy_score", 0) +
        score.get("quality_score", 0) +
        trustworthiness["trustworthiness_score"]
    )

    result = {
        "compliance_matrix": updated_compliance,
        "parallel_results": {
            "_self_review_score": score,
            "_auto_improve_count": auto_improve_count,
        },
    }

    # ★ v3.3: 원인별 재시도 횟수 추적 (무한 루프 방지 — §22-4-3)
    retry_research_count = state.get("parallel_results", {}).get("_retry_research_count", 0)
    retry_strategy_count = state.get("parallel_results", {}).get("_retry_strategy_count", 0)

    if score["total"] >= 80:
        result["current_step"] = "self_review_pass"
    elif auto_improve_count < MAX_AUTO_IMPROVE:
        # ★ v3.3: 축별 약점 분석으로 원인별 라우팅 결정
        trustworthiness_score = trustworthiness.get("trustworthiness_score", 25)
        strategy_score = score.get("strategy_score", 25)

        if trustworthiness_score < 12 and retry_research_count < 1:
            # 근거 부족 → 리서치 보강 (최대 1회)
            result["parallel_results"]["_retry_research_count"] = retry_research_count + 1
            result["parallel_results"]["_auto_improve_count"] = auto_improve_count + 1
            result["current_step"] = "self_review_retry_research"
        elif strategy_score < 15 and retry_strategy_count < 1:
            # 전략 약함 → 전략 재수립 (최대 1회)
            result["parallel_results"]["_retry_strategy_count"] = retry_strategy_count + 1
            result["parallel_results"]["_auto_improve_count"] = auto_improve_count + 1
            result["current_step"] = "self_review_retry_strategy"
        else:
            # 그 외 → 섹션 재작성
            weak_sections = [s for s in score["section_scores"] if s["score"] < 70]
            result["rework_targets"] = [s["section_id"] for s in weak_sections]
            result["parallel_results"]["_auto_improve_count"] = auto_improve_count + 1
            result["current_step"] = "self_review_retry_sections"
    else:
        result["current_step"] = "self_review_force_review"

    return result


def route_after_self_review(state: ProposalState) -> str:
    """
    ★ v3.3: 원인별 피드백 라우팅 (ProposalForge quality_gate_router 반영).
    기존 3방향(pass/auto_retry/force_review) → 5방향 확장.
    self_review_with_auto_improve에서 설정한 current_step 값에 따라 분기.
    """
    step = state.get("current_step", "")
    if "pass" in step:
        return "pass"
    elif "force_review" in step:
        return "force_review"
    elif "retry_research" in step:
        return "retry_research"
    elif "retry_strategy" in step:
        return "retry_strategy"
    return "retry_sections"
```

---

## 9. 케이스 B (서식 있음) 처리 — D-3 해결

> **v3.5 변경**: 단일 `proposal_section` 프롬프트가 10개 유형별 전문 프롬프트로 대체됨. 상세 → [12-prompts.md](12-prompts.md) §32-5 참조.

```python
# app/graph/nodes/proposal_nodes.py

async def proposal_section(state: ProposalState) -> dict:
    """
    섹션 생성 노드. 케이스 A/B에 따라 접근 방식이 다름.
    """
    section_id = state.get("_current_section_id", "")
    case_type = state.get("_case_type", "A")
    strategy = state.get("strategy")
    positioning = state.get("positioning")
    rfp = state.get("rfp_analysis")

    if case_type == "B":
        # ★ 케이스 B: 서식 구조 보존, 내용만 채우기
        template_structure = rfp.get("format_template", {}).get("structure", {})
        section_template = template_structure.get(section_id, {})

        content = await claude_generate(
            PROPOSAL_CASE_B_PROMPT.format(
                section_id=section_id,
                template_structure=section_template,  # 원본 서식 구조
                strategy=strategy,
                positioning=positioning,
                positioning_guide=POSITIONING_STRATEGY_MATRIX[positioning],
                rfp_analysis=rfp,
            ),
        )
        return {
            "proposal_sections": [ProposalSection(
                section_id=section_id,
                title=section_template.get("title", section_id),
                content=content,
                version=1,
                case_type="B",
                template_structure=section_template,
            )],
        }
    else:
        # 케이스 A: 자유 양식
        content = await claude_generate(
            PROPOSAL_CASE_A_PROMPT.format(
                section_id=section_id,
                strategy=strategy,
                positioning=positioning,
                positioning_guide=POSITIONING_STRATEGY_MATRIX[positioning],
                rfp_analysis=rfp,
            ),
        )
        return {
            "proposal_sections": [ProposalSection(
                section_id=section_id,
                title=section_id,
                content=content,
                version=1,
                case_type="A",
            )],
        }
```

### 9-1. DOCX 빌더 케이스 분기

```python
# app/services/docx_builder.py

async def build_docx(sections: list[ProposalSection], rfp: RFPAnalysis) -> bytes:
    if rfp.case_type == "B":
        # 케이스 B: RFP 서식 템플릿을 기반으로 DOCX 생성
        # 원본 서식의 제목·번호·구조를 그대로 재현하고 content만 삽입
        return _build_from_template(sections, rfp.format_template["structure"])
    else:
        # 케이스 A: 자유 양식 DOCX 생성
        return _build_freeform(sections)
```

---

## 10. Compliance Matrix 생애주기 — D-4 해결

```python
# app/services/compliance_tracker.py

class ComplianceTracker:
    """Compliance Matrix 전 단계 생애주기 관리."""

    @staticmethod
    async def create_initial(rfp_analysis: RFPAnalysis) -> list[ComplianceItem]:
        """STEP 1: RFP 필수 요건에서 초안 생성."""
        items = []
        for i, req in enumerate(rfp_analysis.mandatory_reqs):
            items.append(ComplianceItem(
                req_id=f"REQ-{i+1:03d}",
                content=req,
                source_step="rfp",
                status="미확인",
            ))
        # 평가항목에서 추가 요건 추출
        for item in rfp_analysis.eval_items:
            items.append(ComplianceItem(
                req_id=f"EVAL-{item['항목명'][:10]}",
                content=f"평가항목: {item['항목명']} ({item['배점']}점)",
                source_step="rfp",
                status="미확인",
            ))
        return items

    @staticmethod
    async def update_from_strategy(
        matrix: list[ComplianceItem], strategy: Strategy
    ) -> list[ComplianceItem]:
        """STEP 2: 전략 관점 항목 추가 (Win Theme 반영 체크 등)."""
        matrix.append(ComplianceItem(
            req_id="STR-WIN",
            content=f"Win Theme 반영 확인: {strategy.win_theme}",
            source_step="strategy",
            status="미확인",
        ))
        matrix.append(ComplianceItem(
            req_id="STR-AFE",
            content=f"Action Forcing Event 반영: {strategy.action_forcing_event}",
            source_step="strategy",
            status="미확인",
        ))
        for i, msg in enumerate(strategy.key_messages):
            matrix.append(ComplianceItem(
                req_id=f"STR-MSG-{i+1}",
                content=f"핵심 메시지 {i+1} 반영: {msg}",
                source_step="strategy",
                status="미확인",
            ))
        return matrix

    @staticmethod
    async def check_compliance(
        sections: list[ProposalSection], matrix: list[ComplianceItem]
    ) -> list[ComplianceItem]:
        """STEP 4 자가진단: 각 항목의 충족 여부를 AI로 체크."""
        all_content = "\n".join(s.content for s in sections)
        for item in matrix:
            # Claude에게 각 항목의 충족 여부 판정 요청
            result = await claude_generate(
                COMPLIANCE_CHECK_PROMPT.format(
                    requirement=item.content,
                    proposal_content=all_content,
                ),
            )
            item.status = result["status"]  # 충족|미충족|해당없음
            item.proposal_section = result.get("matching_section", "")
        return matrix
```

---

## 10-1. 스토리라인 파이프라인 (§32-6 merged)

> plan_story → plan_merge → proposal_write_next로 이어지는 스토리라인 흐름을 명시한다.

#### 10-1-1. plan_story 프롬프트 강화

기존 §8의 PLAN_STORY_PROMPT를 3단계로 확장:

```
입력: {current_sections} (dynamic_sections에서 생성)

1단계: 목차 확정
  - RFP eval_items 기반 초안 검토
  - 항목 추가/삭제/순서 조정 결정

2단계: 섹션별 스토리라인
  - 각 섹션에 대해:
    eval_item, key_message, narrative_arc, supporting_points,
    evidence, win_theme_connection, transition_to_next, tone

3단계: 톤앤매너
  - overall_narrative, opening_hook, closing_impact
```

**출력 JSON**:
```json
{
  "storylines": {
    "overall_narrative": "전체 제안서를 관통하는 서사",
    "opening_hook": "도입부 후킹 전략",
    "closing_impact": "마무리 인상 전략",
    "sections": [
      {
        "eval_item": "평가 항목명",
        "key_message": "핵심 주장 (Assertion Title)",
        "narrative_arc": "문제 제기 → 긴장감 → 해결책 구조",
        "supporting_points": ["근거1", "근거2"],
        "evidence": ["실적1", "수치1"],
        "win_theme_connection": "Win Theme과 연결 방식",
        "transition_to_next": "다음 섹션 연결고리",
        "tone": "톤 가이드"
      }
    ]
  }
}
```

#### 10-1-2. plan_merge에서 목차 동기화 (_sync_dynamic_sections)

`plan_merge` 노드 실행 시 `_sync_dynamic_sections(state, storylines)` 호출:

1. `storylines.sections[].eval_item` 순서로 `dynamic_sections` 재정렬
2. 기존 `dynamic_sections`에 있으나 storylines에 없는 섹션은 후미에 보존
3. 신규 섹션에 대해 `classify_section_type()` 호출하여 `_section_type_map` 갱신
4. 결과: `{ "dynamic_sections": [...], "parallel_results": {"_section_type_map": {...}} }` 반환

```python
def _sync_dynamic_sections(state: ProposalState, storylines: dict) -> dict:
    story_sections = storylines.get("sections", [])
    if not story_sections:
        return {}
    new_order = []
    for s in story_sections:
        section_id = s.get("eval_item") or s.get("section_id", "")
        if section_id and section_id not in new_order:
            new_order.append(section_id)
    existing = state.get("dynamic_sections", [])
    for sid in existing:
        if sid not in new_order:
            new_order.append(sid)
    section_type_map = state.get("parallel_results", {}).get("_section_type_map", {})
    for sid in new_order:
        if sid not in section_type_map:
            section_type_map[sid] = classify_section_type(sid)
    return {
        "dynamic_sections": new_order,
        "parallel_results": {"_section_type_map": section_type_map},
    }
```

#### 10-1-3. proposal_write_next에서 스토리라인 주입

`_build_context()` 내부에서 현재 섹션에 해당하는 스토리라인을 추출하여 `storyline_context` 문자열 생성:

```python
# plan.storylines에서 현재 섹션 매칭
storylines = state.get("plan", {}).get("storylines", {})
sections_data = storylines.get("sections", [])
matched = next((s for s in sections_data if s.get("eval_item") == section_id), None)

if matched:
    storyline_context = f"""## 스토리라인 가이드
전체 서사: {storylines.get('overall_narrative', '')}
도입 전략: {storylines.get('opening_hook', '')}

### 이 섹션의 스토리라인
- 핵심 메시지: {matched.get('key_message', '')}
- 서사 구조: {matched.get('narrative_arc', '')}
- 근거 포인트: {', '.join(matched.get('supporting_points', []))}
- 증빙: {', '.join(matched.get('evidence', []))}
- Win Theme 연결: {matched.get('win_theme_connection', '')}
- 다음 섹션 전환: {matched.get('transition_to_next', '')}
- 톤: {matched.get('tone', '')}"""
```

---

## 10-2. 유형별 전문 프롬프트 체계 (§32-5 merged)

> §9의 단일 `proposal_section` 프롬프트를 아래 10개 유형 + 케이스 B 프롬프트로 대체한다.
> 구현: `app/prompts/section_prompts.py`

#### 10-2-1. 10개 섹션 유형 분류

| 유형 | 설명 | 대표 키워드 |
|---|---|---|
| UNDERSTAND | 과업 이해 | 과업, 현황, 배경, 목적 |
| STRATEGY | 전략·추진방향 | 전략, 추진방향, 비전, 접근 |
| METHODOLOGY | 방법론·절차 | 방법론, 절차, 프로세스, 단계 |
| TECHNICAL | 기술·시스템 | 기술, 시스템, 아키텍처, 인프라 |
| MANAGEMENT | 관리·품질 | 관리, 품질, 위험, 이슈 |
| PERSONNEL | 인력·조직 | 인력, 조직, 자격, 투입 |
| TRACK_RECORD | 수행실적 | 실적, 사례, 유사과업, 경험 |
| SECURITY | 보안·정보보호 | 보안, 정보보호, 개인정보, 암호화 |
| MAINTENANCE | 유지보수·운영 | 유지보수, 운영, 하자보수, SLA |
| ADDED_VALUE | 가산점·부가제안 | 가산, 부가, 추가, 기여 |

`classify_section_type(section_id: str) -> str` — 섹션 ID/이름의 키워드를 매칭하여 유형 결정.
매칭 실패 시 기본값: `TECHNICAL`.

#### 10-2-2. EVALUATOR_PERSPECTIVE_BLOCK (공통)

모든 유형별 프롬프트 상단에 삽입되는 공통 블록:

```
## 평가위원 채점 관점
이 섹션은 평가위원에 의해 채점됩니다. 다음 기준을 최우선으로 고려하세요:
1. **세부 평가항목 1:1 대응**: 모든 세부 평가항목에 대해 명시적으로 답변
2. **구체적 근거 제시**: 주장마다 수치, 사례, 방법론으로 뒷받침
3. **차별화 포인트**: 경쟁사 대비 우위를 명확히 드러내는 서술
4. **논리적 흐름**: 문제 인식 → 접근 방법 → 기대 효과의 일관된 논리 구조
5. **배점 비례 분량**: 고배점 항목에 더 많은 지면과 깊이 할당
```

#### 10-2-3. 유형별 프롬프트 구조

각 유형 프롬프트는 동일한 구조를 따른다:

```
{EVALUATOR_PERSPECTIVE_BLOCK}

## [{유형}] {유형 설명} 섹션 작성 지침
### 이 유형의 핵심 목표
### 필수 포함 요소
### 자가진단 체크리스트
### 출력 형식 (JSON)

## 작성 지침
{storyline_context}
{positioning_guide}
{prev_sections_context}
{feedback_context}
```

**입력 변수** (proposal_write_next에서 주입):

| 변수 | 출처 | 설명 |
|---|---|---|
| `section_name` | dynamic_sections[current_section_index] | 섹션 ID/이름 |
| `eval_item_detail` | eval_items 매칭 | 배점, 세부항목 |
| `storyline_context` | plan.storylines → _build_context() | 스토리라인 컨텍스트 (32-6 참조) |
| `positioning_guide` | strategy | 포지셔닝 전략 |
| `prev_sections_context` | parallel_results (이전 섹션들) | 이전 섹션 요약 |
| `feedback_context` | rework_targets | 재작업 시 피드백 |
| `rfp_context` | rfp_analysis | RFP 분석 결과 |
| `kb_context` | KB 검색 결과 | 관련 역량·실적·콘텐츠 |
| `research_context` | research_brief | 리서치 결과 |

#### 10-2-4. 배점 기반 분량 조절

```python
def get_recommended_pages(score_weight: float, total_pages: int = 100) -> int:
    """배점 비율에 따른 권장 페이지 수 산출."""
    base = max(2, int(total_pages * score_weight / 100))
    return min(base, 15)  # 최대 15페이지
```

#### 10-2-5. 케이스 B 프롬프트

서식이 사전 정의된 케이스 B에서는 별도 `CASE_B_PROMPT`를 사용:
- 서식 구조(제목, 하위 항목, 표, 다이어그램 위치) 보존 최우선
- 유형별 간략 가이드(`SECTION_TYPE_BRIEF_GUIDES`)를 참조하여 각 유형의 핵심 포인트 반영
- 서식 슬롯에 내용을 채우는 방식
