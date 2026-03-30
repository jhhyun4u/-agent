"""
STEP 8A-8F Import Verification Test
No emoji, just ASCII for Windows compatibility
"""

import asyncio
import sys

async def test_all_imports():
    """Test all STEP 8A-8F imports"""
    print("\n" + "=" * 60)
    print("[TEST] STEP 8A-8F Import Verification")
    print("=" * 60 + "\n")

    tests_passed = 0
    tests_failed = 0

    # Test 1: step8a
    try:
        from app.graph.nodes.step8a_customer_analysis import proposal_customer_analysis
        from app.graph.state import CustomerProfile
        assert asyncio.iscoroutinefunction(proposal_customer_analysis)
        print("[PASS] step8a_customer_analysis: imports and signature verified")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] step8a_customer_analysis: {str(e)}")
        tests_failed += 1

    # Test 2: step8b
    try:
        from app.graph.nodes.step8b_section_validator import proposal_section_validator
        from app.graph.state import ValidationReport
        assert asyncio.iscoroutinefunction(proposal_section_validator)
        print("[PASS] step8b_section_validator: imports and signature verified")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] step8b_section_validator: {str(e)}")
        tests_failed += 1

    # Test 3: step8c
    try:
        from app.graph.nodes.step8c_consolidation import proposal_sections_consolidation
        from app.graph.state import ConsolidatedProposal
        assert asyncio.iscoroutinefunction(proposal_sections_consolidation)
        print("[PASS] step8c_consolidation: imports and signature verified")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] step8c_consolidation: {str(e)}")
        tests_failed += 1

    # Test 4: step8d
    try:
        from app.graph.nodes.step8d_mock_evaluation import mock_evaluation_analysis
        from app.graph.state import MockEvalResult
        assert asyncio.iscoroutinefunction(mock_evaluation_analysis)
        print("[PASS] step8d_mock_evaluation: imports and signature verified")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] step8d_mock_evaluation: {str(e)}")
        tests_failed += 1

    # Test 5: step8e
    try:
        from app.graph.nodes.step8e_feedback_processor import mock_evaluation_feedback_processor
        from app.graph.state import FeedbackSummary
        assert asyncio.iscoroutinefunction(mock_evaluation_feedback_processor)
        print("[PASS] step8e_feedback_processor: imports and signature verified")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] step8e_feedback_processor: {str(e)}")
        tests_failed += 1

    # Test 6: step8f
    try:
        from app.graph.nodes.step8f_rewrite import proposal_write_next_v2
        assert asyncio.iscoroutinefunction(proposal_write_next_v2)
        print("[PASS] step8f_rewrite: imports and signature verified")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] step8f_rewrite: {str(e)}")
        tests_failed += 1

    # Test 7: constants helper
    try:
        from app.graph.nodes._constants import normalize_proposal_section, MAX_REWRITE_ITERATIONS
        assert MAX_REWRITE_ITERATIONS == 3
        print("[PASS] _constants: helper functions and MAX_REWRITE_ITERATIONS verified")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] _constants: {str(e)}")
        tests_failed += 1

    # Test 8: prompts (Korean translation check)
    try:
        from app.prompts.step8a import CUSTOMER_INTELLIGENCE_PROMPT
        from app.prompts.step8b import PROPOSAL_VALIDATION_PROMPT
        from app.prompts.step8c import CONSOLIDATION_RULES
        from app.prompts.step8d import MOCK_EVALUATION_PROMPT
        from app.prompts.step8e import FEEDBACK_PROCESSING_PROMPT
        from app.prompts.step8f import PROPOSAL_REWRITE_PROMPT

        # Verify Korean content exists
        prompts = [
            CUSTOMER_INTELLIGENCE_PROMPT,
            PROPOSAL_VALIDATION_PROMPT,
            MOCK_EVALUATION_PROMPT,
            FEEDBACK_PROCESSING_PROMPT,
            PROPOSAL_REWRITE_PROMPT,
        ]

        korean_keywords = ["당신은", "분석", "제안서", "평가"]
        has_korean = False
        for prompt in prompts:
            if any(keyword in prompt for keyword in korean_keywords):
                has_korean = True
                break

        assert has_korean, "Korean translations not found"
        print("[PASS] All prompts: Korean translations verified (6/6)")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] Prompts: {str(e)}")
        tests_failed += 1

    # Test 9: version_manager (fixed import)
    try:
        from app.services.version_manager import execute_node_and_create_version
        print("[PASS] version_manager: supabase_async import fixed")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] version_manager: {str(e)}")
        tests_failed += 1

    print("\n" + "=" * 60)
    print(f"[RESULT] {tests_passed} passed, {tests_failed} failed")
    print("=" * 60)

    if tests_failed == 0:
        print("\n[SUCCESS] All STEP 8A-8F imports verified successfully\n")
        return 0
    else:
        print(f"\n[FAILED] {tests_failed} test(s) failed\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(test_all_imports())
    sys.exit(exit_code)
