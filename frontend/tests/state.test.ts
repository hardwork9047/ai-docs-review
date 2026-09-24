import { describe, expect, it } from "vitest";

import type { MetaEvent, ResultEvent } from "../src/logic/events";
import { initialState, reduce, remaining, severityCounts } from "../src/logic/state";

const META: MetaEvent = {
  type: "meta",
  slide_count: 3,
  truncated: false,
  lint: [
    { rule: "半角カナ", detail: "d" },
    { rule: "長文", detail: "d" },
  ],
  reviewer: { id: "boss", name: "上司(部長)", icon: "👔", stance: "s", focus: [] },
};

const issue = (severity: "高" | "中" | "低") => ({
  slide: 1,
  severity,
  problem: "p",
  why: "w",
  fix: "f",
});

const RESULT: ResultEvent = {
  type: "result",
  review: {
    score: 60,
    summary: "s",
    good_points: ["g"],
    issues: [issue("高"), issue("中"), issue("中")],
  },
  verdict: { passed: false, high_issues: 1, overall_passed: false },
};

const start = () => reduce(initialState, { kind: "start", fileName: "deck.pptx" });
const afterMeta = () => reduce(start(), { kind: "event", event: META });
const afterResult = () => reduce(afterMeta(), { kind: "event", event: RESULT });

describe("reduce", () => {
  it("start enters reviewing and clears any previous run", () => {
    const again = reduce(afterResult(), { kind: "start", fileName: "next.pptx" });
    expect(again).toEqual({ ...initialState, phase: "reviewing", fileName: "next.pptx" });
  });

  it("meta keeps reviewing and prepares lint checkboxes", () => {
    const state = afterMeta();
    expect(state.phase).toBe("reviewing");
    expect(state.meta).toEqual(META);
    expect(state.checkedLint).toEqual([false, false]);
  });

  it("result finishes the run and prepares issue checkboxes", () => {
    const state = afterResult();
    expect(state.phase).toBe("done");
    expect(state.review).toEqual(RESULT.review);
    expect(state.verdict).toEqual(RESULT.verdict);
    expect(state.checkedIssues).toEqual([false, false, false]);
  });

  it("error event moves to error but keeps meta for the lint list", () => {
    const failed = reduce(afterMeta(), { kind: "event", event: { type: "error", message: "down" } });
    expect(failed.phase).toBe("error");
    expect(failed.error).toBe("down");
    expect(failed.meta).toEqual(META);
  });

  it("fail (HTTP error) moves to error", () => {
    const failed = reduce(start(), { kind: "fail", message: "400" });
    expect(failed.phase).toBe("error");
    expect(failed.error).toBe("400");
  });

  it("end while reviewing means the stream was cut", () => {
    const cut = reduce(afterMeta(), { kind: "end" });
    expect(cut.phase).toBe("error");
    expect(cut.error).toMatch(/途中/);
  });

  it("end after result changes nothing", () => {
    const state = afterResult();
    expect(reduce(state, { kind: "end" })).toEqual(state);
  });

  it("toggles issue and lint checkboxes without mutating the previous state", () => {
    const done = afterResult();
    const ticked = reduce(reduce(done, { kind: "toggleIssue", index: 1 }), {
      kind: "toggleLint",
      index: 0,
    });
    expect(ticked.checkedIssues).toEqual([false, true, false]);
    expect(ticked.checkedLint).toEqual([true, false]);
    expect(done.checkedIssues).toEqual([false, false, false]);
    expect(reduce(ticked, { kind: "toggleIssue", index: 1 }).checkedIssues[1]).toBe(false);
  });
});

describe("severityCounts", () => {
  it("counts issues per severity including zero", () => {
    expect(severityCounts(RESULT.review)).toEqual({ 高: 1, 中: 2, 低: 0 });
  });
});

describe("remaining", () => {
  it("counts unticked issues and lint findings", () => {
    const ticked = reduce(afterResult(), { kind: "toggleIssue", index: 0 });
    expect(remaining(ticked)).toEqual({ issues: 2, lint: 2 });
  });

  it("is zero before anything arrives", () => {
    expect(remaining(initialState)).toEqual({ issues: 0, lint: 0 });
  });
});
