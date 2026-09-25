# Findings: session-2026-09-24-page-scoring

対象: `feature/boss-review`(`plans/session-2026-09-23-boss-review.md` と `plans/session-2026-09-24-page-scoring.md` の両方)

## Round 1

### Code Reviewer
- Blocking: 1
- Should Fix: 4
- Informational: 6
- Key Issues:
  - [Blocking] Colab のトンネル URL を `settings.py` の既定値・`render.yaml`・README・テストに直書き(公開リポジトリ)。
    → 対応: 未 push だった該当 2 コミットを履歴から除去(rebase)。既定値は `http://localhost:11434`、
      `render.yaml` は `sync: false` に戻し、ローカルは git 管理外の `.env` を `bin/dev.sh` が読む方式に変更(ユーザー判断)
  - [Should Fix] アップロード上限をボディ全受信後に判定 → 対応: `UploadLimitMiddleware` で本文パース前に打ち切り
    (Content-Length 超過は即 413、chunked は上限到達で切断扱い → 413)。実サーバで 60MB 送信を確認
  - [Should Fix] `plans/workflow_state.md` の削除 → PR 作成時に削除
  - [Should Fix] コンテナが root 実行 → Render は Docker を使わない構成に変更(ユーザー判断)。Dockerfile は任意構成として残置・未対応
  - [Should Fix] 宣言だけのテストが Red で最初から通っていた(Settings の env 上書き等)→ 記録のみ。今後は宣言は Red 対象にしない
- Judgment: 公開リポジトリへの秘匿 URL 流出を push 前に止めた。実害を防いだ有効な指摘

### Doc Parrot
- Divergences Found: 5(すべて gap。wrong / Fix code は 0)
- Details:
  - `load_document`: `DocumentError` / `ConversionError` を投げる条件と、pptx のテーマ書体補正が未記載 → 追記
  - `pptx_to_pdf`: `ConversionError` の条件と `timeout` の意味が未記載 → 追記
  - `fill_theme_east_asian_fonts`: zip でない入力もそのまま返すことが未記載 → 追記
  - `create_app`: 上限は `max_upload_mb` + multipart 余裕分で、厳密な上限はルート側、が不正確 → 修正
  - `UploadLimitMiddleware`: `paths` が完全一致であることが未記載 → 追記
- Judgment: 例外条件の記載漏れが中心。呼び出し側がエラー処理を書く際に効く指摘

### ユーザー判断で追加した変更(Round 1 後)
- Render を Docker なし(Python ランタイム)に変更: `render.yaml` / `bin/render-build.sh`。
  LibreOffice が無い環境では `GET /api/capabilities` が `["pdf"]` を返し、画面は PDF のみ受け付けて pptx は PDF 化を案内
- ローカル起動スクリプト `bin/dev.sh`(`make dev` / `make serve`)
