"""Acceptance tests: the planted-violation sample deck is detected exactly and repeatably.

Copilot 等との比較実験で主張する「検出率・再現性」を、仕込んだ正解表で保証する。
"""

import io
from collections import Counter
from pathlib import Path

from app.domain.pages import Page
from app.domain.precheck import LintFinding, run_precheck
from app.domain.standard import check_pack
from app.infra.pptx_reader import read_slide_texts
from app.infra.standards import load_pack
from tests.fixtures.violation_deck import EXPECTED, PACK_PATH, SLIDES, build_pptx


def _pages() -> list[Page]:
    return [Page(no=i, title=t, body=b) for i, (t, b) in enumerate(SLIDES, start=1)]


def _findings(pages: list[Page]) -> list[LintFinding]:
    return run_precheck(pages) + check_pack(pages, load_pack(str(PACK_PATH)))


def _keys(findings: list[LintFinding]) -> Counter[tuple[str, int]]:
    return Counter((f.rule_id or f.rule, f.page) for f in findings)


def test_all_20_planted_violations_are_detected_and_nothing_else() -> None:
    assert len(EXPECTED) == 20
    assert _keys(_findings(_pages())) == Counter(EXPECTED)


def test_results_are_identical_across_runs() -> None:
    runs = [_findings(_pages()) for _ in range(3)]
    assert runs[0] == runs[1] == runs[2]


def test_every_company_finding_cites_its_guideline_clause() -> None:
    company = [f for f in _findings(_pages()) if f.rule_id]
    assert company
    assert all(f.source for f in company)


def test_the_generated_pptx_gives_the_same_findings(tmp_path: Path) -> None:
    path = tmp_path / "deck.pptx"
    build_pptx(path)
    slides = read_slide_texts(path.read_bytes())
    pages = [Page(no=i, title=s.title, body=s.body) for i, s in enumerate(slides, start=1)]
    assert _keys(_findings(pages)) == Counter(EXPECTED)


def test_answer_key_lists_every_expected_violation() -> None:
    from tests.fixtures.violation_deck import answer_key_markdown

    key = answer_key_markdown()
    assert key.count("\n| ") == len(EXPECTED) + 1  # 見出し行 + 20 行
    assert io.StringIO(key).readline().startswith("# ")


SAMPLE_PDF = Path(__file__).resolve().parents[3] / "samples" / "violation-deck.pdf"


def test_the_pdf_version_gives_the_same_findings() -> None:
    # Regression: PDF 経路では抽出テキストの空白・改行で 2 件を取りこぼしていた
    from app.infra.pdf_reader import read_pdf

    pages = read_pdf(SAMPLE_PDF.read_bytes())
    assert _keys(_findings(pages)) == Counter(EXPECTED)
