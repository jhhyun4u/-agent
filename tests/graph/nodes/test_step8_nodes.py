"""
Tests for STEP 8 nodes (8A-8F).

Tests model schemas, node execution, and routing logic.
"""

import pytest

from app.models.step8_schemas import (
    CustomerProfile, ValidationReport, ConsolidatedProposal,
    MockEvaluationResult, FeedbackSummary, WriteNextV2Output,
    ValidationIssue, ConsolidatedSection,
    EvaluationDimension, ImprovementAction
)


class TestCustomerProfile:
    """Tests for 8A output model."""
    
    def test_customer_profile_creation(self):
        """Test creating a CustomerProfile."""
        profile = CustomerProfile(
            proposal_id="test-123",
            organization_name="Acme Corp",
            industry="Technology",
            decision_authority="VP of Engineering",
            decision_timeline="Q2 2026",
            budget_authority="CFO",
            budget_range_usd="$500K-$1M",
            primary_stakeholders=[],
            rfp_drivers=["Cost reduction", "Scalability"],
            success_criteria=["30% cost reduction"],
        )
        
        assert profile.proposal_id == "test-123"
        assert profile.organization_name == "Acme Corp"
        assert len(profile.rfp_drivers) == 2


class TestValidationReport:
    """Tests for 8B output model."""
    
    def test_validation_report_pass(self):
        """Test a passing validation report."""
        report = ValidationReport(
            proposal_id="test-123",
            pass_validation=True,
            quality_score=95.0,
            compliance_status="compliant",
            style_consistency=90.0,
        )
        
        assert report.pass_validation is True
        assert report.quality_score == 95.0
        assert report.critical_issues_count == 0


class TestConsolidatedProposal:
    """Tests for 8C output model."""
    
    def test_consolidated_proposal_structure(self):
        """Test creating consolidated proposal with sections."""
        section = ConsolidatedSection(
            section_name="Executive Summary",
            content="# Executive Summary\nThis is a consolidated proposal.",
            word_count=100,
        )
        
        proposal = ConsolidatedProposal(
            proposal_id="test-123",
            sections=[section],
            total_word_count=100,
            consolidation_quality=85.0,
        )
        
        assert len(proposal.sections) == 1
        assert proposal.total_word_count == 100


class TestMockEvaluationResult:
    """Tests for 8D output model."""
    
    def test_mock_evaluation_scoring(self):
        """Test mock evaluation with dimensions."""
        dimension = EvaluationDimension(
            dimension_name="Technical Approach",
            max_points=100.0,
            awarded_points=85.0,
            rationale="Strong technical approach",
        )
        
        eval_result = MockEvaluationResult(
            proposal_id="test-123",
            evaluator_type="technical",
            total_possible_points=100.0,
            total_awarded_points=85.0,
            score_percentage=85.0,
            pass_fail_recommendation="pass",
            dimensions=[dimension],
        )
        
        assert eval_result.score_percentage == 85.0
        assert len(eval_result.dimensions) == 1


class TestFeedbackSummary:
    """Tests for 8E output model."""
    
    def test_feedback_summary_with_actions(self):
        """Test feedback summary with improvement actions."""
        action = ImprovementAction(
            priority="high",
            target_section="Technical Approach",
            action="Expand technical methodology",
            expected_impact="significant",
        )
        
        summary = FeedbackSummary(
            proposal_id="test-123",
            source_evaluation_score=85.0,
            improvement_actions=[action],
            estimated_score_improvement=10.0,
        )
        
        assert summary.high_priority_count == 1
        assert summary.estimated_score_improvement == 10.0


class TestWriteNextV2Output:
    """Tests for 8F output model."""
    
    def test_write_next_v2_section(self):
        """Test rewritten section output."""
        rewrite = WriteNextV2Output(
            proposal_id="test-123",
            section_name="Technical Approach",
            section_index=0,
            content="# Improved Technical Approach\nEnhanced content here.",
            word_count=50,
            quality_improvement=15.0,
            ready_for_validation=True,
        )
        
        assert rewrite.section_name == "Technical Approach"
        assert rewrite.quality_improvement == 15.0
        assert rewrite.ready_for_validation is True


class TestPydanticValidation:
    """Tests for model validation."""
    
    def test_validation_report_invalid_severity(self):
        """Test that invalid severity is rejected."""
        with pytest.raises(ValueError):
            ValidationIssue(
                severity="invalid_severity",
                section="Test",
                category="compliance",
                description="Test issue",
                recommendation="Fix it",
            )
    
    def test_customer_profile_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValueError):
            CustomerProfile(
                proposal_id="test-123",
                organization_name="Acme Corp",
                # Missing required fields
            )
    
    def test_mock_evaluation_score_bounds(self):
        """Test score percentage bounds (0-100)."""
        eval_result = MockEvaluationResult(
            proposal_id="test-123",
            evaluator_type="technical",
            total_possible_points=100.0,
            total_awarded_points=100.0,
            score_percentage=100.0,
            pass_fail_recommendation="pass",
        )
        assert eval_result.score_percentage == 100.0
        
        with pytest.raises(ValueError):
            MockEvaluationResult(
                proposal_id="test-123",
                evaluator_type="technical",
                total_possible_points=100.0,
                total_awarded_points=100.0,
                score_percentage=150.0,  # Invalid
                pass_fail_recommendation="pass",
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
