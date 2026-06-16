import type {
  CharacterHeader,
  JourneyActionResult,
  LegacyAbility,
  Message,
  PendingJourney,
  SessionState,
  Shortcut,
  Source,
} from "../types";

import { API, request } from "./core";

export interface ResourceDraftStat {
  stat: "health" | "morale" | "supplies";
  cards: string[];
  pair_sum: number;
  base: number;
  needs_bonus: boolean;
  card_values: number[];
}

export interface ResourceDraft {
  cards_by_stat: Record<string, string[]>;
  pending_bonus: string[];
  base_stats: { health: number; morale: number; supplies: number };
  final_stats?: { health: number; morale: number; supplies: number };
  stats: ResourceDraftStat[];
  remaining?: number;
}

export const api = {
  getSession: () => request<SessionState>("/session"),
  updateSession: (body: Record<string, unknown>) =>
    request<SessionState>("/session", { method: "PUT", body: JSON.stringify(body) }),
  getSettingsMeta: () => request<Record<string, unknown>>("/session/settings-meta"),
  getGames: () => request<{ games: { id: string; label: string }[] }>("/games"),
  getHowToPlay: (gameId: string) =>
    request<{ game_id: string; title: string; markdown: string }>(`/games/${gameId}/how-to-play`),
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
      resource_draft: ResourceDraft | null;
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
    request<JourneyActionResult>("/brambletrek/journey/apply", {
      method: "POST",
      body: JSON.stringify({ event_index }),
    }),
  drawJourneyItem: (event_index: number) =>
    request<JourneyActionResult>("/brambletrek/journey/draw-item", {
      method: "POST",
      body: JSON.stringify({ event_index }),
    }),
  finishJourney: () =>
    request<JourneyActionResult>("/brambletrek/journey/finish", { method: "POST" }),
  discardJourney: () =>
    request<JourneyActionResult>("/brambletrek/journey/discard", { method: "POST" }),
  bulkApplyJourney: () =>
    request<JourneyActionResult>("/brambletrek/journey/bulk-apply", { method: "POST" }),
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
  getBt2Header: () => request<CharacterHeader>("/brambletrek_2/header"),
  getBt2Character: () =>
    request<{
      entity: Record<string, unknown>;
      abilities: LegacyAbility[];
      options: Record<string, unknown>;
      settings: Record<string, string>;
    }>("/brambletrek_2/character"),
  updateBt2Character: (entity: Record<string, unknown>) =>
    request<{ entity: Record<string, unknown>; header: CharacterHeader }>(
      "/brambletrek_2/character",
      { method: "PUT", body: JSON.stringify({ entity }) }
    ),
  drawBt2Arrival: () =>
    request<{ card: string; label: string; band: string; entity: Record<string, unknown> }>(
      "/brambletrek_2/character/draw-arrival",
      { method: "POST" }
    ),
  resetBt2Character: () =>
    request<{ entity: Record<string, unknown>; header: CharacterHeader }>(
      "/brambletrek_2/character/reset",
      { method: "POST" }
    ),
  getBt2Roster: () =>
    request<{ entries: { id: string; name: string }[]; active_id: string }>("/brambletrek_2/roster"),
  createBt2Traveller: (name: string) =>
    request<{ entity: Record<string, unknown>; entries: { id: string; name: string }[] }>(
      "/brambletrek_2/roster",
      { method: "POST", body: JSON.stringify({ name }) }
    ),
  switchBt2Traveller: (id: string) =>
    request<SessionState>(`/brambletrek_2/roster/${id}/switch`, { method: "POST" }),
  deleteBt2Traveller: (id: string) =>
    request<{ entries: { id: string; name: string }[]; session: SessionState }>(
      `/brambletrek_2/roster/${id}`,
      { method: "DELETE" }
    ),
  getBt2Exploration: () =>
    request<{ pending_exploration: import("../types").PendingExploration | null }>(
      "/brambletrek_2/exploration"
    ),
  applyBt2Exploration: (event_index: number) =>
    request<import("../types").ExplorationActionResult>("/brambletrek_2/exploration/apply", {
      method: "POST",
      body: JSON.stringify({ event_index }),
    }),
  finishBt2Exploration: () =>
    request<import("../types").ExplorationActionResult>("/brambletrek_2/exploration/finish", {
      method: "POST",
    }),
  discardBt2Exploration: () =>
    request<import("../types").ExplorationActionResult>("/brambletrek_2/exploration/discard", {
      method: "POST",
    }),
  getBt2Hollow: () =>
    request<{ hollow: import("../types").HollowState | null }>("/brambletrek_2/hollow"),
  moveBt2Hollow: (row: number, col: number) =>
    request<{
      summary: string;
      entity: Record<string, unknown>;
      header: CharacterHeader;
      hollow: import("../types").HollowState | null;
    }>("/brambletrek_2/hollow/move", {
      method: "POST",
      body: JSON.stringify({ row, col }),
    }),
  getBt2Shortcuts: () => request<{ shortcuts: Shortcut[] }>("/brambletrek_2/shortcuts"),
  runBt2Shortcut: (id: string) =>
    request<{
      answer: string;
      sources: Source[];
      route: string;
      messages: Message[];
      pending_exploration: import("../types").PendingExploration | null;
      hollow: import("../types").HollowState | null;
      entity: Record<string, unknown>;
      header: CharacterHeader;
    }>(`/brambletrek_2/shortcuts/${id}`, { method: "POST" }),
  getBt2Lonelog: (n = 50) =>
    request<{ lines: string[]; path: string | null }>(`/brambletrek_2/lonelog?n_lines=${n}`),
  getVisitHeader: () => request<import("../types").VisitHeader>("/sansibilia/header"),
  getVisit: () =>
    request<{
      entity: Record<string, unknown>;
      options: Record<string, unknown>;
      settings: Record<string, string>;
    }>("/sansibilia/visit"),
  updateVisit: (entity: Record<string, unknown>) =>
    request<{ entity: Record<string, unknown>; header: import("../types").VisitHeader }>(
      "/sansibilia/visit",
      { method: "PUT", body: JSON.stringify({ entity }) }
    ),
  resetVisit: () =>
    request<{ entity: Record<string, unknown>; header: import("../types").VisitHeader }>(
      "/sansibilia/visit/reset",
      { method: "POST" }
    ),
  drawVisitCharacter: () =>
    request<{
      entity: Record<string, unknown>;
      header: import("../types").VisitHeader;
      cards: string[];
      archetype: string;
    }>("/sansibilia/visit/draw-character", { method: "POST" }),
  drawVisitDay: () =>
    request<{
      entity: Record<string, unknown>;
      header: import("../types").VisitHeader;
      messages: Message[];
      answer: string;
    }>("/sansibilia/visit/draw-day", { method: "POST" }),
  recordCityChange: (note = "") =>
    request<{ entity: Record<string, unknown>; header: import("../types").VisitHeader }>(
      "/sansibilia/visit/city-change",
      { method: "POST", body: JSON.stringify({ note }) }
    ),
  advanceVisitDay: (days_between?: number) =>
    request<{ entity: Record<string, unknown>; header: import("../types").VisitHeader }>(
      "/sansibilia/visit/advance-day",
      { method: "POST", body: JSON.stringify({ days_between }) }
    ),
  getSansibiliaRoster: () =>
    request<{ entries: { id: string; name: string }[]; active_id: string }>("/sansibilia/roster"),
  createVisit: (name: string) =>
    request<{ entity: Record<string, unknown>; entries: { id: string; name: string }[] }>(
      "/sansibilia/roster",
      { method: "POST", body: JSON.stringify({ name }) }
    ),
  switchVisit: (id: string) =>
    request<SessionState>(`/sansibilia/roster/${id}/switch`, { method: "POST" }),
  deleteVisit: (id: string) =>
    request<{ entries: { id: string; name: string }[]; session: SessionState }>(
      `/sansibilia/roster/${id}`,
      { method: "DELETE" }
    ),
  getSansibiliaShortcuts: () => request<{ shortcuts: Shortcut[] }>("/sansibilia/shortcuts"),
  runSansibiliaShortcut: (id: string) =>
    request<{
      answer: string;
      sources: Source[];
      route: string;
      messages: Message[];
      entity: Record<string, unknown>;
      header: import("../types").VisitHeader;
    }>(`/sansibilia/shortcuts/${id}`, { method: "POST" }),
  getSansibiliaLonelog: (n = 50) =>
    request<{ lines: string[]; path: string | null }>(`/sansibilia/lonelog?n_lines=${n}`),
  getLighthouseHeader: () => request<import("../types").WatchHeader>("/lighthouse/header"),
  getLighthouseWatch: () =>
    request<{
      entity: Record<string, unknown>;
      options: Record<string, unknown>;
      settings: Record<string, string>;
    }>("/lighthouse/watch"),
  updateLighthouseWatch: (entity: Record<string, unknown>) =>
    request<{ entity: Record<string, unknown>; header: import("../types").WatchHeader }>(
      "/lighthouse/watch",
      { method: "PUT", body: JSON.stringify({ entity }) }
    ),
  getLighthouseRoster: () =>
    request<{ entries: { id: string; name: string }[]; active_id: string }>("/lighthouse/roster"),
  createLighthouseWatch: (name: string) =>
    request<{ entity: Record<string, unknown>; entries: { id: string; name: string }[] }>(
      "/lighthouse/roster",
      { method: "POST", body: JSON.stringify({ name }) }
    ),
  switchLighthouseWatch: (id: string) =>
    request<SessionState>(`/lighthouse/roster/${id}/switch`, { method: "POST" }),
  deleteLighthouseWatch: (id: string) =>
    request<{ entries: { id: string; name: string }[]; session: SessionState }>(
      `/lighthouse/roster/${id}`,
      { method: "DELETE" }
    ),
  getLighthouseShortcuts: () => request<{ shortcuts: Shortcut[] }>("/lighthouse/shortcuts"),
  runLighthouseShortcut: (id: string) =>
    request<{
      answer: string;
      sources: Source[];
      route: string;
      messages: Message[];
      entity: Record<string, unknown>;
      header: import("../types").WatchHeader;
    }>(`/lighthouse/shortcuts/${id}`, { method: "POST" }),
  getLighthouseLonelog: (n = 50) =>
    request<{ lines: string[]; path: string | null }>(`/lighthouse/lonelog?n_lines=${n}`),
  getColostleHeader: () => request<import("../types").ColostleHeader>("/colostle/header"),
  getColostleCharacter: () =>
    request<{
      entity: Record<string, unknown>;
      options: Record<string, unknown>;
      settings: Record<string, string>;
    }>("/colostle/character"),
  updateColostleCharacter: (entity: Record<string, unknown>) =>
    request<{ entity: Record<string, unknown>; header: import("../types").ColostleHeader }>(
      "/colostle/character",
      { method: "PUT", body: JSON.stringify({ entity }) }
    ),
  getColostleRoster: () =>
    request<{ entries: { id: string; name: string }[]; active_id: string }>("/colostle/roster"),
  createColostleCharacter: (name: string) =>
    request<{ entity: Record<string, unknown>; entries: { id: string; name: string }[] }>(
      "/colostle/roster",
      { method: "POST", body: JSON.stringify({ name }) }
    ),
  switchColostleCharacter: (id: string) =>
    request<SessionState>(`/colostle/roster/${id}/switch`, { method: "POST" }),
  deleteColostleCharacter: (id: string) =>
    request<{ entries: { id: string; name: string }[]; session: SessionState }>(
      `/colostle/roster/${id}`,
      { method: "DELETE" }
    ),
  getColostleShortcuts: () => request<{ shortcuts: Shortcut[] }>("/colostle/shortcuts"),
  runColostleShortcut: (id: string) =>
    request<{
      answer: string;
      sources: Source[];
      route: string;
      messages: Message[];
      entity: Record<string, unknown>;
      header: import("../types").ColostleHeader;
    }>(`/colostle/shortcuts/${id}`, { method: "POST" }),
  getColostleLonelog: (n = 50) =>
    request<{ lines: string[]; path: string | null }>(`/colostle/lonelog?n_lines=${n}`),
  getApothecariaHeader: () => request<import("../types").CottageHeader>("/apothecaria/header"),
  getApothecariaCottage: () =>
    request<{
      entity: Record<string, unknown>;
      options: Record<string, unknown>;
      settings: Record<string, string>;
    }>("/apothecaria/cottage"),
  updateApothecariaCottage: (entity: Record<string, unknown>) =>
    request<{ entity: Record<string, unknown>; header: import("../types").CottageHeader }>(
      "/apothecaria/cottage",
      { method: "PUT", body: JSON.stringify({ entity }) }
    ),
  getApothecariaRoster: () =>
    request<{ entries: { id: string; name: string }[]; active_id: string }>("/apothecaria/roster"),
  createApothecariaCottage: (name: string) =>
    request<{ entity: Record<string, unknown>; entries: { id: string; name: string }[] }>(
      "/apothecaria/roster",
      { method: "POST", body: JSON.stringify({ name }) }
    ),
  switchApothecariaCottage: (id: string) =>
    request<SessionState>(`/apothecaria/roster/${id}/switch`, { method: "POST" }),
  deleteApothecariaCottage: (id: string) =>
    request<{ entries: { id: string; name: string }[]; session: SessionState }>(
      `/apothecaria/roster/${id}`,
      { method: "DELETE" }
    ),
  getApothecariaShortcuts: () => request<{ shortcuts: Shortcut[] }>("/apothecaria/shortcuts"),
  runApothecariaShortcut: (id: string, params?: Record<string, string>) =>
    request<{
      answer: string;
      sources: Source[];
      route: string;
      messages: Message[];
      entity: Record<string, unknown>;
      header: import("../types").CottageHeader;
    }>(`/apothecaria/shortcuts/${id}`, {
      method: "POST",
      body: JSON.stringify(params || {}),
    }),
  changeApothecariaLocale: (locale_id: string) =>
    request<{ entity: Record<string, unknown>; header: import("../types").CottageHeader }>(
      "/apothecaria/cottage/change-locale",
      { method: "POST", body: JSON.stringify({ locale_id }) }
    ),
  huntApothecariaReagent: (reagent_name: string) =>
    request<{ entity: Record<string, unknown>; header: import("../types").CottageHeader }>(
      "/apothecaria/cottage/hunt",
      { method: "POST", body: JSON.stringify({ reagent_name }) }
    ),
  completeApothecariaPotion: () =>
    request<{ entity: Record<string, unknown>; header: import("../types").CottageHeader }>(
      "/apothecaria/cottage/complete-potion",
      { method: "POST" }
    ),
  advanceApothecariaWeek: () =>
    request<{ entity: Record<string, unknown>; header: import("../types").CottageHeader }>(
      "/apothecaria/cottage/advance-week",
      { method: "POST" }
    ),
  advanceApothecariaDowntime: () =>
    request<{ entity: Record<string, unknown>; header: import("../types").CottageHeader }>(
      "/apothecaria/cottage/advance-downtime",
      { method: "POST" }
    ),
  buyApothecariaTool: (item_id: string) =>
    request<{ entity: Record<string, unknown>; header: import("../types").CottageHeader }>(
      "/apothecaria/cottage/buy-tool",
      { method: "POST", body: JSON.stringify({ item_id }) }
    ),
  buyApothecariaUpgrade: (item_id: string) =>
    request<{ entity: Record<string, unknown>; header: import("../types").CottageHeader }>(
      "/apothecaria/cottage/buy-upgrade",
      { method: "POST", body: JSON.stringify({ item_id }) }
    ),
  getApothecariaLonelog: (n = 50) =>
    request<{ lines: string[]; path: string | null }>(`/apothecaria/lonelog?n_lines=${n}`),
  getWhispersHeader: () => request<import("../types").InvestigationHeader>("/whispers/header"),
  getWhispersInvestigation: () =>
    request<{
      entity: Record<string, unknown>;
      settings: Record<string, string>;
    }>("/whispers/investigation"),
  updateWhispersInvestigation: (entity: Record<string, unknown>) =>
    request<{ entity: Record<string, unknown>; header: import("../types").InvestigationHeader }>(
      "/whispers/investigation",
      { method: "PUT", body: JSON.stringify({ entity }) }
    ),
  getWhispersRoster: () =>
    request<{ entries: { id: string; name: string }[]; active_id: string }>("/whispers/roster"),
  createWhispersInvestigation: (name: string) =>
    request<{ entity: Record<string, unknown>; entries: { id: string; name: string }[] }>(
      "/whispers/roster",
      { method: "POST", body: JSON.stringify({ name }) }
    ),
  switchWhispersInvestigation: (id: string) =>
    request<SessionState>(`/whispers/roster/${id}/switch`, { method: "POST" }),
  deleteWhispersInvestigation: (id: string) =>
    request<{ entries: { id: string; name: string }[]; session: SessionState }>(
      `/whispers/roster/${id}`,
      { method: "DELETE" }
    ),
  getWhispersShortcuts: () => request<{ shortcuts: Shortcut[] }>("/whispers/shortcuts"),
  runWhispersShortcut: (id: string) =>
    request<{
      answer: string;
      sources: Source[];
      route: string;
      messages: Message[];
      entity: Record<string, unknown>;
      header: import("../types").InvestigationHeader;
    }>(`/whispers/shortcuts/${id}`, { method: "POST" }),
  drawWhisper: () =>
    request<{
      entity: Record<string, unknown>;
      header: import("../types").InvestigationHeader;
      messages: Message[];
      answer: string;
    }>("/whispers/investigation/draw", { method: "POST" }),
  buildWhispersDeck: () =>
    request<{
      entity: Record<string, unknown>;
      header: import("../types").InvestigationHeader;
      messages: Message[];
      answer: string;
    }>("/whispers/investigation/build-deck", { method: "POST" }),
  getWhispersLonelog: (n = 50) =>
    request<{ lines: string[]; path: string | null }>(`/whispers/lonelog?n_lines=${n}`),
  getAshesHeader: () => request<import("../types").ScionHeader>("/ashes/header"),
  getAshesScion: () =>
    request<{
      entity: Record<string, unknown>;
      options: { classes: { id: string; label: string }[] };
      settings: Record<string, string>;
    }>("/ashes/scion"),
  updateAshesScion: (entity: Record<string, unknown>) =>
    request<{ entity: Record<string, unknown>; header: import("../types").ScionHeader }>(
      "/ashes/scion",
      { method: "PUT", body: JSON.stringify({ entity }) }
    ),
  getAshesRoster: () =>
    request<{ entries: { id: string; name: string }[]; active_id: string }>("/ashes/roster"),
  createAshesScion: (name: string) =>
    request<{ entity: Record<string, unknown>; entries: { id: string; name: string }[] }>(
      "/ashes/roster",
      { method: "POST", body: JSON.stringify({ name }) }
    ),
  switchAshesScion: (id: string) =>
    request<SessionState>(`/ashes/roster/${id}/switch`, { method: "POST" }),
  deleteAshesScion: (id: string) =>
    request<{ entries: { id: string; name: string }[]; session: SessionState }>(
      `/ashes/roster/${id}`,
      { method: "DELETE" }
    ),
  getAshesShortcuts: () => request<{ shortcuts: Shortcut[] }>("/ashes/shortcuts"),
  runAshesShortcut: (id: string) =>
    request<{
      answer: string;
      sources: Source[];
      route: string;
      messages: Message[];
      entity: Record<string, unknown>;
      header: import("../types").ScionHeader;
    }>(`/ashes/shortcuts/${id}`, { method: "POST" }),
  drawAshesGift: () =>
    request<{ entity: Record<string, unknown>; header: import("../types").ScionHeader; cards: string[]; gift: string }>(
      "/ashes/scion/draw-gift",
      { method: "POST" }
    ),
  getAshesLonelog: (n = 50) =>
    request<{ lines: string[] }>(`/ashes/lonelog?n_lines=${n}`),
  reasonEndingPreview: (reason_band: string) =>
    request<{ preview: string }>(
      `/brambletrek/reason-ending?reason_band=${encodeURIComponent(reason_band)}`
    ),
  drawCharacterTable: (table: "reason" | "background" | "trinket") =>
    request<{
      table: string;
      band_id: string;
      band_field: string;
      card_field: string;
      card: string;
      row_label: string;
      remaining: number;
    }>("/brambletrek/character/draw-table", {
      method: "POST",
      body: JSON.stringify({ table }),
    }),
  drawCharacterResources: () =>
    request<{
      draw_summary: string;
      resource_draft: ResourceDraft;
      remaining: number;
    }>("/brambletrek/character/draw-resources", { method: "POST" }),
  drawCharacterResourceBonus: (stat: "health" | "morale" | "supplies") =>
    request<{
      draw_summary: string;
      bonus_card: string;
      resource_draft: ResourceDraft;
      remaining: number;
    }>("/brambletrek/character/resource-bonus", {
      method: "POST",
      body: JSON.stringify({ stat }),
    }),
  applyCharacterResources: () =>
    request<{
      entity: Record<string, unknown>;
      header: CharacterHeader;
      resource_draft: null;
    }>("/brambletrek/character/apply-resources", { method: "POST" }),
  rollCharacterLegacy: () =>
    request<{
      roll_formatted: string;
      legacy_id: string;
      legacy_label: string;
    }>("/brambletrek/character/roll-legacy", { method: "POST" }),
  deckStatus: () => request<{ remaining: number; card_source: string }>("/deck/status"),
  drawDeck: (count = 1) =>
    request<{ formatted: string; remaining: number }>("/deck/draw", {
      method: "POST",
      body: JSON.stringify({ count }),
    }),
  resetDeck: () =>
    request<{ remaining: number; formatted: string }>("/deck/reset", { method: "POST" }),
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
