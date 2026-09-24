/** Display wording derived from backend data (kept out of ui/ so it is testable). */

import type { Summary } from "./events";

/** Shape of `GET /api/health` (mirror of backend `OllamaHealth`). */
export interface Health {
  ok: boolean;
  model: string;
  model_ready: boolean;
  error: string | null;
}

export type Tone = "ok" | "warn" | "ng";

/** Colour band of a 0-100 score: >=80 good, >=60 fair, else poor; null = not applicable. */
export type ScoreTone = "good" | "fair" | "poor" | "na";

/** Connection lamp text. `null` means the health request itself failed. */
export function healthLabel(health: Health | null): { text: string; tone: Tone } {
  if (!health?.ok) return { text: "Ollama 未接続", tone: "ng" };
  if (!health.model_ready) {
    return { text: `${health.model} が未pull(ollama pull ${health.model})`, tone: "warn" };
  }
  return { text: `Ollama 接続OK / ${health.model}`, tone: "ok" };
}

/** Headline verdict for the whole document. */
export function verdictLabel(summary: Summary): { text: string; tone: Tone } {
  const { verdict } = summary;
  if (!verdict) return { text: "採点できませんでした", tone: "ng" };
  if (verdict.overall_passed) return { text: "提出OK", tone: "ok" };
  if (verdict.passed) return { text: "機械チェックの指摘を直せば提出OK", tone: "warn" };
  return { text: "要修正", tone: "ng" };
}

/** Colour band for a score. */
export function scoreTone(score: number | null): ScoreTone {
  if (score === null) return "na";
  if (score >= 80) return "good";
  return score >= 60 ? "fair" : "poor";
}

/** "82" or "–" when not applicable. */
export function formatScore(score: number | null): string {
  return score === null ? "–" : String(score);
}
