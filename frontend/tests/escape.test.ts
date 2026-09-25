import { describe, expect, it } from "vitest";

import { escapeHtml, formatInline } from "../src/logic/escape";

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

describe("formatInline", () => {
  it("renders **bold** as strong", () => {
    expect(formatInline("**構成:** 3つに分ける")).toBe("<strong>構成:</strong> 3つに分ける");
  });

  it("escapes HTML before formatting", () => {
    expect(formatInline("**<b>x</b>**")).toBe("<strong>&lt;b&gt;x&lt;/b&gt;</strong>");
  });

  it("leaves unpaired asterisks alone", () => {
    expect(formatInline("a ** b")).toBe("a ** b");
  });
});
