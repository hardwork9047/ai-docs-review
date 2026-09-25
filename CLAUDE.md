# CLAUDE.md — AI開発規約

このリポジトリは AI エージェント主体で開発する。以下のルールは全エージェント・全セッションに適用される。

## 構成

- `backend/` — FastAPI アプリ(uv 管理、Python 3.11+)
  - `src/app/api/` — HTTPルーター。**薄く保つ**。ロジックを書かない
  - `src/app/domain/` — ビジネスロジック。**テストの主戦場**
  - `src/app/infra/` — DB・外部API等の接続層
- `frontend/` — Vite + TypeScript(pnpm 管理、フレームワークなしの素の DOM)
  - `src/ui/` — DOM 描画・イベント結線層。**ユニットテスト免除**(薄く保つ)
  - `src/logic/` — 状態・計算ロジック。**必ずここに寄せてテストする**
- `plans/` — plan ファイル、workflow_state、レビュー findings の置き場
- `.claude/skills/` — 開発ワークフロー(下記「ワークフロー」参照)

## コマンド

すべて Makefile 経由で実行する(スタック変更に skills が耐えるための規約):

| コマンド | 用途 |
|---|---|
| `make setup` | 依存インストール(uv sync + pnpm install) |
| `make test` | 全テスト + カバレッジ閾値(80%) |
| `make test-backend` / `make test-frontend` | スコープ別テスト |
| `make lint` / `make format` | ruff チェック / 自動整形 |
| `make typecheck` | mypy(strict)+ tsc |
| `make check` | **push 前に必ず通すフルゲート**(lint + typecheck + test) |
| `make dev-backend` / `make dev-frontend` | 開発サーバ |

TDD の内側ループでは Makefile を経由せず直接実行してよい:
`cd backend && uv run pytest tests/unit/test_foo.py` / `cd frontend && pnpm vitest run tests/foo.test.ts`

## TDD(必須・例外なし)

1. **Red** — 受け入れシナリオを失敗するテストに翻訳する。**実行して失敗を確認**(失敗理由が「未実装」であること、import エラー等でないこと)。`test:` プレフィックスでコミット。
2. **Green** — テストが通る最小の実装を書く。`feat:` / `fix:` でコミット。
3. **Refactor** — テストが通ったまま整理する。`refactor:` でコミット。

守るべき不変条件:
- **失敗するテストのコミットが、実装コミットより先に存在すること**(code-reviewer が git log で検証する)
- テストなしの実装コミットは作らない。テストとまとめての1コミットも不可(Red の失敗確認が検証できなくなる)
- 例外は描画層(`frontend/src/ui/`)のみ。描画にロジックが混ざりそうになったら `logic/` へ抽出してテストする
- カバレッジ 80% 未満は CI で落ちる。閾値を下げて回避しない

## 品質ゲート

- **チェックの失敗を握りつぶさない。** exclude 追加・skip マーカー・`# type: ignore`・閾値の引き下げで通すのは修正ではなく隠蔽。根本原因が自分のスコープ外なら人間にエスカレーションする
- 新規の public 関数・クラスには docstring 必須(次のエージェントが読む前提で書く)
- コミット前に該当スコープの lint / typecheck を通す。push 前に `make check`

## スコープ

作業スコープは `backend` または `frontend`。スコープ外のファイルは読むのは自由、変更は原則しない。やむを得ず変更する場合は plan ファイルに理由を明記する。`plans/`・リポジトリ直下の設定ファイル(CLAUDE.md、Makefile、CHANGELOG.md 等)は常に変更可。

## ブランチ・コミット規約

- ブランチ: `feature/issue-{N}-slug` / `bugfix/issue-{N}-slug`(issue なしの対話セッションは `feature/{slug}`)
- コミット: `test:` `feat:` `fix:` `refactor:` `docs:` `chore:` プレフィックス
- バージョン: 変更したスコープの `backend/pyproject.toml` または `frontend/package.json` を semver でバンプし、ルート `CHANGELOG.md` に1行追記

## plans/ 規約

- plan: `plans/issue-{N}-slug.md`(issue駆動)/ `plans/session-{YYYY-MM-DD}-slug.md`(対話セッションの回顧plan)
- findings: `plans/{plan名}-findings.md` — 自己レビュー各ラウンドの記録
- `plans/workflow_state.md` — 進行中ワークフローの状態。PR 作成時に削除する

## ワークフロー(2レーン)

- **自律レーン**: `/ticket`(issue作成)→ `/implement {scope} {issue#}`(plan → TDD → 自己レビュー → PR)
- **対話レーン**: `/workon {scope}`(セッション開始)→ 開発 → `/ship [issue#]`(回顧plan → 自己レビュー → PR)
- レビュー: `/review [PR#]`。自己レビューは code-reviewer エージェント + `/doc-parrot` を必ず実行

## 補助スキル

- `/debug` — バグ・テスト失敗の際、**修正を試みる前に**必ず使う(根本原因調査 → 回帰テスト → 修正の4フェーズ)
- `/verify` — 「完了」「修正済み」「通った」と主張する前の証拠ゲート。コマンドを実行し出力を読んでから主張する
- `/e2e` — Playwright による E2E 検証・スクリーンショット取得(フルスタック結合、画面確認)
- `/frontend-design` — frontend の UI 設計時に使う(没個性デザインの回避)
- `/skill-creator` — このリポジトリにスキルを追加・改修するときの作法
