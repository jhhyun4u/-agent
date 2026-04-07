"""
프롬프트 진화 파이프라인 E2E 테스트

전체 흐름:
1. 레지스트리 동기화 (sync_all_prompts)
2. 노드 실행 시 프롬프트 조회 (get_active_prompt / get_prompt_for_experiment)
3. 사용 기록 (record_usage → prompt_artifact_link)
4. 사람 수정 추적 (record_action → human_edit_tracking)
5. 성과 메트릭 계산 (compute_effectiveness)
6. 주의 프롬프트 감지 (check_prompts_needing_attention)
7. AI 개선 제안 (suggest_improvements) — Claude mock
8. 후보 등록 (create_candidate → prompt_registry)
9. A/B 실험 시작/라우팅/평가/승격/롤백
10. 주기적 유지보수 (periodic_maintenance)
11. API 엔드포인트 (routes_prompt_evolution)
"""

import hashlib
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ═══════════════════════════════════════════════════════════
# DB Mock — insert 축적 + select 조회 가능한 인메모리 스토어
# ═══════════════════════════════════════════════════════════

class InMemoryDB:
    """테이블별 인메모리 데이터 스토어."""

    def __init__(self):
        self.tables: dict[str, list[dict]] = {}

    def table(self, name: str) -> "InMemoryTable":
        if name not in self.tables:
            self.tables[name] = []
        return InMemoryTable(self.tables[name])

    def rpc(self, fn_name: str):
        mock = AsyncMock()
        result = MagicMock()
        result.data = None
        mock.execute = AsyncMock(return_value=result)
        return mock


class InMemoryTable:
    """체이닝 가능한 인메모리 쿼리 빌더."""

    def __init__(self, rows: list[dict]):
        self._rows = rows
        self._filters: list[tuple[str, str, object]] = []
        self._order_by: str | None = None
        self._order_desc: bool = False
        self._limit_n: int | None = None
        self._insert_data: dict | None = None
        self._update_data: dict | None = None
        self._select_cols: str = "*"

    def _clone(self) -> "InMemoryTable":
        t = InMemoryTable(self._rows)
        t._filters = list(self._filters)
        t._order_by = self._order_by
        t._order_desc = self._order_desc
        t._limit_n = self._limit_n
        t._insert_data = self._insert_data
        t._update_data = self._update_data
        t._select_cols = self._select_cols
        return t

    def select(self, cols="*", **kw):
        c = self._clone()
        c._select_cols = cols
        return c

    def insert(self, data):
        c = self._clone()
        c._insert_data = data
        return c

    def update(self, data):
        c = self._clone()
        c._update_data = data
        return c

    def eq(self, col, val):
        c = self._clone()
        c._filters.append(("eq", col, val))
        return c

    def in_(self, col, vals):
        c = self._clone()
        c._filters.append(("in", col, vals))
        return c

    def order(self, col, desc=False):
        c = self._clone()
        c._order_by = col
        c._order_desc = desc
        return c

    def limit(self, n):
        c = self._clone()
        c._limit_n = n
        return c

    # 나머지 체이닝 (no-op)
    def neq(self, *a, **kw): return self._clone()
    def single(self): return self._clone()
    def maybe_single(self): return self._clone()
    def range(self, *a, **kw): return self._clone()
    def ilike(self, *a, **kw): return self._clone()
    def is_(self, *a, **kw): return self._clone()
    def or_(self, *a, **kw): return self._clone()

    def _apply_filters(self, rows):
        for op, col, val in self._filters:
            if op == "eq":
                rows = [r for r in rows if r.get(col) == val]
            elif op == "in":
                rows = [r for r in rows if r.get(col) in val]
        return rows

    async def execute(self):
        result = MagicMock()

        if self._insert_data is not None:
            self._rows.append(dict(self._insert_data))
            result.data = [dict(self._insert_data)]
            result.count = 1
            return result

        if self._update_data is not None:
            updated = []
            for row in self._rows:
                match = True
                for op, col, val in self._filters:
                    if op == "eq" and row.get(col) != val:
                        match = False
                        break
                if match:
                    row.update(self._update_data)
                    updated.append(row)
            result.data = updated
            result.count = len(updated)
            return result

        rows = self._apply_filters(list(self._rows))
        if self._order_by:
            rows.sort(
                key=lambda r: r.get(self._order_by, 0) or 0,
                reverse=self._order_desc,
            )
        if self._limit_n:
            rows = rows[: self._limit_n]
        result.data = rows
        result.count = len(rows)
        return result


