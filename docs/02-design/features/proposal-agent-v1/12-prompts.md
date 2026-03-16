# 프롬프트 설계

> **소속**: proposal-agent-v1 설계 문서 v3.5
> **관련 파일**: [06-proposal-workflow.md](06-proposal-workflow.md), [04-review-nodes.md](04-review-nodes.md)
> **원본 섹션**: §16, §29 (+ §32-5-2/5-3/8 merged)

---

## 16. 프롬프트 설계 원칙

### 16-1. 공통 컨텍스트 주입

> **★ v3.0 토큰 최적화 원칙** (§21 참조):
> - `COMMON_CONTEXT`는 **Prompt Caching 대상** — `cache_control: {"type": "ephemeral"}` 적용
> - 피드백 이력은 **최근 3회(feedback_window_size)만** 포함
> - KB 참조는 **Top-5, 각 500자 이내**로 요약 후 주입
> - STEP별 컨텍스트 예산 준수 (§21 token_manager.py STEP_BUDGETS 참조)

```python
COMMON_CONTEXT = """
## 현재 제안 컨텍스트
- 사업명: {project_name}
- 발주기관: {client}
- 🏷️ 포지셔닝: {positioning} ({positioning_label})
- 모드: {mode}

## 포지셔닝 전략 가이드
{positioning_guide}

## 핵심 전략
- Ghost Theme: {ghost_theme}
- Win Theme: {win_theme}
- Action Forcing Event: {action_forcing_event}
- 핵심 메시지: {key_messages}

## 이전 단계 피드백 (최근 {feedback_window_size}회)
{feedback_history}

## ★ v3.0: KB 참조 컨텍스트 (Top-5, 각 500자 이내)
{kb_context}

## ★ v3.0: 발주기관 인텔리전스
{client_intel_summary}

## 부분 재작업 지시 (있는 경우)
{rework_instruction}
"""
```

> **Prompt Caching 적용 방법**: `COMMON_CONTEXT` 블록을 `messages[0].content[0]`에 배치하고 `cache_control` 마킹.
> 동일 프로젝트 내 STEP 간 전환 시 90% 입력 토큰 비용 절감 (§21 상세).

### 16-2. 단계별 프롬프트 핵심

| 단계 | 핵심 지시 | Shipley 관점 | 포지셔닝 연동 | KB 참조 | 토큰 예산 |
|------|-----------|-------------|-------------|---------------|-----------------|
| 공고 검색 | 최대 5건 추천, 공고별 요약 + 적합도 | 영업 담당자 | 예상 분류 | 발주기관 입찰이력 | 4,000 |
| RFP 획득 | G2B 첨부파일 자동 추출 + 사용자 업로드 | — (자동+수동) | — | — | — |
| RFP 분석 | 배점 역설계, Compliance Matrix 초안, hidden_requirements | Blue Team | 케이스 A/B | 유사 RFP 콘텐츠 | 8,000 |
| **★ 리서치 조사** | **RFP-적응형 사전조사: 사업 범주별 조사 차원 동적 설계 → 차원별 핵심 발견 수집** | **Blue Team** | **—** | **외부 데이터** | **15,000** |
| Go/No-Go | 포지셔닝 정밀 판정 + 수주 가능성 + **발주기관 인텔 5단계** | 의사결정자 | 유형 확정 | 발주기관+경쟁사 DB+**리서치** | **18,000** |
| 제안전략 | Ghost/Win/AFE + **경쟁사 SWOT + 시나리오 + 연구질문** | Blue Team | **매트릭스 전체** | 경쟁사 강약점·교훈 | **25,000** |
| 스토리라인 | 4단계 구조, 포지셔닝별 강조점 | Pink Team | 수성/공격/인접 | 수주 성공 콘텐츠 | 6,000 |
| 제안서 | 발주처 언어, 수치화, 케이스 A/B + **자체검증 체크리스트** | Red Team | 실적/혁신/전이 | 콘텐츠 라이브러리 | 12,000/섹션 |
| 가격산정 | **원가기준 확인 + 노임단가 M/M + 직접경비 + 입찰시뮬레이션** | Red Team | 가격전략 | KB 단가 DB | **15,000** |
| 자가진단 | 4축 평가 + **3인 페르소나 시뮬레이션** + 80점 기준 | Red Team | 포지셔닝 일관성 | Compliance 규칙 | 8,000 |
| **★ 발표전략** | **킬링 메시지, 시간 배분, Q&A 전략 (서류심사 시 건너뛰기)** | **Gold Team** | **발표 시나리오** | **—** | **8,000** |
| PPT | 1슬라이드 1메시지, **3막 구조(Why→How→Us)**, 50자×5줄 | Gold Team | 메시지 시각화 | — | 4,000/슬라이드 |

> **★ v3.0 토큰 예산 원칙**: 각 STEP의 입력 토큰이 예산을 초과하면 `token_manager`가 컨텍스트를 자동 축소 (RFP 요약 전달, KB 참조 Top-3 축소, 피드백 최근 2회 등). 상세 로직은 §21 참조.

### 16-3. ★ v3.0 AI 산출물 신뢰성 규칙 (TRS-01~12 구현)

> 요구사항 §12-0의 신뢰성 정책을 시스템 프롬프트 + 후처리로 구현한다.

#### 16-3-1. 시스템 프롬프트 — 신뢰성 지시 블록

```python
# app/prompts/trustworthiness.py

TRUSTWORTHINESS_RULES = """
## AI 작성 규칙 — 반드시 준수

### 1. 할루시네이션 금지
- KB(역량 DB, 콘텐츠 라이브러리, 발주기관 DB, 경쟁사 DB)에 있는 데이터를 우선 사용하라.
- 자사 수행실적, 인력 정보, 구체적 금액/기간을 KB 없이 생성하지 마라.
  → KB에 없으면 "[KB 데이터 필요: {필요한 정보 설명}]" 플레이스홀더를 삽입하라.
- 확인할 수 없는 사실을 단정적으로 서술하지 마라.

### 2. 출처 태그 필수
- 모든 수치(금액, 비율, 건수, 기간)에 출처 태그를 부착하라:
  - [KB] — KB 데이터 기반
  - [RFP] — RFP 원문 인용 (페이지 번호 포함)
  - [G2B] — 나라장터 공고/낙찰 데이터
  - [추정] — AI 추론 (반드시 추론 근거를 괄호 안에 명시)
  - [일반지식] — KB/RFP/G2B에 없는 일반적 사실
- 인라인 출처 마커 형식: [역량DB-{id}], [콘텐츠-{id}], [RFP p.{n}]

### 3. 과장 표현 금지
- "업계 최초", "혁신적", "획기적", "독보적" 등 검증 불가능한 표현 사용 금지.
  → 대신 구체적 수치와 비교 근거를 제시하라.
  → 예: "혁신적 기술" ❌ → "처리시간 30% 단축 (기존 10초 → 7초) [KB-CAP-045]" ✅

### 4. 발주처 언어 사용
- RFP에서 사용한 용어를 그대로 사용하라.
- RFP에 없는 자체 용어를 도입할 경우 [비RFP 용어] 태그를 부착하라.

### 5. 외부 데이터 인용 기준
- 시장 동향, 기술 트렌드, 통계 인용 시 공신력 있는 출처만 허용:
  ✅ 정부 통계(통계청, 과기정통부), 공공기관 보고서, 학술 논문, 업계 공식 보고서(Gartner, IDC 등)
  ❌ 개인 블로그, 비공식 매체, 위키백과, 출처 불명 데이터
- 출처를 특정할 수 없는 일반 상식은 [일반지식] 태그 부착.

### 6. 불확실성 명시
- 경쟁사 예상 가격, 시장 점유율 등 확신도가 낮은 판단은
  확신도(높음/보통/낮음)와 판단 근거를 함께 제시하라.
"""

# ── 공통 컨텍스트에 신뢰성 규칙 주입 ──
# COMMON_CONTEXT 빌드 시 TRUSTWORTHINESS_RULES를 cache_control 블록에 포함
# (프로젝트 내 모든 STEP에서 동일하게 적용 → Prompt Caching 대상)
```

