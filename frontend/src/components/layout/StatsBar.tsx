import { CircleHelp, Heart, Package, Settings, Smile } from "lucide-react";
import type { CharacterHeader, ColostleHeader, CottageHeader, InvestigationHeader, PlayHeader, ScionHeader, VisitHeader, WatchHeader } from "../../types";

interface Props {
  gameId: string;
  header: PlayHeader | null;
  gameLabel: string;
  onOpenSettings: () => void;
  onOpenHowToPlay?: () => void;
}

function StatChip({
  icon: Icon,
  value,
  color,
  max = 20,
}: {
  icon: typeof Heart;
  value: number;
  color: string;
  max?: number;
}) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div className="flex items-center gap-1.5 min-w-[4.5rem]" title={`${value}/${max}`}>
      <Icon className="w-3.5 h-3.5 shrink-0" style={{ color }} />
      <div className="flex-1 min-w-0">
        <div className="text-xs font-semibold tabular-nums">{value}</div>
        <div className="stat-bar mt-0.5">
          <div className="stat-bar-fill" style={{ width: `${pct}%`, backgroundColor: color }} />
        </div>
      </div>
    </div>
  );
}

function isVisitHeader(h: PlayHeader): h is VisitHeader {
  return "visit_day" in h && !("health" in h);
}

function isWatchHeader(h: PlayHeader): h is WatchHeader {
  return "night_count" in h && "lamp_lit" in h;
}

function isCottageHeader(h: PlayHeader): h is CottageHeader {
  return "reputation" in h && "current_locale" in h;
}

function isInvestigationHeader(h: PlayHeader): h is InvestigationHeader {
  return "cards_remaining" in h && "deck_built" in h;
}

function isScionHeader(h: PlayHeader): h is ScionHeader {
  return "pwr" in h && "rooms_cleared" in h && !("health" in h);
}

function isColostleHeader(h: PlayHeader): h is ColostleHeader {
  return "exploration_score" in h && "combat_score" in h && "chapter" in h;
}

function isCharacterHeader(h: PlayHeader): h is CharacterHeader {
  return "health" in h && "morale" in h && "supplies" in h;
}

