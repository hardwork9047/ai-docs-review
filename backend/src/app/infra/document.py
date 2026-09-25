"""Load an upload (.pptx or .pdf) into reviewable `Page`s.

pptx は PDF に変換して画像・計測値を取り、テキストと書体名は pptx 本体から重ねる。
変換前にテーマの東アジア書体を補う(infra/pptx_fix: 日本語の文字化け対策)。
"""

from collections.abc import Callable
from typing import Literal

from app.domain.pages import Page, apply_slide_text
from app.infra.converter import pptx_to_pdf
from app.infra.errors import DocumentError
from app.infra.pdf_reader import read_pdf
from app.infra.pptx_fix import fill_theme_east_asian_fonts
from app.infra.pptx_reader import read_slide_texts

Converter = Callable[[bytes, str], bytes]

_MAGIC: dict[str, bytes] = {"pdf": b"%PDF", "pptx": b"PK"}


def detect_kind(filename: str, data: bytes) -> Literal["pdf", "pptx"]:
    """Accept only .pdf / .pptx whose content matches the extension.

    Raise `DocumentError` otherwise (checked by magic bytes: "%PDF" / zip "PK").
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "pdf" and data.startswith(_MAGIC["pdf"]):
        return "pdf"
    if ext == "pptx" and data.startswith(_MAGIC["pptx"]):
        return "pptx"
    raise DocumentError(".pptx または .pdf ファイルをアップロードしてください")


def load_document(
    filename: str,
    data: bytes,
    *,
    soffice: str,
    image_width: int = 1024,
    convert: Converter | None = None,
) -> list[Page]:
    """Read the upload into pages. `convert` defaults to LibreOffice `pptx_to_pdf`.

    pptx は変換前にテーマの東アジア書体を補う(`fill_theme_east_asian_fonts`)。
    Raise `DocumentError` (or its subclass `ConversionError`) when the type is not
    .pdf/.pptx, the file cannot be read, or conversion fails. May return an empty list
    for a document with no pages.
    """
    if detect_kind(filename, data) == "pdf":
        return read_pdf(data, image_width)
    slides = read_slide_texts(data)
    pdf = (convert or pptx_to_pdf)(fill_theme_east_asian_fonts(data), soffice)
    return apply_slide_text(read_pdf(pdf, image_width), slides)
