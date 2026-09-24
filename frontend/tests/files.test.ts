import { describe, expect, it } from "vitest";

import { ACCEPT, uploadKind } from "../src/logic/files";

describe("uploadKind", () => {
  it.each([
    ["deck.pptx", "pptx"],
    ["DECK.PPTX", "pptx"],
    ["資料 v2.pdf", "pdf"],
  ])("accepts %s", (name, kind) => {
    expect(uploadKind(name)).toBe(kind);
  });

  it.each(["deck.ppt", "deck.key", "deck.docx", "pdf", "deck.pdf.zip", ""])("rejects %s", (name) => {
    expect(uploadKind(name)).toBeNull();
  });

  it("matches the file input accept list", () => {
    expect(ACCEPT).toBe(".pptx,.pdf");
  });
});
