"""Extract slide text from .pptx bytes with python-pptx (in memory; nothing hits disk)."""

import io
import zipfile

from pptx import Presentation
from pptx.exc import PackageNotFoundError
from pptx.shapes.autoshape import Shape
from pptx.shapes.graphfrm import GraphicFrame
from pptx.slide import Slide as PptxSlide

from app.domain.slides import Slide


class DeckReadError(Exception):
    """The uploaded bytes are not a readable .pptx file."""


def read_slides(data: bytes) -> list[Slide]:
    """Return one `Slide` per slide with title, body text, tables and speaker notes.

    Raise `DeckReadError` when `data` is not a valid .pptx package.
    """
    try:
        prs = Presentation(io.BytesIO(data))
    except (zipfile.BadZipFile, PackageNotFoundError, KeyError) as exc:
        raise DeckReadError(".pptx として読み込めませんでした") from exc
    return [_read_slide(no, slide) for no, slide in enumerate(prs.slides, start=1)]


def _read_slide(no: int, slide: PptxSlide) -> Slide:
    title_shape = slide.shapes.title
    title_id = title_shape.shape_id if title_shape is not None else None
    title, bodies = "", []
    for shape in slide.shapes:
        if isinstance(shape, Shape) and shape.has_text_frame:
            text = shape.text_frame.text.strip()
            if not text:
                continue
            if shape.shape_id == title_id:
                title = text
            else:
                bodies.append(text)
        elif isinstance(shape, GraphicFrame) and shape.has_table:
            rows = [" | ".join(c.text.strip() for c in row.cells) for row in shape.table.rows]
            bodies.append("[表]\n" + "\n".join(rows))

    notes = ""
    if slide.has_notes_slide:
        frame = slide.notes_slide.notes_text_frame
        notes = frame.text.strip() if frame is not None else ""
    return Slide(no=no, title=title, body="\n".join(bodies), notes=notes)
