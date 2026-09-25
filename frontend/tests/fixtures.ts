import type {
  CriterionScore,
  DoneEvent,
  MetaEvent,
  PageErrorEvent,
  PageEvent,
  PageResult,
} from "../src/logic/events";

const score = (criterion: CriterionScore["criterion"], value: number | null, note = "") => ({
  criterion,
  score: value,
  note,
});

export const META: MetaEvent = {
  type: "meta",
  page_count: 4,
  review_count: 3,
  truncated: true,
  lint: [
    { rule: "半角カナ", detail: "半角カタカナが含まれています" },
    { rule: "長文", detail: "スライド2: 1文が120字" },
  ],
  reviewer: { id: "boss", name: "上司(部長)", icon: "👔", stance: "s", focus: [] },
  criteria: ["内容", "フォントサイズ", "フォント", "図", "グラフ", "文字量"],
};

export function page(no: number, overrides: Partial<PageResult> = {}): PageResult {
  return {
    no,
    title: `ページ${no}`,
    scores: [
      score("内容", 70),
      score("フォントサイズ", 80, "最小12pt / 14pt未満 30%"),
      score("フォント", 100, "Meiryo"),
      score("図", 90),
      score("グラフ", null),
      score("文字量", 60, "300字"),
    ],
    score: 80,
    good_points: ["結論が1行目にある"],
    bad_points: ["数字の出典がない"],
    fixes: ["出典を脚注に入れる", "グラフに単位を付ける"],
    thumbnail: "",
    ...overrides,
  };
}

export const pageEvent = (no: number, overrides: Partial<PageResult> = {}): PageEvent => ({
  type: "page",
  result: page(no, overrides),
});

export const PAGE_ERROR: PageErrorEvent = { type: "page_error", no: 2, message: "timeout" };

export const DONE: DoneEvent = {
  type: "done",
  summary: {
    criteria: [
      score("内容", 70, "2ページ"),
      score("フォントサイズ", 80, "2ページ"),
      score("フォント", 100, "2ページ"),
      score("図", 90, "2ページ"),
      score("グラフ", null, ""),
      score("文字量", 60, "2ページ"),
    ],
    score: 80,
    reviewed_pages: 2,
    failed_pages: 1,
    verdict: { passed: true, overall_passed: false },
  },
};
