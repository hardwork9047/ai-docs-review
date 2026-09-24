"""Integration tests for app.infra.pdf_reader — テスト内で生成した最小 PDF を読む。"""

import io

import pytest
from PIL import Image

from app.infra.errors import DocumentError
from app.infra.pdf_reader import read_pdf
from tests.pdf_factory import make_pdf

PDF = make_pdf(
    [[("Approval Request", 32), ("Budget 5M yen", 18), ("footnote", 10)], [("Next", 24)]],
    images_per_page=[2, 0],
)


def test_one_page_per_pdf_page_numbered_from_one() -> None:
    assert [p.no for p in read_pdf(PDF)] == [1, 2]


def test_title_is_the_largest_text_and_body_is_all_text() -> None:
    page = read_pdf(PDF)[0]
    assert page.title == "Approval Request"
    assert page.body == "Approval Request\nBudget 5M yen\nfootnote"


def test_glyph_sizes_skip_whitespace() -> None:
    page = read_pdf(PDF)[0]
    assert sorted(set(page.char_sizes)) == [10.0, 18.0, 32.0]
    assert len(page.char_sizes) == len("ApprovalRequestBudget5Myenfootnote")


def test_fonts_and_image_count() -> None:
    first, second = read_pdf(PDF)
    assert first.fonts == ("Helvetica",)
    assert (first.image_count, second.image_count) == (2, 0)


def test_page_is_rendered_to_jpeg_of_requested_width() -> None:
    image = Image.open(io.BytesIO(read_pdf(PDF, image_width=640)[0].image))
    assert image.format == "JPEG"
    assert image.width == 640


def test_page_without_text_has_empty_title() -> None:
    page = read_pdf(make_pdf([[]], images_per_page=[1]))[0]
    assert (page.title, page.body, page.char_sizes) == ("", "", ())


def test_non_pdf_bytes_raise_document_error() -> None:
    with pytest.raises(DocumentError):
        read_pdf(b"%PDF-1.4 but broken")
