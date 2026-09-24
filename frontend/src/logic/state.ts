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
  void state;
  void action;
  throw new Error("not implemented");
}

/** Count review issues per severity. */
export function severityCounts(review: Review): Record<Severity, number> {
  void review;
  throw new Error("not implemented");
}

/** Number of issues and lint findings not yet ticked as handled. */
export function remaining(state: ReviewState): { issues: number; lint: number } {
  void state;
  throw new Error("not implemented");
}
