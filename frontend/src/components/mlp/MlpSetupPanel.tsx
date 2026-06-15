import { useEffect, useMemo, useState } from "react";
import { gmSoloApi } from "../../api/gmSolo";
import { rosterEntryLabel } from "../../lib/rosterLabel";
import type { GmSoloHeader } from "../../games/gmSoloGames";

interface TableOption {
  id: string;
  label: string;
}

interface SkillDef {
  id: string;
  label: string;
}

interface MlpOptions {
  origins: (TableOption & { essence_bonus_options?: string[] })[];
  roles: TableOption[];
  influences: (TableOption & { hang_up?: string })[];
  skills_by_essence: Record<string, SkillDef[]>;
  skill_ranks: { rank: number; label: string }[];
  dif_presets: { id: string; label: string; dif: number }[];
  essence_keys: string[];
  player_essence_points: number;
  level_1_essence_total: number;
}

interface Props {
  entity: Record<string, unknown>;
  onChange: (entity: Record<string, unknown>) => void;
  onSaved?: (entity: Record<string, unknown>, header: GmSoloHeader) => void;
  roster?: { id: string; name: string }[];
  activeId?: string;
  onSwitchRoster?: () => void;
}

const ESSENCE_LABELS: Record<string, string> = {
  strength: "Strength",
  speed: "Speed",
  smarts: "Smarts",
  social: "Social",
};

function strList(v: unknown): string[] {
  return Array.isArray(v) ? v.map(String) : [];
}

function numRecord(v: unknown, keys: string[]): Record<string, number> {
  const src = v && typeof v === "object" ? (v as Record<string, number>) : {};
  return Object.fromEntries(keys.map((k) => [k, Number(src[k] ?? 3)]));
}

