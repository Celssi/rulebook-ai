import { useEffect, useState } from "react";
import { Loader2, Shuffle } from "lucide-react";
import { api } from "../../api/client";
import type { CharacterHeader } from "../../types";
import { FormInput, FormSelect, RosterSelect } from "../shared/FormFields";

interface LegacyOption {
  id: string;
  label: string;
  tagline?: string;
  health?: number;
  morale?: number;
  supplies?: number;
}

interface Props {
  entity: Record<string, unknown>;
  onChange: (entity: Record<string, unknown>) => void;
  onSaved?: (entity: Record<string, unknown>, header: CharacterHeader) => void;
  roster?: { id: string; name: string }[];
  activeId?: string;
  onSwitchRoster?: () => void;
}

export default function CharacterSetupPanel({
  entity,
  onChange,
  onSaved,
  roster = [],
  activeId = "",
  onSwitchRoster,
}: Props) {
  const [local, setLocal] = useState(entity);
  const [legacies, setLegacies] = useState<LegacyOption[]>([]);
  const [drawing, setDrawing] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => setLocal(entity), [entity]);

  useEffect(() => {
    api.getBt2Character().then((res) => {
      const opts = (res.options?.legacies || []) as LegacyOption[];
      setLegacies(opts);
    });
  }, []);

  const patch = (key: string, value: unknown) => {
    const next = { ...local, [key]: value };
    setLocal(next);
    onChange(next);
  };

  const applyLegacy = (legacyId: string) => {
    const leg = legacies.find((l) => l.id === legacyId);
    const next = {
      ...local,
      legacy: legacyId,
      health: leg?.health ?? local.health,
      morale: leg?.morale ?? local.morale,
      supplies: leg?.supplies ?? local.supplies,
      legacy_abilities_used: {},
    };
    setLocal(next);
    onChange(next);
  };

  const drawArrival = async () => {
    setDrawing(true);
    try {
      const res = await api.drawBt2Arrival();
      const entity = (res.entity || {}) as Record<string, unknown>;
      const next = {
        ...local,
        how_did_i_get_here: entity.how_did_i_get_here ?? res.label,
        how_did_i_get_here_card: entity.how_did_i_get_here_card ?? res.card,
      };
      setLocal(next);
      onChange(next);
    } finally {
      setDrawing(false);
    }
  };

  const save = async () => {
    setSaving(true);
    try {
      const res = await api.updateBt2Character(local);
      setLocal(res.entity);
      onSaved?.(res.entity, res.header);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      {roster.length > 0 && (
        <RosterSelect
          label="Traveller"
          roster={roster}
          activeId={activeId}
          onChange={(id) => {
            if (id !== activeId) onSwitchRoster?.();
          }}
        />
      )}
      <div>
        <div className="label mb-1">Name</div>
        <FormInput
          className="w-full"
          value={String(local.name || "")}
          onChange={(e) => patch("name", e.target.value)}
        />
      </div>
      <div>
        <div className="label mb-1">Legacy</div>
        <FormSelect
          className="w-full"
          value={String(local.legacy || "")}
          onChange={(e) => applyLegacy(e.target.value)}
        >
          <option value="">— Choose —</option>
          {legacies.map((l) => (
            <option key={l.id} value={l.id}>
              {l.label}
            </option>
          ))}
        </FormSelect>
        {local.legacy ? (
          <p className="text-[11px] text-muted mt-1">
            {String(legacies.find((l) => l.id === local.legacy)?.tagline ?? "")}
          </p>
        ) : null}
      </div>
      <div>
        <div className="flex items-center justify-between mb-1">
          <div className="label">How did I get here?</div>
          <button
            type="button"
            className="btn-ghost text-[11px] px-2 py-1 border border-border rounded inline-flex items-center gap-1"
            disabled={drawing}
            onClick={drawArrival}
          >
            {drawing ? <Loader2 className="w-3 h-3 animate-spin" /> : <Shuffle className="w-3 h-3" />}
            Draw
          </button>
        </div>
        {local.how_did_i_get_here_card ? (
          <div className="space-y-1">
            <p className="text-xs text-muted">{String(local.how_did_i_get_here_card)}</p>
            {local.how_did_i_get_here ? (
              <p className="text-[11px] leading-snug">{String(local.how_did_i_get_here)}</p>
            ) : null}
          </div>
        ) : (
          <p className="text-[11px] text-muted">Optional arrival prompt (p. 17)</p>
        )}
      </div>
      <button type="button" className="btn btn-primary w-full" disabled={saving} onClick={save}>
        {saving ? "Saving…" : "Save character setup"}
      </button>
    </div>
  );
}
