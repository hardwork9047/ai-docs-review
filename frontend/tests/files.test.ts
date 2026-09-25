import { describe, expect, it } from "vitest";

import { ACCEPT, ALL_FORMATS, acceptFor, rejectReason, uploadKind } from "../src/logic/files";

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

describe("acceptFor", () => {
  it("lists every supported format", () => {
    expect(acceptFor(ALL_FORMATS)).toBe(".pptx,.pdf");
    expect(acceptFor(["pdf", "pptx"])).toBe(".pptx,.pdf");
  });

  it("offers only PDF when pptx is unsupported", () => {
    expect(acceptFor(["pdf"])).toBe(".pdf");
  });
});

describe("rejectReason", () => {
  it("allows supported files", () => {
    expect(rejectReason("deck.pptx", ALL_FORMATS)).toBeNull();
    expect(rejectReason("deck.pdf", ["pdf"])).toBeNull();
  });

  it("asks to export pptx to PDF where LibreOffice is absent", () => {
    expect(rejectReason("deck.pptx", ["pdf"])).toMatch(/PDF に書き出して/);
  });

  it("lists the accepted formats for other files", () => {
    expect(rejectReason("deck.docx", ALL_FORMATS)).toBe(
      "アップロードできるのは .pptx と .pdf だけです",
    );
    expect(rejectReason("deck.docx", ["pdf"])).toBe("アップロードできるのは .pdf だけです");
  });
});
