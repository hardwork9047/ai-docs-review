"""Runtime settings, overridable via environment variables prefixed with `REVIEW_`.

例: `REVIEW_MODEL=gemma3:4b make dev-backend`
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Ollama connection and inference parameters."""

    model_config = SettingsConfigDict(env_prefix="REVIEW_")

    ollama_url: str = "http://localhost:11434"
    model: str = "gemma4:e2b"
    temperature: float = 0.2  # 批評は再現性重視で低め
    num_ctx: int = 8192  # 長い資料(30枚超)は 16384 に
    max_slides: int = 40  # これを超えた分はプロンプトに含めない
    timeout_seconds: float = 600.0
