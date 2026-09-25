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
  return `${kind}:${page}:${index}`;
}

/**
 * Return the next state. Never mutates `state`.
 * `end` (stream closed) while still reviewing means `done` never arrived → error.
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
        ? { ...state, phase: "error", error: "採点が終わる前に通信が途中で切れました" }
        : state;
    case "toggle":
      return {
        ...state,
        checked: state.checked.includes(action.key)
          ? state.checked.filter((k) => k !== action.key)
          : [...state.checked, action.key],
      };
  }
}

function applyEvent(state: ReviewState, event: ReviewEvent): ReviewState {
  switch (event.type) {
    case "meta":
      return { ...state, meta: event };
    case "page":
      return {
        ...state,
        pages: [...state.pages, event.result].sort((a, b) => a.no - b.no),
      };
    case "page_error":
      return {
        ...state,
        pageErrors: [...state.pageErrors, { no: event.no, message: event.message }],
      };
    case "done":
      return { ...state, phase: "done", summary: event.summary };
  }
}

/** Pages finished (reviewed or failed) out of the pages being reviewed. */
export function progress(state: ReviewState): { done: number; total: number } {
  return {
    done: state.pages.length + state.pageErrors.length,
    total: state.meta?.review_count ?? 0,
  };
}

/** Number of fixes and lint findings not yet ticked as handled. */
export function remaining(state: ReviewState): { fixes: number; lint: number } {
  const open = (keys: string[]) => keys.filter((k) => !state.checked.includes(k)).length;
  const fixKeys = state.pages.flatMap((p) => p.fixes.map((_, i) => checkKey("fix", p.no, i)));
  const lintKeys = (state.meta?.lint ?? []).map((_, i) => checkKey("lint", 0, i));
  return { fixes: open(fixKeys), lint: open(lintKeys) };
}
