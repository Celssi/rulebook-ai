/** GM-led solo play games (full play profile). */
export const GM_SOLO_GAME_IDS = [
  "outgunned",
  "tor",
  "coriolis",
  "cosmere",
  "mlp",
  "dnd5e",
] as const;

export type GmSoloGameId = (typeof GM_SOLO_GAME_IDS)[number];

export function isGmSoloGameId(id: string): id is GmSoloGameId {
  return (GM_SOLO_GAME_IDS as readonly string[]).includes(id);
}

export interface GmSoloHeader {
  summary: string;
  name: string;
  story_mode?: string;
  [key: string]: unknown;
}

export interface OutgunnedHeader extends GmSoloHeader {
  mission_title?: string;
  ad_phase?: string;
  tension?: number;
  death_roulette_bullets?: number;
  role?: string;
  trope?: string;
}

export interface TorHeader extends GmSoloHeader {
  culture?: string;
  calling?: string;
  hope?: number;
  dread?: number;
  weary?: boolean;
  strider?: boolean;
  eye_awareness?: number;
  patron?: string;
  safe_haven?: string;
  journey_day?: number;
  hunt_region?: string;
}

export function isOutgunnedHeader(h: GmSoloHeader | import("../types").PlayHeader): h is OutgunnedHeader {
  return "tension" in h || "death_roulette_bullets" in h || "ad_phase" in h;
}

export function isTorHeader(h: GmSoloHeader): h is TorHeader {
  return "hope" in h || "dread" in h || "eye_awareness" in h;
}
