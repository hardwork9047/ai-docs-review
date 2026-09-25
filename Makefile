# 統一エントリポイント。skills・CI・人間はすべてこの Makefile 経由でコマンドを実行する。
# スタックを変更する場合はここを書き換えれば skills 側の修正は不要。

.PHONY: setup test test-backend test-frontend lint format typecheck check dev serve dev-backend dev-frontend

## セットアップ ---------------------------------------------------------------

setup: ## 依存関係を全部インストール
	cd backend && uv sync
	cd frontend && pnpm install

## テスト ---------------------------------------------------------------------

test: test-backend test-frontend ## 全テスト(カバレッジ閾値込み)

test-backend:
	cd backend && uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80

test-frontend:
	cd frontend && pnpm test

## 品質ゲート -----------------------------------------------------------------

lint:
	cd backend && uv run ruff check src tests && uv run ruff format --check src tests

format:
	cd backend && uv run ruff check --fix src tests && uv run ruff format src tests

typecheck:
	cd backend && uv run mypy src
	cd frontend && pnpm typecheck

check: lint typecheck test ## push 前に必ず通すフルゲート

## 開発サーバ -----------------------------------------------------------------

dev: ## backend + frontend を同時起動(画面 http://localhost:5173、Ctrl+C で両方停止)
	bin/dev.sh dev

serve: ## frontend をビルドして FastAPI 1 プロセスで配信(Render と同じ構成、http://localhost:8000)
	bin/dev.sh serve

dev-backend:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && pnpm dev
