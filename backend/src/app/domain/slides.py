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
    raise NotImplementedError
