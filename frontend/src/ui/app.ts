/**
 * DOM 描画・イベント結線層(ユニットテスト免除)。
 * 状態遷移・集計・文言・Markdown 生成はすべて logic/ にあり、ここは state を DOM にするだけ。
 *
 * ページカードはサムネイル画像を含むため、受信のたびに作り直さず追記する(再デコードを避ける)。
 */

import { escapeHtml as esc, formatInline } from "../logic/escape";
import type { PageResult } from "../logic/events";
import { parseEvent } from "../logic/events";
import { ACCEPT, ALL_FORMATS, acceptFor, rejectReason, type UploadKind } from "../logic/files";
import { formatScore, type Health, healthLabel, scoreTone, verdictLabel } from "../logic/labels";
import { markdownFileName, toMarkdown } from "../logic/markdown";
import { splitLines } from "../logic/ndjson";
import {
  type Action,
  checkKey,
  initialState,
  type PageFailure,
  progress,
  reduce,
  remaining,
} from "../logic/state";

let state = initialState;
let health: Health | null = null;
/** このデプロイで受け付ける形式(/api/capabilities。LibreOffice の無い環境では pdf のみ) */
let formats: readonly UploadKind[] = ALL_FORMATS;
let root: HTMLElement;
const renderedPages = new Set<number>();

const ICON_DOC = `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6"/><path d="M9 15l2 2 4-4"/></svg>`;
const ICON_UP = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 16V4"/><path d="M6 10l6-6 6 6"/><path d="M4 20h16"/></svg>`;
const ICON_DL = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v12"/><path d="M6 10l6 6 6-6"/><path d="M4 20h16"/></svg>`;

/** Render the app into `el`, wire events, and start the Ollama health check. */
export function mount(el: HTMLElement): void {
  root = el;
  root.innerHTML = `
    <header class="topbar"><div class="wrap">
      <div class="brand"><span class="brand-mark">${ICON_DOC}</span>部長レビュー<small>ページ別 資料採点</small></div>
      <span class="pill" id="lamp">確認中</span>
    </div></header>
    <main class="wrap">
      <section class="hero">
        <h1>提出前の資料を、<em>部長の目</em>で1ページずつ採点</h1>
        <p>内容・フォントサイズ・フォント・図・グラフ・文字量の6基準で、良い点・悪い点・修正点を返します。</p>
        <label class="drop" id="drop">
          <input type="file" accept="${ACCEPT}" />
          <span class="drop-icon">${ICON_UP}</span>
          <span><strong id="drop-title">資料をドロップ、またはクリックして選択</strong>
          <span>対応形式<span id="formats"><i class="chip">PPTX</i><i class="chip">PDF</i></span> ・ 最大50MB ・ 1ページ15秒前後</span></span>
        </label>
        <div id="notice"></div>
      </section>
      <div id="status"></div>
      <div id="summary"></div>
      <div id="lint"></div>
      <div id="pages"></div>
    </main>
    <footer>採点は目安です。LLM の指摘は必ず人が確認してください。</footer>
    <dialog id="zoom"><img alt="" /></dialog>`;

  root.addEventListener("change", onChange);
  root.addEventListener("click", onClick);
  const drop = root.querySelector<HTMLElement>("#drop")!;
  drop.addEventListener("dragover", (e) => {
    e.preventDefault();
    drop.classList.add("over");
  });
  drop.addEventListener("dragleave", () => drop.classList.remove("over"));
  drop.addEventListener("drop", (e) => {
    e.preventDefault();
    drop.classList.remove("over");
    const file = e.dataTransfer?.files[0];
    if (file) void startReview(file);
  });

  render();
  fetch("/api/health")
    .then((r) => r.json() as Promise<Health>)
    .then((h) => (health = h))
    .catch(() => (health = null))
    .finally(renderLamp);
  fetch("/api/capabilities")
    .then((r) => r.json() as Promise<{ formats: UploadKind[] }>)
    .then((c) => {
      formats = c.formats;
      renderFormats();
    })
    .catch(() => undefined);
}

function renderFormats(): void {
  root.querySelector<HTMLInputElement>("#drop input")!.accept = acceptFor(formats);
  root.querySelector("#formats")!.innerHTML = formats
    .slice()
    .sort()
    .reverse()
    .map((f) => `<i class="chip">${f.toUpperCase()}</i>`)
    .join("");
  render();
}

function dispatch(action: Action): void {
  state = reduce(state, action);
  render();
}

