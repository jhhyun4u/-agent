# 갭 분석 HIGH 항목 보완 (§27)

> **소속**: proposal-agent-v1 설계 문서 v3.5
> **관련 파일**: [15b-gap-medium-archive.md](15b-gap-medium-archive.md)
> **원본 섹션**: §27

---

## 27. ★ 갭 분석 HIGH 항목 보완 설계 (v3.0)

> **갭 분석 결과 HIGH 심각도 7건 중 AUTH-06은 §17-1에 반영 완료. 나머지 6건을 아래에서 설계.**

### 27-1. TRS-09: AI 생성 vs Human 편집 구분 기록

> **목적**: 최종 산출물에서 AI가 작성한 부분과 Human이 직접 수정한 부분을 구분 기록하여 감사 추적 및 품질 관리에 활용.

#### DB 스키마 확장

```sql
-- artifacts 테이블에 편집 주체 추적 컬럼 추가
ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS edit_source TEXT DEFAULT 'ai';
-- 유효값: 'ai' (AI 생성 원본), 'human' (사용자 직접 편집), 'ai_revised' (피드백 반영 AI 재생성)

-- 편집 이력 테이블 (섹션별 변경 추적)
CREATE TABLE artifact_edit_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artifact_id     UUID REFERENCES artifacts(id) NOT NULL,
    proposal_id     UUID REFERENCES proposals(id) NOT NULL,
    section_id      TEXT NOT NULL,
    edit_source     TEXT NOT NULL,           -- 'ai' | 'human' | 'ai_revised'
    editor_id       UUID REFERENCES users(id),  -- Human 편집 시 사용자 ID
    diff_summary    TEXT,                    -- 변경 요약 (추가/삭제/수정 줄 수)
    previous_hash   TEXT,                    -- 이전 버전 해시 (변경 감지용)
    current_hash    TEXT,                    -- 현재 버전 해시
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_artifact_edit_history ON artifact_edit_history(proposal_id, section_id);
```

#### API 확장

```python
# app/api/routes_artifact.py 확장

@router.put("/api/proposals/{id}/artifacts/{step}/sections/{section_id}")
async def update_section_content(
    id: str, step: str, section_id: str,
    body: SectionEditRequest,
    user: dict = Depends(get_current_user),
):
    """
    TRS-09: Human이 직접 섹션 내용을 편집할 때 호출.
    edit_source='human'으로 기록하여 AI 생성분과 구분.
    """
    existing = await get_artifact_section(id, step, section_id)
    previous_hash = hashlib.sha256(existing["content"].encode()).hexdigest()
    current_hash = hashlib.sha256(body.content.encode()).hexdigest()

    if previous_hash == current_hash:
        return {"message": "변경 없음"}

    # 편집 이력 기록
    await insert_edit_history(
        artifact_id=existing["artifact_id"],
        proposal_id=id,
        section_id=section_id,
        edit_source="human",
        editor_id=user["id"],
        diff_summary=_compute_diff_summary(existing["content"], body.content),
        previous_hash=previous_hash,
        current_hash=current_hash,
    )

    # 산출물 업데이트
    await update_artifact_content(id, step, section_id, body.content, edit_source="human")
    return {"message": "편집 저장 완료", "edit_source": "human"}
```

> **프론트엔드 연동**: ArtifactViewer에서 각 섹션 옆에 편집 주체 아이콘 표시 (🤖 AI / ✏️ Human / 🔄 AI 재작성).

### 27-2. PSM-05: expired 자동 전환

> **목적**: 제출 기한(deadline)이 지난 프로젝트를 자동으로 `expired` 상태로 전환.

```python
# app/services/scheduled_monitor.py 에 추가

async def check_expired_projects():
    """
    PSM-05: 제출 기한 초과 프로젝트 자동 expired 전환.
    daily_g2b_monitor와 같은 스케줄러에서 실행.

    대상: status IN ('draft','searching','analyzing','strategizing') AND deadline < now()
    제외: 이미 submitted/presented/won/lost/no_go/abandoned/retrospect 상태
    """
    from datetime import datetime, timezone

    expirable_statuses = ('draft', 'searching', 'analyzing', 'strategizing')
    now = datetime.now(timezone.utc)

    expired_projects = await supabase.table("proposals") \
        .select("id, project_name, team_id, status, deadline") \
        .in_("status", expirable_statuses) \
        .lt("deadline", now.isoformat()) \
        .execute()

    for project in expired_projects.data:
        # 상태 전환
        await supabase.table("proposals") \
            .update({
                "status": "expired",
                "previous_status": project["status"],
            }) \
            .eq("id", project["id"]) \
            .execute()

        # 감사 로그
        await insert_audit_log(
            action="auto_expire",
            resource_type="proposal",
            resource_id=project["id"],
            detail={"previous_status": project["status"], "deadline": project["deadline"]},
        )

        # 팀장 알림
        lead = await get_team_lead(project["team_id"])
        if lead:
            await create_notification(
                user_id=lead["id"],
                proposal_id=project["id"],
                type="project_expired",
                title=f"⏰ 프로젝트 기한 만료: {project['project_name']}",
                body=f"제출 기한({project['deadline']})이 지나 자동으로 만료 처리되었습니다. 회고 작성을 권장합니다.",
            )

# 매일 00:30 실행 (daily_g2b_monitor 09:00과 분리)
scheduler.add_job(check_expired_projects, "cron", hour=0, minute=30)
```

