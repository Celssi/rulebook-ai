import { useEffect, useMemo, useState } from "react";
import { gmSoloApi } from "../../api/gmSolo";
import type { PlayHeader, SessionState } from "../../types";

interface TableOption {
  id: string;
  label: string;
}

interface SpecialtyOption extends TableOption {
  free_talent: string;
}

interface ProfessionOption extends TableOption {
  key_attribute: string;
  key_talents: string[];
  specialties: SpecialtyOption[];
}

interface CoriolisOptions {
  attributes: TableOption[];
  professions: ProfessionOption[];
  talents: TableOption[];
  crew_roles: TableOption[];
  attribute_budget: number;
}

interface Props {
  entity: Record<string, unknown>;
  onSaved: (session: SessionState, header?: PlayHeader) => void;
  session: SessionState;
}

const ATTR_KEYS = ["strength", "agility", "logic", "perception", "insight", "empathy"] as const;

function optionLabel(options: TableOption[], id: string): string {
  return options.find((o) => o.id === id)?.label || id.replace(/_/g, " ");
}

export default function CoriolisSetupPanel({ entity, onSaved, session }: Props) {
  const api = gmSoloApi("coriolis");
  const [options, setOptions] = useState<CoriolisOptions | null>(null);

  const name = String(entity.name || "");
  const profession = String(entity.profession || "");
  const specialty = String(entity.specialty || "");
  const crewName = String(entity.crew_name || "");
  const birdName = String(entity.bird_name || "");
  const shuttleName = String(entity.shuttle_name || "");
  const roverName = String(entity.rover_name || "");
  const gearBonus = Number(entity.gear_bonus ?? 0);
  const health = Number(entity.health ?? 0);
  const hope = Number(entity.hope ?? 0);
  const heart = Number(entity.heart ?? 0);
  const attributes = (entity.attributes as Record<string, number>) || {};
  const talents = (entity.talents as Record<string, number>) || {};

  useEffect(() => {
    api.getCharacter().then((res) => setOptions(res.options as unknown as CoriolisOptions));
  }, []);

  const budget = options?.attribute_budget ?? 24;
  const budgetUsed = useMemo(
    () => ATTR_KEYS.reduce((sum, k) => sum + Number(attributes[k] ?? 0), 0),
    [attributes],
  );

  const selectedProfession = options?.professions.find((p) => p.id === profession);
  const specialties = selectedProfession?.specialties || [];

  const saveEntity = async (patch: Record<string, unknown>) => {
    const res = await api.updateCharacter({ ...entity, ...patch });
    onSaved({ ...session, entity: res.entity }, res.header);
  };

  const saveAttribute = (key: string, raw: string) => {
    const val = Math.max(2, Math.min(6, parseInt(raw, 10) || 2));
    void saveEntity({ attributes: { ...attributes, [key]: val } });
  };

  const saveTalentLevel = (talentId: string, level: number) => {
    const next = { ...talents, [talentId]: Math.max(0, Math.min(3, level)) };
    if (level <= 0) delete next[talentId];
    void saveEntity({ talents: next, last_talent: talentId });
  };

  const talentChoices = options?.talents || [];
  const activeTalents = Object.entries(talents).filter(([, lvl]) => Number(lvl) > 0);

  return (
    <div className="space-y-3 text-sm">
      <label className="block">
        <span className="text-muted text-xs">Explorer name</span>
        <input
          className="input w-full mt-1"
          defaultValue={name}
          onBlur={(e) => {
            const v = e.target.value.trim();
            if (v !== name) void saveEntity({ name: v });
          }}
        />
      </label>

      <div className="grid sm:grid-cols-2 gap-3">
        <label className="block">
          <span className="text-muted text-xs">Profession</span>
          <select
            className="select w-full mt-1"
            value={profession}
            onChange={(e) => void saveEntity({ profession: e.target.value, specialty: "" })}
          >
            <option value="">—</option>
            {(options?.professions || []).map((p) => (
              <option key={p.id} value={p.id}>
                {p.label}
              </option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="text-muted text-xs">Specialty</span>
          <select
            className="select w-full mt-1"
            value={specialty}
            disabled={!profession}
            onChange={(e) => {
              const sid = e.target.value;
              const spec = specialties.find((s) => s.id === sid);
              const patch: Record<string, unknown> = { specialty: sid };
              if (spec?.free_talent) {
                patch.talents = { ...talents, [spec.free_talent]: 1 };
                patch.last_talent = spec.free_talent;
              }
              void saveEntity(patch);
            }}
          >
            <option value="">—</option>
            {specialties.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div>
        <div className="flex justify-between text-xs text-muted mb-1">
          <span>Attributes (budget {budgetUsed}/{budget})</span>
          {selectedProfession?.key_attribute && (
            <span>Key: {optionLabel(options?.attributes || [], selectedProfession.key_attribute)}</span>
          )}
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {ATTR_KEYS.map((key) => (
            <label key={key} className="block">
              <span className="text-muted text-[10px]">{optionLabel(options?.attributes || [], key)}</span>
              <input
                type="number"
                min={2}
                max={selectedProfession?.key_attribute === key ? 6 : 5}
                className="input w-full mt-0.5 py-1 text-sm"
                value={Number(attributes[key] ?? 4)}
                onChange={(e) => saveAttribute(key, e.target.value)}
              />
            </label>
          ))}
        </div>
      </div>

      <div className="grid sm:grid-cols-3 gap-3">
        <label className="block">
          <span className="text-muted text-xs">Health</span>
          <input
            type="number"
            min={0}
            className="input w-full mt-1"
            value={health}
            onChange={(e) => void saveEntity({ health: parseInt(e.target.value, 10) || 0 })}
          />
        </label>
        <label className="block">
          <span className="text-muted text-xs">Hope</span>
          <input
            type="number"
            min={0}
            className="input w-full mt-1"
            value={hope}
            onChange={(e) => void saveEntity({ hope: parseInt(e.target.value, 10) || 0 })}
          />
        </label>
        <label className="block">
          <span className="text-muted text-xs">Heart</span>
          <input
            type="number"
            min={0}
            className="input w-full mt-1"
            value={heart}
            onChange={(e) => void saveEntity({ heart: parseInt(e.target.value, 10) || 0 })}
          />
        </label>
      </div>

      <div className="grid sm:grid-cols-2 gap-3">
        <label className="block">
          <span className="text-muted text-xs">Crew name</span>
          <input
            className="input w-full mt-1"
            defaultValue={crewName}
            onBlur={(e) => {
              const v = e.target.value.trim();
              if (v !== crewName) void saveEntity({ crew_name: v });
            }}
          />
        </label>
        <label className="block">
          <span className="text-muted text-xs">Bird name</span>
          <input
            className="input w-full mt-1"
            defaultValue={birdName}
            onBlur={(e) => {
              const v = e.target.value.trim();
              if (v !== birdName) void saveEntity({ bird_name: v });
            }}
          />
        </label>
        <label className="block">
          <span className="text-muted text-xs">Shuttle name</span>
          <input
            className="input w-full mt-1"
            defaultValue={shuttleName}
            onBlur={(e) => {
              const v = e.target.value.trim();
              if (v !== shuttleName) void saveEntity({ shuttle_name: v });
            }}
          />
        </label>
        <label className="block">
          <span className="text-muted text-xs">Rover name</span>
          <input
            className="input w-full mt-1"
            defaultValue={roverName}
            onBlur={(e) => {
              const v = e.target.value.trim();
              if (v !== roverName) void saveEntity({ rover_name: v });
            }}
          />
        </label>
      </div>

      <label className="block">
        <span className="text-muted text-xs">Gear bonus dice</span>
        <input
          type="number"
          min={0}
          max={6}
          className="input w-full mt-1"
          value={gearBonus}
          onChange={(e) => void saveEntity({ gear_bonus: parseInt(e.target.value, 10) || 0 })}
        />
      </label>

      <div>
        <span className="text-muted text-xs">Talents</span>
        {activeTalents.length > 0 && (
          <ul className="mt-1 space-y-1">
            {activeTalents.map(([tid, lvl]) => (
              <li key={tid} className="flex items-center gap-2">
                <span className="flex-1 truncate">{optionLabel(talentChoices, tid)}</span>
                <select
                  className="select py-0.5 text-xs"
                  value={Number(lvl)}
                  onChange={(e) => saveTalentLevel(tid, parseInt(e.target.value, 10))}
                >
                  {[0, 1, 2, 3].map((n) => (
                    <option key={n} value={n}>
                      {n}
                    </option>
                  ))}
                </select>
              </li>
            ))}
          </ul>
        )}
        <select
          className="select w-full mt-1"
          value=""
          onChange={(e) => {
            const tid = e.target.value;
            if (tid) saveTalentLevel(tid, 1);
          }}
        >
          <option value="">Add talent…</option>
          {talentChoices
            .filter((t) => !talents[t.id])
            .map((t) => (
              <option key={t.id} value={t.id}>
                {t.label}
              </option>
            ))}
        </select>
      </div>

      <p className="text-xs text-muted">
        Use shortcuts in the Play tab for attribute rolls, pushes, despair checks, and encounters.
      </p>
    </div>
  );
}
