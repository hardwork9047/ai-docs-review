#!/usr/bin/env bash
# Render(Python ネイティブランタイム、Docker なし)のビルドコマンド。render.yaml から呼ばれる。
# backend の依存を入れ、frontend をビルドして backend から配信できるようにする。
# LibreOffice はこの環境に入らないため、Render 上では PDF のみ採点できる(pptx は PDF 化を案内)。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NODE_VERSION="${NODE_VERSION:-22.12.0}"

cd "$ROOT"

echo "→ uv"
pip install --quiet --upgrade uv

echo "→ backend 依存(本番のみ)"
(cd backend && uv sync --frozen --no-dev)

# Node が無い(または古い)ランタイムでは公式バイナリを取得して使う
if ! command -v node >/dev/null 2>&1 || [ "$(node -p 'process.versions.node.split(".")[0]')" -lt 20 ]; then
    echo "→ Node.js ${NODE_VERSION} を取得"
    mkdir -p "$ROOT/.render/node"
    curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz" \
        | tar -xJ -C "$ROOT/.render/node" --strip-components=1
    export PATH="$ROOT/.render/node/bin:$PATH"
fi
echo "→ node $(node -v)"

echo "→ frontend ビルド"
corepack enable --install-directory "$ROOT/.render/bin" 2>/dev/null \
    || corepack enable
export PATH="$ROOT/.render/bin:$PATH"
(cd frontend && pnpm install --frozen-lockfile && pnpm build)

echo "✓ build done: backend/.venv と frontend/dist"
