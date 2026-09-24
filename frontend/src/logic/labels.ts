/** Display wording derived from backend data (kept out of ui/ so it is testable). */

import type { Verdict } from "./events";

/** Shape of `GET /api/health` (mirror of backend `OllamaHealth`). */
export interface Health {
  ok: boolean;
  model: string;
  model_ready: boolean;
  error: string | null;
}

export type Tone = "ok" | "warn" | "ng";

/** Connection lamp text. `null` means the health request itself failed. */
export function healthLabel(health: Health | null): { text: string; tone: Tone } {
  if (!health?.ok) return { text: "Ollama 未接続", tone: "ng" };
  if (!health.model_ready) {
    return { text: `${health.model} が未pull(ollama pull ${health.model})`, tone: "warn" };
  }
  return { text: `Ollama 接続OK / ${health.model}`, tone: "ok" };
}

/**
 * Headline verdict and the word on the 検印 seal.
 * The reviewer's pass and the rule checks are distinguished (warn = only rule checks remain).
 */
export function verdictLabel(verdict: Verdict): { text: string; tone: Tone; seal: string } {
  if (verdict.overall_passed) return { text: "検印:提出OK", tone: "ok", seal: "承認" };
  if (verdict.passed) {
    return { text: "部長はOK — ルールチェックの指摘を直せば提出可", tone: "warn", seal: "条件付" };
  }
  if (verdict.high_issues > 0) {
    return { text: `差し戻し — 重要度「高」が${verdict.high_issues}件`, tone: "ng", seal: "差戻" };
  }
  return { text: "差し戻し — 合格点に届いていません", tone: "ng", seal: "差戻" };
}