function onChange(e: Event): void {
  const input = e.target as HTMLInputElement;
  if (input.type === "file") {
    const file = input.files?.[0];
    input.value = "";
    if (file) void startReview(file);
    return;
  }
  const key = input.dataset.key;
  if (key) {
    input.closest(".check")?.classList.toggle("done", input.checked);
    dispatch({ kind: "toggle", key });
  }
}

function onClick(e: Event): void {
  const target = e.target as HTMLElement;
  const tile = target.closest<HTMLElement>("[data-goto]");
  if (tile) {
    root.querySelector(`#page-${tile.dataset.goto}`)?.scrollIntoView({ behavior: "smooth" });
    return;
  }
  const thumb = target.closest<HTMLElement>("[data-zoom]");
  if (thumb) {
    const dialog = root.querySelector<HTMLDialogElement>("#zoom")!;
    dialog.querySelector("img")!.src = thumb.querySelector("img")!.src;
    dialog.showModal();
    return;
  }
  if (target.closest("#zoom")) {
    root.querySelector<HTMLDialogElement>("#zoom")!.close();
    return;
  }
  if (target.closest("#download")) download();
}

async function startReview(file: File): Promise<void> {
  if (state.phase === "reviewing") return;
  const reason = rejectReason(file.name, formats);
  if (reason) {
    dispatch({ kind: "fail", message: reason });
    return;
  }
  renderedPages.clear();
  root.querySelector("#pages")!.innerHTML = "";
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

function download(): void {
  const blob = new Blob([toMarkdown(state)], { type: "text/markdown;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = markdownFileName(state.fileName);
  a.click();
  URL.revokeObjectURL(a.href);
}

// ---------------------------------------------------------------- render

function render(): void {
  renderDrop();
  set("#notice", noticeHtml());
  set("#status", state.phase === "idle" ? "" : statusHtml());
  set("#summary", state.summary ? summaryHtml() : "");
  set("#lint", state.meta ? lintHtml() : "");
  renderPages();
}

function set(selector: string, html: string): void {
  const el = root.querySelector(selector)!;
  if (el.innerHTML !== html) el.innerHTML = html;
}

function renderLamp(): void {
  const lamp = healthLabel(health);
  const el = root.querySelector("#lamp")!;
  el.className = `pill tone-${lamp.tone}`;
  el.textContent = lamp.text;
}

function renderDrop(): void {
  const busy = state.phase === "reviewing";
  root.querySelector("#drop")!.classList.toggle("busy", busy);
  root.querySelector<HTMLInputElement>("#drop input")!.disabled = busy;
  root.querySelector("#drop-title")!.textContent = busy
    ? `${state.fileName ?? ""} を採点しています…`
    : "資料をドロップ、またはクリックして選択";
}

function noticeHtml(): string {
  if (state.error) return `<div class="notice error">${esc(state.error)}</div>`;
  if (state.meta?.truncated) {
    return `<div class="notice info">全${state.meta.page_count}ページ中、先頭${state.meta.review_count}ページを採点します。</div>`;
  }
  if (!formats.includes("pptx")) {
    return `<div class="notice info">この環境では PDF のみ採点できます。pptx は PowerPoint で PDF に書き出してからアップロードしてください。</div>`;
  }
  return "";
}

function statusHtml(): string {
  const { done, total } = progress(state);
  const pct = total ? Math.round((done / total) * 100) : 0;
  const byNo = new Map<number, PageResult | PageFailure>();
  for (const p of state.pages) byNo.set(p.no, p);
  for (const f of state.pageErrors) byNo.set(f.no, f);
  const tiles = Array.from({ length: total }, (_, i) => {
    const entry = byNo.get(i + 1);
    if (!entry) return `<span class="tile pending">${i + 1}</span>`;
    if (!("scores" in entry)) {
      return `<button class="tile failed" data-goto="${entry.no}" title="採点失敗">${entry.no}<b>!</b></button>`;
    }
    return `<button class="tile ${scoreTone(entry.score)}" data-goto="${entry.no}" title="${esc(entry.title)}">${entry.no}<b>${formatScore(entry.score)}</b></button>`;
  }).join("");
  const label = state.phase === "reviewing" ? "採点中" : state.phase === "done" ? "採点完了" : "中断";
  return `
    <section class="card">
      <div class="status">
        <span class="file">${esc(state.fileName ?? "")}</span>
        <span class="count">${label} ${done} / ${total || "–"} ページ</span>
      </div>
      <div class="bar"><i style="width:${pct}%"></i></div>
      <div class="map">${tiles}</div>
    </section>`;
}

function summaryHtml(): string {
  const summary = state.summary!;
  const verdict = verdictLabel(summary);
  const left = remaining(state);
  const bars = summary.criteria
    .map((c) => {
      const na = c.score === null;
      return `
        <div class="crit${na ? " na" : ""}" title="${esc(c.note)}">
          <span>${c.criterion}</span>
          <span class="track"><i style="width:${c.score ?? 0}%"></i></span>
          <span class="val">${formatScore(c.score)}</span>
        </div>`;
    })
    .join("");
  return `
    <section class="card">
      <div class="summary">
        <div class="donut" style="--p:${summary.score ?? 0}"><div><strong>${formatScore(summary.score)}</strong><span>総合スコア</span></div></div>
        <div>
          <span class="verdict tone-${verdict.tone}">${verdict.text}</span>
          <div class="criteria">${bars}</div>
          <div class="actions">
            <button class="btn" id="download">${ICON_DL}採点結果を Markdown でダウンロード</button>
            <span class="hint">未対応の修正点 ${left.fixes}件 ・ 機械チェック ${left.lint}件</span>
          </div>
        </div>
      </div>
    </section>`;
}

function lintHtml(): string {
  const lint = state.meta!.lint;
  const items = lint
    .map((f, i) => checkHtml(checkKey("lint", 0, i), `<span class="tag">${esc(f.rule)}</span>${esc(f.detail)}`))
    .join("");
  return `
    <section class="card">
      <h2>機械チェック<small>表記ゆれ・半角カナ・長文・表紙(LLM を使わない即時判定)</small></h2>
      ${items || `<p class="empty">指摘はありません。</p>`}
    </section>`;
}

function checkHtml(key: string, html: string): string {
  const done = state.checked.includes(key);
  return `
    <label class="check${done ? " done" : ""}">
      <input type="checkbox" data-key="${key}" ${done ? "checked" : ""} />
      <span class="text">${html}</span>
    </label>`;
}

function renderPages(): void {
  const container = root.querySelector("#pages")!;
  const entries: (PageResult | PageFailure)[] = [...state.pages, ...state.pageErrors];
  for (const entry of entries.sort((a, b) => a.no - b.no)) {
    if (renderedPages.has(entry.no)) continue;
    renderedPages.add(entry.no);
    const card = document.createElement("section");
    card.id = `page-${entry.no}`;
    card.innerHTML = "scores" in entry ? pageHtml(entry) : failureHtml(entry);
    card.className = "scores" in entry ? "card page" : "card page failed";
    // ページ番号順に差し込む
    const next = Array.from(container.children).find((c) => Number(c.id.slice(5)) > entry.no);
    container.insertBefore(card, next ?? null);
  }
}

function pageHtml(page: PageResult): string {
  const tone = scoreTone(page.score);
  const cells = page.scores
    .map(
      (s) =>
        `<div class="cell ${scoreTone(s.score)}" title="${esc(s.note)}"><b>${formatScore(s.score)}</b>${s.criterion}</div>`,
    )
    .join("");
  const list = (items: string[]) => `<ul>${items.map((t) => `<li>${formatInline(t)}</li>`).join("")}</ul>`;
  const fixes = page.fixes.map((f, i) => checkHtml(checkKey("fix", page.no, i), formatInline(f))).join("");
  const thumb = page.thumbnail
    ? `<button class="thumb" data-zoom><img alt="ページ${page.no}" src="data:image/jpeg;base64,${page.thumbnail}" loading="lazy" /></button>`
    : "<div></div>";
  return `
    ${thumb}
    <div>
      <div class="page-head">
        <h3><small>PAGE ${page.no}</small>${esc(page.title || "(タイトルなし)")}</h3>
        <span class="badge ${tone}">${formatScore(page.score)}</span>
      </div>
      <div class="cells">${cells}</div>
      <div class="notes">
        <div class="good-col"><h4>良い点</h4>${list(page.good_points)}</div>
        <div class="bad-col"><h4>悪い点</h4>${list(page.bad_points)}</div>
        <div class="fix-col"><h4>修正点</h4>${fixes}</div>
      </div>
    </div>`;
}

function failureHtml(failure: PageFailure): string {
  return `<h3>PAGE ${failure.no} — 採点できませんでした</h3><p class="empty">${esc(failure.message)}</p>`;
}
