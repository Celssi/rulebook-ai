import type { GameId } from "../types";

/** Games that refresh session messages after shortcuts (chat-integrated draws). */
export const GAMES_RELOAD_SESSION: GameId[] = [
  "sansibilia",
  "lighthouse",
  "apothecaria",
  "whispers",
  "ashes",
  "colostle",
];

export function shouldReloadSession(gameId: string): boolean {
  return GAMES_RELOAD_SESSION.includes(gameId as GameId);
}

export type GameLoaderKey = Exclude<GameId, "40k">;

export const GAME_LOADERS: Record<GameLoaderKey, string> = {
  brambletrek: "loadBrambletrek",
  sansibilia: "loadSansibilia",
  lighthouse: "loadLighthouse",
  apothecaria: "loadApothecaria",
  whispers: "loadWhispers",
  colostle: "loadColostle",
  ashes: "loadAshes",
};
