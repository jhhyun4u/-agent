"""
STEP 8A-8F Node Tests

Unit tests for proposal quality gate analysis nodes (8A-8B).
Test coverage: Input validation, Claude integration, versioning, error handling.
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime
from uuid import uuid4

from app.models.step8_schemas import StakeholderProfile
from app.graph.nodes.step8a_customer_analysis import proposal_customer_analysis
from app.graph.nodes.step8b_section_validator import proposal_section_validator


# ========== Fixtures ==========


@pytest.fixture
def base_state():
    """Base proposal state for testing."""
    return {
        "project_id": str(uuid4()),
        "created_by": str(uuid4()),
        "rfp_analysis": {
            "project_name": "Test Project",
            "client_name": "Test Client",
            "budget": "$500K-$1M",
            "deadline": "2026-06-30",
            "requirements": ["Requirement 1", "Requirement 2"],
        },
        "strategy": {
            "positioning": "offensive",
            "win_themes": ["Theme 1", "Theme 2"],
        },
        "kb_references": [
            {"title": "Similar Project", "summary": "Lessons learned from similar project"}
        ],
        "competitor_refs": [],
        "dynamic_sections": [
            {"title": "Executive Summary", "content": "This is the executive summary..."},
            {"title": "Technical Approach", "content": "Our technical approach..."},
        ],
        "node_errors": {},
        "artifact_versions": {},
        "active_versions": {},
    }


# ========== Node 8A Tests ==========


class TestProposalCustomerAnalysis:
    """Test Node 8A: proposal_customer_analysis"""

    @pytest.mark.asyncio
    async def test_8a_missing_rfp_analysis(self, base_state):
        """Test 8A with missing RFP analysis (should return error)."""
        state = {**base_state, "rfp_analysis": None}
        result = await proposal_customer_analysis(state)

        assert result["customer_profile"] is None
        assert "proposal_customer_analysis" in result["node_errors"]

    @pytest.mark.asyncio
    async def test_8a_valid_input(self, base_state):
        """Test 8A with valid input (mocked Claude response)."""
        customer_profile_data = {
            "client_org": "Test Client Inc",
            "market_segment": "Technology",
            "organization_size": "Enterprise",
            "decision_drivers": ["Cost", "Performance", "Support"],
            "budget_authority": "VP of Engineering approves",
            "budget_range": "$500K-$1M",
            "internal_politics": "Engineering has strong influence",
            "pain_points": ["Legacy system issues", "Performance gaps"],
            "success_metrics": ["30% cost reduction", "99.9% uptime"],
            "key_stakeholders": [
                {
                    "name": "John Doe",
                    "title": "VP of Engineering",
                    "role": "decision_maker",
                    "interests": ["Technical excellence"],
                    "influence_level": 5,
                    "contact_info": None,
                }
            ],
            "risk_perception": "Integration complexity",
            "timeline_pressure": "high",
            "procurement_process": "Formal RFP process",
            "competitive_landscape": "3-5 likely competitors",
            "prior_experience": "Used similar vendor 2 years ago",
            "created_at": datetime.utcnow().isoformat(),
        }

        with patch(
            "app.graph.nodes.step8a_customer_analysis.claude_generate",
            new_callable=AsyncMock,
        ) as mock_claude:
            with patch(
                "app.graph.nodes.step8a_customer_analysis.execute_node_and_create_version",
                new_callable=AsyncMock,
            ) as mock_version:
                mock_claude.return_value = customer_profile_data
                mock_version.return_value = (1, {"version": 1, "artifact_id": "test-id"})

                result = await proposal_customer_analysis(base_state)

                assert result["customer_profile"] is not None
                assert result["customer_profile"].client_org == "Test Client Inc"
                assert result["customer_profile"].market_segment == "Technology"
                mock_claude.assert_called_once()
                mock_version.assert_called_once()

    @pytest.mark.asyncio
    async def test_8a_claude_error_handling(self, base_state):
        """Test 8A error handling when Claude fails."""
        with patch(
            "app.graph.nodes.step8a_customer_analysis.claude_generate",
            new_callable=AsyncMock,
        ) as mock_claude:
            mock_claude.side_effect = Exception("Claude API error")
            result = await proposal_customer_analysis(base_state)

            assert result["customer_profile"] is None
            assert "proposal_customer_analysis" in result["node_errors"]
            assert "Claude API error" in result["node_errors"]["proposal_customer_analysis"]

    @pytest.mark.asyncio
    async def test_8a_kb_references_included(self, base_state):
        """Test 8A includes KB references in prompt."""
        with patch(
            "app.graph.nodes.step8a_customer_analysis.claude_generate",
            new_callable=AsyncMock,
        ) as mock_claude:
            with patch(
                "app.graph.nodes.step8a_customer_analysis.execute_node_and_create_version",
                new_callable=AsyncMock,
            ) as mock_version:
                mock_claude.return_value = {
                    "client_org": "Test",
                    "market_segment": "Tech",
                    "organization_size": "Small",
                    "decision_drivers": ["Cost"],
                    "budget_authority": "CEO",
                    "budget_range": None,
                    "internal_politics": "Flat structure",
                    "pain_points": ["Growth"],
                    "success_metrics": ["Revenue"],
                    "key_stakeholders": [],
                    "risk_perception": "None",
                    "timeline_pressure": "medium",
                    "procurement_process": "Informal",
                    "competitive_landscape": "None",
                    "prior_experience": None,
                    "created_at": datetime.utcnow().isoformat(),
                }
                mock_version.return_value = (1, {})

                await proposal_customer_analysis(base_state)

                # Verify Claude was called with KB references
                call_args = mock_claude.call_args
                assert "kb_references" in call_args[1]["prompt"] or "Similar Project" in str(
                    call_args
                )

    @pytest.mark.asyncio
    async def test_8a_stakeholder_validation(self, base_state):
        """Test 8A validates stakeholder data structure."""
        stakeholder = StakeholderProfile(
            name="Jane Smith",
            role="Budget Owner",
            influence_level="high",
            priorities=["ROI", "Risk mitigation"],
            concerns=["Integration complexity"],
        )

        assert stakeholder.name == "Jane Smith"
        assert stakeholder.influence_level == "high"
        assert stakeholder.role == "Budget Owner"


# ========== Node 8B Tests ==========


class TestProposalSectionValidator:
    """Test Node 8B: proposal_section_validator"""

    @pytest.mark.asyncio
    async def test_8b_missing_sections(self, base_state):
        """Test 8B with missing sections (should return error)."""
        state = {**base_state, "dynamic_sections": []}
        result = await proposal_section_validator(state)

        assert result["validation_report"] is None
        assert "proposal_section_validator" in result["node_errors"]

    @pytest.mark.asyncio
    async def test_8b_valid_validation(self, base_state):
        """Test 8B with valid sections and validation results."""
        validation_response = {
            "issues": [
                {
                    "severity": "major",
                    "section": "Executive Summary",
                    "category": "compliance",
                    "description": "Missing budget justification",
                    "recommendation": "Add budget breakdown",
                    "line_reference": 5,
                },
                {
                    "severity": "minor",
                    "section": "Technical Approach",
                    "category": "style",
                    "description": "Inconsistent formatting",
                    "recommendation": "Standardize bullet points",
                    "line_reference": 15,
                },
            ],
            "compliance_status": "non_compliant",
            "style_consistency": 75.0,
            "recommendations": ["Fix budget", "Improve formatting"],
            "next_steps": ["Rewrite summary", "Review style"],
        }

        with patch(
            "app.graph.nodes.step8b_section_validator.claude_generate",
            new_callable=AsyncMock,
        ) as mock_claude:
            with patch(
                "app.graph.nodes.step8b_section_validator.execute_node_and_create_version",
                new_callable=AsyncMock,
            ) as mock_version:
                mock_claude.return_value = validation_response
                mock_version.return_value = (1, {"version": 1, "artifact_id": "test-id"})

                result = await proposal_section_validator(base_state)

                assert result["validation_report"] is not None
                # pass_validation is True because there are no critical issues
                assert result["validation_report"].pass_validation is True
                assert result["validation_report"].critical_issues_count == 0
                assert result["validation_report"].major_issues_count == 1
                assert result["validation_report"].minor_issues_count == 1
                mock_claude.assert_called_once()

    @pytest.mark.asyncio
    async def test_8b_quality_score_calculation(self, base_state):
        """Test 8B calculates quality score correctly."""
        # 1 critical (-20) + 1 major (-5) + 1 minor (-1) = 100 - 26 = 74
        validation_response = {
            "issues": [
                {
                    "severity": "critical",
                    "section": "Exec",
                    "category": "compliance",
                    "description": "Missing",
                    "recommendation": "Add",
                    "line_reference": None,
                },
                {
                    "severity": "major",
                    "section": "Tech",
                    "category": "style",
                    "description": "Bad formatting",
                    "recommendation": "Fix",
                    "line_reference": None,
                },
                {
                    "severity": "minor",
                    "section": "Team",
                    "category": "clarity",
                    "description": "Unclear",
                    "recommendation": "Clarify",
                    "line_reference": None,
                },
            ],
            "compliance_status": "non_compliant",
            "style_consistency": 60.0,
            "recommendations": ["Fix critical issue"],
            "next_steps": ["Rewrite"],
        }

        with patch(
            "app.graph.nodes.step8b_section_validator.claude_generate",
            new_callable=AsyncMock,
        ) as mock_claude:
            with patch(
                "app.graph.nodes.step8b_section_validator.execute_node_and_create_version",
                new_callable=AsyncMock,
            ) as mock_version:
                mock_claude.return_value = validation_response
                mock_version.return_value = (1, {})

                result = await proposal_section_validator(base_state)

                # Quality score should be: 100 - (1*20 + 1*5 + 1*1) = 74
                assert result["validation_report"].quality_score == 74

    @pytest.mark.asyncio
    async def test_8b_pass_validation_gate(self, base_state):
        """Test 8B pass_validation when no critical issues."""
        validation_response = {
            "issues": [
                {
                    "severity": "minor",
                    "section": "Exec",
                    "category": "style",
                    "description": "Typo",
                    "recommendation": "Fix typo",
                    "line_reference": None,
                }
            ],
            "compliance_status": "compliant",
            "style_consistency": 90.0,
            "recommendations": ["Review typo"],
            "next_steps": [],
        }

        with patch(
            "app.graph.nodes.step8b_section_validator.claude_generate",
            new_callable=AsyncMock,
        ) as mock_claude:
            with patch(
                "app.graph.nodes.step8b_section_validator.execute_node_and_create_version",
                new_callable=AsyncMock,
            ) as mock_version:
                mock_claude.return_value = validation_response
                mock_version.return_value = (1, {})

                result = await proposal_section_validator(base_state)

                assert result["validation_report"].pass_validation is True

    @pytest.mark.asyncio
    async def test_8b_claude_error_handling(self, base_state):
        """Test 8B error handling when Claude fails."""
        with patch(
            "app.graph.nodes.step8b_section_validator.claude_generate",
            new_callable=AsyncMock,
        ) as mock_claude:
            mock_claude.side_effect = Exception("Claude validation failed")
            result = await proposal_section_validator(base_state)

            assert result["validation_report"] is None
            assert "proposal_section_validator" in result["node_errors"]
            assert "Claude validation failed" in result["node_errors"][
                "proposal_section_validator"
            ]

    @pytest.mark.asyncio
    async def test_8b_large_section_handling(self, base_state):
        """Test 8B handles proposals with many sections."""
        # Create state with 20 sections
        state = {
            **base_state,
            "dynamic_sections": [
                {
                    "title": f"Section {i}",
                    "content": f"Content for section {i}. " * 20,
                }
                for i in range(20)
            ],
        }

        validation_response = {
            "issues": [],
            "compliance_status": "compliant",
            "style_consistency": 85.0,
            "recommendations": [],
            "next_steps": [],
        }

        with patch(
            "app.graph.nodes.step8b_section_validator.claude_generate",
            new_callable=AsyncMock,
        ) as mock_claude:
            with patch(
                "app.graph.nodes.step8b_section_validator.execute_node_and_create_version",
                new_callable=AsyncMock,
            ) as mock_version:
                mock_claude.return_value = validation_response
                mock_version.return_value = (1, {})

                result = await proposal_section_validator(state)

                # Verify result is valid
                assert result["validation_report"] is not None
                # Verify Claude was called (sections were processed)
                mock_claude.assert_called_once()


# ========== Node 8C Tests ==========


class TestProposalSectionsConsolidation:
    """Test Node 8C: proposal_sections_consolidation"""

    @pytest.mark.asyncio
    async def test_8c_missing_sections(self, base_state):
        """Test 8C with missing sections."""
        from app.graph.nodes.step8c_consolidation import proposal_sections_consolidation

        state = {**base_state, "dynamic_sections": []}
        result = await proposal_sections_consolidation(state)

        assert result["consolidated_proposal"] is None
        assert "proposal_sections_consolidation" in result["node_errors"]

    @pytest.mark.asyncio
    async def test_8c_successful_consolidation(self, base_state):
        """Test 8C successfully consolidates sections."""
        from app.graph.nodes.step8c_consolidation import proposal_sections_consolidation

        consolidation_response = {
            "sections": [
                {
                    "section_name": "Executive Summary",
                    "content": "Consolidated executive summary...",
                    "source_sections": ["Original Summary"],
                    "word_count": 250,
                    "conflicts_resolved": 0,
                    "quality_notes": "Good summary",
                }
            ],
            "sections_merged": 2,
            "conflicts_resolved": 1,
            "quality_score": 85.0,
            "executive_summary": "Auto-generated summary",
            "issues": [],
            "style_notes": "Consistent style",
        }

        with patch(
            "app.graph.nodes.step8c_consolidation.claude_generate",
            new_callable=AsyncMock,
        ) as mock_claude:
            with patch(
                "app.graph.nodes.step8c_consolidation.execute_node_and_create_version",
                new_callable=AsyncMock,
            ) as mock_version:
                mock_claude.return_value = consolidation_response
                mock_version.return_value = (1, {})

                result = await proposal_sections_consolidation(base_state)

                assert result["consolidated_proposal"] is not None
                assert result["consolidated_proposal"].sections_merged == 2
                assert result["consolidated_proposal"].conflicts_resolved == 1


# ========== Node 8D Tests ==========


class TestMockEvaluationAnalysis:
    """Test Node 8D: mock_evaluation_analysis"""

    @pytest.mark.asyncio
    async def test_8d_missing_proposal(self, base_state):
        """Test 8D with missing proposal."""
        from app.graph.nodes.step8d_mock_evaluation import mock_evaluation_analysis

        state = {**base_state, "consolidated_proposal": None}
        result = await mock_evaluation_analysis(state)

        assert result["mock_evaluation_result"] is None
        assert "mock_evaluation_analysis" in result["node_errors"]

    @pytest.mark.asyncio
    async def test_8d_evaluation_scoring(self, base_state):
        """Test 8D performs evaluation scoring."""
        from app.graph.nodes.step8d_mock_evaluation import mock_evaluation_analysis
        from app.graph.state import ConsolidatedProposal

        base_state["consolidated_proposal"] = ConsolidatedProposal(
            proposal_id=base_state["project_id"],
            final_sections=[],
            section_count=0,
            total_word_count=5000,
            completeness_score=85,
            consistency_score=85,
            compliance_score=85,
            submission_ready=True,
            consolidated_at="2026-03-30T00:00:00",
        )

        eval_response = {
            "evaluation_method": "A",
            "evaluator_persona": "standard",
            "dimensions": [
                {
                    "criterion": "Technical Approach",
                    "max_points": 100,
                    "estimated_score": 85,
                    "feedback": "Strong approach",
                    "strengths": ["Good structure"],
                    "weaknesses": ["Add more detail"],
                }
            ],
            "estimated_rank": "competitive",
            "win_probability": 0.85,
            "strengths": ["Good structure"],
            "weaknesses": ["Minor issues"],
            "critical_gaps": [],
            "improvements": ["Add examples"],
        }

        with patch(
            "app.graph.nodes.step8d_mock_evaluation.claude_generate",
            new_callable=AsyncMock,
        ) as mock_claude:
            with patch(
                "app.graph.nodes.step8d_mock_evaluation.execute_node_and_create_version",
                new_callable=AsyncMock,
            ) as mock_version:
                mock_claude.return_value = eval_response
                mock_version.return_value = (1, {})

                result = await mock_evaluation_analysis(base_state)

                assert result["mock_evaluation_result"] is not None
                # estimated_percentage = 85/100 * 100 = 85%
                assert result["mock_evaluation_result"].estimated_percentage == 85.0


# ========== Node 8E Tests ==========


class TestMockEvaluationFeedbackProcessor:
    """Test Node 8E: mock_evaluation_feedback_processor"""

    @pytest.mark.asyncio
    async def test_8e_missing_evaluation(self, base_state):
        """Test 8E with missing evaluation result."""
        from app.graph.nodes.step8e_feedback_processor import mock_evaluation_feedback_processor

        state = {**base_state, "mock_evaluation_result": None}
        result = await mock_evaluation_feedback_processor(state)

        assert result["feedback_summary"] is None
        assert "mock_evaluation_feedback_processor" in result["node_errors"]

    @pytest.mark.asyncio
    async def test_8e_feedback_generation(self, base_state):
        """Test 8E generates feedback from evaluation."""
        from app.graph.nodes.step8e_feedback_processor import mock_evaluation_feedback_processor
        from app.graph.state import MockEvalResult, ScoreComponent
        import datetime

        base_state["mock_evaluation_result"] = MockEvalResult(
            proposal_id=base_state["project_id"],
            evaluation_method="A",
            evaluator_persona="standard",
            total_max_points=100,
            estimated_total_score=80,
            estimated_percentage=80.0,
            score_components=[
                ScoreComponent(
                    criterion="Technical",
                    max_points=100,
                    estimated_score=80,
                    feedback="Good approach",
                    strengths=["Good structure"],
                    weaknesses=["Add examples"],
                )
            ],
            estimated_rank="competitive",
            win_probability=0.80,
            key_strengths=["Good structure"],
            key_weaknesses=["Missing examples"],
            critical_gaps=[],
            improvement_recommendations=["Add examples"],
            analysis_at=datetime.datetime.utcnow().isoformat(),
        )

        feedback_response = {
            "key_findings": ["Finding 1"],
            "improvement_actions": [
                {
                    "section_id": "tech_approach",
                    "section_title": "Technical Approach",
                    "issue_category": "improvement",
                    "priority": 5,
                    "issue_description": "Add examples",
                    "rewrite_guidance": "Include concrete examples",
                    "estimated_effort": "medium",
                }
            ],
            "rewrite_strategy": "Focus on evidence",
            "affected_sections": ["Technical Approach"],
            "estimated_effort": "medium",
            "critical_effort": "medium",
            "estimated_improvement": 10,
            "estimated_new_rank": "competitive",
            "timeline": "2 days",
        }

        with patch(
            "app.graph.nodes.step8e_feedback_processor.claude_generate",
            new_callable=AsyncMock,
        ) as mock_claude:
            with patch(
                "app.graph.nodes.step8e_feedback_processor.execute_node_and_create_version",
                new_callable=AsyncMock,
            ) as mock_version:
                mock_claude.return_value = feedback_response
                mock_version.return_value = (1, {})

                result = await mock_evaluation_feedback_processor(base_state)

                assert result["feedback_summary"] is not None
                # improvement_opportunities contains the "improvement" category actions
                assert len(result["feedback_summary"].improvement_opportunities) == 1


# ========== Node 8F Tests ==========


class TestProposalWriteNextV2:
    """Test Node 8F: proposal_write_next_v2"""

    @pytest.mark.asyncio
    async def test_8f_missing_sections(self, base_state):
        """Test 8F with missing proposal sections."""
        from app.graph.nodes.step8f_rewrite import proposal_write_next_v2

        state = {**base_state, "proposal_sections": []}
        result = await proposal_write_next_v2(state)

        assert result["proposal_sections"] is None
        assert "proposal_write_next_v2" in result["node_errors"]

    @pytest.mark.asyncio
    async def test_8f_section_rewrite(self, base_state):
        """Test 8F rewrites a single section."""
        from app.graph.nodes.step8f_rewrite import proposal_write_next_v2

        base_state["proposal_sections"] = [
            {"title": "Section 1", "content": "Original content..."},
            {"title": "Section 2", "content": "Other content..."},
        ]
        base_state["current_section_index"] = 0
        base_state["rewrite_iteration_count"] = 0

        rewrite_response = "Improved section content..."

        with patch(
            "app.graph.nodes.step8f_rewrite.claude_generate",
            new_callable=AsyncMock,
        ) as mock_claude:
            with patch(
                "app.graph.nodes.step8f_rewrite.execute_node_and_create_version",
                new_callable=AsyncMock,
            ) as mock_version:
                mock_claude.return_value = rewrite_response
                mock_version.return_value = (1, {})

                result = await proposal_write_next_v2(base_state)

                assert result["proposal_sections"] is not None
                # Should have moved to next section
                assert result["current_section_index"] == 1
                # Should have incremented iteration count
                assert result["rewrite_iteration_count"] == 1

    @pytest.mark.asyncio
    async def test_8f_all_sections_complete(self, base_state):
        """Test 8F completion when all sections are processed."""
        from app.graph.nodes.step8f_rewrite import proposal_write_next_v2

        base_state["proposal_sections"] = [
            {"title": "Section 1", "content": "Content 1..."}
        ]
        base_state["current_section_index"] = 1  # Beyond last section

        result = await proposal_write_next_v2(base_state)

        # Should return sections unchanged when index is out of range
        assert result["proposal_sections"] is not None
