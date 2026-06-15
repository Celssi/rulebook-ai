import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { rosterEntryLabel } from "../../lib/rosterLabel";
import type { CharacterHeader, LegacyAbility } from "../../types";
import { FormSelect } from "../shared/FormFields";

const STAT_MAX = 30;

interface Props {
  entity: Record<string, unknown>;
  abilities: LegacyAbility[];
  roster: { id: string; name: string }[];
  activeId: string;
  onUpdate: (entity: Record<string, unknown>, header: CharacterHeader) => void;
  onSwitch: () => void;
}

function StatBar({
  label,
  value,
  color,
  onChange,
  onBlur,
}: {
  label: string;
  value: number;
  color: string;
  onChange: (v: number) => void;
  onBlur: () => void;
}) {
  const pct = Math.min(100, Math.max(0, (value / STAT_MAX) * 100));
  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <span className="text-xs text-muted capitalize">{label}</span>
        <input
          type="number"
          min={0}
          max={STAT_MAX}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          onBlur={onBlur}
          className="w-10 bg-transparent text-right text-xs font-semibold tabular-nums focus:outline-none"
        />
      </div>
      <div className="stat-bar">
        <div className="stat-bar-fill" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
    </div>
  );
}

export default function CharacterPanel({ entity, abilities, roster, activeId, onUpdate, onSwitch }: Props) {
  const [local, setLocal] = useState(entity);
  const [saving, setSaving] = useState(false);

  useEffect(() => setLocal(entity), [entity]);

  const save = async (next?: Record<string, unknown>) => {
    const payload = next ?? local;
    setSaving(true);
    try {
      const res = await api.updateBt2Character(payload);
      setLocal(res.entity);
      onUpdate(res.entity, res.header);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="card p-3 space-y-3 text-sm">
      <div className="font-medium">{rosterEntryLabel(String(local.name || "")) || "Traveller"}</div>
      <FormSelect className="w-full text-xs" value={activeId} onChange={() => onSwitch()}>
        {roster.map((r) => (
          <option key={r.id} value={r.id}>
            {rosterEntryLabel(r.name) || r.id}
          </option>
        ))}
      </FormSelect>
      <StatBar label="health" value={Number(local.health) || 0} color="#e05a5a" onChange={(v) => setLocal((p) => ({ ...p, health: v }))} onBlur={() => save()} />
      <StatBar label="morale" value={Number(local.morale) || 0} color="#6b9fff" onChange={(v) => setLocal((p) => ({ ...p, morale: v }))} onBlur={() => save()} />
      <StatBar label="supplies" value={Number(local.supplies) || 0} color="#d4a24c" onChange={(v) => setLocal((p) => ({ ...p, supplies: v }))} onBlur={() => save()} />
      {abilities.length > 0 && (
        <div className="text-[11px] text-muted space-y-1 pt-2 border-t border-border">
          {abilities.map((a) => (
            <div key={a.id} className={a.used ? "opacity-50" : ""}>
              <span className="text-gray-300">{a.label}</span>
              {a.used && " (used)"}
            </div>
          ))}
        </div>
      )}
      {saving && <span className="text-[10px] text-muted">Saving…</span>}
    </div>
  );
}
