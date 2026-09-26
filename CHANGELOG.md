# Changelog

記法: `v{version}: {summary}, see PR #{N}`(新しいものを上に追加)

## Unreleased

- docs: 製造業向けのサンプル基準パック(稟議・品質報告・改善提案の14ルール)を追加
- v0.3.0 (backend, frontend): 基準パック(会社ルール)を追加。禁止表現・表記の統一・必須記載事項を YAML で定義し、根拠の条文付きで決定的に判定(formal_passed)。違反を20件仕込んだサンプル資料と正解表(make sample-deck)
- v0.2.2 (backend): Modal(T4・proxy auth)で Ollama を動かす構成を追加。Ollama へのヘッダー設定、Render 用の生存確認 /api/live、接続確認の待ち時間を設定可能に
- v0.2.1 (frontend): 表示幅を画面いっぱい(左右に少しの余白)に拡大し、ページのサムネイルも横幅に合わせて拡大
- v0.2.1 (backend): Colab 起動直後の Cloudflare タイムアウト(524)を 1 回だけ自動再試行。README の Colab 手順に文脈長・常駐・暖機を追加
- v0.2.0 (backend, frontend): 部長一名視点の資料レビューアプリ。pptx/PDF をページ別に6基準(内容・フォントサイズ・フォント・図・グラフ・文字量)で採点し、良い点・悪い点・修正点を表示、Markdown ダウンロード、Render ホスティング(Docker なしの Python ランタイム・PDF のみ。pptx 対応の Dockerfile も同梱)
- v0.1.0: テンプレート初期構成(FastAPI backend + Vite/Three.js frontend + AI開発ワークフロー)
