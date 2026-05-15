from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "PaperForge"
    app_version: str = "0.1.0"
    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    cors_origins: list[str] = Field(
        default=["http://localhost:3000"], alias="CORS_ORIGINS"
    )
    anthropic_api_key: str = Field(..., alias="ANTHROPIC_API_KEY")
    claude_model: str = Field(default="claude-sonnet-4-20250514", alias="CLAUDE_MODEL")
    claude_max_tokens: int = Field(default=4096, alias="CLAUDE_MAX_TOKENS")
    supabase_url: str = Field(..., alias="SUPABASE_URL")
    supabase_service_key: str = Field(..., alias="SUPABASE_SERVICE_KEY")
    max_pdf_size_mb: int = Field(default=20, alias="MAX_PDF_SIZE_MB")
    arxiv_request_timeout: int = Field(default=30, alias="ARXIV_REQUEST_TIMEOUT")

    model_config = {"env_file": ".env", "populate_by_name": True}

    @property
    def max_pdf_size_bytes(self) -> int:
        return self.max_pdf_size_mb * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache()
def get_settings() -> Settings:
    return Settings()