# 基準パック(会社ルール)の最小版と、違反を仕込んだサンプル資料

> Note: This plan was generated retroactively from the completed changes.
> This is expected for interactive development sessions (/workon + /ship).

## Goal

Copilot in PowerPoint「Review this presentation」(構成・明快さ・ストーリーへの汎用の助言)との差別化として、
**会社の業務ルールを根拠付き・決定的に判定する**機能の最小版を作り、その差を**数字で示せる比較用資料**を用意する。

## Approach

- **domain/standard.py**: 基準パック(YAML)のモデルと判定。ルールは `forbid`(禁止表現)/ `prefer`(表記の統一)/
  `required`(必須記載事項)の 3 種、`severity` は must / should、`source` に根拠の条文。LLM を使わず文字列・正規表現で照合
- **照合の正規化**: PDF 抽出が書体の切り替わりに空白、折り返しに改行を入れるため、空白・改行を無視して照合する。
  ただしタイトル/本文・ページの境目は改行で区切り、境目をまたぐ一致は起こさない(レビュー指摘で修正)
- **結果の載せ方(後方互換)**: 既存の `MetaEvent.lint`(`LintFinding`)に既定値付きの項目(rule_id / severity / source / page)を足し、
  `Verdict.formal_passed`(must 違反ゼロ)と `MetaEvent.standard` を追加。パック未設定なら従来と同じ形
- **infra/standards.py**: `REVIEW_STANDARD_PATH` の YAML を読む。壊れたパックは黙って無効にせず 500(設定ミスに気づける)
- **サンプル資料**: 架空の介護向け提案書 9 ページに違反 20 件を仕込み、正解表と組にする。pptx・PDF 両経路で 20 件ちょうどを検出することをテストで保証
- **frontend**: 必須/推奨のタグ、ページへのリンク、根拠の条文、判定文言「会社ルールの必須項目に違反があります」、Markdown に根拠列

## Alternatives considered

- パックの結果を新しいイベント型で流す → frontend が未知の type で throw するため、既存の lint に項目を足す形を選んだ
- 合否を平均点から形式判定に置き換える → 既存の意味を変えるので今回は `formal_passed` の追加に留めた
- 空白の正規化を pdf_reader 側で行う → pptx 経路やページ内の折り返しにも効くよう、照合側で行った

## Scope

- **backend と frontend の両方を変更**(全層にまたがる機能のため。frontend は表示の追加のみ)
- **`samples/` をリポジトリ直下に新設**: `make sample-deck` の出力(架空の pptx・PDF・正解表)。Copilot などとの比較実験で
  他者に渡す成果物なので、テストの内部(`backend/tests/fixtures/`)ではなく見つけやすい場所に置いた。生成元は `backend/tests/fixtures/violation_deck.py`
- 触らない: 採点(LLM)の流れ、既存の合否(passed / overall_passed)の意味、Render の設定ファイル
- 顧客のパックはリポジトリに置かない(Render は Secret File + `REVIEW_STANDARD_PATH`)

## デバッグ記録

- Root cause: pdfplumber が書体の切り替わりに空白を入れる(「業界 No.1」「山田花子様 (85 歳 )」)ため、PDF 経路で 2 件を取りこぼした。
  Regression test: `test_violation_deck.py::test_the_pdf_version_gives_the_same_findings`, `test_standard.py::test_spaces_and_line_breaks_inside_a_match_are_ignored`
- Root cause: 上の修正でページの境目まで詰めたため、ページをまたいで `required` が満たされていた(「料|金」)。
  Regression test: `test_standard.py::test_required_item_is_not_satisfied_across_a_page_boundary`, `test_matches_do_not_span_the_title_and_the_body`