@pytest.fixture
def db():
    return InMemoryDB()


@pytest.fixture
def patch_db(db):
    """모든 get_async_client 호출을 인메모리 DB로 대체."""
    with patch(
        "app.utils.supabase_client.get_async_client",
        new_callable=lambda: lambda: AsyncMock(return_value=db),
    ):
        yield db


# ═══════════════════════════════════════════════════════════
# Phase 1: 순수 함수 단위 테스트
# ═══════════════════════════════════════════════════════════


class TestComputeEditRatio:
    """human_edit_tracker.compute_edit_ratio 단위 테스트."""

    def test_identical(self):
        from app.services.human_edit_tracker import compute_edit_ratio
        assert compute_edit_ratio("hello", "hello") == 0.0

    def test_empty_both(self):
        from app.services.human_edit_tracker import compute_edit_ratio
        assert compute_edit_ratio("", "") == 0.0

    def test_empty_original(self):
        from app.services.human_edit_tracker import compute_edit_ratio
        assert compute_edit_ratio("", "new text") == 1.0

    def test_partial_edit(self):
        from app.services.human_edit_tracker import compute_edit_ratio
        ratio = compute_edit_ratio(
            "이것은 AI가 작성한 제안서 섹션입니다.",
            "이것은 사람이 수정한 제안서 섹션입니다.",
        )
        assert 0.0 < ratio < 1.0

    def test_complete_rewrite(self):
        from app.services.human_edit_tracker import compute_edit_ratio
        ratio = compute_edit_ratio("ABC", "XYZ")
        assert ratio > 0.8


class TestExtractVariables:
    """prompt_registry._extract_variables 단위 테스트."""

    def test_simple(self):
        from app.services.prompt_registry import _extract_variables
        result = _extract_variables("Hello {name}, your {role} is ready.")
        assert result == ["name", "role"]

    def test_escaped_braces(self):
        from app.services.prompt_registry import _extract_variables
        # {{...}} 는 이스케이프로 제거됨, 그 밖의 {var}만 추출
        result = _extract_variables("{{escaped}} and {real_var}")
        assert result == ["real_var"]

    def test_no_variables(self):
        from app.services.prompt_registry import _extract_variables
        result = _extract_variables("No variables here.")
        assert result == []


class TestContentHash:
    """prompt_registry._content_hash 일관성 테스트."""

    def test_deterministic(self):
        from app.services.prompt_registry import _content_hash
        text = "테스트 프롬프트 텍스트"
        assert _content_hash(text) == _content_hash(text)
        assert _content_hash(text) == hashlib.sha256(text.encode("utf-8")).hexdigest()

    def test_different_text(self):
        from app.services.prompt_registry import _content_hash
        assert _content_hash("A") != _content_hash("B")


class TestMakePromptId:
    """prompt_registry._make_prompt_id 매핑 테스트."""

    def test_section_prompt(self):
        from app.services.prompt_registry import _make_prompt_id
        assert _make_prompt_id("app.prompts.section_prompts", "SECTION_PROMPT_UNDERSTAND") == "section_prompts.UNDERSTAND"

    def test_plan_prompt(self):
        from app.services.prompt_registry import _make_prompt_id
        assert _make_prompt_id("app.prompts.plan", "PLAN_TEAM_PROMPT") == "plan.TEAM_PROMPT"

    def test_no_prefix(self):
        from app.services.prompt_registry import _make_prompt_id
        assert _make_prompt_id("app.prompts.strategy", "COMPETITIVE_ANALYSIS_FRAMEWORK") == "strategy.COMPETITIVE_ANALYSIS_FRAMEWORK"


