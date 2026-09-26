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


MANUFACTURING = (
    Path(__file__).resolve().parents[1] / "fixtures" / "packs" / "sample_manufacturing.yaml"
)


def _manufacturing_findings(*bodies: str) -> list[tuple[str, int]]:
    from app.domain.pages import Page
    from app.domain.standard import check_pack

    pages = [Page(no=i, title=f"t{i}", body=b) for i, b in enumerate(bodies, start=1)]
    return [(f.rule_id, f.page) for f in check_pack(pages, load_pack(str(MANUFACTURING)))]


CLEAN_MANUFACTURING_DECK = (
    "目的: 2号ラインの不良率を下げるため、検査装置の更新を承認いただきたい",
    "投資額 500万円、削減額 年300万円、投資回収期間 1.7年",
    "スケジュール: 10月発注、12月立上げ。リスク: 立上げ遅延 → 対策: 予備日を確保",
    "作成日 2026/9/25 Rev.1 社外秘 治具の改善で歩留まりを改善",
)


def test_manufacturing_pack_is_valid_and_quiet_on_a_well_formed_deck() -> None:
    pack = load_pack(str(MANUFACTURING))
    assert pack.name.startswith("サンプル基準(製造業")
    assert _manufacturing_findings(*CLEAN_MANUFACTURING_DECK) == []


def test_manufacturing_pack_catches_typical_mistakes() -> None:
    findings = _manufacturing_findings(
        "不良は必ずゼロになります",  # 言い切り
        "かなり改善し、早急に対応",  # 曖昧な表現 ×2
        "原因は作業者のミス",  # 個人に原因を帰す
        "冶具を１０台追加",  # 誤字(冶具)、全角数字
    )
    rules = {rule for rule, _ in findings}
    assert {"R-EXPR-01", "R-VAGUE-01", "R-QUAL-01", "R-TERM-01", "R-NUM-01"} <= rules
    # 必須記載事項(目的・費用・効果・日程・リスク・版・機密区分)がすべて抜けている
    missing = {rule for rule, page in findings if page == 0}
    assert missing == {
        "R-REQ-01",
        "R-REQ-02",
        "R-REQ-03",
        "R-REQ-04",
        "R-REQ-05",
        "R-DOC-01",
        "R-CONF-01",
    }
