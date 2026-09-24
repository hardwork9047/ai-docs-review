import { describe, expect, it } from "vitest";

import { healthLabel, verdictLabel } from "../src/logic/labels";

describe("healthLabel", () => {
  it("is ok when Ollama is reachable and the model is pulled", () => {
    const label = healthLabel({ ok: true, model: "gemma4:e2b", model_ready: true, error: null });
    expect(label).toEqual({ text: "Ollama 接続OK / gemma4:e2b", tone: "ok" });
  });

  it("warns when the model is not pulled yet", () => {
    const label = healthLabel({ ok: true, model: "gemma4:e2b", model_ready: false, error: null });
    expect(label).toEqual({ text: "gemma4:e2b が未pull(ollama pull gemma4:e2b)", tone: "warn" });
  });

  it("is ng when Ollama is unreachable or the request failed", () => {
    const down = { ok: false, model: "m", model_ready: false, error: "refused" };
    expect(healthLabel(down)).toEqual({ text: "Ollama 未接続", tone: "ng" });
    expect(healthLabel(null)).toEqual({ text: "Ollama 未接続", tone: "ng" });
  });
});

describe("verdictLabel", () => {
  it("passes overall", () => {
    const label = verdictLabel({ passed: true, high_issues: 0, overall_passed: true });
    expect(label).toEqual({ text: "検印:提出OK", tone: "ok", seal: "承認" });
  });

  it("asks to fix rule-check findings when only those remain", () => {
    const label = verdictLabel({ passed: true, high_issues: 0, overall_passed: false });
    expect(label).toEqual({
      text: "部長はOK — ルールチェックの指摘を直せば提出可",
      tone: "warn",
      seal: "条件付",
    });
  });

  it("mentions high issues when the reviewer rejects", () => {
    const label = verdictLabel({ passed: false, high_issues: 2, overall_passed: false });
    expect(label).toEqual({ text: "差し戻し — 重要度「高」が2件", tone: "ng", seal: "差戻" });
  });

  it("falls back to score wording when there is no high issue", () => {
    const label = verdictLabel({ passed: false, high_issues: 0, overall_passed: false });
    expect(label).toEqual({ text: "差し戻し — 合格点に届いていません", tone: "ng", seal: "差戻" });
  });
});
