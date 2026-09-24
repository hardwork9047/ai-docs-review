# plans/

plan ファイル・ワークフロー状態・レビュー findings の置き場。

| ファイル | 用途 | ライフサイクル |
|---|---|---|
| `issue-{N}-slug.md` | issue 駆動実装の plan(コード着手前にコミット) | 永続。実装の意図の記録 |
| `session-{YYYY-MM-DD}-slug.md` | 対話セッションの回顧 plan(`/ship` が生成) | 永続 |
| `{plan名}-findings.md` | 自己レビュー(code-reviewer + doc-parrot)の各ラウンド記録 | 永続 |
| `workflow_state.md` | 進行中ワークフローの状態(中断・再開用) | **一時的。PR 作成時に削除** |

plan に書くこと: issue のゴール(逐語)、選んだアプローチと分解、検討して捨てた代替案、
明示的なスコープ外、他スコープへの前提、各受け入れシナリオのテスト方針。
