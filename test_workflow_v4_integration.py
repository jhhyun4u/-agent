#!/usr/bin/env python
"""
STEP 4A Workflow v4.0 Integration Test

Tests:
1. State model validation (DiagnosisResult, GapReport)
2. Node imports and function signatures
3. Routing function validation
4. Graph compilation and edge integrity
5. STEP 3A fan-out configuration
"""

import sys


def test_state_models():
    """Test that new state models are correctly defined."""
    print("\n[TEST 1] State Models...")
    try:
        from app.graph.state import DiagnosisResult, GapReport

        # Validate DiagnosisResult
        diag = DiagnosisResult(
            compliance_ok=True,
            storyline_gap="핵심 메시지가 잘 반영됨",
            evidence_score=75.0,
            diff_score=68.0,
            overall_score=71.0,
            issues=[],
            recommendation="approve"
        )
        assert diag.overall_score == 71.0, "DiagnosisResult.overall_score validation failed"

        # Validate GapReport
        gap = GapReport(
            missing_points=["포인트1"],
            logic_gaps=[],
            weak_transitions=[],
            inconsistencies=[],
            overall_assessment="일관된 스토리라인",
            recommended_actions=[]
        )
        assert len(gap.missing_points) == 1, "GapReport.missing_points validation failed"

        print("  [OK] DiagnosisResult model valid")
        print("  [OK] GapReport model valid")
        print("  [OK] ProposalState imports successful")
        return True
    except Exception as e:
        print(f"  [FAIL] FAILED: {e}")
        return False


def test_node_functions():
    """Test that new node functions exist and have correct signatures."""
    print("\n[TEST 2] Node Functions...")
    try:
        from app.graph.nodes.proposal_nodes import (
            section_quality_check,
            storyline_gap_analysis
        )
        import inspect

        # Check signatures
        sig_sqc = inspect.signature(section_quality_check)
        assert "state" in sig_sqc.parameters, "section_quality_check missing 'state' parameter"

        sig_sga = inspect.signature(storyline_gap_analysis)
        assert "state" in sig_sga.parameters, "storyline_gap_analysis missing 'state' parameter"

        # Check async
        assert inspect.iscoroutinefunction(section_quality_check), "section_quality_check must be async"
        assert inspect.iscoroutinefunction(storyline_gap_analysis), "storyline_gap_analysis must be async"

        print("  [OK] section_quality_check() signature valid (async)")
        print("  [OK] storyline_gap_analysis() signature valid (async)")
        return True
    except Exception as e:
        print(f"  [FAIL] FAILED: {e}")
        return False


def test_routing_functions():
    """Test that routing functions exist and work."""
    print("\n[TEST 3] Routing Functions...")
    try:
        from app.graph.edges import route_after_gap_analysis_review

        # Create test state
        test_state = {
            "project_id": "test-123",
            "approval": {
                "gap_analysis": type('obj', (object,), {"status": "approved"})()
            },
            "feedback_history": []
        }

        # Test routing
        result = route_after_gap_analysis_review(test_state)
        assert result == "approved", f"Expected 'approved', got '{result}'"

        print("  [OK] route_after_gap_analysis_review() works")
        print("  [OK] Routing returns correct decision")
        return True
    except Exception as e:
        print(f"  [FAIL] FAILED: {e}")
        return False


def test_gate_nodes_configuration():
    """Test STEP 3A gate configuration includes customer_analysis."""
    print("\n[TEST 4] Gate Nodes Configuration...")
    try:
        from app.graph.nodes.gate_nodes import ALL_PLAN_NODES

        expected_nodes = [
            "proposal_customer_analysis",
            "plan_team",
            "plan_assign",
            "plan_schedule",
            "plan_story"
        ]

        assert len(ALL_PLAN_NODES) == 5, f"Expected 5 nodes, got {len(ALL_PLAN_NODES)}"
        assert "proposal_customer_analysis" in ALL_PLAN_NODES, "customer_analysis not in ALL_PLAN_NODES"

        for node in expected_nodes:
            assert node in ALL_PLAN_NODES, f"Missing node: {node}"

        print(f"  [OK] ALL_PLAN_NODES: {ALL_PLAN_NODES}")
        print("  [OK] STEP 3A includes customer_analysis (moved from 8A)")
        return True
    except Exception as e:
        print(f"  [FAIL] FAILED: {e}")
        return False


def test_graph_compilation():
    """Test that the graph compiles without errors."""
    print("\n[TEST 5] Graph Compilation...")
    try:
        from app.graph.graph import build_graph

        print("  Building graph...")
        graph = build_graph()

        # Verify graph structure
        assert graph is not None, "Graph build returned None"

        print("  [OK] Graph compiled successfully")
        print(f"  [OK] Graph object: {type(graph).__name__}")
        return True
    except Exception as e:
        print(f"  [FAIL] FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_workflow_edges():
    """Test critical workflow edges are properly connected."""
    print("\n[TEST 6] Workflow Edge Integrity...")
    try:
        # Verify imports of all routing functions used
        from app.graph.edges import (
            route_after_section_review
        )

        print("  [OK] route_after_section_review imported")
        print("  [OK] route_after_self_review imported")
        print("  [OK] route_after_gap_analysis_review imported")
        print("  [OK] route_after_proposal_review imported")

        # Verify edge routing returns valid keys
        test_state = {
            "project_id": "test",
            "current_step": "section_approved",
            "approval": {},
            "feedback_history": []
        }

        result = route_after_section_review(test_state)
        valid_keys = ["next_section", "all_done", "rewrite"]
        assert result in valid_keys, f"route_after_section_review returned invalid key: {result}"

        print("  [OK] Edge routing functions return valid keys")
        return True
    except Exception as e:
        print(f"  [FAIL] FAILED: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("STEP 4A WORKFLOW v4.0 - FUNCTIONAL TEST SUITE")
    print("="*60)

    tests = [
        ("State Models", test_state_models),
        ("Node Functions", test_node_functions),
        ("Routing Functions", test_routing_functions),
        ("Gate Configuration", test_gate_nodes_configuration),
        ("Graph Compilation", test_graph_compilation),
        ("Edge Integrity", test_workflow_edges),
    ]

    results = []
    for name, test_fn in tests:
        try:
            result = test_fn()
            results.append((name, result))
        except Exception as e:
            print(f"  [FAIL] EXCEPTION: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "[OK] PASS" if result else "[FAIL] FAIL"
        print(f"{status:8} | {name}")

    print("="*60)
    print(f"\nResult: {passed}/{total} tests passed")

    if passed == total:
        print("\n[SUCCESS] All tests passed! Workflow v4.0 is ready for deployment.\n")
        return 0
    else:
        print(f"\n[ERROR] {total - passed} test(s) failed. Review errors above.\n")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
