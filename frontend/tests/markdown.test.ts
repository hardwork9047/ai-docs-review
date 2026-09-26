import { describe, expect, it } from "vitest";

import { markdownFileName, toMarkdown } from "../src/logic/markdown";
import { checkKey, initialState, reduce, type ReviewState } from "../src/logic/state";
import { DONE, META, PAGE_ERROR, pageEvent } from "./fixtures";

function finished(): ReviewState {
  const events = [META, pageEvent(1), PAGE_ERROR, pageEvent(3, { title: "" }), DONE];
  const state = events.reduce(
    (s, event) => reduce(s, { kind: "event", event }),
    reduce(initialState, { kind: "start", fileName: "提案資料.pptx" }),
  );
  return reduce(state, { kind: "toggle", key: checkKey("fix", 1, 0) });
}

describe("toMarkdown", () => {
  const render = () => toMarkdown(finished());

  it("starts with the file name, total score and verdict", () => {
    const md = render();
    expect(md.startsWith("# 部長レビュー結果: 提案資料.pptx\n")).toBe(true);
    expect(md).toContain("- 総合スコア: **80** / 100");
    expect(md).toContain("- 判定: 機械チェックの指摘を直せば提出OK");
    expect(md).toContain("- 採点ページ: 2 / 3(失敗 1)");
  });

  it("notes truncation", () => {
    const md = render();
    expect(md).toContain("全4ページ中、先頭3ページのみ採点しました");
  });

  it("has a criteria table with dashes for not-applicable", () => {
    const md = render();
    expect(md).toContain("| 基準 | スコア | 備考 |\n|---|---|---|\n| 内容 | 70 | 2ページ |");
    expect(md).toContain("| グラフ | – |  |");
  });

  it("lists rule checks as a checklist", () => {
    const md = render();
    expect(md).toContain("## 機械チェック\n\n- [ ] 半角カナ: 半角カタカナが含まれています");
  });

  it("renders each page with scores, good/bad points and ticked fixes", () => {
    const md = render();
    expect(md).toContain("### P1 ページ1 — 80点");
    expect(md).toContain(
      "| 内容 | フォントサイズ | フォント | 図 | グラフ | 文字量 |\n|---|---|---|---|---|---|\n| 70 | 80 | 100 | 90 | – | 60 |",
    );
    expect(md).toContain("**良い点**\n\n- 結論が1行目にある");
    expect(md).toContain("**悪い点**\n\n- 数字の出典がない");
    expect(md).toContain("**修正点**\n\n- [x] 出典を脚注に入れる\n- [ ] グラフに単位を付ける");
  });

  it("keeps page order and includes failed pages", () => {
    const md = render();
    const p1 = md.indexOf("### P1");
    const p2 = md.indexOf("### P2 — 採点できませんでした\n\n> timeout");
    const p3 = md.indexOf("### P3 (タイトルなし) — 80点");
    expect(p1).toBeGreaterThan(-1);
    expect(p2).toBeGreaterThan(p1);
    expect(p3).toBeGreaterThan(p2);
  });

  it("escapes table pipes in notes", () => {
    const state = finished();
    const summary = {
      ...DONE.summary,
      criteria: [{ criterion: "フォント" as const, score: 70, note: "A | B" }],
    };
    expect(toMarkdown({ ...state, summary })).toContain("| フォント | 70 | A \\| B |");
  });

  it("says so when there are no rule-check findings", () => {
    const state = finished();
    const meta = { ...META, lint: [] };
    expect(toMarkdown({ ...state, meta })).toContain("## 機械チェック\n\n指摘はありません。");
  });
});

describe("markdownFileName", () => {
  it("replaces the extension with _review.md", () => {
    expect(markdownFileName("提案資料.pptx")).toBe("提案資料_review.md");
    expect(markdownFileName("a.b.pdf")).toBe("a.b_review.md");
  });

  it("falls back when there is no name", () => {
    expect(markdownFileName(null)).toBe("review.md");
  });
});

describe("toMarkdown with company rules", () => {
  it("shows the standard pack and cites the clause for company findings", () => {
    const state = finished();
    const meta = {
      ...META,
      standard: { name: "サンプル基準", version: "1.0" },
      lint: [
        {
          rule: "会社ルール",
          detail: "効果を言い切らない(「必ず」)",
          rule_id: "R-EXPR-01",
          severity: "must" as const,
          source: "ガイドライン §4.2",
          page: 3,
        },
      ],
    };
    const md = toMarkdown({ ...state, meta });
    expect(md).toContain("- 基準: サンプル基準 v1.0");
    expect(md).toContain(
      "- [ ] 会社ルール・必須(P3): 効果を言い切らない(「必ず」) — 根拠: ガイドライン §4.2",
    );
  });
});
