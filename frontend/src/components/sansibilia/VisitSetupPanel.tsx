import { useEffect, useState } from "react";
import { Loader2, Shuffle } from "lucide-react";
import { api } from "../../api/client";
import { rosterEntryLabel } from "../../lib/rosterLabel";
import type { VisitHeader } from "../../types";

interface TableOption {
  id: string;
  label: string;
}

interface VisitOptions {
  ending_modes: TableOption[];
  character_traits: TableOption[];
  character_roles: TableOption[];
}

interface Props {
  entity: Record<string, unknown>;
  onChange: (entity: Record<string, unknown>) => void;
  onSaved?: (entity: Record<string, unknown>, header: VisitHeader) => void;
  roster?: { id: string; name: string }[];
  activeId?: string;
  onSwitchRoster?: () => void;
}

function rankLabel(options: TableOption[], rankId: string): string {
  return options.find((o) => o.id === rankId)?.label || "";
}

function combinedArchetype(
  traitRank: string,
  roleRank: string,
  traits: TableOption[],
  roles: TableOption[],
): string {
  const trait = rankLabel(traits, traitRank);
  const role = rankLabel(roles, roleRank);
  if (!trait || !role) return "";
  return `${trait} ${role.toLowerCase()}`;
}

export default function VisitSetupPanel({
  entity,
  onChange,
  onSaved,
  roster,
  activeId,
  onSwitchRoster,
}: Props) {
  const [options, setOptions] = useState<VisitOptions | null>(null);
  const [saving, setSaving] = useState(false);
  const [drawing, setDrawing] = useState(false);
  const [switching, setSwitching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getVisit().then((res) => setOptions(res.options as unknown as VisitOptions));
  }, []);

  const traits = options?.character_traits || [];
  const roles = options?.character_roles || [];
  const characterCards = (entity.character_cards as string[] | undefined) || [];
  const traitRank = String(entity.character_trait_rank || "");
  const roleRank = String(entity.character_role_rank || "");

  const switchRoster = async (id: string) => {
    if (!id || id === activeId) return;
    setSwitching(true);
    setError(null);
    try {
      await api.switchVisit(id);
      onSwitchRoster?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Switch failed");
    } finally {
      setSwitching(false);
    }
  };

  const drawCharacter = async () => {
    setDrawing(true);
    setError(null);
    try {
      const res = await api.drawVisitCharacter();
      onChange(res.entity);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Draw failed");
    } finally {
      setDrawing(false);
    }
  };

  const changeTrait = (rankId: string) => {
    const archetype = combinedArchetype(rankId, roleRank, traits, roles);
    onChange({
      ...entity,
      character_trait_rank: rankId,
      character_rank: "",
      archetype: archetype || entity.archetype,
      character_cards: rankId || roleRank ? [] : entity.character_cards,
    });
  };

  const changeRole = (rankId: string) => {
    const archetype = combinedArchetype(traitRank, rankId, traits, roles);
    onChange({
      ...entity,
      character_role_rank: rankId,
      character_rank: "",
      archetype: archetype || entity.archetype,
      character_cards: traitRank || rankId ? [] : entity.character_cards,
    });
  };

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      const res = await api.updateVisit(entity);
      onSaved?.(res.entity, res.header);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const archetypeDisplay =
    String(entity.archetype || "").trim() ||
    combinedArchetype(traitRank, roleRank, traits, roles);

  return (
    <div className="space-y-4">
      <p className="text-muted text-xs">
        Edit your active visit — name, character (draw 2 cards: trait + role, or pick from the table), ending mode.
      </p>

      {error && <p className="text-xs text-red-400">{error}</p>}

      {roster && roster.length > 0 && (
        <div>
          <div className="label mb-1">Active visit</div>
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
        </div>
      )}

      <div>
        <div className="label mb-1">Name</div>
        <input
          className="input"
          value={String(entity.name || "")}
          onChange={(e) => onChange({ ...entity, name: e.target.value })}
        />
      </div>

      <div>
        <div className="flex items-center justify-between gap-2 mb-1">
          <div className="label">Character</div>
          <button
            type="button"
            className="btn-ghost text-[11px] px-2 py-1 border border-border rounded-md inline-flex items-center gap-1 text-muted hover:text-accent"
            disabled={drawing}
            onClick={drawCharacter}
          >
            {drawing ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <Shuffle className="w-3 h-3" />
            )}
            Draw (2 cards)
          </button>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <div className="text-[10px] text-muted mb-0.5">Trait (1st card)</div>
            <select className="select" value={traitRank} onChange={(e) => changeTrait(e.target.value)}>
              <option value="">—</option>
              {traits.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <div className="text-[10px] text-muted mb-0.5">Role (2nd card)</div>
            <select className="select" value={roleRank} onChange={(e) => changeRole(e.target.value)}>
              <option value="">—</option>
              {roles.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
        </div>
        {archetypeDisplay && (
          <p className="mt-1.5 text-[11px] text-gray-300 italic">{archetypeDisplay}</p>
        )}
        {characterCards.length > 0 && (
          <div className="mt-1 text-[11px] text-muted">
            Cards drawn:{" "}
            <span className="text-gray-300">
              {characterCards[0]} (trait)
              {characterCards[1] ? ` · ${characterCards[1]} (role)` : ""}
            </span>
          </div>
        )}
      </div>

      {options?.ending_modes && (
        <div>
          <div className="label mb-1">Ending mode</div>
          <select
            className="select"
            value={String(entity.ending_mode || "four_changes")}
            onChange={(e) => onChange({ ...entity, ending_mode: e.target.value })}
          >
            {options.ending_modes.map((m) => (
              <option key={m.id} value={m.id}>
                {m.label}
              </option>
            ))}
          </select>
        </div>
      )}

      {String(entity.ending_mode) === "score_90" && (
        <div>
          <div className="label mb-1">Ace value (1 or 11)</div>
          <select
            className="select"
            value={String(entity.ace_value ?? 11)}
            onChange={(e) => onChange({ ...entity, ace_value: Number(e.target.value) })}
          >
            <option value="11">11 (faster end)</option>
            <option value="1">1 (slower end)</option>
          </select>
        </div>
      )}

      <button type="button" className="btn btn-primary w-full" disabled={saving} onClick={save}>
        {saving ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin inline mr-2" />
            Saving…
          </>
        ) : (
          "Save visit"
        )}
      </button>
    </div>
  );
}
