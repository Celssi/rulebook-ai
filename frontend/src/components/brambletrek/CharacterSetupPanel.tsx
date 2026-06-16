import { useEffect, useState } from "react";
import { Loader2, Shuffle } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { api, type ResourceDraft } from "../../api/client";
import { applyLegacyStatSwap, applyLegacyToBases, hasResourceBases } from "../../lib/legacyStats";
import type { CharacterHeader } from "../../types";
import { FormSelect, RosterSelect, SelectField } from "../shared/FormFields";

interface TableOption {
  id: string;
  label: string;
}

interface LegacyOption {
  id: string;
  label: string;
  boost?: string;
  flaw?: string;
  health_delta?: number;
  morale_delta?: number;
  supplies_delta?: number;
  abilities?: { id: string; label: string; description: string; tags: string[] }[];
}

interface CharacterOptions {
  reasons: TableOption[];
  backgrounds: TableOption[];
  trinkets: TableOption[];
  card_bands: TableOption[];
  legacies: LegacyOption[];
  adventures: TableOption[];
}

interface Props {
  entity: Record<string, unknown>;
  onChange: (entity: Record<string, unknown>) => void;
  onSaved?: (entity: Record<string, unknown>, header: CharacterHeader) => void;
  roster?: { id: string; name: string }[];
  activeId?: string;
  onSwitchRoster?: () => void;
}

function CardDrawnDisplay({
  bandId,
  card,
  cardBands,
}: {
  bandId: string;
  card?: string;
  cardBands: TableOption[];
}) {
  if (card) {
    return (
      <div className="mt-1.5 text-[11px] text-muted">
        Card drawn: <span className="text-gray-300">{card}</span>
      </div>
    );
  }
  if (!bandId) return null;
  const bandLabel = cardBands.find((b) => b.id === bandId)?.label;
  if (!bandLabel) return null;
  return (
    <div className="mt-1.5 text-[11px] text-muted">
      Card band: <span className="text-gray-300">{bandLabel}</span>
    </div>
  );
}

function TableDrawField({
  label,
  value,
  options,
  bandId,
  card,
  cardBands,
  drawing,
  onChange,
  onDraw,
}: {
  label: string;
  value: string;
  options: TableOption[];
  bandId: string;
  card?: string;
  cardBands: TableOption[];
  drawing: boolean;
  onChange: (id: string) => void;
  onDraw: () => void;
}) {
  return (
    <div>
      <div className="flex items-center justify-between gap-2 mb-1">
        <div className="label">{label}</div>
        <button
          type="button"
          className="btn-ghost text-[11px] px-2 py-1 border border-border rounded-md inline-flex items-center gap-1 text-muted hover:text-accent"
          disabled={drawing}
          onClick={onDraw}
        >
          {drawing ? (
            <Loader2 className="w-3 h-3 animate-spin" />
          ) : (
            <Shuffle className="w-3 h-3" />
          )}
          Draw
        </button>
      </div>
      <FormSelect value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map((o) => (
          <option key={o.id || "empty"} value={o.id}>
            {o.label}
          </option>
        ))}
      </FormSelect>
      <CardDrawnDisplay bandId={bandId} card={card} cardBands={cardBands} />
    </div>
  );
}

