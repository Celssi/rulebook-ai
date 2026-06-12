import type {
  CharacterHeader,
  LegacyAbility,
  Message,
  PendingJourney,
  SessionState,
  Shortcut,
  Source,
} from "../types";

const API = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getSession: () => request<SessionState>("/session"),
  updateSession: (body: Record<string, unknown>) =>
    request<SessionState>("/session", { method: "PUT", body: JSON.stringify(body) }),
  getSettingsMeta: () => request<Record<string, unknown>>("/session/settings-meta"),
  getGames: () => request<{ games: { id: string; label: string }[] }>("/games"),
  chat: (prompt: string) =>
    request<{
      answer: string;
      sources: Source[];
      route: string;
      messages: Message[];
      session_id: string;
    }>("/chat", { method: "POST", body: JSON.stringify({ prompt }) }),
  getHeader: () => request<CharacterHeader>("/brambletrek/header"),
  getCharacter: () =>
    request<{
      entity: Record<string, unknown>;
      abilities: LegacyAbility[];
      options: Record<string, { id: string; label: string }[]>;
      settings: Record<string, string>;
    }>("/brambletrek/character"),
  updateCharacter: (entity: Record<string, unknown>) =>
    request<{ entity: Record<string, unknown>; header: CharacterHeader }>(
      "/brambletrek/character",
      { method: "PUT", body: JSON.stringify({ entity }) }
    ),
  resetCharacter: () =>
    request<{ entity: Record<string, unknown>; header: CharacterHeader }>(
      "/brambletrek/character/reset",
      { method: "POST" }
    ),
  getRoster: () => request<{ entries: { id: string; name: string }[]; active_id: string }>("/brambletrek/roster"),
  createGnawborn: (name: string) =>
    request<{ entity: Record<string, unknown>; entries: { id: string; name: string }[] }>(
      "/brambletrek/roster",
      { method: "POST", body: JSON.stringify({ name }) }
    ),
  switchGnawborn: (id: string) =>
    request<SessionState>(`/brambletrek/roster/${id}/switch`, { method: "POST" }),
  deleteGnawborn: (id: string) =>
    request<{ entries: { id: string; name: string }[]; session: SessionState }>(
      `/brambletrek/roster/${id}`,
      { method: "DELETE" }
    ),
  getJourney: () => request<{ pending_journey: PendingJourney | null }>("/brambletrek/journey"),
  applyJourney: (event_index: number) =>
    request<Record<string, unknown>>("/brambletrek/journey/apply", {
      method: "POST",
      body: JSON.stringify({ event_index }),
    }),
  drawJourneyItem: (event_index: number) =>
    request<Record<string, unknown>>("/brambletrek/journey/draw-item", {
      method: "POST",
      body: JSON.stringify({ event_index }),
    }),
  finishJourney: () => request<Record<string, unknown>>("/brambletrek/journey/finish", { method: "POST" }),
  discardJourney: () => request<Record<string, unknown>>("/brambletrek/journey/discard", { method: "POST" }),
  bulkApplyJourney: () => request<Record<string, unknown>>("/brambletrek/journey/bulk-apply", { method: "POST" }),
  getShortcuts: () => request<{ shortcuts: Shortcut[] }>("/brambletrek/shortcuts"),
  runShortcut: (id: string) =>
    request<{
      answer: string;
      sources: Source[];
      route: string;
      messages: Message[];
      pending_journey: PendingJourney | null;
      entity: Record<string, unknown>;
      header: CharacterHeader;
    }>(`/brambletrek/shortcuts/${id}`, { method: "POST" }),
  getLonelog: (n = 50) => request<{ lines: string[]; path: string | null }>(`/brambletrek/lonelog?n_lines=${n}`),
  deckStatus: () => request<{ remaining: number; card_source: string }>("/deck/status"),
  drawDeck: (count = 1) =>
    request<{ formatted: string; remaining: number }>("/deck/draw", {
      method: "POST",
      body: JSON.stringify({ count }),
    }),
  resetDeck: () => request<{ remaining: number }>("/deck/reset", { method: "POST" }),
  rollDice: (expression: string) =>
    request<{ formatted: string; messages: Message[] }>("/deck/roll", {
      method: "POST",
      body: JSON.stringify({ expression }),
    }),
  reportCard: (card: string) =>
    request<{ formatted: string }>("/deck/report", {
      method: "POST",
      body: JSON.stringify({ card }),
    }),
  indexStatus: () => request<Record<string, unknown>>("/index/status"),
  reindex: (ingest_all = true, use_ocr = true) =>
    request<{ ok: boolean }>(`/index/reindex?ingest_all=${ingest_all}&use_ocr=${use_ocr}`, { method: "POST" }),
  get40kState: () =>
    request<{
      game_state: Record<string, unknown>;
      summary: string;
      options: Record<string, Record<string, string>>;
    }>("/warhammer40k/state"),
  update40kState: (game_state: Record<string, unknown>) =>
    request<{ game_state: Record<string, unknown>; summary: string }>("/warhammer40k/state", {
      method: "PUT",
      body: JSON.stringify({ game_state }),
    }),
};

export async function streamChat(
  prompt: string,
  onDone: (data: {
    answer: string;
    sources: Source[];
    route: string;
    messages: Message[];
  }) => void,
  onError: (err: Error) => void | Promise<void>
): Promise<void> {
  const res = await fetch(`${API}/chat/stream`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  if (!res.ok || !res.body) {
    onError(new Error(await res.text()));
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let gotDone = false;

  const handleBlock = (block: string) => {
    const trimmed = block.trim();
    if (!trimmed) return;
    let event = "message";
    let data = "";
    for (const line of trimmed.split("\n")) {
      if (line.startsWith("event:")) event = line.slice(6).trim();
      else if (line.startsWith("data:")) data = line.slice(5).trim();
    }
    if (event !== "done" || !data) return;
    try {
      onDone(JSON.parse(data));
      gotDone = true;
    } catch (e) {
      throw new Error(e instanceof Error ? e.message : "Invalid stream payload");
    }
  };

  const flushBuffer = (final = false) => {
    const parts = buffer.split("\n\n");
    if (final) {
      for (const part of parts) handleBlock(part);
      buffer = "";
      return;
    }
    buffer = parts.pop() || "";
    for (const part of parts) handleBlock(part);
  };

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (value) {
        buffer += decoder.decode(value, { stream: true });
        flushBuffer();
      }
      if (done) break;
    }
    flushBuffer(true);
    if (!gotDone) await onError(new Error("Stream ended without response"));
  } catch (e) {
    await onError(e instanceof Error ? e : new Error(String(e)));
  }
}
