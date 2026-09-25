#!/usr/bin/env bash
# Render(Python ネイティブランタイム、Docker なし)のビルドコマンド。render.yaml から呼ばれる。
# backend の依存を入れ、frontend をビルドして backend から配信できるようにする。
# LibreOffice はこの環境に入らないため、Render 上では PDF のみ採点できる(pptx は PDF 化を案内)。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# pnpm 11(frontend/package.json の packageManager)は Node.js 22.13 以上が必要。
# Render のネイティブランタイムは NODE_VERSION を見て Node を用意するので export する
export NODE_VERSION="${NODE_VERSION:-24.20.0}"
MIN_NODE="22.13.0"

cd "$ROOT"

echo "→ uv"
pip install --quiet --upgrade uv

echo "→ backend 依存(本番のみ)"
(cd backend && uv sync --frozen --no-dev)

# Node が無い、または pnpm の要件(MIN_NODE)より古いときは公式バイナリを取得して使う
node_ok() {
    command -v node >/dev/null 2>&1 && node -e '
        const [a, b] = [process.versions.node, process.argv[1]].map((v) => v.split(".").map(Number));
        process.exit((a[0] - b[0] || a[1] - b[1] || a[2] - b[2]) >= 0 ? 0 : 1);
    ' "$MIN_NODE"
}
if ! node_ok; then
    echo "→ Node.js ${NODE_VERSION} を取得"
    mkdir -p "$ROOT/.render/node"
    curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz" \
        | tar -xJ -C "$ROOT/.render/node" --strip-components=1
    export PATH="$ROOT/.render/node/bin:$PATH"
fi
echo "→ node $(node -v)"

echo "→ frontend ビルド"
# Render のランタイムはグローバルに書き込めないことがあるので、pnpm の shim はリポジトリ内に置く
mkdir -p "$ROOT/.render/bin"
corepack enable --install-directory "$ROOT/.render/bin"
export PATH="$ROOT/.render/bin:$PATH"
(cd frontend && pnpm install --frozen-lockfile && pnpm build)

echo "✓ build done: backend/.venv と frontend/dist"
