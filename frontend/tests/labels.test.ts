import { describe, expect, it } from "vitest";

import { formatScore, healthLabel, scoreTone, verdictLabel } from "../src/logic/labels";
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
