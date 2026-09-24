"""Read pages from PDF bytes with pdfplumber: text, glyph sizes, fonts, images, render.

pdfplumber(MIT)を使う。PyMuPDF は AGPL のため公開ホスティングでは避ける。
"""

from app.domain.pages import Page


def read_pdf(data: bytes, image_width: int = 1024) -> list[Page]:
    """Return one `Page` per PDF page, rendered to a JPEG `image_width` pixels wide.

    The title is the text drawn at the page's largest font size. Raise `DocumentError`
    when `data` is not a readable PDF.
    """
    raise NotImplementedError
