import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { rosterEntryLabel } from "../../lib/rosterLabel";
import type { ColostleHeader } from "../../types";

interface ClassOption {
  id: string;
  label: string;
  exploration: number;
  combat: number;
}

interface Props {
  entity: Record<string, unknown>;
  onChange: (entity: Record<string, unknown>) => void;
  onSaved?: (entity: Record<string, unknown>, header: ColostleHeader) => void;
  roster?: { id: string; name: string }[];
  activeId?: string;
  onSwitchRoster?: () => void;
}

export default function AdventurerSetupPanel({
  entity,
  onChange,
  onSaved,
  roster,
  activeId,
  onSwitchRoster,
}: Props) {
  const [classes, setClasses] = useState<ClassOption[]>([]);
  const [saving, setSaving] = useState(false);
  const [drawing, setDrawing] = useState(false);
  const [switching, setSwitching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getColostleCharacter().then((res) => {
      const opts = (res.options as { classes?: ClassOption[] }).classes || [];
      setClasses(opts);
    });
  }, []);

  const switchRoster = async (id: string) => {
    if (!id || id === activeId) return;
    setSwitching(true);
    setError(null);
    try {
      await api.switchColostleCharacter(id);
      onSwitchRoster?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Switch failed");
    } finally {
      setSwitching(false);
    }
  };

  const applyClass = (classId: string) => {
    const picked = classes.find((c) => c.id === classId);
    onChange({
      ...entity,
      character_class: classId,
      exploration_score: picked?.exploration ?? entity.exploration_score,
      combat_score: picked?.combat ?? entity.combat_score,
    });
  };

  const drawCallingNature = async () => {
    setDrawing(true);
    setError(null);
    try {
      const res = await api.runColostleShortcut("draw_character");
      onChange(res.entity);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Draw failed");
    } finally {
      setDrawing(false);
    }
  };

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      const res = await api.updateColostleCharacter(entity);
      onChange(res.entity);
      onSaved?.(res.entity, res.header);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      {roster && roster.length > 0 && (
        <section>
          <div className="label mb-2">Active adventurer</div>
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

      <section>
        <div className="label mb-2">Name</div>
        <input
          className="input"
          value={String(entity.name || "")}
          onChange={(e) => onChange({ ...entity, name: e.target.value })}
          placeholder="Adventurer name"
        />
      </section>

      <section>
        <div className="label mb-2">Look</div>
        <input
          className="input"
          value={String(entity.look || "")}
          onChange={(e) => onChange({ ...entity, look: e.target.value })}
          placeholder="Appearance"
        />
      </section>

      <section>
        <div className="label mb-2">Class</div>
        <select
          className="select"
          value={String(entity.character_class || "")}
          onChange={(e) => applyClass(e.target.value)}
        >
          <option value="">— Choose class —</option>
          {classes.map((c) => (
            <option key={c.id} value={c.id}>
              {c.label} (Exp {c.exploration}, Combat {c.combat})
            </option>
          ))}
        </select>
      </section>

      <section>
        <div className="label mb-2">Weapon</div>
        <input
          className="input"
          value={String(entity.weapon || "")}
          onChange={(e) => onChange({ ...entity, weapon: e.target.value })}
          placeholder="Your weapon"
        />
      </section>

      <section className="grid grid-cols-2 gap-3">
        <div>
          <div className="label mb-2">Exploration</div>
          <input
            className="input w-full"
            type="number"
            min={0}
            max={5}
            value={Number(entity.exploration_score ?? 3)}
            onChange={(e) =>
              onChange({ ...entity, exploration_score: Math.min(5, Math.max(0, Number(e.target.value) || 0)) })
            }
          />
        </div>
        <div>
          <div className="label mb-2">Combat</div>
          <input
            className="input w-full"
            type="number"
            min={0}
            max={5}
            value={Number(entity.combat_score ?? 3)}
            onChange={(e) =>
              onChange({ ...entity, combat_score: Math.min(5, Math.max(0, Number(e.target.value) || 0)) })
            }
          />
        </div>
      </section>

      <section>
        <div className="label mb-2">Calling &amp; Nature</div>
        <button type="button" className="btn btn-secondary w-full" disabled={drawing} onClick={drawCallingNature}>
          {drawing ? "Drawing…" : "Draw Calling & Nature (2 cards)"}
        </button>
        {entity.calling != null && String(entity.calling) !== "" && (
          <p className="text-xs text-muted mt-2 line-clamp-3">
            <strong>Calling:</strong> {String(entity.calling)}
          </p>
        )}
        {entity.nature != null && String(entity.nature) !== "" && (
          <p className="text-xs text-muted mt-1">
            <strong>Nature:</strong> {String(entity.nature)}
          </p>
        )}
      </section>

      {error && <p className="text-sm text-red-300">{error}</p>}

      <button type="button" className="btn btn-primary" disabled={saving} onClick={save}>
        {saving ? "Saving…" : "Save adventurer"}
      </button>
    </div>
  );
}
