# 서비스 설계 v3.0 (§20-§26)

> **소속**: proposal-agent-v1 설계 문서 v3.5
> **관련 파일**: [11-database-schema.md](11-database-schema.md), [01-architecture.md](01-architecture.md)
> **원본 섹션**: §20, §21, §22, §23, §24, §25, §26

---

## 20. ★ Knowledge Base 설계 (v3.0)

> **요구사항 §4 (Part A~F + Export) 대응**. 모든 KB 데이터는 조직(org_id) 단위로 격리, pgvector 시맨틱 검색 지원.

### 20-1. 임베딩 서비스

```python
# app/services/embedding_service.py
from openai import AsyncOpenAI

EMBEDDING_MODEL = "text-embedding-3-small"  # 1536차원
EMBEDDING_DIMENSIONS = 1536

openai_client = AsyncOpenAI()

async def generate_embedding(text: str) -> list[float]:
    """텍스트 → 임베딩 벡터 생성."""
    response = await openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text[:8000],  # 토큰 제한 방어
    )
    return response.data[0].embedding


async def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """배치 임베딩 생성 (최대 100건)."""
    response = await openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[t[:8000] for t in texts[:100]],
    )
    return [d.embedding for d in response.data]
```

### 20-2. 통합 KB 검색 서비스

```python
# app/services/knowledge_search.py

async def unified_search(
    query: str,
    org_id: str,
    filters: dict = None,  # { areas: ["content","client","competitor","lesson","capability"], period, industry, positioning }
    top_k: int = 5,
    max_body_length: int = 500,  # TKN-04: 본문 축약 상한
) -> dict:
    """
    통합 KB 검색 — 시맨틱(pgvector) + 키워드(tsvector) 하이브리드.
    결과를 영역별로 그룹화하여 반환.
    """
    query_embedding = await generate_embedding(query)

    results = {}
    areas = filters.get("areas", ["content","client","competitor","lesson","capability"]) if filters else None

    # 영역별 병렬 검색
    tasks = []
    if not areas or "content" in areas:
        tasks.append(_search_content(query, query_embedding, org_id, top_k, max_body_length))
    if not areas or "client" in areas:
        tasks.append(_search_clients(query, query_embedding, org_id, top_k))
    if not areas or "competitor" in areas:
        tasks.append(_search_competitors(query, query_embedding, org_id, top_k))
    if not areas or "lesson" in areas:
        tasks.append(_search_lessons(query, query_embedding, org_id, top_k))
    if not areas or "capability" in areas:
        tasks.append(_search_capabilities(query, org_id, top_k))

    all_results = await asyncio.gather(*tasks)
    # 영역별 그룹화 반환
    return {r["area"]: r["items"] for r in all_results}


async def _search_content(query, embedding, org_id, top_k, max_body):
    """콘텐츠 라이브러리 시맨틱 검색 (pgvector cosine similarity)."""
    rows = await db.execute("""
        SELECT id, title, LEFT(body, $4) as body_excerpt, quality_score,
               1 - (embedding <=> $1::vector) as similarity
        FROM content_library
        WHERE org_id = $2 AND status = 'published'
        ORDER BY embedding <=> $1::vector
        LIMIT $3
    """, embedding, org_id, top_k, max_body)
    return {"area": "content", "items": rows}
```

### 20-3. 콘텐츠 라이브러리 서비스

```python
# app/services/content_library.py

async def calculate_quality_score(content_id: str) -> float:
    """
    콘텐츠 품질 점수 산출 (CL-08):
    quality_score = (won_rate × 40) + (reuse_rate × 30) + (freshness × 30)
    - won_rate: 이 콘텐츠 포함 제안서 수주 비율
    - reuse_rate: 재사용 횟수 (정규화)
    - freshness: 최근 갱신일 기준 (6개월 내 = 100%, 이후 감쇠)
    """
    content = await get_content(content_id)
    total = content["won_count"] + content["lost_count"]
    won_rate = (content["won_count"] / total * 100) if total > 0 else 50
    reuse_rate = min(content["reuse_count"] / 10 * 100, 100)  # 10회 이상이면 100%
    days_since_update = (now() - content["updated_at"]).days
    freshness = max(0, 100 - (days_since_update - 180) * 0.5) if days_since_update > 180 else 100

    return won_rate * 0.4 + reuse_rate * 0.3 + freshness * 0.3


async def suggest_content_for_section(
    section_topic: str,
    org_id: str,
    top_k: int = 5,
) -> list[dict]:
    """STEP 4 섹션 작성 시 유사 콘텐츠 자동 추천 (DOC-14)."""
    results = await unified_search(
        query=section_topic,
        org_id=org_id,
        filters={"areas": ["content"]},
        top_k=top_k,
    )
    return sorted(results.get("content", []), key=lambda x: x["quality_score"], reverse=True)
```

### 20-4. 학습 피드백 루프 (프로젝트 완료 시 자동 KB 환류)