class TestCompositeScore:
    """prompt_evolution._composite_score 계산 테스트."""

    def test_perfect(self):
        from app.services.prompt_evolution import _composite_score
        score = _composite_score({
            "win_rate": 100, "avg_quality_score": 100, "avg_edit_ratio": 0.0,
        })
        # 100*0.5 + 100*0.3 + 100*0.2 = 100
        assert score == 100.0

    def test_worst(self):
        from app.services.prompt_evolution import _composite_score
        score = _composite_score({
            "win_rate": 0, "avg_quality_score": 0, "avg_edit_ratio": 1.0,
        })
        assert score == 0.0

    def test_mixed(self):
        from app.services.prompt_evolution import _composite_score
        score = _composite_score({
            "win_rate": 60, "avg_quality_score": 80, "avg_edit_ratio": 0.3,
        })
        # 60*0.5 + 80*0.3 + 70*0.2 = 30+24+14 = 68
        assert score == 68.0


# ═══════════════════════════════════════════════════════════
# Phase 2: 레지스트리 동기화 + 조회
# ═══════════════════════════════════════════════════════════


class TestPromptRegistrySync:
    """sync_all_prompts → DB 등록 확인."""

    @pytest.mark.asyncio
    async def test_sync_registers_prompts(self, db):
        """Python 상수에서 프롬프트를 읽어 DB에 등록."""
        with patch("app.utils.supabase_client.get_async_client", AsyncMock(return_value=db)):
            from app.services.prompt_registry import sync_all_prompts
            result = await sync_all_prompts()

        assert result["synced"] + result["updated"] > 0
        # prompt_registry 테이블에 데이터가 들어갔는지 확인
        rows = db.tables.get("prompt_registry", [])
        assert len(rows) > 0
        # 첫 행 구조 확인
        row = rows[0]
        assert "prompt_id" in row
        assert "content_text" in row
        assert row["status"] == "active"

    @pytest.mark.asyncio
    async def test_sync_idempotent(self, db):
        """같은 내용 재동기화 시 updated=0."""
        with patch("app.utils.supabase_client.get_async_client", AsyncMock(return_value=db)):
            from app.services.prompt_registry import sync_all_prompts
            r1 = await sync_all_prompts()
            r2 = await sync_all_prompts()

        # 두 번째 실행에서는 해시 일치로 updated=0 이어야 함
        assert r2["updated"] == 0


class TestPromptRegistryGet:
    """get_active_prompt / 폴백 테스트."""

    @pytest.mark.asyncio
    async def test_fallback_from_python(self):
        """DB 실패 시 Python 상수에서 직접 로드."""
        from app.services.prompt_registry import _fallback_from_python

        text, version, hash_ = _fallback_from_python("section_prompts.UNDERSTAND")
        assert len(text) > 100  # 실제 프롬프트 텍스트
        assert version == 0  # 폴백이므로 0
        assert len(hash_) == 64  # SHA-256

    @pytest.mark.asyncio
    async def test_get_active_prompt_db_fail_fallback(self):
        """DB 연결 실패 → Python 폴백."""
        with patch(
            "app.utils.supabase_client.get_async_client",
            side_effect=Exception("DB 연결 실패"),
        ):
            from app.services.prompt_registry import get_active_prompt
            text, ver, hash_ = await get_active_prompt("section_prompts.UNDERSTAND")

        assert len(text) > 0
        assert ver == 0  # 폴백


# ═══════════════════════════════════════════════════════════
# Phase 3: 프롬프트 사용 기록 + 수정 추적
# ═══════════════════════════════════════════════════════════


class TestPromptTracker:
    """record_usage → prompt_artifact_link 삽입 확인."""

    @pytest.mark.asyncio
    async def test_record_usage(self, db):
        with patch("app.utils.supabase_client.get_async_client", AsyncMock(return_value=db)):
            from app.services.prompt_tracker import record_usage
            await record_usage(
                proposal_id="prop-001",
                artifact_step="proposal_write_next",
                section_id="understand",
                prompt_id="section_prompts.UNDERSTAND",
                prompt_version=1,
                prompt_hash="abc123",
                input_tokens=5000,
                output_tokens=2000,
                duration_ms=3500,
                quality_score=85.0,
            )

        rows = db.tables.get("prompt_artifact_link", [])
        assert len(rows) == 1
        assert rows[0]["proposal_id"] == "prop-001"
        assert rows[0]["quality_score"] == 85.0


