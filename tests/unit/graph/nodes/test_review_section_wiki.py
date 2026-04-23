"""Unit tests for wiki-aware review guidance in review_section_node."""
import pytest
from unittest.mock import patch, MagicMock
from langgraph.types import Interrupt
from app.graph.state import ProposalSection
from app.graph.nodes.review_node import review_section_node, _build_wiki_review_guidance


class TestWikiReviewGuidance:
    """Test wiki review guidance builder."""

    def test_empty_suggestions_returns_empty_string(self):
        """Empty suggestions list returns empty guidance."""
        guidance = _build_wiki_review_guidance([])
        assert guidance == ""

    def test_single_suggestion_guidance(self):
        """Guidance for single suggestion includes title and confidence."""
        suggestions = [
            {
                "wiki_id": "wiki_1",
                "template_name": "Executive Summary Template",
                "confidence_score": 0.85,
            }
        ]
        guidance = _build_wiki_review_guidance(suggestions)

        assert "Wiki 제안 활용" in guidance
        assert "Executive Summary Template" in guidance
        assert "85%" in guidance
        assert "wiki_1" in guidance

    def test_multiple_suggestions_guidance(self):
        """Guidance includes all suggestions with confidence scores."""
        suggestions = [
            {"wiki_id": "w1", "template_name": "Template 1", "confidence_score": 0.9},
            {"wiki_id": "w2", "template_name": "Template 2", "confidence_score": 0.75},
            {"wiki_id": "w3", "template_name": "Template 3", "confidence_score": 0.65},
        ]
        guidance = _build_wiki_review_guidance(suggestions)

        assert "Template 1" in guidance
        assert "Template 2" in guidance
        assert "Template 3" in guidance
        assert "90%" in guidance
        assert "75%" in guidance
        assert "65%" in guidance

    def test_guidance_includes_tips(self):
        """Guidance includes usage tips."""
        suggestions = [
            {"wiki_id": "w1", "template_name": "Template", "confidence_score": 0.8}
        ]
        guidance = _build_wiki_review_guidance(suggestions)

        assert "💡 Tips:" in guidance
        assert "+15% 신뢰도 부스트" in guidance


