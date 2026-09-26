# Findings: session-2026-09-25-standard-pack

## Round 1

### Code Reviewer
- Blocking: 3
- Should Fix: 3
- Informational: 6
- Key Issues:
  - [Blocking] plan ファイルが無い → `plans/session-2026-09-25-standard-pack.md` を作成
  - [Blocking] backend・frontend・`samples/` にまたがる変更の理由が未記載 → plan の Scope に記載
  - [Blocking] 空白の正規化でページ境界まで詰めたため、`required`(must)がページをまたぐ偶然の一致で満たされうる
    → 回帰テストを先にコミットし(`test:`)、タイトル/本文・ページを改行で区切る修正(`fix:`)。
    正規表現の `.` が境目をまたがないテストは修正と同じコミットに入った(規約からの逸脱として記録)
  - [Should Fix] 壊れたパックが 500 になる経路のテストが無い → `test_api.py::test_broken_standard_pack_is_a_server_error_not_silently_skipped` を追加(現状の動作を固定する回帰ガード)
  - [Should Fix] 正規表現の ReDoS について記載が無い → `parse_pack` の docstring と README に注意を追記(パックは管理者が書く前提)
  - [Should Fix] labels.test.ts の import 行が長い → prettier は未設定で lint 対象外。見送り
- Judgment: 境界の一致は must の必須記載事項を誤って満たす実害のある指摘で、直す価値が高かった

### Doc Parrot
- Divergences Found: 0(新規 callable の docstring は例外条件・境界・正規化の方針まで記載済み。`check_pack` と `parse_pack` は今回の修正で追記)
