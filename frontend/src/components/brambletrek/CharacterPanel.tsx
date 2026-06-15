import { useEffect, useState } from "react";
import { ChevronDown, ChevronUp, RotateCcw } from "lucide-react";
import { api } from "../../api/client";
import { rosterEntryLabel } from "../../lib/rosterLabel";
import type { CharacterHeader, LegacyAbility } from "../../types";

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
  const pct = Math.min(100, Math.max(0, (value / 20) * 100));
  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <span className="text-xs text-muted capitalize">{label}</span>
        <input
          type="number"
          min={0}
          max={20}
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

export default function CharacterPanel({
  entity,
  abilities,
  roster,
  activeId,
  onUpdate,
  onSwitch,
}: Props) {
  const [local, setLocal] = useState(entity);
  const [saving, setSaving] = useState(false);
  const [statsOpen, setStatsOpen] = useState(false);

  useEffect(() => {
    setLocal(entity);
  }, [entity]);

  const displayName = rosterEntryLabel(String(local.name || ""));

  const patch = (key: string, value: unknown) => {
    setLocal((prev) => ({ ...prev, [key]: value }));
  };

  const save = async (next?: Record<string, unknown>) => {
    const payload = next ?? local;
    setSaving(true);
    try {
      const res = await api.updateCharacter(payload);
      setLocal(res.entity);
      onUpdate(res.entity, res.header);
    } finally {
      setSaving(false);
    }
  };

  const toggleAbility = async (id: string, used: boolean) => {
    const usedMap = {
      ...((local.legacy_abilities_used as Record<string, boolean>) || {}),
      [id]: used,
    };
    const next = { ...local, legacy_abilities_used: usedMap };
    setLocal(next);
    const res = await api.updateCharacter(next);
    onUpdate(res.entity, res.header);
  };

  const switchChar = async (id: string) => {
    await api.switchGnawborn(id);
    onSwitch();
  };

  const statColors = { health: "#e05a5a", morale: "#6b9fff", supplies: "#d4a24c" };

  return (
    <div className="panel flex flex-col h-full min-h-0 overflow-hidden">
      <div className="px-4 py-2.5 border-b border-border section-title">Gnawborn</div>

      <div className="flex-1 overflow-y-auto p-3 space-y-3 text-sm min-h-0">
        <select
          className="select text-sm py-1"
          value={activeId}
          onChange={(e) => switchChar(e.target.value)}
        >
          {roster.map((r) => (
            <option key={r.id} value={r.id}>
              {rosterEntryLabel(r.name)}
            </option>
          ))}
        </select>

        <div className="font-medium text-sm truncate">{displayName}</div>

        <button
          type="button"
          className="w-full flex items-center justify-between text-xs text-muted hover:text-gray-200"
          onClick={() => setStatsOpen(!statsOpen)}
        >
          <span>Stats</span>
          {statsOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>

        <div className="grid gap-2">
          {(["health", "morale", "supplies"] as const).map((k) => (
            <StatBar
              key={k}
              label={k}
              value={Number(local[k] ?? 10)}
              color={statColors[k]}
              onChange={(v) => patch(k, v)}
              onBlur={() => save()}
            />
          ))}
        </div>
        {statsOpen && (
          <p className="text-[10px] text-muted">Stats save when you leave a field.</p>
        )}

        <label className="flex items-center gap-2 text-xs cursor-pointer">
          <input
            type="checkbox"
            checked={Boolean(local.in_aldwund)}
            onChange={(e) => {
              const next = { ...local, in_aldwund: e.target.checked };
              setLocal(next);
              save(next);
            }}
            className="rounded border-border"
          />
          In Aldwund (Depths)
        </label>

        {abilities.length > 0 && (
          <div>
            <div className="section-title mb-2">Daily abilities</div>
            <div className="space-y-1.5">
              {abilities.map((ab) => (
                <label
                  key={ab.id}
                  className={`flex items-start gap-2 p-2 rounded-lg hover:bg-elevated/50 cursor-pointer ${
                    ab.used ? "opacity-50" : ""
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={ab.used}
                    onChange={(e) => toggleAbility(ab.id, e.target.checked)}
                    className="mt-0.5 rounded border-border"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="font-medium text-xs">{ab.label}</span>
                      {ab.tags?.map((tag) => (
                        <span
                          key={tag}
                          className={`text-[10px] px-1.5 py-0 rounded ${
                            tag === "combat"
                              ? "bg-red-900/40 text-red-300"
                              : "bg-moss-muted text-moss"
                          }`}
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                    <div className="text-xs text-muted line-clamp-2">{ab.description}</div>
                  </div>
                </label>
              ))}
            </div>
            <button
              type="button"
              className="btn-ghost w-full mt-2 flex items-center justify-center gap-1 text-xs"
              onClick={async () => {
                const res = await api.updateCharacter({ ...local, legacy_abilities_used: {} });
                setLocal(res.entity);
                onUpdate(res.entity, res.header);
              }}
            >
              <RotateCcw className="w-3 h-3" />
              Reset daily abilities
            </button>
          </div>
        )}
      </div>

      {saving && (
        <div className="px-3 py-1.5 text-xs text-muted border-t border-border">Saving…</div>
      )}
    </div>
  );
}
