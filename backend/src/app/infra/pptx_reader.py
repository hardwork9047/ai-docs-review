"""Extract slide text from .pptx bytes with python-pptx (in memory; nothing hits disk)."""

from app.domain.slides import Slide


class DeckReadError(Exception):
    """The uploaded bytes are not a readable .pptx file."""


def read_slides(data: bytes) -> list[Slide]:
    """Return one `Slide` per slide with title, body text, tables and speaker notes.

    Raise `DeckReadError` when `data` is not a valid .pptx package.
    """
    raise NotImplementedError
