#!/usr/bin/env bash
# ローカル起動スクリプト。Makefile の `make dev` / `make serve` から呼ばれる。
#
#   bin/dev.sh          開発モード: backend(:8000, 自動リロード)+ Vite(:5173)を同時起動
#   bin/dev.sh serve    本番同等:   frontend をビルドし、FastAPI 1 プロセス(:8000)で画面と API を配信
#
# 接続先 Ollama は REVIEW_OLLAMA_URL で上書きできる(未設定なら settings.py の既定 = Colab トンネル)。
#   例: REVIEW_OLLAMA_URL=http://localhost:11434 bin/dev.sh
# Ctrl+C で起動したサーバをすべて止める。
set -euo pipefail

MODE="${1:-dev}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

cd "$ROOT"

for tool in uv pnpm; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "✗ $tool が見つかりません(README の「必要なツール」を参照)" >&2
        exit 1
    fi
done

if ! command -v soffice >/dev/null 2>&1 \
    && [ ! -x /Applications/LibreOffice.app/Contents/MacOS/soffice ]; then
    echo "⚠ LibreOffice が見つかりません。PDF は採点できますが、pptx は変換できません" >&2
    echo "  macOS: brew install --cask libreoffice" >&2
fi

if [ ! -d backend/.venv ] || [ ! -d frontend/node_modules ]; then
    echo "→ 依存をインストールします(make setup)"
    make setup
fi

# 子プロセスをまとめて止める(Ctrl+C・どちらかの異常終了のどちらでも)
PIDS=()
cleanup() {
    trap - EXIT INT TERM
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

case "$MODE" in
    dev)
        (cd backend && exec uv run uvicorn app.main:app --reload --port "$BACKEND_PORT") &
        PIDS+=($!)
        (cd frontend && exec pnpm dev --port "$FRONTEND_PORT" --strictPort) &
        PIDS+=($!)
        echo
        echo "✓ 画面: http://localhost:${FRONTEND_PORT}  (API: http://localhost:${BACKEND_PORT}/api/health)"
        echo "  Ctrl+C で停止"
        echo
        ;;
    serve)
        echo "→ frontend をビルドします"
        (cd frontend && pnpm build)
        (cd backend && REVIEW_STATIC_DIR="$ROOT/frontend/dist" \
            exec uv run uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT") &
        PIDS+=($!)
        echo
        echo "✓ 画面と API: http://localhost:${BACKEND_PORT}"
        echo "  Ctrl+C で停止"
        echo
        ;;
    *)
        echo "使い方: bin/dev.sh [dev|serve]" >&2
        exit 2
        ;;
esac

# どれか 1 つでも終了したら残りも止める(macOS 標準の bash 3.2 には wait -n が無いので監視ループ)
while :; do
    for pid in "${PIDS[@]}"; do
        if ! kill -0 "$pid" 2>/dev/null; then
            echo "サーバが終了しました(pid $pid)。残りを停止します" >&2
            exit 1
        fi
    done
    sleep 1
done
