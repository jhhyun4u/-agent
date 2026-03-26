"""
이메일 발송 서비스 (Microsoft Graph API)

Azure AD 앱의 Mail.Send 애플리케이션 권한을 사용하여
OAuth2 client_credentials 토큰으로 이메일 발송.
"""

import asyncio
import html as html_mod
import logging
import time

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# ── 토큰 캐시 (asyncio.Lock으로 동시 갱신 방지) ──

_token_cache: dict = {"access_token": "", "expires_at": 0.0}
_token_lock = asyncio.Lock()


async def _get_graph_token() -> str:
    """OAuth2 client_credentials로 Graph API 토큰 발급 (인메모리 캐싱)."""
    async with _token_lock:
        now = time.time()
        if _token_cache["access_token"] and _token_cache["expires_at"] > now + 60:
            return str(_token_cache["access_token"])

        url = (
            f"https://login.microsoftonline.com/"
            f"{settings.azure_ad_tenant_id}/oauth2/v2.0/token"
        )
        data = {
            "client_id": settings.azure_ad_client_id,
            "client_secret": settings.azure_ad_client_secret,
            "scope": settings.email_graph_scope,
            "grant_type": "client_credentials",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, data=data)
            resp.raise_for_status()
            body = resp.json()

        _token_cache["access_token"] = body["access_token"]
        _token_cache["expires_at"] = now + body.get("expires_in", 3600)
        return str(body["access_token"])


# ── 이메일 발송 ──

async def send_email(
    to: str, subject: str, html_body: str, *, _client: httpx.AsyncClient | None = None,
) -> bool:
    """단건 이메일 발송 (Graph API). 성공 시 True."""
    if not settings.email_enabled or not settings.email_sender:
        return False

    try:
        token = await _get_graph_token()
        url = (
            f"https://graph.microsoft.com/v1.0/users/"
            f"{settings.email_sender}/sendMail"
        )
        payload = {
            "message": {
                "subject": subject,
                "body": {"contentType": "HTML", "content": html_body},
                "toRecipients": [{"emailAddress": {"address": to}}],
            },
            "saveToSentItems": False,
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        if _client:
            resp = await _client.post(url, json=payload, headers=headers)
        else:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(url, json=payload, headers=headers)

        if resp.status_code == 202:
            logger.debug(f"이메일 발송 성공: {to}")
            return True
        logger.warning(f"이메일 발송 실패: {resp.status_code} {resp.text[:200]}")
        return False
    except Exception as e:
        logger.warning(f"이메일 발송 오류 ({to}): {e}")
        return False


async def send_email_batch(recipients: list[str], subject: str, html_body: str) -> int:
    """다건 이메일 발송 (httpx 클라이언트 재사용). 성공 건수 반환."""
    sent = 0
    async with httpx.AsyncClient(timeout=15) as client:
        for to in recipients:
            if await send_email(to, subject, html_body, _client=client):
                sent += 1
    return sent


# ── HTML 템플릿 ──

def _safe(text: str) -> str:
    """HTML 이스케이프."""
    return html_mod.escape(str(text))


def _safe_link(link: str) -> str:
    """링크 URL 검증 + 이스케이프. http(s)만 허용."""
    link = link.strip()
    if not link.startswith(("http://", "https://")):
        return ""
    return html_mod.escape(link)


def build_email_html(title: str, body: str, link: str = "") -> str:
    """공통 이메일 HTML 템플릿. title은 자동 이스케이프. body는 신뢰된 HTML 허용 (호출부 책임)."""
    safe_title = _safe(title)
    safe_body = body  # body는 HTML 포함 가능 (bold 등) — 호출부에서 관리
    safe_link = _safe_link(link)

    link_html = ""
    if safe_link:
        link_html = (
            f'<div style="margin-top:16px;">'
            f'<a href="{safe_link}" style="display:inline-block;background:#C9A84C;'
            f"color:#0D1B2A;padding:10px 24px;border-radius:6px;font-weight:700;"
            f'font-size:13px;text-decoration:none;">바로 가기</a>'
            f"</div>"
        )
    return (
        f'<div style="max-width:560px;margin:0 auto;'
        f"font-family:'맑은 고딕','Malgun Gothic',sans-serif;"
        f'background:#f5f5f5;padding:24px;">'
        # 헤더
        f'<div style="background:#0D1B2A;padding:16px 20px;'
        f'border-radius:8px 8px 0 0;">'
        f'<span style="color:#C9A84C;font-weight:700;font-size:14px;">TNP</span>'
        f'<span style="color:#fff;font-size:14px;margin-left:8px;">'
        f"Proposal Coworker</span>"
        f"</div>"
        # 본문
        f'<div style="background:#fff;padding:24px 20px;'
        f'border:1px solid #e0e0e0;border-top:none;">'
        f'<h2 style="font-size:16px;color:#1a2332;margin:0 0 12px;">{safe_title}</h2>'
        f'<div style="font-size:14px;color:#4a5568;line-height:1.7;">{safe_body}</div>'
        f"{link_html}"
        f"</div>"
        # 푸터
        f'<div style="text-align:center;padding:12px;font-size:11px;color:#999;">'
        f"Proposal Coworker &middot; TENOPA 사내 플랫폼"
        f"</div>"
        f"</div>"
    )
