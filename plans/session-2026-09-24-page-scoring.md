# ページ単位採点・図表評価・Render ホスティング

対話セッション(2026-09-24)。ユーザー指示を自律実施するための plan。

## 要件

1. pptx / PDF のみアップロード可
2. アップロードを PDF に統一(pptx は LibreOffice で変換)し、ページ画像を vision モデル(gemma4:e2b)に渡して図・グラフも採点
3. 1ページずつ「良い点・悪い点・修正点」を表示
4. 採点基準: 内容・フォントサイズ・フォント・図・グラフ・文字量
5. 採点結果を Markdown でダウンロード
6. render.com でホスティング。Web 版は Colab 上の Ollama(e2b)を `REVIEW_OLLAMA_URL` で使う
7. UI はモダン、白背景 + 青アクセント

## 設計判断

- **採点の分担**: 小型モデルに計測させない。
  - 決定的(PDF から計測・説明可能): フォントサイズ(12pt 未満の文字比率)/ フォント(ページ内の書体ファミリー数)/ 文字量(非空白文字数)
  - LLM(画像 + テキスト): 内容 / 図 / グラフ(該当なしは null)+ 良い点・悪い点・修正点
- **PDF ライブラリ**: pdfplumber(MIT, py.typed)。PyMuPDF は AGPL のため公開ホスティングでは避ける
- **イベント**: NDJSON `meta` → `page` | `page_error`(ページごと)→ `done`(基準別平均・判定)。1ページ失敗しても続行
- **Ollama 呼び出し**: `stream: true` で受信して連結(Cloudflare Quick Tunnel の 100 秒制限を回避)、`images` にページ JPEG
- **配信**: Render では 1 サービス(Docker: LibreOffice + Noto CJK)。FastAPI が `REVIEW_STATIC_DIR` のビルド済み frontend を同一オリジン配信。ローカル開発は従来どおり Vite proxy
- **置き換え**: `domain/slides.py` → `domain/pages.py`、`infra/pptx_reader.py` → `infra/pdf_reader.py` + `infra/converter.py`。python-pptx は不要になるので削除
- **テスト**: LibreOffice に依存するテストは偽 soffice スクリプトで配線のみ検証(CI に LibreOffice を入れない・skip しない)。PDF フィクスチャはテスト内で最小 PDF を生成

## 秘匿

実資料(`~/Documents/company/...`)と採点結果はリポジトリに入れない(scratchpad のみ)。

## デバッグ記録

- Root cause: 日本語テーマの `<a:ea typeface="">` が空(実体は `<a:font script="Jpan">`)だと、LibreOffice はテーマ書体を継承した日本語テキストの書体名を空にし、PDF が未定義フォント(/F7 等)を参照して描画・テキスト抽出とも文字化けする。変換前に a:ea を Jpan 書体で補って解消(実資料 25 ページで化け 0)。Regression test: `backend/tests/integration/test_pptx_fix.py`, `test_document.py::test_pptx_theme_fonts_are_fixed_before_conversion`