#### 16-3-2. 출처 태그 후처리 — source_tagger.py

```python
# app/services/source_tagger.py
import re
from dataclasses import dataclass

@dataclass
class SourceTag:
    """AI 산출물 내 출처 태그 파싱 결과."""
    tag_type: str      # "KB" | "RFP" | "G2B" | "추정" | "일반지식" | "플레이스홀더"
    reference_id: str   # 예: "CAP-045", "p.12", ""
    text_span: tuple[int, int]  # 원문 내 위치

# ── 출처 태그 패턴 ──
TAG_PATTERNS = {
    "KB":           r'\[KB(?:-([A-Z]+-\d+))?\]',
    "역량DB":       r'\[역량DB-([A-Z]+-\d+)\]',
    "콘텐츠":       r'\[콘텐츠-([A-Z]+-\d+)\]',
    "RFP":          r'\[RFP\s*p\.(\d+)\]',
    "G2B":          r'\[G2B(?:\s+([^\]]+))?\]',
    "추정":         r'\[추정(?:\s*\(([^)]+)\))?\]',
    "일반지식":     r'\[일반지식\]',
    "플레이스홀더": r'\[KB 데이터 필요:\s*([^\]]+)\]',
    "비RFP용어":    r'\[비RFP 용어\]',
    "과장표현":     r'\[과장 표현 주의\]',
}

def extract_source_tags(text: str) -> list[SourceTag]:
    """AI 산출물에서 모든 출처 태그를 추출."""
    tags = []
    for tag_type, pattern in TAG_PATTERNS.items():
        for match in re.finditer(pattern, text):
            tags.append(SourceTag(
                tag_type=tag_type,
                reference_id=match.group(1) or "" if match.lastindex else "",
                text_span=(match.start(), match.end()),
            ))
    return tags

def calculate_grounding_ratio(text: str) -> dict:
    """
    TRS-05: KB 참조 신뢰도 산출.
    - kb_ratio: KB/RFP/G2B 기반 문장 비율
    - general_ratio: 일반지식 기반 비율
    - untagged_ratio: 출처 태그 없는 비율 (검증 필요)
    """
    sentences = [s.strip() for s in re.split(r'[.。!?]\s*', text) if s.strip()]
    if not sentences:
        return {"kb_ratio": 0, "general_ratio": 0, "untagged_ratio": 1.0, "level": "일반지식 기반"}

    kb_count = sum(1 for s in sentences
                   if re.search(r'\[(KB|역량DB|콘텐츠|RFP|G2B)', s))
    general_count = sum(1 for s in sentences
                        if re.search(r'\[일반지식\]', s))
    total = len(sentences)
    untagged = total - kb_count - general_count

    kb_ratio = kb_count / total
    # TRS-05 3단계 판정
    if kb_ratio >= 0.7:
        level = "KB 기반"
    elif kb_ratio >= 0.3:
        level = "혼합"
    else:
        level = "일반지식 기반"

    return {
        "kb_ratio": round(kb_ratio, 2),
        "general_ratio": round(general_count / total, 2),
        "untagged_ratio": round(untagged / total, 2),
        "level": level,
    }

def find_ungrounded_claims(text: str) -> list[dict]:
    """
    TRS-07: 출처 없는 주장·수치 탐지 → 검증 필요 목록.
    - 수치가 포함된 문장 중 출처 태그가 없는 것
    - 수행실적/인력/금액 키워드가 포함된 문장 중 KB 태그가 없는 것
    """
    issues = []
    sentences = re.split(r'(?<=[.。!?])\s+', text)
    for i, sent in enumerate(sentences):
        has_number = bool(re.search(r'\d+[억만천건명년월일%]', sent))
        has_fact_keyword = bool(re.search(r'수행실적|인력|투입|프로젝트명|사업비|계약', sent))
        has_source_tag = bool(re.search(r'\[(KB|역량DB|콘텐츠|RFP|G2B|추정)', sent))

        if has_number and not has_source_tag:
            issues.append({
                "sentence_index": i,
                "sentence": sent[:100],
                "issue": "수치에 출처 태그 누락",
                "severity": "high",
            })
        elif has_fact_keyword and not has_source_tag:
            issues.append({
                "sentence_index": i,
                "sentence": sent[:100],
                "issue": "사실 주장에 KB 출처 누락",
                "severity": "high",
            })
    return issues
```

#### 16-3-3. 자가진단 4축 확장 — 근거 신뢰성 축 추가

```python
# app/graph/nodes/self_review.py 에 추가

async def evaluate_trustworthiness(sections: list, strategy) -> dict:
    """
    4축: 근거 신뢰성 평가 (25점 만점).
    TRS-07 + TRS-08 + TRS-10 + TRS-11 구현.
    """
    from app.services.source_tagger import (
        calculate_grounding_ratio,
        find_ungrounded_claims,
    )

    all_text = "\n".join(s.content for s in sections)
    grounding = calculate_grounding_ratio(all_text)
    ungrounded = find_ungrounded_claims(all_text)

    # ── 개별 점수 산출 ──
    # (1) 출처 태그 부착률 (10점)
    tag_score = max(0, 10 - len([u for u in ungrounded if u["severity"] == "high"]))

    # (2) KB 참조 비율 (5점)
    kb_score = round(grounding["kb_ratio"] * 5, 1)

    # (3) 과장 표현 감지 (5점)
    exaggeration_patterns = r'업계\s*최초|혁신적|획기적|독보적|세계\s*최고|압도적'
    exaggeration_count = len(re.findall(exaggeration_patterns, all_text))
    exaggeration_score = max(0, 5 - exaggeration_count)

    # (4) 섹션 간 수치 일관성 (5점) — TRS-08
    inconsistencies = _check_number_consistency(sections)
    consistency_score = max(0, 5 - len(inconsistencies))

    total = tag_score + kb_score + exaggeration_score + consistency_score

    return {
        "trustworthiness_score": round(total, 1),
        "max_score": 25,
        "details": {
            "source_tag_score": tag_score,
            "kb_ratio_score": kb_score,
            "exaggeration_score": exaggeration_score,
            "consistency_score": consistency_score,
        },
        "grounding_level": grounding["level"],
        "ungrounded_claims": ungrounded[:10],  # 상위 10건
        "exaggeration_count": exaggeration_count,
        "inconsistencies": inconsistencies,
        "warning": "출처 보강 필요" if total < 15 else None,
    }


def _check_number_consistency(sections: list) -> list[dict]:
    """
    TRS-08: 동일 수치가 여러 섹션에서 다르게 언급되는 경우 탐지.
    예: "투입인력 10명" vs "투입인력 12명" 불일치.
    """
    # 섹션별 수치+맥락 추출 → 동일 키워드 다른 수치 비교
    import re
    number_mentions = {}  # { "투입인력": [("10명", section_id), ("12명", section_id)] }
    pattern = r'(투입인력|사업비|예산|기간|처리시간|인원|건수)\s*[:：]?\s*(\d+[\d,.]*\s*[억만천건명년월일개%]+)'

    for s in sections:
        for match in re.finditer(pattern, s.content):
            key = match.group(1)
            value = match.group(2).strip()
            number_mentions.setdefault(key, []).append((value, s.section_id))

    inconsistencies = []
    for key, mentions in number_mentions.items():
        values = set(v for v, _ in mentions)
        if len(values) > 1:
            inconsistencies.append({
                "keyword": key,
                "values": [{"value": v, "section": sid} for v, sid in mentions],
                "issue": f"'{key}' 수치 불일치: {', '.join(values)}",
            })
    return inconsistencies
```

