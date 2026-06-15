import { useEffect, useState } from "react";
import { gmSoloApi } from "../../api/gmSolo";
import type { PlayHeader, SessionState } from "../../types";

interface TableOption {
  id: string;
  label: string;
}

interface TorOptions {
  cultures: TableOption[];
  patrons: TableOption[];
  callings: TableOption[];
  hunt_regions: TableOption[];
}

interface Props {
  entity: Record<string, unknown>;
  onSaved: (session: SessionState, header?: PlayHeader) => void;
  session: SessionState;
}

function optionLabel(options: TableOption[], id: string): string {
  return options.find((o) => o.id === id)?.label || id.replace(/_/g, " ");
}

export default function TorSetupPanel({ entity, onSaved, session }: Props) {
  const api = gmSoloApi("tor");
  const [options, setOptions] = useState<TorOptions | null>(null);

  const name = String(entity.name || "");
  const culture = String(entity.culture || "");
  const calling = String(entity.calling || "");
  const patron = String(entity.patron || "");
  const safeHaven = String(entity.safe_haven || "");
  const hope = Number(entity.hope ?? 0);
  const dread = Number(entity.dread ?? 0);
  const eyeAwareness = Number(entity.eye_awareness ?? 0);
  const journeyDay = Number(entity.journey_day ?? 0);
  const huntRegion = String(entity.hunt_region || "wild");
  const weary = Boolean(entity.weary);
  const strider = entity.strider !== false;

  useEffect(() => {
    api.getCharacter().then((res) => setOptions(res.options as unknown as TorOptions));
  }, []);

  const saveEntity = async (patch: Record<string, unknown>) => {
    const res = await api.updateCharacter({ ...entity, ...patch });
    onSaved({ ...session, entity: res.entity }, res.header);
  };

  const cultures = options?.cultures || [];
  const patrons = options?.patrons || [];
  const callings = options?.callings || [];
  const huntRegions = options?.hunt_regions || [];

  const cultureIds = new Set(cultures.map((c) => c.id));
  const cultureOptions =
    culture && !cultureIds.has(culture)
      ? [...cultures, { id: culture, label: optionLabel(cultures, culture) }]
      : cultures;

  return (
    <div className="space-y-3 text-sm">
      <label className="block">
        <span className="text-muted text-xs">Name</span>
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
          <span className="text-muted text-xs">Culture</span>
          <select
            className="select w-full mt-1"
            value={culture}
            onChange={(e) => void saveEntity({ culture: e.target.value })}
          >
            <option value="">—</option>
            {cultureOptions.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label}
              </option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="text-muted text-xs">Calling</span>
          <select
            className="select w-full mt-1"
            value={calling}
            onChange={(e) => void saveEntity({ calling: e.target.value })}
          >
            <option value="">—</option>
            {callings.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <label className="block">
        <span className="text-muted text-xs">Patron</span>
        <select
          className="select w-full mt-1"
          value={patron}
          onChange={(e) => void saveEntity({ patron: e.target.value })}
        >
          <option value="">—</option>
          {patrons.map((p) => (
            <option key={p.id} value={p.id}>
              {p.label}
            </option>
          ))}
        </select>
      </label>

      <label className="block">
        <span className="text-muted text-xs">Safe Haven</span>
        <input
          className="input w-full mt-1"
          defaultValue={safeHaven}
          placeholder="e.g. Rivendell"
          onBlur={(e) => {
            const v = e.target.value.trim();
            if (v !== safeHaven) void saveEntity({ safe_haven: v });
          }}
        />
      </label>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <label className="block">
          <span className="text-muted text-xs">Hope</span>
          <input
            type="number"
            min={0}
            max={20}
            className="input w-full mt-1"
            defaultValue={hope}
            onBlur={(e) => {
              const v = Math.max(0, Math.min(20, Number(e.target.value) || 0));
              if (v !== hope) void saveEntity({ hope: v });
            }}
          />
        </label>
        <label className="block">
          <span className="text-muted text-xs">Dread</span>
          <input
            type="number"
            min={0}
            max={20}
            className="input w-full mt-1"
            defaultValue={dread}
            onBlur={(e) => {
              const v = Math.max(0, Math.min(20, Number(e.target.value) || 0));
              if (v !== dread) void saveEntity({ dread: v });
            }}
          />
        </label>
        <label className="block">
          <span className="text-muted text-xs">Eye Awareness</span>
          <input
            type="number"
            min={0}
            max={20}
            className="input w-full mt-1"
            defaultValue={eyeAwareness}
            onBlur={(e) => {
              const v = Math.max(0, Math.min(20, Number(e.target.value) || 0));
              if (v !== eyeAwareness) void saveEntity({ eye_awareness: v });
            }}
          />
        </label>
        <label className="block">
          <span className="text-muted text-xs">Journey day</span>
          <input
            type="number"
            min={0}
            max={999}
            className="input w-full mt-1"
            defaultValue={journeyDay}
            onBlur={(e) => {
              const v = Math.max(0, Math.min(999, Number(e.target.value) || 0));
              if (v !== journeyDay) void saveEntity({ journey_day: v });
            }}
          />
        </label>
      </div>

      <label className="block">
        <span className="text-muted text-xs">Hunt region (journey events)</span>
        <select
          className="select w-full mt-1"
          value={huntRegion}
          onChange={(e) => void saveEntity({ hunt_region: e.target.value })}
        >
          {huntRegions.map((r) => (
            <option key={r.id} value={r.id}>
              {r.label}
            </option>
          ))}
        </select>
      </label>

      <div className="flex flex-wrap gap-4">
        <label className="flex items-center gap-2 text-xs">
          <input
            type="checkbox"
            checked={weary}
            onChange={(e) => void saveEntity({ weary: e.target.checked })}
          />
          Weary
        </label>
        <label className="flex items-center gap-2 text-xs">
          <input
            type="checkbox"
            checked={strider}
            onChange={(e) => void saveEntity({ strider: e.target.checked })}
          />
          Strider (Inspired on journey)
        </label>
      </div>

      <p className="text-xs text-muted">
        Full character creation (attributes, skills, virtues) follows the Core Rulebook on paper.
        Use shortcuts for tables and dice. Enable <strong>AI narrator</strong> in Play settings for
        GM scene prose.
      </p>
    </div>
  );
}