```python
# app/services/feedback_loop.py

async def process_project_completion(proposal_id: str, result: str):
    """
    프로젝트 완료 시 KB 자동 환류 (LRN-03~07):
    1. 발주기관 DB 업데이트 제안
    2. 경쟁사 DB 업데이트 제안
    3. 전략 아카이브 기록
    4. (수주 시) 콘텐츠 라이브러리 등록 후보 추천
    """
    proposal = await get_proposal(proposal_id)

    # 1. 발주기관 DB 자동 업데이트 제안
    if proposal.get("client"):
        client = await find_client_by_name(proposal["client"], proposal["org_id"])
        if client:
            await create_client_bid_history(client["id"], proposal_id, result)
            # 관계 수준 업데이트 제안 (수주→격상, 패찰→유지)
            suggested_relationship = "close" if result == "won" else client["relationship"]
            await create_notification(
                user_id=proposal["created_by"],
                type="kb_update_suggestion",
                title=f"발주기관 DB 업데이트 제안: {proposal['client']}",
                body=f"관계 수준: {client['relationship']} → {suggested_relationship} (제안)",
            )

    # 2. 콘텐츠 라이브러리 등록 후보 추천 (수주 시)
    if result == "won":
        sections = await get_proposal_sections(proposal_id)
        for section in sections:
            await create_notification(
                user_id=proposal["created_by"],
                type="content_suggestion",
                title=f"콘텐츠 등록 후보: {section['title']}",
                body=f"수주 제안서 '{proposal['name']}'의 섹션을 콘텐츠 라이브러리에 등록하시겠습니까?",
            )

    # 3. 교훈 아카이브 기록 준비 (회고 워크시트 작성 대기)
    await create_notification(
        user_id=proposal["created_by"],
        type="retrospect_reminder",
        title=f"회고 작성 요청: {proposal['name']}",
        body="프로젝트 결과가 등록되었습니다. 7일 이내에 회고 워크시트를 작성해 주세요.",
    )
```

### 20-5. KB 내보내기 API

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET | `/api/kb/export/capabilities` | 역량 DB CSV/Excel 다운로드 | lead (소속 팀), admin (전체) |
| GET | `/api/kb/export/clients` | 발주기관 DB CSV/Excel 다운로드 | lead, admin |
| GET | `/api/kb/export/competitors` | 경쟁사 DB CSV/Excel 다운로드 | lead, admin |
| GET | `/api/kb/export/content` | 콘텐츠 라이브러리 메타 CSV + 본문 ZIP | lead, admin |
| GET | `/api/kb/export/lessons` | 교훈 아카이브 CSV/Excel 다운로드 | lead, admin |

### 20-6. KB API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/kb/search` | 통합 KB 검색 (시맨틱 + 키워드, 영역별 그룹화) |
| GET/POST/PUT/DELETE | `/api/content-library/*` | 콘텐츠 라이브러리 CRUD |
| POST | `/api/content-library/{id}/approve` | 콘텐츠 승인 (팀장) |
| GET/POST/PUT/DELETE | `/api/clients/*` | 발주기관 DB CRUD |
| GET/POST/PUT/DELETE | `/api/competitors/*` | 경쟁사 DB CRUD |
| GET/POST | `/api/lessons/*` | 교훈 아카이브 조회·작성 |
| POST | `/api/proposals/{id}/retrospect` | 회고 워크시트 작성 → retrospect 상태 전환 |

---

## 21. ★ AI 토큰 효율화 설계 (v3.0)

> **요구사항 §12-2 (TKN-01~09) 대응**. Claude API 비용의 대부분은 input 토큰에서 발생. 필요한 정보만 필요한 만큼 전달.

### 21-1. 토큰 매니저