class TestHumanEditTracker:
    """record_action → human_edit_tracking 삽입 + edit_ratio 계산."""

    @pytest.mark.asyncio
    async def test_record_edit_action(self, db):
        # prompt_artifact_link에 미리 데이터 넣기 (자동 매핑용)
        db.tables["prompt_artifact_link"] = [{
            "proposal_id": "prop-001",
            "section_id": "understand",
            "prompt_id": "section_prompts.UNDERSTAND",
            "prompt_version": 1,
            "created_at": "2026-03-25T00:00:00Z",
        }]

        with patch("app.utils.supabase_client.get_async_client", AsyncMock(return_value=db)):
            from app.services.human_edit_tracker import record_action
            await record_action(
                proposal_id="prop-001",
                section_id="understand",
                action="edit",
                original="AI가 작성한 과업이해 섹션입니다.",
                edited="사람이 수정한 과업이해 섹션입니다.",
                user_id="user-001",
            )

        rows = db.tables.get("human_edit_tracking", [])
        assert len(rows) == 1
        assert rows[0]["action"] == "edit"
        assert 0.0 < rows[0]["edit_ratio"] < 1.0
        assert rows[0]["prompt_id"] == "section_prompts.UNDERSTAND"

    @pytest.mark.asyncio
    async def test_record_accept_action(self, db):
        db.tables["prompt_artifact_link"] = []

        with patch("app.utils.supabase_client.get_async_client", AsyncMock(return_value=db)):
            from app.services.human_edit_tracker import record_action
            await record_action(
                proposal_id="prop-002",
                section_id="review_strategy",
                action="accept",
            )

        rows = db.tables.get("human_edit_tracking", [])
        assert len(rows) == 1
        assert rows[0]["action"] == "accept"
        assert rows[0]["edit_ratio"] == 0.0

    @pytest.mark.asyncio
    async def test_record_reject_action(self, db):
        db.tables["prompt_artifact_link"] = []

        with patch("app.utils.supabase_client.get_async_client", AsyncMock(return_value=db)):
            from app.services.human_edit_tracker import record_action
            await record_action(
                proposal_id="prop-003",
                section_id="review_plan",
                action="reject",
            )

        rows = db.tables["human_edit_tracking"]
        assert rows[0]["edit_ratio"] == 1.0


# ═══════════════════════════════════════════════════════════
# Phase 4: 성과 메트릭 + 주의 프롬프트 감지
# ═══════════════════════════════════════════════════════════


class TestComputeEffectiveness:
    """compute_effectiveness — DB 집계 테스트."""

    @pytest.mark.asyncio
    async def test_with_data(self, db):
        # 사용 기록
        db.tables["prompt_artifact_link"] = [
            {"proposal_id": "p1", "prompt_id": "section_prompts.UNDERSTAND", "prompt_version": 1,
             "quality_score": 80, "input_tokens": 5000, "output_tokens": 2000, "duration_ms": 3000},
            {"proposal_id": "p2", "prompt_id": "section_prompts.UNDERSTAND", "prompt_version": 1,
             "quality_score": 90, "input_tokens": 4500, "output_tokens": 1800, "duration_ms": 2800},
        ]
        # 수주 결과
        db.tables["proposal_results"] = [
            {"proposal_id": "p1", "result": "won"},
            {"proposal_id": "p2", "result": "lost"},
        ]
        # 수정 기록
        db.tables["human_edit_tracking"] = [
            {"prompt_id": "section_prompts.UNDERSTAND", "edit_ratio": 0.3},
            {"prompt_id": "section_prompts.UNDERSTAND", "edit_ratio": 0.2},
        ]

        with patch("app.utils.supabase_client.get_async_client", AsyncMock(return_value=db)):
            from app.services.prompt_tracker import compute_effectiveness
            metrics = await compute_effectiveness("section_prompts.UNDERSTAND", 1)

        assert metrics["proposals_used"] == 2
        assert metrics["won"] == 1
        assert metrics["lost"] == 1
        assert metrics["win_rate"] == 50.0
        assert metrics["avg_quality_score"] == 85.0
        assert metrics["avg_edit_ratio"] == 0.25

    @pytest.mark.asyncio
    async def test_no_data(self, db):
        db.tables["prompt_artifact_link"] = []
        with patch("app.utils.supabase_client.get_async_client", AsyncMock(return_value=db)):
            from app.services.prompt_tracker import compute_effectiveness
            metrics = await compute_effectiveness("nonexistent", 1)

        assert metrics["proposals_used"] == 0


