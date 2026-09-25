# 五視点レビューアプリを「部長一名視点」に作り替え、リポジトリ構成へ移植

> Note: This plan was generated retroactively from the completed changes.
> This is expected for interactive development sessions (/workon + /ship).

後続の拡張(ページ別採点・図表評価・Render ホスティング)は
`plans/session-2026-09-24-page-scoring.md` を参照。

## Goal

外部の単一ファイル構成アプリ(penta-review: FastAPI + 素の JS、5人格を並列で Ollama に投げる)を、
上司(部長)一名の視点に絞り、本リポジトリの層構成(api / domain / infra、logic / ui)と TDD 規約に沿って作り直す。

## Approach

- **domain**: スライドのプロンプト組み立て、決定的ルールチェック(表記ゆれ・半角カナ・長文・表紙)、
  pydantic の LLM 出力スキーマ(`model_json_schema()` を Ollama の `format` に渡し、同じモデルで返答を検証)、
  合否判定、LLM を Protocol ポートとして受け取るイベント生成(meta → result | error)
- **infra**: python-pptx での抽出、httpx の Ollama クライアント(health はモデル名の完全一致 or `:latest`)、
  pydantic-settings(`REVIEW_*` 環境変数)
- **api**: `/api/health`、`/api/review`(NDJSON ストリーム)。薄く保つ
- **frontend**: Three.js サンプルを撤去し、素の DOM + TypeScript。状態遷移・文言は `logic/` で vitest、
  描画は `ui/`(テスト免除層を `scene/` から `ui/` に改名し CLAUDE.md・skills を更新)
- **配信**: 開発時は Vite proxy + 2 サーバ(ユーザー指定「コード量が少ないシンプルな方法」)

## Alternatives considered

- レビュアー: (a) 5人から1人を選ぶ / (b) 総合レビュアーを新設 / (c) 実行時選択 → ユーザー選択で (a) 上司
- Three.js: 残す / 外す → 外す(ユーザー選択)
- 配信: FastAPI から同一オリジン配信 / Vite proxy → proxy(後に Render 対応で同一オリジン配信も追加)

## Scope

- 変更: backend 全層、frontend 全体、CLAUDE.md・README・code-reviewer / workon / implement / review / frontend-design skill の `scene/` 記述
- 触らない: CI 定義、Makefile のターゲット構成

## 実機検証

Google Colab 上の Ollama(gemma4:e2b)を Cloudflare Quick Tunnel 経由で接続。
Ollama が 127.0.0.1 待ち受けだと Host ヘッダ検査で 403 になるため `OLLAMA_HOST=0.0.0.0` が必要(README に記載)。
