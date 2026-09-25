"""Deterministic rule checks that need no LLM.

判断が要らない指摘(表記ゆれ・半角カナ・長文・表紙の必須項目)は正規表現とルールで拾い、
LLM には判断が要る批評だけを任せる。結果は毎回同じで説明可能。
"""

import re
from dataclasses import dataclass

from app.domain.pages import Page

# 両方の表記が資料内に共存していたら指摘する表記ゆれペア(社内標準に合わせて育てる)
YURAGI_PAIRS: list[tuple[str, str]] = [
    ("サーバー", "サーバ"),
    ("ユーザー", "ユーザ"),
    ("コンピューター", "コンピュータ"),
    ("ください", "下さい"),
    ("いたします", "致します"),
    ("打ち合わせ", "打合せ"),
]

MAX_LINE_LEN = 90  # 本文の1行がこれを超えたら「長文」


@dataclass(frozen=True)
class LintFinding:
    """One rule-check finding. `rule` is the category label, `detail` the message."""

    rule: str
    detail: str


def run_precheck(pages: list[Page]) -> list[LintFinding]:
    """Run all deterministic checks over the deck and return findings in rule order.

    Checks titles and bodies (not speaker notes). An empty list means the deck passes.
    """
    findings: list[LintFinding] = []
    full_text = "\n".join(f"{s.title}\n{s.body}" for s in pages)

    for long_form, short_form in YURAGI_PAIRS:
        # 短い表記は長い表記の部分文字列になりうるので、直後に「ー」が続くものは除外する
        if long_form in full_text and re.search(rf"{re.escape(short_form)}(?!ー)", full_text):
            findings.append(
                LintFinding("表記ゆれ", f"「{long_form}」と「{short_form}」が混在しています")
            )

    if re.search(r"[ｦ-ﾟ]", full_text):
        findings.append(LintFinding("半角カナ", "半角カタカナが含まれています(全角に統一推奨)"))

    for slide in pages:
        for line in slide.body.splitlines():
            if len(line) > MAX_LINE_LEN:
                detail = f"スライド{slide.no}: 1文が{len(line)}字(分割か箇条書き化を推奨)"
                findings.append(LintFinding("長文", detail))

    if pages and not pages[0].title:
        findings.append(LintFinding("必須項目", "表紙のタイトルが空です"))

    return findings