class TestAttentionPrompts:
    """check_prompts_needing_attention — 수정율 높은 프롬프트 감지."""

    @pytest.mark.asyncio
    async def test_detects_high_edit_ratio(self, db):
        # 수정율이 높은 프롬프트 데이터
        db.tables["human_edit_tracking"] = [
            {"prompt_id": "section_prompts.UNDERSTAND", "edit_ratio": 0.8},
            {"prompt_id": "section_prompts.UNDERSTAND", "edit_ratio": 0.7},
            {"prompt_id": "section_prompts.UNDERSTAND", "edit_ratio": 0.9},
            {"prompt_id": "section_prompts.UNDERSTAND", "edit_ratio": 0.6},
            # 낮은 수정율 프롬프트
            {"prompt_id": "strategy.GENERATE_PROMPT", "edit_ratio": 0.1},
            {"prompt_id": "strategy.GENERATE_PROMPT", "edit_ratio": 0.05},
            {"prompt_id": "strategy.GENERATE_PROMPT", "edit_ratio": 0.15},
            {"prompt_id": "strategy.GENERATE_PROMPT", "edit_ratio": 0.1},
        ]

        with patch("app.utils.supabase_client.get_async_client", AsyncMock(return_value=db)):
            from app.services.prompt_tracker import check_prompts_needing_attention
            result = await check_prompts_needing_attention(
                edit_ratio_threshold=0.5, min_edits=3,
            )

        assert len(result) == 1
        assert result[0]["prompt_id"] == "section_prompts.UNDERSTAND"
        assert result[0]["avg_edit_ratio"] > 0.5


# ═══════════════════════════════════════════════════════════
# Phase 5: 후보 등록 + A/B 실험
# ═══════════════════════════════════════════════════════════


class TestCandidateRegistration:
    """register_candidate → prompt_registry 후보 등록."""

    @pytest.mark.asyncio
    async def test_register(self, db):
        # 기존 active 프롬프트
        db.tables["prompt_registry"] = [{
            "prompt_id": "section_prompts.UNDERSTAND",
            "version": 1,
            "source_file": "app/prompts/section_prompts.py",
            "status": "active",
        }]

        with patch("app.utils.supabase_client.get_async_client", AsyncMock(return_value=db)):
            from app.services.prompt_registry import register_candidate
            new_ver = await register_candidate(
                "section_prompts.UNDERSTAND",
                "개선된 프롬프트 텍스트...",
                "수정율 80% — AI 자동 개선",
                created_by="evolution_engine",
            )

        assert new_ver == 2
        candidates = [r for r in db.tables["prompt_registry"] if r.get("status") == "candidate"]
        assert len(candidates) == 1
        assert candidates[0]["version"] == 2


