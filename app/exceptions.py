"""커스텀 예외 클래스"""


class ProposalAgentException(Exception):
    """제안서 에이전트 기본 예외"""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class FileProcessingError(ProposalAgentException):
    """파일 처리 오류"""
    pass


class RFPParsingError(ProposalAgentException):
    """RFP 파싱 오류"""
    pass


class ClaudeAPIError(ProposalAgentException):
    """Claude API 호출 오류"""
    pass


class ProposalGenerationError(ProposalAgentException):
    """제안서 생성 오류"""
    pass


class SessionNotFoundError(ProposalAgentException):
    """세션을 찾을 수 없음"""
    pass


class ValidationError(ProposalAgentException):
    """입력 검증 오류"""
    pass