> **자가진단 점수 체계 변경 (v3.0)**:
> | 축 | 배점 | 항목 |
> |----|------|------|
> | 1. Compliance Matrix | 25점 | RFP 요건 충족, 분량·서식 준수 |
> | 2. 전략 반영도 | 25점 | Win Theme·Hot Button·AFE·스토리라인 |
> | 3. 품질 | 25점 | 수치 구체성·발주처 언어·논리 일관성·차별성 |
> | **4. 근거 신뢰성** | **25점** | 출처 태그 부착률·KB 참조 비율·과장 표현·수치 일관성 |
> | **합계** | **100점** | 통과 기준 80점, 근거 신뢰성 15점 미만 시 개별 경고 |

---

---

## 29. ★ ProposalForge 프롬프트 설계 통합 (v3.2)

> **배경**: ProposalForge 13개 에이전트 상세 프롬프트 설계서를 Pattern A(모놀리식 StateGraph) 구조 내에서 흡수.
> ProposalForge는 Pattern B(오케스트레이터+전문에이전트) 기반이므로 아키텍처는 변경하지 않고, **프롬프트 내용**만 노드 레벨로 통합.
> 7개 리서치 서브에이전트 → 1개 `research_gather` 노드로 통합하되, **획일적 7차원 템플릿이 아닌 RFP-적응형**으로 설계 (사업 범주에 따라 조사 차원 자체를 동적 도출).

### 29-1. 그래프 플로우 변경 요약

**v3.1 → v3.2 엣지 변경**:
```
[변경 전] review_rfp → go_no_go → review_gng → ...
[변경 후] review_rfp → research_gather → go_no_go → review_gng → ...

[변경 전] ... → review_proposal → ppt_fan_out_gate → ...
[변경 후] ... → review_proposal → presentation_strategy → ppt_fan_out_gate → ...
```

- `research_gather`는 별도 Human review 없이 자동 통과 (리서치 결과는 Go/No-Go에서 함께 검토)
- `presentation_strategy`는 `eval_method == 'document_only'`이면 건너뛰기 (서류심사)

### 29-2. 신규 노드: `research_gather`

**위치**: `review_rfp` approved → `research_gather` → `go_no_go`
**역할**: RFP 분석 결과를 기반으로 **해당 사업에 맞는 조사 차원을 동적으로 설계**하고, Go/No-Go 의사결정과 제안전략 수립에 필요한 정보를 수집
**근거**: ProposalForge #5(리서치 디렉터) + #6(7개 서브에이전트) 통합
**토큰 예산**: 15,000 (입력) / 8,000 (출력)
**리뷰**: 없음 (go_no_go에서 함께 검토)

#### 핵심 설계 원칙: RFP-적응형 리서치

> **획일적 템플릿(시장동향·기술동향·규제동향 등)을 일률 적용하지 않는다.**
> RFP의 사업 범주와 내용에 따라 조사 차원 자체가 달라져야 한다.
>
> | RFP 사업 유형 | 필요한 조사 차원 (예시) |
> |---|---|
> | 성과조사분석 용역 | 대상 사업의 기집행 현황, 기존 성과지표 체계, 평가 방법론 비교, 유사 성과분석 사례, 이해관계자 맵 |
> | 정책연구 용역 | 정책 배경·입법 이력, 해외 정책 벤치마크, 선행연구 검토, 정책 수혜자 분석, 정량 데이터 가용성 |
> | SI/SW개발 사업 | 기술 스택 동향, 유사 시스템 구축 사례, 기술 인력 시장, 보안/인증 요건, 데이터 이관 복잡도 |
> | 컨설팅 용역 | 발주기관 조직 현황, 동종 기관 사례, 방법론 프레임워크 비교, 변화관리 이슈, 산업 벤치마크 |
>
> 프롬프트는 **2단계 구조**로 실행된다:
> 1. **조사 설계**: RFP 분석 결과를 보고 "이 사업에 필요한 조사 차원 3~7개"를 AI가 직접 도출
> 2. **조사 수행**: 도출된 차원별로 Go/No-Go + 전략 수립에 쓸 수 있는 핵심 발견을 수집

```python
# app/graph/nodes/research_gather.py

async def research_gather(state: ProposalState) -> dict:
    """
    ★ v3.2: RFP-적응형 사전조사.
    획일적 7차원이 아니라, RFP의 사업 범주·내용에 맞게 조사 차원을
    동적으로 설계한 뒤, 각 차원별 핵심 발견을 수집한다.
    Go/No-Go 의사결정과 제안전략 수립을 위한 정보 제공이 목적.
    """
    rfp = state.get("rfp_analysis")
    rfp_raw = state.get("rfp_raw", "")

    # RFP 원문이 긴 경우 핵심부만 전달 (토큰 예산 관리)
    rfp_excerpt = rfp_raw[:8000] if len(rfp_raw) > 8000 else rfp_raw

    result = await claude_generate(
        RESEARCH_GATHER_PROMPT.format(
            rfp_analysis=rfp,
            rfp_excerpt=rfp_excerpt,
            project_name=rfp.project_name if rfp else "",
            client=rfp.client if rfp else "",
            hot_buttons=rfp.hot_buttons if rfp else [],
            mandatory_reqs=rfp.mandatory_reqs if rfp else [],
            eval_items=rfp.eval_items if rfp else [],
            special_conditions=rfp.special_conditions if rfp else [],
        ),
    )

    return {
        "research_brief": result,
        "current_step": "research_gather_complete",
    }
```

