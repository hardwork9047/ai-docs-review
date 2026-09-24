"""Unit tests for app.domain.pages — PDF 由来のページに pptx のテキストを重ねる。"""

from app.domain.pages import Page, SlideText, apply_slide_text

RENDERED = [
    Page(no=1, title="(cid:1)", body="(cid:2)", char_sizes=(36.0, 18.0), image=b"jpg1"),
    Page(no=2, title="", body="", char_sizes=(18.0,), image_count=2, image=b"jpg2"),
]


def test_text_and_fonts_come_from_slides_and_measurements_are_kept() -> None:
    merged = apply_slide_text(RENDERED, [SlideText("表紙", "本文", "ノート", ("メイリオ",))])
    assert merged[0] == Page(
        no=1,
        title="表紙",
        body="本文",
        notes="ノート",
        char_sizes=(36.0, 18.0),
        fonts=("メイリオ",),
        image=b"jpg1",
    )


def test_pages_without_matching_slide_are_unchanged() -> None:
    merged = apply_slide_text(RENDERED, [SlideText("表紙", "本文")])
    assert merged[1] == RENDERED[1]


def test_extra_slides_are_ignored() -> None:
    slides = [SlideText("a", ""), SlideText("b", ""), SlideText("c", "")]
    assert [p.title for p in apply_slide_text(RENDERED, slides)] == ["a", "b"]
