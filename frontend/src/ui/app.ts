/**
 * DOM 描画・イベント結線層(ユニットテスト免除)。
 * 状態遷移・集計・文言はすべて logic/ にあり、ここは state を HTML にするだけ。
 */

import { escapeHtml as esc } from "../logic/escape";
import type { Issue, LintFinding } from "../logic/events";
import { parseEvent } from "../logic/events";
import { type Health, healthLabel, verdictLabel } from "../logic/labels";
import { splitLines } from "../logic/ndjson";
import { type Action, initialState, reduce, remaining, severityCounts } from "../logic/state";

let state = initialState;
let root: HTMLElement;
let health: Health | null = null;
/** 検印アニメーションは done に遷移した直後の1回だけ再生する */
let pressSeal = false;

/** Render the app into `el`, wire events, and start the Ollama health check. */
export function mount(el: HTMLElement): void {
  root = el;
  root.addEventListener("change", onChange);
  root.addEventListener("dragover", (e) => {
    e.preventDefault();
    root.querySelector(".tray")?.classList.add("over");
  });
  root.addEventListener("dragleave", () => root.querySelector(".tray")?.classList.remove("over"));
  root.addEventListener("drop", (e) => {
    e.preventDefault();
    const file = e.dataTransfer?.files[0];
    if (file) void startReview(file);
  });
  render();
  fetch("/api/health")
    .then((r) => r.json() as Promise<Health>)
    .then((h) => (health = h))
    .catch(() => (health = null))
    .finally(render);
}

function dispatch(action: Action): void {
  const before = state.phase;
  state = reduce(state, action);
  pressSeal = before !== "done" && state.phase === "done";
  render();
}

function onChange(e: Event): void {
  const input = e.target as HTMLInputElement;
  if (input.type === "file") {
    const file = input.files?.[0];
    if (file) void startReview(file);
    return;
  }
  const index = Number(input.dataset.index);
  if (input.dataset.kind === "issue") dispatch({ kind: "toggleIssue", index });
  if (input.dataset.kind === "lint") dispatch({ kind: "toggleLint", index });
}

async function startReview(file: File): Promise<void> {
  if (state.phase === "reviewing") return;
  dispatch({ kind: "start", fileName: file.name });
  const form = new FormData();
  form.append("file", file);
  try {
    const res = await fetch("/api/review", { method: "POST", body: form });
    if (!res.ok || !res.body) {
      const body = (await res.json().catch(() => ({}))) as { detail?: unknown };
      dispatch({ kind: "fail", message: String(body.detail ?? `HTTP ${res.status}`) });
      return;
    }
    const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
    let rest = "";
    for (;;) {
      const { value, done } = await reader.read();
      const split = splitLines(rest, done ? "\n" : value);
      rest = split.rest;
      for (const line of split.lines) dispatch({ kind: "event", event: parseEvent(line) });
      if (done) break;
    }
    dispatch({ kind: "end" });
  } catch (err) {
    dispatch({ kind: "fail", message: err instanceof Error ? err.message : String(err) });
  }
}

// ---------------------------------------------------------------- render

function render(): void {
  const lamp = healthLabel(health);
  root.innerHTML = `
    <div class="app">
      <header>
        <h1>部長レビュー</h1>
        <span class="lamp tone-${lamp.tone}">${esc(lamp.text)}</span>
      </header>
      <p class="lead">提出前のパワポを、多忙な部長の目で読みます。結論・依頼事項・意思決定に使える数字があるか。データはこのPCの外に出ません。</p>
      ${trayHtml()}
      ${state.phase === "idle" ? "" : sheetHtml()}
    </div>`;
}

function trayHtml(): string {
  const busy = state.phase === "reviewing";
  const label = busy ? `${esc(state.fileName ?? "")} を部長が読んでいます` : ".pptx をここにドロップ";
  return `
    <label class="tray${busy ? " busy" : ""}">
      <input type="file" accept=".pptx" ${busy ? "disabled" : ""} />
      <strong class="${busy ? "waiting" : ""}">${label}</strong>
      <small>クリックして選択もできます。読み取るのはテキスト・表・発表者ノートです(数十秒〜数分)</small>
    </label>`;
}