class TestReviewSectionWikiAware:
    """Test wiki-aware enhancements in review_section_node."""

    @patch("app.graph.nodes.review_node.interrupt")
    @patch("app.graph.nodes.review_node._get_sections_to_write")
    def test_wiki_suggestions_included_in_interrupt(self, mock_get_sections, mock_interrupt):
        """Wiki suggestions are included in interrupt data when available."""
        mock_get_sections.return_value = ["sec_1", "sec_2"]

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
                    "template_name": "Template 1",
                    "confidence_score": 0.85,
                }
            ],
        }

        # Mock interrupt to capture data
        mock_interrupt.return_value = {"approved": True}

        review_section_node(state)

        # Verify interrupt was called with wiki suggestions
        mock_interrupt.assert_called_once()
        interrupt_data = mock_interrupt.call_args[0][0]

        assert "wiki_suggestions" in interrupt_data
        assert interrupt_data["wiki_suggestion_enabled"] is True
        assert len(interrupt_data["wiki_suggestions"]) == 1

    @patch("app.graph.nodes.review_node.interrupt")
    @patch("app.graph.nodes.review_node._get_sections_to_write")
    def test_no_wiki_suggestions_no_guidance(self, mock_get_sections, mock_interrupt):
        """No wiki guidance when suggestions are empty."""
        mock_get_sections.return_value = ["sec_1"]

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
            "current_wiki_suggestions": [],
        }

        mock_interrupt.return_value = {"approved": True}

        review_section_node(state)

        interrupt_data = mock_interrupt.call_args[0][0]

        assert "wiki_suggestions" not in interrupt_data
        assert "wiki_guidance" not in interrupt_data

    @patch("app.graph.nodes.review_node.interrupt")
    @patch("app.graph.nodes.review_node._get_sections_to_write")
    @patch("app.graph.nodes.review_node._auto_register_to_content_library")
    def test_selected_wiki_suggestion_saved_on_approval(
        self, mock_register, mock_get_sections, mock_interrupt
    ):
        """Selected wiki suggestion is saved when section is approved."""
        mock_get_sections.return_value = ["sec_1", "sec_2"]

        section = ProposalSection(
            section_id="sec_1",
            title="Section 1",
            content="Content",
            version=1,
            case_type="A",
            wiki_suggestion_id=None,
        )

        state = {
            "current_section_index": 0,
            "proposal_sections": [section],
            "positioning": "offensive",
            "current_wiki_suggestions": [
                {"wiki_id": "wiki_selected", "template_name": "Selected Template", "confidence_score": 0.9}
            ],
        }

        # User approves and selects wiki suggestion
        mock_interrupt.return_value = {
            "approved": True,
            "selected_wiki_suggestion_id": "wiki_selected",
        }

        result = review_section_node(state)

        # Verify wiki_suggestion_id is in result
        assert result.get("wiki_suggestion_id") == "wiki_selected"
        assert result.get("current_section_index") == 1

    @patch("app.graph.nodes.review_node.interrupt")
    @patch("app.graph.nodes.review_node._get_sections_to_write")
    @patch("app.graph.nodes.review_node._auto_register_to_content_library")
    def test_rejection_includes_wiki_suggestion_feedback(
        self, mock_register, mock_get_sections, mock_interrupt
    ):
        """Rejection feedback includes wiki suggestion review flag."""
        mock_get_sections.return_value = ["sec_1"]

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
                {"wiki_id": "wiki_1", "template_name": "Template", "confidence_score": 0.8}
            ],
        }

        # User rejects with feedback
        mock_interrupt.return_value = {
            "approved": False,
            "feedback": "Please revise",
            "selected_wiki_suggestion_id": None,
        }

        result = review_section_node(state)

        # Verify feedback includes wiki suggestion info
        feedback_entry = result["feedback_history"][0]
        assert feedback_entry["wiki_suggestion_reviewed"] is True
        assert feedback_entry["selected_wiki_id"] is None

    @patch("app.graph.nodes.review_node.interrupt")
    @patch("app.graph.nodes.review_node._get_sections_to_write")
    @patch("app.graph.nodes.review_node._auto_register_to_content_library")
    def test_last_section_approval_with_wiki(
        self, mock_register, mock_get_sections, mock_interrupt
    ):
        """Last section approval with wiki suggestion returns sections_complete."""
        mock_get_sections.return_value = ["sec_1"]

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
                {"wiki_id": "wiki_1", "template_name": "Template", "confidence_score": 0.8}
            ],
        }

        mock_interrupt.return_value = {
            "approved": True,
            "selected_wiki_suggestion_id": "wiki_1",
        }

        result = review_section_node(state)

        assert result["current_step"] == "sections_complete"
        assert result["wiki_suggestion_id"] == "wiki_1"
        assert result["current_section_index"] == 1

    @patch("app.graph.nodes.review_node.interrupt")
    @patch("app.graph.nodes.review_node._get_sections_to_write")
    @patch("app.graph.nodes.review_node._auto_register_to_content_library")
    def test_mid_section_approval_advances_index(
        self, mock_register, mock_get_sections, mock_interrupt
    ):
        """Mid-section approval advances current_section_index."""
        mock_get_sections.return_value = ["sec_1", "sec_2", "sec_3"]

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
            "current_wiki_suggestions": [],
        }

        mock_interrupt.return_value = {"approved": True}

        result = review_section_node(state)

        assert result["current_step"] == "section_approved"
        assert result["current_section_index"] == 1

    @patch("app.graph.nodes.review_node.interrupt")
    @patch("app.graph.nodes.review_node._get_sections_to_write")
    def test_wiki_guidance_in_interrupt_data(self, mock_get_sections, mock_interrupt):
        """Wiki guidance is properly included in interrupt data."""
        mock_get_sections.return_value = ["sec_1"]

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
                    "wiki_id": "w1",
                    "template_name": "Template 1",
                    "confidence_score": 0.85,
                },
                {
                    "wiki_id": "w2",
                    "template_name": "Template 2",
                    "confidence_score": 0.7,
                },
            ],
        }

        mock_interrupt.return_value = {"approved": True}

        review_section_node(state)

        interrupt_data = mock_interrupt.call_args[0][0]

        # Verify guidance includes all templates
        guidance = interrupt_data.get("wiki_guidance", "")
        assert "Template 1" in guidance
        assert "Template 2" in guidance
        assert "85%" in guidance
        assert "70%" in guidance

    @patch("app.graph.nodes.review_node.interrupt")
    @patch("app.graph.nodes.review_node._get_sections_to_write")
    def test_rejection_without_wiki_suggestion(self, mock_get_sections, mock_interrupt):
        """Rejection without wiki suggestions still records feedback."""
        mock_get_sections.return_value = ["sec_1"]

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
            "current_wiki_suggestions": [],
        }

        mock_interrupt.return_value = {
            "approved": False,
            "feedback": "Needs revision",
        }

        result = review_section_node(state)

        assert result["current_step"] == "section_rejected"
        feedback_entry = result["feedback_history"][0]
        assert feedback_entry["wiki_suggestion_reviewed"] is False
        assert feedback_entry["feedback"] == "Needs revision"

    @patch("app.graph.nodes.review_node.interrupt")
    @patch("app.graph.nodes.review_node._get_sections_to_write")
    @patch("app.graph.nodes.review_node._auto_register_to_content_library")
    def test_approval_without_selecting_wiki(
        self, mock_register, mock_get_sections, mock_interrupt
    ):
        """Approval without selecting wiki suggestion still advances."""
        mock_get_sections.return_value = ["sec_1", "sec_2"]

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
                {"wiki_id": "wiki_1", "template_name": "Template", "confidence_score": 0.8}
            ],
        }

        # Approve without selecting wiki suggestion
        mock_interrupt.return_value = {
            "approved": True,
            "selected_wiki_suggestion_id": None,
        }

        result = review_section_node(state)

        assert result["current_step"] == "section_approved"
        assert result["current_section_index"] == 1
        assert "wiki_suggestion_id" not in result