```python
# app/prompts/research_gather.py

RESEARCH_GATHER_PROMPT = """
## 역할
당신은 정부 용역 제안을 위한 사전조사 전문가입니다.
RFP 분석 결과를 면밀히 검토한 뒤, **이 사업에 맞는 조사 차원을 직접 설계**하고 조사를 수행하세요.

## RFP 분석 결과
- 사업명: {project_name}
- 발주기관: {client}
- Hot Buttons (발주기관 핵심 관심사): {hot_buttons}
- 필수 요구사항: {mandatory_reqs}
- 평가항목: {eval_items}
- 특수조건: {special_conditions}

## RFP 원문 발췌
{rfp_excerpt}

---

## STEP 1: 조사 차원 설계

아래를 고려하여, **이 사업의 Go/No-Go 판단과 제안전략 수립에 실질적으로 필요한 조사 차원 3~7개**를 도출하세요.

### 차원 설계 기준
- RFP의 **사업 범주**를 먼저 판별하세요 (예: 성과조사분석, 정책연구, SI/SW개발, 컨설팅, 교육훈련, R&D, 기획·타당성조사 등)
- 사업 범주에 따라 필요한 조사가 근본적으로 다릅니다:
  - 성과조사분석 → 대상 사업 집행 현황, 성과지표 체계, 평가 방법론 비교 등
  - 정책연구 → 정책 입법 이력, 해외 벤치마크, 선행연구, 정책 수혜자 분석 등
  - SI/SW개발 → 기술 스택 동향, 유사 시스템 사례, 보안 요건, 데이터 이관 등
  - 컨설팅 → 조직 현황, 동종 기관 사례, 방법론 비교, 변화관리 등
- **모든 사업에 공통 적용하는 고정 템플릿을 사용하지 마세요**
- 각 차원은 다음 질문에 답할 수 있어야 합니다:
  "이 조사 결과가 Go/No-Go 판단이나 제안전략에 어떻게 쓰이는가?"

### 차원 도출 출력
각 차원에 대해:
- 차원명 (간결하게)
- 조사 목적: 이 차원의 조사 결과가 Go/No-Go 또는 전략 수립에 왜 필요한지
- 핵심 조사 질문 2~3개

## STEP 2: 차원별 조사 수행

STEP 1에서 도출한 각 차원에 대해 조사를 수행하세요.

### 각 차원별 조사 출력
- **핵심 발견 3~5개**: Go/No-Go 판단이나 전략 수립에 직접 영향을 줄 사실·데이터
- **시사점(So What?)**: 이 발견이 우리 입찰에 구체적으로 의미하는 바 (1~2문장)
- **전략 활용 방향**: Go/No-Go 판단 근거 또는 제안전략에 어떻게 반영할지

## 품질 규칙
- 모든 수치에 출처(기관명, 보고서명, 연도) 명기. 예: "대상 사업 예산 집행률 78% (기재부, 2025)"
- 확인 불가한 수치 생성 금지 → "[확인 필요]" 표기
- [추정] 태그로 추정과 사실 구분
- 출처를 특정할 수 없는 일반 상식은 [일반지식] 태그 부착
- **RFP와 무관한 일반론을 나열하지 마세요** — 모든 발견은 이 사업에 대한 구체적 시사점과 연결되어야 합니다

## 출력 형식 (JSON)
{{
  "project_category": "사업 범주 판별 결과 (예: 성과조사분석, 정책연구, SI/SW개발 등)",
  "category_rationale": "사업 범주 판별 근거 (1~2문장)",
  "research_dimensions": [
    {{
      "dimension_id": "D1",
      "dimension_name": "차원명",
      "purpose": "이 차원의 조사 목적 — Go/No-Go 또는 전략에 왜 필요한가",
      "key_questions": ["핵심 조사 질문 1", "..."],
      "findings": [
        {{
          "finding": "핵심 발견 내용",
          "source": "출처 (기관명, 문서명, 연도)",
          "confidence": "확인됨|추정|확인필요"
        }}
      ],
      "implication": "이 사업에 대한 시사점",
      "strategic_use": "go_no_go|strategy|both — 어디에 활용할 정보인지"
    }}
  ],
  "go_no_go_summary": "Go/No-Go 판단에 영향을 줄 핵심 요인 요약 (3~5문장)",
  "strategy_inputs": "제안전략 수립에 활용할 핵심 인사이트 요약 (3~5문장)"
}}
"""
```

### 29-3. 신규 노드: `presentation_strategy`

**위치**: `review_proposal` approved → `presentation_strategy` → `ppt_fan_out_gate`
**역할**: 발표전략 수립 (킬링 메시지, 시간 배분, Q&A 전략)
**근거**: ProposalForge #12(발표전략)
**토큰 예산**: 8,000
**조건부 실행**: `eval_method == 'document_only'`이면 건너뛰기 (POST-06 연동)

```python
# app/graph/nodes/presentation_strategy.py

async def presentation_strategy(state: ProposalState) -> dict:
    """
    ★ v3.2: 발표전략 수립.
    서류심사(document_only) 방식이면 건너뛰고 PPT 생성으로 직행.
    """
    rfp = state.get("rfp_analysis")
    eval_method = ""
    if rfp:
        eval_method = rfp.eval_method if hasattr(rfp, 'eval_method') else rfp.get("eval_method", "")

    # 서류심사이면 발표전략 생략
    if "document_only" in str(eval_method).lower():
        return {"current_step": "presentation_strategy_skip"}

    strategy = state.get("strategy")
    proposal_sections = state.get("proposal_sections", [])
    self_review_score = state.get("parallel_results", {}).get("_self_review_score", {})

    result = await claude_generate(
        PRESENTATION_STRATEGY_PROMPT.format(
            project_name=rfp.project_name if rfp else "",
            client=rfp.client if rfp else "",
            eval_items=rfp.eval_items if rfp else [],
            tech_price_ratio=rfp.tech_price_ratio if rfp else {},
            win_theme=strategy.win_theme if strategy else "",
            ghost_theme=strategy.ghost_theme if strategy else "",
            key_messages=strategy.key_messages if strategy else [],
            self_review_score=self_review_score,
        ),
    )

    return {
        "presentation_strategy": result,
        "current_step": "presentation_strategy_complete",
    }
```

```python
# app/prompts/presentation_strategy.py

PRESENTATION_STRATEGY_PROMPT = """
## 역할
당신은 정부 용역 발표 전략 수립 전문가입니다.
제안서 내용과 평가 기준을 기반으로 최적의 발표 전략을 수립하세요.

## 제안 컨텍스트
- 사업명: {project_name}
- 발주기관: {client}
- 평가항목: {eval_items}
- 기술:가격 비율: {tech_price_ratio}
- Win Theme: {win_theme}
- Ghost Theme: {ghost_theme}
- 핵심 메시지: {key_messages}
- 자가진단 점수: {self_review_score}

## 발표전략 수립 지시

### 1. 킬링 메시지 설계
- 평가위원이 기억할 핵심 메시지 1개 (15자 이내)
- 보조 메시지 2~3개
- 반복 전략: 도입-본론-결론에서 어떻게 반복할 것인가

### 2. 시간 배분 전략
- 전체 발표 시간 대비 각 파트 배분 (배점 비례 + 전략적 가중)
- 고배점 항목에 시간 집중 배분
- 도입(10%), 본론(70%), 결론(10%), 질의응답 대비(10%) 기본 구조

### 3. 발표 3막 구조
- Act 1 (Why): 왜 이 사업이 중요한가 + 우리의 이해도
- Act 2 (How): 어떻게 수행할 것인가 (차별화 방법론)
- Act 3 (Us): 왜 우리팀인가 (실적 + 팀 역량)

### 4. Q&A 전략
- 예상 질문 Top 10 (평가위원 관점)
- 각 질문에 대한 모범 답변 (30초 이내)
- 위험 질문 대응: 약점을 강점으로 전환하는 프레이밍

### 5. 시각 전략
- 핵심 슬라이드 5~7장 선정 + 각 슬라이드의 시각적 포인트
- 데모/시연이 필요한 구간 식별

## 출력 형식 (JSON)
{{
  "killing_message": {{
    "main": "...",
    "sub_messages": [...],
    "repetition_strategy": "..."
  }},
  "time_allocation": [
    {{ "section": "...", "duration_pct": 0, "rationale": "..." }}
  ],
  "three_act_structure": {{
    "act1_why": {{ "key_point": "...", "duration_pct": 0 }},
    "act2_how": {{ "key_point": "...", "duration_pct": 0 }},
    "act3_us": {{ "key_point": "...", "duration_pct": 0 }}
  }},
  "qa_strategy": {{
    "expected_questions": [
      {{ "question": "...", "answer": "...", "risk_level": "high|medium|low" }}
    ]
  }},
  "visual_strategy": {{
    "key_slides": [...],
    "demo_sections": [...]
  }}
}}
"""
```

### 29-4. 기존 프롬프트 보강 — `go_no_go` (발주기관 인텔리전스 5단계)

