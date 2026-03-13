"""Phase 0: 앱 기동 + 헬스체크 + 인증 의존성 테스트."""
import pytest


async def test_health_check(client):
    """GET /health 정상 응답."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data


async def test_status_endpoint(client):
    """GET /status 정상 응답."""
    resp = await client.get("/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "operational"


async def test_openapi_schema(client):
    """OpenAPI 스키마 생성 확인."""
    resp = await client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    assert "paths" in schema
    assert "/health" in schema["paths"]
