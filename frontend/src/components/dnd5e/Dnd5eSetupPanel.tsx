import { useEffect, useMemo, useState } from "react";
import { gmSoloApi } from "../../api/gmSolo";
import type { PlayHeader, SessionState } from "../../types";
import {
  spellLimitsFromClass,
  spellListField,
  spellPickLabel,
  spellPickLimit,
} from "../../lib/dnd5eCharacterCreation";
import { FormInput, FormSelect, FormTextarea, RosterSelect } from "../shared/FormFields";

interface OptionRow {
  id: string;
  label: string;
  [key: string]: unknown;
}

interface ClassOption extends OptionRow {
  hit_die?: number;
  primary_ability?: string;
  spellcasting?: string | null;
  spell_list?: string;
  skill_choices?: number;
  skill_options?: string[] | "any";
  subclasses?: string[];
  subclass_level?: number;
  cantrips_by_level?: number[];
  prepared_by_level?: number[];
  spells_known_by_level?: number[];
}

interface BackgroundOption extends OptionRow {
  ability_scores?: string[];
  feat?: string;
  skills?: string[];
  tool?: string;
}

interface SpeciesOption extends OptionRow {
  speed?: number;
  size_options?: string[];
  traits?: string[];
}

interface SkillOption {
  id: string;
  label: string;
  ability: string;
}

interface Props {
  entity: Record<string, unknown>;
  onSaved: (session: SessionState, header?: PlayHeader) => void;
  session: SessionState;
  roster?: { id: string; name: string }[];
  activeId?: string;
  onSwitchRoster?: () => void;
}

const STEPS = ["Basics", "Origin", "Abilities", "Skills & spells", "Review"] as const;

function str(v: unknown): string {
  return String(v ?? "").trim();
}

function list(v: unknown): string[] {
  return Array.isArray(v) ? v.map((x) => String(x)) : [];
}