class TestABExperiment:
    """A/B 실험 생성/라우팅/평가/승격/롤백."""

    @pytest.mark.asyncio
    async def test_experiment_routing_deterministic(self, db):
        """같은 proposal_id + experiment_id → 항상 같은 그룹."""
        db.tables["prompt_registry"] = [
            {"prompt_id": "test.PROMPT", "version": 1, "status": "active",
             "content_text": "baseline", "content_hash": "h1"},
            {"prompt_id": "test.PROMPT", "version": 2, "status": "candidate",
             "content_text": "candidate", "content_hash": "h2"},
        ]
        db.tables["prompt_ab_experiments"] = [{
            "id": "exp-001",
            "prompt_id": "test.PROMPT",
            "baseline_version": 1,
            "candidate_version": 2,
            "traffic_pct": 50,
            "status": "running",
        }]

        with patch("app.utils.supabase_client.get_async_client", AsyncMock(return_value=db)):
            from app.services.prompt_registry import get_prompt_for_experiment

            # 같은 입력 → 같은 결과 (결정론적)
            r1 = await get_prompt_for_experiment("test.PROMPT", "proposal-abc")
            r2 = await get_prompt_for_experiment("test.PROMPT", "proposal-abc")
            assert r1[0] == r2[0]  # 같은 텍스트
            assert r1[1] == r2[1]  # 같은 버전

    @pytest.mark.asyncio
    async def test_promote_candidate(self, db):
        """후보 승격: candidate → active, 기존 active → retired."""
        db.tables["prompt_registry"] = [
            {"prompt_id": "test.P", "version": 1, "status": "active"},
            {"prompt_id": "test.P", "version": 2, "status": "candidate"},
        ]
        db.tables["prompt_ab_experiments"] = [{
            "id": "exp-002",
            "prompt_id": "test.P",
            "baseline_version": 1,
            "candidate_version": 2,
            "status": "running",
        }]

        with patch("app.utils.supabase_client.get_async_client", AsyncMock(return_value=db)):
            from app.services.prompt_evolution import promote_candidate
            result = await promote_candidate("exp-002")

        assert result.get("promoted") is True
        # v1 → retired
        v1 = next(r for r in db.tables["prompt_registry"] if r["version"] == 1)
        assert v1["status"] == "retired"
        # v2 → active
        v2 = next(r for r in db.tables["prompt_registry"] if r["version"] == 2)
        assert v2["status"] == "active"
        # 실험 완료
        exp = db.tables["prompt_ab_experiments"][0]
        assert exp["status"] == "completed"

    @pytest.mark.asyncio
    async def test_rollback_experiment(self, db):
        """실험 롤백: candidate → retired, baseline 유지."""
        db.tables["prompt_registry"] = [
            {"prompt_id": "test.R", "version": 1, "status": "active"},
            {"prompt_id": "test.R", "version": 2, "status": "candidate"},
        ]
        db.tables["prompt_ab_experiments"] = [{
            "id": "exp-003",
            "prompt_id": "test.R",
            "baseline_version": 1,
            "candidate_version": 2,
            "status": "running",
        }]

        with patch("app.utils.supabase_client.get_async_client", AsyncMock(return_value=db)):
            from app.services.prompt_evolution import rollback_experiment
            result = await rollback_experiment("exp-003")

        assert result.get("rolled_back") is True
        v1 = next(r for r in db.tables["prompt_registry"] if r["version"] == 1)
        assert v1["status"] == "active"  # 변경 없음
        v2 = next(r for r in db.tables["prompt_registry"] if r["version"] == 2)
        assert v2["status"] == "retired"


# ═══════════════════════════════════════════════════════════
# Phase 6: AI 개선 제안 (Claude mock)
# ═══════════════════════════════════════════════════════════


class TestSuggestImprovements:
    """suggest_improvements — Claude API mock."""

    @pytest.mark.asyncio
    async def test_suggest(self, db):
        # 필요 데이터 세팅
        db.tables["prompt_artifact_link"] = [
            {"proposal_id": "p1", "prompt_id": "section_prompts.UNDERSTAND", "prompt_version": 1,
             "quality_score": 60, "input_tokens": 5000, "output_tokens": 2000, "duration_ms": 3000,
             "artifact_step": "proposal_write_next", "section_id": "understand",
             "created_at": "2026-03-25"},
        ]
        db.tables["proposal_results"] = [{"proposal_id": "p1", "result": "lost"}]
        db.tables["human_edit_tracking"] = [
            {"prompt_id": "section_prompts.UNDERSTAND", "action": "edit",
             "edit_ratio": 0.8, "section_id": "understand", "created_at": "2026-03-25"},
        ]
        db.tables["prompt_registry"] = [{
            "prompt_id": "section_prompts.UNDERSTAND",
            "version": 1, "status": "active",
            "content_text": "테스트 프롬프트", "content_hash": "abc",
        }]
        db.tables["feedbacks"] = [
            {"step": "section", "feedback": "근거가 부족합니다", "comments": None,
             "proposal_id": "p1", "created_at": "2026-03-25"},
        ]

        mock_ai_response = {
            "analysis": "수정율 80%로 높음, 근거 제시 부족",
            "suggestions": [
                {
                    "title": "근거 제시 지시 강화",
                    "rationale": "사람 리뷰에서 '근거 부족' 반복",
                    "key_changes": ["출처 명시 의무화", "데이터 기반 주장 강제"],
                    "prompt_text": "개선된 프롬프트 텍스트...",
                },
            ],
        }

        with patch("app.utils.supabase_client.get_async_client", AsyncMock(return_value=db)), \
             patch("app.services.claude_client.claude_generate", AsyncMock(return_value=mock_ai_response)):
            from app.services.prompt_evolution import suggest_improvements
            result = await suggest_improvements("section_prompts.UNDERSTAND")

        assert "suggestions" in result
        assert len(result["suggestions"]) == 1
        assert result["suggestions"][0]["title"] == "근거 제시 지시 강화"