function sheetHtml(): string {
  const { meta, review, verdict } = state;
  const counts = review ? severityCounts(review) : null;
  const label = verdict ? verdictLabel(verdict) : null;
  const seal = label
    ? `<div class="seal${pressSeal ? " press" : ""}">${label.seal}</div>`
    : `<div class="seal pending">未決裁</div>`;
  return `
    <div class="sheet">
      <div class="approval">
        <div><div class="k">件名</div><div class="v title">${esc(state.fileName ?? "")}</div></div>
        <div><div class="k">スライド</div><div class="v">${meta ? `${meta.slide_count}枚` : "–"}</div></div>
        <div><div class="k">部長の評点</div><div class="v">${review ? review.score : "–"}</div></div>
        <div class="seal-box">${seal}</div>
      </div>
      ${label ? `<p class="verdict tone-${label.tone}">${esc(label.text)}</p>` : ""}
      ${meta?.truncated ? `<p class="empty">枚数が多いため、先頭の一部だけを部長に渡しました。</p>` : ""}
      ${state.error ? `<p class="error">${esc(state.error)}</p>` : ""}
      ${reviewHtml(counts)}
      ${lintHtml()}
    </div>`;
}

function reviewHtml(counts: Record<string, number> | null): string {
  const { meta, review } = state;
  if (!meta) return "";
  const who = `
    <div class="reviewer">
      <h2>${esc(meta.reviewer.icon)} ${esc(meta.reviewer.name)}の所見</h2>
      <span class="stance">${esc(meta.reviewer.stance)}</span>
    </div>`;
  if (!review) {
    return state.phase === "reviewing"
      ? `<section>${who}<p class="waiting">読んでいます</p></section>`
      : "";
  }
  const left = remaining(state).issues;
  const tally = counts ? `高${counts["高"]} / 中${counts["中"]} / 低${counts["低"]}` : "";
  return `
    <section>
      ${who}
      <p class="comment">${esc(review.summary)}</p>
      <ul class="good">${review.good_points.map((g) => `<li>${esc(g)}</li>`).join("")}</ul>
    </section>
    <section>
      <h2>朱書き<span class="count">${tally} — 未対応 ${left}/${review.issues.length}件</span></h2>
      ${review.issues.length ? review.issues.map(issueHtml).join("") : `<p class="empty">指摘はありません。</p>`}
    </section>`;
}

function issueHtml(issue: Issue, i: number): string {
  const done = state.checkedIssues[i] ?? false;
  return `
    <label class="item${done ? " done" : ""}">
      <input type="checkbox" data-kind="issue" data-index="${i}" ${done ? "checked" : ""} />
      <span class="body">
        <span class="chip">${issue.slide ? `S${issue.slide}` : "全体"}</span><span class="chip sev-${esc(issue.severity)}">${esc(issue.severity)}</span>
        <b>${esc(issue.problem)}</b><br />
        <span class="why">なぜ:${esc(issue.why)}</span><br />
        <span class="fix">${esc(issue.fix)}</span>
      </span>
    </label>`;
}

function lintHtml(): string {
  const { meta } = state;
  if (!meta) return "";
  const left = remaining(state).lint;
  const items = meta.lint.map((f: LintFinding, i: number) => {
    const done = state.checkedLint[i] ?? false;
    return `
      <label class="item${done ? " done" : ""}">
        <input type="checkbox" data-kind="lint" data-index="${i}" ${done ? "checked" : ""} />
        <span class="body"><span class="chip">${esc(f.rule)}</span>${esc(f.detail)}</span>
      </label>`;
  });
  return `
    <section>
      <h2>機械チェック<span class="count">表記ゆれ・半角カナ・長文・表紙 — 未対応 ${left}/${meta.lint.length}件</span></h2>
      ${items.length ? items.join("") : `<p class="empty">指摘はありません。</p>`}
    </section>`;
}
