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
  void summary;
  throw new Error("not implemented");
}

/** Colour band for a score. */
export function scoreTone(score: number | null): ScoreTone {
  void score;
  throw new Error("not implemented");
}

/** "82" or "–" when not applicable. */
export function formatScore(score: number | null): string {
  void score;
  throw new Error("not implemented");
}