```python
# app/services/token_manager.py
from anthropic import Anthropic

# STEP별 컨텍스트 토큰 예산 (TKN-01) — v3.5 실제 운영값으로 업데이트
# [v3.5 변경] 노드명 변경(strategy→strategy_generate, plan_section→plan_*), 새 노드 추가
STEP_TOKEN_BUDGETS = {
    "rfp_search":         8_000,   # STEP 0: 공고 목록 + 역량 요약
    "rfp_analyze":        20_000,  # STEP 1①: RFP 원문 (v3.5: 30K→20K, 구조화 요약 전달로 축소)
    "research_gather":    15_000,  # STEP 1①-b: RFP 기반 동적 리서치 (v3.2 신규)
    "go_no_go":           12_000,  # STEP 1②: RFP분석서 + 역량 (v3.5: 15K→12K)
    "strategy_generate":  25_000,  # STEP 2: 포지셔닝 매트릭스 + SWOT + 시나리오
    "plan_team":          10_000,  # STEP 3: 인력 구성
    "plan_assign":        10_000,  # STEP 3: 역할 배정
    "plan_schedule":      10_000,  # STEP 3: 일정
    "plan_story":         20_000,  # STEP 3: 목차 + 스토리라인 설계 (v3.5)
    "plan_price":         15_000,  # STEP 3: 가격 + 노임단가 DB 조회
    "proposal_write_next": 30_000, # STEP 4: 순차 섹션 작성 (v3.5, 이전 섹션 컨텍스트 포함)
    "self_review":        25_000,  # STEP 4: 전체 제안서 + Compliance + 5방향 라우팅
    "presentation_strategy": 10_000, # STEP 5: 발표 전략 (서류심사 시 스킵)
    "ppt_toc":            12_000,  # STEP 5: PPT 목차
    "ppt_visual_brief":   12_000,  # STEP 5: 비주얼 브리프
    "ppt_storyboard":     15_000,  # STEP 5: 스토리보드
}

# KB 검색 결과 상한 (TKN-04)
KB_TOP_K = 5
KB_MAX_BODY_LENGTH = 500  # 각 건 본문 축약 길이

# 피드백 윈도우 (TKN-03)
FEEDBACK_WINDOW_SIZE = 3  # 최근 N회분만 전체 포함


class TokenManager:
    """토큰 예산 관리 + Prompt Caching 제어."""

    @staticmethod
    def build_context(
        step: str,
        rfp_summary: dict,        # TKN-02: RFP분석서 (원문 아님)
        strategy: dict = None,
        plan: dict = None,
        feedback_history: list = None,
        kb_results: list = None,
        section_specific: dict = None,
    ) -> tuple[list[dict], dict]:
        """
        STEP별 컨텍스트 구성.
        반환: (content_blocks, cache_config)

        [구현 참고] 반환값은 전체 messages 리스트가 아닌 system prompt용 content 블록 리스트.
        claude_client.py에서 시스템 프롬프트의 content 배열로 직접 삽입됨.
        반환 형식: ([{"type": "text", "text": ..., "cache_control": {...}}], {"cached": bool})

        TKN-02: RFP 원문 대신 RFP분석서(구조화 요약)를 전달
        TKN-03: 피드백 최근 3회분 + 이전은 요약
        TKN-04: KB 검색 결과 Top-K, 본문 축약
        TKN-05/06: 공통 컨텍스트는 cache_control로 캐시 대상 지정
        """
        budget = STEP_TOKEN_BUDGETS.get(step, 15_000)

        # ── 공통 컨텍스트 (Prompt Caching 대상) ──
        system_prompt = _build_system_prompt(step)
        common_context = _build_common_context(rfp_summary, strategy, plan)

        # ── 피드백 윈도우 (TKN-03) ──
        feedback_text = ""
        if feedback_history:
            recent = feedback_history[-FEEDBACK_WINDOW_SIZE:]
            older = feedback_history[:-FEEDBACK_WINDOW_SIZE]
            if older:
                feedback_text += f"[이전 피드백 요약] {_summarize_feedbacks(older)}\n\n"
            for fb in recent:
                feedback_text += f"[피드백 #{fb.get('version','')}] {fb.get('feedback','')}\n"

        # ── KB 검색 결과 (TKN-04) ──
        kb_text = ""
        if kb_results:
            for item in kb_results[:KB_TOP_K]:
                body = item.get("body_excerpt", item.get("body", ""))[:KB_MAX_BODY_LENGTH]
                kb_text += f"- [{item.get('area','')}] {item.get('title','')}: {body}\n"

        # ── 메시지 구성 ──
        messages = [
            {
                "role": "system",
                "content": system_prompt + "\n\n" + common_context,
                # TKN-06: 공통 컨텍스트에 Prompt Caching 적용
                "cache_control": {"type": "ephemeral"},
            },
        ]

        user_content = ""
        if feedback_text:
            user_content += f"## 피드백 이력\n{feedback_text}\n\n"
        if kb_text:
            user_content += f"## KB 참조 자료 (상위 {KB_TOP_K}건)\n{kb_text}\n\n"
        if section_specific:
            user_content += f"## 현재 작업\n{_format_section_context(section_specific)}\n"

        messages.append({"role": "user", "content": user_content})

        return messages

    @staticmethod
    def build_structured_output_schema(step: str) -> dict:
        """TKN-09: 산출물별 JSON Structured Output 스키마."""
        schemas = {
            "rfp_analyze": {
                "type": "json_schema",
                "json_schema": {
                    "name": "rfp_analysis",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "project_name": {"type": "string"},
                            "client": {"type": "string"},
                            "deadline": {"type": "string"},
                            "case_type": {"type": "string", "enum": ["A", "B"]},
                            "eval_items": {"type": "array"},
                            "tech_price_ratio": {"type": "object"},
                            "hot_buttons": {"type": "array"},
                            "mandatory_reqs": {"type": "array"},
                            "format_template": {"type": "object"},
                            "volume_spec": {"type": "object"},
                            "special_conditions": {"type": "array"},
                        },
                        "required": ["project_name", "client", "case_type", "eval_items", "hot_buttons"],
                    },
                },
            },
            # go_no_go, strategy, plan 등 각 STEP별 스키마 정의...
        }
        return schemas.get(step)
```

