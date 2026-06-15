import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { rosterEntryLabel } from "../../lib/rosterLabel";
import type { WatchHeader } from "../../types";

interface WeatherOption {
  id: string;
  label: string;
  description: string;
}

interface Props {
  entity: Record<string, unknown>;
  onChange: (entity: Record<string, unknown>) => void;
  onSaved?: (entity: Record<string, unknown>, header: WatchHeader) => void;
  roster?: { id: string; name: string }[];
  activeId?: string;
  onSwitchRoster?: () => void;
}

export default function WatchSetupPanel({
  entity,
  onChange,
  onSaved,
  roster,
  activeId,
  onSwitchRoster,
}: Props) {
  const [weatherOptions, setWeatherOptions] = useState<WeatherOption[]>([]);
  const [saving, setSaving] = useState(false);
  const [switching, setSwitching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getLighthouseWatch().then((res) => {
      const opts = (res.options as { weather_moods?: WeatherOption[] }).weather_moods || [];
      setWeatherOptions(opts);
    });
  }, []);

  const switchRoster = async (id: string) => {
    if (!id || id === activeId) return;
    setSwitching(true);
    setError(null);
    try {
      await api.switchLighthouseWatch(id);
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
      const res = await api.updateLighthouseWatch(entity);
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
          <div className="label mb-2">Active watch</div>
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
        <div className="label mb-2">Keeper name</div>
        <input
          className="input"
          value={String(entity.name || "")}
          onChange={(e) => onChange({ ...entity, name: e.target.value })}
          placeholder="Your name or a character"
        />
      </section>

      <section>
        <div className="label mb-2">Night number</div>
        <input
          className="input w-24"
          type="number"
          min={1}
          value={Number(entity.night_count || 1)}
          onChange={(e) =>
            onChange({ ...entity, night_count: Math.max(1, Number(e.target.value) || 1) })
          }
        />
      </section>

      <section>
        <div className="label mb-2">Weather mood (p.8)</div>
        <select
          className="select"
          value={String(entity.weather_mood || "")}
          onChange={(e) => onChange({ ...entity, weather_mood: e.target.value })}
        >
          <option value="">— Choose tonight —</option>
          {weatherOptions.map((w) => (
            <option key={w.id} value={w.id}>
              {w.label}
            </option>
          ))}
        </select>
        {entity.weather_mood != null && String(entity.weather_mood) !== "" && (
          <p className="text-xs text-muted mt-2">
            {weatherOptions.find((w) => w.id === entity.weather_mood)?.description ?? ""}
          </p>
        )}
      </section>

      {error && <p className="text-sm text-red-300">{error}</p>}

      <button type="button" className="btn btn-primary" disabled={saving} onClick={save}>
        {saving ? "Saving…" : "Save watch setup"}
      </button>
    </div>
  );
}