```python
# app/prompts/go_no_go.py 에 추가 (기존 GO_NO_GO_FULL_PROMPT 보강)

# ★ v3.2: 발주기관 인텔리전스 5단계 프레임워크 (ProposalForge #3)
CLIENT_INTELLIGENCE_FRAMEWORK = """
## 발주기관 인텔리전스 분석 (5단계)

아래 5단계에 따라 발주기관을 심층 분석하세요.
각 단계의 분석 결과가 Go/No-Go 판단의 핵심 근거가 됩니다.

### Step 1: 기관 프로파일링
- 기관 미션, 비전, 전략방향
- 최근 인사이동 (기관장, 부서장)
- 조직도상 해당 사업 담당 부서 파악

### Step 2: 과거 발주 패턴
- 최근 3년 유사 사업 발주 이력
- 낙찰률 (예정가 대비 낙찰가 비율)
- 선호 수행기관 유형 (대기업/중소/학교/연구기관)
- 반복 발주 여부 (동일·유사 사업 계속 발주 시 기존 수행기관 유리)

### Step 3: 평가 성향 추정
- 실적 중시 vs 방법론 중시 vs 가격 중시
- 외부 평가위원 구성 성향 (학계/산업계/연구기관 비율)
- 과거 선정 결과에서 드러나는 패턴

### Step 4: 정책 맥락
- 상위 정책과의 연결 (국가전략, 부처 계획)
- 현 정부 정책 방향과의 정합성
- 관련 법령·제도 변화

### Step 5: 리스크
- 조직개편 리스크 (해당 부서 축소·통합 가능성)
- 예산삭감 리스크 (예산안 변동)
- 국감 이슈 (감사원·국정감사 지적 사항)
- 정치적 민감도 (선거, 정권 교체 영향)

데이터 소스: client_intel_ref (KB 발주기관 DB), research_brief (리서치 조사 결과)
"""

# GO_NO_GO_FULL_PROMPT에 client_intelligence_framework, research_brief 삽입
# 토큰 예산: 15,000 → 18,000 (+3,000)
```

### 29-5. 기존 프롬프트 보강 — `strategy_generate` (경쟁 SWOT + 시나리오 + 연구질문)

```python
# app/prompts/strategy.py 에 추가 (기존 STRATEGY_PROMPT 보강)

# ★ v3.2: 경쟁분석 & Win Strategy (ProposalForge #4)
COMPETITIVE_ANALYSIS_FRAMEWORK = """
## 경쟁분석 프레임워크

### 경쟁사별 SWOT 매트릭스
각 경쟁사에 대해 SWOT 분석 + "그래서 어떻게" 대응전략을 제시:
| 경쟁사 | S(강점) → 대응 | W(약점) → 공략 | O(기회) → 활용 | T(위협) → 방어 |

### 차별화 포인트 구조
각 차별화 포인트를 다음 구조로 작성:
- **What**: 무엇이 다른가
- **Why**: 왜 발주기관에 중요한가
- **How**: 어떻게 증명할 것인가
- **Evidence**: 구체적 근거 (수행실적, 특허, 인력 자격 등)

### 경쟁 시나리오별 대응전략
- **Best Case**: 경쟁사 약점이 부각되는 시나리오 → 공격적 차별화
- **Base Case**: 동등 경쟁 시나리오 → 가격+품질 균형
- **Worst Case**: 경쟁사 강점이 부각되는 시나리오 → 방어적 대응

### Win Theme 구조
"우리는 [X역량/경험]이기 때문에 [Y성과]를 가장 잘 할 수 있다"
- 각 Win Theme에 supporting evidence 최소 2개
"""

# ★ v3.2: 전략수립 보강 (ProposalForge #7)
STRATEGY_RESEARCH_FRAMEWORK = """
## 연구수행 전략 프레임워크

### 핵심 연구질문(Research Questions) 도출
RFP의 핵심 과업에서 3~5개 연구질문을 도출하세요:
- RQ1: [연구질문] → [답을 위한 접근법]
- RQ2: ...

### 연구수행 프레임워크
전체 연구/수행 구조를 시각적으로 설명 (Phase → Task → Output):
- Phase 1: [명칭] — 핵심 활동, 산출물, 기간
- Phase 2: ...

### 방법론 선택 근거
각 방법론 선택에 대해 3가지 관점의 근거 제시:
1. **학술 타당성**: 해당 방법론의 이론적 기반, 선행연구 활용 사례
2. **실무 실현가능성**: 투입인력·기간·예산 내 실행 가능 여부
3. **차별성**: 경쟁사 대비 방법론적 우위 포인트
"""

# 토큰 예산: 20,000 → 25,000 (+5,000)
```

### 29-6. 기존 프롬프트 보강 — `plan_price` (원가기준·노임단가·입찰시뮬레이션)

