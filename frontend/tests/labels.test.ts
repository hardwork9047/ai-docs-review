import { describe, expect, it } from "vitest";

import { formatScore, healthLabel, lintLabel, scoreTone, standardLabel, verdictLabel } from "../src/logic/labels";
import { DONE } from "./fixtures";

const summary = (verdict: typeof DONE.summary.verdict) => ({ ...DONE.summary, verdict });

describe("healthLabel", () => {
  it("is ok when Ollama is reachable and the model is pulled", () => {
    const label = healthLabel({ ok: true, model: "gemma4:e2b", model_ready: true, error: null });
    expect(label).toEqual({ text: "Ollama 接続OK / gemma4:e2b", tone: "ok" });
  });

  it("warns when the model is not pulled yet", () => {
    const label = healthLabel({ ok: true, model: "gemma4:e2b", model_ready: false, error: null });
    expect(label.tone).toBe("warn");
  });

  it("is ng when Ollama is unreachable or the request failed", () => {
    expect(healthLabel(null)).toEqual({ text: "Ollama 未接続", tone: "ng" });
  });
});

describe("verdictLabel", () => {
  it("passes overall", () => {
    expect(verdictLabel(summary({ passed: true, overall_passed: true }))).toEqual({
      text: "提出OK",
      tone: "ok",
    });
  });

  it("asks to fix rule-check findings when only those remain", () => {
    expect(verdictLabel(summary({ passed: true, overall_passed: false }))).toEqual({
      text: "機械チェックの指摘を直せば提出OK",
      tone: "warn",
    });
  });

  it("asks for revision below the pass score", () => {
    expect(verdictLabel(summary({ passed: false, overall_passed: false }))).toEqual({
      text: "要修正",
      tone: "ng",
    });
  });

  it("reports when nothing could be scored", () => {
    expect(verdictLabel(summary(null))).toEqual({ text: "採点できませんでした", tone: "ng" });
  });
});

describe("scoreTone", () => {
  it.each([
    [100, "good"],
    [80, "good"],
    [79, "fair"],
    [60, "fair"],
    [59, "poor"],
    [0, "poor"],
    [null, "na"],
  ] as const)("%s → %s", (score, tone) => {
    expect(scoreTone(score)).toBe(tone);
  });
});

describe("formatScore", () => {
  it("prints numbers and a dash for not-applicable", () => {
    expect(formatScore(82)).toBe("82");
    expect(formatScore(null)).toBe("–");
  });
});

describe("verdictLabel with company rules", () => {
  it("fails formally on a must violation even if the reviewer passed", () => {
    const label = verdictLabel(summary({ passed: true, overall_passed: false, formal_passed: false }));
    expect(label).toEqual({ text: "会社ルールの必須項目に違反があります", tone: "ng" });
  });

  it("keeps the previous wording when formal_passed is true or absent", () => {
    expect(verdictLabel(summary({ passed: true, overall_passed: true, formal_passed: true })).text).toBe(
      "提出OK",
    );
    expect(verdictLabel(summary({ passed: false, overall_passed: false })).text).toBe("要修正");
  });
});

describe("lintLabel", () => {
  it("labels a company rule with severity, page and source", () => {
    const label = lintLabel({
      rule: "会社ルール",
      detail: "d",
      rule_id: "R-EXPR-01",
      severity: "must",
      source: "ガイドライン §4.2",
      page: 3,
    });
    expect(label).toEqual({ tag: "会社ルール・必須", place: "P3", source: "ガイドライン §4.2", must: true });
  });

  it("marks document-level and advisory findings", () => {
    const label = lintLabel({ rule: "会社ルール", detail: "d", rule_id: "R", severity: "should", source: "§2", page: 0 });
    expect(label).toEqual({ tag: "会社ルール・推奨", place: "資料全体", source: "§2", must: false });
  });

  it("leaves built-in checks as they were", () => {
    expect(lintLabel({ rule: "半角カナ", detail: "d" })).toEqual({ tag: "半角カナ", place: "", source: "", must: false });
  });
});

describe("standardLabel", () => {
  it("shows name and version", () => {
    expect(standardLabel({ name: "サンプル基準", version: "1.0" })).toBe("サンプル基準 v1.0");
  });

  it("is null without a pack", () => {
    expect(standardLabel(null)).toBeNull();
    expect(standardLabel(undefined)).toBeNull();
  });
});
