/** Display wording derived from backend data (kept out of ui/ so it is testable). */

import type { LintFinding, Summary } from "./events";

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
  if (verdict.formal_passed === false) {
    return { text: "会社ルールの必須項目に違反があります", tone: "ng" };
  }
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

/**
 * Display parts for one rule-check finding: a tag (種類と必須/推奨), where it is
 * (ページ or 資料全体, empty for built-in checks without a page), and the cited clause.
 */
export function lintLabel(finding: LintFinding): {
  tag: string;
  place: string;
  source: string;
  must: boolean;
} {
  if (!finding.rule_id) return { tag: finding.rule, place: "", source: "", must: false };
  const must = finding.severity === "must";
  const page = finding.page ?? 0;
  return {
    tag: `${finding.rule}・${must ? "必須" : "推奨"}`,
    place: page > 0 ? `P${page}` : "資料全体",
    source: finding.source ?? "",
    must,
  };
}

/** "サンプル基準 v1.0", or null when no standard pack is configured. */
export function standardLabel(
  standard: { name: string; version: string } | null | undefined,
): string | null {
  return standard ? `${standard.name} v${standard.version}` : null;
}