```python
# app/prompts/plan.py 에 추가 (기존 PLAN_PRICE_PROMPT 보강)

# ★ v3.2: 예산산정 상세 (ProposalForge #8 — 최대 가치 항목)
BUDGET_DETAIL_FRAMEWORK = """
## 예산산정 상세 프레임워크

### 1. 원가 기준 확인
RFP에서 적용 원가 기준을 판별하세요:
- SW사업 대가산정 기준 (한국소프트웨어산업협회)
- 엔지니어링 사업 대가 기준 (한국엔지니어링협회)
- 학술연구용역비 산정 기준 (기획재정부)
- 기타 (RFP 명시 기준)

### 2. 인건비 산출
등급별 노임단가 × 투입 M/M:
| 등급 | 노임단가(월) | 투입 M/M | 소계 |
|------|-------------|---------|------|
| 기술사 | [단가] | [M/M] | [금액] |
| 특급기술자 | [단가] | [M/M] | [금액] |
| 고급기술자 | [단가] | [M/M] | [금액] |
| 중급기술자 | [단가] | [M/M] | [금액] |
| 초급기술자 | [단가] | [M/M] | [금액] |

### 3. 직접경비
항목별 산출 근거를 명시:
- 여비 (출장비): 출장 횟수 × 단가
- 회의비: 회의 횟수 × 단가
- 설문조사비: 대상 수 × 단가 (해당 시)
- 데이터 구매비: 필요 데이터 목록 × 단가
- 인쇄비: 보고서 부수 × 단가
- 기타: RFP 특수 요구사항

### 4. 간접경비(제경비)
기관 유형별 인건비 대비 비율:
- 영리법인: 110~120%
- 비영리법인: 40~60%
- 컨소시엄 시 기관별 차등 적용

### 5. 기술료(이윤)
(인건비 + 직접경비 + 간접경비) × 비율:
- 영리법인: 20% 이내
- 비영리법인: 해당 없음

### 6. 입찰가격 결정 시뮬레이션
계약 방식별 최적가 산출:
- **협상에 의한 계약**: 기술평가 70~90% + 가격평가 10~30% → 최적 제안가격 범위
- **적격심사**: 추정가격 대비 최적 사정률 산출
- **2단계 경쟁입찰**: 기술 통과 후 가격 경쟁 → 최저가 전략 vs 적정가 전략

## 출력 형식 (JSON)
{{
  "cost_standard": "적용 원가 기준",
  "labor_cost": {{
    "breakdown": [...],
    "total": 0
  }},
  "direct_expenses": {{
    "items": [...],
    "total": 0
  }},
  "overhead": {{
    "rate": 0,
    "total": 0
  }},
  "profit": {{
    "rate": 0,
    "total": 0
  }},
  "total_cost": 0,
  "bid_simulation": {{
    "method": "...",
    "optimal_price": 0,
    "price_range": {{ "min": 0, "max": 0 }},
    "rationale": "..."
  }}
}}
"""

# plan_price 노드 출력에 budget_detail 필드 추가
# 토큰 예산: 12,000 → 15,000 (+3,000)

# ★ v3.3: labor_rates, market_price_data DB 조회 로직 추가 (ProposalForge 비교 검토 반영)
# 프롬프트의 "[단가]" 플레이스홀더를 실제 DB 데이터로 대체

async def plan_price(state: ProposalState) -> dict:
    """
    STEP 3: 예산산정.
    ★ v3.3: labor_rates, market_price_data 테이블에서 실제 데이터 조회 후
    프롬프트에 주입하여 "[단가]" 플레이스홀더 제거.
    """
    rfp = state.get("rfp_analysis")
    strategy = state.get("strategy")

    # 1. 원가 기준 판별 → 해당 기관의 노임단가 조회
    cost_standard = _detect_cost_standard(rfp)  # 'KOSA' | 'KEA' | 'MOEF' | 'OTHER'
    current_year = datetime.now().year

    labor_rates = await db.fetch_all(
        """SELECT grade, monthly_rate, daily_rate
           FROM labor_rates
           WHERE standard_org = $1 AND year = $2
           ORDER BY monthly_rate DESC""",
        cost_standard, current_year
    )
    # Fallback: 올해 데이터 없으면 직전 연도 조회 (§22-4-2)
    if not labor_rates:
        labor_rates = await db.fetch_all(
            """SELECT grade, monthly_rate, daily_rate
               FROM labor_rates
               WHERE standard_org = $1 AND year = $2
               ORDER BY monthly_rate DESC""",
            cost_standard, current_year - 1
        )

    # 2. 유사 도메인·규모의 시장 낙찰가 벤치마크 조회
    domain = _classify_domain(rfp)  # 'SI/SW개발', '정책연구', '성과분석', '컨설팅' 등
    budget = rfp.budget if rfp else None
    budget_range = (int(budget * 0.5), int(budget * 2.0)) if budget else (0, 999_999_999_999)

    market_benchmarks = await db.fetch_all(
        """SELECT bid_ratio, num_bidders, evaluation_method, year
           FROM market_price_data
           WHERE domain = $1 AND budget BETWEEN $2 AND $3
           ORDER BY year DESC LIMIT 20""",
        domain, budget_range[0], budget_range[1]
    )

    # 3. 조회된 데이터를 프롬프트에 주입
    labor_rates_table = _format_labor_rates_table(labor_rates)  # Markdown 테이블 형식
    benchmark_summary = _format_benchmark_summary(market_benchmarks)  # 평균 낙찰률, 경쟁 강도 등

    result = await claude_generate(
        PLAN_PRICE_PROMPT.format(
            rfp_analysis=rfp,
            strategy=strategy,
            cost_standard=cost_standard,
            labor_rates_table=labor_rates_table,      # ★ 실제 노임단가 데이터
            benchmark_summary=benchmark_summary,       # ★ 시장 벤치마크 데이터
        ),
    )

    return {
        "parallel_results": {"bid_price": result},
        "budget_detail": result,
    }


def _detect_cost_standard(rfp) -> str:
    """RFP 내용에서 적용 원가 기준 자동 판별."""
    if not rfp:
        return "KOSA"
    text = str(rfp).lower()
    if "엔지니어링" in text or "기술용역" in text:
        return "KEA"
    if "학술" in text or "연구용역" in text or "기획재정부" in text:
        return "MOEF"
    return "KOSA"  # SW사업 대가산정 기준 (기본값)


def _classify_domain(rfp) -> str:
    """RFP 사업 유형을 도메인으로 분류."""
    if not rfp:
        return "기타"
    text = str(rfp).lower()
    if any(kw in text for kw in ["시스템", "개발", "구축", "sw", "소프트웨어"]):
        return "SI/SW개발"
    if any(kw in text for kw in ["정책", "연구", "학술"]):
        return "정책연구"
    if any(kw in text for kw in ["성과", "평가", "분석", "조사"]):
        return "성과분석"
    if any(kw in text for kw in ["컨설팅", "자문", "진단"]):
        return "컨설팅"
    return "기타"
```

### 29-7. 기존 프롬프트 보강 — `self_review` (3인 페르소나 시뮬레이션)

```python
# app/prompts/self_review.py 에 추가 (기존 SELF_REVIEW_PROMPT 보강)

# ★ v3.2: 평가 시뮬레이션 (ProposalForge #10 — 3인 페르소나)
EVALUATION_SIMULATION_FRAMEWORK = """
## 평가위원 시뮬레이션 (3인 페르소나)

기존 4축 100점 정량 평가에 추가하여, 3인의 가상 평가위원 관점에서 정성 평가를 수행하세요.

### 평가위원 A (산업계 전문가)
- 관점: 실현가능성, 현장 적용성, 실무 경험 기반 판단
- 핵심 질문: "이 방법론을 실제 현장에서 적용할 수 있는가?"
- 평가: 각 평가항목에 대해 강점/약점 1줄 코멘트 + 예상 질문 1개

### 평가위원 B (학계 전문가)
- 관점: 방법론 타당성, 논리 구조, 학술적 엄밀성
- 핵심 질문: "이론적 근거가 충분하고 연구 설계가 타당한가?"
- 평가: 각 평가항목에 대해 강점/약점 1줄 코멘트 + 예상 질문 1개

### 평가위원 C (연구기관 전문가)
- 관점: 기존 연구 대비 차별성, 정책 기여, 활용 가능성
- 핵심 질문: "기존 유사 연구와 차별화되고, 정책에 실제 기여하는가?"
- 평가: 각 평가항목에 대해 강점/약점 1줄 코멘트 + 예상 질문 1개

## 품질 게이트 (★ v3.2 개선)
기존: 전체 ≥ 80 → pass
변경: 전체 ≥ 80 AND 각 축 ≥ 17.5 (70% of 25) → pass
      전체 ≥ 80 BUT 축 < 17.5 → 해당 축 경고 + Human 판단 위임

## 출력에 추가되는 필드 (evaluation_simulation)
{{
  "persona_reviews": [
    {{
      "persona": "산업계",
      "strengths": [...],
      "weaknesses": [...],
      "expected_questions": [{{ "question": "...", "model_answer": "..." }}]
    }},
    ...
  ],
  "axis_warnings": [
    {{ "axis": "...", "score": 0, "warning": "..." }}
  ]
}}
"""

# self_review_with_auto_improve 함수에 통합:
# 1. 기존 4축 100점 평가 유지
# 2. 3인 페르소나 정성 코멘트 추가
# 3. 축별 최소 기준(17.5) 적용
# 4. evaluation_simulation state 필드로 출력
```

### 29-8. 기존 프롬프트 보강 — `proposal_section` (자체검증 체크리스트)

```python
# app/prompts/proposal_sections.py 에 추가

# ★ v3.2: 섹션별 자체검증 체크리스트 (ProposalForge #9)
SECTION_SELF_CHECK = """
## 섹션 자체검증 체크리스트
작성 완료 후 아래 항목을 자체 검증하고 결과를 JSON에 포함하세요:

1. □ RFP 필수과업 반영 여부: 해당 섹션이 매핑된 RFP 요구사항을 모두 다루었는가?
2. □ 평가항목 대응 충분성: 해당 평가항목의 배점에 비례한 분량과 깊이인가?
3. □ 핵심 키워드 포함 여부: RFP의 핵심 키워드가 섹션 내에 자연스럽게 포함되었는가?
4. □ 연속 텍스트 제한: 2페이지 이상 연속 텍스트가 없는가? (도표·그림·박스 삽입 필요)

출력에 추가:
"self_check": {{
  "rfp_coverage": true|false,
  "eval_item_depth": true|false,
  "keyword_inclusion": true|false,
  "text_break_ok": true|false,
  "issues": ["미충족 항목 설명"]
}}
"""
```

