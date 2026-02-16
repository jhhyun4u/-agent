from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """애플리케이션 설정 (v3.0 Multi-Agent)"""

    # API 키
    anthropic_api_key: str = ""

    # 모델 선택
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

    # 데이터베이스 (MCP 서버용)
    proposal_db_url: str = "postgresql://localhost/proposal_db"
    personnel_db_url: str = "postgresql://localhost/personnel_db"
    vector_db_path: str = "./data/vectors"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
