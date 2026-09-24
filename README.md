# 部長レビュー(ai-docs-review)

提出前のパワポ(.pptx)を、**多忙な部長の視点**でローカル LLM(Ollama)がレビューする Web アプリ。
ファイルはメモリ上でのみ処理し、ディスクにも社外にも出さない。

- **部長の所見**: 結論ファースト・資料の目的・意思決定に使える数字・依頼事項と期限を評価(0〜100点+朱書き指摘)
- **機械チェック**: 表記ゆれ・半角カナ・長文・表紙タイトルを LLM なしで即時判定
- **検印**: 評点 70 以上かつ重要度「高」ゼロで部長 OK。機械チェックもゼロなら「承認」

元になった五視点版(penta-review)から、上司(部長)一名に絞って作り直したもの。

## 必要なツール

- [uv](https://docs.astral.sh/uv/)、[pnpm](https://pnpm.io/) + Node.js 22+(`corepack enable pnpm`)
- [Ollama](https://ollama.com/) と使用モデル: `ollama pull gemma4:e2b`
- 開発ワークフロー用: [gh](https://cli.github.com/)、Claude Code

## 起動

```bash
make setup
make dev-backend    # http://localhost:8000(API)
make dev-frontend   # http://localhost:5173(画面。/api は backend へ proxy)
```

ブラウザで http://localhost:5173 を開き、.pptx をドロップする。右上のランプで Ollama の接続とモデルの pull 状況を確認できる。

## 設定(環境変数)

| 変数 | 既定値 | 用途 |
|---|---|---|
| `REVIEW_OLLAMA_URL` | `http://localhost:11434` | Ollama の URL |
| `REVIEW_MODEL` | `gemma4:e2b` | 使用モデル(`ollama list` の名前) |
| `REVIEW_TEMPERATURE` | `0.2` | 生成温度(批評は再現性重視で低め) |
| `REVIEW_NUM_CTX` | `8192` | コンテキスト長。30枚超の資料は `16384` に |
| `REVIEW_MAX_SLIDES` | `40` | LLM に渡す最大枚数 |
| `REVIEW_TIMEOUT_SECONDS` | `600` | LLM 応答のタイムアウト |

例: `REVIEW_MODEL=gemma3:4b make dev-backend`

## API

- `GET /api/health` — `{ok, model, model_ready, error}`
- `POST /api/review`(multipart `file`)— NDJSON で `meta`(枚数・機械チェック・レビュアー)→ `result`(所見・判定)または `error` の順に流す

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
  domain/   slides(プロンプト組立)/ precheck(機械チェック)/ review(スキーマ・判定)
            reviewer(部長の定義)/ service(meta→result|error のイベント生成)
  infra/    pptx_reader / ollama / settings
  api/      routes(/api/health, /api/review)
frontend/src/
  logic/    events / ndjson / state(reducer)/ labels / escape  ← vitest
  ui/       DOM 描画・イベント結線(テスト免除)
plans/      plan・workflow_state・findings
.claude/    skills + code-reviewer agent
```
