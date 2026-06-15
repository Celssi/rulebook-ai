import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { rosterEntryLabel } from "../../lib/rosterLabel";
import type { VisitHeader } from "../../types";

interface Props {
  entity: Record<string, unknown>;
  roster: { id: string; name: string }[];
  activeId: string;
  header: VisitHeader | null;
  onUpdate: (entity: Record<string, unknown>, header: VisitHeader) => void;
  onSwitch: () => void;
}

export default function VisitPanel({
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

  const displayName = rosterEntryLabel(String(local.name || ""));

  const switchVisit = async (id: string) => {
    await api.switchVisit(id);
    onSwitch();
  };

  const archetype = String(local.archetype || header?.archetype || "");
  const visitDay = Number(header?.visit_day ?? local.visit_day ?? 1);

  const cityChanges = Number(header?.city_changes ?? local.city_changes ?? 0);

  return (
    <div className="panel flex flex-col h-full min-h-0 overflow-hidden">
      <div className="px-4 py-2.5 border-b border-border section-title">Visit</div>

      <div className="flex-1 overflow-y-auto p-3 space-y-3 text-sm min-h-0">
        <select
          className="select text-sm py-1"
          value={activeId}
          onChange={(e) => switchVisit(e.target.value)}
        >
          {roster.map((r) => (
            <option key={r.id} value={r.id}>
              {rosterEntryLabel(r.name)}
            </option>
          ))}
        </select>

        <div className="font-medium text-sm truncate">{displayName}</div>
        {archetype && <p className="text-xs text-muted italic">{archetype}</p>}

        <div className="text-xs text-muted">
          Day <span className="text-gray-200 font-medium">{visitDay}</span>
          {header?.ending_mode === "score_90" && (
            <span className="ml-2">
              · Score {header.score_total}/90
            </span>
          )}
        </div>

        <div>
          <div className="label mb-2">City changes</div>
          <div className="flex gap-2">
            {[0, 1, 2, 3].map((i) => (
              <div
                key={i}
                className={`w-8 h-8 rounded border ${
                  i < cityChanges ? "bg-accent border-accent" : "border-border bg-elevated"
                }`}
                title={`Change ${i + 1}`}
              />
            ))}
          </div>
        </div>

        {(Boolean(local.last_adjective) || Boolean(local.last_location_event)) && (
          <div className="text-xs p-2 rounded-lg bg-elevated/60 border border-border">
            <div className="text-muted mb-1">Last draw</div>
            <div>
              {String(local.last_adjective || "")} · {String(local.last_location_event || "")}
            </div>
          </div>
        )}

        {header?.visit_complete && (
          <p className="text-xs text-moss">Visit complete — write your final entry.</p>
        )}
      </div>
    </div>
  );
}