### 29-9. PPT 프롬프트 신규 생성

```python
# app/prompts/ppt.py (★ v3.2: 신규 작성 — ProposalForge #11)

PPT_SYSTEM_PROMPT = """
## 역할
당신은 정부 용역 발표 PPT 설계 전문가입니다.
제안서 내용과 발표전략을 기반으로 효과적인 슬라이드를 설계하세요.

## PPT 설계 원칙

### 1. 1슬라이드 1메시지
- 하나의 슬라이드에는 하나의 핵심 메시지만 전달
- 헤드라인이 곧 메시지 (질문형 X, 선언형 O)
- 예: "시스템 아키텍처" ❌ → "클라우드 네이티브로 30% 비용 절감" ✅

### 2. 시각 > 텍스트
- 텍스트: 50자 × 5줄 이내 (250자 제한)
- 키워드 중심, 문장형 서술 최소화
- 도표, 차트, 다이어그램, 아이콘 적극 활용
- 시각적 요소가 슬라이드 면적의 60% 이상 차지

### 3. 고배점 항목 집중
- 평가 배점 비례로 슬라이드 수 배분
- 핵심 차별화 포인트에 2~3배 슬라이드 할당
- 저배점/행정사항은 1장 요약으로 처리

### 4. 3막 구조 스토리라인
- **Why (도입)**: 사업 이해도 + 문제 인식 → 청중의 공감 확보
- **How (본론)**: 수행 방법론 + 차별화 → 논리적 설득
- **Us (결론)**: 팀 역량 + 약속 → 신뢰와 확신

### 5. 슬라이드 설계 단위
각 슬라이드에 대해 아래 정보를 생성:
"""

PPT_SLIDE_PROMPT = """
{ppt_system_prompt}

## 발표전략 컨텍스트
{presentation_strategy}

## 제안서 섹션 내용
{section_content}

## 해당 슬라이드 지시
- 섹션: {section_id}
- 슬라이드 번호: {slide_index}

## 출력 형식 (JSON)
{{
  "slide_id": "{section_id}_slide_{slide_index}",
  "headline": "핵심 메시지 (선언형, 20자 이내)",
  "visual_type": "chart|diagram|table|icon_grid|timeline|comparison|image",
  "key_points": ["핵심 포인트 1", "핵심 포인트 2", "핵심 포인트 3"],
  "text_content": "본문 (250자 이내)",
  "speaker_note": "발표자 노트 (구어체, 30초~1분 분량)",
  "duration_seconds": 60,
  "visual_description": "시각 자료 상세 설명 (pptx_builder가 참조)"
}}
"""
```

### 29-10. 토큰 예산 갱신 요약

| 노드 | v3.1 예산 | v3.2 예산 | 변경 | 비고 |
|------|----------|----------|------|------|
| research_gather | — | 15,000 | 신규 | RFP-적응형 사전조사 |
| go_no_go | 6,000 | 18,000 | +12,000 | 발주기관 인텔 5단계 + research_brief |
| strategy_generate | 10,000 | 25,000 | +15,000 | SWOT + 시나리오 + 연구질문 |
| plan_price | (plan 6,000 중 일부) | 15,000 | +9,000 | 원가기준·노임단가·입찰시뮬레이션 |
| presentation_strategy | — | 8,000 | 신규 | 발표전략 (조건부) |
| PPT (sldie당) | 4,000 | 4,000 | 변경 없음 | 프롬프트 내용만 보강 |
| **추가 토큰 합계** | | | **~+34,000** | ~80K → ~114K/프로젝트 |

> **비용 영향**: Claude Sonnet 기준 프로젝트당 ~$0.10~0.50 추가. 허용 범위 내.
> `token_manager.py`의 `STEP_BUDGETS` 딕셔너리에 신규 노드 예산 추가 필요 (§21 참조).

### 29-11. ProposalForge 에이전트 → TENOPA 노드 매핑 참조표

| # | ProposalForge 에이전트 | 판정 | TENOPA 대응 | 비고 |
|---|---|---|---|---|
| 1 | Orchestrator | 스킵 | graph.py 엣지 라우팅 | LangGraph가 동일 역할 수행 |
| 2 | RFP 해석 | 소폭 보강 | rfp_analyze | hidden_requirements 필드 추가 |
| 3 | 발주기관 인텔리전스 | 프롬프트 보강 | go_no_go | 5단계 분석 프레임워크 (§29-4) |
| 4 | 경쟁분석 & Win Strategy | 프롬프트 보강 | strategy_generate | SWOT + 시나리오 (§29-5) |
| 5-6 | 리서치 디렉터 + 7서브 | 신규 노드 | research_gather | RFP-적응형 1개 노드 (§29-2) |
| 7 | 전략 수립 | 소폭 보강 | strategy_generate | 연구질문·방법론 (§29-5) |
| 8 | 예산 산정 | 대폭 보강 | plan_price | 원가기준·입찰시뮬 (§29-6) |
| 9 | 제안서 작성 | 소폭 보강 | proposal_section | 자체검증 체크리스트 (§29-8) |
| 10 | 평가 시뮬레이션 | self_review 보강 | self_review | 3인 페르소나 (§29-7) |
| 11 | PPT 생성 | 프롬프트 생성 | ppt.py | 신규 프롬프트 (§29-9) |
| 12 | 발표전략 | 신규 노드 | presentation_strategy | 발표전략 수립 (§29-3) |
| 13 | Verification | 소폭 보강 | self_review | 팩트체크 강화 (기존 source_tagger 활용) |

---

## 29-1. prompt-enhancement 추가 필드 (§32-8 merged)

> `docs/02-design/features/prompt-enhancement.design.md` 보완 사항.
> 구현: `app/services/phase_prompts.py`

#### 29-1-1. PHASE3_USER 추가 출력 필드

| 필드 | 설명 | 설계 문서 상태 |
|---|---|---|
| `alternatives_considered` | 대안 비교 | 기존 (prompt-enhancement §2-1) |
| `risks_mitigations` | 리스크 대응 | 기존 |
| `implementation_checklist` | 추진 체크리스트 | 기존 |
| `logic_model` | 투입→활동→산출→결과→영향 Logic Model | ★ 신규 추가 |
| `objection_responses` | 예상 반론 + 대응 논리 | ★ 신규 추가 |

#### 29-1-2. PHASE4_SYSTEM 추가 원칙

기존 3개 원칙에 5개 추가:

| # | 원칙 | 설명 | 설계 문서 상태 |
|---|---|---|---|
| 1 | 대안 비교 | 2개 이상 대안 + 채택 근거 | 기존 |
| 2 | 리스크 대응 | 리스크별 대응 전략 | 기존 |
| 3 | 추진 체계 | 담당/일정/마일스톤 | 기존 |
| 4 | Logic Model | 투입→활동→산출→결과→영향 | ★ 신규 |
| 5 | Assertion Title | 각 섹션 제목을 주장형으로 | ★ 신규 |
| 6 | Narrative Arc | 문제→긴장→해결 구조 | ★ 신규 |
| 7 | Objection Handling | 예상 반론 선제 대응 | ★ 신규 |
| 8 | Price Anchoring | 비용 대비 가치 프레이밍 | ★ 신규 |

