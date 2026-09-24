/**
 * Review screen state as a pure reducer. ui/ dispatches actions and re-renders from state.
 *
 * phase: idle → reviewing(アップロード後)→ done(result 受信)| error(error 受信・HTTP失敗・途中切断)
 */

import type { MetaEvent, Review, ReviewEvent, Severity, Verdict } from "./events";

export type Phase = "idle" | "reviewing" | "done" | "error";

export interface ReviewState {
  phase: Phase;
  fileName: string | null;
  meta: MetaEvent | null;
  review: Review | null;
  verdict: Verdict | null;
  error: string | null;
  /** 「対応済み」チェック。index は review.issues / meta.lint の並びに対応 */
  checkedIssues: boolean[];
  checkedLint: boolean[];
}

export type Action =
  | { kind: "start"; fileName: string }
  | { kind: "event"; event: ReviewEvent }
  | { kind: "fail"; message: string }
  | { kind: "end" }
  | { kind: "toggleIssue"; index: number }
  | { kind: "toggleLint"; index: number };

export const initialState: ReviewState = {
  phase: "idle",
  fileName: null,
  meta: null,
  review: null,
  verdict: null,
  error: null,
  checkedIssues: [],
  checkedLint: [],
};

/**
 * Return the next state. Never mutates `state`.
 * `end` (stream closed) while still reviewing means the result never arrived → error.
 */
export function reduce(state: ReviewState, action: Action): ReviewState {
  switch (action.kind) {
    case "start":
      return { ...initialState, phase: "reviewing", fileName: action.fileName };
    case "event":
      return applyEvent(state, action.event);
    case "fail":
      return { ...state, phase: "error", error: action.message };
    case "end":
      return state.phase === "reviewing"
        ? { ...state, phase: "error", error: "レビュー結果を受け取る前に通信が途中で切れました" }
        : state;
    case "toggleIssue":
      return { ...state, checkedIssues: toggle(state.checkedIssues, action.index) };
    case "toggleLint":
      return { ...state, checkedLint: toggle(state.checkedLint, action.index) };
  }
}

function applyEvent(state: ReviewState, event: ReviewEvent): ReviewState {
  switch (event.type) {
    case "meta":
      return { ...state, meta: event, checkedLint: event.lint.map(() => false) };
    case "result":
      return {
        ...state,
        phase: "done",
        review: event.review,
        verdict: event.verdict,
        checkedIssues: event.review.issues.map(() => false),
      };
    case "error":
      return { ...state, phase: "error", error: event.message };
  }
}

function toggle(flags: boolean[], index: number): boolean[] {
  return flags.map((flag, i) => (i === index ? !flag : flag));
}

/** Count review issues per severity. */
export function severityCounts(review: Review): Record<Severity, number> {
  const counts: Record<Severity, number> = { 高: 0, 中: 0, 低: 0 };
  for (const issue of review.issues) counts[issue.severity] += 1;
  return counts;
}

/** Number of issues and lint findings not yet ticked as handled. */
export function remaining(state: ReviewState): { issues: number; lint: number } {
  const unticked = (flags: boolean[]) => flags.filter((flag) => !flag).length;
  return { issues: unticked(state.checkedIssues), lint: unticked(state.checkedLint) };
}
