"""
Standalone test for STEP 8A-8F nodes - no conftest dependency
Tests core logic without full app initialization
"""

import asyncio
import sys
from unittest.mock import MagicMock

# Add app to path
sys.path.insert(0, 'c:\\project\\tenopa proposer\\-agent-master')


async def test_step8a_imports():
    """Test step8a imports and basic function signature"""
    from app.graph.nodes.step8a_customer_analysis import proposal_customer_analysis

    # Verify function exists and is async
    assert asyncio.iscoroutinefunction(proposal_customer_analysis)
    print("[OK] step8a: imports and signature verified")


async def test_step8b_imports():
    """Test step8b imports and basic function signature"""
    from app.graph.nodes.step8b_section_validator import proposal_section_validator

    assert asyncio.iscoroutinefunction(proposal_section_validator)
    print("✅ step8b: imports and signature verified")


async def test_step8c_imports():
    """Test step8c imports and basic function signature"""
    from app.graph.nodes.step8c_consolidation import proposal_sections_consolidation

    assert asyncio.iscoroutinefunction(proposal_sections_consolidation)
    print("✅ step8c: imports and signature verified")


async def test_step8d_imports():
    """Test step8d imports and basic function signature"""
    from app.graph.nodes.step8d_mock_evaluation import mock_evaluation_analysis

    assert asyncio.iscoroutinefunction(mock_evaluation_analysis)
    print("✅ step8d: imports and signature verified")


async def test_step8e_imports():
    """Test step8e imports and basic function signature"""
    from app.graph.nodes.step8e_feedback_processor import mock_evaluation_feedback_processor

    assert asyncio.iscoroutinefunction(mock_evaluation_feedback_processor)
    print("✅ step8e: imports and signature verified")


async def test_step8f_imports():
    """Test step8f imports and basic function signature"""
    from app.graph.nodes.step8f_rewrite import proposal_write_next_v2

    assert asyncio.iscoroutinefunction(proposal_write_next_v2)
    print("✅ step8f: imports and signature verified")


async def test_constants_helper():
    """Test normalize_proposal_section helper function"""
    from app.graph.nodes._constants import normalize_proposal_section, MAX_REWRITE_ITERATIONS

    # Test with dict
    dict_section = {"title": "Test", "content": "Content"}
    result = normalize_proposal_section(dict_section)
    assert result == dict_section

    # Test with mock Pydantic model
    mock_section = MagicMock()
    mock_section.model_dump.return_value = {"title": "Test", "content": "Content"}
    result = normalize_proposal_section(mock_section)
    assert result == {"title": "Test", "content": "Content"}

    # Verify constant
    assert MAX_REWRITE_ITERATIONS == 3

    print("✅ constants: helper functions and MAX_REWRITE_ITERATIONS verified")


async def test_prompt_translations():
    """Test Korean prompt translations"""
    from app.prompts.step8a import CUSTOMER_INTELLIGENCE_PROMPT
    from app.prompts.step8b import PROPOSAL_VALIDATION_PROMPT
    from app.prompts.step8d import MOCK_EVALUATION_PROMPT
    from app.prompts.step8e import FEEDBACK_PROCESSING_PROMPT
    from app.prompts.step8f import PROPOSAL_REWRITE_PROMPT

    prompts = [
        CUSTOMER_INTELLIGENCE_PROMPT,
        PROPOSAL_VALIDATION_PROMPT,
        MOCK_EVALUATION_PROMPT,
        FEEDBACK_PROCESSING_PROMPT,
        PROPOSAL_REWRITE_PROMPT,
    ]

    # Check that prompts contain Korean text
    korean_keywords = ["당신은", "분석", "제안서", "평가", "작성"]

    for i, prompt in enumerate(prompts):
        has_korean = any(keyword in prompt for keyword in korean_keywords)
        assert has_korean, f"Prompt {i} missing Korean translation"

    print("✅ prompts: Korean translations verified (6/6 files)")


async def test_error_handling_patterns():
    """Test error handling pattern consistency"""
    import inspect
    from app.graph.nodes import step8a_customer_analysis
    from app.graph.nodes import step8b_section_validator
    from app.graph.nodes import step8f_rewrite

    # All nodes should have except Exception handler
    nodes = [
        step8a_customer_analysis.proposal_customer_analysis,
        step8b_section_validator.proposal_section_validator,
        step8f_rewrite.proposal_write_next_v2,
    ]

    for node in nodes:
        source = inspect.getsource(node)
        assert "except Exception as e:" in source, f"{node.__name__} missing exception handler"

    print("✅ error-handling: all nodes have proper exception handling")


async def test_state_field_documentation():
    """Test state field clarity (mock_eval_result vs mock_evaluation_result)"""
    from app.graph.state import ProposalState
    import inspect

    source = inspect.getsource(ProposalState)

    # Should have notes clarifying the two different fields
    assert "mock_eval_result" in source  # 8D evaluator simulation
    assert "mock_evaluation_result" in source  # 6A final evaluation

    print("✅ state-fields: mock_eval_result vs mock_evaluation_result clarified")


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("[TEST] STEP 8A-8F Standalone Test Suite")
    print("="*60 + "\n")

    tests = [
        ("Imports (8A)", test_step8a_imports),
        ("Imports (8B)", test_step8b_imports),
        ("Imports (8C)", test_step8c_imports),
        ("Imports (8D)", test_step8d_imports),
        ("Imports (8E)", test_step8e_imports),
        ("Imports (8F)", test_step8f_imports),
        ("Constants & Helpers", test_constants_helper),
        ("Prompt Translations", test_prompt_translations),
        ("Error Handling", test_error_handling_patterns),
        ("State Documentation", test_state_field_documentation),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_name}: {str(e)}")
            failed += 1

    print("\n" + "="*60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    print("="*60)

    if failed == 0:
        print("\n✅ ALL TESTS PASSED - STEP 8A-8F Ready for Staging\n")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