export default function CharacterSetupPanel({
  entity,
  onChange,
  onSaved,
  roster,
  activeId,
  onSwitchRoster,
}: Props) {
  const [options, setOptions] = useState<CharacterOptions | null>(null);
  const [resourceDraft, setResourceDraft] = useState<ResourceDraft | null>(null);
  const [reasonPreview, setReasonPreview] = useState("");
  const [saving, setSaving] = useState(false);
  const [drawing, setDrawing] = useState<string | null>(null);
  const [resourceBusy, setResourceBusy] = useState<string | null>(null);
  const [switching, setSwitching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getCharacter().then((res) => {
      setOptions(res.options as unknown as CharacterOptions);
      setResourceDraft(res.resource_draft);
    });
  }, [activeId]);

  const reasonBand = String(entity.reason_band || "");
  useEffect(() => {
    if (!reasonBand) {
      setReasonPreview("");
      return;
    }
    api.reasonEndingPreview(reasonBand).then((r) => setReasonPreview(r.preview));
  }, [reasonBand]);

  const patch = (key: string, value: unknown) => onChange({ ...entity, [key]: value });

  const drawTable = async (table: "reason" | "background" | "trinket") => {
    setDrawing(table);
    setError(null);
    try {
      const res = await api.drawCharacterTable(table);
      onChange({
        ...entity,
        [res.band_field]: res.band_id,
        [res.card_field]: res.card,
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Draw failed");
    } finally {
      setDrawing(null);
    }
  };

  const changeLegacy = (id: string) => {
    const oldLegacy = options?.legacies.find((l) => l.id === String(entity.legacy || ""));
    const newLegacy = options?.legacies.find((l) => l.id === id);
    let stats: { health: number; morale: number; supplies: number };
    if (hasResourceBases(entity)) {
      stats = applyLegacyToBases(
        {
          health: Number(entity.resource_base_health ?? 0),
          morale: Number(entity.resource_base_morale ?? 0),
          supplies: Number(entity.resource_base_supplies ?? 0),
        },
        newLegacy
      );
    } else {
      stats = applyLegacyStatSwap(
        {
          health: Number(entity.health ?? 10),
          morale: Number(entity.morale ?? 10),
          supplies: Number(entity.supplies ?? 10),
        },
        oldLegacy,
        newLegacy
      );
    }
    onChange({
      ...entity,
      legacy: id,
      ...stats,
      legacy_abilities_used: {},
    });
    if (resourceDraft?.base_stats) {
      setResourceDraft({
        ...resourceDraft,
        final_stats: applyLegacyToBases(resourceDraft.base_stats, newLegacy),
      });
    }
  };

  const rollLegacy = async () => {
    setDrawing("legacy");
    setError(null);
    try {
      const res = await api.rollCharacterLegacy();
      changeLegacy(res.legacy_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Legacy roll failed");
    } finally {
      setDrawing(null);
    }
  };

  const drawResources = async () => {
    setResourceBusy("draw");
    setError(null);
    try {
      const res = await api.drawCharacterResources();
      setResourceDraft(res.resource_draft);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Resource draw failed");
    } finally {
      setResourceBusy(null);
    }
  };

  const drawResourceBonus = async (stat: "health" | "morale" | "supplies") => {
    setResourceBusy(stat);
    setError(null);
    try {
      const res = await api.drawCharacterResourceBonus(stat);
      setResourceDraft(res.resource_draft);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Bonus draw failed");
    } finally {
      setResourceBusy(null);
    }
  };

  const applyResources = async () => {
    setResourceBusy("apply");
    setError(null);
    try {
      const res = await api.applyCharacterResources();
      setResourceDraft(null);
      onChange(res.entity);
      onSaved?.(res.entity, res.header);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Apply resources failed");
    } finally {
      setResourceBusy(null);
    }
  };

  const selectedLegacy = options?.legacies.find((l) => l.id === String(entity.legacy || ""));

  const switchRoster = async (id: string) => {
    if (!id || id === activeId) return;
    setSwitching(true);
    setError(null);
    try {
      await api.switchGnawborn(id);
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
      const res = await api.updateCharacter(entity);
      onChange(res.entity);
      onSaved?.(res.entity, res.header);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  if (!options) {
    return <p className="text-muted text-sm">Loading character tables…</p>;
  }

  return (
    <div className="space-y-4">
      <p className="text-muted text-xs">
        Edit the active Gnawborn — name, creation bands, legacy, resources, and adventure.
        Use <strong>Draw</strong> to pull table cards from the virtual deck.
      </p>

      {roster && roster.length > 0 && (
        <RosterSelect
          label="Active Gnawborn"
          roster={roster}
          activeId={activeId || ""}
          disabled={switching}
          onChange={switchRoster}
        />
      )}

      <div>
        <div className="label mb-1">Name</div>
        <input
          className="input"
          value={String(entity.name || "")}
          onChange={(e) => patch("name", e.target.value)}
        />
      </div>

      <TableDrawField
        label="Reason for adventure"
        value={reasonBand}
        bandId={reasonBand}
        card={String(entity.reason_card || "") || undefined}
        cardBands={options.card_bands || []}
        options={options.reasons}
        drawing={drawing === "reason"}
        onChange={(id) => onChange({ ...entity, reason_band: id, reason_card: "" })}
        onDraw={() => drawTable("reason")}
      />

      <TableDrawField
        label="Background"
        value={String(entity.background_band || "")}
        bandId={String(entity.background_band || "")}
        card={String(entity.background_card || "") || undefined}
        cardBands={options.card_bands || []}
        options={options.backgrounds}
        drawing={drawing === "background"}
        onChange={(id) => onChange({ ...entity, background_band: id, background_card: "" })}
        onDraw={() => drawTable("background")}
      />

      <TableDrawField
        label="Trinket"
        value={String(entity.trinket_band || "")}
        bandId={String(entity.trinket_band || "")}
        card={String(entity.trinket_card || "") || undefined}
        cardBands={options.card_bands || []}
        options={options.trinkets}
        drawing={drawing === "trinket"}
        onChange={(id) => onChange({ ...entity, trinket_band: id, trinket_card: "" })}
        onDraw={() => drawTable("trinket")}
      />

      <SelectField
        label="Legacy"
        value={String(entity.legacy || "")}
        options={[{ id: "", label: "— Not set —" }, ...options.legacies]}
        onChange={changeLegacy}
      />
      <div className="flex items-center gap-2">
        <button
          type="button"
          className="btn-ghost text-[11px] px-2 py-1 border border-border rounded-md inline-flex items-center gap-1 text-muted hover:text-accent"
          disabled={drawing === "legacy"}
          onClick={rollLegacy}
        >
          {drawing === "legacy" ? (
            <Loader2 className="w-3 h-3 animate-spin" />
          ) : (
            <Shuffle className="w-3 h-3" />
          )}
          Roll d6
        </button>
        <span className="text-[11px] text-muted">Rulebook order: resources from cards, then legacy modifiers.</span>
      </div>
      {selectedLegacy?.boost && (
        <p className="text-xs">
          <span className="text-moss">{selectedLegacy.boost}</span>
          <span className="text-muted"> · </span>
          <span className="text-red-400">{selectedLegacy.flaw}</span>
        </p>
      )}

      {selectedLegacy && (selectedLegacy.abilities?.length ?? 0) > 0 && (
        <div className="rounded-lg border border-border p-3 space-y-2">
          <div className="section-title">Daily abilities</div>
          {selectedLegacy.abilities!.map((ab) => (
            <div key={ab.id} className="text-xs">
              <span className="font-medium">{ab.label}</span>
              {ab.tags?.map((tag) => (
                <span
                  key={tag}
                  className={`ml-1.5 text-[10px] px-1 rounded ${
                    tag === "combat" ? "bg-red-900/40 text-red-300" : "bg-moss-muted text-moss"
                  }`}
                >
                  {tag}
                </span>
              ))}
              <div className="text-muted mt-0.5">{ab.description}</div>
            </div>
          ))}
        </div>
      )}

      <div className="rounded-lg border border-border p-3 space-y-3">
        <div className="flex items-center justify-between gap-2">
          <div>
            <div className="section-title">Resources (max 20 each)</div>
            <p className="text-[11px] text-muted mt-0.5">
              Draw six cards (1–2 Health, 3–4 Morale, 5–6 Supplies). Ace = 11, J/Q/K = 10. Pair total ≤ 6
              may take one bonus card.
            </p>
          </div>
          <button
            type="button"
            className="btn-ghost text-[11px] px-2 py-1 border border-border rounded-md inline-flex items-center gap-1 text-muted hover:text-accent shrink-0"
            disabled={Boolean(resourceBusy)}
            onClick={drawResources}
          >
            {resourceBusy === "draw" ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <Shuffle className="w-3 h-3" />
            )}
            Draw 6
          </button>
        </div>

        {resourceDraft && (
          <div className="space-y-2">
            {resourceDraft.stats.map((row) => (
              <div key={row.stat} className="text-xs rounded-md bg-surface/50 p-2">
                <div className="flex items-center justify-between gap-2">
                  <span className="capitalize font-medium">{row.stat}</span>
                  <span className="text-muted">
                    base {row.base}
                    {resourceDraft.final_stats && (
                      <span className="text-gray-300">
                        {" "}
                        → {resourceDraft.final_stats[row.stat]}
                      </span>
                    )}
                  </span>
                </div>
                <div className="text-muted mt-1">
                  {row.cards.map((card, i) => (
                    <span key={`${card}-${i}`}>
                      {i > 0 ? ", " : ""}
                      {card} ({row.card_values[i] ?? "?"})
                    </span>
                  ))}
                </div>
                {row.needs_bonus && (
                  <button
                    type="button"
                    className="mt-1.5 text-[11px] text-accent hover:underline"
                    disabled={resourceBusy === row.stat}
                    onClick={() => drawResourceBonus(row.stat)}
                  >
                    {resourceBusy === row.stat ? "Drawing bonus…" : "Low roll — draw bonus card"}
                  </button>
                )}
              </div>
            ))}
            <button
              type="button"
              className="btn btn-secondary text-xs w-full"
              disabled={Boolean(resourceBusy)}
              onClick={applyResources}
            >
              {resourceBusy === "apply" ? "Applying…" : "Apply resources to character"}
            </button>
          </div>
        )}

        {hasResourceBases(entity) && !resourceDraft && (
          <div className="text-[11px] text-muted space-y-1">
            {(["health", "morale", "supplies"] as const).map((k) => {
              const cards = (entity.resource_cards as Record<string, string[]> | undefined)?.[k] || [];
              if (!cards.length) return null;
              return (
                <div key={k}>
                  <span className="capitalize">{k}</span>: {cards.join(", ")} (base{" "}
                  {Number(entity[`resource_base_${k}`] ?? 0)})
                </div>
              );
            })}
          </div>
        )}

        <div className="grid grid-cols-3 gap-2">
          {(["health", "morale", "supplies"] as const).map((k) => (
            <div key={k}>
              <div className="text-xs text-muted capitalize mb-1">{k}</div>
              <input
                type="number"
                min={0}
                max={20}
                className="input"
                value={Number(entity[k] ?? 10)}
                onChange={(e) => patch(k, Number(e.target.value))}
              />
            </div>
          ))}
        </div>
      </div>

      <SelectField
        label="Active adventure"
        value={String(entity.active_adventure || "")}
        options={options.adventures}
        onChange={(id) => patch("active_adventure", id)}
      />

      {reasonBand && reasonPreview && (
        <details className="rounded-lg border border-border p-3">
          <summary className="cursor-pointer text-xs text-muted">Reason ending preview (p. 36)</summary>
          <div className="prose-chat mt-2 text-xs">
            <ReactMarkdown>{reasonPreview}</ReactMarkdown>
          </div>
        </details>
      )}

      <textarea
        className="input min-h-[80px]"
        placeholder="Journal notes"
        value={String(entity.notes || "")}
        onChange={(e) => patch("notes", e.target.value)}
      />

      {error && <p className="text-red-400 text-xs">{error}</p>}

      <button type="button" className="btn btn-primary" disabled={saving || switching} onClick={save}>
        {saving ? "Saving…" : "Save character"}
      </button>
    </div>
  );
}
