/** Markdown export of a finished review (downloaded as a .md file by ui/). */

import type { ReviewState } from "./state";

/** Render the review as Markdown: summary table, rule checks, then one section per page. */
export function toMarkdown(state: ReviewState): string {
  void state;
  throw new Error("not implemented");
}

/** Download file name: "<元ファイル名(拡張子なし)>_review.md". */
export function markdownFileName(fileName: string | null): string {
  void fileName;
  throw new Error("not implemented");
}
