"""프로젝트 아카이브 — 중간 산출물 파일화 + manifest + API 테스트."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from tests.conftest import make_supabase_mock


# ══════════════════════════════════════════════
# 1. 렌더러 단위 테스트
# ══════════════════════════════════════════════

class TestRenderers:
    """State → Markdown 렌더링 검증."""

    def test_render_rfp_analysis(self):
        from app.services.project_archive_service import _render_rfp_analysis
        data = {
            "project_name": "AI 플랫폼 구축",
            "client": "행정안전부",
            "deadline": "2026-04-01",
            "case_type": "A",
            "eval_method": "협상에 의한 계약",
            "tech_price_ratio": {"tech": 80, "price": 20},
            "hot_buttons": ["클라우드 네이티브", "보안"],
            "mandatory_reqs": ["PM 10년 경력"],
            "eval_items": [{"name": "기술", "weight": 80}],
            "special_conditions": ["지체상금 0.1%/일"],
        }
        md = _render_rfp_analysis(data)
        assert "# RFP 분석 보고서" in md
        assert "AI 플랫폼 구축" in md
        assert "클라우드 네이티브" in md

    def test_render_compliance_matrix(self):
        from app.services.project_archive_service import _render_compliance_matrix
        data = [
            {"req_id": "R-001", "content": "PM 10년 경력", "source_step": "rfp", "status": "충족", "proposal_section": "4.1"},
            {"req_id": "R-002", "content": "보안 인증", "source_step": "rfp", "status": "미확인", "proposal_section": ""},
        ]
        md = _render_compliance_matrix(data)
        assert "| R-001" in md
        assert "| R-002" in md
        assert "충족" in md

    def test_render_go_no_go(self):
        from app.services.project_archive_service import _render_go_no_go
        data = {
            "recommendation": "go",
            "positioning": "offensive",
            "positioning_rationale": "기술 우위",
            "feasibility_score": 85,
            "decision": "go",
            "score_breakdown": {"기술": 90, "가격": 80},
            "pros": ["핵심 기술 보유"],
            "risks": ["인력 부족"],
        }
        md = _render_go_no_go(data)
        assert "**GO**" in md
        assert "offensive" in md
        assert "85점" in md

    def test_render_strategy(self):
        from app.services.project_archive_service import _render_strategy
        data = {
            "positioning": "offensive",
            "positioning_rationale": "기술 차별화",
            "win_theme": "AI 네이티브 역량",
            "ghost_theme": "레거시 의존",
            "action_forcing_event": "정부 AI 정책",
            "key_messages": ["AI 전문 인력 30명"],
            "price_strategy": {"approach": "competitive"},
            "competitor_analysis": {"삼성SDS": {"threat": "high"}},
            "risks": [{"name": "인력", "severity": "medium"}],
            "alternatives": [{"alt_id": "A1", "win_theme": "비용 효율", "ghost_theme": "품질 리스크"}],
        }
        md = _render_strategy(data)
        assert "AI 네이티브 역량" in md
        assert "offensive" in md

    def test_render_bid_plan(self):
        from app.services.project_archive_service import _render_bid_plan
        data = {
            "recommended_bid": 450000000,
            "recommended_ratio": 0.9,
            "win_probability": 0.72,
            "data_quality": "market_based",
            "scenarios": [{"name": "보수적", "price": 460000000}],
            "cost_breakdown": {"인건비": 300000000},
            "market_context": {"유사과제_평균": 0.88},
        }
        md = _render_bid_plan(data)
        assert "450,000,000" in md
        assert "90.0%" in md

    def test_render_proposal_sections(self):
        from app.services.project_archive_service import _render_proposal_sections
        data = [
            {"section_id": "s1", "title": "사업 이해", "content": "본 사업은...", "case_type": "A", "version": 1},
            {"section_id": "s2", "title": "수행 방법", "content": "MSA 기반...", "case_type": "A", "version": 1},
        ]
        md = _render_proposal_sections(data)
        assert "## 사업 이해" in md
        assert "## 수행 방법" in md
        assert "MSA 기반" in md

    def test_render_ppt_slides(self):
        from app.services.project_archive_service import _render_ppt_slides
        data = [
            {"slide_id": "p1", "title": "표지", "content": "AI 플랫폼 구축 제안", "notes": "인사 후 시작", "version": 1},
        ]
        md = _render_ppt_slides(data)
        assert "## 슬라이드: 표지" in md
        assert "발표자 노트" in md

    def test_render_feedback_history(self):
        from app.services.project_archive_service import _render_feedback_history
        data = [
            {"step": "strategy", "color": "YELLOW", "feedback": "가격 전략 보완 필요"},
        ]
        md = _render_feedback_history(data)
        assert "피드백 #1" in md
        assert "YELLOW" in md

    def test_render_empty_data_returns_fallback(self):
        from app.services.project_archive_service import _render_proposal_sections, _render_ppt_slides
        assert "(섹션 없음)" in _render_proposal_sections(None)
        assert "(슬라이드 없음)" in _render_ppt_slides(None)

    def test_render_plan_section(self):
        from app.services.project_archive_service import _render_plan_section
        data = {"team": [{"name": "PM", "grade": "특급"}], "schedule": {"start": "2026-04"}}
        md = _render_plan_section(data, sub_key="team")
        assert "투입인력 계획" in md

    def test_render_storyline(self):
        from app.services.project_archive_service import _render_storyline
        data = {"storylines": {"사업이해": {"key_message": "AI 핵심 역량", "narrative_arc": "도입→전개→결론"}}}
        md = _render_storyline(data)
        assert "스토리라인" in md
        assert "사업이해" in md


# ══════════════════════════════════════════════
# 2. render_artifact 통합 테스트
# ══════════════════════════════════════════════

class TestRenderArtifact:
    """ARCHIVE_DEFS + state → render_artifact 통합."""

    def test_render_rfp_raw(self):
        from app.services.project_archive_service import render_artifact, _DEF_MAP
        state = {"rfp_raw": "RFP 원문 텍스트 내용입니다."}
        result = render_artifact(_DEF_MAP["rfp_raw_text"], state)
        assert "RFP 원문" in result

    def test_render_missing_state_returns_none(self):
        from app.services.project_archive_service import render_artifact, _DEF_MAP
        state = {}
        result = render_artifact(_DEF_MAP["rfp_raw_text"], state)
        assert result is None

    def test_render_plan_sub_key(self):
        from app.services.project_archive_service import render_artifact, _DEF_MAP
        state = {"plan": {"team": [{"name": "PM"}], "schedule": {}, "storylines": {}, "bid_price": {}}}
        result = render_artifact(_DEF_MAP["team_plan"], state)
        assert result is not None
        assert "투입인력" in result

    def test_render_all_defs_with_data(self):
        """모든 ARCHIVE_DEFS에 대해 데이터가 있을 때 렌더링 성공."""
        from app.services.project_archive_service import render_artifact, ARCHIVE_DEFS

        state = {
            "rfp_raw": "RFP 텍스트",
            "rfp_analysis": {"project_name": "T", "client": "C", "deadline": "D", "case_type": "A",
                             "eval_method": "", "eval_items": [], "tech_price_ratio": {},
                             "hot_buttons": [], "mandatory_reqs": [], "format_template": {},
                             "volume_spec": {}, "special_conditions": []},
            "compliance_matrix": [{"req_id": "R1", "content": "C", "source_step": "S", "status": "충족", "proposal_section": ""}],
            "go_no_go": {"recommendation": "go", "positioning": "offensive", "positioning_rationale": "",
                         "feasibility_score": 80, "score_breakdown": {}, "pros": [], "risks": [], "decision": "go"},
            "research_brief": {"topics": ["AI"]},
            "strategy": {"positioning": "offensive", "positioning_rationale": "", "alternatives": [],
                         "win_theme": "", "ghost_theme": "", "action_forcing_event": "",
                         "key_messages": [], "price_strategy": {}, "competitor_analysis": {}, "risks": []},
            "bid_plan": {"recommended_bid": 100, "recommended_ratio": 0.9, "win_probability": 0.5,
                         "scenarios": [], "cost_breakdown": {}, "sensitivity_curve": [],
                         "market_context": {}, "data_quality": "rule_based"},
            "evaluation_simulation": {"score": 85},
            "plan": {"team": [{"name": "PM"}], "schedule": {"start": "2026-04"},
                     "storylines": {"sec1": {"key_message": ""}}, "bid_price": {"total": 100},
                     "deliverables": []},
            "proposal_sections": [{"section_id": "s1", "title": "T", "content": "C", "case_type": "A", "version": 1}],
            "ppt_slides": [{"slide_id": "p1", "title": "T", "content": "C", "notes": "", "version": 1}],
            "presentation_strategy": {"approach": "storytelling"},
            "feedback_history": [{"step": "strategy", "feedback": "OK"}],
        }

        rendered_count = 0
        for defn in ARCHIVE_DEFS:
            result = render_artifact(defn, state)
            if result is not None:
                rendered_count += 1
                assert isinstance(result, str)
                assert len(result) > 0

        assert rendered_count == len(ARCHIVE_DEFS), f"모든 {len(ARCHIVE_DEFS)}개 정의가 렌더링되어야 함 (실제: {rendered_count})"


# ══════════════════════════════════════════════
# 3. archive_artifact 서비스 테스트
# ══════════════════════════════════════════════

class TestArchiveArtifact:
    """archive_artifact DB + Storage 연동."""

    _svc = "app.services.project_archive_service.get_async_client"

    async def test_archive_artifact_success(self):
        from app.services.project_archive_service import archive_artifact

        mock_sb = make_supabase_mock({"project_archive": [{"version": 1}]})
        mock_storage = AsyncMock()
        mock_sb.storage = MagicMock()
        mock_sb.storage.from_ = MagicMock(return_value=mock_storage)

        with patch(self._svc, return_value=mock_sb):
            result = await archive_artifact(
                "proj-001", "rfp_raw_text", "RFP 원문 텍스트입니다.",
                created_by="user-001",
            )
        assert isinstance(result, dict)

    async def test_archive_binary_artifact(self):
        from app.services.project_archive_service import archive_binary_artifact

        mock_sb = make_supabase_mock({"project_archive": [{"version": 0}]})
        mock_storage = AsyncMock()
        mock_sb.storage = MagicMock()
        mock_sb.storage.from_ = MagicMock(return_value=mock_storage)

        with patch(self._svc, return_value=mock_sb):
            result = await archive_binary_artifact(
                "proj-001", doc_type="proposal_docx", category="proposal",
                title="제안서 DOCX", file_format="docx",
                file_bytes=b"PK\x03\x04fake-docx",
                storage_subpath="proposal/proposal.docx",
            )
        assert isinstance(result, dict)


# ══════════════════════════════════════════════
# 4. snapshot_from_state 통합 테스트
# ══════════════════════════════════════════════

class TestSnapshotFromState:
    """전체 state 스냅샷."""

    _svc = "app.services.project_archive_service.get_async_client"

    async def test_snapshot_archives_available_artifacts(self):
        from app.services.project_archive_service import snapshot_from_state

        mock_sb = make_supabase_mock({"project_archive": [{"version": 0}]})
        mock_storage = AsyncMock()
        mock_sb.storage = MagicMock()
        mock_sb.storage.from_ = MagicMock(return_value=mock_storage)

        state = {
            "project_id": "proj-001",
            "rfp_raw": "RFP 텍스트",
            "rfp_analysis": {"project_name": "T", "client": "C", "deadline": "D", "case_type": "A",
                             "eval_method": "", "eval_items": [], "tech_price_ratio": {},
                             "hot_buttons": [], "mandatory_reqs": [], "format_template": {},
                             "volume_spec": {}, "special_conditions": []},
            "go_no_go": {"recommendation": "go", "positioning": "offensive", "positioning_rationale": "",
                         "feasibility_score": 80, "score_breakdown": {}, "pros": [], "risks": [], "decision": "go"},
        }

        with patch(self._svc, return_value=mock_sb):
            archived = await snapshot_from_state("proj-001", state, created_by="user-001")

        # rfp_raw, rfp_analysis, compliance_matrix(empty=skip), go_no_go → 3개 이상
        assert len(archived) >= 3

    async def test_snapshot_empty_state(self):
        from app.services.project_archive_service import snapshot_from_state

        mock_sb = make_supabase_mock()
        with patch(self._svc, return_value=mock_sb):
            archived = await snapshot_from_state("proj-001", {})
        assert len(archived) == 0


# ══════════════════════════════════════════════
# 5. manifest API 테스트
# ══════════════════════════════════════════════

class TestManifestAPI:
    """프로젝트 마스터 파일 일람 API."""

    async def test_get_manifest(self, client):
        """GET /api/proposals/{id}/archive → 마스터 일람."""
        mock_manifest = {
            "proposal_id": "proj-001",
            "categories": {},
            "total_count": 0,
            "total_size": 0,
        }
        with patch("app.api.routes_project_archive.get_project_manifest",
                   new_callable=AsyncMock, return_value=mock_manifest) as mock_fn:
            # get_project_manifest is imported inside the endpoint, patch at route level
            with patch("app.services.project_archive_service.get_project_manifest",
                       new_callable=AsyncMock, return_value=mock_manifest):
                resp = await client.get("/api/proposals/proj-001/archive")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "categories" in data
        assert "total_count" in data
        assert "total_size" in data

    async def test_get_archive_versions(self, client):
        """GET /api/proposals/{id}/archive/{doc_type}/versions → 버전 이력."""
        resp = await client.get("/api/proposals/proj-001/archive/rfp_analysis/versions")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert isinstance(data["data"], list)


# ══════════════════════════════════════════════
# 6. ARCHIVE_DEFS 레지스트리 검증
# ══════════════════════════════════════════════

class TestArchiveDefsRegistry:
    """산출물 정의 레지스트리 일관성."""

    def test_all_defs_have_required_fields(self):
        from app.services.project_archive_service import ARCHIVE_DEFS
        required = {"doc_type", "category", "title", "file_format", "state_key", "graph_step", "storage_subpath"}
        for defn in ARCHIVE_DEFS:
            for field in required:
                assert field in defn, f"{defn['doc_type']}: 필수 필드 {field} 누락"

    def test_all_doc_types_unique(self):
        from app.services.project_archive_service import ARCHIVE_DEFS
        doc_types = [d["doc_type"] for d in ARCHIVE_DEFS]
        assert len(doc_types) == len(set(doc_types)), "중복 doc_type 존재"

    def test_all_storage_subpaths_unique(self):
        from app.services.project_archive_service import ARCHIVE_DEFS
        paths = [d["storage_subpath"] for d in ARCHIVE_DEFS]
        assert len(paths) == len(set(paths)), "중복 storage_subpath 존재"

    def test_def_map_consistent(self):
        from app.services.project_archive_service import ARCHIVE_DEFS, _DEF_MAP
        assert len(_DEF_MAP) == len(ARCHIVE_DEFS)
        for defn in ARCHIVE_DEFS:
            assert defn["doc_type"] in _DEF_MAP

    def test_all_renderers_exist(self):
        from app.services.project_archive_service import ARCHIVE_DEFS, _RENDERERS
        for defn in ARCHIVE_DEFS:
            renderer_name = defn.get("renderer")
            if renderer_name:
                assert renderer_name in _RENDERERS, f"{defn['doc_type']}: 렌더러 {renderer_name} 미존재"

    def test_def_count(self):
        """16개 중간 산출물 정의."""
        from app.services.project_archive_service import ARCHIVE_DEFS
        assert len(ARCHIVE_DEFS) == 16
