import { describe, expect, it } from "vitest";

import { splitLines } from "../src/logic/ndjson";

describe("splitLines", () => {
  it("returns complete lines and keeps the partial tail", () => {
    expect(splitLines("", '{"a":1}\n{"b":')).toEqual({ lines: ['{"a":1}'], rest: '{"b":' });
  });

  it("joins the previous partial line with the next chunk", () => {
    expect(splitLines('{"b":', "2}\n")).toEqual({ lines: ['{"b":2}'], rest: "" });
  });

  it("returns several lines from one chunk and drops blank lines", () => {
    expect(splitLines("", "x\n\ny\n")).toEqual({ lines: ["x", "y"], rest: "" });
  });

  it("keeps everything as rest when there is no newline yet", () => {
    expect(splitLines("ab", "c")).toEqual({ lines: [], rest: "abc" });
  });
});