### 21-2. Compliance Matrix 규칙/AI 분리 (TKN-07)

```python
# app/services/compliance_tracker.py (v3.0 확장)

class ComplianceTracker:
    """v3.0: 규칙 기반 검증과 AI 판단 검증을 분리."""

    @staticmethod
    async def check_compliance_hybrid(
        sections: list[ProposalSection],
        matrix: list[ComplianceItem],
        rfp_analysis: RFPAnalysis,
    ) -> list[ComplianceItem]:
        """
        TKN-07: 규칙 기반 + AI 판단 하이브리드 검증.
        규칙 검증 가능한 항목은 코드로 자동 처리 (AI 호출 불필요).
        """
        for item in matrix:
            # ── 규칙 기반 자동 검증 (AI 미사용) ──
            if item.source_step == "rfp" and _is_rule_checkable(item):
                item.status = _rule_check(item, sections, rfp_analysis)
            # ── AI 판단 필요 항목만 AI 호출 ──
            else:
                pass  # 배치로 모아서 1회 AI 호출

        # AI 판단 필요 항목 배치 처리
        ai_items = [i for i in matrix if i.status == "미확인"]
        if ai_items:
            all_content = "\n".join(s.content for s in sections)
            results = await claude_generate(
                COMPLIANCE_BATCH_CHECK_PROMPT.format(
                    items=[{"req_id": i.req_id, "content": i.content} for i in ai_items],
                    proposal_content=all_content[:20000],  # 토큰 제한
                ),
            )
            for item, result in zip(ai_items, results):
                item.status = result["status"]
                item.proposal_section = result.get("matching_section", "")

        return matrix

    @staticmethod
    def _is_rule_checkable(item: ComplianceItem) -> bool:
        """규칙 기반 검증 가능 여부 판단."""
        # 분량·서식·필수 요건 포함 여부는 규칙으로 체크 가능
        return any(kw in item.content for kw in ["분량", "페이지", "서식", "용지", "글자"])

    @staticmethod
    def _rule_check(item, sections, rfp) -> str:
        """규칙 기반 자동 검증."""
        total_length = sum(len(s.content) for s in sections)
        if "분량" in item.content or "페이지" in item.content:
            max_pages = rfp.volume_spec.get("max_pages", 999)
            est_pages = total_length / 2000  # 대략 페이지 추정
            return "충족" if est_pages <= max_pages else "미충족"
        return "미확인"
```

### 21-3. 섹션별 출력 토큰 상한 (TKN-08)

```python
# proposal_nodes.py 내 출력 토큰 계산

def calculate_section_max_tokens(rfp_analysis: RFPAnalysis, section_count: int) -> int:
    """
    TKN-08: RFP 분량 제한에서 섹션별 출력 토큰 상한 자동 계산.
    1페이지 ≈ 500 토큰 (한국어 기준)
    """
    max_pages = rfp_analysis.volume_spec.get("max_pages", 50)
    tokens_per_page = 500
    total_budget = max_pages * tokens_per_page
    # 섹션별 균등 배분 (배점 비중으로 가중 가능)
    return total_budget // max(section_count, 1)
```

---

## 22. ★ AI 실행 상태 모니터링 설계 (v3.0)

> **요구사항 §5-1 (AGT-01~11) 대응**. AI Coworker 작업 중 실시간 상태·진행률·Heartbeat를 SSE로 클라이언트에 전달.

### 22-1. AI 상태 매니저

