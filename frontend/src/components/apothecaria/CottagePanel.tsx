import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { rosterEntryLabel } from "../../lib/rosterLabel";
import type { CottageHeader } from "../../types";

interface Props {
  entity: Record<string, unknown>;
  roster: { id: string; name: string }[];
  activeId: string;
  header: CottageHeader | null;
  onSwitch: () => void;
}

export default function CottagePanel({ entity, roster, activeId, header, onSwitch }: Props) {
  const [local, setLocal] = useState(entity);

  useEffect(() => {
    setLocal(entity);
  }, [entity]);

  const switchCottage = async (id: string) => {
    await api.switchApothecariaCottage(id);
    onSwitch();
  };

  const displayName = rosterEntryLabel(String(local.name || ""));
  const reputation = Number(header?.reputation ?? local.reputation ?? 5);
  const week = Number(header?.week ?? local.week ?? 1);
  const season = String(header?.season ?? local.season ?? "spring");
  const silver = Number(header?.silver ?? local.silver ?? 0);
  const phase = String(header?.phase ?? local.phase ?? "idle");

  return (
    <div className="panel flex flex-col h-full min-h-0 overflow-hidden">
      <div className="px-4 py-2.5 border-b border-border section-title">Cottage</div>

      <div className="flex-1 overflow-y-auto p-3 space-y-3 text-sm min-h-0">
        <select
          className="select text-sm py-1"
          value={activeId}
          onChange={(e) => switchCottage(e.target.value)}
        >
          {roster.map((r) => (
            <option key={r.id} value={r.id}>
              {rosterEntryLabel(r.name)}
            </option>
          ))}
        </select>

        <div className="font-medium text-sm truncate">{displayName}</div>

        <div className="text-xs text-muted">
          Rep <span className="text-gray-200 font-medium">{reputation}</span>
          <span className="ml-2">
            Wk {week}, {season}
          </span>
          {silver > 0 && (
            <span className="ml-2">
              <span className="text-gray-200 font-medium">{silver}</span> Silver
            </span>
          )}
        </div>

        {phase !== "idle" && (
          <div className="text-xs capitalize text-muted">
            Phase: {phase.replace(/_/g, " ")}
            {phase === "downtime" && header?.downtime_timer != null && (
              <span> ({header.downtime_timer} segments)</span>
            )}
          </div>
        )}

        {Boolean(header?.ailment_name || local.ailment_name) && (
          <div className="text-xs p-2 rounded-lg bg-elevated/60 border border-border">
            <div className="text-muted mb-1">Current ailment</div>
            <div className="font-medium">{String(header?.ailment_name || local.ailment_name)}</div>
            {(header?.ailment_tags?.length || (local.ailment_tags as string[])?.length) ? (
              <div className="text-muted mt-1">
                {(header?.ailment_tags || (local.ailment_tags as string[]) || []).join(" · ")}
              </div>
            ) : null}
            {header?.ailment_timer != null && (
              <div className="mt-1">Timer: {header.ailment_timer}</div>
            )}
            {header?.hunting_reagent && (
              <div className="mt-1">
                Hunting {header.hunting_reagent} (FV {header.hunting_fv})
              </div>
            )}
          </div>
        )}

        {Boolean(header?.familiar_type || local.familiar_type) && (
          <div className="text-xs text-muted">
            Familiar: {String(header?.familiar_type || local.familiar_type)}
            {Boolean(header?.familiar_skill || local.familiar_skill) &&
              ` · ${String(header?.familiar_skill || local.familiar_skill)}`}
          </div>
        )}

        <div className="text-xs text-muted">
          Locale: {String(header?.current_locale || local.current_locale || "glimmerwood").replace(/_/g, " ")}
          {header?.foraging_points != null && header.foraging_points > 0 && (
            <span> · {header.foraging_points} foraging pts</span>
          )}
        </div>

        {(header?.tools_owned?.length ?? 0) > 3 && (
          <div className="text-xs text-muted truncate" title={(header?.tools_owned || []).join(", ")}>
            Tools: {(header?.tools_owned || []).slice(3).join(", ")}
          </div>
        )}
      </div>
    </div>
  );
}
