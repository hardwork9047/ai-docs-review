/** Incremental NDJSON line splitting for streamed fetch responses. */

/**
 * Split `buffer + chunk` into complete lines and the trailing partial line.
 * Blank lines are dropped. Feed `rest` back in as `buffer` with the next chunk.
 */
export function splitLines(buffer: string, chunk: string): { lines: string[]; rest: string } {
  void buffer;
  void chunk;
  throw new Error("not implemented");
}