# ═══════════════════════════════════════════════════════════
# Phase 7: API 엔드포인트 테스트
# ═══════════════════════════════════════════════════════════


class TestPromptEvolutionAPI:
    """routes_prompt_evolution API 엔드포인트 테스트."""

    @pytest.mark.asyncio
    async def test_dashboard(self, client):
        resp = await client.get("/api/prompts/dashboard")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "prompts" in data
        assert "total_prompts" in data

    @pytest.mark.asyncio
    async def test_list_prompts(self, client):
        resp = await client.get("/api/prompts/list?status=active")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "prompts" in data

    @pytest.mark.asyncio
    async def test_section_heatmap(self, client):
        resp = await client.get("/api/prompts/section-heatmap")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "heatmap" in data

    @pytest.mark.asyncio
    async def test_record_edit_action(self, client):
        resp = await client.post("/api/prompts/edit-action", json={
            "proposal_id": "prop-001",
            "section_id": "understand",
            "action": "edit",
            "original": "원본 텍스트",
            "edited": "수정된 텍스트",
        })
        assert resp.status_code == 200
        assert resp.json()["meta"]["message"] == "기록 완료"

    @pytest.mark.asyncio
    async def test_experiments_list(self, client):
        resp = await client.get("/api/prompts/experiments/list")
        assert resp.status_code == 200
        assert "experiments" in resp.json()["data"]


# ═══════════════════════════════════════════════════════════
# Phase 8: 전체 파이프라인 통합 시나리오
# ═══════════════════════════════════════════════════════════


