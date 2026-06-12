import { useEffect, useState } from "react";
import { BookOpen, Database, Play, User, X } from "lucide-react";
import { api } from "../../api/client";
import type { SessionState } from "../../types";

type Tab = "play" | "rag" | "character" | "index";

interface Props {
  open: boolean;
  session: SessionState;
  onClose: () => void;
  onSaved: (session: SessionState) => void;
}

const TABS: { id: Tab; label: string; icon: typeof Play }[] = [
  { id: "play", label: "Play", icon: Play },
  { id: "rag", label: "RAG", icon: BookOpen },
  { id: "character", label: "Character", icon: User },
  { id: "index", label: "Index", icon: Database },
];

export default function SettingsDialog({ open, session, onClose, onSaved }: Props) {
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

  if (!open) return null;

  const providers = (meta?.chat_providers as { id: string; label: string }[]) || [];
  const profiles = (meta?.retrieval_profiles as string[]) || [];

  const saveSession = async (patch: Record<string, unknown>) => {
    setSaving(true);
    try {
      const res = await api.updateSession(patch);
      onSaved(res);
    } finally {
      setSaving(false);
    }
  };

  const saveCharacter = async () => {
    if (session.has_character_sheet) {
      await api.updateCharacter(entity);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="panel-elevated w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-border shrink-0">
          <h2 className="font-semibold text-lg">Settings</h2>
          <button type="button" className="btn-ghost p-2" onClick={onClose}>
            <X className="w-4 h-4" />
          </button>
        </div>

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
                  <select
                    className="select"
                    value={session.selected_game_id}
                    onChange={(e) => saveSession({ selected_game_id: e.target.value })}
                  >
                    {games.map((g) => (
                      <option key={g.id} value={g.id}>
                        {g.label}
                      </option>
                    ))}
                  </select>
                </section>

                {session.has_character_sheet && session.settings && (
                  <section className="grid sm:grid-cols-2 gap-4 pt-4 border-t border-border">
                    <div>
                      <div className="label mb-2">Story mode</div>
                      <select
                        className="select"
                        value={session.settings.story_mode || "player"}
                        onChange={(e) =>
                          saveSession({
                            settings: { ...session.settings, story_mode: e.target.value },
                          })
                        }
                      >
                        <option value="player">Player-led</option>
                        <option value="ai_narrator">AI narrator</option>
                      </select>
                    </div>
                    <div>
                      <div className="label mb-2">Card source</div>
                      <select
                        className="select"
                        value={session.settings.card_source || "virtual"}
                        onChange={(e) =>
                          saveSession({
                            settings: { ...session.settings, card_source: e.target.value },
                          })
                        }
                      >
                        <option value="virtual">Virtual (AI draws)</option>
                        <option value="physical">Physical deck</option>
                      </select>
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
                    <select
                      className="select"
                      value={session.chat_provider}
                      onChange={(e) => saveSession({ chat_provider: e.target.value })}
                    >
                      {providers.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.label}
                        </option>
                      ))}
                    </select>
                  </section>
                )}

                <section className="grid sm:grid-cols-2 gap-4">
                  <div>
                    <div className="label mb-2">Mode</div>
                    <select
                      className="select"
                      value={session.mode}
                      onChange={(e) => saveSession({ mode: e.target.value })}
                    >
                      <option value="RAG">RAG</option>
                      <option value="Agent">Agent</option>
                    </select>
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
                  <select
                    className="select"
                    value={session.retrieval_profile}
                    onChange={(e) => saveSession({ retrieval_profile: e.target.value })}
                  >
                    {profiles.map((p) => (
                      <option key={p} value={p}>
                        {p}
                      </option>
                    ))}
                  </select>
                </section>
              </div>
            )}

            {tab === "character" && session.has_character_sheet && (
              <div className="space-y-4">
                <p className="text-muted text-xs">
                  Optional setup cards and journal notes for the active Gnawborn.
                </p>
                <input
                  className="input"
                  placeholder="Reason card (optional)"
                  value={String(entity.reason_card || "")}
                  onChange={(e) => setEntity({ ...entity, reason_card: e.target.value })}
                />
                <input
                  className="input"
                  placeholder="Background card (optional)"
                  value={String(entity.background_card || "")}
                  onChange={(e) => setEntity({ ...entity, background_card: e.target.value })}
                />
                <input
                  className="input"
                  placeholder="Trinket card (optional)"
                  value={String(entity.trinket_card || "")}
                  onChange={(e) => setEntity({ ...entity, trinket_card: e.target.value })}
                />
                <input
                  className="input"
                  placeholder="Legacy (optional)"
                  value={String(entity.legacy || "")}
                  onChange={(e) => setEntity({ ...entity, legacy: e.target.value })}
                />
                <textarea
                  className="input min-h-[80px]"
                  placeholder="Journal notes"
                  value={String(entity.notes || "")}
                  onChange={(e) => setEntity({ ...entity, notes: e.target.value })}
                />
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={async () => {
                    await saveCharacter();
                    onClose();
                  }}
                >
                  Save character setup
                </button>
              </div>
            )}

            {tab === "character" && !session.has_character_sheet && (
              <p className="text-muted">Character setup is available in Brambletrek mode.</p>
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
      </div>
    </div>
  );
}
