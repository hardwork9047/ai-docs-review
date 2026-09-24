"""Convert .pptx to PDF with LibreOffice (`soffice --headless`).

変換は一時ディレクトリ内で行い、終了時に削除する。LibreOffice は同一プロファイルの
同時起動を拒否するため、変換ごとに一時プロファイル(-env:UserInstallation)を使う。
"""

from app.infra.errors import DocumentError

MAC_SOFFICE = "/Applications/LibreOffice.app/Contents/MacOS/soffice"


class ConversionError(DocumentError):
    """LibreOffice is missing, timed out, or produced no PDF."""


def default_soffice() -> str:
    """`soffice` on PATH, else the macOS app bundle binary, else plain "soffice"."""
    raise NotImplementedError


def pptx_to_pdf(data: bytes, soffice: str, timeout: float = 180.0) -> bytes:
    """Return the PDF bytes LibreOffice produces for the given .pptx bytes."""
    raise NotImplementedError
