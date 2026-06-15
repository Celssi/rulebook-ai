import type { GmSoloHeader, GmSoloGameId } from "../games/gmSoloGames";
import type { Message, SessionState, Shortcut, Source } from "../types";
import { request } from "./core";

export function gmSoloApi(gameId: GmSoloGameId) {
  const base = `/${gameId}`;
  return {
    getHeader: () => request<GmSoloHeader>(`${base}/header`),
    getCharacter: () =>
      request<{
        entity: Record<string, unknown>;
        options: Record<string, unknown>;
        settings: Record<string, string>;
      }>(`${base}/character`),
    updateCharacter: (entity: Record<string, unknown>) =>
      request<{ entity: Record<string, unknown>; header: GmSoloHeader }>(
        `${base}/character`,
        { method: "PUT", body: JSON.stringify({ entity }) },
      ),
    levelUp: (hp_roll?: number) =>
      request<{
        entity: Record<string, unknown>;
        header: GmSoloHeader;
        summary: Record<string, unknown>;
      }>(`${base}/character/level-up`, {
        method: "POST",
        body: JSON.stringify(hp_roll != null ? { hp_roll } : {}),
      }),
    getCreationSummary: () =>
      request<Record<string, unknown>>(`${base}/character/summary`),
    getRoster: () =>
      request<{ entries: { id: string; name: string }[]; active_id: string }>(`${base}/roster`),
    createCharacter: (name: string) =>
      request<{ entity: Record<string, unknown>; entries: { id: string; name: string }[] }>(
        `${base}/roster`,
        { method: "POST", body: JSON.stringify({ name }) },
      ),
    switchCharacter: (id: string) =>
      request<SessionState>(`${base}/roster/${id}/switch`, { method: "POST" }),
    deleteCharacter: (id: string) =>
      request<{ entries: { id: string; name: string }[]; session: SessionState }>(
        `${base}/roster/${id}`,
        { method: "DELETE" },
      ),
    getShortcuts: () => request<{ shortcuts: Shortcut[] }>(`${base}/shortcuts`),
    runShortcut: (id: string, params?: Record<string, unknown>) =>
      request<{
        answer: string;
        sources: Source[];
        route: string;
        messages: Message[];
        entity: Record<string, unknown>;
        header: GmSoloHeader;
      }>(`${base}/shortcuts/${id}`, {
        method: "POST",
        body: JSON.stringify(params ?? {}),
      }),
    getLonelog: (n = 50) =>
      request<{ lines: string[]; path: string | null }>(`${base}/lonelog?n_lines=${n}`),
  };
}
