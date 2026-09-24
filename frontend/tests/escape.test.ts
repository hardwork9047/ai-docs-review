import { describe, expect, it } from "vitest";

import { escapeHtml } from "../src/logic/escape";

describe("escapeHtml", () => {
  it("escapes HTML metacharacters", () => {
    expect(escapeHtml(`<a href="x" title='y'>&</a>`)).toBe(
      "&lt;a href=&quot;x&quot; title=&#39;y&#39;&gt;&amp;&lt;/a&gt;",
    );
  });

  it("leaves plain Japanese text unchanged", () => {
    expect(escapeHtml("結論ファースト")).toBe("結論ファースト");
  });
});
