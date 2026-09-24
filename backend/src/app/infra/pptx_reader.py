"""Read slide text and font families from .pptx bytes with python-pptx (in memory).

LibreOffice の PDF では日本語テキストが化けたり書体が置換されたりするため、
pptx のアップロードではテキストと書体名をここで元ファイルから読む。
"""

from app.domain.pages import SlideText


def read_slide_texts(data: bytes) -> list[SlideText]:
    """Return one `SlideText` per *visible* slide (hidden slides are not exported to PDF).

    Fonts are the typefaces set explicitly on runs plus the theme's body (and, when the
    slide has a title, heading) fonts, with theme references like "+mn-ea" resolved.
    Raise `DocumentError` when `data` is not a valid .pptx package.
    """
    raise NotImplementedError
