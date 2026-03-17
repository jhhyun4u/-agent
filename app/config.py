from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal


class Settings(BaseSettings):
    """애플리케이션 설정 (v3.4)"""

    # API 키
    anthropic_api_key: str = ""

    # 모델 선택
    claude_model: str = "claude-sonnet-4-5-20250929"
    supervisor_model: str = "claude-sonnet-4-5-20250929"
    default_model: str = "claude-sonnet-4-5-20250929"

    # 최적화 옵션
    enable_token_optimization: bool = True
    enable_prompt_caching: bool = True
    enable_extended_thinking: bool = True
    max_retries: int = 3

    # 토큰 예산
    max_input_tokens: int = 100_000
    max_output_tokens: int = 16_000
    max_thinking_tokens: int = 10_000

    # HITL 설정
    enable_hitl: bool = True
    hitl_gates: list[str] = ["strategy", "personnel", "final"]

    # 세션 (AUTH-04)
    session_timeout_minutes: int = 30

    # 로깅 (OPS-03: 구조화 로깅)
    log_level: str = "INFO"
    log_format: Literal["text", "json"] = "text"  # 프로덕션 배포 시 "json"
    log_token_usage: bool = True

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""  # anon key (프론트엔드용)
    supabase_service_role_key: str = ""  # 서버 사이드 작업용 (RLS 우회)

    # PostgreSQL 직접 연결 (LangGraph checkpointer용)
    database_url: str = ""  # postgresql://user:pass@host:port/db

    # Azure AD (Entra ID) — §17 인증 흐름
    azure_ad_tenant_id: str = ""
    azure_ad_client_id: str = ""
    azure_ad_client_secret: str = ""

    # 프론트엔드 URL
    frontend_url: str = "http://localhost:3000"

    # CORS 허용 오리진
    cors_origins: list[str] = Field(default=["http://localhost:3000"])

    # 나라장터 API 키
    g2b_api_key: str = ""

    # Teams Webhook (기본값, 팀별 webhook은 teams 테이블)
    teams_webhook_url: str = ""

    # 파일 업로드 설정
    max_file_size_mb: int = 50
    allowed_file_extensions: list[str] = [".pdf", ".docx", ".hwp", ".hwpx", ".txt", ".pptx"]

    # 출력 디렉토리
    output_dir: str = "output"

    # 제안업체명 (HWPX 표지용)
    proposer_name: str = ""

    # 제안서 템플릿 디렉토리
    template_dir: str = "output/output template"

    # OpenAI (임베딩용)
    openai_api_key: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    def validate_required_keys(self) -> list[str]:
        """필수 API 키 누락 여부 확인. 누락된 키 이름 목록 반환."""
        missing = []
        if not self.anthropic_api_key:
            missing.append("ANTHROPIC_API_KEY")
        if not self.supabase_url:
            missing.append("SUPABASE_URL")
        if not self.supabase_key:
            missing.append("SUPABASE_KEY")
        return missing


settings = Settings()

# 시작 시 필수 키 경고
_missing = settings.validate_required_keys()
if _missing:
    import logging as _logging
    _logging.getLogger(__name__).warning(
        f"필수 환경변수 누락: {', '.join(_missing)} — 기능이 제한될 수 있습니다."
    )
