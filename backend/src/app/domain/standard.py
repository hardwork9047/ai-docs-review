"""Company standard pack: the customer's own document rules, checked deterministically.

基準パックは会社ごとのガイドライン(禁止表現・表記の統一・必須記載事項)を宣言的に持つ。
判定は正規表現と文字列照合だけで行い、同じ資料なら毎回同じ結果と根拠(条文)を返す。
LLM は使わない。
"""

import re
from typing import Literal

from pydantic import BaseModel, ValidationError

from app.domain.pages import Page
from app.domain.precheck import LintFinding

RULE_LABEL = "会社ルール"
_WHITESPACE = re.compile(r"\s+")
# 空白を詰めた後に、タイトル/本文・ページの境目として挟む文字。
# 正規表現の `.` は既定で改行に一致しないので、`料金.{0,3}円` のような規則も境目をまたがない
_BOUNDARY = "\n"


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
    compilable regexes, and `use` for `prefer` rules. Regexes are trusted admin input:
    pack authors must avoid catastrophic backtracking (nested quantifiers such as `(a+)+`).
    """
    if not isinstance(data, dict):
        raise PackError("パックの形式が不正です(name / version / rules を持つ辞書にする)")
    try:
        pack = StandardPack.model_validate(data)
    except ValidationError as exc:
        fields = ", ".join(".".join(str(p) for p in e["loc"]) for e in exc.errors())
        raise PackError(f"パックの項目が不正です: {fields}") from exc

    seen: set[str] = set()
    for rule in pack.rules:
        if rule.id in seen:
            raise PackError(f"ルール ID が重複しています: {rule.id}")
        seen.add(rule.id)
        if not rule.patterns or any(not p for p in rule.patterns):
            raise PackError(f"{rule.id}: patterns が空です")
        if rule.kind == "prefer" and not rule.use:
            raise PackError(f"{rule.id}: prefer ルールには use(推奨表記)が必要です")
        if rule.regex:
            for pattern in rule.patterns:
                try:
                    re.compile(pattern)
                except re.error as exc:
                    raise PackError(f"{rule.id}: 正規表現が不正です: {pattern}") from exc
    return pack


def check_pack(pages: list[Page], pack: StandardPack) -> list[LintFinding]:
    """Check page titles and bodies (not speaker notes) against the pack.

    Page-level findings come first (page order, then rule order, one per matched text);
    document-level `required` findings follow with page 0. Whitespace and line breaks are
    ignored when matching, because PDF text extraction inserts them at font changes and
    line wraps (e.g. 「業界 No.1」, 「必\nず」). Matches never span a title/body or a
    page boundary.
    """
    findings: list[LintFinding] = []
    for page in pages:
        text = _page_text(page)
        for rule in pack.rules:
            if rule.kind == "required":
                continue
            for hit in _matches(rule, text):
                detail = (
                    f"{rule.message}: 「{hit}」→「{rule.use}」"
                    if rule.kind == "prefer"
                    else f"{rule.message}(「{hit}」)"
                )
                findings.append(_finding(rule, detail, page.no))

    whole = _BOUNDARY.join(_page_text(p) for p in pages)
    for rule in pack.rules:
        if rule.kind == "required" and not _matches(rule, whole):
            findings.append(_finding(rule, rule.message, 0))
    return findings


def _matches(rule: Rule, text: str) -> list[str]:
    """Distinct matched strings in order of first appearance."""
    hits: list[str] = []
    for pattern in rule.patterns:
        regex = pattern if rule.regex else re.escape(_squash(pattern))
        for match in re.finditer(regex, text):
            if match.group(0) and match.group(0) not in hits:
                hits.append(match.group(0))
    return hits


def _page_text(page: Page) -> str:
    """Title and body squashed separately and kept apart, so matches never span them."""
    return f"{_squash(page.title)}{_BOUNDARY}{_squash(page.body)}"


def _squash(text: str) -> str:
    """Drop all whitespace (incl. full-width spaces and line breaks) before matching."""
    return _WHITESPACE.sub("", text)


def _finding(rule: Rule, detail: str, page: int) -> LintFinding:
    return LintFinding(
        rule=RULE_LABEL,
        detail=detail,
        rule_id=rule.id,
        severity=rule.severity,
        source=rule.source,
        page=page,
    )
