"""Runtime settings, overridable via environment variables prefixed with `REVIEW_`.

例: `REVIEW_OLLAMA_URL=https://xxxx.trycloudflare.com make dev-backend`
Render では Colab 上の Ollama のトンネル URL を `REVIEW_OLLAMA_URL` に設定する。
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Ollama connection, inference parameters, and upload/serving options."""

    model_config = SettingsConfigDict(env_prefix="REVIEW_")

    ollama_url: str = "http://localhost:11434"
    # 接続先が要求する追加ヘッダー。環境変数では JSON で渡す(秘密値なのでリポジトリに書かない)
    # 例(Modal の proxy auth):
    #   REVIEW_OLLAMA_HEADERS='{"Modal-Key": "wk-...", "Modal-Secret": "ws-..."}'
    ollama_headers: dict[str, str] = {}
    model: str = "gemma4:e2b"
    temperature: float = 0.2  # 批評は再現性重視で低め
    num_ctx: int = 8192
    think: bool | None = None  # None = モデル既定。False で思考を止めて速くする
    timeout_seconds: float = 600.0
    # 接続確認の待ち時間。Modal は停止中の GPU コンテナの起動に 80 秒ほどかかるので長めにする
    health_timeout_seconds: float = 120.0

    max_pages: int = 40  # これを超えたページは採点しない
    max_upload_mb: int = 50
    image_width: int = 1024  # LLM に渡すページ画像の幅(px)
    soffice_path: str | None = None  # None なら PATH / macOS の既定位置から探す

    # 会社ルールの基準パック(YAML)。未設定なら会社ルールのチェックはしない
    standard_path: str | None = None

    static_dir: str | None = None  # ビルド済み frontend(Render の 1 サービス構成で使用)
