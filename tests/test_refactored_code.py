"""리팩토링된 코드 테스트"""

import pytest
from pathlib import Path

from app.config import settings
from app.exceptions import FileProcessingError, ClaudeAPIError
from app.utils import extract_json_from_response, validate_file_type
from app.services.session_manager import session_manager, SessionNotFoundError


class TestUtils:
    """유틸리티 함수 테스트"""

    def test_validate_file_type(self):
        """파일 타입 검증 테스트"""
        assert validate_file_type("test.pdf") is True
        assert validate_file_type("test.docx") is True
        assert validate_file_type("test.txt") is True
        assert validate_file_type("test.hwp") is True
        assert validate_file_type("test.exe") is False
        assert validate_file_type("test.jpg") is False

    def test_extract_json_from_response(self):
        """JSON 추출 테스트"""
        # JSON 코드 블록이 있는 경우
        response = '```json\n{"key": "value"}\n```'
        result = extract_json_from_response(response)
        assert result == {"key": "value"}

        # JSON만 있는 경우
        response = '{"key": "value"}'
        result = extract_json_from_response(response)
        assert result == {"key": "value"}

    def test_extract_json_invalid(self):
        """잘못된 JSON 추출 테스트"""
        with pytest.raises(ClaudeAPIError):
            extract_json_from_response("invalid json")


class TestSessionManager:
    """세션 관리자 테스트"""

    def test_create_session(self):
        """세션 생성 테스트"""
        session = session_manager.create_session(
            proposal_id="test-001",
            initial_data={"status": "initialized"},
            session_type="v3"
        )

        assert session["proposal_id"] == "test-001"
        assert session["status"] == "initialized"
        assert session["session_type"] == "v3"
        assert "created_at" in session
        assert "updated_at" in session

    def test_get_session(self):
        """세션 조회 테스트"""
        # 세션 생성
        session_manager.create_session(
            proposal_id="test-002",
            initial_data={"custom_field": "test_value"},
            session_type="v3"
        )

        # 세션 조회
        session = session_manager.get_session("test-002")
        assert session["proposal_id"] == "test-002"
        assert session["status"] == "initialized"  # 자동 설정됨
        assert session["custom_field"] == "test_value"

    def test_get_nonexistent_session(self):
        """존재하지 않는 세션 조회 테스트"""
        with pytest.raises(SessionNotFoundError):
            session_manager.get_session("nonexistent-id")

    def test_update_session(self):
        """세션 업데이트 테스트"""
        session_manager.create_session(
            proposal_id="test-003",
            initial_data={"status": "initialized"},
            session_type="v3"
        )

        updated = session_manager.update_session(
            "test-003",
            {"status": "completed", "result": "success"}
        )

        assert updated["status"] == "completed"
        assert updated["result"] == "success"

    def test_delete_session(self):
        """세션 삭제 테스트"""
        session_manager.create_session(
            proposal_id="test-004",
            initial_data={},
            session_type="v3"
        )

        assert session_manager.session_exists("test-004") is True

        session_manager.delete_session("test-004")

        assert session_manager.session_exists("test-004") is False

    def test_list_sessions(self):
        """세션 목록 조회 테스트"""
        # 테스트용 세션 생성
        session_manager.create_session("test-list-1", {}, "v3")
        session_manager.create_session("test-list-2", {}, "v3.1")

        # 전체 목록
        all_sessions = session_manager.list_sessions()
        assert "test-list-1" in all_sessions
        assert "test-list-2" in all_sessions

        # 타입별 필터링
        v3_sessions = session_manager.list_sessions(session_type="v3")
        assert "test-list-1" in v3_sessions
        assert "test-list-2" not in v3_sessions

    def test_session_count(self):
        """세션 개수 조회 테스트"""
        initial_count = session_manager.get_session_count()

        session_manager.create_session("test-count-1", {}, "v3")
        session_manager.create_session("test-count-2", {}, "v3")

        assert session_manager.get_session_count() == initial_count + 2
        assert session_manager.get_session_count("v3") >= 2


class TestConfig:
    """설정 테스트"""

    def test_config_fields(self):
        """설정 필드 존재 확인"""
        assert hasattr(settings, "claude_model")
        assert hasattr(settings, "supervisor_model")
        assert hasattr(settings, "default_model")
        assert hasattr(settings, "max_file_size_mb")
        assert hasattr(settings, "allowed_file_extensions")
        assert hasattr(settings, "output_dir")

    def test_config_values(self):
        """설정 값 확인"""
        assert isinstance(settings.allowed_file_extensions, list)
        assert ".pdf" in settings.allowed_file_extensions
        assert ".docx" in settings.allowed_file_extensions
        assert settings.max_file_size_mb > 0


class TestExceptions:
    """예외 클래스 테스트"""

    def test_file_processing_error(self):
        """파일 처리 예외 테스트"""
        error = FileProcessingError(
            "파일을 읽을 수 없습니다",
            details={"path": "/test/file.pdf"}
        )

        assert error.message == "파일을 읽을 수 없습니다"
        assert error.details["path"] == "/test/file.pdf"

    def test_session_not_found_error(self):
        """세션 없음 예외 테스트"""
        error = SessionNotFoundError(
            "세션을 찾을 수 없습니다",
            details={"proposal_id": "test-123"}
        )

        assert error.message == "세션을 찾을 수 없습니다"
        assert error.details["proposal_id"] == "test-123"


# 테스트 정리 (각 테스트 후 세션 정리)
@pytest.fixture(autouse=True)
def cleanup_sessions():
    """각 테스트 후 생성된 세션 정리"""
    yield
    # 테스트용 세션 정리
    test_ids = [k for k in session_manager._sessions.keys() if k.startswith("test-")]
    for test_id in test_ids:
        try:
            session_manager.delete_session(test_id)
        except SessionNotFoundError:
            pass
