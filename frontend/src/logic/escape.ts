const ENTITIES: Record<string, string> = {
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;",
};

/** Escape text for safe interpolation into HTML (element content and quoted attributes). */
export function escapeHtml(text: string): string {
  return text.replace(/[&<>"']/g, (c) => ENTITIES[c] ?? c);
}

/**
 * Escape `text`, then turn `**bold**` (which the LLM often emits) into <strong>.
 * No other Markdown is interpreted, so the result is safe to assign to innerHTML.
 */
export function formatInline(text: string): string {
  return escapeHtml(text).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
}
