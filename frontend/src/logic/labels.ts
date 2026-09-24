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
  void health;
  throw new Error("not implemented");
}

/** Headline verdict (検印). The reviewer's pass and the rule checks are shown separately. */
export function verdictLabel(verdict: Verdict): { text: string; tone: Tone } {
  void verdict;
  throw new Error("not implemented");
}