```python
# app/services/ai_status_manager.py
import asyncio
from datetime import datetime, timedelta

HEARTBEAT_TIMEOUT = 60  # 초 — AGT-08

class AiStatusManager:
    """프로젝트별 AI 실행 상태 관리."""

    def __init__(self):
        self._states: dict[str, dict] = {}  # proposal_id → status dict

    def start_task(self, proposal_id: str, step: str, sub_tasks: list[str] = None):
        """AI 작업 시작 등록.

        [구현 참고] 동기 메서드로 구현됨 (async 불필요 — 메모리 딕셔너리만 갱신).
        DB 기록은 별도의 async persist_log() 메서드를 통해 완료/오류 시점에 호출.
        """
        self._states[proposal_id] = {
            "status": "running",         # idle | running | complete | error | paused | no_response | waiting_approval
            "step": step,
            "sub_tasks": {
                t: {"status": "pending", "started_at": None, "completed_at": None, "duration_ms": None}
                for t in (sub_tasks or [step])
            },
            "progress_pct": 0,
            "started_at": datetime.utcnow().isoformat(),
            "last_heartbeat": datetime.utcnow(),
            "error": None,
        }
        # DB 기록은 persist_log() (async)를 별도로 호출

    async def update_sub_task(self, proposal_id: str, sub_task: str, status: str):
        """하위 작업 상태 갱신 + 진행률 자동 계산."""
        state = self._states.get(proposal_id)
        if not state:
            return
        if sub_task in state["sub_tasks"]:
            state["sub_tasks"][sub_task]["status"] = status
            if status == "running":
                state["sub_tasks"][sub_task]["started_at"] = datetime.utcnow().isoformat()
            elif status in ("complete", "error"):
                state["sub_tasks"][sub_task]["completed_at"] = datetime.utcnow().isoformat()

        # 진행률 계산
        total = len(state["sub_tasks"])
        done = sum(1 for t in state["sub_tasks"].values() if t["status"] in ("complete",))
        state["progress_pct"] = int(done / total * 100) if total > 0 else 0

        # Heartbeat 갱신
        state["last_heartbeat"] = datetime.utcnow()

        # SSE 이벤트 발송
        await self._emit_sse(proposal_id, "ai_status", state)

    async def heartbeat(self, proposal_id: str):
        """Heartbeat 수신 — 60초 이상 무응답 시 no_response."""
        state = self._states.get(proposal_id)
        if state:
            state["last_heartbeat"] = datetime.utcnow()

    async def check_heartbeat(self, proposal_id: str) -> bool:
        """Heartbeat 타임아웃 체크 (AGT-08)."""
        state = self._states.get(proposal_id)
        if not state or state["status"] != "running":
            return True
        elapsed = (datetime.utcnow() - state["last_heartbeat"]).total_seconds()
        if elapsed > HEARTBEAT_TIMEOUT:
            state["status"] = "no_response"
            await self._emit_sse(proposal_id, "ai_status", state)
            # 담당자 + 팀장에게 알림 (NOTI-10)
            await notify_ai_no_response(proposal_id, state["step"])
            return False
        return True

    async def abort_task(self, proposal_id: str):
        """사용자 요청에 의한 AI 작업 중단 (AGT-06). 완료된 하위 작업 결과는 보존."""
        state = self._states.get(proposal_id)
        if state:
            state["status"] = "paused"
            await self._emit_sse(proposal_id, "ai_status", state)

    async def get_composite_status(self, proposal_id: str) -> dict:
        """AGT-11: 복합 상태 조회 (프로젝트 상태 + 현재 STEP + AI 상태)."""
        proposal = await get_proposal(proposal_id)
        ai_state = self._states.get(proposal_id, {"status": "idle"})
        return {
            "project_status": proposal["status"],
            "current_step": proposal.get("current_step", ""),
            "ai_status": ai_state["status"],
            "ai_progress_pct": ai_state.get("progress_pct", 0),
            "ai_sub_tasks": ai_state.get("sub_tasks", {}),
        }
```

### 22-2. SSE 이벤트 타입 확장

```python
# app/api/routes_workflow.py (v3.0 확장)

SSE_EVENT_TYPES = {
    "workflow_progress":  "워크플로 단계 전환",
    "artifact_ready":     "산출물 생성 완료",
    "approval_required":  "승인 대기 전환",
    "ai_status":          "★ AI 상태 변경 (running/complete/error/paused/no_response)",
    "ai_progress":        "★ AI 진행률 갱신 (%, 하위 작업별)",
    "ai_heartbeat":       "★ AI Heartbeat (alive 확인)",
    "section_lock":       "★ 섹션 편집 잠금/해제 알림",
    "notification":       "인앱 알림",
}

# 단일 SSE 연결 원칙 (NFR-07): 모든 이벤트를 event 타입으로 구분하여 1개 연결로 멀티플렉싱
async def sse_stream(proposal_id: str):
    """SSE 스트림 — 모든 이벤트 타입을 하나의 연결로 전달."""
    async for event in event_bus.subscribe(proposal_id):
        yield f"event: {event['type']}\ndata: {json.dumps(event['data'])}\n\n"
```

### 22-3. AI 상태 API

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/proposals/{id}/ai-status` | AI 실행 상태 조회 (AGT-11 복합 상태) |
| POST | `/api/proposals/{id}/ai-abort` | AI 작업 중단 (AGT-06) |
| POST | `/api/proposals/{id}/ai-retry` | AI 작업 재시도 (AGT-07) |
| GET | `/api/proposals/{id}/ai-logs` | AI 작업 이력 조회 (AGT-09) |

### 22-4. ★ v3.3: Fallback 전략 (ProposalForge 비교 검토 반영)

> 체계적 장애 대응 전략. 기존 §22 Heartbeat/no_response와 일관되게 설계.

#### 22-4-1. Claude API 장애

| 단계 | 조건 | 동작 |
|------|------|------|
| 1차 | API 오류 (5xx, timeout) | 지수 백오프 재시도 (1s → 2s → 4s, 최대 3회) |
| 2차 | 3회 재시도 실패 | `ai_task_logs.status = 'error'` 기록, SSE `ai_status: error` 발송 |
| 3차 | 사용자 안내 | 인앱 알림 + Teams 알림: "AI 작업 실패 — 수동 진행 또는 재시도 가능" |

> **다중 LLM Fallback (Claude → GPT 등)은 의도적으로 스킵**. 프롬프트 호환성 관리 비용이 크고, 재시도 + 에러 알림으로 충분. (ProposalForge 비교 검토 §4-2)

```python
# app/services/claude_client.py — Fallback 재시도 로직

