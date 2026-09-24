"""Document pages as the reviewer sees them.

Every upload is normalised to PDF: the rendered PDF gives the page image and the
measured glyph sizes. For .pptx uploads, text and font names come from the pptx
itself (`SlideText`), because LibreOffice's PDF often lacks a Unicode map for CJK
glyphs and substitutes fonts.
"""

from dataclasses import dataclass, replace

GARBLED = "(cid:"  # pdfminer が Unicode 対応表の無いグリフを出力するときの表記


@dataclass(frozen=True)
class Page:
    """One page (slide) ready for review.

    `char_sizes` holds the font size (pt) of every visible glyph on the rendered page,
    so its length is the page's character count. `fonts` are font family names used on
    the page. `image` is the rendered page as JPEG (empty in tests that don't need it).
    """

    no: int
    title: str
    body: str
    notes: str = ""
    char_sizes: tuple[float, ...] = ()
    fonts: tuple[str, ...] = ()
    image_count: int = 0
    image: bytes = b""


@dataclass(frozen=True)
class SlideText:
    """Text and font families read directly from one visible pptx slide."""

    title: str
    body: str
    notes: str = ""
    fonts: tuple[str, ...] = ()


def apply_slide_text(pages: list[Page], slides: list[SlideText]) -> list[Page]:
    """Overlay pptx text and fonts onto the pages rendered from that pptx's PDF.

    Pages and slides are matched by position; pages without a matching slide are
    returned unchanged. Measured values (`char_sizes`, `image`, ...) are kept.
    A slide without a title placeholder keeps the rendered page's title (its largest
    text) unless that text is garbled ("(cid:N)" glyphs without a Unicode map).
    """
    merged = [
        replace(
            page,
            title=s.title or ("" if GARBLED in page.title else page.title),
            body=s.body,
            notes=s.notes,
            fonts=s.fonts,
        )
        for page, s in zip(pages, slides, strict=False)
    ]
    return merged + pages[len(merged) :]
