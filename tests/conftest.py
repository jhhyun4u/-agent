"""pytest 공통 설정 및 fixtures"""
import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any


@pytest.fixture(scope="session")
def event_loop():
    """세션 전체에서 사용할 이벤트 루프"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def output_dir(tmp_path) -> Path:
    """테스트용 임시 출력 디렉토리"""
    output = tmp_path / "output"
    output.mkdir(exist_ok=True)
    return output


@pytest.fixture
def mock_rfp_document() -> str:
    """테스트용 Mock RFP 문서"""
    return """제안요청서
사업명: 클라우드 기반 ERP 시스템 구축
발주기관: ABC 주식회사
예산: 5억원
기간: 6개월"""


@pytest.fixture
def skip_if_no_api_key():
    """API 키가 없으면 테스트 스킵"""
    import os
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")