export default function StatsBar({ gameId, header, gameLabel, onOpenSettings, onOpenHowToPlay }: Props) {
  return (
    <header className="flex items-center gap-3 px-4 py-2.5 border-b border-border bg-panel shrink-0">
      <div className="font-semibold text-sm whitespace-nowrap text-accent">{gameLabel}</div>

      {header && gameId === "sansibilia" && isVisitHeader(header) && (
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <div className="min-w-0 hidden sm:block">
            <div className="font-medium text-sm truncate">{header.name || header.archetype || "Visitor"}</div>
            {header.archetype && header.name && (
              <div className="text-xs text-muted truncate">{header.archetype}</div>
            )}
          </div>
          <div className="flex items-center gap-3 ml-auto shrink-0 text-xs text-muted">
            <span>Day {header.visit_day}</span>
            <span>Changes {header.city_changes}/4</span>
            {header.ending_mode === "score_90" && <span>Score {header.score_total}/90</span>}
            {header.visit_complete && <span className="badge-accent">Ended</span>}
          </div>
        </div>
      )}

      {header && gameId === "lighthouse" && isWatchHeader(header) && (
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <div className="min-w-0 hidden sm:block">
            <div className="font-medium text-sm truncate">{header.name || "Keeper"}</div>
          </div>
          <div className="flex items-center gap-3 ml-auto shrink-0 text-xs text-muted">
            <span>Night {header.night_count}</span>
            <span>{header.lamp_lit ? "Lamp lit" : "Lamp out"}</span>
            {header.weather_mood && <span className="capitalize">{header.weather_mood}</span>}
          </div>
        </div>
      )}

      {header && gameId === "apothecaria" && isCottageHeader(header) && (
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <div className="min-w-0 hidden sm:block">
            <div className="font-medium text-sm truncate">{header.name || "Witch"}</div>
          </div>
          <div className="flex items-center gap-3 ml-auto shrink-0 text-xs text-muted">
            <span>Rep {header.reputation}</span>
            {header.silver > 0 && <span>{header.silver} Ag</span>}
            <span>
              Wk {header.week} {header.season}
            </span>
            {header.phase && header.phase !== "idle" && (
              <span className="capitalize">{header.phase.replace(/_/g, " ")}</span>
            )}
            {header.ailment_name && <span className="truncate max-w-[8rem]">{header.ailment_name}</span>}
          </div>
        </div>
      )}

      {header && gameId === "whispers" && isInvestigationHeader(header) && (
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <div className="min-w-0 hidden sm:block">
            <div className="font-medium text-sm truncate">
              {header.investigator_name || header.location_name || "Investigator"}
            </div>
          </div>
          <div className="flex items-center gap-3 ml-auto shrink-0 text-xs text-muted">
            {header.deck_built ? (
              <>
                <span>{header.cards_remaining} cards</span>
                <span>Turn {header.turn_number}</span>
                <span>Jokers {header.jokers_drawn}/2</span>
              </>
            ) : (
              <span>Deck not built</span>
            )}
            {header.investigation_complete && <span className="badge-accent">Ended</span>}
          </div>
        </div>
      )}

      {header && gameId === "ashes" && isScionHeader(header) && (
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <div className="min-w-0 hidden sm:block">
            <div className="font-medium text-sm truncate">{header.name || "Scion"}</div>
            {header.scion_class && (
              <div className="text-xs text-muted truncate capitalize">{header.scion_class}</div>
            )}
          </div>
          <div className="flex items-center gap-3 ml-auto shrink-0 text-xs text-muted">
            <span>
              HP {header.hp}/{header.max_hp}
            </span>
            <span>Lv {header.level}</span>
            <span>{header.rooms_cleared} rooms</span>
          </div>
        </div>
      )}

      {header && gameId === "colostle" && isColostleHeader(header) && (
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <div className="min-w-0 hidden sm:block">
            <div className="font-medium text-sm truncate">{header.name || "Adventurer"}</div>
            {header.character_class && (
              <div className="text-xs text-muted truncate capitalize">{header.character_class}</div>
            )}
          </div>
          <div className="flex items-center gap-3 ml-auto shrink-0 text-xs text-muted">
            <span>Ch. {header.chapter}</span>
            <span>Exp {header.exploration_score}</span>
            <span>Combat {header.combat_score}</span>
            {header.wounds > 0 && <span>Wounds {header.wounds}</span>}
          </div>
        </div>
      )}

      {header && gameId === "brambletrek_2" && isCharacterHeader(header) && (
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <div className="min-w-0 hidden sm:block">
            <div className="font-medium text-sm truncate">{header.name || "Unnamed"}</div>
            {header.legacy_label && (
              <div className="text-xs text-muted truncate">{header.legacy_label}</div>
            )}
          </div>
          <div className="flex items-center gap-4 ml-auto shrink-0">
            <StatChip icon={Heart} value={header.health} color="#e05a5a" max={30} />
            <StatChip icon={Smile} value={header.morale} color="#6b9fff" max={30} />
            <StatChip icon={Package} value={header.supplies} color="#d4a24c" max={30} />
            <span className="text-xs text-muted whitespace-nowrap hidden md:inline">
              Day {header.exploration_day ?? header.journey_day ?? 1}
            </span>
            {header.in_hollow && <span className="badge-accent">Hollow</span>}
          </div>
        </div>
      )}

      {header && gameId === "tor" && (
        <div className="flex items-center gap-3 min-w-0 flex-1">
          {(() => {
            const h = header as Record<string, unknown>;
            const name = String(h.name || "Hero");
            const culture = String(h.culture || "");
            const calling = String(h.calling || "");
            return (
              <>
                <div className="min-w-0 hidden sm:block">
                  <div className="font-medium text-sm truncate">{name}</div>
                  {(culture || calling) && (
                    <div className="text-xs text-muted truncate capitalize">
                      {[culture, calling]
                        .filter(Boolean)
                        .map((s) => s.replace(/_/g, " "))
                        .join(" · ")}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-4 ml-auto shrink-0">
                  <StatChip icon={Smile} value={Number(h.hope ?? 0)} color="#6b9fff" />
                  <StatChip icon={Heart} value={Number(h.dread ?? 0)} color="#c45c5c" />
                  <StatChip icon={Package} value={Number(h.eye_awareness ?? 0)} color="#d4a24c" />
                  {Number(h.journey_day ?? 0) > 0 && (
                    <span className="text-xs text-muted whitespace-nowrap hidden md:inline">
                      Day {Number(h.journey_day)}
                    </span>
                  )}
                  {Boolean(h.weary) && <span className="badge-accent">Weary</span>}
                </div>
              </>
            );
          })()}
        </div>
      )}

      {header && gameId === "brambletrek" && isCharacterHeader(header) && (
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <div className="min-w-0 hidden sm:block">
            <div className="font-medium text-sm truncate">{header.name || "Unnamed"}</div>
            {header.legacy_label && (
              <div className="text-xs text-muted truncate">{header.legacy_label}</div>
            )}
          </div>

          <div className="flex items-center gap-4 ml-auto shrink-0">
            <StatChip icon={Heart} value={header.health} color="#e05a5a" />
            <StatChip icon={Smile} value={header.morale} color="#6b9fff" />
            <StatChip icon={Package} value={header.supplies} color="#d4a24c" />
            <span className="text-xs text-muted whitespace-nowrap hidden md:inline">
              Day {header.journey_day}
            </span>
            {header.in_aldwund && <span className="badge-accent">Depths</span>}
          </div>
        </div>
      )}

      {header && gameId === "outgunned" && (
        <div className="flex items-center gap-3 min-w-0 flex-1">
          {(() => {
            const h = header as Record<string, unknown>;
            return (
              <>
                <div className="min-w-0 hidden sm:block">
                  <div className="font-medium text-sm truncate">{String(h.name || "Hero")}</div>
                  {h.mission_title ? (
                    <div className="text-xs text-muted truncate">{String(h.mission_title)}</div>
                  ) : null}
                </div>
                <div className="flex items-center gap-3 ml-auto shrink-0 text-xs text-muted">
                  {h.ad_phase ? <span>{String(h.ad_phase)}</span> : null}
                  {h.tension !== undefined ? <span>Tension {Number(h.tension)}/12</span> : null}
                  {h.death_roulette_bullets !== undefined ? (
                    <span>Roulette {Number(h.death_roulette_bullets)}/6</span>
                  ) : null}
                </div>
              </>
            );
          })()}
        </div>
      )}

      {!header && <div className="flex-1" />}

      {gameId !== "40k" && onOpenHowToPlay && (
        <button
          type="button"
          className="btn-ghost p-2 rounded-lg shrink-0"
          onClick={onOpenHowToPlay}
          title="Näin pelaat"
        >
          <CircleHelp className="w-4 h-4" />
        </button>
      )}

      <button
        type="button"
        className="btn-ghost p-2 rounded-lg shrink-0"
        onClick={onOpenSettings}
        title="Settings"
      >
        <Settings className="w-4 h-4" />
      </button>
    </header>
  );
}