import asyncio
from anthropic import APIError, APITimeoutError

MAX_RETRIES = 3
BASE_DELAY = 1.0  # seconds

async def call_claude_with_retry(prompt: str, **kwargs) -> dict:
    """지수 백오프 재시도 + 실패 시 에러 기록."""
    for attempt in range(MAX_RETRIES):
        try:
            return await claude_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                messages=[{"role": "user", "content": prompt}],
                **kwargs,
            )
        except (APIError, APITimeoutError) as e:
            if attempt == MAX_RETRIES - 1:
                # 최종 실패: 에러 로깅 + 알림
                await log_ai_error(e, prompt_summary=prompt[:200])
                raise
            delay = BASE_DELAY * (2 ** attempt)
            await asyncio.sleep(delay)
```

#### 22-4-2. 외부 데이터 소스 장애 (MCP/G2B/나라장터)

| 소스 | 장애 시 동작 |
|------|-------------|
| G2B 공고 검색 | 캐시(`g2b_cache`) 조회 → 없으면 `[G2B 접속 불가]` 태그 + 수동 RFP 업로드 안내 |
| 노임단가 DB (`labor_rates`) | 최근 연도 데이터 fallback → 없으면 `[노임단가 미확인]` 플레이스홀더 유지 |
| 시장 낙찰가 (`market_price_data`) | 해당 데이터 스킵 + `[벤치마크 데이터 부족]` 태그 → 수동 입력 안내 |
| KB 검색 (pgvector) | 검색 결과 0건 시 `[참조 데이터 없음]` 태그 → 프롬프트에서 일반 지식 기반 생성 |

#### 22-4-3. 품질 게이트 반복 실패

| 조건 | 동작 |
|------|------|
| `self_review` 2회 연속 80점 미만 | `force_review` → Human 판단 (기존 §8 `MAX_AUTO_IMPROVE=2`와 일관) |
| `retry_research` 후에도 trustworthiness < 12 | `force_review` → Human 판단 (무한 루프 방지) |
| `retry_strategy` 후에도 strategy_score < 15 | `force_review` → Human 판단 (무한 루프 방지) |

> **무한 루프 방지 원칙**: 모든 피드백 루프는 최대 재시도 횟수를 가짐. `_auto_improve_count` (§8)와 동일 메커니즘으로 `_retry_research_count`, `_retry_strategy_count`를 추적 (각 최대 1회).

#### 22-4-4. 노드별 타임아웃

| 노드 유형 | 타임아웃 | 초과 시 |
|-----------|---------|---------|
| 단일 LLM 호출 노드 | 120s | `no_response` → Heartbeat 알림 (기존 §22-1) |
| 병렬 fan-out 노드 | 300s (전체) | 완료된 하위 작업 보존 + 미완료 작업 `error` 처리 |
| 외부 API 호출 | 30s | 해당 데이터 스킵 + 태그 (§22-4-2 참조) |

---

## 23. ★ 사용자 라이프사이클 + 크로스팀 + 컨소시엄 설계 (v3.0)

> **요구사항 §2-7 (ULM), §10-1 (TEAM-09~11), §10-2 (CST) 대응**.

### 23-1. 사용자 관리 API 확장

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| POST | `/api/users` | 사용자 등록 (이름·이메일·소속·역할) | admin |
| POST | `/api/users/bulk` | CSV 일괄 등록 (OB-03) | admin |
| PUT | `/api/users/{id}/team` | 소속 변경 (기존 프로젝트 접근 유지 여부 선택) | admin |
| PUT | `/api/users/{id}/deactivate` | 계정 비활성화 (soft delete) + 후임자 지정 안내 | admin |
| PUT | `/api/users/{id}/reactivate` | 계정 재활성화 | admin |
| POST | `/api/users/{id}/delegate` | 임시 위임 (ULM-07) | admin, lead |
| GET | `/api/users/{id}/projects` | 담당 프로젝트 목록 (퇴사·이동 시 후임 지정용) | admin |

### 23-2. 자기결재 방지 (§2-4)

```python
# app/services/approval_chain.py (v3.0 확장)

