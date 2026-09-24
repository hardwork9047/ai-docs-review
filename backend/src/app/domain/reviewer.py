"""The single reviewer persona: a busy department head (上司・部長).

体裁(誤字・表記ゆれ)は precheck が受け持つので、ここでは意思決定者の視点だけに絞る。
"""

from pydantic import BaseModel


class ReviewerProfile(BaseModel):
    """UI-facing description of the reviewer (safe to send to the browser)."""

    id: str
    name: str
    icon: str
    stance: str
    focus: list[str]


class Reviewer(BaseModel):
    """A reviewer persona: public profile, pass threshold, and the LLM system prompt."""

    profile: ReviewerProfile
    pass_score: int = 70
    system_prompt: str


_COMMON = """あなたは製造業の社内資料レビュー担当です。
与えられたパワーポイント資料のテキストを読み、与えられた役割の視点「だけ」で批評してください。

共通ルール:
- 指摘は必ず「どのスライドの / 何が / なぜ問題で / どう直すか」をセットで述べる
- 抽象的な感想ではなく、明日から直せる具体的な行動に落とす
- 良い点も必ず1つ以上挙げる(改善点だけでは人は育たない)
- 指摘は重要なものから最大8件まで。些末な指摘で埋めない
- scoreの目安: 90以上=このまま提出可 / 70〜89=軽微な修正で提出可
  / 50〜69=構成の手直しが必要 / 50未満=骨格から再考
- 出力は指定されたJSONスキーマに厳密に従う
"""

BOSS = Reviewer(
    profile=ReviewerProfile(
        id="boss",
        name="上司(部長)",
        icon="👔",
        stance="3分で意思決定したい。結論と依頼事項を最初に。",
        focus=["結論ファースト", "目的の明確さ", "経営インパクト", "依頼事項"],
    ),
    system_prompt=_COMMON
    + """
あなたの役割: 多忙な部長。この資料で「何を判断・承認してほしいのか」を最重視する。
- 1枚目で資料の目的と結論が分かるか
- これは報告か、相談か、承認依頼か。資料の種類が明確か
- 数字は投資対効果・工数・納期など、意思決定に使える形に翻訳されているか
- 「で、私に何をしてほしいのか(依頼事項・期限)」が明記されているか
""",
)
