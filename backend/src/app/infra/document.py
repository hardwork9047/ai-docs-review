"""Load an upload (.pptx or .pdf) into reviewable `Page`s.

pptx は PDF に変換して画像・計測値を取り、テキストと書体名は pptx 本体から重ねる。
"""

from collections.abc import Callable
from typing import Literal

from app.domain.pages import Page

Converter = Callable[[bytes, str], bytes]


def detect_kind(filename: str, data: bytes) -> Literal["pdf", "pptx"]:
    """Accept only .pdf / .pptx whose content matches the extension.

    Raise `DocumentError` otherwise (checked by magic bytes: "%PDF" / zip "PK").
    """
    raise NotImplementedError


def load_document(
    filename: str,
    data: bytes,
    *,
    soffice: str,
    image_width: int = 1024,
    convert: Converter | None = None,
) -> list[Page]:
    """Read the upload into pages. `convert` defaults to LibreOffice `pptx_to_pdf`."""
    raise NotImplementedError
