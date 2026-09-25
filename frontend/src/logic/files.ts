/** Upload file-type rules (the backend enforces the same by extension + magic bytes). */

export type UploadKind = "pptx" | "pdf";

/** Formats when the backend has not answered `/api/capabilities` yet. */
export const ALL_FORMATS: readonly UploadKind[] = ["pptx", "pdf"];

/** Value for `<input type="file" accept>`. */
export const ACCEPT = ".pptx,.pdf";

/** "pptx" / "pdf" for accepted file names (case-insensitive), otherwise null. */
export function uploadKind(fileName: string): UploadKind | null {
  const match = /\.(pptx|pdf)$/i.exec(fileName);
  return match ? (match[1]!.toLowerCase() as UploadKind) : null;
}

/** `accept` attribute for the formats this deployment supports (pptx first). */
export function acceptFor(formats: readonly UploadKind[]): string {
  return ALL_FORMATS.filter((f) => formats.includes(f))
    .map((f) => `.${f}`)
    .join(",");
}

/**
 * Why `fileName` cannot be uploaded here, or null when it can.
 * pptx on a deployment without LibreOffice gets a hint to export to PDF first.
 */
export function rejectReason(fileName: string, formats: readonly UploadKind[]): string | null {
  const kind = uploadKind(fileName);
  if (kind && formats.includes(kind)) return null;
  if (kind === "pptx") {
    return "この環境では pptx を採点できません。PowerPoint で PDF に書き出してからアップロードしてください";
  }
  return `アップロードできるのは ${acceptFor(formats).split(",").join(" と ")} だけです`;
}