async def build_approval_chain(proposal_id: str, step: str) -> list[dict]:
    """
    결재선 구성 — 자기결재 방지 원칙 적용.
    프로젝트 생성자가 팀장인 경우, 차상위 결재자(본부장)로 상향.
    """
    proposal = await get_proposal(proposal_id)
    budget = proposal.get("budget_amount", 0)
    team_id = proposal["team_id"]
    created_by = proposal["created_by"]

    lead = await get_team_lead(team_id)
    chain = []

    # 자기결재 방지: 생성자 == 팀장이면 팀장 단계 건너뛰고 본부장부터
    if lead["id"] == created_by:
        director = await get_division_director(proposal["division_id"])
        chain.append({"role": "director", "user_id": director["id"], "user_name": director["name"]})
        if budget >= 500_000_000:
            executive = await get_executive()
            chain.append({"role": "executive", "user_id": executive["id"], "user_name": executive["name"]})
    else:
        chain.append({"role": "lead", "user_id": lead["id"], "user_name": lead["name"]})
        if budget >= 300_000_000:
            director = await get_division_director(proposal["division_id"])
            chain.append({"role": "director", "user_id": director["id"], "user_name": director["name"]})
        if budget >= 500_000_000:
            executive = await get_executive()
            chain.append({"role": "executive", "user_id": executive["id"], "user_name": executive["name"]})

    # 임시 위임 체크
    chain = await _apply_delegation(chain)
    return chain
```

### 23-3. 크로스팀 프로젝트

```python
# 프로젝트 생성 시 참여 팀 지정
# POST /api/proposals
{
    "name": "AI 플랫폼 구축",
    "mode": "full",
    "participating_teams": ["team-uuid-2", "team-uuid-3"],  # 참여 팀
    # ... 기타
}

# 크로스팀 대시보드 가시성 (TEAM-11):
# 참여 팀장의 대시보드 쿼리에 project_teams 조인 추가
# SELECT * FROM proposals p
# JOIN project_teams pt ON p.id = pt.proposal_id
# WHERE pt.team_id = {team_id}
```

### 23-4. 컨소시엄 관리

```python
# POST /api/proposals/{id}/consortium
{
    "company_name": "○○기술",
    "role": "partner",
    "scope": "데이터 분석 모듈 개발",
    "personnel_count": 3,
    "share_amount": 120000000,
    "contact_name": "김담당",
    "contact_email": "kim@example.com"
}
# CST-06: 참여사는 시스템 계정 없음 — 담당 섹션은 DOCX 업로드로 수집
```

---

## 24. ★ 동시 편집 충돌 방지 설계 (v3.0)

> **요구사항 GATE-17/18 대응**. 동일 섹션을 다른 사용자가 편집 중일 때 잠금 표시 + 읽기 전용 전환.

### 24-1. 섹션 잠금 서비스

```python
# app/services/section_lock.py

LOCK_DURATION_MINUTES = 5  # 자동 해제 타임아웃

class SectionLockService:
    """섹션별 편집 잠금 관리."""

    async def acquire_lock(self, proposal_id: str, section_id: str, user_id: str) -> dict:
        """섹션 잠금 획득. 이미 다른 사용자가 잠금 중이면 실패."""
        # 만료된 잠금 정리
        await self._cleanup_expired()

        existing = await db.fetchone(
            "SELECT * FROM section_locks WHERE proposal_id=$1 AND section_id=$2",
            proposal_id, section_id
        )
        if existing and existing["locked_by"] != user_id:
            locker = await get_user(existing["locked_by"])
            return {
                "acquired": False,
                "locked_by": locker["name"],
                "locked_at": existing["locked_at"],
                "expires_at": existing["expires_at"],
            }

        expires_at = datetime.utcnow() + timedelta(minutes=LOCK_DURATION_MINUTES)
        await db.execute("""
            INSERT INTO section_locks (proposal_id, section_id, locked_by, expires_at)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (proposal_id, section_id) DO UPDATE
            SET locked_by=$3, locked_at=now(), expires_at=$4
        """, proposal_id, section_id, user_id, expires_at)

        # SSE로 잠금 알림 발송
        await emit_sse(proposal_id, "section_lock", {
            "section_id": section_id, "locked_by": user_id, "action": "locked"
        })
        return {"acquired": True, "expires_at": expires_at.isoformat()}

    async def release_lock(self, proposal_id: str, section_id: str, user_id: str):
        """잠금 해제 (수동)."""
        await db.execute(
            "DELETE FROM section_locks WHERE proposal_id=$1 AND section_id=$2 AND locked_by=$3",
            proposal_id, section_id, user_id
        )
        await emit_sse(proposal_id, "section_lock", {
            "section_id": section_id, "action": "unlocked"
        })
```

### 24-2. 섹션 잠금 API

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/proposals/{id}/sections/{section_id}/lock` | 섹션 편집 잠금 획득 |
| DELETE | `/api/proposals/{id}/sections/{section_id}/lock` | 섹션 편집 잠금 해제 |
| GET | `/api/proposals/{id}/sections/locks` | 현재 잠금 목록 조회 |

---

## 25. ★ 입력 검증 및 파일 보안 설계 (v3.0)

> **요구사항 §12-5 (VAL-01~07), NFR-11 대응**.

