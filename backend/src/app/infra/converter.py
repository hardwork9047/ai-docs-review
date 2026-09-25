"""Convert .pptx to PDF with LibreOffice (`soffice --headless`).

変換は一時ディレクトリ内で行い、終了時に削除する。LibreOffice は同一プロファイルの
同時起動を拒否するため、変換ごとに一時プロファイル(-env:UserInstallation)を使う。
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.infra.errors import DocumentError

MAC_SOFFICE = "/Applications/LibreOffice.app/Contents/MacOS/soffice"


class ConversionError(DocumentError):
    """LibreOffice is missing, timed out, or produced no PDF."""


def default_soffice() -> str:
    """`soffice` on PATH, else the macOS app bundle binary, else plain "soffice"."""
    found = shutil.which("soffice")
    if found:
        return found
    return MAC_SOFFICE if os.path.exists(MAC_SOFFICE) else "soffice"


def soffice_available(soffice: str) -> bool:
    """True when `soffice` resolves to an executable (on PATH or as a path).

    Render の Python ランタイムなど LibreOffice の無い環境では False(pptx は受け付けない)。
    """
    raise NotImplementedError


def pptx_to_pdf(data: bytes, soffice: str, timeout: float = 180.0) -> bytes:
    """Return the PDF bytes LibreOffice produces for the given .pptx bytes."""
    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        src = workdir / "input.pptx"
        src.write_bytes(data)
        command = [
            soffice,
            "--headless",
            "--norestore",
            f"-env:UserInstallation={(workdir / 'profile').as_uri()}",
            "--convert-to",
            "pdf",
            "--outdir",
            str(workdir),
            str(src),
        ]
        try:
            proc = subprocess.run(command, capture_output=True, timeout=timeout, check=False)
        except FileNotFoundError as exc:
            raise ConversionError(f"LibreOffice が見つかりません: {soffice}") from exc
        except subprocess.TimeoutExpired as exc:
            raise ConversionError(f"PDF 変換がタイムアウトしました({timeout:.0f}秒)") from exc

        out = workdir / "input.pdf"
        if not out.exists():
            detail = proc.stderr.decode(errors="replace").strip()[-300:]
            raise ConversionError(f"PDF に変換できませんでした: {detail}")
        return out.read_bytes()