### 27-3. PSM-16: Q&A 기록 검색 가능 저장

> **목적**: 발표 후 Q&A 기록을 콘텐츠 라이브러리와 교훈 아카이브에 검색 가능하게 저장.

```python
# app/services/feedback_loop.py 에 추가

async def save_qa_to_kb(proposal_id: str, qa_records: list[dict]):
    """
    PSM-16: Q&A 기록을 KB에 검색 가능하게 저장.
    presentation_qa 테이블에 저장 후, 콘텐츠 라이브러리에도 등록.

    qa_records 형식: [{ "question": str, "answer": str, "category": str }]
    """
    proposal = await get_proposal(proposal_id)

    for qa in qa_records:
        # 1) presentation_qa 테이블 저장 (기존)
        qa_id = await insert_presentation_qa(proposal_id, qa)

        # 2) 콘텐츠 라이브러리에 qa_record 유형으로 등록
        content_body = f"Q: {qa['question']}\nA: {qa['answer']}"
        content_id = await insert_content_library(
            org_id=proposal["org_id"],
            type="qa_record",
            title=f"[Q&A] {qa['question'][:50]}",
            body=content_body,
            source_project_id=proposal_id,
            industry=proposal.get("industry"),
            tags=[qa.get("category", "general"), "qa", "presentation"],
        )

        # 3) 임베딩 생성 → 시맨틱 검색 가능
        embedding = await embedding_service.generate(content_body)
        await update_content_embedding(content_id, embedding)

    # 4) 교훈 아카이브에 Q&A 요약 기록
    if qa_records:
        qa_summary = "\n".join(
            f"• Q: {qa['question'][:80]} → A: {qa['answer'][:80]}"
            for qa in qa_records
        )
        await append_lesson_learned(
            proposal_id=proposal_id,
            category="qa_insight",
            detail=f"발표 Q&A ({len(qa_records)}건):\n{qa_summary}",
        )
```

#### presentation_qa 테이블 확장

```sql
-- 기존 presentation_qa에 임베딩 + 콘텐츠 연결 추가
ALTER TABLE presentation_qa ADD COLUMN IF NOT EXISTS embedding vector(1536);
ALTER TABLE presentation_qa ADD COLUMN IF NOT EXISTS content_library_id UUID REFERENCES content_library(id);

CREATE INDEX idx_presentation_qa_embedding ON presentation_qa USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10);
```

### 27-4. POST-06: 발표 없이 서류 심사 시 presented 건너뛰기

> **목적**: 서류 심사만으로 결과가 결정되는 공고의 경우 submitted → won/lost 직접 전환.

#### 프로젝트 상태 머신 확장

```sql
-- proposals 테이블에 심사 방식 플래그 추가
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS eval_method TEXT DEFAULT 'presentation';
-- 유효값: 'presentation' (발표 심사), 'document_only' (서류 심사만)
```

#### 상태 전환 로직

```python
# app/api/routes_proposal.py 확장

@router.post("/api/proposals/{id}/result")
async def register_result(
    id: str,
    body: ResultRequest,  # { result: "won"|"lost"|"canceled", eval_method?: str, ... }
    user: dict = Depends(require_role("lead")),
):
    """
    POST-06: 제안 결과 등록.
    - eval_method='document_only': submitted → won/lost (presented 건너뛰기)
    - eval_method='presentation': submitted → presented → won/lost (기존 흐름)
    """
    proposal = await get_proposal(id)

    if body.eval_method == "document_only":
        # 서류 심사: submitted → 바로 won/lost
        if proposal["status"] not in ("submitted",):
            raise HTTPException(400, "서류 심사 결과는 submitted 상태에서만 등록 가능")
        new_status = body.result  # "won" | "lost" | "canceled"
    else:
        # 발표 심사: presented 상태에서 won/lost
        if proposal["status"] not in ("presented",):
            raise HTTPException(400, "발표 심사 결과는 presented 상태에서만 등록 가능")
        new_status = body.result

    await update_proposal_status(id, new_status)
    await insert_audit_log(
        action="result_registered",
        resource_type="proposal",
        resource_id=id,
        detail={"result": body.result, "eval_method": body.eval_method or "presentation"},
        user_id=user["id"],
    )

    # 수주/패찰 시 KB 환류 트리거
    if new_status in ("won", "lost"):
        await trigger_feedback_loop(id, new_status)

    return {"status": new_status}
```

