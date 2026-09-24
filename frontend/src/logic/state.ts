/**
 * Review screen state as a pure reducer. ui/ dispatches actions and re-renders from state.
 *
 * phase: idle → reviewing(アップロード後)→ done(done 受信)| error(HTTP失敗・途中切断)
 * ページ単位の失敗(page_error)は error にせず pageErrors に積む。
 */

import type { MetaEvent, PageResult, ReviewEvent, Summary } from "./events";

export type Phase = "idle" | "reviewing" | "done" | "error";

export interface PageFailure {
  no: number;
  message: string;
}

export interface ReviewState {
  phase: Phase;
  fileName: string | null;
  meta: MetaEvent | null;
  /** ページ番号順 */
  pages: PageResult[];
  pageErrors: PageFailure[];
  summary: Summary | null;
  error: string | null;
  /** 「対応済み」チェック。キーは checkKey() で作る */
  checked: string[];
}

export type Action =
  | { kind: "start"; fileName: string }
  | { kind: "event"; event: ReviewEvent }
  | { kind: "fail"; message: string }
  | { kind: "end" }
  | { kind: "toggle"; key: string };

export const initialState: ReviewState = {
  phase: "idle",
  fileName: null,
  meta: null,
  pages: [],
  pageErrors: [],
  summary: null,
  error: null,
  checked: [],
};

/** Checkbox key for a page's fix (`page`, 0-based `index`) or a lint finding (`page` = 0). */
export function checkKey(kind: "fix" | "lint", page: number, index: number): string {
  void kind;
  void page;
  void index;
  throw new Error("not implemented");
}

/**
 * Return the next state. Never mutates `state`.
 * `end` (stream closed) while still reviewing means `done` never arrived → error.
 */
export function reduce(state: ReviewState, action: Action): ReviewState {
  void state;
  void action;
  throw new Error("not implemented");
}

/** Pages finished (reviewed or failed) out of the pages being reviewed. */
export function progress(state: ReviewState): { done: number; total: number } {
  void state;
  throw new Error("not implemented");
}

/** Number of fixes and lint findings not yet ticked as handled. */
export function remaining(state: ReviewState): { fixes: number; lint: number } {
  void state;
  throw new Error("not implemented");
}
