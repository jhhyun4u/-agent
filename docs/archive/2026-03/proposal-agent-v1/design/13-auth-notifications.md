# 인증 + Teams 알림

> **소속**: proposal-agent-v1 설계 문서 v3.5
> **관련 파일**: [08-api-endpoints.md](08-api-endpoints.md), [01-architecture.md](01-architecture.md)
> **원본 섹션**: §17, §18

---

## 17. ★ 인증 흐름 (v2.0)

```
┌─────────┐     ┌──────────┐     ┌──────────────┐     ┌───────────┐
│ 사용자   │────→│ Next.js  │────→│ Supabase Auth│────→│ Azure AD  │
│ 브라우저 │     │ /login   │     │ (OAuth)      │     │ (Entra ID)│
└─────────┘     └──────────┘     └──────────────┘     └───────────┘
                                        │                    │
                                        │  ← OAuth callback  │
                                        │  (id_token + profile)
                                        ▼
                                 ┌──────────────┐
                                 │ Supabase      │
                                 │ - JWT 발급    │
                                 │ - users 조회  │
                                 │ - 역할 매핑   │
                                 └──────┬───────┘
                                        │ JWT
                                        ▼
                                 ┌──────────────┐
                                 │ FastAPI       │
                                 │ - JWT 검증    │
                                 │ - RLS 적용    │
                                 └──────────────┘
```

### 17-1. 인증 서비스

```python
# app/services/auth_service.py

from supabase import create_client
from fastapi import Depends, HTTPException, Request
from app.config import SUPABASE_URL, SUPABASE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

async def get_current_user(request: Request) -> dict:
    """JWT에서 현재 사용자 정보 추출 + DB 역할 조회."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(401, "인증 필요")

    # Supabase JWT 검증
    user = supabase.auth.get_user(token)
    if not user:
        raise HTTPException(401, "유효하지 않은 토큰")

    # DB에서 역할·소속 조회
    profile = supabase.table("users").select("*").eq("id", user.user.id).single().execute()
    return profile.data


# ── ★ v3.0: AUTH-06 세션 만료와 AI 작업 분리 ──

async def get_current_user_or_none(request: Request) -> dict | None:
    """세션 만료 여부만 확인 (AI 작업 백그라운드 실행에 사용)."""
    try:
        return await get_current_user(request)
    except HTTPException:
        return None  # 세션 만료 — AI 작업은 계속 진행


# ── AUTH-06 아키텍처 원칙 ──
# 1. AI 작업은 세션과 독립적으로 실행:
#    - LangGraph StateGraph 실행은 서버 측 asyncio task로 동작
#    - ai_task_logs에 작업 결과를 영속화 (세션 무관)
#    - 사용자 세션이 만료되어도 진행 중인 AI 작업은 중단하지 않음
#
# 2. 재로그인 시 미확인 결과 자동 표시:
#    - 로그인 시 ai_task_logs에서 status='complete' AND viewed=false 조회
#    - SSE 연결 재수립 시 미확인 이벤트 일괄 전송
#    - 프론트엔드에서 "AI 작업 완료 알림" 배지 표시
#
# 3. AI 작업 결과 영속화 흐름:
#    AI 작업 완료 → ai_task_logs.status='complete' + result JSONB 저장
#    → notification 생성 (NOTI-11)
#    → 사용자 재접속 시 GET /api/proposals/{id}/ai-logs?viewed=false 로 조회


def require_role(*roles: str):
    """역할 기반 접근 제어 데코레이터."""
    async def check(user=Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(403, f"권한 부족: {user['role']} not in {roles}")
        return user
    return check
```

### 17-2. 결재선 서비스