#### 상태 머신 제약 갱신

```sql
-- submitted → won/lost 직접 전환 허용 (서류 심사 경로)
-- 기존: submitted → presented → won/lost
-- 추가: submitted → won/lost (eval_method='document_only')
COMMENT ON COLUMN proposals.eval_method IS
  'presentation: 발표 심사 (submitted→presented→won/lost), document_only: 서류 심사 (submitted→won/lost 직접)';
```

### 27-5. OPS-02: /health 헬스체크 엔드포인트

```python
# app/api/routes_health.py

from fastapi import APIRouter
from app.models.db import supabase
from app.services.g2b_client import g2b_client
from app.config import CLAUDE_API_KEY
import httpx

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    OPS-02: 애플리케이션 헬스체크.
    DB·외부 서비스 연결 상태를 포함하여 200/503 반환.
    """
    checks = {}

    # 1. Supabase PostgreSQL 연결
    try:
        result = supabase.table("users").select("id").limit(1).execute()
        checks["database"] = {"status": "ok"}
    except Exception as e:
        checks["database"] = {"status": "error", "detail": str(e)[:100]}

    # 2. Supabase Storage 연결
    try:
        supabase.storage.list_buckets()
        checks["storage"] = {"status": "ok"}
    except Exception as e:
        checks["storage"] = {"status": "error", "detail": str(e)[:100]}

    # 3. Claude API 연결 (간단한 ping)
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.anthropic.com/v1/models",
                headers={"x-api-key": CLAUDE_API_KEY, "anthropic-version": "2023-06-01"},
                timeout=5,
            )
            checks["claude_api"] = {"status": "ok" if resp.status_code == 200 else "degraded"}
    except Exception as e:
        checks["claude_api"] = {"status": "error", "detail": str(e)[:100]}

    # 4. G2B API 연결
    try:
        await g2b_client.ping()
        checks["g2b_api"] = {"status": "ok"}
    except Exception:
        checks["g2b_api"] = {"status": "degraded", "detail": "G2B API 응답 없음 (비필수)"}

    # 종합 판정
    critical_ok = all(
        checks[k]["status"] == "ok"
        for k in ("database", "storage")  # 필수 서비스
    )

    return {
        "status": "healthy" if critical_ok else "unhealthy",
        "checks": checks,
        "version": "v3.0",
    }
    # 응답 코드: 200 (healthy) / 503 (unhealthy)
```

### 27-6. OPS-03: 구조화 로깅 설계

```python
# app/config.py 에 추가

import structlog

def configure_logging():
    """
    OPS-03: 구조화 로깅 (JSON 형식).
    모든 로그에 request_id, user_id, proposal_id 등 컨텍스트 자동 포함.
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,      # 컨텍스트 변수 자동 병합
            structlog.processors.TimeStamper(fmt="iso"),   # ISO 타임스탬프
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),           # JSON 출력
        ],
        wrapper_class=structlog.make_filtering_bound_logger(10),  # DEBUG 이상
        logger_factory=structlog.PrintLoggerFactory(),
    )

# ── 로깅 미들웨어 ──
# app/main.py

from starlette.middleware.base import BaseHTTPMiddleware
import structlog
import uuid

logger = structlog.get_logger()

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """모든 요청에 request_id를 바인딩하고 요청/응답을 로깅."""

    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())[:8]
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        # 사용자 컨텍스트 (인증된 경우)
        user = getattr(request.state, "user", None)
        if user:
            structlog.contextvars.bind_contextvars(
                user_id=user.get("id"),
                team_id=user.get("team_id"),
            )

        logger.info("request_start")
        response = await call_next(request)
        logger.info("request_end", status_code=response.status_code)
        return response


# ── 로깅 표준 패턴 (각 서비스에서 사용) ──
# 예: app/services/claude_client.py
#
# logger = structlog.get_logger()
#
# async def claude_generate(prompt, ...):
#     logger.info("claude_api_call", step=step, input_tokens=len(prompt))
#     response = await client.messages.create(...)
#     logger.info("claude_api_response",
#         step=step,
#         input_tokens=response.usage.input_tokens,
#         output_tokens=response.usage.output_tokens,
#         cached_tokens=response.usage.cache_read_input_tokens,
#     )
#     return response
```

> **로깅 레벨 가이드**:
> | 레벨 | 용도 | 예시 |
> |------|------|------|
> | INFO | 정상 흐름 | API 요청/응답, AI 호출, 상태 전환 |
> | WARNING | 비정상이지만 계속 가능 | Heartbeat 지연, API 재시도, 세션 만료 |
> | ERROR | 실패 | Claude API 오류, DB 연결 실패, 파일 파싱 실패 |
> | DEBUG | 개발용 상세 | 프롬프트 내용, KB 검색 결과, 토큰 카운트 |

---
