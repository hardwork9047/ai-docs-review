import { describe, expect, it } from "vitest";

import { parseEvent } from "../src/logic/events";

describe("parseEvent", () => {
  it.each(["meta", "page", "page_error", "done"])("accepts %s events", (type) => {
    expect(parseEvent(JSON.stringify({ type })).type).toBe(type);
  });

  it("returns the parsed payload", () => {
    expect(parseEvent('{"type": "page_error", "no": 2, "message": "x"}')).toEqual({
      type: "page_error",
      no: 2,
      message: "x",
    });
  });

  it("rejects an unknown event type", () => {
    expect(() => parseEvent('{"type": "result"}')).toThrow(/unknown event/);
  });

  it("rejects non-object JSON", () => {
    expect(() => parseEvent("42")).toThrow(/unknown event/);
  });

  it("rejects invalid JSON", () => {
    expect(() => parseEvent("{oops")).toThrow(SyntaxError);
  });
});
