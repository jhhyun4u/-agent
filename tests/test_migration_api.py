"""
Phase 4: 마이그레이션 API 테스트

FastAPI 라우터 등록 및 엔드포인트 검증
"""

import pytest

from app.api.routes_migrations import router as migrations_router


class TestMigrationAPI:
    """마이그레이션 API 라우터 테스트"""

    def test_router_has_5_routes(self):
        """마이그레이션 라우터에 5개 경로 등록 확인"""
        # router.routes는 APIRoute 객체 리스트
        routes = [route for route in migrations_router.routes]
        # 5개의 API 엔드포인트 확인
        assert len(routes) >= 5, f"Expected at least 5 routes, got {len(routes)}"

    def test_trigger_endpoint_exists(self):
        """POST /trigger 엔드포인트 존재"""
        route_paths = [str(route.path) for route in migrations_router.routes]
        assert any("/trigger" in path for path in route_paths), \
            f"Trigger endpoint not found in routes: {route_paths}"

    def test_list_batches_endpoint_exists(self):
        """GET /batches 엔드포인트 존재"""
        route_paths = [str(route.path) for route in migrations_router.routes]
        assert any("/batches" in path for path in route_paths), \
            f"List batches endpoint not found in routes: {route_paths}"

    def test_get_batch_endpoint_exists(self):
        """GET /batches/{batch_id} 엔드포인트 존재"""
        route_paths = [str(route.path) for route in migrations_router.routes]
        assert any("/batches/{batch_id}" in path for path in route_paths), \
            f"Get batch endpoint not found in routes: {route_paths}"

    def test_get_schedule_endpoint_exists(self):
        """GET /schedule 엔드포인트 존재"""
        route_paths = [str(route.path) for route in migrations_router.routes]
        assert any("/schedule" in path for path in route_paths), \
            f"Get schedule endpoint not found in routes: {route_paths}"

    def test_update_schedule_endpoint_exists(self):
        """PUT /schedule/{schedule_id} 엔드포인트 존재"""
        route_paths = [str(route.path) for route in migrations_router.routes]
        assert any("schedule" in path and "{schedule_id}" in path for path in route_paths), \
            f"Update schedule endpoint not found in routes: {route_paths}"

    def test_trigger_endpoint_is_post(self):
        """POST /trigger 메서드 확인"""
        for route in migrations_router.routes:
            if "/trigger" in str(route.path):
                assert "POST" in route.methods, f"POST not in {route.methods}"
                break
        else:
            pytest.fail("POST /trigger endpoint not found")

    def test_list_batches_endpoint_is_get(self):
        """GET /batches 메서드 확인"""
        # Check if GET /batches exists (不用完全一致，检查包含)
        found = False
        for route in migrations_router.routes:
            if "/batches" in str(route.path) and "{" not in str(route.path):
                if "GET" in route.methods:
                    found = True
                    break
        assert found, "GET /batches endpoint not properly configured"

    def test_get_batch_endpoint_is_get(self):
        """GET /batches/{batch_id} 메서드 확인"""
        found = False
        for route in migrations_router.routes:
            if "/batches/{batch_id}" in str(route.path):
                if "GET" in route.methods:
                    found = True
                    break
        assert found, "GET /batches/{batch_id} endpoint not properly configured"

    def test_get_schedule_endpoint_is_get(self):
        """GET /schedule 메서드 확인"""
        found = False
        for route in migrations_router.routes:
            path = str(route.path)
            if path == "/schedule" or "/schedule" in path and "{" not in path:
                if "GET" in route.methods:
                    found = True
                    break
        assert found, "GET /schedule endpoint not properly configured"

    def test_update_schedule_endpoint_is_put(self):
        """PUT /schedule/{schedule_id} 메서드 확인"""
        for route in migrations_router.routes:
            if "/schedule/{schedule_id}" in str(route.path):
                assert "PUT" in route.methods, f"PUT not in {route.methods}"
                break
        else:
            pytest.fail("PUT /schedule/{schedule_id} endpoint not found")


if __name__ == "__main__":
    # pytest 실행: pytest tests/test_migration_api.py -v
    pass
