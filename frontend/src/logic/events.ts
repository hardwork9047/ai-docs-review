/**
 * Backend event types (mirror of backend `app.domain.service` / `review`) and parsing.
 * `/api/review` は NDJSON で meta → (page | page_error) × ページ数 → done の順に返す。
 */

export type Criterion = "内容" | "フォントサイズ" | "フォント" | "図" | "グラフ" | "文字量";

export interface CriterionScore {
  criterion: Criterion;
  /** 0-100。その基準が当てはまらないページ(図が無い等)は null */
  score: number | null;
  note: string;
}

export interface PageResult {
  no: number;
  title: string;
  /** 6基準すべて(meta.criteria の順) */
  scores: CriterionScore[];
  score: number | null;
  good_points: string[];
  bad_points: string[];
  fixes: string[];
  /** ページ画像(JPEG)の base64。空文字なら画像なし */
  thumbnail: string;
}

export interface Verdict {
  passed: boolean;
  overall_passed: boolean;
  /** must の会社ルール違反がゼロ(LLM の点に左右されない決定的な判定) */
  formal_passed?: boolean;
}

export interface Summary {
  criteria: CriterionScore[];
  score: number | null;
  reviewed_pages: number;
  failed_pages: number;
  verdict: Verdict | null;
}

export interface LintFinding {
  rule: string;
  detail: string;
  /** 会社ルール(基準パック)の指摘だけが持つ。組み込みの機械チェックは空文字・既定値 */
  rule_id?: string;
  /** "must" は形式判定を不合格にする。"should" は推奨 */
  severity?: "must" | "should";
  /** 根拠の条文(例: 提案書作成ガイドライン §4.2) */
  source?: string;
  /** 1 始まりのページ番号。0 は資料全体 */
  page?: number;
}

/** 採点に使った基準パック */
export interface StandardInfo {
  name: string;
  version: string;
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
  page_count: number;
  review_count: number;
  truncated: boolean;
  lint: LintFinding[];
  reviewer: ReviewerProfile;
  criteria: Criterion[];
  standard?: StandardInfo | null;
}

export interface PageEvent {
  type: "page";
  result: PageResult;
}

export interface PageErrorEvent {
  type: "page_error";
  no: number;
  message: string;
}

export interface DoneEvent {
  type: "done";
  summary: Summary;
}

export type ReviewEvent = MetaEvent | PageEvent | PageErrorEvent | DoneEvent;

const TYPES: ReadonlySet<string> = new Set(["meta", "page", "page_error", "done"]);

/** Parse one NDJSON line. Throws on invalid JSON or an unknown `type`. */
export function parseEvent(line: string): ReviewEvent {
  const data: unknown = JSON.parse(line);
  const type = typeof data === "object" && data !== null ? (data as { type?: unknown }).type : null;
  if (typeof type !== "string" || !TYPES.has(type)) {
    throw new Error(`unknown event: ${line}`);
  }
  return data as ReviewEvent;
}