### 25-1. 입력 검증 미들웨어

```python
# app/services/input_validator.py
import magic  # python-magic (MIME 타입 검증)

# VAL-01: RFP 파일 허용 확장자 + 크기
RFP_ALLOWED_EXTENSIONS = {".pdf", ".hwpx"}
RFP_MAX_SIZE_MB = 50

# VAL-02: 첨부 파일 허용 확장자
ATTACHMENT_ALLOWED_EXTENSIONS = {".pdf", ".hwpx", ".docx", ".pptx", ".xlsx", ".csv"}

# VAL-03: 단일 필드 텍스트
TEXT_SHORT_MAX_LENGTH = 200

# VAL-04: 장문 텍스트
TEXT_LONG_MAX_LENGTH = 10_000

# VAL-06: 숫자 범위
BUDGET_MIN = 1
BUDGET_MAX = 99_900_000_000  # 999억


async def validate_file_upload(file, allowed_extensions: set, max_size_mb: int = 50):
    """파일 업로드 검증 — 확장자 + 크기 + MIME 타입."""
    # 확장자 체크
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_extensions:
        raise ValidationError(f"허용되지 않는 파일 형식: {ext}. 허용: {allowed_extensions}")

    # 크기 체크
    content = await file.read()
    if len(content) > max_size_mb * 1024 * 1024:
        raise ValidationError(f"파일 크기 초과: {len(content)} bytes (최대 {max_size_mb}MB)")

    # MIME 타입 체크
    mime = magic.from_buffer(content, mime=True)
    expected_mimes = {
        ".pdf": "application/pdf",
        ".hwpx": "application/hwp+zip",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }
    if ext in expected_mimes and mime != expected_mimes[ext]:
        raise ValidationError(f"MIME 타입 불일치: {mime} (기대: {expected_mimes[ext]})")

    await file.seek(0)  # 파일 포인터 리셋
    return content


def sanitize_text(text: str, max_length: int = TEXT_LONG_MAX_LENGTH) -> str:
    """텍스트 입력 sanitization — XSS/HTML 태그 제거."""
    import bleach
    cleaned = bleach.clean(text, tags=[], strip=True)
    return cleaned[:max_length]
```

### 25-2. 주기적 자동 모니터링 (SRC-11)

```python
# app/services/scheduled_monitor.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

async def daily_g2b_monitor():
    """
    SRC-11: 일 1회 G2B 신규 공고 자동 검색.
    등록된 관심 분야·키워드 기반으로 검색 → 적합 공고 발견 시 Teams 알림.
    """
    # 모든 활성 팀의 관심 키워드 수집
    teams = await get_all_active_teams()
    for team in teams:
        keywords = team.get("monitor_keywords", [])
        if not keywords:
            continue

        for kw in keywords:
            results = await g2b_client.search_bids(keywords=kw)
            # 이미 알림한 공고 제외
            new_results = await filter_new_bids(results, team["id"])
            if new_results:
                lead = await get_team_lead(team["id"])
                await send_teams_notification(
                    team_id=team["id"],
                    title=f"🔔 신규 공고 발견 ({len(new_results)}건)",
                    body="\n".join(f"• {r['project_name']} ({r['budget']})" for r in new_results[:5]),
                    link=f"{APP_URL}/projects?search={kw}",
                )

# 매일 09:00 실행
scheduler.add_job(daily_g2b_monitor, "cron", hour=9, minute=0)
```

---

## 26. ★ 회사 템플릿 관리 설계 (v3.0)

> **요구사항 ART-07~10 대응**. DOCX·PPTX 회사 표준 템플릿을 등록·관리하고 산출물 출력 시 자동 적용.

### 26-1. 템플릿 관리 API

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET | `/api/templates` | 템플릿 목록 조회 | all |
| POST | `/api/templates` | 템플릿 업로드 (DOCX/PPTX) | admin |
| PUT | `/api/templates/{id}` | 템플릿 수정 (신규 버전 생성) | admin |
| DELETE | `/api/templates/{id}` | 템플릿 비활성화 | admin |

### 26-2. DOCX/PPTX 빌더 템플릿 적용

```python
# app/services/docx_builder.py (v3.0 확장)

async def build_docx(sections, rfp, proposal_id=None) -> bytes:
    """제안서 DOCX 생성 — 회사 템플릿 자동 적용 (ART-08)."""
    # 활성 DOCX 템플릿 조회
    template = await get_active_template(org_id, type="docx")

    if template:
        # 템플릿 기반 생성: 표지·머리글·바닥글·스타일 적용
        doc = Document(template["file_path"])
        _apply_template_styles(doc, sections)
    else:
        # 기본 스타일로 생성
        doc = Document()

    if rfp.case_type == "B":
        _build_from_template(doc, sections, rfp.format_template["structure"])
    else:
        _build_freeform(doc, sections)

    return _save_to_bytes(doc)
```

---