```python
# app/services/approval_chain.py

async def build_approval_chain(proposal_id: str, step: str) -> list[dict]:
    """
    프로젝트 예산 기준으로 결재선 구성.
    - 3억 미만: [팀장]
    - 3~5억: [팀장, 본부장]
    - 5억 이상: [팀장, 본부장, 경영진]
    """
    proposal = await get_proposal(proposal_id)
    budget = proposal.get("budget_amount", 0)
    team_id = proposal["team_id"]
    division_id = proposal["division_id"]

    chain = []
    # 팀장 (항상 필요)
    lead = await get_team_lead(team_id)
    chain.append({"role": "lead", "user_id": lead["id"], "user_name": lead["name"]})

    if budget >= 300_000_000:
        director = await get_division_director(division_id)
        chain.append({"role": "director", "user_id": director["id"], "user_name": director["name"]})

    if budget >= 500_000_000:
        executive = await get_executive()
        chain.append({"role": "executive", "user_id": executive["id"], "user_name": executive["name"]})

    return chain


async def check_can_approve(user: dict, proposal_id: str, step: str) -> bool:
    """현재 사용자가 이 단계를 승인할 권한이 있는지 확인."""
    chain = await build_approval_chain(proposal_id, step)
    # 결재선에 포함된 역할만 승인 가능
    user_role = user["role"]
    return any(c["role"] == user_role and c["user_id"] == user["id"] for c in chain)
```

---

## 18. ★ Teams 알림 연동 (v2.0)

```python
# app/services/notification_service.py

import httpx
from app.config import TEAMS_WEBHOOK_DEFAULT

async def send_teams_notification(
    team_id: str,
    title: str,
    body: str,
    link: str = "",
):
    """Teams Incoming Webhook으로 알림 발송."""
    # 팀별 Webhook URL 조회 (teams 테이블)
    team = await get_team(team_id)
    webhook_url = team.get("teams_webhook_url") or TEAMS_WEBHOOK_DEFAULT

    if not webhook_url:
        return  # Webhook 미설정 시 생략

    card = {
        "type": "message",
        "attachments": [{
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": [
                    {"type": "TextBlock", "text": title, "weight": "bolder", "size": "medium"},
                    {"type": "TextBlock", "text": body, "wrap": True},
                ],
                "actions": [
                    {"type": "Action.OpenUrl", "title": "바로 가기", "url": link}
                ] if link else [],
            },
        }],
    }

    async with httpx.AsyncClient() as client:
        await client.post(webhook_url, json=card)


async def notify_approval_request(proposal_id: str, step: str, approver_id: str):
    """승인 요청 알림 (Teams + 인앱)."""
    proposal = await get_proposal(proposal_id)
    approver = await get_user(approver_id)

    # 인앱 알림 생성
    await create_notification(
        user_id=approver_id,
        proposal_id=proposal_id,
        type="approval_request",
        title=f"[승인 요청] {proposal['name']}",
        body=f"{step} 단계 승인이 필요합니다.",
        link=f"/projects/{proposal_id}/review/{step}",
    )

    # Teams 알림
    await send_teams_notification(
        team_id=proposal["team_id"],
        title=f"🔔 승인 요청: {proposal['name']}",
        body=f"{approver['name']}님, {step} 단계 승인을 요청드립니다.",
        link=f"{APP_URL}/projects/{proposal_id}/review/{step}",
    )


async def notify_deadline_alert(proposal_id: str, days_left: int):
    """마감 임박 알림 (D-7, D-3, D-1)."""
    proposal = await get_proposal(proposal_id)
    participants = await get_participants(proposal_id)

    for user in participants:
        await create_notification(
            user_id=user["user_id"],
            proposal_id=proposal_id,
            type="deadline",
            title=f"⏰ 마감 D-{days_left}: {proposal['name']}",
            body=f"제출 마감까지 {days_left}일 남았습니다.",
            link=f"/projects/{proposal_id}",
        )

    await send_teams_notification(
        team_id=proposal["team_id"],
        title=f"⏰ 마감 D-{days_left}: {proposal['name']}",
        body=f"제출 마감까지 {days_left}일 남았습니다. 현재 단계: {proposal.get('status', '')}",
        link=f"{APP_URL}/projects/{proposal_id}",
    )
```

---
