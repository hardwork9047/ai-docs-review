/**
 * Backend event types (mirror of backend `app.domain.service` / `review`) and parsing.
 * `/api/review` は NDJSON で meta → result | error の順に1行1イベントを返す。
 */

export type Severity = "高" | "中" | "低";

export interface Issue {
  /** 対象スライド番号。0 は資料全体への指摘 */
  slide: number;
  severity: Severity;
  problem: string;
  why: string;
  fix: string;
}

export interface Review {
  score: number;
  summary: string;
  good_points: string[];
  issues: Issue[];
}

export interface Verdict {
  passed: boolean;
  high_issues: number;
  overall_passed: boolean;
}

export interface LintFinding {
  rule: string;
  detail: string;
}

export interface ReviewerProfile {
  id: string;
  name: string;
  icon: string;
  stance: string;
  focus: string[];
}

export interface MetaEvent {
  type: "meta";
  slide_count: number;
  truncated: boolean;
  lint: LintFinding[];
  reviewer: ReviewerProfile;
}

export interface ResultEvent {
  type: "result";
  review: Review;
  verdict: Verdict;
}

export interface ErrorEvent {
  type: "error";
  message: string;
}

export type ReviewEvent = MetaEvent | ResultEvent | ErrorEvent;

/** Parse one NDJSON line. Throws on invalid JSON or an unknown `type`. */
export function parseEvent(line: string): ReviewEvent {
  const data: unknown = JSON.parse(line);
  const type = typeof data === "object" && data !== null ? (data as { type?: unknown }).type : null;
  if (type !== "meta" && type !== "result" && type !== "error") {
    throw new Error(`unknown event: ${line}`);
  }
  return data as ReviewEvent;
}
