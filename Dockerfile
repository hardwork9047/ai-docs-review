# 任意: Docker で動かす場合の 1 サービス構成(pptx も採点できる)。render.yaml は使わない。
# Render では既定で Docker なしの Python ランタイム(render.yaml)を使う。
# frontend をビルドして FastAPI から同一オリジンで配信し、pptx→PDF 変換に LibreOffice を使う。

# ---- frontend build ----------------------------------------------------------
FROM node:22-slim AS frontend
WORKDIR /app/frontend
RUN corepack enable
COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
RUN pnpm build

# ---- backend runtime ---------------------------------------------------------
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# LibreOffice(Impress のみ)と日本語フォント。Carlito/Caladea は Calibri/Cambria の計量互換フォント
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libreoffice-impress fonts-noto-cjk fonts-crosextra-carlito fonts-crosextra-caladea \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /usr/local/bin/uv
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY backend/src ./src
RUN uv sync --frozen --no-dev

COPY --from=frontend /app/frontend/dist /app/static

ENV PATH="/app/backend/.venv/bin:$PATH" \
    REVIEW_STATIC_DIR=/app/static \
    REVIEW_SOFFICE_PATH=/usr/bin/soffice \
    HOME=/tmp

EXPOSE 10000
# Render は PORT を注入する(既定 10000)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
