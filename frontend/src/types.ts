export interface Message {
  role: "user" | "assistant";
  content: string;
}

export interface Source {
  source_label?: string;
  source_file?: string;
  page?: number | string;
  score?: number;
  faction?: string;
  text?: string;
}

export interface SessionState {
  session_id: string;
  selected_game_id: string;
  chat_provider: string;
  mode: string;
  top_k: number;
  retrieval_profile: string;
  selected_factions: string[];
  last_sources: Source[];
  has_character_sheet: boolean;
  has_game_state: boolean;
  has_play_roster: boolean;
  slot_id?: string;
  settings?: Record<string, string>;
  messages: Message[];
  entity?: Record<string, unknown>;
  pending_journey?: unknown;
  deck_remaining?: number;
  game_state?: Record<string, unknown>;
}

export interface CharacterHeader {
  summary: string;
  health: number;
  morale: number;
  supplies: number;
  journey_day: number;
  name: string;
  legacy: string;
  legacy_label?: string;
  in_aldwund: boolean;
}

export interface JourneyEvent {
  index: number;
  card: string;
  zone: string;
  applied: boolean;
  can_apply: boolean;
  label?: string;
  preview: string;
  needs_item: boolean;
  item_card?: string | null;
  item_label?: string | null;
  item_preview?: string | null;
}

export interface PendingJourney {
  events: JourneyEvent[];
  shortcut_id?: string;
}

export interface JourneyActionResult {
  summary?: string;
  item_error?: string | null;
  entity?: Record<string, unknown>;
  header?: CharacterHeader;
  pending_journey?: PendingJourney | null;
}

export interface LegacyAbility {
  id: string;
  label: string;
  description: string;
  tags: string[];
  used: boolean;
}

export interface Shortcut {
  id: string;
  label: string;
}
