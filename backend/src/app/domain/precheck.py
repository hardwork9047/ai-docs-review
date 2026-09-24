"""Deterministic rule checks that need no LLM.

判断が要らない指摘(表記ゆれ・半角カナ・長文・表紙の必須項目)は正規表現とルールで拾い、
LLM には判断が要る批評だけを任せる。結果は毎回同じで説明可能。
"""

from dataclasses import dataclass

from app.domain.slides import Slide

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


def run_precheck(slides: list[Slide]) -> list[LintFinding]:
    """Run all deterministic checks over the deck and return findings in rule order.

    Checks titles and bodies (not speaker notes). An empty list means the deck passes.
    """
    raise NotImplementedError
