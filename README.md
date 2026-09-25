# 部長レビュー(ai-docs-review)

提出前の資料(**.pptx / .pdf**)を、**多忙な部長の視点**で 1 ページずつ採点する Web アプリ。
LLM はローカルまたは Google Colab 上の Ollama(`gemma4:e2b`、vision 対応)を使う。

- **ページ別の採点**: 各ページに 6 基準のスコアと「良い点・悪い点・修正点」
  | 基準 | 採点者 | 方法 |
  |---|---|---|
  | 内容 | LLM | ページ画像 + テキスト + 資料全体の構成から判断 |
  | 図 / グラフ | LLM | ページ画像を見て判断。無いページは対象外(–) |
  | フォントサイズ | 計測 | 14pt 未満の文字の割合(PDF の実寸) |
  | フォント | 計測 | ページ内の書体ファミリー数(pptx は元ファイルの書体) |
  | 文字量 | 計測 | ページの文字数(150字以下が満点) |
- **機械チェック**: 表記ゆれ・半角カナ・長文・表紙タイトルを LLM なしで即時判定
- **総合判定**: 全ページ平均 70 点以上で合格。機械チェックもゼロなら「提出OK」
- **Markdown ダウンロード**: 採点結果(修正点のチェック状態つき)を `.md` で保存
- pptx は LibreOffice で PDF 化し、ページ画像・文字サイズは PDF から、テキスト・書体は pptx から読む

## 必要なツール

