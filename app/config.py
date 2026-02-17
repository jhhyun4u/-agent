from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # API 키
    anthropic_api_key: str = ""

    # 모델 선택 (일관된 필드명)
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

    # 로깅
    log_level: str = "INFO"
    log_token_usage: bool = True

    # Supabase 설정 (MCP 서버용)
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_role_key: str = ""  # 서버 사이드 작업용
    vector_db_path: str = "./data/vectors"
    
    # 파일 업로드 설정
    max_file_size_mb: int = 10
    allowed_file_extensions: list[str] = [".pdf", ".docx", ".hwp", ".txt"]
    
    # 출력 디렉토리
    output_dir: str = "output"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
