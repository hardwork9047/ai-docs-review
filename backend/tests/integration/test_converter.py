"""Integration tests for app.infra.converter — 偽の soffice スクリプトで配線を検証する。

実 LibreOffice による変換は E2E / 手動で確認する(CI に LibreOffice を入れない)。
"""

import stat
import sys
from pathlib import Path

import pytest

from app.infra import converter
from app.infra.converter import ConversionError, default_soffice, pptx_to_pdf, soffice_available


def _fake_soffice(tmp_path: Path, body: str) -> str:
    """Write an executable that mimics `soffice ... --outdir DIR SRC`."""
    script = tmp_path / "soffice"
    script.write_text(
        f"#!{sys.executable}\n"
        "import sys, pathlib, time\n"
        "args = sys.argv[1:]\n"
        "outdir = pathlib.Path(args[args.index('--outdir') + 1])\n"
        "src = pathlib.Path(args[-1])\n"
        f"{body}\n"
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return str(script)


def test_returns_the_pdf_written_next_to_the_input(tmp_path: Path) -> None:
    fake = _fake_soffice(
        tmp_path,
        "assert '--headless' in args and args[args.index('--convert-to') + 1] == 'pdf'\n"
        "assert src.read_bytes() == b'PPTX'\n"
        "(outdir / (src.stem + '.pdf')).write_bytes(b'%PDF-converted')",
    )
    assert pptx_to_pdf(b"PPTX", fake) == b"%PDF-converted"


def test_no_output_raises_conversion_error(tmp_path: Path) -> None:
    fake = _fake_soffice(tmp_path, "print('boom', file=sys.stderr); sys.exit(1)")
    with pytest.raises(ConversionError, match="boom"):
        pptx_to_pdf(b"PPTX", fake)


def test_timeout_raises_conversion_error(tmp_path: Path) -> None:
    fake = _fake_soffice(tmp_path, "time.sleep(5)")
    with pytest.raises(ConversionError, match="タイムアウト"):
        pptx_to_pdf(b"PPTX", fake, timeout=0.5)


def test_missing_binary_raises_conversion_error(tmp_path: Path) -> None:
    with pytest.raises(ConversionError, match="LibreOffice"):
        pptx_to_pdf(b"PPTX", str(tmp_path / "nope"))


def test_default_soffice_prefers_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(converter.shutil, "which", lambda name: "/usr/bin/soffice")
    assert default_soffice() == "/usr/bin/soffice"


def test_default_soffice_falls_back_to_mac_bundle(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(converter.shutil, "which", lambda name: None)
    monkeypatch.setattr(converter.os.path, "exists", lambda path: path == converter.MAC_SOFFICE)
    assert default_soffice() == converter.MAC_SOFFICE


def test_default_soffice_last_resort_is_plain_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(converter.shutil, "which", lambda name: None)
    monkeypatch.setattr(converter.os.path, "exists", lambda path: False)
    assert default_soffice() == "soffice"


def test_soffice_available_for_an_executable_path(tmp_path: Path) -> None:
    assert soffice_available(_fake_soffice(tmp_path, "pass"))


def test_soffice_unavailable_for_missing_binary(tmp_path: Path) -> None:
    assert not soffice_available(str(tmp_path / "nope"))
    assert not soffice_available("definitely-not-a-command-xyz")


def test_missing_binary_message_tells_the_user_to_upload_pdf(tmp_path: Path) -> None:
    with pytest.raises(ConversionError, match="PDF に書き出して"):
        pptx_to_pdf(b"PPTX", str(tmp_path / "nope"))
