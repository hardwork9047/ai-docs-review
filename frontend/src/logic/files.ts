/** Upload file-type rules (the backend enforces the same by extension + magic bytes). */

export type UploadKind = "pptx" | "pdf";

/** Value for `<input type="file" accept>`. */
export const ACCEPT = ".pptx,.pdf";

/** "pptx" / "pdf" for accepted file names (case-insensitive), otherwise null. */
export function uploadKind(fileName: string): UploadKind | null {
  void fileName;
  throw new Error("not implemented");
}
