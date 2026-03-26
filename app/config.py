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

    # 개발 모드 (인증 바이패스)
    # WARNING: 운영 환경에서는 반드시 false. is_production과 동시 활성화 시 서버 시작 거부.
    dev_mode: bool = False

    # 프로덕션 환경 플래그 (Railway/Render에서 ENVIRONMENT=production 설정)
    environment: str = "development"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in ("production", "prod")

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
    cors_origins: list[str] = Field(default=["http://localhost:3000", "http://127.0.0.1:3000"])

    # 나라장터 API 키
    g2b_api_key: str = ""

    # Teams Webhook (기본값, 팀별 webhook은 teams 테이블)
    teams_webhook_url: str = ""

    # 이메일 알림 (Microsoft Graph API)
    email_enabled: bool = False
    email_sender: str = ""  # noreply@tenopa.co.kr 또는 공유 사서함
    email_graph_scope: str = "https://graph.microsoft.com/.default"

    # 파일 업로드 설정
    max_file_size_mb: int = 50
    allowed_file_extensions: list[str] = [".pdf", ".docx", ".hwp", ".hwpx", ".txt", ".pptx"]

    # Storage 버킷
    storage_bucket_proposals: str = "proposal-files"
    storage_bucket_attachments: str = "bid-attachments"
    storage_bucket_intranet: str = "intranet-documents"

    # 인트라넷 문서 수집
    intranet_max_file_size_mb: int = 100
    intranet_max_batch_size: int = 20

    # Timeout (초)
    claude_api_timeout: int = 40
    bid_analysis_timeout: int = 45
    file_download_timeout_seconds: int = 30
    edge_function_timeout_seconds: int = 10
    webhook_timeout_seconds: int = 10
    g2b_api_timeout_seconds: int = 15
    bid_pipeline_timeout_seconds: int = 120
    heartbeat_timeout_seconds: int = 60

    # Signed URL / 캐시 TTL
    signed_url_expiry_seconds: int = 3600
    g2b_cache_ttl_hours: int = 24
    bid_fetch_cooldown_hours: int = 1
    section_lock_duration_minutes: int = 5

    # 나라장터 API 파라미터
    g2b_api_base_url: str = "https://apis.data.go.kr/1230000"
    g2b_max_retries: int = 3
    g2b_default_lookback_days: int = 14
    g2b_historical_days: int = 180

    # 출력 디렉토리
    output_dir: str = "output"

    # 자가검증 (Health Check)
    health_check_enabled: bool = True
    health_suppress_minutes: int = 30
    health_resource_warn_pct: int = 75
    health_resource_fail_pct: int = 90
    health_mv_max_hours: int = 24
    health_stale_session_hours: int = 2

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
        if not self.g2b_api_key:
            missing.append("G2B_API_KEY")
        return missing


settings = Settings()

# ── H-1 보안 가드: 프로덕션에서 DEV_MODE=true 차단 ──
if settings.is_production and settings.dev_mode:
    raise RuntimeError(
        "SECURITY: DEV_MODE=true는 프로덕션 환경(ENVIRONMENT=production)에서 사용할 수 없습니다. "
        "DEV_MODE=false로 설정하거나 ENVIRONMENT를 변경하세요."
    )

# 시작 시 필수 키 경고
_missing = settings.validate_required_keys()
if _missing:
    import logging as _logging
    _logging.getLogger(__name__).warning(
        f"필수 환경변수 누락: {', '.join(_missing)} — 기능이 제한될 수 있습니다."
    )

if settings.dev_mode:
    import logging as _logging
    _logging.getLogger(__name__).warning(
        "⚠️ DEV_MODE=true: 인증이 우회됩니다. 개발 환경에서만 사용하세요."
    )