export default function MlpSetupPanel({
  entity,
  onChange,
  onSaved,
  roster,
  activeId,
  onSwitchRoster,
}: Props) {
  const api = gmSoloApi("mlp");
  const [options, setOptions] = useState<MlpOptions | null>(null);
  const [saving, setSaving] = useState(false);
  const [switching, setSwitching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getCharacter().then((res) => setOptions(res.options as unknown as MlpOptions));
  }, []);

  const essenceKeys = options?.essence_keys || ["strength", "speed", "smarts", "social"];
  const playerPoints = options?.player_essence_points ?? 12;

  const baseEssences = useMemo(
    () => numRecord(entity.base_essences, essenceKeys),
    [entity.base_essences, essenceKeys],
  );
  const baseSum = essenceKeys.reduce((s, k) => s + (baseEssences[k] || 0), 0);
  const skills = (entity.skills as Record<string, number>) || {};
  const influences = strList(entity.influences);
  const hangUps = strList(entity.hang_ups);
  const bonds = strList(entity.background_bonds);
  const defenses = (entity.defenses as Record<string, number>) || {};
  const essences = (entity.essences as Record<string, number>) || {};

  const originData = options?.origins.find((o) => o.id === String(entity.origin || ""));
  const essenceBonusOptions = originData?.essence_bonus_options || essenceKeys;

  const switchRoster = async (id: string) => {
    if (!id || id === activeId) return;
    setSwitching(true);
    setError(null);
    try {
      await api.switchCharacter(id);
      onSwitchRoster?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Switch failed");
    } finally {
      setSwitching(false);
    }
  };

  const setInfluenceAt = (idx: number, value: string) => {
    const next = [...influences];
    while (next.length <= idx) next.push("");
    next[idx] = value;
    onChange({ ...entity, influences: next.filter(Boolean) });
  };

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      const payload = {
        ...entity,
        pony_name: entity.pony_name || entity.name,
        name: entity.name || entity.pony_name,
      };
      const res = await api.updateCharacter(payload);
      onChange(res.entity);
      onSaved?.(res.entity, res.header);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const allSkills = options?.skills_by_essence || {};

  return (
    <div className="space-y-4 text-sm">
      {roster && roster.length > 0 && (
        <section>
          <div className="label mb-2">Active pony</div>
          <select
            className="select"
            value={activeId || ""}
            disabled={switching}
            onChange={(e) => switchRoster(e.target.value)}
          >
            {roster.map((r) => (
              <option key={r.id} value={r.id}>
                {rosterEntryLabel(r.name)}
              </option>
            ))}
          </select>
        </section>
      )}

      <section className="space-y-2">
        <div className="font-medium text-xs text-muted uppercase tracking-wide">Identity</div>
        <label className="block">
          <span className="text-muted text-xs">Pony name</span>
          <input
            className="input w-full mt-1"
            value={String(entity.pony_name || entity.name || "")}
            onChange={(e) =>
              onChange({ ...entity, pony_name: e.target.value, name: e.target.value })
            }
          />
        </label>
        <div className="grid sm:grid-cols-2 gap-3">
          <label className="block">
            <span className="text-muted text-xs">Origin</span>
            <select
              className="select w-full mt-1"
              value={String(entity.origin || "")}
              onChange={(e) => onChange({ ...entity, origin: e.target.value })}
            >
              <option value="">—</option>
              {(options?.origins || []).map((o) => (
                <option key={o.id} value={o.id}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="text-muted text-xs">Role (Spirit of Harmony)</span>
            <select
              className="select w-full mt-1"
              value={String(entity.role || "")}
              onChange={(e) => onChange({ ...entity, role: e.target.value })}
            >
              <option value="">—</option>
              {(options?.roles || []).map((r) => (
                <option key={r.id} value={r.id}>
                  {r.label}
                </option>
              ))}
            </select>
          </label>
        </div>
        {String(entity.origin || "") !== "" && (
          <label className="block">
            <span className="text-muted text-xs">Origin +1 Essence target</span>
            <select
              className="select w-full mt-1"
              value={String(entity.origin_essence_target || "")}
              onChange={(e) => onChange({ ...entity, origin_essence_target: e.target.value })}
            >
              <option value="">Default</option>
              {essenceBonusOptions.map((k) => (
                <option key={k} value={k}>
                  {ESSENCE_LABELS[k] || k}
                </option>
              ))}
            </select>
          </label>
        )}
      </section>

      <section className="space-y-2">
        <div className="font-medium text-xs text-muted uppercase tracking-wide">Influences</div>
        {[0, 1, 2].map((i) => (
          <label key={i} className="block">
            <span className="text-muted text-xs">Influence {i + 1}</span>
            <select
              className="select w-full mt-1"
              value={influences[i] || ""}
              onChange={(e) => setInfluenceAt(i, e.target.value)}
            >
              <option value="">—</option>
              {(options?.influences || []).map((inf) => (
                <option key={inf.id} value={inf.id}>
                  {inf.label}
                </option>
              ))}
            </select>
          </label>
        ))}
        {influences.length >= 2 && (
          <label className="block">
            <span className="text-muted text-xs">Hang-Up</span>
            <input
              className="input w-full mt-1"
              value={hangUps[0] || ""}
              placeholder="From an Influence you chose"
              onChange={(e) =>
                onChange({
                  ...entity,
                  hang_ups: [e.target.value, hangUps[1] || ""].filter(Boolean),
                })
              }
            />
          </label>
        )}
        {influences.length >= 3 && (
          <label className="block">
            <span className="text-muted text-xs">Second Hang-Up</span>
            <input
              className="input w-full mt-1"
              value={hangUps[1] || ""}
              onChange={(e) =>
                onChange({
                  ...entity,
                  hang_ups: [hangUps[0] || "", e.target.value].filter(Boolean),
                })
              }
            />
          </label>
        )}
        {[0, 1, 2].slice(0, Math.max(1, influences.length)).map((i) => (
          <label key={`bond-${i}`} className="block">
            <span className="text-muted text-xs">Background bond {i + 1}</span>
            <input
              className="input w-full mt-1"
              value={bonds[i] || ""}
              onChange={(e) => {
                const next = [...bonds];
                next[i] = e.target.value;
                onChange({ ...entity, background_bonds: next });
              }}
            />
          </label>
        ))}
      </section>

      <section className="space-y-2">
        <div className="font-medium text-xs text-muted uppercase tracking-wide">
          Essences ({baseSum}/{playerPoints} base points · total {options?.level_1_essence_total ?? 16}{" "}
          with Origin + Role)
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {essenceKeys.map((k) => (
            <label key={k} className="block">
              <span className="text-muted text-xs">{ESSENCE_LABELS[k] || k}</span>
              <input
                type="number"
                min={1}
                max={10}
                className="input w-full mt-1"
                value={baseEssences[k]}
                onChange={(e) =>
                  onChange({
                    ...entity,
                    base_essences: { ...baseEssences, [k]: Math.max(1, Number(e.target.value) || 1) },
                  })
                }
              />
              <span className="text-xs text-muted">→ {essences[k] ?? "—"}</span>
            </label>
          ))}
        </div>
        <div className="text-xs text-muted">
          Defenses: Toughness {defenses.toughness ?? "—"}, Evasion {defenses.evasion ?? "—"}, Willpower{" "}
          {defenses.willpower ?? "—"}, Cleverness {defenses.cleverness ?? "—"}
        </div>
      </section>

      <section className="space-y-3">
        <div className="font-medium text-xs text-muted uppercase tracking-wide">Skills</div>
        {essenceKeys.map((ek) => (
          <div key={ek}>
            <div className="text-xs font-medium mb-1">{ESSENCE_LABELS[ek] || ek}</div>
            <div className="grid sm:grid-cols-2 gap-2">
              {(allSkills[ek] || []).map((sk) => (
                <label key={sk.id} className="flex items-center gap-2">
                  <span className="text-xs w-28 shrink-0 truncate">{sk.label}</span>
                  <select
                    className="select flex-1 text-xs py-1"
                    value={Number(skills[sk.id] ?? 0)}
                    onChange={(e) =>
                      onChange({
                        ...entity,
                        skills: { ...skills, [sk.id]: Number(e.target.value) },
                      })
                    }
                  >
                    {(options?.skill_ranks || []).map((r) => (
                      <option key={r.rank} value={r.rank}>
                        {r.label}
                      </option>
                    ))}
                  </select>
                </label>
              ))}
            </div>
          </div>
        ))}
      </section>

      <section className="space-y-2">
        <div className="font-medium text-xs text-muted uppercase tracking-wide">Cutie Mark</div>
        <label className="block">
          <span className="text-muted text-xs">Description</span>
          <input
            className="input w-full mt-1"
            value={String(entity.cutie_mark || "")}
            onChange={(e) => onChange({ ...entity, cutie_mark: e.target.value })}
          />
        </label>
        <label className="block">
          <span className="text-muted text-xs">Cutie Mark Perk (skill)</span>
          <input
            className="input w-full mt-1"
            value={String(entity.cutie_mark_perk_skill || "")}
            onChange={(e) => onChange({ ...entity, cutie_mark_perk_skill: e.target.value })}
            placeholder="e.g. Performance"
          />
        </label>
      </section>

      <section className="space-y-2">
        <div className="font-medium text-xs text-muted uppercase tracking-wide">Play shortcuts</div>
        <div className="grid sm:grid-cols-2 gap-3">
          <label className="block">
            <span className="text-muted text-xs">Default skill for Skill Test</span>
            <select
              className="select w-full mt-1"
              value={String(entity.default_skill_id || "alertness")}
              onChange={(e) => onChange({ ...entity, default_skill_id: e.target.value })}
            >
              {Object.values(allSkills)
                .flat()
                .map((sk) => (
                  <option key={sk.id} value={sk.id}>
                    {sk.label}
                  </option>
                ))}
            </select>
          </label>
          <label className="block">
            <span className="text-muted text-xs">Default DIF</span>
            <select
              className="select w-full mt-1"
              value={Number(entity.default_dif ?? 15)}
              onChange={(e) => onChange({ ...entity, default_dif: Number(e.target.value) })}
            >
              {(options?.dif_presets || []).map((d) => (
                <option key={d.id} value={d.dif}>
                  {d.label} ({d.dif})
                </option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="text-muted text-xs">Edge / Snag</span>
            <select
              className="select w-full mt-1"
              value={String(entity.edge_snag || "normal")}
              onChange={(e) => onChange({ ...entity, edge_snag: e.target.value })}
            >
              <option value="normal">Normal</option>
              <option value="edge">Edge</option>
              <option value="snag">Snag</option>
            </select>
          </label>
          <label className="block">
            <span className="text-muted text-xs">Friendship Points</span>
            <input
              type="number"
              min={0}
              max={20}
              className="input w-full mt-1"
              value={Number(entity.friendship_points ?? 1)}
              onChange={(e) =>
                onChange({ ...entity, friendship_points: Math.max(0, Number(e.target.value) || 0) })
              }
            />
          </label>
          <label className="block">
            <span className="text-muted text-xs">Spellcasting rank (0–6)</span>
            <input
              type="number"
              min={0}
              max={6}
              className="input w-full mt-1"
              value={Number(entity.spellcasting_rank ?? 0)}
              onChange={(e) =>
                onChange({ ...entity, spellcasting_rank: Math.max(0, Math.min(6, Number(e.target.value) || 0)) })
              }
            />
          </label>
          <label className="block">
            <span className="text-muted text-xs">Spell cost (downshift steps)</span>
            <input
              type="number"
              min={1}
              max={6}
              className="input w-full mt-1"
              value={Number(entity.spell_cost ?? 1)}
              onChange={(e) =>
                onChange({ ...entity, spell_cost: Math.max(1, Math.min(6, Number(e.target.value) || 1)) })
              }
            />
          </label>
        </div>
      </section>

      {error && <p className="text-accent text-xs">{error}</p>}

      <button type="button" className="btn btn-primary" disabled={saving} onClick={() => void save()}>
        {saving ? "Saving…" : "Save character"}
      </button>
    </div>
  );
}
