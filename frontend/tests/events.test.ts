import { describe, expect, it } from "vitest";

import { parseEvent } from "../src/logic/events";

describe("parseEvent", () => {
  it("parses a known event type", () => {
    const event = parseEvent('{"type": "error", "message": "down"}');
    expect(event).toEqual({ type: "error", message: "down" });
  });

  it("rejects an unknown event type", () => {
    expect(() => parseEvent('{"type": "done"}')).toThrow(/unknown event/);
  });

  it("rejects non-object JSON", () => {
    expect(() => parseEvent("42")).toThrow(/unknown event/);
  });

  it("rejects invalid JSON", () => {
    expect(() => parseEvent("{oops")).toThrow(SyntaxError);
  });
});
