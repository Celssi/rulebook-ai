import { useEffect, useState } from "react";
import { gmSoloApi } from "../../api/gmSolo";
import type { PlayHeader, SessionState } from "../../types";
import { FormSelect } from "../shared/FormFields";

const OUTGUNNED_PHASES = [
  "Pilot Shot",
  "Discovery",
  "Point of No Return",
  "Exploration",
  "Moment of Truth",
  "Establishing Shot",
  "Pressure",
  "Turning Point",
  "Crisis",
  "Showdown",
];

interface RoleOption {
  id: string;
  label: string;
  special?: boolean;
  attribute_point?: string;
  attribute_points?: string[];
  skill_points?: string[];
}

interface TropeOption {
  id: string;
  label: string;
  attribute_options?: string[];
  skill_points?: string[];
}

interface Props {
  entity: Record<string, unknown>;
  session: SessionState;
  onSaved: (session: SessionState, header?: PlayHeader) => void;
}

export default function OutgunnedSetupPanel({ entity, session, onSaved }: Props) {
  const api = gmSoloApi("outgunned");
  const [roles, setRoles] = useState<RoleOption[]>([]);
  const [tropes, setTropes] = useState<TropeOption[]>([]);
  const [attributes, setAttributes] = useState<string[]>([]);
  const [skills, setSkills] = useState<string[]>([]);
  const [ages, setAges] = useState<string[]>([]);

  const adState = (entity.ad_state as Record<string, unknown> | undefined) || {};
  const attrs = (entity.attributes as Record<string, number> | undefined) || {};
  const skillMap = (entity.skills as Record<string, number> | undefined) || {};

  useEffect(() => {
    api.getCharacter().then((res) => {
      const opts = res.options as {
        roles?: RoleOption[];
        tropes?: TropeOption[];
        attributes?: string[];
        skills?: string[];
        ages?: string[];
      };
      setRoles(opts.roles || []);
      setTropes(opts.tropes || []);
      setAttributes(opts.attributes || []);
      setSkills(opts.skills || []);
      setAges(opts.ages || ["Young", "Adult", "Old"]);
    });
  }, []);

  const saveEntity = async (patch: Record<string, unknown>) => {
    const merged = { ...entity, ...patch };
    const res = await api.updateCharacter(merged);
    onSaved({ ...session, entity: res.entity }, res.header);
  };

  const applyRole = async (roleId: string) => {
    const row = roles.find((r) => r.id === roleId);
    if (!row) return;
    const nextAttrs = Object.fromEntries(attributes.map((a) => [a, 2]));
    const nextSkills = Object.fromEntries(skills.map((s) => [s, 1]));
    if (row.special) {
      for (const a of row.attribute_points || []) {
        if (nextAttrs[a] !== undefined) nextAttrs[a] = Math.min(3, nextAttrs[a] + 1);
      }
    } else if (row.attribute_point && nextAttrs[row.attribute_point] !== undefined) {
      nextAttrs[row.attribute_point] = Math.min(3, nextAttrs[row.attribute_point] + 1);
    }
    for (const sk of row.skill_points || []) {
      if (nextSkills[sk] !== undefined) nextSkills[sk] = Math.min(3, nextSkills[sk] + 1);
    }
    await saveEntity({
      role: roleId,
      trope: row.special ? "" : String(entity.trope || ""),
      attributes: nextAttrs,
      skills: nextSkills,
      feats: [],
      solo_boosts_applied: false,
      solo_boost_attr: "",
      solo_boost_skills: [],
    });
  };

  const applyTrope = async (tropeId: string) => {
    const roleId = String(entity.role || "");
    if (!roleId) return;
    const roleRow = roles.find((r) => r.id === roleId);
    const tropeRow = tropes.find((t) => t.id === tropeId);
    if (!roleRow || !tropeRow || roleRow.special) return;
    const nextAttrs = Object.fromEntries(attributes.map((a) => [a, 2]));
    const nextSkills = Object.fromEntries(skills.map((s) => [s, 1]));
    if (roleRow.attribute_point && nextAttrs[roleRow.attribute_point] !== undefined) {
      nextAttrs[roleRow.attribute_point] = Math.min(3, nextAttrs[roleRow.attribute_point] + 1);
    }
    for (const sk of roleRow.skill_points || []) {
      if (nextSkills[sk] !== undefined) nextSkills[sk] = Math.min(3, nextSkills[sk] + 1);
    }
    const opts = tropeRow.attribute_options || [];
    const roleAttr = roleRow.attribute_point || "";
    const attrPick = opts.length > 1 && roleAttr === opts[0] ? opts[1] : opts[0];
    if (attrPick && nextAttrs[attrPick] !== undefined) {
      nextAttrs[attrPick] = Math.min(3, nextAttrs[attrPick] + 1);
    }
    for (const sk of tropeRow.skill_points || []) {
      if (nextSkills[sk] !== undefined) nextSkills[sk] = Math.min(3, nextSkills[sk] + 1);
    }
    await saveEntity({
      trope: tropeId,
      attributes: nextAttrs,
      skills: nextSkills,
      solo_boosts_applied: false,
      solo_boost_attr: "",
      solo_boost_skills: [],
    });
  };

  const applySoloBoosts = async () => {
    const boostAttr = String(entity.solo_boost_attr || "");
    const boostSkills = (entity.solo_boost_skills as string[] | undefined) || [];
    const nextAttrs = { ...attrs };
    const nextSkills = { ...skillMap };
    if (boostAttr && nextAttrs[boostAttr] !== undefined) {
      nextAttrs[boostAttr] = Math.min(3, (nextAttrs[boostAttr] || 2) + 1);
    }
    for (const sk of boostSkills.slice(0, 2)) {
      if (nextSkills[sk] !== undefined) {
        nextSkills[sk] = Math.min(3, (nextSkills[sk] || 1) + 1);
      }
    }
    await saveEntity({
      attributes: nextAttrs,
      skills: nextSkills,
      solo_boosts_applied: true,
    });
  };

  return (
    <div className="space-y-4 text-sm max-h-[60vh] overflow-y-auto pr-1">
      <section className="space-y-2">
        <h3 className="text-xs font-semibold text-muted uppercase tracking-wide">Identity</h3>
        <label className="block">
          <span className="text-muted text-xs">Name</span>
          <input
            className="input w-full mt-1"
            defaultValue={String(entity.name || "")}
            onBlur={(e) => {
              const v = e.target.value.trim();
              if (v !== String(entity.name || "")) void saveEntity({ name: v });
            }}
          />
        </label>
        <div className="grid grid-cols-2 gap-3">
          <label className="block">
            <span className="text-muted text-xs">Age</span>
            <FormSelect
              className="w-full mt-1"
              defaultValue={String(entity.age || "Adult")}
              onChange={(e) => void saveEntity({ age: e.target.value })}
            >
              {ages.map((a) => (
                <option key={a} value={a}>
                  {a}
                </option>
              ))}
            </FormSelect>
          </label>
          <label className="block">
            <span className="text-muted text-xs">Role</span>
            <FormSelect
              className="w-full mt-1"
              value={String(entity.role || "")}
              onChange={(e) => void applyRole(e.target.value)}
            >
              <option value="">—</option>
              {roles.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.label}
                </option>
              ))}
            </FormSelect>
          </label>
        </div>
        {!roles.find((r) => r.id === entity.role)?.special && (
          <label className="block">
            <span className="text-muted text-xs">Trope</span>
            <FormSelect
              className="w-full mt-1"
              value={String(entity.trope || "")}
              onChange={(e) => void applyTrope(e.target.value)}
            >
              <option value="">—</option>
              {tropes.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.label}
                </option>
              ))}
            </FormSelect>
          </label>
        )}
        <label className="block">
          <span className="text-muted text-xs">Background</span>
          <input
            className="input w-full mt-1"
            defaultValue={String(entity.background || "")}
            onBlur={(e) => {
              const v = e.target.value.trim();
              if (v !== String(entity.background || "")) void saveEntity({ background: v });
            }}
          />
        </label>
        <div className="grid grid-cols-2 gap-3">
          <label className="block">
            <span className="text-muted text-xs">Catchphrase</span>
            <input
              className="input w-full mt-1"
              defaultValue={String(entity.catchphrase || "")}
              onBlur={(e) => {
                const v = e.target.value.trim();
                if (v !== String(entity.catchphrase || "")) void saveEntity({ catchphrase: v });
              }}
            />
          </label>
          <label className="block">
            <span className="text-muted text-xs">Flaw</span>
            <input
              className="input w-full mt-1"
              defaultValue={String(entity.flaw || "")}
              onBlur={(e) => {
                const v = e.target.value.trim();
                if (v !== String(entity.flaw || "")) void saveEntity({ flaw: v });
              }}
            />
          </label>
        </div>
      </section>

      <section className="space-y-2">
        <h3 className="text-xs font-semibold text-muted uppercase tracking-wide">Solo boosts</h3>
        <div className="grid grid-cols-2 gap-3">
          <label className="block">
            <span className="text-muted text-xs">+1 Attribute</span>
            <FormSelect
              className="w-full mt-1"
              value={String(entity.solo_boost_attr || "")}
              disabled={Boolean(entity.solo_boosts_applied)}
              onChange={(e) => void saveEntity({ solo_boost_attr: e.target.value })}
            >
              <option value="">—</option>
              {attributes.map((a) => (
                <option key={a} value={a}>
                  {a}
                </option>
              ))}
            </FormSelect>
          </label>
          <label className="block">
            <span className="text-muted text-xs">+2 Skills (comma-separated)</span>
            <input
              className="input w-full mt-1"
              defaultValue={((entity.solo_boost_skills as string[]) || []).join(", ")}
              disabled={Boolean(entity.solo_boosts_applied)}
              onBlur={(e) => {
                const list = e.target.value
                  .split(",")
                  .map((s) => s.trim())
                  .filter(Boolean)
                  .slice(0, 2);
                void saveEntity({ solo_boost_skills: list });
              }}
              placeholder="Fight, Shoot"
            />
          </label>
        </div>
        <button
          type="button"
          className="btn btn-secondary text-xs"
          disabled={Boolean(entity.solo_boosts_applied)}
          onClick={() => void applySoloBoosts()}
        >
          Apply Solo Boosts
        </button>
      </section>

      <section className="space-y-2">
        <h3 className="text-xs font-semibold text-muted uppercase tracking-wide">Campaign</h3>
        <label className="block">
          <span className="text-muted text-xs">Mission title</span>
          <input
            className="input w-full mt-1"
            defaultValue={String(entity.mission_title || "")}
            onBlur={(e) => {
              const v = e.target.value.trim();
              if (v !== String(entity.mission_title || "")) void saveEntity({ mission_title: v });
            }}
          />
        </label>
        <label className="block">
          <span className="text-muted text-xs">Campaign phase</span>
          <input
            className="input w-full mt-1"
            list="outgunned-phases"
            defaultValue={String(adState.phase || "")}
            onBlur={(e) => {
              const v = e.target.value.trim();
              if (v !== String(adState.phase || "")) {
                void saveEntity({ ad_state: { ...adState, phase: v } });
              }
            }}
          />
          <datalist id="outgunned-phases">
            {OUTGUNNED_PHASES.map((p) => (
              <option key={p} value={p} />
            ))}
          </datalist>
        </label>
        <div className="grid grid-cols-2 gap-3">
          <label className="block">
            <span className="text-muted text-xs">Phase aim</span>
            <input
              className="input w-full mt-1"
              defaultValue={String(adState.aim || "")}
              onBlur={(e) => {
                const v = e.target.value.trim();
                if (v !== String(adState.aim || "")) {
                  void saveEntity({ ad_state: { ...adState, aim: v } });
                }
              }}
            />
          </label>
          <label className="block">
            <span className="text-muted text-xs">Phase hurdle</span>
            <input
              className="input w-full mt-1"
              defaultValue={String(adState.hurdle || "")}
              onBlur={(e) => {
                const v = e.target.value.trim();
                if (v !== String(adState.hurdle || "")) {
                  void saveEntity({ ad_state: { ...adState, hurdle: v } });
                }
              }}
            />
          </label>
        </div>
        <div className="grid grid-cols-3 gap-3">
          <label className="block">
            <span className="text-muted text-xs">Tension (0–12)</span>
            <input
              type="number"
              min={0}
              max={12}
              className="input w-full mt-1"
              defaultValue={Number(adState.tension ?? 1)}
              onBlur={(e) => {
                const v = Math.max(0, Math.min(12, Number(e.target.value) || 1));
                void saveEntity({ ad_state: { ...adState, tension: v } });
              }}
            />
          </label>
          <label className="block">
            <span className="text-muted text-xs">Death Roulette (1–6)</span>
            <input
              type="number"
              min={1}
              max={6}
              className="input w-full mt-1"
              defaultValue={Number(entity.death_roulette_bullets ?? 1)}
              onBlur={(e) => {
                const v = Math.max(1, Math.min(6, Number(e.target.value) || 1));
                void saveEntity({ death_roulette_bullets: v });
              }}
            />
          </label>
          <label className="block">
            <span className="text-muted text-xs">Fallback pool dice</span>
            <input
              type="number"
              min={2}
              max={9}
              className="input w-full mt-1"
              defaultValue={Number(adState.pool_dice ?? 3)}
              onBlur={(e) => {
                const v = Math.max(2, Math.min(9, Number(e.target.value) || 3));
                void saveEntity({ ad_state: { ...adState, pool_dice: v } });
              }}
            />
          </label>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <label className="block">
            <span className="text-muted text-xs">Roll attribute</span>
            <FormSelect
              className="w-full mt-1"
              value={String(entity.roll_attribute || "")}
              onChange={(e) => void saveEntity({ roll_attribute: e.target.value })}
            >
              <option value="">—</option>
              {attributes.map((a) => (
                <option key={a} value={a}>
                  {a} ({attrs[a] ?? 2})
                </option>
              ))}
            </FormSelect>
          </label>
          <label className="block">
            <span className="text-muted text-xs">Roll skill</span>
            <FormSelect
              className="w-full mt-1"
              value={String(entity.roll_skill || "")}
              onChange={(e) => void saveEntity({ roll_skill: e.target.value })}
            >
              <option value="">—</option>
              {skills.map((s) => (
                <option key={s} value={s}>
                  {s} ({skillMap[s] ?? 1})
                </option>
              ))}
            </FormSelect>
          </label>
        </div>
      </section>

      <p className="text-xs text-muted">
        Use Play shortcuts for AD prompts, dice pools, re-rolls, Tension, and Death Roulette.
        Enable <strong>AI narrator</strong> in Settings for cinematic prose.
      </p>
    </div>
  );
}