---

## 33. ★ Grant-Writer Best Practice 프롬프트 개선 (v3.6)

> **배경**: 미국 비영리/연구 보조금 제안서 작성 스킬(Grant-Writer)의 Best Practice를 검토하여, 한국 용역 제안서 시스템에 적용 가능한 공통 원칙을 반영. "심사위원 설득", "근거 기반 서술", "내러티브 일관성" 등 도메인 불문 공통 원칙.
>
> **변경하지 않는 것**: 새 섹션 유형 추가(미국식 구조 이식 금지), Supporting Documents, Funder Language Vector DB (인프라 변경 필요)

### 33-1. 스토리텔링 원칙 — EVALUATOR_PERSPECTIVE_BLOCK

**파일**: `app/prompts/section_prompts.py`
**근거**: Grant-Writer "Balance statistics with human stories", "Individual narratives make abstract problems real"

모든 섹션 프롬프트에 공통 적용되는 EVALUATOR_PERSPECTIVE_BLOCK에 스토리텔링 원칙 추가:

```
### 스토리텔링 원칙
- 핵심 주장마다 **구체적 사례 1개 이상** 포함 (프로젝트명, 기간, 성과 수치)
- 추상적 설명 → 구체적 장면(미니 내러티브)으로 전환: "A기관에서 B문제를 C방법으로 해결하여 D% 개선"
- 수치와 스토리를 교차 배치: 데이터로 신뢰 → 사례로 공감 → 결론으로 확신
```

> 기존 채점 원리(정합성·구체성·논리성·차별성·실현가능성)와 최고점 획득 방법은 유지. 스토리텔링은 "구체성"과 "차별성" 원리를 실행 레벨로 구체화한 것.

### 33-2. SMART 목표 프레임워크 — PLAN_STORY + ADDED_VALUE

**파일**: `app/prompts/plan.py` (PLAN_STORY_PROMPT), `app/prompts/section_prompts.py` (ADDED_VALUE)
**근거**: Grant-Writer "Write SMART goals — Specific, Measurable, Achievable, Relevant, Time-bound"

#### PLAN_STORY_PROMPT 2단계 추가:

```
- 각 섹션의 **기대 성과**를 SMART 기준으로 구체화하세요:
  - **S**pecific(구체적): 무엇을 달성하는가
  - **M**easurable(측정 가능): 어떤 지표로 측정하는가
  - **A**chievable(달성 가능): 현실적 근거가 있는가
  - **R**elevant(관련성): 사업 목적과 직결되는가
  - **T**ime-bound(기한): 언제까지 달성하는가
```

#### ADDED_VALUE 기대효과 (정량) 보강:

```
| 목표 | 현재(Baseline) | 목표치(Target) | 측정방법 | 달성시점 |
```

+ "향후 확장 로드맵"에 자체 운영 전환 계획 포함.

### 33-3. 예산-활동 정합성 — PLAN_PRICE Budget Narrative

**파일**: `app/prompts/plan.py` (PLAN_PRICE_PROMPT)
**근거**: Grant-Writer "Budget alignment — Expenses must match stated activities", "Budget Narrative"

지시사항에 추가:
```
5. **예산 서술(Budget Narrative)**: 각 비용 항목이 어떤 수행 활동을 지원하는지 연결하여 정당화.
```

출력 JSON에 `budget_narrative` 필드 추가:
```json
"budget_narrative": [
  {"cost_item": "비용 항목명", "linked_activity": "수행 활동", "justification": "필요성 근거"}
]
```

### 33-4. 발주기관 용어 정합성 — COMMON_SYSTEM_RULES

**파일**: `app/services/claude_client.py`
**근거**: Grant-Writer "Align with funder — Mirror their language, priorities, and values"

```
[용어 정합성 원칙]
- RFP에서 사용하는 핵심 용어·표현을 그대로 사용하세요. 동의어로 바꾸지 마세요.
- 발주기관의 비전·미션 문서에 나오는 키워드를 자연스럽게 활용하세요.
```

> 기존 §16-3-1 TRUSTWORTHINESS_RULES의 "4. 발주처 언어 사용"을 COMMON_SYSTEM_RULES 레벨로 승격. 모든 Claude 호출에 적용되는 기본 원칙으로 강화.

### 33-5. 지속가능성 — MAINTENANCE

**파일**: `app/prompts/section_prompts.py` (MAINTENANCE)
**근거**: Grant-Writer "Sustainability Plan — Show long-term viability beyond grant period"

필수 포함 요소 6번 추가:
```
6. **지속가능성** — 사업 종료 후 시스템/성과 유지 방안
   - 자체 운영 역량 확보 계획 (내부 인력 교육, 운영 매뉴얼 수준)
   - 기술 종속 최소화 전략 (표준 기술 활용, 소스코드 이전 등)
   - 유지보수 예산 확보 가이드라인
```

self_check에 `sustainability_plan_included` 키 추가.

### 33-6. 적응적 관리 — METHODOLOGY

**파일**: `app/prompts/section_prompts.py` (METHODOLOGY)
**근거**: Grant-Writer "Challenges & Adaptations — Honest assessment", "Lessons Learned"

필수 포함 요소 6번 추가:
```
6. 적응적 관리 (Adaptive Management)
   - 중간점검 시점에서의 성과 평가 → 계획 조정 프로세스
   - 이해관계자 피드백 수집·반영 절차
   - 예상치 못한 이슈 발생 시 의사결정 프로세스
   - 이전 단계에서 얻은 교훈(Lessons Learned)을 다음 단계에 반영하는 메커니즘
```

self_check에 `adaptive_management_included` 키 추가.

### 33-7. Needs Validation 강화 — UNDERSTAND

**파일**: `app/prompts/section_prompts.py` (UNDERSTAND)
**근거**: Grant-Writer "Document problem with data and human stories", "Needs Statement"

현황 분석(AS-IS) 보강:
```
- 명시적 요구(RFP에 적힌 것) vs 잠재적 요구(맥락에서 추론되는 것)를 구분하여 서술
- "발주기관이 아직 인식하지 못했을 수 있는 관련 이슈" 1~2개 제시 (리서치 기반)
```

### 33-8. 변경 영향 요약

| 파일 | 변경 항목 | 추가 줄 수 | 토큰 영향 |
|------|----------|:--------:|:--------:|
| `app/services/claude_client.py` | COMMON_SYSTEM_RULES 용어 정합성 | +3 | +50 (모든 호출) |
| `app/prompts/section_prompts.py` | EVALUATOR_PERSPECTIVE_BLOCK 스토리텔링 | +4 (×11 섹션) | +200/섹션 |
| `app/prompts/section_prompts.py` | METHODOLOGY 적응적 관리 | +5 | +150 |
| `app/prompts/section_prompts.py` | MAINTENANCE 지속가능성 | +4 | +120 |
| `app/prompts/section_prompts.py` | ADDED_VALUE SMART 표 + 자체 운영 | +4 | +120 |
| `app/prompts/section_prompts.py` | UNDERSTAND Needs Validation | +2 | +60 |
| `app/prompts/plan.py` | PLAN_STORY SMART 프레임워크 | +6 | +180 |
| `app/prompts/plan.py` | PLAN_PRICE Budget Narrative | +3 | +90 |
| **합계** | | **~+31줄** | **~+970 토큰** |

> 토큰 예산 영향: 프로젝트당 ~+1K 토큰 (전체 ~114K 대비 0.9%). 허용 범위.
