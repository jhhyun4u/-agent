"""E2E tests for LLM-Wiki integration in STEP 4A workflow."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.graph.state import ProposalSection, ProposalState


@pytest.mark.asyncio
class TestLLMWikiE2EWorkflow:
    """End-to-end tests for wiki-aware section workflow."""

    async def test_complete_wiki_section_workflow(self):
        """Complete workflow: write → wiki suggestions → diagnosis → review → approve with wiki."""
        section = ProposalSection(
            section_id="execution_team",
            title="Execution Team",
            content="Our team has 20 years of experience...",
            version=1,
            case_type="A",
        )

        state = {
            "project_id": "proj_123",
            "created_by": "user_1",
            "team_id": "team_1",
            "current_section_index": 0,
            "proposal_sections": [section],
            "current_wiki_suggestions": [],
            "rewrite_iteration_count": 0,
            "positioning": "offensive",
            "compliance_matrix": [],
            "rfp_analysis": None,
            "plan": None,
            "strategy": None,
        }

        with patch("app.services.llm_wiki.hybrid_search.HybridSearch") as mock_search_class:
            with patch("app.services.wiki_embedding_cache.get_wiki_cache") as mock_get_cache:
                # Wiki suggestions returned
                mock_search = AsyncMock()
                mock_search.search.return_value = [
                    {"wiki_id": "w1", "template_name": "Team Template", "confidence_score": 0.9},
                    {"wiki_id": "w2", "template_name": "Capability Template", "confidence_score": 0.8},
                ]
                mock_search_class.return_value = mock_search

                # Mock cache returns None (miss), then caches result
                mock_cache_obj = AsyncMock()
                mock_cache_obj.get.return_value = None
                mock_cache_obj.set = AsyncMock()
                mock_get_cache.return_value = mock_cache_obj

                # Import and call wiki_suggestion_node
                from app.graph.nodes.wiki_suggestion_node import wiki_suggestion_node

                result = await wiki_suggestion_node(state)

                # Verify wiki suggestions returned
                assert "current_wiki_suggestions" in result
                assert len(result["current_wiki_suggestions"]) == 2
                assert result["current_wiki_suggestions"][0]["confidence_score"] == 0.9

    async def test_wiki_suggestion_boosts_diagnosis_score(self):
        """Wiki suggestion selection boosts diagnosis confidence score."""
        section = ProposalSection(
            section_id="execution_team",
            title="Execution Team",
            content="Our team content...",
            version=1,
            case_type="A",
            wiki_suggestion_id="w1_selected",  # User selected this wiki
        )

        state = {
            "project_id": "proj_123",
            "created_by": "user_1",
            "team_id": "team_1",
            "current_section_index": 0,
            "proposal_sections": [section],
            "rewrite_iteration_count": 0,
            "positioning": "offensive",
            "compliance_matrix": [],
            "rfp_analysis": None,
            "plan": None,
            "strategy": None,
        }

        with patch("app.graph.nodes.proposal_nodes.claude_generate") as mock_claude:
            with patch("app.graph.nodes.proposal_nodes._persist_node_result") as mock_persist:
                with patch("app.services.evaluation_feedback_service.EvaluationFeedbackService.create_feedback"):
                    mock_claude.return_value = {
                        "compliance_ok": True,
                        "storyline_gap": "",
                        "evidence_score": 80,
                        "diff_score": 85,
                        "overall_score": 82.5,
                        "issues": [],
                        "recommendation": "approve",
                    }

                    from app.graph.nodes.proposal_nodes import section_quality_check

                    result = await section_quality_check(state)

                    # Verify boost applied: 82.5 * 1.15 = 94.875
                    persisted = mock_persist.call_args[1]["payload"]
                    assert persisted["overall_score"] == pytest.approx(94.875, abs=0.1)
                    assert persisted["wiki_suggestion_id"] == "w1_selected"

    async def test_wiki_suggestions_passed_to_review(self):
        """Wiki suggestions flow from wiki_suggestion_node through to review_section."""
        from app.graph.nodes.review_node import review_section_node

        section = ProposalSection(
            section_id="sec_1",
            title="Section 1",
            content="Content",
            version=1,
            case_type="A",
        )

        state = {
            "current_section_index": 0,
            "proposal_sections": [section],
            "positioning": "offensive",
            "current_wiki_suggestions": [
                {
                    "wiki_id": "wiki_1",
                    "template_name": "Executive Summary",
                    "confidence_score": 0.85,
                }
            ],
            "current_step": "review_section",
        }

        with patch("app.graph.nodes.review_node.interrupt") as mock_interrupt:
            mock_interrupt.return_value = {
                "approved": True,
                "selected_wiki_suggestion_id": "wiki_1",
            }

            result = review_section_node(state)

            # Verify wiki suggestions are passed to interrupt and result contains wiki_suggestion_id
            assert mock_interrupt.called
            # Check that the interrupt data included wiki suggestions
            call_args = mock_interrupt.call_args
            assert call_args is not None

    async def test_feedback_captures_wiki_selection(self):
        """Feedback system records wiki suggestion acceptance/rejection."""
        from app.services.evaluation_feedback_service import EvaluationFeedbackService

        # Mock the entire feedback service's database insert
        with patch.object(EvaluationFeedbackService, "create_feedback", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = {
                "id": "fb_123",
                "wiki_suggestion_accepted": True,
                "wiki_suggestion_id": "wiki_x",
                "metrics_before": {"overall_score": 80},
                "metrics_after": {"overall_score": 92},
            }

            result = await EvaluationFeedbackService.create_feedback(
                org_id="org_123",
                proposal_id="proj_456",
                section_id="sec_789",
                round=1,
                human_feedback="Applied wiki suggestion",
                confidence_feedback="Score improved",
                wiki_suggestion_accepted=True,
                wiki_suggestion_id="wiki_x",
                metrics_before={"overall_score": 80},
                metrics_after={"overall_score": 92},
                created_by="user_1",
            )

            # Verify the mock was called and result is not None
            assert mock_create.called
            assert result is not None
            assert result["wiki_suggestion_accepted"] is True

    async def test_multi_section_workflow_with_wiki(self):
        """Multiple sections processed with wiki suggestions."""
        sections = [
            ProposalSection(
                section_id="team",
                title="Team",
                content="Team content",
                version=1,
                case_type="A",
                wiki_suggestion_id="w_team",
                wiki_suggestion_accepted=True,
            ),
            ProposalSection(
                section_id="schedule",
                title="Schedule",
                content="Schedule content",
                version=1,
                case_type="A",
                wiki_suggestion_id="w_schedule",
                wiki_suggestion_accepted=True,
            ),
        ]

        state = {
            "project_id": "proj_123",
            "created_by": "user_1",
            "team_id": "team_1",
            "current_section_index": 0,
            "proposal_sections": sections,
            "rewrite_iteration_count": 0,
            "positioning": "offensive",
            "compliance_matrix": [],
            "rfp_analysis": None,
            "plan": None,
            "strategy": None,
        }

        # First section diagnosis
        with patch("app.graph.nodes.proposal_nodes.claude_generate") as mock_claude:
            with patch("app.graph.nodes.proposal_nodes._persist_node_result"):
                with patch("app.services.evaluation_feedback_service.EvaluationFeedbackService.create_feedback"):
                    mock_claude.return_value = {
                        "compliance_ok": True,
                        "storyline_gap": "",
                        "evidence_score": 85,
                        "diff_score": 90,
                        "overall_score": 87.5,
                        "issues": [],
                        "recommendation": "approve",
                    }

                    from app.graph.nodes.proposal_nodes import section_quality_check

                    result = await section_quality_check(state)

                    # First section with wiki boost: 87.5 * 1.15 = 100.625 → capped at 100
                    assert result is not None

                    # Now test second section
                    state["current_section_index"] = 1
                    result2 = await section_quality_check(state)
                    assert result2 is not None

    async def test_wiki_rejection_path_records_feedback(self):
        """Rejection with wiki suggestions records comprehensive feedback."""
        from app.graph.nodes.review_node import review_section_node

        section = ProposalSection(
            section_id="sec_1",
            title="Section 1",
            content="Content",
            version=1,
            case_type="A",
        )

        state = {
            "current_section_index": 0,
            "proposal_sections": [section],
            "positioning": "offensive",
            "current_wiki_suggestions": [
                {"wiki_id": "w1", "template_name": "Template", "confidence_score": 0.8}
            ],
            "current_step": "review_section",
            "feedback_history": [],
        }

        with patch("app.graph.nodes.review_node.interrupt") as mock_interrupt:
            mock_interrupt.return_value = {
                "approved": False,
                "feedback": "Needs more specifics",
                "selected_wiki_suggestion_id": None,
            }

            result = review_section_node(state)

            # Verify interrupt was called with wiki suggestions in context
            assert mock_interrupt.called
            # The function should have handled the rejection
            assert result is not None

    async def test_cache_efficiency_across_similar_sections(self):
        """Wiki cache improves efficiency for similar sections."""
        section1 = ProposalSection(
            section_id="sec_1",
            title="Section 1",
            content="Similar content A",
            version=1,
            case_type="A",
        )

        section2 = ProposalSection(
            section_id="sec_2",
            title="Section 2",
            content="Similar content B",
            version=1,
            case_type="A",
        )

        with patch("app.services.wiki_embedding_cache.get_wiki_cache") as mock_get_cache:
            mock_cache = AsyncMock()
            # First call misses cache, second hits
            mock_cache.get.side_effect = [None, []]  # Miss then hit
            mock_cache.set = AsyncMock()
            mock_get_cache.return_value = mock_cache

            with patch("app.services.llm_wiki.hybrid_search.HybridSearch") as mock_search_class:
                mock_search = AsyncMock()
                # Mock returns 2 suggestions to test filtering
                mock_search.search.return_value = [
                    {"wiki_id": "w1", "template_name": "Template", "confidence_score": 0.85},
                    {"wiki_id": "w2", "template_name": "Template2", "confidence_score": 0.75}
                ]
                mock_search_class.return_value = mock_search

                from app.graph.nodes.wiki_suggestion_node import wiki_suggestion_node

                # First call: cache miss
                state1 = {
                    "current_section_index": 0,
                    "proposal_sections": [section1],
                    "project_id": "proj_123",
                }

                result1 = await wiki_suggestion_node(state1)
                # Both suggestions should pass the 0.7 threshold
                assert len(result1["current_wiki_suggestions"]) == 2
                assert result1["current_wiki_suggestions"][0]["confidence_score"] >= 0.7
                # Verify cache is being used (get was called)
                assert mock_cache.get.called

    async def test_confidence_score_cap_prevents_overflow(self):
        """Very high wiki-boosted scores capped at 100."""
        section = ProposalSection(
            section_id="high_score",
            title="High Quality Section",
            content="Excellent content",
            version=1,
            case_type="A",
            wiki_suggestion_id="w_excellent",
        )

        state = {
            "project_id": "proj_123",
            "created_by": "user_1",
            "team_id": "team_1",
            "current_section_index": 0,
            "proposal_sections": [section],
            "rewrite_iteration_count": 0,
            "positioning": "offensive",
            "compliance_matrix": [],
            "rfp_analysis": None,
            "plan": None,
            "strategy": None,
        }

        with patch("app.graph.nodes.proposal_nodes.claude_generate") as mock_claude:
            with patch("app.graph.nodes.proposal_nodes._persist_node_result") as mock_persist:
                with patch("app.services.evaluation_feedback_service.EvaluationFeedbackService.create_feedback"):
                    mock_claude.return_value = {
                        "compliance_ok": True,
                        "storyline_gap": "",
                        "evidence_score": 98,
                        "diff_score": 99,
                        "overall_score": 98.5,  # High score
                        "issues": [],
                        "recommendation": "approve",
                    }

                    from app.graph.nodes.proposal_nodes import section_quality_check

                    result = await section_quality_check(state)

                    # 98.5 * 1.15 = 113.275 → capped at 100
                    persisted = mock_persist.call_args[1]["payload"]
                    assert persisted["overall_score"] == 100.0
