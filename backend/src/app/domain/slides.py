"""Slide text model and prompt assembly for the LLM reviewer."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Slide:
    """Text extracted from one slide.

    `no` is 1-indexed. `body` joins non-title text frames and tables (tables are
    rendered as "[表]" followed by pipe-separated rows). Empty strings mean absent.
    """

    no: int
    title: str
    body: str
    notes: str = ""


def build_user_prompt(slides: list[Slide], max_slides: int) -> str:
    """Render slides as the user message for the reviewer LLM.

    Only the first `max_slides` slides are included; the header still reports the
    full slide count so the model knows the deck was truncated.
    """
    blocks = [_render(s) for s in slides[:max_slides]]
    return (
        f"以下は全{len(slides)}枚のパワーポイント資料から抽出したテキストです。\n"
        f"あなたの役割の視点でレビューし、JSONで出力してください。\n\n" + "\n\n".join(blocks)
    )


def _render(slide: Slide) -> str:
    block = f"--- スライド{slide.no} ---\n[タイトル] {slide.title or '(なし)'}\n{slide.body}"
    if slide.notes:
        block += f"\n[発表者ノート] {slide.notes}"
    return block
