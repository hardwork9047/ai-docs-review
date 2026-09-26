"""Company standard pack: the customer's own document rules, checked deterministically.

基準パックは会社ごとのガイドライン(禁止表現・表記の統一・必須記載事項)を宣言的に持つ。
判定は正規表現と文字列照合だけで行い、同じ資料なら毎回同じ結果と根拠(条文)を返す。
LLM は使わない。
"""

from typing import Literal

from pydantic import BaseModel

from app.domain.pages import Page
from app.domain.precheck import LintFinding

RULE_LABEL = "会社ルール"


class PackError(ValueError):
    """The pack definition is invalid (duplicate ids, bad regex, missing fields...)."""


class Rule(BaseModel):
    """One company rule.

    - `forbid`: any of `patterns` on a page is a violation (e.g. 効果の言い切り)
    - `prefer`: `patterns` are discouraged spellings; `use` is the approved one
    - `required`: at least one of `patterns` must appear somewhere in the document
    `patterns` are literal strings unless `regex` is true.
    """

    id: str
    kind: Literal["forbid", "prefer", "required"]
    patterns: list[str]
    use: str = ""
    regex: bool = False
    severity: Literal["must", "should"] = "should"
    source: str
    message: str


class StandardPack(BaseModel):
    """A versioned set of company rules."""

    name: str
    version: str
    rules: list[Rule]


def parse_pack(data: object) -> StandardPack:
    """Validate a pack loaded from YAML/JSON. Raise `PackError` with a readable reason.

    Checks: required fields and types, unique rule ids, non-empty patterns,
    compilable regexes, and `use` for `prefer` rules.
    """
    raise NotImplementedError


def check_pack(pages: list[Page], pack: StandardPack) -> list[LintFinding]:
    """Check page titles and bodies (not speaker notes) against the pack.

    Page-level findings come first (page order, then rule order, one per matched text);
    document-level `required` findings follow with page 0.
    """
    raise NotImplementedError