- [uv](https://docs.astral.sh/uv/)、[pnpm](https://pnpm.io/) + Node.js 22+(`corepack enable pnpm`)
- [LibreOffice](https://www.libreoffice.org/)(pptx の PDF 変換。macOS: `brew install --cask libreoffice`)
- [Ollama](https://ollama.com/) と `gemma4:e2b`(ローカル、または下記の Colab)
- 開発ワークフロー用: [gh](https://cli.github.com/)、Claude Code

## ローカルで起動

```bash
make dev     # backend(:8000)+ 画面(:5173)を同時起動。依存が無ければ make setup も自動実行
make serve   # frontend をビルドして :8000 の 1 プロセスで配信(Render と同じ構成)
```

どちらも Ctrl+C で全サーバが止まる。接続先などの設定はリポジトリ直下の `.env` に書く
(`cp .env.example .env` して `REVIEW_OLLAMA_URL` に Colab のトンネル URL を入れる)。`.env` は git 管理外。
未設定なら `http://localhost:11434`。コマンド実行時の環境変数が `.env` より優先される。
ポートは `BACKEND_PORT` / `FRONTEND_PORT` で変更できる。

> トンネル URL は公開リポジトリにコミットしない。認証の無い Ollama を誰でも直接使えてしまうため。

## Google Colab の Ollama を使う

Colab(**GPU ランタイム**)で Ollama を起動し、Cloudflare Quick Tunnel で公開する。セルを上から順に実行する。

```python
# 1) Ollama を入れて起動する
!curl -fsSL https://ollama.com/install.sh | sh
import subprocess, os
env = {
    **os.environ,
    "OLLAMA_HOST": "0.0.0.0:11434",   # 必須: 127.0.0.1 待ち受けだとトンネル経由は Host 検査で 403
    "OLLAMA_ORIGINS": "*",
    "OLLAMA_CONTEXT_LENGTH": "8192",  # アプリの REVIEW_NUM_CTX と揃える(違うと初回にモデルを読み直す)
    "OLLAMA_KEEP_ALIVE": "-1",        # モデルをメモリに置いたままにする(既定は 5 分で解放)
}
subprocess.Popen(["ollama", "serve"], env=env, stdout=open("ollama.log", "w"), stderr=subprocess.STDOUT)
!sleep 5 && ollama pull gemma4:e2b
```

```python
# 2) 暖機: モデルを読み込んでおく(Colab 起動直後の初回は読み込みで 100 秒を超え、Cloudflare が 524 を返すことがある)
!curl -s localhost:11434/api/chat -d '{"model":"gemma4:e2b","stream":false,"options":{"num_ctx":8192},"messages":[{"role":"user","content":"ok"}]}' > /dev/null && echo warmed
```

```python
# 3) トンネルを張って URL を表示する
!wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared && chmod +x cloudflared
!nohup ./cloudflared tunnel --url http://localhost:11434 > cloudflared.log 2>&1 &
!sleep 8 && grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' cloudflared.log | head -1
```

表示された URL を、Render のダッシュボード(またはローカルの `.env`)の `REVIEW_OLLAMA_URL` に設定する。
Quick Tunnel の URL は起動のたびに変わる。アプリ側も 524 は 1 回だけ自動で再試行するが、暖機しておくと確実。

## Render でホスティング(Docker なし)

1. このリポジトリを Render に接続し、**New → Blueprint** で `render.yaml` から作成する
   - Python ネイティブランタイム。ビルドは `bin/render-build.sh`(uv で backend、Node を用意して frontend をビルド)
   - 起動は `cd backend && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port $PORT`(画面と API を同一オリジンで配信)
2. `REVIEW_OLLAMA_URL` に Colab のトンネル URL を**ダッシュボードで**入力する(`sync: false`。公開リポジトリに載せない)。
   Colab を再起動して URL が変わったら更新する
3. プランは Free で動く(無操作 15 分でスリープし、次のアクセスで起動に 1 分程度かかる)

> **Render 上では PDF のみ採点できる。** Python ランタイムには LibreOffice を入れられないため、pptx は
> 画面で「PowerPoint で PDF に書き出してからアップロード」と案内する(対応形式は `GET /api/capabilities`)。
> pptx も採点したい場合は、同梱の `Dockerfile`(LibreOffice 入り)で Docker ランタイムを使う。

> **公開時の注意**: Render の URL を知っていれば誰でもアップロードでき、Colab の GPU を消費する。
> アップロードした資料は Render と Colab(Cloudflare 経由)に送られる。社外秘の資料を扱う場合は、
> アクセス制限(Render の IP 制限や前段の認証)を検討すること。

## 設定(環境変数)

| 変数 | 既定値 | 用途 |
|---|---|---|
| `REVIEW_OLLAMA_URL` | `http://localhost:11434` | Ollama の URL(Colab のトンネル URL など) |
| `REVIEW_MODEL` | `gemma4:e2b` | 使用モデル(vision 対応が必要) |
| `REVIEW_THINK` | 未設定(モデル既定) | `false` で思考を止めて速くする |
| `REVIEW_TEMPERATURE` / `REVIEW_NUM_CTX` | `0.2` / `8192` | 推論パラメータ |
| `REVIEW_TIMEOUT_SECONDS` | `600` | 1 ページあたりの LLM タイムアウト |
| `REVIEW_MAX_PAGES` | `40` | 採点する最大ページ数 |
| `REVIEW_MAX_UPLOAD_MB` | `50` | アップロード上限 |
| `REVIEW_IMAGE_WIDTH` | `1024` | LLM に渡すページ画像の幅(px) |
| `REVIEW_SOFFICE_PATH` | 自動検出 | LibreOffice `soffice` のパス |
| `REVIEW_STATIC_DIR` | 未設定 | ビルド済み frontend の配信元(render.yaml・Dockerfile で設定済み) |

## API

- `GET /api/health` — `{ok, model, model_ready, error}`
- `GET /api/capabilities` — `{formats: ["pdf", "pptx"]}`(LibreOffice が無ければ `["pdf"]`)
- `POST /api/review`(multipart `file`、.pptx / .pdf のみ)— NDJSON で
  `meta`(ページ数・機械チェック)→ `page` / `page_error`(1 ページずつ)→ `done`(基準別平均・判定)

## 開発の回し方

### 自律レーン(issue 駆動)

```
/ticket                      # 会話で意図を引き出し、GitHub issue を作成
/implement backend 42        # issue #42 を plan → TDD → 自己レビュー → PR まで自律実行
```

### 対話レーン(人間と並走)

```
/workon backend              # 環境確認・ブランチ作成・コンテキスト確立
...(対話しながら開発)...
/ship 42                     # 回顧plan生成 → 自己レビュー → PR(issue# は省略可)
```

### レビュー

```
/review 123                  # PR #123 を plan・ticket と突き合わせてレビュー
```

### 補助スキル

| スキル | 用途 | 原典 |
|---|---|---|
| `/debug` | 修正前の根本原因調査(4フェーズ)+ 回帰テスト強制 | obra/superpowers |
| `/verify` | 完了主張前の証拠ゲート(コマンド実行 → 出力確認 → 主張) | obra/superpowers |
| `/e2e` | Playwright でフルスタック検証・スクリーンショット | anthropics/skills |
| `/frontend-design` | 没個性UIを避ける設計プロセス | anthropics/skills |
| `/skill-creator` | スキル追加・改修の作法 | anthropics/skills |

## TDD の強制(4層)

1. **CLAUDE.md 規約** — 失敗テストのコミットが実装コミットに先行すること
2. **implement skill** — Red(失敗確認 → コミット)→ Green → Refactor を手順として強制
3. **CI** — カバレッジ 80% 未満で fail
4. **code-reviewer** — テストコミットの先行を git log で検証。違反は Blocking

## ディレクトリ

```
backend/src/app/
  domain/   pages(ページ・pptx テキスト重ね合わせ)/ metrics(計測で採点する3基準)
            review(6基準・LLM スキーマ・集計)/ reviewer(部長の定義・ページ用プロンプト)
            precheck(機械チェック)/ service(meta→page…→done のイベント生成)
  infra/    document(形式判定・読み込み)/ converter(LibreOffice)/ pdf_reader / pptx_reader
            ollama(stream + 画像)/ settings
  api/      routes(/api/health, /api/review)
frontend/src/
  logic/    events / ndjson / state(reducer)/ labels / markdown / files / escape  ← vitest
  ui/       DOM 描画・イベント結線(テスト免除)
render.yaml, bin/render-build.sh   Render 用(Docker なし)/ Dockerfile は任意の Docker 構成
plans/      plan・workflow_state・findings
```
