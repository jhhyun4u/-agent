"""
테스트: 통합 테스트 실행

문서 API 통합 테스트를 실행하고 결과를 보고한다.
"""

import subprocess
import sys


def run_integration_tests():
    """Run integration tests with pytest"""
    print("\n" + "="*60)
    print("Integration Test Execution")
    print("="*60 + "\n")

    # Run pytest on integration tests
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/integration/test_routes_documents.py",
            "-v",
            "--tb=short",
            "-s",
        ],
        cwd=None,
    )

    return result.returncode == 0


def main():
    """Main entry point"""
    success = run_integration_tests()

    print("\n" + "="*60)
    if success:
        print("[SUCCESS] All integration tests passed!")
    else:
        print("[ERROR] Some integration tests failed")
        print("\nNext steps:")
        print("1. Review test output above")
        print("2. Fix any mock setup issues")
        print("3. Re-run tests")
    print("="*60)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
