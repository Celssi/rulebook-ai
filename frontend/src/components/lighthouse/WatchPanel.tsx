import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { rosterEntryLabel } from "../../lib/rosterLabel";
import type { WatchHeader } from "../../types";

interface Props {
  entity: Record<string, unknown>;
  roster: { id: string; name: string }[];
  activeId: string;
  header: WatchHeader | null;
  onSwitch: () => void;
}

export default function WatchPanel({
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

  const switchWatch = async (id: string) => {
    await api.switchLighthouseWatch(id);
    onSwitch();
  };

  const displayName = rosterEntryLabel(String(local.name || ""));
  const night = Number(header?.night_count ?? local.night_count ?? 1);
  const lampLit = Boolean(header?.lamp_lit ?? local.lamp_lit);
  const weather = String(header?.weather_mood || local.weather_mood || "");
  const lastTask = String(header?.last_task || local.last_task || "");

  return (
    <div className="panel flex flex-col h-full min-h-0 overflow-hidden">
      <div className="px-4 py-2.5 border-b border-border section-title">Watch</div>
      <div className="flex-1 overflow-y-auto p-3 space-y-3 text-sm min-h-0">
        <select
          className="select text-sm py-1"
          value={activeId}
          onChange={(e) => switchWatch(e.target.value)}
        >
          {roster.map((r) => (
            <option key={r.id} value={r.id}>
              {rosterEntryLabel(r.name)}
            </option>
          ))}
        </select>
        <div className="font-medium text-sm truncate">{displayName || "Keeper"}</div>
        <div className="text-xs text-muted">
          Night <span className="text-gray-200 font-medium">{night}</span>
          <span className="ml-2">· Lamp {lampLit ? "lit" : "unlit"}</span>
        </div>
        {weather && (
          <div className="text-xs p-2 rounded-lg bg-elevated/60 border border-border">
            <div className="text-muted mb-1">Weather mood</div>
            <div>{weather}</div>
          </div>
        )}
        {lastTask && (
          <div className="text-xs p-2 rounded-lg bg-elevated/60 border border-border">
            <div className="text-muted mb-1">Last task</div>
            <div>{lastTask.replace(/_/g, " ")}</div>
          </div>
        )}
      </div>
    </div>
  );
}
