"""
표준 에러 코드 체계 (§12-0)

에러 프리픽스:
- AUTH_: 인증·인가
- PROP_: 프로젝트·워크플로
- WF_: 워크플로 실행
- SECT_: 섹션·편집
- KB_: Knowledge Base
- AI_: AI 서비스
- FILE_: 파일 처리
- ADMIN_: 관리자 기능
- TEAM_: 팀·초대·댓글
- BID_: 입찰·공고
- G2B_: 나라장터 외부 API
- GEN_: 범용 (리소스·일정·서식 등)
"""

from typing import Any


class TenopAPIError(Exception):
    """TENOPA 표준 API 에러 기반 클래스.

    FastAPI exception_handler에서 표준 JSON 형식으로 직렬화:
    {
        "error_code": "SECT_001",
        "message": "섹션이 다른 사용자에 의해 잠겨 있습니다.",
        "detail": { ... }
    }
    """

    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = 400,
        detail: dict[str, Any] | None = None,
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(self.message)

    def to_dict(self) -> dict:
        result = {"error_code": self.error_code, "message": self.message}
        if self.detail:
            result["detail"] = self.detail
        return result


# ── AUTH 에러 ──

class AuthTokenExpiredError(TenopAPIError):
    """AUTH_001: JWT 토큰 만료"""
    def __init__(self, detail: dict | None = None):
        super().__init__("AUTH_001", "토큰이 만료되었습니다.", 401, detail)


class AuthInsufficientRoleError(TenopAPIError):
    """AUTH_002: 역할 권한 부족"""
    def __init__(self, required_roles: list[str], current_role: str):
        super().__init__(
            "AUTH_002",
            f"권한 부족: {current_role} (필요: {', '.join(required_roles)})",
            403,
            {"required_roles": required_roles, "current_role": current_role},
        )


class AuthProjectAccessError(TenopAPIError):
    """AUTH_003: 프로젝트 접근 권한 없음"""
    def __init__(self, proposal_id: str):
        super().__init__(
            "AUTH_003", "프로젝트 접근 권한이 없습니다.", 403,
            {"proposal_id": proposal_id},
        )


# ── PROP 에러 ──

class PropStatusTransitionError(TenopAPIError):
    """PROP_001: 프로젝트 상태 전이 불가"""
    def __init__(self, current_status: str, target_status: str):
        super().__init__(
            "PROP_001",
            f"상태 전이 불가: {current_status} → {target_status}",
            409,
            {"current_status": current_status, "target_status": target_status},
        )


class PropNotFoundError(TenopAPIError):
    """PROP_002: 프로젝트 없음"""
    def __init__(self, proposal_id: str):
        super().__init__(
            "PROP_002", "프로젝트를 찾을 수 없습니다.", 404,
            {"proposal_id": proposal_id},
        )


# ── WF 에러 ──

class WFAlreadyRunningError(TenopAPIError):
    """WF_001: 워크플로 이미 실행 중"""
    def __init__(self, proposal_id: str):
        super().__init__(
            "WF_001", "워크플로가 이미 실행 중입니다.", 409,
            {"proposal_id": proposal_id},
        )


class WFResumeValidationError(TenopAPIError):
    """WF_002: resume 페이로드 검증 실패"""
    def __init__(self, errors: list[str]):
        super().__init__(
            "WF_002", "resume 요청 데이터가 유효하지 않습니다.", 422,
            {"validation_errors": errors},
        )


# ── SECT 에러 ──

class SectLockConflictError(TenopAPIError):
    """SECT_001: 섹션 잠금 충돌"""
    def __init__(self, locked_by: str, locked_at: str, expires_at: str):
        super().__init__(
            "SECT_001", "섹션이 다른 사용자에 의해 잠겨 있습니다.", 423,
            {"locked_by": locked_by, "locked_at": locked_at, "expires_at": expires_at},
        )


class SectVersionConflictError(TenopAPIError):
    """SECT_002: 섹션 버전 충돌"""
    def __init__(self, current_version: int, submitted_version: int):
        super().__init__(
            "SECT_002", "섹션 버전이 충돌합니다. 최신 버전을 확인하세요.", 409,
            {"current_version": current_version, "submitted_version": submitted_version},
        )


# ── KB 에러 ──

class KBImportValidationError(TenopAPIError):
    """KB_001: KB 임포트 데이터 검증 실패"""
    def __init__(self, error_rows: list[dict]):
        super().__init__(
            "KB_001", "KB 데이터 검증에 실패했습니다.", 422,
            {"error_rows": error_rows},
        )


# ── AI 에러 ──

# 레거시 호환
ClaudeAPIError = type("ClaudeAPIError", (Exception,), {})
FileProcessingError = type("FileProcessingError", (Exception,), {})
SessionNotFoundError = type("SessionNotFoundError", (TenopAPIError,), {
    "__init__": lambda self, session_id="": TenopAPIError.__init__(
        self, "WF_003", f"세션을 찾을 수 없습니다: {session_id}", 404,
    ),
})


class AdminAuthCreateError(TenopAPIError):
    """ADMIN_004: 사용자 Auth 계정 생성 실패"""
    def __init__(self, detail: dict | None = None):
        super().__init__("ADMIN_004", "사용자 Auth 계정 생성 실패", 500, detail)


class AdminPasswordResetError(TenopAPIError):
    """ADMIN_005: 비밀번호 초기화 실패"""
    def __init__(self, detail: dict | None = None):
        super().__init__("ADMIN_005", "비밀번호 초기화 실패", 500, detail)


class AuthPasswordChangeRequired(TenopAPIError):
    """AUTH_005: 비밀번호 변경 필요"""
    def __init__(self):
        super().__init__("AUTH_005", "비밀번호 변경이 필요합니다.", 403)


