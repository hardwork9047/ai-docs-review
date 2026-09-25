"""Pre-conversion fixes applied to .pptx bytes before LibreOffice renders them.

Root cause (2026-09-24 調査): 多くの日本語テーマは東アジア書体を `<a:ea typeface="">`(空)にし、
実体を `<a:font script="Jpan" typeface="メイリオ"/>` に置く。LibreOffice は空の a:ea を読むため、
テーマ書体を継承した日本語テキストの書体名が空になり、PDF 出力で未定義フォントを参照して
描画が文字化けする(画像を見る LLM にも化けた文字が渡る)。
"""

import io
import re
import zipfile

_SCHEME = re.compile(r"<a:(major|minor)Font>.*?</a:\1Font>", re.S)
_JPAN = re.compile(r'<a:font\b(?=[^>]*\bscript="Jpan")[^>]*\btypeface="([^"]+)"')
_EMPTY_EA = re.compile(r'(<a:ea\b[^>]*\btypeface=)""')


def fill_theme_east_asian_fonts(data: bytes) -> bytes:
    """Copy each theme font scheme's Jpan typeface into its empty `<a:ea typeface="">`.

    Only `ppt/theme/*.xml` entries change; every other zip entry is copied as is.
    Returns `data` unchanged when nothing needs fixing or `data` is not a zip
    (reading errors are left to the pptx reader, which reports them properly).
    """
    try:
        src = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        return data
    with src:
        themes = {
            name: _fix_theme(src.read(name).decode("utf-8"))
            for name in src.namelist()
            if name.startswith("ppt/theme/") and name.endswith(".xml")
        }
        changed = {n: xml for n, xml in themes.items() if xml != src.read(n).decode("utf-8")}
        if not changed:
            return data
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
            for info in src.infolist():
                body = changed[info.filename].encode() if info.filename in changed else None
                dst.writestr(info, body if body is not None else src.read(info.filename))
        return out.getvalue()


def _fix_theme(xml: str) -> str:
    def fix_scheme(match: re.Match[str]) -> str:
        block = match.group(0)
        jpan = _JPAN.search(block)
        if not jpan:
            return block
        return _EMPTY_EA.sub(lambda m: f'{m.group(1)}"{jpan.group(1)}"', block, count=1)

    return _SCHEME.sub(fix_scheme, xml)
