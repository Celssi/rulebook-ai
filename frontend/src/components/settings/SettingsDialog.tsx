import { useEffect, useState } from "react";
import { BookOpen, Database, Play, User } from "lucide-react";
import { api } from "../../api/client";
import CharacterSetupPanel from "../brambletrek/CharacterSetupPanel";
import Bt2CharacterSetupPanel from "../brambletrek_2/CharacterSetupPanel";
import VisitSetupPanel from "../sansibilia/VisitSetupPanel";
import WatchSetupPanel from "../lighthouse/WatchSetupPanel";
import CottageSetupPanel from "../apothecaria/CottageSetupPanel";
import InvestigationSetupPanel from "../whispers/InvestigationSetupPanel";
import AdventurerSetupPanel from "../colostle/AdventurerSetupPanel";
import ScionSetupPanel from "../ashes/ScionSetupPanel";
import GmSoloSetupPanel from "../gm_solo/GmSoloSetupPanel";
import OutgunnedSetupPanel from "../outgunned/OutgunnedSetupPanel";
import CoriolisSetupPanel from "../coriolis/CoriolisSetupPanel";
import TorSetupPanel from "../tor/TorSetupPanel";
import Dnd5eSetupPanel from "../dnd5e/Dnd5eSetupPanel";
import MlpSetupPanel from "../mlp/MlpSetupPanel";
import { isGmSoloGameId } from "../../games/gmSoloGames";
import type { PlayHeader, SessionState } from "../../types";
import { ASHES_PROMPT_SETS } from "../ashes/promptSets";
import AppDialog from "../shared/AppDialog";
import { FormSelect } from "../shared/FormFields";

type Tab = "play" | "rag" | "character" | "index";

interface Props {
  open: boolean;
  session: SessionState;
  roster?: { id: string; name: string }[];
  onClose: () => void;
  onSaved: (session: SessionState, header?: PlayHeader) => void;
  onRosterSwitch?: () => void;
}

const TABS: { id: Tab; label: string; icon: typeof Play }[] = [
  { id: "play", label: "Play", icon: Play },
  { id: "rag", label: "RAG", icon: BookOpen },
  { id: "character", label: "Character", icon: User },
  { id: "index", label: "Index", icon: Database },
];

