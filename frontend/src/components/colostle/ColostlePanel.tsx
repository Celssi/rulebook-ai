import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { rosterEntryLabel } from "../../lib/rosterLabel";
import type { ColostleHeader } from "../../types";

interface Props {
  entity: Record<string, unknown>;
  roster: { id: string; name: string }[];
  activeId: string;
  header: ColostleHeader | null;
  onSwitch: () => void;
}

export default function ColostlePanel({ entity, roster, activeId, header, onSwitch }: Props) {
  const [local, setLocal] = useState(entity);

  useEffect(() => {
    setLocal(entity);
  }, [entity]);

  const switchCharacter = async (id: string) => {
    await api.switchColostleCharacter(id);
    onSwitch();
  };

  const displayName = rosterEntryLabel(String(local.name || ""));
  const chapter = Number(header?.chapter ?? local.chapter ?? 1);
  const exp = Number(header?.exploration_score ?? local.exploration_score ?? 0);
  const combat = Number(header?.combat_score ?? local.combat_score ?? 0);
  const cls = String(header?.character_class || local.character_class || "");

  return (
    <div className="panel flex flex-col h-full min-h-0 overflow-hidden">
      <div className="px-4 py-2.5 border-b border-border section-title">Adventurer</div>
      <div className="flex-1 overflow-y-auto p-3 space-y-3 text-sm min-h-0">
        <select
          className="select text-sm py-1"
          value={activeId}
          onChange={(e) => switchCharacter(e.target.value)}
        >
          {roster.map((r) => (
            <option key={r.id} value={r.id}>
              {rosterEntryLabel(r.name)}
            </option>
          ))}
        </select>
        <div className="font-medium text-sm truncate">{displayName || "Adventurer"}</div>
        <div className="text-xs text-muted">
          Ch. <span className="text-gray-200 font-medium">{chapter}</span>
          {cls && <span className="ml-2 capitalize">{cls.replace(/_/g, " ")}</span>}
        </div>
        <div className="text-xs text-muted">
          Exp <span className="text-gray-200 font-medium">{exp}</span>
          <span className="ml-2">
            Combat <span className="text-gray-200 font-medium">{combat}</span>
          </span>
        </div>
        {Boolean(header?.calling || local.calling) && (
          <div className="text-xs p-2 rounded-lg bg-elevated/60 border border-border">
            <div className="text-muted mb-1">Calling</div>
            <div className="line-clamp-4">{String(header?.calling || local.calling)}</div>
          </div>
        )}
        {Boolean(header?.nature || local.nature) && (
          <div className="text-xs p-2 rounded-lg bg-elevated/60 border border-border">
            <div className="text-muted mb-1">Nature</div>
            <div>{String(header?.nature || local.nature)}</div>
          </div>
        )}
      </div>
    </div>
  );
}
