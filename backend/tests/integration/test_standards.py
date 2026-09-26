"""Integration tests for app.infra.standards — YAML の基準パックを読む。"""

from pathlib import Path

import pytest

from app.domain.standard import PackError
from app.infra.standards import load_pack

VALID = """
name: サンプル(介護向け提案営業)
version: "1.2"
rules:
  - id: R-FORBID-01
    kind: forbid
    patterns: [必ず改善]
    severity: must
    source: ガイドライン §4.2
    message: 効果を言い切らない
"""


def test_valid_yaml_is_loaded(tmp_path: Path) -> None:
    path = tmp_path / "pack.yaml"
    path.write_text(VALID, encoding="utf-8")
    pack = load_pack(str(path))
    assert (pack.name, pack.version, [r.id for r in pack.rules]) == (
        "サンプル(介護向け提案営業)",
        "1.2",
        ["R-FORBID-01"],
    )


def test_missing_file_is_a_pack_error(tmp_path: Path) -> None:
    with pytest.raises(PackError, match="読み込めません"):
        load_pack(str(tmp_path / "none.yaml"))


def test_broken_yaml_is_a_pack_error(tmp_path: Path) -> None:
    path = tmp_path / "pack.yaml"
    path.write_text("name: [unclosed", encoding="utf-8")
    with pytest.raises(PackError, match="YAML"):
        load_pack(str(path))


def test_invalid_pack_content_is_a_pack_error(tmp_path: Path) -> None:
    path = tmp_path / "pack.yaml"
    path.write_text("name: x\nversion: '1'\nrules: []\nextra: [", encoding="utf-8")
    with pytest.raises(PackError):
        load_pack(str(path))
