export type GameId =
  | "40k"
  | "brambletrek"
  | "brambletrek_2"
  | "sansibilia"
  | "lighthouse"
  | "apothecaria"
  | "whispers"
  | "colostle"
  | "ashes"
  | "outgunned"
  | "tor"
  | "coriolis"
  | "cosmere"
  | "mlp"
  | "dnd5e";

export const PLAY_GAME_IDS: GameId[] = [
  "brambletrek",
  "brambletrek_2",
  "sansibilia",
  "lighthouse",
  "apothecaria",
  "whispers",
  "colostle",
  "ashes",
  "outgunned",
  "tor",
  "coriolis",
  "cosmere",
  "mlp",
  "dnd5e",
];

export function isPlayGameId(id: string): id is GameId {
  return PLAY_GAME_IDS.includes(id as GameId);
}

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
  play_style?: string;
  slot_id?: string;
  settings?: Record<string, string>;
  messages: Message[];
  entity?: Record<string, unknown>;
  pending_journey?: unknown;
  pending_exploration?: unknown;
  hollow?: HollowState | null;
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
  exploration_day?: number;
  in_aldwund?: boolean;
  in_hollow?: boolean;
  memory_fragments?: number;
  hollow_awareness?: boolean;
}

export interface ExplorationEvent {
  index: number;
  card: string;
  applied: boolean;
  can_apply: boolean;
  label?: string;
  preview: string;
  needs_item: boolean;
  needs_hollow?: boolean;
  item_card?: string | null;
  item_label?: string | null;
}

export interface PendingExploration {
  events: ExplorationEvent[];
}

export interface ExplorationActionResult {
  summary?: string;
  entity?: Record<string, unknown>;
  header?: CharacterHeader;
  pending_exploration?: PendingExploration | null;
}

export interface HollowCell {
  card: string;
  revealed: boolean;
  row: number;
  col: number;
}

export interface HollowState {
  entry_card: string;
  entry_prompt: string;
  grid: HollowCell[][];
  marker_row: number;
  marker_col: number;
  memory_fragments: number;
  awareness: boolean;
  adjacent?: { row: number; col: number }[];
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

export interface VisitHeader {
  summary: string;
  name: string;
  archetype: string;
  visit_day: number;
  city_changes: number;
  ending_mode: string;
  score_total: number;
  ace_value: number;
  visit_complete: boolean;
  last_adjective: string;
  last_location_event: string;
}

export interface WatchHeader {
  summary: string;
  name: string;
  night_count: number;
  weather_mood: string;
  lamp_lit: boolean;
  last_task: string;
  story_mode?: string;
}

export interface CottageHeader {
  summary: string;
  name: string;
  reputation: number;
  silver: number;
  season: string;
  week: number;
  phase: string;
  downtime_timer: number;
  foraging_points: number;
  current_locale: string;
  patient_name: string;
  patient_type: string;
  ailment_name: string;
  ailment_tags: string[];
  ailment_timer: number | null;
  hunting_reagent?: string;
  hunting_fv?: number | null;
  inventory_count?: number;
  potion_poison?: number;
  potion_sweet?: number;
  familiar_type: string;
  familiar_skill: string;
  tools_owned?: string[];
  upgrades_owned?: string[];
  story_mode?: string;
}

export interface ColostleHeader {
  summary: string;
  name: string;
  character_class: string;
  calling: string;
  nature: string;
  exploration_score: number;
  combat_score: number;
  wounds: number;
  treasures: number;
  chapter: number;
  location_mode: string;
  last_task: string;
  story_mode?: string;
}

export interface InvestigationHeader {
  summary: string;
  investigator_name: string;
  background: string;
  belonging: string;
  location_name: string;
  location_title: string;
  deck_built: boolean;
  cards_remaining: number;
  turn_number: number;
  jokers_drawn: number;
  difficulty: string;
  investigation_complete: boolean;
  last_table?: string;
  last_title?: string;
}

export interface ScionHeader {
  summary: string;
  name: string;
  scion_class: string;
  pwr: number;
  int: number;
  agl: number;
  hp: number;
  max_hp: number;
  stamina: number;
  max_stamina: number;
  level: number;
  ember: number;
  ember_to_level?: number;
  rooms_cleared: number;
  lore_count?: number;
  sanctuaries_visited?: number;
  trials_completed?: number;
  active_trials?: { card: string; color: string; trial: string }[];
  fate_gift: string;
  armour: string;
  starting_weapon_melee?: string;
  starting_weapon_ranged?: string;
  last_room_name: string;
  last_enemy: string;
}

/** Union of per-game play-mode header payloads from the API. */
export type PlayHeader =
  | CharacterHeader
  | VisitHeader
  | WatchHeader
  | CottageHeader
  | ColostleHeader
  | InvestigationHeader
  | ScionHeader
  | import("./games/gmSoloGames").GmSoloHeader
  | import("./games/gmSoloGames").OutgunnedHeader;
