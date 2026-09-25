/** Incremental NDJSON line splitting for streamed fetch responses. */

/**
 * Split `buffer + chunk` into complete lines and the trailing partial line.
 * Blank lines are dropped. Feed `rest` back in as `buffer` with the next chunk.
 */
export function splitLines(buffer: string, chunk: string): { lines: string[]; rest: string } {
  const parts = (buffer + chunk).split("\n");
  const rest = parts.pop() ?? "";
  return { lines: parts.filter((line) => line.trim() !== ""), rest };
}
