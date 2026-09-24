"""Read pages from PDF bytes with pdfplumber: text, glyph sizes, fonts, images, render.

pdfplumber(MIT)を使う。PyMuPDF は AGPL のため公開ホスティングでは避ける。
"""

import io
import logging
from typing import Any

import pdfplumber
from pdfminer.pdfparser import PDFSyntaxError
from pdfplumber.page import Page as PdfPage
from pdfplumber.utils.exceptions import PdfminerException

from app.domain.pages import Page
from app.infra.errors import DocumentError

# 埋め込みフォント情報が欠けた PDF で大量に出る警告を抑える(読み取り結果には影響しない)
logging.getLogger("pdfminer").setLevel(logging.ERROR)

JPEG_QUALITY = 80


def read_pdf(data: bytes, image_width: int = 1024) -> list[Page]:
    """Return one `Page` per PDF page, rendered to a JPEG `image_width` pixels wide.

    The title is the text drawn at the page's largest font size. Raise `DocumentError`
    when `data` is not a readable PDF.
    """
    try:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            return [_read_page(page, image_width) for page in pdf.pages]
    except (PdfminerException, PDFSyntaxError) as exc:
        raise DocumentError("PDF として読み込めませんでした") from exc


def _read_page(page: PdfPage, image_width: int) -> Page:
    chars = [c for c in page.chars if str(c["text"]).strip()]
    return Page(
        no=page.page_number,
        title=_title(page.chars),
        body=(page.extract_text() or "").strip(),
        char_sizes=tuple(round(float(c["size"]), 1) for c in chars),
        fonts=tuple(sorted({str(c["fontname"]) for c in chars})),
        image_count=len(page.images),
        image=_render(page, image_width),
    )


def _title(chars: list[dict[str, Any]]) -> str:
    visible = [c for c in chars if str(c["text"]).strip()]
    if not visible:
        return ""
    largest = max(float(c["size"]) for c in visible)
    # 空白文字も同じサイズで描かれているので、全文字から拾うと単語間の空白が残る
    return "".join(str(c["text"]) for c in chars if float(c["size"]) == largest).strip()


def _render(page: PdfPage, width: int) -> bytes:
    buf = io.BytesIO()
    page.to_image(width=width).original.convert("RGB").save(buf, "JPEG", quality=JPEG_QUALITY)
    return buf.getvalue()