class TestFullPipelineScenario:
    """
    시나리오: 프롬프트 등록 → 사용 → 수정 → 감지 → 개선 → 후보 등록 → 승격.

    실제 운영에서 수개월에 걸쳐 발생하는 과정을 단일 테스트로 시뮬레이션.
    """

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, db):
        PROMPT_ID = "section_prompts.UNDERSTAND"

        with patch("app.utils.supabase_client.get_async_client", AsyncMock(return_value=db)):

            # ── STEP 1: 레지스트리 동기화 ──
            from app.services.prompt_registry import sync_all_prompts
            sync_result = await sync_all_prompts()
            assert sync_result["synced"] + sync_result["updated"] > 0

            # 등록된 프롬프트 확인
            registry = db.tables["prompt_registry"]
            active = [r for r in registry if r["prompt_id"] == PROMPT_ID and r["status"] == "active"]
            assert len(active) == 1
            v1_text = active[0]["content_text"]
            v1_hash = active[0]["content_hash"]

            # ── STEP 2: 노드 실행 시 프롬프트 조회 ──
            from app.services.prompt_registry import get_active_prompt
            text, ver, hash_ = await get_active_prompt(PROMPT_ID)
            assert text == v1_text
            assert ver == 1

            # ── STEP 3: 사용 기록 (5개 프로젝트) ──
            from app.services.prompt_tracker import record_usage
            for i in range(5):
                await record_usage(
                    proposal_id=f"prop-{i:03d}",
                    artifact_step="proposal_write_next",
                    section_id="understand",
                    prompt_id=PROMPT_ID,
                    prompt_version=1,
                    prompt_hash=v1_hash,
                    input_tokens=5000,
                    output_tokens=2000,
                    quality_score=60.0 + i * 5,  # 60~80
                )
            assert len(db.tables["prompt_artifact_link"]) == 5

            # ── STEP 4: 사람 수정 추적 (높은 수정율) ──
            from app.services.human_edit_tracker import record_action
            for i in range(5):
                await record_action(
                    proposal_id=f"prop-{i:03d}",
                    section_id="understand",
                    action="edit",
                    original="AI 원본 " * 50,
                    edited="사람 수정 " * 50,
                )
            edits = db.tables["human_edit_tracking"]
            assert len(edits) == 5
            assert all(e["edit_ratio"] > 0 for e in edits)

            # ── STEP 5: 수주 결과 등록 ──
            db.tables["proposal_results"] = [
                {"proposal_id": "prop-000", "result": "won"},
                {"proposal_id": "prop-001", "result": "lost"},
                {"proposal_id": "prop-002", "result": "lost"},
                {"proposal_id": "prop-003", "result": "lost"},
                {"proposal_id": "prop-004", "result": "won"},
            ]

            # ── STEP 6: 성과 메트릭 계산 ──
            from app.services.prompt_tracker import compute_effectiveness
            metrics = await compute_effectiveness(PROMPT_ID, 1)
            assert metrics["proposals_used"] == 5
            assert metrics["won"] == 2
            assert metrics["lost"] == 3
            assert metrics["win_rate"] == 40.0

            # ── STEP 7: 주의 프롬프트 감지 ──
            from app.services.prompt_tracker import check_prompts_needing_attention
            attention = await check_prompts_needing_attention(
                edit_ratio_threshold=0.3, min_edits=3,
            )
            prompt_ids = [a["prompt_id"] for a in attention]
            assert PROMPT_ID in prompt_ids

            # ── STEP 8: AI 개선 제안 (mock) ──
            improved_text = v1_text + "\n\n## 추가 지시: 모든 주장에 출처를 명시하세요."
            mock_ai = {
                "analysis": "수정율 높음",
                "suggestions": [{
                    "title": "출처 명시 강화",
                    "rationale": "사람이 근거를 자주 추가",
                    "key_changes": ["출처 의무화"],
                    "prompt_text": improved_text,
                }],
            }

            with patch("app.services.claude_client.claude_generate", AsyncMock(return_value=mock_ai)):
                from app.services.prompt_evolution import suggest_improvements
                suggestions = await suggest_improvements(PROMPT_ID)
            assert len(suggestions["suggestions"]) == 1

            # ── STEP 9: 후보 등록 ──
            from app.services.prompt_evolution import create_candidate
            new_ver = await create_candidate(
                PROMPT_ID, improved_text, "출처 명시 강화",
            )
            assert new_ver == 2
            candidates = [r for r in db.tables["prompt_registry"]
                          if r["prompt_id"] == PROMPT_ID and r["status"] == "candidate"]
            assert len(candidates) == 1

            # ── STEP 10: A/B 실험 시작 ──
            from app.services.prompt_evolution import start_experiment
            exp_id = await start_experiment(
                PROMPT_ID, candidate_version=2, traffic_pct=50,
                experiment_name="출처 명시 실험",
            )
            # start_experiment이 DB에 실험 등록 (exp_id는 insert data에 id가 없으므로 None 가능)
            exps = db.tables.get("prompt_ab_experiments", [])
            assert len(exps) == 1
            assert exps[0]["status"] == "running"

            # ── STEP 11: 승격 ──
            # exp_id가 None이면 직접 세팅
            if not exp_id:
                exps[0]["id"] = "exp-test-001"
                exp_id = "exp-test-001"

            from app.services.prompt_evolution import promote_candidate
            result = await promote_candidate(exp_id)
            assert result.get("promoted") is True

            # v1 retired, v2 active 확인
            v1_rows = [r for r in db.tables["prompt_registry"]
                       if r["prompt_id"] == PROMPT_ID and r.get("version") == 1]
            v2_rows = [r for r in db.tables["prompt_registry"]
                       if r["prompt_id"] == PROMPT_ID and r.get("version") == 2]
            assert v1_rows[0]["status"] == "retired"
            assert v2_rows[0]["status"] == "active"

            # ── STEP 12: 승격 후 프롬프트 조회 → v2 반환 ──
            text2, ver2, _ = await get_active_prompt(PROMPT_ID)
            assert ver2 == 2
            assert "출처를 명시" in text2
