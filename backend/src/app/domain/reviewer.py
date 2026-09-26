"""The single reviewer persona (上司・部長) and the per-page prompt given to the LLM.

誤字・表記ゆれは precheck、フォントサイズ・書体・文字量は metrics が受け持つ。
LLM には判断が要る「内容・図・グラフ」の採点と、ページごとの良い点・悪い点・修正点を任せる。
"""

from pydantic import BaseModel

from app.domain.pages import Page
from app.domain.review import CriterionScore
from app.domain.standard import StandardPack


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


_SYSTEM = """あなたは製造業の多忙な部長です。部下が作った提出前のプレゼン資料を1ページずつ読み、
「このページで意思決定できるか」「3分で要点が伝わるか」の視点で批評します。
入力は、ページの画像・抽出テキスト・計測値(フォントサイズ・書体・文字数)です。

採点(0〜100。90以上=このまま使える / 70〜89=軽微な修正 / 50〜69=作り直しが必要 / 50未満=要再考):
- content_score(内容): 主張が明確か、結論・根拠・依頼事項が読み取れるか、
  資料全体の流れの中で役割が分かるか
- figure_score(図): 写真・イラスト・図解・表が主張を助けているか、読みやすいか。
  画像に図が無ければ null
- chart_score(グラフ): 棒・折れ線・円などのグラフの軸・単位・凡例・強調が適切か。
  グラフが無ければ null
- フォントサイズ・書体・文字量は計測済み。点数は付けないが、問題があれば悪い点・修正点で触れる

ルール:
- good_points / bad_points / fixes はそれぞれ1〜3件。このページ固有の具体的な内容にする
- fixes は「何を・どう変えるか」が明日できる粒度で書く
  (例: タイトルを「A案500万円の承認依頼」に変える)
- 画像に写っている図やグラフは、テキストに無くても評価に含める
- 出力は指定された JSON スキーマに厳密に従う
"""

BOSS = Reviewer(
    profile=ReviewerProfile(
        id="boss",
        name="上司(部長)",
        icon="👔",
        stance="3分で意思決定したい。結論と依頼事項を最初に。",
        focus=["結論ファースト", "目的の明確さ", "図表の分かりやすさ", "読みやすさ"],
    ),
    system_prompt=_SYSTEM,
)


def build_page_prompt(
    page: Page, total: int, outline: list[str], measured: list[CriterionScore]
) -> str:
    """User message for reviewing one page: position, deck outline, text and measurements."""
    lines = [
        f"全{total}ページ中の{page.no}ページ目をレビューしてください。画像も添付しています。",
        "",
        "## 資料全体の構成",
        *(f"{i}. {title or '(タイトルなし)'}" for i, title in enumerate(outline, start=1)),
        "",
        "## このページのテキスト",
        f"[タイトル] {page.title or '(なし)'}",
        f"[本文]\n{page.body}",
    ]
    if page.notes:
        lines.append(f"[発表者ノート] {page.notes}")
    lines += ["", "## 計測値"]
    for m in measured:
        lines.append(
            f"- {m.criterion}: {m.note}(判定: {_band(m.score)})"
            if m.score is not None
            else f"- {m.criterion}: 計測不可"
        )
    lines.append(f"- 埋め込み画像: {page.image_count}個")
    return "\n".join(lines)


def _band(score: int) -> str:
    # 点数をそのまま渡すと小型モデルが「58点」を「58pt」と読み違えるため、言葉で渡す
    if score >= 80:
        return "良好"
    return "やや問題" if score >= 60 else "要改善"


def build_system_prompt(reviewer: Reviewer, pack: StandardPack | None) -> str:
    """The reviewer's system prompt, extended with the pack's review guidelines.

    Without a pack (or with no guidelines) this is exactly `reviewer.system_prompt`.
    """
    raise NotImplementedError
