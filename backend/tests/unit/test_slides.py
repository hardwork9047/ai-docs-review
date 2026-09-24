"""Unit tests for app.domain.slides — LLM に渡すユーザープロンプトの組み立て。"""

from app.domain.slides import Slide, build_user_prompt


def test_prompt_reports_total_slide_count() -> None:
    slides = [Slide(no=1, title="表紙", body=""), Slide(no=2, title="結論", body="承認依頼")]
    prompt = build_user_prompt(slides, max_slides=40)
    assert "全2枚" in prompt


def test_each_slide_is_rendered_with_number_title_and_body() -> None:
    prompt = build_user_prompt([Slide(no=3, title="結論", body="A案を採用")], max_slides=40)
    assert "--- スライド3 ---\n[タイトル] 結論\nA案を採用" in prompt


def test_missing_title_is_shown_as_none_marker() -> None:
    prompt = build_user_prompt([Slide(no=1, title="", body="本文")], max_slides=40)
    assert "[タイトル] (なし)" in prompt


def test_notes_are_included_only_when_present() -> None:
    with_notes = build_user_prompt([Slide(no=1, title="t", body="b", notes="補足")], 40)
    without_notes = build_user_prompt([Slide(no=1, title="t", body="b")], 40)
    assert "[発表者ノート] 補足" in with_notes
    assert "発表者ノート" not in without_notes


def test_slides_beyond_max_are_dropped_but_total_is_kept() -> None:
    slides = [Slide(no=i, title=f"t{i}", body="") for i in range(1, 6)]
    prompt = build_user_prompt(slides, max_slides=3)
    assert "全5枚" in prompt
    assert "スライド3" in prompt
    assert "スライド4" not in prompt
