import { useState } from "react";
import { api } from "../../api/client";
import { rosterEntryLabel } from "../../lib/rosterLabel";
import type { PlayHeader, SessionState } from "../../types";

interface Props {
  session: SessionState;
  onSaved?: (session: SessionState, header?: PlayHeader) => void;
}

export default function ScionSetupPanel({ session, onSaved }: Props) {
  const entity = session.entity || {};
  const [name, setName] = useState(String(entity.name || ""));
  const [scionClass, setScionClass] = useState(String(entity.scion_class || ""));
  const [pwr, setPwr] = useState(Number(entity.pwr ?? 3));
  const [intStat, setIntStat] = useState(Number(entity.int ?? 3));
  const [agl, setAgl] = useState(Number(entity.agl ?? 3));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      const next = {
        ...entity,
        name: name.trim(),
        scion_class: scionClass,
        pwr,
        int: intStat,
        agl,
      };
      const res = await api.updateAshesScion(next);
      const s = await api.getSession();
      onSaved?.(s, res.header);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const drawGift = async () => {
    setSaving(true);
    setError(null);
    try {
      await api.drawAshesGift();
      const s = await api.getSession();
      const h = await api.getAshesHeader();
      onSaved?.(s, h);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Draw failed");
    } finally {
      setSaving(false);
    }
  };

  const runShortcut = async (id: string) => {
    setSaving(true);
    setError(null);
    try {
      await api.runAshesShortcut(id);
      const s = await api.getSession();
      const h = await api.getAshesHeader();
      onSaved?.(s, h);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Shortcut failed");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-3 text-sm">
      <div>
        <label className="label">Scion name</label>
        <input className="input w-full" value={name} onChange={(e) => setName(e.target.value)} />
      </div>
      <div>
        <label className="label">Class</label>
        <select className="select w-full" value={scionClass} onChange={(e) => setScionClass(e.target.value)}>
          <option value="">Choose…</option>
          <option value="warrior">Warrior</option>
          <option value="ordained">Ordained</option>
          <option value="pioneer">Pioneer</option>
          <option value="hallowed">Hallowed</option>
          <option value="deadeyed">Deadeyed</option>
        </select>
      </div>
      <div className="grid grid-cols-3 gap-2">
        <div>
          <label className="label">PWR</label>
          <input className="input w-full" type="number" min={-4} max={6} value={pwr} onChange={(e) => setPwr(Number(e.target.value))} />
        </div>
        <div>
          <label className="label">INT</label>
          <input className="input w-full" type="number" min={-4} max={6} value={intStat} onChange={(e) => setIntStat(Number(e.target.value))} />
        </div>
        <div>
          <label className="label">AGL</label>
          <input className="input w-full" type="number" min={-4} max={6} value={agl} onChange={(e) => setAgl(Number(e.target.value))} />
        </div>
      </div>
      {entity.fate_gift ? (
        <p className="text-xs text-muted">Fate&apos;s Gift: {String(entity.fate_gift).slice(0, 120)}…</p>
      ) : (
        <button type="button" className="btn btn-secondary w-full" disabled={saving} onClick={drawGift}>
          Draw Fate&apos;s Gift
        </button>
      )}
      <div className="grid grid-cols-3 gap-2">
        <button
          type="button"
          className="btn btn-secondary text-xs"
          disabled={saving}
          onClick={() => runShortcut("roll_melee_weapon")}
        >
          Roll melee
        </button>
        <button
          type="button"
          className="btn btn-secondary text-xs"
          disabled={saving}
          onClick={() => runShortcut("roll_ranged_weapon")}
        >
          Roll ranged
        </button>
        <button
          type="button"
          className="btn btn-secondary text-xs"
          disabled={saving}
          onClick={() => runShortcut("character_armour")}
        >
          Roll armour
        </button>
      </div>
      {error && <p className="text-xs text-red-400">{error}</p>}
      <button type="button" className="btn btn-primary w-full" disabled={saving} onClick={save}>
        {saving ? "Saving…" : "Save Scion"}
      </button>
      {session.slot_id && (
        <p className="text-xs text-muted">Active: {rosterEntryLabel(name || "Scion")}</p>
      )}
    </div>
  );
}
