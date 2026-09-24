import { describe, expect, it } from "vitest";

import { checkKey, initialState, progress, reduce, remaining } from "../src/logic/state";
import { DONE, META, PAGE_ERROR, pageEvent } from "./fixtures";

const start = () => reduce(initialState, { kind: "start", fileName: "deck.pptx" });
const afterMeta = () => reduce(start(), { kind: "event", event: META });
const afterPages = () =>
  [pageEvent(3), PAGE_ERROR, pageEvent(1)].reduce(
    (s, event) => reduce(s, { kind: "event", event }),
    afterMeta(),
  );
const afterDone = () => reduce(afterPages(), { kind: "event", event: DONE });

describe("reduce", () => {
  it("start enters reviewing and clears any previous run", () => {
    const again = reduce(afterDone(), { kind: "start", fileName: "next.pdf" });
    expect(again).toEqual({ ...initialState, phase: "reviewing", fileName: "next.pdf" });
  });

  it("meta is stored while still reviewing", () => {
    const state = afterMeta();
    expect(state.phase).toBe("reviewing");
    expect(state.meta).toEqual(META);
  });

  it("pages are kept in page-number order and failures are collected", () => {
    const state = afterPages();
    expect(state.phase).toBe("reviewing");
    expect(state.pages.map((p) => p.no)).toEqual([1, 3]);
    expect(state.pageErrors).toEqual([{ no: 2, message: "timeout" }]);
  });

  it("done finishes the run with the summary", () => {
    const state = afterDone();
    expect(state.phase).toBe("done");
    expect(state.summary).toEqual(DONE.summary);
  });

  it("fail (HTTP error) moves to error", () => {
    const failed = reduce(start(), { kind: "fail", message: "400" });
    expect(failed.phase).toBe("error");
    expect(failed.error).toBe("400");
  });

  it("end while reviewing means the stream was cut, keeping pages received so far", () => {
    const cut = reduce(afterPages(), { kind: "end" });
    expect(cut.phase).toBe("error");
    expect(cut.error).toMatch(/途中/);
    expect(cut.pages).toHaveLength(2);
  });

  it("end after done changes nothing", () => {
    const state = afterDone();
    expect(reduce(state, { kind: "end" })).toEqual(state);
  });

  it("toggle ticks and unticks a key without mutating the previous state", () => {
    const done = afterDone();
    const key = checkKey("fix", 1, 0);
    const ticked = reduce(done, { kind: "toggle", key });
    expect(ticked.checked).toEqual([key]);
    expect(done.checked).toEqual([]);
    expect(reduce(ticked, { kind: "toggle", key }).checked).toEqual([]);
  });
});

describe("checkKey", () => {
  it("distinguishes fixes by page and index from lint findings", () => {
    const keys = [checkKey("fix", 1, 0), checkKey("fix", 1, 1), checkKey("fix", 2, 0)];
    expect(new Set([...keys, checkKey("lint", 0, 0)]).size).toBe(4);
  });
});

describe("progress", () => {
  it("counts reviewed and failed pages against the pages being reviewed", () => {
    expect(progress(afterPages())).toEqual({ done: 3, total: 3 });
  });

  it("is zero of zero before meta", () => {
    expect(progress(start())).toEqual({ done: 0, total: 0 });
  });
});

describe("remaining", () => {
  it("counts unticked fixes over all pages and unticked lint findings", () => {
    const state = reduce(afterDone(), { kind: "toggle", key: checkKey("fix", 3, 1) });
    const both = reduce(state, { kind: "toggle", key: checkKey("lint", 0, 0) });
    expect(remaining(both)).toEqual({ fixes: 3, lint: 1 });
  });

  it("is zero before anything arrives", () => {
    expect(remaining(initialState)).toEqual({ fixes: 0, lint: 0 });
  });
});
