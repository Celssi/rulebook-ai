import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { rosterEntryLabel } from "../../lib/rosterLabel";
import type { CottageHeader } from "../../types";

interface LocaleOption {
  id: string;
  label: string;
}

interface Props {
  entity: Record<string, unknown>;
  onChange: (entity: Record<string, unknown>) => void;
  onSaved?: (entity: Record<string, unknown>, header: CottageHeader) => void;
  roster?: { id: string; name: string }[];
  activeId?: string;
  onSwitchRoster?: () => void;
}

export default function CottageSetupPanel({
  entity,
  onChange,
  onSaved,
  roster,
  activeId,
  onSwitchRoster,
}: Props) {
  const [locales, setLocales] = useState<LocaleOption[]>([]);
  const [saving, setSaving] = useState(false);
  const [switching, setSwitching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getApothecariaCottage().then((res) => {
      const opts = (res.options as { locales?: LocaleOption[] }).locales || [];
      setLocales(opts);
    });
  }, []);

  const switchRoster = async (id: string) => {
    if (!id || id === activeId) return;
    setSwitching(true);
    setError(null);
    try {
      await api.switchApothecariaCottage(id);
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
      const res = await api.updateApothecariaCottage(entity);
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
          <div className="label mb-2">Active cottage</div>
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
        <div className="label mb-2">Witch name</div>
        <input
          className="input"
          value={String(entity.name || "")}
          onChange={(e) => onChange({ ...entity, name: e.target.value })}
          placeholder="Your witch's name"
        />
      </section>

      <section className="grid grid-cols-2 gap-3">
        <div>
          <div className="label mb-2">Reputation</div>
          <input
            className="input"
            type="number"
            min={0}
            value={Number(entity.reputation ?? 5)}
            onChange={(e) =>
              onChange({ ...entity, reputation: Math.max(0, Number(e.target.value) || 0) })
            }
          />
        </div>
        <div>
          <div className="label mb-2">Silver</div>
          <input
            className="input"
            type="number"
            min={0}
            value={Number(entity.silver ?? 0)}
            onChange={(e) =>
              onChange({ ...entity, silver: Math.max(0, Number(e.target.value) || 0) })
            }
          />
        </div>
      </section>

      <section className="grid grid-cols-2 gap-3">
        <div>
          <div className="label mb-2">Week</div>
          <input
            className="input"
            type="number"
            min={1}
            max={13}
            value={Number(entity.week ?? 1)}
            onChange={(e) =>
              onChange({ ...entity, week: Math.max(1, Math.min(13, Number(e.target.value) || 1)) })
            }
          />
        </div>
        <div>
          <div className="label mb-2">Season</div>
          <select
            className="select"
            value={String(entity.season || "spring")}
            onChange={(e) => onChange({ ...entity, season: e.target.value })}
          >
            {["spring", "summer", "autumn", "winter"].map((s) => (
              <option key={s} value={s}>
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </option>
            ))}
          </select>
        </div>
      </section>

      <section>
        <div className="label mb-2">Foraging locale</div>
        <select
          className="select"
          value={String(entity.current_locale || "village")}
          onChange={(e) => onChange({ ...entity, current_locale: e.target.value })}
        >
          {locales.map((loc) => (
            <option key={loc.id} value={loc.id}>
              {loc.label}
            </option>
          ))}
        </select>
      </section>

      {error && <p className="text-sm text-red-300">{error}</p>}

      <button type="button" className="btn btn-primary" disabled={saving} onClick={save}>
        {saving ? "Saving…" : "Save cottage setup"}
      </button>
    </div>
  );
}