export default function Dnd5eSetupPanel({
  entity,
  onSaved,
  session,
  roster = [],
  activeId = "",
  onSwitchRoster,
}: Props) {
  const api = gmSoloApi("dnd5e");
  const [local, setLocal] = useState(entity);
  const [step, setStep] = useState(0);
  const [options, setOptions] = useState<Record<string, unknown>>({});
  const [summary, setSummary] = useState<Record<string, unknown>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => setLocal(entity), [entity]);

  useEffect(() => {
    api.getCharacter().then((res) => {
      setOptions(res.options || {});
      setLocal(res.entity);
    });
    api.getCreationSummary().then(setSummary).catch(() => undefined);
  }, [activeId]);

  const classes = (options.classes || []) as ClassOption[];
  const species = (options.species || []) as SpeciesOption[];
  const backgrounds = (options.backgrounds || []) as BackgroundOption[];
  const skills = (options.skills || []) as SkillOption[];
  const alignments = list(options.alignments);
  const campaignSettings = (options.campaign_settings || []) as OptionRow[];
  const spellLists = (options.spell_lists || {}) as Record<string, Record<string, string[]>>;

  const selectedClass = classes.find((c) => c.id === str(local.class_name));
  const selectedBg = backgrounds.find((b) => b.id === str(local.background));
  const selectedSpecies = species.find((s) => s.id === str(local.species));

  const classSkillOptions = useMemo(() => {
    if (!selectedClass) return skills;
    const opts = selectedClass.skill_options;
    if (opts === "any") return skills;
    const ids = list(opts);
    return skills.filter((s) => ids.includes(s.id));
  }, [selectedClass, skills]);

  const spellListKey = str(selectedClass?.spell_list || selectedClass?.id);
  const classSpells = spellLists[spellListKey] || {};
  const cantripChoices = classSpells.cantrips || [];
  const level1Spells = classSpells["1"] || [];

  const spellMode = selectedClass?.spellcasting;
  const limits = useMemo(() => {
    if (selectedClass?.spellcasting) {
      return spellLimitsFromClass(selectedClass, Number(local.level || 1));
    }
    return (summary.spell_limits || { cantrips: 0, prepared: 0, known: 0 }) as Record<string, number>;
  }, [selectedClass, local.level, summary.spell_limits]);
  const cantripLimit = limits.cantrips ?? 0;
  const spellPickLimitCount = spellPickLimit(spellMode, {
    cantrips: cantripLimit,
    prepared: limits.prepared ?? 0,
    known: limits.known ?? 0,
  });
  const spellEntityKey = spellListField(spellMode);
  const isSpellcaster = Boolean(spellMode);

  const patch = (updates: Record<string, unknown>) => {
    setLocal((prev) => ({ ...prev, ...updates }));
  };

  const toggleList = (key: string, value: string, max: number) => {
    const current = list(local[key]);
    const v = value.toLowerCase();
    if (current.includes(v)) {
      patch({ [key]: current.filter((x) => x !== v) });
      return;
    }
    if (max > 0 && current.length >= max) return;
    patch({ [key]: [...current, v] });
  };

  const save = async (extra: Record<string, unknown> = {}) => {
    setSaving(true);
    setError(null);
    try {
      const payload = { ...local, ...extra, rebuild_stats: true };
      const res = await api.updateCharacter(payload);
      setLocal(res.entity);
      const sum = await api.getCreationSummary();
      setSummary(sum);
      onSaved({ ...session, entity: res.entity }, res.header);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const levelUp = async () => {
    setSaving(true);
    setError(null);
    try {
      await save();
      const res = await api.levelUp();
      setLocal(res.entity);
      setSummary(res.summary);
      onSaved({ ...session, entity: res.entity }, res.header);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Level up failed");
    } finally {
      setSaving(false);
    }
  };

  const applyStandardArray = () => {
    const table = (options.standard_array_by_class || {}) as Record<string, Record<string, number>>;
    const scores = table[str(local.class_name)];
    if (!scores) return;
    patch({ ability_scores: scores, ability_scores_set: true });
  };

  const scores = (local.ability_scores || {}) as Record<string, number>;
  const bgAbilities = list(selectedBg?.ability_scores);

  return (
    <div className="space-y-4 text-sm">
      {roster.length > 0 && (
        <RosterSelect
          label="Character"
          roster={roster}
          activeId={activeId}
          onChange={() => onSwitchRoster?.()}
        />
      )}

      <div className="flex flex-wrap gap-1">
        {STEPS.map((label, i) => (
          <button
            key={label}
            type="button"
            className={`btn text-xs py-1 px-2 ${step === i ? "btn-primary" : "btn-ghost"}`}
            onClick={() => setStep(i)}
          >
            {i + 1}. {label}
          </button>
        ))}
      </div>

      {step === 0 && (
        <div className="space-y-3">
          <label className="block">
            <span className="text-muted text-xs">Name</span>
            <FormInput
              className="w-full mt-1"
              value={str(local.name)}
              onChange={(e) => patch({ name: e.target.value })}
            />
          </label>
          <label className="block">
            <span className="text-muted text-xs">Class</span>
            <FormSelect
              className="w-full mt-1"
              value={str(local.class_name)}
              onChange={(e) =>
                patch({
                  class_name: e.target.value,
                  subclass: "",
                  class_skill_choices: [],
                  cantrips: [],
                  prepared_spells: [],
                  known_spells: [],
                })
              }
            >
              <option value="">Choose class…</option>
              {classes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.label} (d{c.hit_die})
                </option>
              ))}
            </FormSelect>
          </label>
          {selectedClass && (
            <p className="text-xs text-muted">
              Primary ability: {selectedClass.primary_ability?.toUpperCase()} · Saves:{" "}
              {list(selectedClass.saving_throws).join(", ").toUpperCase()}
              {selectedClass.spellcasting ? ` · Caster (${selectedClass.spellcasting})` : ""}
            </p>
          )}
          <div className="grid grid-cols-2 gap-3">
            <label className="block">
              <span className="text-muted text-xs">Level</span>
              <FormInput
                type="number"
                min={1}
                max={20}
                className="w-full mt-1"
                value={Number(local.level || 1)}
                onChange={(e) => patch({ level: Number(e.target.value) })}
              />
            </label>
            <label className="block">
              <span className="text-muted text-xs">XP</span>
              <FormInput
                type="number"
                min={0}
                className="w-full mt-1"
                value={Number(local.xp || 0)}
                onChange={(e) => patch({ xp: Number(e.target.value) })}
              />
            </label>
          </div>
          {Number(local.level) < 20 && (
            <button type="button" className="btn btn-ghost text-xs" disabled={saving} onClick={levelUp}>
              Level up (+1 level, roll HP)
            </button>
          )}
          <label className="block">
            <span className="text-muted text-xs">Campaign setting</span>
            <FormSelect
              className="w-full mt-1"
              value={str(local.campaign_setting) || "freeform"}
              onChange={(e) => patch({ campaign_setting: e.target.value })}
            >
              {campaignSettings.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.label}
                </option>
              ))}
              {campaignSettings.length === 0 && (
                <>
                  <option value="freeform">Freeform / homebrew</option>
                  <option value="faerun">Faerûn (Forgotten Realms)</option>
                </>
              )}
            </FormSelect>
          </label>
          {str(local.campaign_setting || "freeform") !== "faerun" && (
            <label className="block">
              <span className="text-muted text-xs">Campaign notes (optional)</span>
              <FormTextarea
                className="w-full mt-1 min-h-[4rem]"
                placeholder="e.g. homebrew kingdom, Eberron, custom dungeon crawl…"
                value={str(local.campaign_notes)}
                onChange={(e) => patch({ campaign_notes: e.target.value })}
              />
            </label>
          )}
          {selectedClass && Number(local.level) >= (selectedClass.subclass_level || 3) && (
            <label className="block">
              <span className="text-muted text-xs">Subclass</span>
              <FormSelect
                className="w-full mt-1"
                value={str(local.subclass)}
                onChange={(e) => patch({ subclass: e.target.value })}
              >
                <option value="">Choose subclass…</option>
                {list(selectedClass.subclasses).map((sc) => (
                  <option key={sc} value={sc}>
                    {sc}
                  </option>
                ))}
              </FormSelect>
            </label>
          )}
        </div>
      )}

      {step === 1 && (
        <div className="space-y-3">
          <label className="block">
            <span className="text-muted text-xs">Species</span>
            <FormSelect
              className="w-full mt-1"
              value={str(local.species)}
              onChange={(e) => patch({ species: e.target.value })}
            >
              <option value="">Choose species…</option>
              {species.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.label}
                </option>
              ))}
            </FormSelect>
          </label>
          {selectedSpecies && (
            <>
              {list(selectedSpecies.size_options).length > 1 && (
                <label className="block">
                  <span className="text-muted text-xs">Size</span>
                  <FormSelect
                    className="w-full mt-1"
                    value={str(local.size) || selectedSpecies.size_options?.[0]}
                    onChange={(e) => patch({ size: e.target.value })}
                  >
                    {list(selectedSpecies.size_options).map((sz) => (
                      <option key={sz} value={sz}>
                        {sz}
                      </option>
                    ))}
                  </FormSelect>
                </label>
              )}
              <ul className="text-xs text-muted list-disc pl-4 space-y-0.5">
                {list(selectedSpecies.traits).map((t) => (
                  <li key={t}>{t}</li>
                ))}
              </ul>
            </>
          )}
          {str(local.species) === "human" && (
            <label className="block">
              <span className="text-muted text-xs">Human — bonus skill (Skillful)</span>
              <FormSelect
                className="w-full mt-1"
                value={str(local.human_skill)}
                onChange={(e) => patch({ human_skill: e.target.value })}
              >
                <option value="">Choose skill…</option>
                {skills.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.label}
                  </option>
                ))}
              </FormSelect>
            </label>
          )}
          <label className="block">
            <span className="text-muted text-xs">Background</span>
            <FormSelect
              className="w-full mt-1"
              value={str(local.background)}
              onChange={(e) => patch({ background: e.target.value, background_asi_plus2: "", background_asi_plus1: "" })}
            >
              <option value="">Choose background…</option>
              {backgrounds.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.label}
                </option>
              ))}
            </FormSelect>
          </label>
          {selectedBg && (
            <p className="text-xs text-muted">
              Feat: {selectedBg.feat} · Skills: {list(selectedBg.skills).join(", ")} · Tool:{" "}
              {selectedBg.tool}
            </p>
          )}
          <label className="block">
            <span className="text-muted text-xs">Alignment</span>
            <FormSelect
              className="w-full mt-1"
              value={str(local.alignment)}
              onChange={(e) => patch({ alignment: e.target.value })}
            >
              <option value="">Choose alignment…</option>
              {alignments.map((a) => (
                <option key={a} value={a}>
                  {a.replace(/_/g, " ")}
                </option>
              ))}
            </FormSelect>
          </label>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <button type="button" className="btn btn-ghost text-xs" onClick={applyStandardArray} disabled={!selectedClass}>
              Use PHB standard array for class
            </button>
          </div>
          {selectedBg && (
            <div className="space-y-2 border border-border rounded p-2">
              <div className="text-xs font-medium">Background ability increases</div>
              <label className="flex items-center gap-2 text-xs">
                <FormInput
                  type="checkbox"
                  checked={Boolean(local.background_asi_all_three)}
                  onChange={(e) => patch({ background_asi_all_three: e.target.checked })}
                />
                +1 to all three background abilities ({bgAbilities.join(", ").toUpperCase()})
              </label>
              {!local.background_asi_all_three && (
                <div className="grid grid-cols-2 gap-2">
                  <label className="block text-xs">
                    +2 to
                    <FormSelect
                      className="w-full mt-1"
                      value={str(local.background_asi_plus2)}
                      onChange={(e) => patch({ background_asi_plus2: e.target.value })}
                    >
                      <option value="">Auto</option>
                      {bgAbilities.map((a) => (
                        <option key={a} value={a}>
                          {a.toUpperCase()}
                        </option>
                      ))}
                    </FormSelect>
                  </label>
                  <label className="block text-xs">
                    +1 to
                    <FormSelect
                      className="w-full mt-1"
                      value={str(local.background_asi_plus1)}
                      onChange={(e) => patch({ background_asi_plus1: e.target.value })}
                    >
                      <option value="">Auto</option>
                      {bgAbilities.map((a) => (
                        <option key={a} value={a}>
                          {a.toUpperCase()}
                        </option>
                      ))}
                    </FormSelect>
                  </label>
                </div>
              )}
            </div>
          )}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {["str", "dex", "con", "int", "wis", "cha"].map((ab) => (
              <label key={ab} className="block">
                <span className="text-muted text-xs">{ab.toUpperCase()}</span>
                <FormInput
                  type="number"
                  min={1}
                  max={30}
                  className="w-full mt-1"
                  value={Number(scores[ab] ?? 10)}
                  onChange={(e) =>
                    patch({
                      ability_scores: { ...scores, [ab]: Number(e.target.value) },
                      ability_scores_set: true,
                    })
                  }
                />
              </label>
            ))}
          </div>
          <div className="grid grid-cols-3 gap-2">
            <label className="block">
              <span className="text-muted text-xs">HP</span>
              <FormInput
                type="number"
                min={0}
                className="w-full mt-1"
                value={Number(local.hp || 0)}
                onChange={(e) => patch({ hp: Number(e.target.value) })}
              />
            </label>
            <label className="block">
              <span className="text-muted text-xs">Max HP</span>
              <FormInput
                type="number"
                min={0}
                className="w-full mt-1"
                value={Number(local.max_hp || 0)}
                onChange={(e) => patch({ max_hp: Number(e.target.value) })}
              />
            </label>
            <label className="block">
              <span className="text-muted text-xs">AC</span>
              <FormInput
                type="number"
                min={1}
                className="w-full mt-1"
                value={Number(local.ac || 10)}
                onChange={(e) => patch({ ac: Number(e.target.value) })}
              />
            </label>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <label className="block">
              <span className="text-muted text-xs">Hit Dice spent</span>
              <FormInput
                type="number"
                min={0}
                max={Number(local.level || 1)}
                className="w-full mt-1"
                value={Number(local.hit_dice_spent || 0)}
                onChange={(e) => patch({ hit_dice_spent: Number(e.target.value) })}
              />
            </label>
            <div className="text-xs text-muted pt-6">
              Available: {Math.max(0, Number(local.hit_dice_max || local.level || 1) - Number(local.hit_dice_spent || 0))}
              d{Number(local.hit_die || 8)}
            </div>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="space-y-4">
          {selectedClass && (selectedClass.skill_choices || 0) > 0 && (
            <div>
              <div className="label mb-1">
                Class skills (pick {selectedClass.skill_choices})
              </div>
              <div className="flex flex-wrap gap-1">
                {classSkillOptions.map((s) => {
                  const chosen = list(local.class_skill_choices);
                  const on = chosen.includes(s.id);
                  return (
                    <button
                      key={s.id}
                      type="button"
                      className={`btn text-xs py-1 px-2 ${on ? "btn-primary" : "btn-ghost"}`}
                      onClick={() =>
                        toggleList("class_skill_choices", s.id, selectedClass.skill_choices || 0)
                      }
                    >
                      {s.label}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {cantripLimit > 0 && (
            <div>
              <div className="label mb-1">
                Cantrips ({list(local.cantrips).length}/{cantripLimit})
              </div>
              <div className="max-h-40 overflow-y-auto flex flex-wrap gap-1">
                {cantripChoices.map((sp) => {
                  const on = list(local.cantrips).includes(sp.toLowerCase());
                  return (
                    <button
                      key={sp}
                      type="button"
                      className={`btn text-xs py-1 px-2 ${on ? "btn-primary" : "btn-ghost"}`}
                      onClick={() => toggleList("cantrips", sp, cantripLimit)}
                    >
                      {sp}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {spellPickLimitCount > 0 && level1Spells.length > 0 && (
            <div>
              <div className="label mb-1">
                {spellPickLabel(spellMode)} (
                {list(local[spellEntityKey]).length}/{spellPickLimitCount})
              </div>
              <div className="max-h-48 overflow-y-auto flex flex-wrap gap-1">
                {level1Spells.map((sp) => {
                  const on = list(local[spellEntityKey]).includes(sp.toLowerCase());
                  return (
                    <button
                      key={sp}
                      type="button"
                      className={`btn text-xs py-1 px-2 ${on ? "btn-primary" : "btn-ghost"}`}
                      onClick={() => toggleList(spellEntityKey, sp, spellPickLimitCount)}
                    >
                      {sp}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {!isSpellcaster && selectedClass && (
            <p className="text-xs text-muted">This class has no spellcasting.</p>
          )}

          {isSpellcaster && cantripLimit === 0 && spellPickLimitCount === 0 && (
            <p className="text-xs text-muted">No spell picks at this level.</p>
          )}

          {isSpellcaster && cantripLimit > 0 && cantripChoices.length === 0 && (
            <p className="text-xs text-accent">Spell list not loaded — try saving the character and reopening Settings.</p>
          )}

          {isSpellcaster && spellPickLimitCount > 0 && level1Spells.length === 0 && (
            <p className="text-xs text-accent">Level 1 spell list missing for this class.</p>
          )}
        </div>
      )}

      {step === 4 && (
        <div className="space-y-2 text-xs">
          <div className="font-medium">{str(local.name) || "Unnamed hero"}</div>
          <div className="text-muted whitespace-pre-wrap">
            {[
              selectedSpecies?.label,
              selectedClass?.label,
              local.subclass,
              `Level ${local.level}`,
              selectedBg?.label,
              `HP ${local.hp}/${local.max_hp} · AC ${local.ac}`,
              `Campaign: ${
                campaignSettings.find((c) => c.id === str(local.campaign_setting || "freeform"))?.label ||
                (str(local.campaign_setting) === "faerun" ? "Faerûn" : "Freeform")
              }${local.campaign_notes ? ` — ${local.campaign_notes}` : ""}`,
              `Proficiency +${summary.proficiency_bonus ?? "?"}`,
              `Origin feat: ${local.origin_feat || selectedBg?.feat || "—"}`,
              `Skills: ${list(local.skill_proficiencies).join(", ") || "—"}`,
              `Cantrips: ${list(local.cantrips).join(", ") || "—"}`,
              `Spells: ${list(local.prepared_spells).concat(list(local.known_spells)).join(", ") || "—"}`,
              `Slots: ${Object.entries((local.spell_slots as Record<string, number>) || {})
                .map(([k, v]) => `L${k}×${v}`)
                .join(", ") || "—"}`,
            ]
              .filter(Boolean)
              .join("\n")}
          </div>
        </div>
      )}

      {error && <p className="text-xs text-accent">{error}</p>}

      <div className="flex gap-2 pt-2">
        {step > 0 && (
          <button type="button" className="btn btn-ghost" onClick={() => setStep(step - 1)}>
            Back
          </button>
        )}
        {step < STEPS.length - 1 ? (
          <button type="button" className="btn btn-primary" onClick={() => setStep(step + 1)}>
            Next
          </button>
        ) : null}
        <button type="button" className="btn btn-primary ml-auto" disabled={saving} onClick={() => save()}>
          {saving ? "Saving…" : "Save character"}
        </button>
      </div>
    </div>
  );
}
