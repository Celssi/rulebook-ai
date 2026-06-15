import { useState } from "react";
import { api } from "../../api/client";
import { rosterEntryLabel } from "../../lib/rosterLabel";
import type { InvestigationHeader } from "../../types";

interface Props {
  entity: Record<string, unknown>;
  onChange: (entity: Record<string, unknown>) => void;
  onSaved?: (entity: Record<string, unknown>, header: InvestigationHeader) => void;
  roster?: { id: string; name: string }[];
  activeId?: string;
  onSwitchRoster?: () => void;
}

export default function InvestigationSetupPanel({
  entity,
  onChange,
  onSaved,
  roster,
  activeId,
  onSwitchRoster,
}: Props) {
  const [saving, setSaving] = useState(false);
  const [switching, setSwitching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = (key: string, value: string | number) => {
    onChange({ ...entity, [key]: value });
  };

  const switchRoster = async (id: string) => {
    if (!id || id === activeId) return;
    setSwitching(true);
    setError(null);
    try {
      await api.switchWhispersInvestigation(id);
      onSwitchRoster?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Switch failed");
    } finally {
      setSwitching(false);
    }
  };

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      const res = await api.updateWhispersInvestigation(entity);
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
          <div className="label mb-2">Active investigation</div>
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
        <div className="label mb-2">Investigator name</div>
        <input
          className="input"
          value={String(entity.investigator_name || "")}
          onChange={(e) => set("investigator_name", e.target.value)}
          placeholder="Private investigator"
        />
      </section>

      <section>
        <div className="label mb-2">Background</div>
        <textarea
          className="input min-h-[4rem]"
          value={String(entity.background || "")}
          onChange={(e) => set("background", e.target.value)}
          placeholder="Whose background is…"
        />
      </section>

      <section>
        <div className="label mb-2">Belonging</div>
        <textarea
          className="input min-h-[4rem]"
          value={String(entity.belonging || "")}
          onChange={(e) => set("belonging", e.target.value)}
          placeholder="Belonging to…"
        />
      </section>

      <section>
        <div className="label mb-2">Location name</div>
        <input
          className="input"
          value={String(entity.location_name || "")}
          onChange={(e) => set("location_name", e.target.value)}
          placeholder="After location draw — name this place"
        />
      </section>

      <section>
        <div className="label mb-2">Extra secrets cards (longer game)</div>
        <input
          className="input"
          type="number"
          min={0}
          max={10}
          value={Number(entity.extra_secrets || 0)}
          onChange={(e) => set("extra_secrets", Number(e.target.value) || 0)}
        />
      </section>

      {error && <p className="text-xs text-red-300">{error}</p>}

      <button type="button" className="btn btn-primary w-full" disabled={saving} onClick={save}>
        {saving ? "Saving…" : "Save investigation"}
      </button>
    </div>
  );
}
