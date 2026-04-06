"""Phase 10: 프로젝트 파일 관리 체계 테스트 (GAP-1~6).

GAP-1: RFP 원본 파일 보존 (create_from_rfp → Storage + proposal_files)
GAP-2: 프로젝트 파일 관리 API (routes_files.py 4개 엔드포인트)
GAP-3: 피드백 DB 자동 저장 (resume → feedbacks INSERT)
GAP-4: 산출물 버전 관리 (save_artifact/regenerate → artifacts INSERT)
GAP-5: 프로젝트 삭제 + Storage 정리
GAP-6: 프로젝트별 참고자료 업로드 (routes_files.py)
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from tests.conftest import MockQueryBuilder


# ── 헬퍼 ──

def make_async_client_mock(table_overrides=None):
    """테스트용 Supabase async client mock (table별 데이터 커스터마이즈)."""
    table_overrides = table_overrides or {}
    mock_client = AsyncMock()

    def _table(name):
        if name in table_overrides:
            return table_overrides[name]
        return MockQueryBuilder()

    mock_client.table = _table

    # storage mock
    bucket = AsyncMock()
    bucket.upload = AsyncMock(return_value=None)
    bucket.remove = AsyncMock(return_value=None)
    bucket.create_signed_url = AsyncMock(return_value={
        "signedURL": "https://storage.test/signed?token=abc"
    })
    mock_client.storage = MagicMock()
    mock_client.storage.from_ = MagicMock(return_value=bucket)

    return mock_client


class SingleQueryBuilder(MockQueryBuilder):
    """maybe_single()가 단일 dict를 반환하는 MockQueryBuilder.

    routes_files, routes_proposal의 .maybe_single().execute()는
    result.data가 dict (또는 None)이어야 한다.
    """

    async def execute(self):
        result = MagicMock()
        if self._data and isinstance(self._data, list):
            result.data = self._data[0]
        else:
            result.data = self._data
        result.count = 1 if result.data else 0
        return result


class TrackingQueryBuilder(MockQueryBuilder):
    """insert/delete 호출을 추적하는 MockQueryBuilder."""

    def __init__(self, data=None):
        super().__init__(data)
        self.inserted = []
        self.deleted = False

    def insert(self, data):
        self.inserted.append(data)
        return self

    def delete(self):
        self.deleted = True
        return self


class TrackingSingleBuilder(SingleQueryBuilder):
    """단일 결과 + insert/delete 추적."""

    def __init__(self, data=None):
        super().__init__(data)
        self.inserted = []
        self.deleted = False

    def insert(self, data):
        self.inserted.append(data)
        return self

    def delete(self):
        self.deleted = True
        return self


# ──────────────────────────────────────────────────────────────────────
# GAP-1: RFP 원본 파일 보존
# ──────────────────────────────────────────────────────────────────────

async def test_create_from_rfp_stores_rfp_file(client):
    """POST /api/proposals/from-rfp — proposal_files에 rfp 레코드 INSERT."""
    pf_builder = TrackingQueryBuilder()
    prop_builder = TrackingQueryBuilder()
    mock_sb = make_async_client_mock({
        "proposals": prop_builder,
        "proposal_files": pf_builder,
    })

    with patch("app.api.routes_proposal.get_async_client", new=AsyncMock(return_value=mock_sb)):
        resp = await client.post(
            "/api/proposals/from-rfp",
            files={"rfp_file": ("test_rfp.pdf", b"fake pdf content", "application/pdf")},
            data={"rfp_title": "테스트 RFP", "mode": "lite"},
        )

    assert resp.status_code == 201
    data = resp.json()
    assert "proposal_id" in data
    assert data["title"] == "테스트 RFP"

    # proposal_files에 rfp 레코드가 삽입되었는지
    rfp_inserts = [r for r in pf_builder.inserted if r.get("category") == "rfp"]
    assert len(rfp_inserts) == 1
    row = rfp_inserts[0]
    assert row["filename"] == "test_rfp.pdf"
    assert row["file_type"] == "pdf"
    assert row["file_size"] == len(b"fake pdf content")
    assert "rfp/" in row["storage_path"]


async def test_create_from_rfp_sets_storage_path_rfp(client):
    """proposals.storage_path_rfp가 설정되는지 확인."""
    prop_builder = TrackingQueryBuilder()
    pf_builder = TrackingQueryBuilder()
    mock_sb = make_async_client_mock({
        "proposals": prop_builder,
        "proposal_files": pf_builder,
    })

    with patch("app.api.routes_proposal.get_async_client", new=AsyncMock(return_value=mock_sb)):
        resp = await client.post(
            "/api/proposals/from-rfp",
            files={"rfp_file": ("제안요청서.hwp", b"hwp content", "application/hwp")},
            data={"rfp_title": ""},
        )

    assert resp.status_code == 201
    assert len(prop_builder.inserted) == 1
    row = prop_builder.inserted[0]
    assert "storage_path_rfp" in row
    assert row["storage_path_rfp"].endswith("/rfp/제안요청서.hwp")


# ──────────────────────────────────────────────────────────────────────
# GAP-2 + GAP-6: 프로젝트 파일 관리 API
# ──────────────────────────────────────────────────────────────────────

async def test_upload_project_file(client):
    """POST /api/proposals/{id}/files — 참고자료 업로드 성공."""
    pf_builder = TrackingQueryBuilder()
    mock_sb = make_async_client_mock({
        "proposals": MockQueryBuilder([{"id": "prop-001", "owner_id": "user-001", "team_id": "team-001"}]),
        "proposal_files": pf_builder,
    })

    with patch("app.api.routes_files.get_async_client", new=AsyncMock(return_value=mock_sb)):
        resp = await client.post(
            "/api/proposals/prop-001/files",
            files={"file": ("참고자료.pdf", b"pdf bytes here", "application/pdf")},
            data={"description": "사업 참고자료"},
        )

    assert resp.status_code == 201
    data = resp.json()["data"]
    assert "file_id" in data
    assert data["filename"] == "참고자료.pdf"
    assert "references/" in data["storage_path"]

    assert len(pf_builder.inserted) == 1
    row = pf_builder.inserted[0]
    assert row["category"] == "reference"
    assert row["description"] == "사업 참고자료"
    assert row["file_type"] == "pdf"


async def test_upload_file_rejected_extension(client):
    """허용되지 않는 확장자 → 400."""
    mock_sb = make_async_client_mock({
        "proposals": MockQueryBuilder([{"id": "prop-001", "owner_id": "user-001", "team_id": "team-001"}]),
    })

    with patch("app.api.routes_files.get_async_client", new=AsyncMock(return_value=mock_sb)):
        resp = await client.post(
            "/api/proposals/prop-001/files",
            files={"file": ("malware.exe", b"bad", "application/exe")},
        )

    assert resp.status_code == 415
    assert "지원하지 않는" in resp.json()["message"]


async def test_list_project_files(client):
    """GET /api/proposals/{id}/files — 파일 목록."""
    mock_sb = make_async_client_mock({
        "proposal_files": MockQueryBuilder([
            {"id": "f1", "proposal_id": "prop-001", "category": "rfp", "filename": "rfp.pdf",
             "storage_path": "prop-001/rfp/rfp.pdf", "file_type": "pdf", "file_size": 1024,
             "uploaded_by": "u1", "description": None, "created_at": "2026-03-20T10:00:00Z"},
            {"id": "f2", "proposal_id": "prop-001", "category": "reference", "filename": "ref.docx",
             "storage_path": "prop-001/references/f2.docx", "file_type": "docx", "file_size": 2048,
             "uploaded_by": "u1", "description": "참고", "created_at": "2026-03-20T11:00:00Z"},
        ]),
    })

    with patch("app.api.routes_files.get_async_client", new=AsyncMock(return_value=mock_sb)):
        resp = await client.get("/api/proposals/prop-001/files")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) == 2


async def test_list_project_files_with_category_filter(client):
    """GET /api/proposals/{id}/files?category=rfp — 카테고리 필터."""
    mock_sb = make_async_client_mock({
        "proposal_files": MockQueryBuilder([{"id": "f1", "category": "rfp", "filename": "rfp.pdf"}]),
    })

    with patch("app.api.routes_files.get_async_client", new=AsyncMock(return_value=mock_sb)):
        resp = await client.get("/api/proposals/prop-001/files?category=rfp")

    assert resp.status_code == 200
    assert "data" in resp.json()


async def test_delete_project_file(client):
    """DELETE /api/proposals/{id}/files/{file_id} — 파일 삭제."""
    pf_builder = TrackingSingleBuilder([{
        "id": "f2", "storage_path": "p/references/f2.docx",
        "uploaded_by": "user-001", "category": "reference",
    }])
    mock_sb = make_async_client_mock({
        "proposal_files": pf_builder,
        "proposals": SingleQueryBuilder([{"owner_id": "user-001"}]),
    })

    with patch("app.api.routes_files.get_async_client", new=AsyncMock(return_value=mock_sb)):
        resp = await client.delete("/api/proposals/prop-001/files/f2")

    assert resp.status_code == 204


async def test_delete_rfp_file_forbidden(client):
    """RFP 원본 삭제 → 403."""
    mock_sb = make_async_client_mock({
        "proposal_files": SingleQueryBuilder([{
            "id": "f1", "storage_path": "p/rfp/rfp.pdf",
            "uploaded_by": "user-001", "category": "rfp",
        }]),
    })

    with patch("app.api.routes_files.get_async_client", new=AsyncMock(return_value=mock_sb)):
        resp = await client.delete("/api/proposals/prop-001/files/f1")

    assert resp.status_code == 403
    assert "RFP" in resp.json()["message"]


async def test_get_file_download_url(client):
    """GET /api/proposals/{id}/files/{file_id}/url — 서명 URL."""
    mock_sb = make_async_client_mock({
        "proposal_files": SingleQueryBuilder([{
            "storage_path": "p/references/f2.docx", "filename": "참고.docx",
        }]),
    })

    with patch("app.api.routes_files.get_async_client", new=AsyncMock(return_value=mock_sb)):
        resp = await client.get("/api/proposals/prop-001/files/f2/url")

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "url" in data
    assert data["filename"] == "참고.docx"
    assert data["expires_in"] == 3600


async def test_get_file_url_not_found(client):
    """존재하지 않는 파일 → 404."""
    mock_sb = make_async_client_mock({
        "proposal_files": SingleQueryBuilder([]),  # 빈 결과
    })

    with patch("app.api.routes_files.get_async_client", new=AsyncMock(return_value=mock_sb)):
        resp = await client.get("/api/proposals/prop-001/files/nonexist/url")

    assert resp.status_code == 404


# ──────────────────────────────────────────────────────────────────────
# GAP-3: 피드백 DB 자동 저장
# ──────────────────────────────────────────────────────────────────────

async def test_resume_saves_feedback_to_db(client):
    """POST /api/proposals/{id}/resume — feedback → feedbacks INSERT."""
    fb_builder = TrackingQueryBuilder()
    mock_sb = make_async_client_mock({
        "feedbacks": fb_builder,
        "proposals": MockQueryBuilder(),
    })

    mock_snapshot = MagicMock()
    mock_snapshot.next = ["review_strategy"]
    mock_snapshot.values = {"current_step": "review_strategy"}

    mock_graph = AsyncMock()
    mock_graph.aget_state = AsyncMock(return_value=mock_snapshot)
    mock_graph.ainvoke = AsyncMock(return_value={"current_step": "strategy_approved"})

    with patch("app.api.routes_workflow.get_async_client", new=AsyncMock(return_value=mock_sb)), \
         patch("app.api.routes_workflow._get_graph", return_value=mock_graph):
        resp = await client.post("/api/proposals/test-prop/resume", json={
            "approved": True,
            "feedback": "전략이 좋습니다. Win Theme 보완 필요.",
            "comments": {"strategy": "공격적 포지셔닝 유지"},
        })

    assert resp.status_code == 200

    assert len(fb_builder.inserted) == 1
    row = fb_builder.inserted[0]
    assert row["proposal_id"] == "test-prop"
    assert "전략이 좋습니다" in row["feedback"]
    assert row["author_id"] == "user-001"


async def test_resume_no_feedback_skips_insert(client):
    """feedback 없으면 feedbacks INSERT 안 함."""
    fb_builder = TrackingQueryBuilder()
    mock_sb = make_async_client_mock({
        "feedbacks": fb_builder,
        "proposals": MockQueryBuilder(),
    })

    mock_snapshot = MagicMock()
    mock_snapshot.next = ["review_rfp"]
    mock_snapshot.values = {"current_step": "review_rfp"}

    mock_graph = AsyncMock()
    mock_graph.aget_state = AsyncMock(return_value=mock_snapshot)
    mock_graph.ainvoke = AsyncMock(return_value={"current_step": "rfp_approved"})

    with patch("app.api.routes_workflow.get_async_client", new=AsyncMock(return_value=mock_sb)), \
         patch("app.api.routes_workflow._get_graph", return_value=mock_graph):
        resp = await client.post("/api/proposals/test-prop/resume", json={
            "approved": True,
        })

    assert resp.status_code == 200
    assert len(fb_builder.inserted) == 0


# ──────────────────────────────────────────────────────────────────────
# GAP-4: 산출물 버전 관리
# ──────────────────────────────────────────────────────────────────────

async def test_save_artifact_creates_version(client):
    """PUT /api/proposals/{id}/artifacts/{step} — artifacts v1 INSERT."""
    art_builder = TrackingQueryBuilder([])  # 기존 버전 없음

    mock_snapshot = MagicMock()
    mock_snapshot.values = {"proposal_sections": [{"title": "sec1", "content": "old"}]}

    mock_graph = AsyncMock()
    mock_graph.aget_state = AsyncMock(return_value=mock_snapshot)
    mock_graph.aupdate_state = AsyncMock()

    # save_artifact 내의 lazy import용 mock
    art_mock_sb = make_async_client_mock({"artifacts": art_builder})

    # artifacts 버전 기록은 lazy import로 app.utils.supabase_client.get_async_client 사용
    with patch("app.api.routes_workflow._get_graph", return_value=mock_graph), \
         patch("app.utils.supabase_client.get_async_client", new=AsyncMock(return_value=art_mock_sb)):
        resp = await client.put("/api/proposals/test-prop/artifacts/proposal", json={
            "content": "<p>수정된 내용</p>",
            "change_source": "human_edit",
        })

    assert resp.status_code == 200
    assert resp.json()["saved"] is True

    assert len(art_builder.inserted) == 1
    row = art_builder.inserted[0]
    assert row["proposal_id"] == "test-prop"
    assert row["step"] == "proposal"
    assert row["version"] == 1
    assert row["change_source"] == "human_edit"
    assert row["created_by"] == "user-001"


async def test_save_artifact_increments_version(client):
    """기존 버전 3 → version 4로 증가."""
    art_builder = TrackingQueryBuilder([{
        "id": "art-001",
        "proposal_id": "test-prop",
        "step": "strategy",
        "version": 3,
        "status": "completed",
        "created_by": "user-001",
    }])

    mock_snapshot = MagicMock()
    mock_snapshot.values = {"strategy": {"win_theme": "기존"}}

    mock_graph = AsyncMock()
    mock_graph.aget_state = AsyncMock(return_value=mock_snapshot)
    mock_graph.aupdate_state = AsyncMock()

    art_mock_sb = make_async_client_mock({"artifacts": art_builder})

    with patch("app.api.routes_workflow._get_graph", return_value=mock_graph), \
         patch("app.utils.supabase_client.get_async_client", new=AsyncMock(return_value=art_mock_sb)):
        resp = await client.put("/api/proposals/test-prop/artifacts/strategy", json={
            "content": {"win_theme": "수정됨"},
            "change_source": "human_edit",
        })

    assert resp.status_code == 200
    assert len(art_builder.inserted) == 1
    assert art_builder.inserted[0]["version"] == 4


# ──────────────────────────────────────────────────────────────────────
# GAP-5: 프로젝트 삭제 + Storage 정리
# ──────────────────────────────────────────────────────────────────────

async def test_delete_proposal(client):
    """DELETE /api/proposals/{id} — 프로젝트 삭제."""
    prop_builder = TrackingSingleBuilder([{
        "id": "prop-001", "owner_id": "user-001", "status": "completed",
        "storage_path_docx": "prop-001/proposal.docx",
        "storage_path_pptx": None, "storage_path_hwpx": None,
        "storage_path_rfp": "prop-001/rfp/test.pdf",
    }])
    pf_builder = MockQueryBuilder([
        {"proposal_id": "prop-001", "storage_path": "prop-001/references/ref1.pdf"},
        {"proposal_id": "prop-001", "storage_path": "prop-001/rfp/test.pdf"},
    ])
    mock_sb = make_async_client_mock({
        "proposals": prop_builder,
        "proposal_files": pf_builder,
    })

    with patch("app.api.routes_proposal.get_async_client", new=AsyncMock(return_value=mock_sb)):
        resp = await client.delete("/api/proposals/prop-001")

    assert resp.status_code == 204

    # Storage remove 호출
    bucket = mock_sb.storage.from_.return_value
    bucket.remove.assert_called_once()
    removed = bucket.remove.call_args[0][0]
    assert "prop-001/references/ref1.pdf" in removed
    assert "prop-001/proposal.docx" in removed
    assert "prop-001/rfp/test.pdf" in removed


async def test_delete_proposal_not_owner(client):
    """소유자 아닌 사용자 → 403."""
    mock_sb = make_async_client_mock({
        "proposals": SingleQueryBuilder([{
            "id": "prop-001", "owner_id": "user-999", "status": "completed",
        }]),
    })

    with patch("app.api.routes_proposal.get_async_client", new=AsyncMock(return_value=mock_sb)):
        resp = await client.delete("/api/proposals/prop-001")

    assert resp.status_code == 403


async def test_delete_running_proposal_blocked(client):
    """실행 중 삭제 → 409."""
    mock_sb = make_async_client_mock({
        "proposals": SingleQueryBuilder([{
            "id": "prop-001", "owner_id": "user-001", "status": "processing",
        }]),
    })

    with patch("app.api.routes_proposal.get_async_client", new=AsyncMock(return_value=mock_sb)):
        resp = await client.delete("/api/proposals/prop-001")

    assert resp.status_code == 409


# ──────────────────────────────────────────────────────────────────────
# DB 마이그레이션 + 라우터 등록 검증
# ──────────────────────────────────────────────────────────────────────

def test_migration_sql_exists():
    """009_proposal_files.sql 마이그레이션 파일 존재 + 핵심 구문."""
    from pathlib import Path
    sql_path = Path(__file__).parent.parent / "database" / "migrations" / "009_proposal_files.sql"
    assert sql_path.exists()

    content = sql_path.read_text(encoding="utf-8")
    assert "CREATE TABLE" in content
    assert "proposal_files" in content
    assert "ON DELETE CASCADE" in content
    assert "idx_proposal_files_proposal" in content
    assert "idx_proposal_files_category" in content


def test_files_router_registered():
    """files_router가 app에 등록되어 있는지."""
    from tests.conftest import _get_test_app
    app = _get_test_app()
    routes = [r.path for r in app.routes]
    assert any("/files" in r for r in routes)


async def test_upload_file_to_storage_helper():
    """_upload_file_to_storage 헬퍼 함수 동작."""
    from app.api.routes_proposal import _upload_file_to_storage

    mock_sb = make_async_client_mock()

    with patch("app.api.routes_proposal.get_async_client", new=AsyncMock(return_value=mock_sb)):
        await _upload_file_to_storage("p/rfp/test.pdf", b"content", "application/pdf")

    bucket = mock_sb.storage.from_.return_value
    bucket.upload.assert_called_once()
    assert bucket.upload.call_args.kwargs["path"] == "p/rfp/test.pdf"
