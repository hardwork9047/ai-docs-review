# ai-template

AI エージェント(Claude Code)主体の開発を、シンプルかつ高品質に回すためのテンプレートリポジトリ。

- **Backend**: FastAPI + uv + pytest + ruff + mypy(strict)
- **Frontend**: Vite + TypeScript + Three.js + vitest
- **ワークフロー**: TDD を強制する Claude Code skills 一式(`.claude/skills/`)
- **CI**: lint / typecheck / test(カバレッジ 80% 閾値)

## 必要なツール

- [uv](https://docs.astral.sh/uv/)(Python 環境・依存管理)
- [pnpm](https://pnpm.io/) + Node.js 22+
- [gh](https://cli.github.com/)(issue / PR 操作。skills が使用)
- Claude Code

## このテンプレートから始める

1. GitHub で「Use this template」またはクローンしてリモートを差し替え
2. `make setup` — 依存を全部インストール
3. `make check` — ゲートが通ることを確認
4. プロジェクトに合わせて書き換え:
   - `backend/src/app/domain/pagination.py` と対応テストは **TDD スタイルのサンプル**。実開発開始時に削除してよい
   - `frontend/src/logic/orbit.ts` と `src/scene/` の回転キューブも同様のサンプル
   - `backend/pyproject.toml` の `name` / `description`、`frontend/package.json` の `name` を変更
   - `CLAUDE.md` のプロジェクト固有部分(構成説明など)を実態に合わせて更新

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
backend/          FastAPI(src/app/{api,domain,infra}, tests/{unit,integration})
frontend/         Vite + Three.js(src/{scene,logic}, tests/)
plans/            plan・workflow_state・findings
.claude/          skills(ticket/implement/workon/ship/review/doc-parrot/grill-me)+ code-reviewer agent
.github/          CI
bin/              補助スクリプト(claude-headroom.sh)
```
