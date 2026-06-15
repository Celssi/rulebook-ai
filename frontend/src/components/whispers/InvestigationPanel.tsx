import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { rosterEntryLabel } from "../../lib/rosterLabel";
import type { InvestigationHeader } from "../../types";

interface Props {
  entity: Record<string, unknown>;
  roster: { id: string; name: string }[];
  activeId: string;
  header: InvestigationHeader | null;
  onSwitch: () => void;
}

export default function InvestigationPanel({
  entity,
  roster,
  activeId,
  header,
  onSwitch,
}: Props) {
  const [local, setLocal] = useState(entity);

  useEffect(() => {
    setLocal(entity);
  }, [entity]);

  const switchInvestigation = async (id: string) => {
    await api.switchWhispersInvestigation(id);
    onSwitch();
  };

  const name = String(local.investigator_name || header?.investigator_name || "");
  const displayName = rosterEntryLabel(name);
  const location =
    String(local.location_name || header?.location_name || "") ||
    String(local.location_title || header?.location_title || "");
  const deck = local.whispers_deck;
  const cardsLeft = Number(
    header?.cards_remaining ?? (Array.isArray(deck) ? deck.length : 0),
  );
  const deckBuilt = Boolean(header?.deck_built ?? local.deck_built);
  const turn = Number(header?.turn_number ?? local.turn_number ?? 0);
  const jokers = Number(header?.jokers_drawn ?? local.jokers_drawn ?? 0);

  return (
    <div className="panel flex flex-col h-full min-h-0 overflow-hidden">
      <div className="px-4 py-2.5 border-b border-border section-title">Investigation</div>
      <div className="flex-1 overflow-y-auto p-3 space-y-3 text-sm min-h-0">
        <select
          className="select text-sm py-1"
          value={activeId}
          onChange={(e) => switchInvestigation(e.target.value)}
        >
          {roster.map((r) => (
            <option key={r.id} value={r.id}>
              {rosterEntryLabel(r.name)}
            </option>
          ))}
        </select>

        <div className="font-medium text-sm truncate">{displayName || "Investigator"}</div>
        {location && <p className="text-xs text-muted italic truncate">{location}</p>}

        <div className="text-xs text-muted">
          {deckBuilt ? (
            <>
              <span className="text-gray-200 font-medium">{cardsLeft}</span> cards in Whispers deck
              <span className="ml-2">· Turn {turn}</span>
              <span className="ml-2">· Jokers {jokers}/2</span>
            </>
          ) : (
            "Whispers deck not built yet"
          )}
        </div>

        {(Boolean(local.last_title) || Boolean(header?.last_title)) && (
          <div className="text-xs p-2 rounded-lg bg-elevated/60 border border-border">
            <div className="text-muted mb-1">Last draw</div>
            <div>{String(local.last_title || header?.last_title || "")}</div>
          </div>
        )}

        {header?.investigation_complete && (
          <p className="text-xs text-moss">Investigation complete — write your conclusion.</p>
        )}
      </div>
    </div>
  );
}
