"""Integration tests for app.infra.pptx_reader — 実際に python-pptx で生成した pptx を読む。"""

import io

import pytest
from pptx import Presentation
from pptx.util import Inches

from app.infra.pptx_reader import DeckReadError, read_slides

TITLE_AND_CONTENT = 1
BLANK = 6


def _to_bytes(prs: Presentation) -> bytes:
    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()


def _deck() -> bytes:
    prs = Presentation()

    s1 = prs.slides.add_slide(prs.slide_layouts[TITLE_AND_CONTENT])
    s1.shapes.title.text = "設備投資の承認依頼"
    s1.placeholders[1].text = "結論: A案を採用\n期限: 10月末"
    s1.notes_slide.notes_text_frame.text = "冒頭で結論を述べる"

    s2 = prs.slides.add_slide(prs.slide_layouts[BLANK])
    table = s2.shapes.add_table(2, 2, Inches(1), Inches(1), Inches(4), Inches(1)).table
    for r, row in enumerate([["項目", "金額"], ["設備", "500万円"]]):
        for c, text in enumerate(row):
            table.cell(r, c).text = text

    return _to_bytes(prs)


def test_title_body_and_notes_are_extracted() -> None:
    slide = read_slides(_deck())[0]
    assert slide.no == 1
    assert slide.title == "設備投資の承認依頼"
    assert slide.body == "結論: A案を採用\n期限: 10月末"
    assert slide.notes == "冒頭で結論を述べる"


def test_table_is_rendered_as_pipe_rows_and_missing_title_is_empty() -> None:
    slide = read_slides(_deck())[1]
    assert slide.no == 2
    assert slide.title == ""
    assert slide.body == "[表]\n項目 | 金額\n設備 | 500万円"
    assert slide.notes == ""


def test_deck_without_slides_returns_empty_list() -> None:
    assert read_slides(_to_bytes(Presentation())) == []


def test_non_pptx_bytes_raise_deck_read_error() -> None:
    with pytest.raises(DeckReadError):
        read_slides(b"not a pptx")
