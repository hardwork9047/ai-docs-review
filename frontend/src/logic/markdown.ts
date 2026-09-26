/** Markdown export of a finished review (downloaded as a .md file by ui/). */

import type { CriterionScore, PageResult } from "./events";
import { formatScore, lintLabel, standardLabel, verdictLabel } from "./labels";
import { checkKey, type PageFailure, type ReviewState } from "./state";

/** Render the review as Markdown: summary table, rule checks, then one section per page. */
export function toMarkdown(state: ReviewState): string {
  const { meta, summary } = state;
  const out: string[] = [`# 部長レビュー結果: ${state.fileName ?? ""}`, ""];

  if (summary) {
    out.push(`- 総合スコア: **${formatScore(summary.score)}** / 100`);
    out.push(`- 判定: ${verdictLabel(summary).text}`);
    const total = summary.reviewed_pages + summary.failed_pages;
    out.push(`- 採点ページ: ${summary.reviewed_pages} / ${total}(失敗 ${summary.failed_pages})`);
  }
  const standard = standardLabel(meta?.standard);
  if (standard) out.push(`- 基準: ${standard}`);
  if (meta?.truncated) {
    out.push(`- 全${meta.page_count}ページ中、先頭${meta.review_count}ページのみ採点しました`);
  }

  if (summary) {
    out.push("", "## 基準別スコア", "", "| 基準 | スコア | 備考 |", "|---|---|---|");
    for (const c of summary.criteria) {
      out.push(`| ${c.criterion} | ${formatScore(c.score)} | ${cell(c.note)} |`);
    }
  }

  out.push("", "## 機械チェック", "");
  const lint = meta?.lint ?? [];
  if (lint.length === 0) out.push("指摘はありません。");
  lint.forEach((f, i) => {
    const label = lintLabel(f);
    const place = label.place ? `(${label.place})` : "";
    const source = label.source ? ` — 根拠: ${label.source}` : "";
    out.push(`- ${box(state, checkKey("lint", 0, i))} ${label.tag}${place}: ${f.detail}${source}`);
  });

  out.push("", "## ページ別");
  const entries: (PageResult | PageFailure)[] = [...state.pages, ...state.pageErrors];
  for (const entry of entries.sort((a, b) => a.no - b.no)) {
    out.push("", ...("scores" in entry ? pageSection(state, entry) : failureSection(entry)));
  }
  return out.join("\n") + "\n";
}

/** Download file name: "<元ファイル名(拡張子なし)>_review.md". */
export function markdownFileName(fileName: string | null): string {
  if (!fileName) return "review.md";
  return `${fileName.replace(/\.[^.]+$/, "")}_review.md`;
}

function pageSection(state: ReviewState, page: PageResult): string[] {
  const scores: CriterionScore[] = page.scores;
  return [
    `### P${page.no} ${page.title || "(タイトルなし)"} — ${formatScore(page.score)}点`,
    "",
    `| ${scores.map((s) => s.criterion).join(" | ")} |`,
    `|${scores.map(() => "---").join("|")}|`,
    `| ${scores.map((s) => formatScore(s.score)).join(" | ")} |`,
    "",
    "**良い点**",
    "",
    ...page.good_points.map((g) => `- ${g}`),
    "",
    "**悪い点**",
    "",
    ...page.bad_points.map((b) => `- ${b}`),
    "",
    "**修正点**",
    "",
    ...page.fixes.map((f, i) => `- ${box(state, checkKey("fix", page.no, i))} ${f}`),
  ];
}

function failureSection(failure: PageFailure): string[] {
  return [`### P${failure.no} — 採点できませんでした`, "", `> ${failure.message}`];
}

function box(state: ReviewState, key: string): string {
  return state.checked.includes(key) ? "[x]" : "[ ]";
}

function cell(text: string): string {
  return text.replace(/\|/g, "\\|");
}
