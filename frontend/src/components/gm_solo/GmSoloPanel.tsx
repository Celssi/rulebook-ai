import { useEffect, useState } from "react";
import { gmSoloApi } from "../../api/gmSolo";
import type { GmSoloGameId } from "../../games/gmSoloGames";
import { rosterEntryLabel } from "../../lib/rosterLabel";
import type { GmSoloHeader } from "../../games/gmSoloGames";
import { FormSelect } from "../shared/FormFields";

interface Props {
  gameId: GmSoloGameId;
  entity: Record<string, unknown>;
  roster: { id: string; name: string }[];
  activeId: string;
  header: GmSoloHeader | null;
  onSwitch: () => void;
}

export default function GmSoloPanel({
  gameId,
  entity,
  roster,
  activeId,
  header,
  onSwitch,
}: Props) {
  const [local, setLocal] = useState(entity);
  const api = gmSoloApi(gameId);

  useEffect(() => {
    setLocal(entity);
  }, [entity]);

  const switchCharacter = async (id: string) => {
    await api.switchCharacter(id);
    onSwitch();
  };

  const displayName = rosterEntryLabel(String(local.name || header?.name || ""));
  const summary = String(header?.summary || local.summary || "");
  const isDnd = gameId === "dnd5e";

  return (
    <div className="panel flex flex-col h-full min-h-0 overflow-hidden">
      <div className="px-4 py-2.5 border-b border-border section-title">Character</div>
      <div className="flex-1 overflow-y-auto p-3 space-y-3 text-sm min-h-0">
        <FormSelect
          className="text-sm py-1"
          value={activeId}
          onChange={(e) => switchCharacter(e.target.value)}
        >
          {roster.map((r) => (
            <option key={r.id} value={r.id}>
              {rosterEntryLabel(r.name)}
            </option>
          ))}
        </FormSelect>
        <div className="font-medium text-sm truncate">{displayName || "Hero"}</div>
        {summary && (
          <div className="text-xs text-muted whitespace-pre-wrap">{summary}</div>
        )}
        {gameId === "coriolis" && header && (
          <div className="text-xs text-muted space-y-0.5">
            {Boolean(header.crew_name) && <div>Crew: {String(header.crew_name)}</div>}
            {Boolean(header.bird_name) && <div>Bird: {String(header.bird_name)}</div>}
            {header.health != null && header.max_health != null && (
              <div>
                Health {String(header.health)}/{String(header.max_health)} · Hope {String(header.hope)}
                /{String(header.max_hope)} · Heart {String(header.heart)}/{String(header.max_heart)}
              </div>
            )}
          </div>
        )}
        {isDnd && (
          <div className="text-xs text-muted space-y-1 border-t border-border pt-2">
            {local.species ? <div>Species: {String(local.species)}</div> : null}
            {local.background ? <div>Background: {String(local.background)}</div> : null}
            {local.subclass ? <div>Subclass: {String(local.subclass)}</div> : null}
            {local.origin_feat ? <div>Feat: {String(local.origin_feat)}</div> : null}
            {Array.isArray(local.cantrips) && local.cantrips.length > 0 ? (
              <div>Cantrips: {(local.cantrips as string[]).join(", ")}</div>
            ) : null}
          </div>
        )}
        {gameId === "tor" && (
          <div className="text-xs text-muted space-y-1 border-t border-border pt-2">
            {header?.patron ? <div>Patron: {String(header.patron)}</div> : null}
            {header?.safe_haven ? <div>Safe haven: {String(header.safe_haven)}</div> : null}
            {header?.culture ? (
              <div>
                {String(header.culture).replace(/_/g, " ")}
                {header?.calling ? ` · ${String(header.calling).replace(/_/g, " ")}` : ""}
              </div>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}
