/** Legacy roster placeholder before unnamed slots used empty names. */
const LEGACY_PLACEHOLDER = "Gnawborn";

export const UNNAMED_CHARACTER_LABEL = "New character";

export function rosterEntryLabel(name: string | undefined | null): string {
  const trimmed = String(name ?? "").trim();
  if (!trimmed || trimmed === LEGACY_PLACEHOLDER) {
    return UNNAMED_CHARACTER_LABEL;
  }
  return trimmed;
}
