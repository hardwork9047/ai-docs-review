"""Pre-conversion fixes applied to .pptx bytes before LibreOffice renders them.

Root cause (2026-09-24 調査): 多くの日本語テーマは東アジア書体を `<a:ea typeface="">`(空)にし、
実体を `<a:font script="Jpan" typeface="メイリオ"/>` に置く。LibreOffice は空の a:ea を読むため、
テーマ書体を継承した日本語テキストの書体名が空になり、PDF 出力で未定義フォントを参照して
描画が文字化けする(画像を見る LLM にも化けた文字が渡る)。
"""


def fill_theme_east_asian_fonts(data: bytes) -> bytes:
    """Copy each theme font scheme's Jpan typeface into its empty `<a:ea typeface="">`.

    Only `ppt/theme/*.xml` entries change; every other zip entry is copied as is.
    Returns `data` unchanged when nothing needs fixing.
    """
    raise NotImplementedError