export default function SettingsDialog({
  open,
  session,
  roster,
  onClose,
  onSaved,
  onRosterSwitch,
}: Props) {
  const [tab, setTab] = useState<Tab>("play");
  const [meta, setMeta] = useState<Record<string, unknown> | null>(null);
  const [games, setGames] = useState<{ id: string; label: string }[]>([]);
  const [entity, setEntity] = useState<Record<string, unknown>>(session.entity || {});
  const [indexStatus, setIndexStatus] = useState<Record<string, unknown> | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) return;
    Promise.all([api.getSettingsMeta(), api.getGames(), api.indexStatus()]).then(
      ([m, g, idx]) => {
        setMeta(m);
        setGames(g.games);
        setIndexStatus(idx);
      }
    );
    if (session.entity) setEntity(session.entity);
  }, [open, session.entity]);

  const providers = (meta?.chat_providers as { id: string; label: string }[]) || [];
  const profiles = (meta?.retrieval_profiles as string[]) || [];

  const handleCharacterSaved = (
    updated: Record<string, unknown>,
    header: PlayHeader
  ) => {
    setEntity(updated);
    onSaved({ ...session, entity: updated }, header);
    onClose();
  };

  const saveSession = async (patch: Record<string, unknown>) => {
    setSaving(true);
    try {
      const res = await api.updateSession(patch);
      onSaved(res);
    } finally {
      setSaving(false);
    }
  };

  return (
    <AppDialog open={open} title="Settings" onClose={onClose} size="lg">
        <div className="flex flex-1 min-h-0 overflow-hidden">
          <nav className="hidden sm:flex sm:flex-col w-36 shrink-0 border-r border-border p-2 space-y-0.5">
            {TABS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                type="button"
                className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                  tab === id
                    ? "bg-accent-muted text-accent font-medium"
                    : "text-muted hover:bg-elevated hover:text-gray-200"
                }`}
                onClick={() => setTab(id)}
              >
                <Icon className="w-4 h-4 shrink-0" />
                {label}
              </button>
            ))}
          </nav>

          <div className="flex-1 flex flex-col min-h-0 min-w-0">
            <div className="sm:hidden flex border-b border-border shrink-0 overflow-x-auto">
              {TABS.map(({ id, label }) => (
                <button
                  key={id}
                  type="button"
                  className={
                    tab === id ? "tab-btn-active whitespace-nowrap" : "tab-btn whitespace-nowrap"
                  }
                  onClick={() => setTab(id)}
                >
                  {label}
                </button>
              ))}
            </div>

            <div className="flex-1 overflow-y-auto p-5 text-sm min-h-0">
            {tab === "play" && (
              <div className="space-y-4">
                <section>
                  <div className="label mb-2">Game</div>
                  <FormSelect
                    value={session.selected_game_id}
                    onChange={(e) => saveSession({ selected_game_id: e.target.value })}
                  >
                    {games.map((g) => (
                      <option key={g.id} value={g.id}>
                        {g.label}
                      </option>
                    ))}
                  </FormSelect>
                </section>

                {session.has_character_sheet && session.settings && (
                  <section className="grid sm:grid-cols-2 gap-4 pt-4 border-t border-border">
                    {(session.selected_game_id === "brambletrek" ||
                      session.selected_game_id === "brambletrek_2") && (
                      <div>
                        <div className="label mb-2">Story mode</div>
                        <FormSelect
                          value={session.settings.story_mode || "player"}
                          onChange={(e) =>
                            saveSession({
                              settings: { ...session.settings, story_mode: e.target.value },
                            })
                          }
                        >
                          <option value="player">Player-led</option>
                          <option value="ai_narrator">AI narrator</option>
                        </FormSelect>
                      </div>
                    )}
                    {session.selected_game_id === "apothecaria" && (
                      <div>
                        <div className="label mb-2">Story mode</div>
                        <FormSelect
                          value={session.settings.story_mode || "player"}
                          onChange={(e) =>
                            saveSession({
                              settings: { ...session.settings, story_mode: e.target.value },
                            })
                          }
                        >
                          <option value="player">Player-led journal</option>
                          <option value="ai_narrator">AI narrator</option>
                        </FormSelect>
                      </div>
                    )}
                    {session.selected_game_id === "lighthouse" && (
                      <div>
                        <div className="label mb-2">Story mode</div>
                        <FormSelect
                          value={session.settings.story_mode || "player"}
                          onChange={(e) =>
                            saveSession({
                              settings: { ...session.settings, story_mode: e.target.value },
                            })
                          }
                        >
                          <option value="player">Player-led logbook</option>
                          <option value="ai_narrator">AI narrator</option>
                        </FormSelect>
                      </div>
                    )}
                    {session.selected_game_id === "colostle" && (
                      <>
                        <div>
                          <div className="label mb-2">Story mode</div>
                          <FormSelect
                            value={session.settings.story_mode || "player"}
                            onChange={(e) =>
                              saveSession({
                                settings: { ...session.settings, story_mode: e.target.value },
                              })
                            }
                          >
                            <option value="player">Player-led journal</option>
                            <option value="ai_narrator">AI narrator</option>
                          </FormSelect>
                        </div>
                        <div>
                          <div className="label mb-2">Location module</div>
                          <FormSelect
                            value={session.settings.location_mode || "roomlands"}
                            onChange={(e) =>
                              saveSession({
                                settings: { ...session.settings, location_mode: e.target.value },
                              })
                            }
                          >
                            <option value="roomlands">Roomlands</option>
                            <option value="ocean">Ocean</option>
                            <option value="city">City</option>
                            <option value="battlements">Battlements</option>
                          </FormSelect>
                        </div>
                      </>
                    )}
                    {session.selected_game_id === "whispers" && (
                      <>
                        <div>
                          <div className="label mb-2">Story mode</div>
                          <FormSelect
                            value={session.settings.story_mode || "player"}
                            onChange={(e) =>
                              saveSession({
                                settings: { ...session.settings, story_mode: e.target.value },
                              })
                            }
                          >
                            <option value="player">Player-led journal</option>
                            <option value="ai_narrator">AI narrator</option>
                          </FormSelect>
                        </div>
                        <div>
                          <div className="label mb-2">Difficulty</div>
                          <FormSelect
                            value={session.settings.difficulty || "normal"}
                            onChange={(e) =>
                              saveSession({
                                settings: { ...session.settings, difficulty: e.target.value },
                              })
                            }
                          >
                            <option value="normal">Normal (2 jokers)</option>
                            <option value="easy">Easy (1 joker)</option>
                          </FormSelect>
                        </div>
                      </>
                    )}
                    {session.selected_game_id === "ashes" && (
                      <>
                        <div>
                          <div className="label mb-2">Story mode</div>
                          <FormSelect
                            value={session.settings.story_mode || "player"}
                            onChange={(e) =>
                              saveSession({
                                settings: { ...session.settings, story_mode: e.target.value },
                              })
                            }
                          >
                            <option value="player">Player-led journal</option>
                            <option value="ai_narrator">AI narrator</option>
                          </FormSelect>
                        </div>
                        <div>
                          <div className="label mb-2">Journal prompt set</div>
                          <FormSelect
                            value={session.settings.prompt_set || "crypt"}
                            onChange={(e) =>
                              saveSession({
                                settings: { ...session.settings, prompt_set: e.target.value },
                              })
                            }
                          >
                            {ASHES_PROMPT_SETS.map((s) => (
                              <option key={s.id} value={s.id}>
                                {s.label}
                              </option>
                            ))}
                          </FormSelect>
                        </div>
                      </>
                    )}
                    {session.selected_game_id === "sansibilia" && (
                      <>
                        <div>
                          <div className="label mb-2">Story mode</div>
                          <FormSelect
                            value={session.settings.story_mode || "player"}
                            onChange={(e) =>
                              saveSession({
                                settings: { ...session.settings, story_mode: e.target.value },
                              })
                            }
                          >
                            <option value="player">Player-led journal</option>
                            <option value="ai_narrator">AI narrator</option>
                          </FormSelect>
                        </div>
                        <div>
                          <div className="label mb-2">Ending mode</div>
                          <FormSelect
                            value={session.settings.ending_mode || "four_changes"}
                            onChange={(e) =>
                              saveSession({
                                settings: { ...session.settings, ending_mode: e.target.value },
                              })
                            }
                          >
                            <option value="four_changes">Four city changes</option>
                            <option value="score_90">Score to 90</option>
                          </FormSelect>
                        </div>
                      </>
                    )}
                    {isGmSoloGameId(session.selected_game_id) && (
                      <div>
                        <div className="label mb-2">Story mode</div>
                        <FormSelect
                          value={session.settings.story_mode || "player"}
                          onChange={(e) =>
                            saveSession({
                              settings: { ...session.settings, story_mode: e.target.value },
                            })
                          }
                        >
                          <option value="player">Player-led</option>
                          <option value="ai_narrator">AI narrator</option>
                        </FormSelect>
                      </div>
                    )}
                    <div>
                      <div className="label mb-2">Card source</div>
                      <FormSelect
                        value={session.settings.card_source || "virtual"}
                        onChange={(e) =>
                          saveSession({
                            settings: { ...session.settings, card_source: e.target.value },
                          })
                        }
                      >
                        <option value="virtual">Virtual (AI draws)</option>
                        <option value="physical">Physical deck</option>
                      </FormSelect>
                    </div>
                  </section>
                )}
              </div>
            )}

            {tab === "rag" && (
              <div className="space-y-4">
                {providers.length > 1 && (
                  <section>
                    <div className="label mb-2">Chat provider</div>
                    <FormSelect
                      value={session.chat_provider}
                      onChange={(e) => saveSession({ chat_provider: e.target.value })}
                    >
                      {providers.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.label}
                        </option>
                      ))}
                    </FormSelect>
                  </section>
                )}

                <section className="grid sm:grid-cols-2 gap-4">
                  <div>
                    <div className="label mb-2">Mode</div>
                    <FormSelect
                      value={session.mode}
                      onChange={(e) => saveSession({ mode: e.target.value })}
                    >
                      <option value="RAG">RAG</option>
                      <option value="Agent">Agent</option>
                    </FormSelect>
                  </div>
                  <div>
                    <div className="label mb-2">Top-k ({session.top_k})</div>
                    <input
                      type="range"
                      min={3}
                      max={12}
                      value={session.top_k}
                      onChange={(e) => saveSession({ top_k: Number(e.target.value) })}
                      className="w-full accent-accent"
                    />
                  </div>
                </section>

                <section>
                  <div className="label mb-2">Retrieval profile</div>
                  <FormSelect
                    value={session.retrieval_profile}
                    onChange={(e) => saveSession({ retrieval_profile: e.target.value })}
                  >
                    {profiles.map((p) => (
                      <option key={p} value={p}>
                        {p}
                      </option>
                    ))}
                  </FormSelect>
                </section>
              </div>
            )}

            {tab === "character" && session.has_character_sheet && session.selected_game_id === "brambletrek_2" && (
              <Bt2CharacterSetupPanel
                entity={entity}
                onChange={setEntity}
                onSaved={handleCharacterSaved}
                roster={roster}
                activeId={session.slot_id}
                onSwitchRoster={onRosterSwitch}
              />
            )}

            {tab === "character" && session.has_character_sheet && session.selected_game_id === "brambletrek" && (
              <CharacterSetupPanel
                entity={entity}
                onChange={setEntity}
                onSaved={handleCharacterSaved}
                roster={roster}
                activeId={session.slot_id}
                onSwitchRoster={onRosterSwitch}
              />
            )}

            {tab === "character" && session.has_character_sheet && session.selected_game_id === "sansibilia" && (
              <VisitSetupPanel
                entity={entity}
                onChange={setEntity}
                onSaved={handleCharacterSaved}
                roster={roster}
                activeId={session.slot_id}
                onSwitchRoster={onRosterSwitch}
              />
            )}

            {tab === "character" && session.has_character_sheet && session.selected_game_id === "lighthouse" && (
              <WatchSetupPanel
                entity={entity}
                onChange={setEntity}
                onSaved={handleCharacterSaved}
                roster={roster}
                activeId={session.slot_id}
                onSwitchRoster={onRosterSwitch}
              />
            )}

            {tab === "character" && session.has_character_sheet && session.selected_game_id === "apothecaria" && (
              <CottageSetupPanel
                entity={entity}
                onChange={setEntity}
                onSaved={handleCharacterSaved}
                roster={roster}
                activeId={session.slot_id}
                onSwitchRoster={onRosterSwitch}
              />
            )}

            {tab === "character" && session.has_character_sheet && session.selected_game_id === "colostle" && (
              <AdventurerSetupPanel
                entity={entity}
                onChange={setEntity}
                onSaved={handleCharacterSaved}
                roster={roster}
                activeId={session.slot_id}
                onSwitchRoster={onRosterSwitch}
              />
            )}

            {tab === "character" && session.has_character_sheet && session.selected_game_id === "whispers" && (
              <InvestigationSetupPanel
                entity={entity}
                onChange={setEntity}
                onSaved={handleCharacterSaved}
                roster={roster}
                activeId={session.slot_id}
                onSwitchRoster={onRosterSwitch}
              />
            )}

            {tab === "character" && session.has_character_sheet && session.selected_game_id === "ashes" && (
              <ScionSetupPanel session={session} onSaved={onSaved} />
            )}

            {tab === "character" &&
              session.has_character_sheet &&
              session.selected_game_id === "mlp" &&
              session.entity && (
                <MlpSetupPanel
                  entity={entity}
                  onChange={setEntity}
                  onSaved={handleCharacterSaved}
                  roster={roster}
                  activeId={session.slot_id}
                  onSwitchRoster={onRosterSwitch}
                />
              )}

            {tab === "character" &&
              session.has_character_sheet &&
              session.selected_game_id === "dnd5e" &&
              session.entity && (
                <Dnd5eSetupPanel
                  entity={session.entity}
                  session={session}
                  roster={roster}
                  activeId={session.slot_id}
                  onSwitchRoster={onRosterSwitch}
                  onSaved={onSaved}
                />
              )}

            {tab === "character" &&
              session.has_character_sheet &&
              session.selected_game_id === "tor" &&
              session.entity && (
                <TorSetupPanel entity={session.entity} session={session} onSaved={onSaved} />
              )}

            {tab === "character" &&
              session.has_character_sheet &&
              session.selected_game_id === "outgunned" &&
              session.entity && (
                <OutgunnedSetupPanel
                  entity={session.entity}
                  session={session}
                  onSaved={onSaved}
                />
              )}

            {tab === "character" &&
              session.has_character_sheet &&
              session.selected_game_id === "coriolis" &&
              session.entity && (
                <CoriolisSetupPanel entity={session.entity} session={session} onSaved={onSaved} />
              )}

            {tab === "character" &&
              session.has_character_sheet &&
              isGmSoloGameId(session.selected_game_id) &&
              session.selected_game_id !== "dnd5e" &&
              session.selected_game_id !== "tor" &&
              session.selected_game_id !== "outgunned" &&
              session.selected_game_id !== "mlp" &&
              session.selected_game_id !== "coriolis" &&
              session.entity && (
                <GmSoloSetupPanel
                  gameId={session.selected_game_id}
                  entity={session.entity}
                  session={session}
                  onSaved={onSaved}
                />
              )}

            {tab === "character" && !session.has_character_sheet && (
              <p className="text-muted">Character setup is available in supported play games.</p>
            )}

            {tab === "index" && (
              <div className="space-y-4">
                <p className="text-muted text-xs">
                  Status:{" "}
                  <span className={indexStatus?.indexed ? "text-moss" : "text-accent"}>
                    {indexStatus?.indexed ? "Ready" : "Not indexed"}
                  </span>
                </p>
                <button
                  type="button"
                  className="btn btn-primary"
                  disabled={saving}
                  onClick={async () => {
                    await api.reindex();
                    setIndexStatus(await api.indexStatus());
                  }}
                >
                  Reindex documents
                </button>
              </div>
            )}
            </div>
          </div>
        </div>
    </AppDialog>
  );
}