class AIServiceError(TenopAPIError):
    """AI_001: Claude API 일시 오류"""
    def __init__(self, message: str = "AI 서비스 일시 오류"):
        super().__init__("AI_001", message, 503)


class AITokenBudgetExceededError(TenopAPIError):
    """AI_002: AI 요청 토큰 예산 초과"""
    def __init__(self, budget: int, required: int):
        super().__init__(
            "AI_002", "AI 요청 토큰 예산을 초과했습니다.", 422,
            {"budget": budget, "required": required},
        )


class AITimeoutError(TenopAPIError):
    """AI_003: AI 응답 타임아웃"""
    def __init__(self, step: str):
        super().__init__(
            "AI_003", "AI 응답 시간이 초과되었습니다.", 504,
            {"step": step},
        )


# ── FILE 에러 ──

class FileSizeExceededError(TenopAPIError):
    """FILE_001: 파일 크기 초과"""
    def __init__(self, max_mb: int, actual_mb: float):
        super().__init__(
            "FILE_001", f"파일 크기 제한({max_mb}MB) 초과", 413,
            {"max_mb": max_mb, "actual_mb": actual_mb},
        )


class FileFormatError(TenopAPIError):
    """FILE_002: 지원하지 않는 파일 형식"""
    def __init__(self, extension: str, allowed: list[str]):
        super().__init__(
            "FILE_002", f"지원하지 않는 파일 형식: {extension}", 415,
            {"extension": extension, "allowed_formats": allowed},
        )


class FileNotFoundError_(TenopAPIError):
    """FILE_003: 파일 없음"""
    def __init__(self, message: str = "파일을 찾을 수 없습니다"):
        super().__init__("FILE_003", message, 404)


class FileUploadError(TenopAPIError):
    """FILE_004: 파일 업로드 실패"""
    def __init__(self, message: str = "파일 업로드에 실패했습니다"):
        super().__init__("FILE_004", message, 500)


# ── TEAM 에러 ──

class TeamNotFoundError(TenopAPIError):
    """TEAM_001: 팀 없음"""
    def __init__(self, team_id: str = ""):
        super().__init__(
            "TEAM_001", "팀을 찾을 수 없습니다.", 404,
            {"team_id": team_id} if team_id else None,
        )


class TeamAccessDeniedError(TenopAPIError):
    """TEAM_002: 팀 접근 권한 부족 (멤버/관리자)"""
    def __init__(self, message: str = "팀 멤버만 접근 가능합니다."):
        super().__init__("TEAM_002", message, 403)


class TeamInviteError(TenopAPIError):
    """TEAM_003: 초대 관련 오류 (만료, 중복, 불일치 등)"""
    def __init__(self, message: str, status_code: int = 409):
        super().__init__("TEAM_003", message, status_code)


# ── BID 에러 ──

class BidNotFoundError(TenopAPIError):
    """BID_001: 공고 없음"""
    def __init__(self, bid_no: str = ""):
        super().__init__(
            "BID_001", "공고를 찾을 수 없습니다.", 404,
            {"bid_no": bid_no} if bid_no else None,
        )


class BidValidationError(TenopAPIError):
    """BID_002: 입찰 데이터 검증 실패"""
    def __init__(self, message: str):
        super().__init__("BID_002", message, 400)


# ── G2B 에러 ──

class G2BExternalError(TenopAPIError):
    """G2B_001: 나라장터 외부 API 통신 오류"""
    def __init__(self, message: str = "외부 API 호출 중 오류가 발생했습니다."):
        super().__init__("G2B_001", message, 502)


class G2BServiceError(TenopAPIError):
    """G2B_002: 나라장터 관련 내부 처리 오류"""
    def __init__(self, message: str = "나라장터 API 호출 중 오류가 발생했습니다."):
        super().__init__("G2B_002", message, 500)


# ── GEN 범용 에러 ──

class ResourceNotFoundError(TenopAPIError):
    """GEN_001: 범용 리소스 없음 (일정, 서식, 섹션, 댓글 등)"""
    def __init__(self, resource: str, resource_id: str = ""):
        super().__init__(
            "GEN_001", f"{resource}을(를) 찾을 수 없습니다.", 404,
            {"resource": resource, "resource_id": resource_id} if resource_id else {"resource": resource},
        )


class OwnershipRequiredError(TenopAPIError):
    """GEN_002: 소유자 권한 필요 (본인만 수정/삭제)"""
    def __init__(self, message: str = "본인 리소스만 수정/삭제할 수 있습니다."):
        super().__init__("GEN_002", message, 403)


class InvalidRequestError(TenopAPIError):
    """GEN_003: 범용 잘못된 요청"""
    def __init__(self, message: str):
        super().__init__("GEN_003", message, 400)


class ConflictError(TenopAPIError):
    """GEN_004: 범용 충돌 (이미 존재, 이미 실행 중 등)"""
    def __init__(self, message: str):
        super().__init__("GEN_004", message, 409)


class InternalServiceError(TenopAPIError):
    """GEN_005: 범용 내부 서비스 오류"""
    def __init__(self, message: str = "내부 오류가 발생했습니다."):
        super().__init__("GEN_005", message, 500)


class RateLimitError(TenopAPIError):
    """GEN_006: 요청 한도 초과"""
    def __init__(self, message: str = "요청 한도를 초과했습니다."):
        super().__init__("GEN_006", message, 429)


class ExpiredError(TenopAPIError):
    """GEN_007: 만료된 리소스"""
    def __init__(self, message: str = "만료되었습니다."):
        super().__init__("GEN_007", message, 410)
