import { useCallback, useEffect, useState } from "react";
import { MessageSquare, ScrollText, User } from "lucide-react";
import { api } from "../api/client";
import CharacterPanel from "../components/brambletrek/CharacterPanel";
import LonelogBar from "../components/brambletrek/LonelogBar";
import ChatPanel from "../components/chat/ChatPanel";
import PlayPanel from "../components/layout/PlayPanel";
import StatsBar from "../components/layout/StatsBar";
import SettingsDialog from "../components/settings/SettingsDialog";
import type {
  CharacterHeader,
  JourneyActionResult,
  LegacyAbility,
  Message,
  PendingJourney,
  SessionState,
  Shortcut,
  Source,
} from "../types";

type MobileTab = "character" | "chat" | "play";

export default function PlayPage() {
  const [session, setSession] = useState<SessionState | null>(null);
  const [games, setGames] = useState<Record<string, string>>({});
  const [header, setHeader] = useState<CharacterHeader | null>(null);
  const [abilities, setAbilities] = useState<LegacyAbility[]>([]);
  const [roster, setRoster] = useState<{ id: string; name: string }[]>([]);
  const [journey, setJourney] = useState<PendingJourney | null>(null);
  const [shortcuts, setShortcuts] = useState<Shortcut[]>([]);
  const [lonelog, setLonelog] = useState<string[]>([]);
  const [deckRemaining, setDeckRemaining] = useState(0);
  const [cardSource, setCardSource] = useState("virtual");
  const [messages, setMessages] = useState<Message[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [lastRoute, setLastRoute] = useState("");
  const [loading, setLoading] = useState(false);
  const [shortcutLoading, setShortcutLoading] = useState<string | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [mobileTab, setMobileTab] = useState<MobileTab>("chat");
  const [state40k, setState40k] = useState<{
    game_state: Record<string, unknown>;
    summary: string;
    options: Record<string, Record<string, string>>;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadBrambletrek = useCallback(async () => {
    const [h, char, rosterRes, journeyRes, shortcutsRes, lonelogRes, deckRes] =
      await Promise.all([
        api.getHeader(),
        api.getCharacter(),
        api.getRoster(),
        api.getJourney(),
        api.getShortcuts(),
        api.getLonelog(),
        api.deckStatus(),
      ]);
    setHeader(h);
    setAbilities(char.abilities);
    setRoster(rosterRes.entries);
    setJourney(journeyRes.pending_journey);
    setShortcuts(shortcutsRes.shortcuts);
    setLonelog(lonelogRes.lines);
    setDeckRemaining(deckRes.remaining);
    setCardSource(deckRes.card_source);
  }, []);

  const load40k = useCallback(async () => {
    const res = await api.get40kState();
    setState40k(res);
    setHeader(null);
  }, []);

  const refresh = useCallback(async () => {
    try {
      setError(null);
      const s = await api.getSession();
      setSession(s);
      setMessages(s.messages || []);
      setSources(s.last_sources || []);
      const g = await api.getGames();
      setGames(Object.fromEntries(g.games.map((x) => [x.id, x.label])));
      if (s.has_character_sheet) {
        await loadBrambletrek();
      } else if (s.has_game_state) {
        await load40k();
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load session");
    }
  }, [loadBrambletrek, load40k]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    if (journey?.events?.length) setMobileTab("play");
  }, [journey?.events?.length]);

  const handleSend = async (prompt: string) => {
    setLoading(true);
    try {
      const res = await api.chat(prompt);
      setMessages(res.messages);
      setSources(res.sources);
      setLastRoute(res.route);
      if (session?.has_character_sheet) await loadBrambletrek();
    } finally {
      setLoading(false);
    }
  };

  const handleShortcut = async (id: string) => {
    const label = shortcuts.find((s) => s.id === id)?.label || id;
    setShortcutLoading(id);
    setMobileTab("chat");
    setLoading(true);
    setLastRoute(`brambletrek:${id}`);
    setMessages((m) => [...m, { role: "user", content: `**${label}**` }]);
    try {
      const res = await api.runShortcut(id);
      setMessages(res.messages);
      setSources(res.sources);
      setLastRoute(res.route);
      setHeader(res.header);
      setJourney(res.pending_journey);
      if (res.entity) setSession((s) => (s ? { ...s, entity: res.entity } : s));
      await loadBrambletrek();
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Shortcut failed";
      setMessages((m) => [
        ...m,
        { role: "assistant", content: `**Shortcut error:** ${msg}` },
      ]);
    } finally {
      setShortcutLoading(null);
      setLoading(false);
    }
  };

  const applyJourneyResult = useCallback((res: JourneyActionResult) => {
    if (res.header) setHeader(res.header);
    if (res.pending_journey !== undefined) setJourney(res.pending_journey);
    if (res.entity) setSession((s) => (s ? { ...s, entity: res.entity } : s));
  }, []);

  const handleJourneyApply = async (eventIndex: number) => {
    const res = await api.applyJourney(eventIndex);
    applyJourneyResult(res);
    const lonelogRes = await api.getLonelog();
    setLonelog(lonelogRes.lines);
    return { summary: res.summary, item_error: res.item_error };
  };

  const handleJourneyDrawItem = async (eventIndex: number) => {
    const res = await api.drawJourneyItem(eventIndex);
    applyJourneyResult(res);
    return { item_error: res.item_error };
  };

  const handleJourneyFinish = async () => {
    const res = await api.finishJourney();
    applyJourneyResult(res);
    const lonelogRes = await api.getLonelog();
    setLonelog(lonelogRes.lines);
  };

  const handleJourneyDiscard = async () => {
    const res = await api.discardJourney();
    applyJourneyResult(res);
  };

  const handleDeckAction = (formatted: string) => {
    setMessages((m) => [...m, { role: "assistant", content: formatted }]);
    loadBrambletrek();
  };

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8">
        <div className="panel-elevated p-6 max-w-md text-center space-y-3">
          <p className="text-red-300">{error}</p>
          <p className="text-sm text-muted">
            Ensure the API is running: uvicorn api.main:app --reload
          </p>
          <button type="button" className="btn btn-primary" onClick={refresh}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen flex items-center justify-center text-muted">Loading…</div>
    );
  }

  const gameLabel = games[session.selected_game_id] || session.selected_game_id;
  const showCharacter = session.has_character_sheet && session.entity;
  const showPlay = session.has_character_sheet || session.has_game_state;
  const hasJourney = Boolean(journey?.events?.length);

  const desktopGridClass = showCharacter
    ? "lg:grid-cols-[minmax(220px,16rem)_minmax(0,1fr)_minmax(18rem,24rem)]"
    : showPlay
      ? "lg:grid-cols-[minmax(0,1fr)_minmax(18rem,22rem)]"
      : "lg:grid-cols-1";

  const playPanel = (
    <PlayPanel
      hasCharacterSheet={session.has_character_sheet}
      hasGameState={session.has_game_state}
      journey={journey}
      shortcuts={shortcuts}
      shortcutLoading={shortcutLoading}
      deckRemaining={deckRemaining}
      cardSource={cardSource}
      state40k={state40k}
      onJourneyApply={handleJourneyApply}
      onJourneyDrawItem={handleJourneyDrawItem}
      onJourneyFinish={handleJourneyFinish}
      onJourneyDiscard={handleJourneyDiscard}
      onDeckAction={handleDeckAction}
      onShortcut={handleShortcut}
      on40kUpdate={(game_state, summary) =>
        setState40k((s) => (s ? { ...s, game_state, summary } : s))
      }
    />
  );

  return (
    <div className="h-screen flex flex-col bg-surface">
      <StatsBar
        header={session.has_character_sheet ? header : null}
        gameLabel={gameLabel}
        onOpenSettings={() => setSettingsOpen(true)}
      />

      {session.has_game_state && state40k?.summary && (
        <div className="px-4 py-1.5 text-xs text-muted border-b border-border bg-panel truncate">
          {state40k.summary}
        </div>
      )}

      {/* Desktop layout */}
      <div
        className={`hidden lg:grid flex-1 w-full gap-2 p-2 min-h-0 overflow-hidden ${desktopGridClass}`}
      >
        {showCharacter && (
          <div className="min-h-0">
            <CharacterPanel
              entity={session.entity!}
              abilities={abilities}
              roster={roster}
              activeId={session.slot_id || ""}
              onUpdate={(entity, h) => {
                setSession({ ...session, entity });
                setHeader(h);
              }}
              onSwitch={refresh}
            />
          </div>
        )}

        <div className="min-h-0 flex flex-col">
          <ChatPanel
            messages={messages}
            sources={sources}
            lastRoute={lastRoute}
            loading={loading}
            onSend={handleSend}
            onMessagesUpdate={(m, s, r) => {
              setMessages(m);
              setSources(s);
              setLastRoute(r);
            }}
            placeholder={
              session.has_character_sheet
                ? "Journey, @ action, rules… or /day, /roll d20"
                : "Ask about rules… or /roll 2d6+1, /draw 1"
            }
          />
        </div>

        {showPlay && <div className="min-h-0">{playPanel}</div>}
      </div>

      {/* Mobile layout */}
      <div className="lg:hidden flex-1 flex flex-col min-h-0 overflow-hidden pb-14">
        {mobileTab === "character" && showCharacter && (
          <div className="flex-1 min-h-0 p-2">
            <CharacterPanel
              entity={session.entity!}
              abilities={abilities}
              roster={roster}
              activeId={session.slot_id || ""}
              onUpdate={(entity, h) => {
                setSession({ ...session, entity });
                setHeader(h);
              }}
              onSwitch={refresh}
            />
          </div>
        )}

        {mobileTab === "chat" && (
          <div className="flex-1 min-h-0 p-2 flex flex-col">
            <ChatPanel
              messages={messages}
              sources={sources}
              lastRoute={lastRoute}
              loading={loading}
              onSend={handleSend}
              onMessagesUpdate={(m, s, r) => {
                setMessages(m);
                setSources(s);
                setLastRoute(r);
              }}
              placeholder={
                session.has_character_sheet
                  ? "Journey, @ action, rules… or /day, /roll d20"
                  : "Ask about rules… or /roll 2d6+1, /draw 1"
              }
            />
          </div>
        )}

        {mobileTab === "play" && showPlay && (
          <div className="flex-1 min-h-0 p-2">{playPanel}</div>
        )}
      </div>

      {session.has_character_sheet && (
        <div className="hidden lg:block shrink-0">
          <LonelogBar lines={lonelog} />
        </div>
      )}

      {/* Mobile bottom tabs */}
      <nav className="lg:hidden fixed bottom-0 inset-x-0 flex border-t border-border bg-panel z-40 safe-area-pb">
        {showCharacter && (
          <button
            type="button"
            className={`flex-1 flex flex-col items-center gap-0.5 py-2 text-xs ${
              mobileTab === "character" ? "text-accent" : "text-muted"
            }`}
            onClick={() => setMobileTab("character")}
          >
            <User className="w-5 h-5" />
            Character
          </button>
        )}
        <button
          type="button"
          className={`flex-1 flex flex-col items-center gap-0.5 py-2 text-xs ${
            mobileTab === "chat" ? "text-accent" : "text-muted"
          }`}
          onClick={() => setMobileTab("chat")}
        >
          <MessageSquare className="w-5 h-5" />
          Chat
        </button>
        {showPlay && (
          <button
            type="button"
            className={`flex-1 flex flex-col items-center gap-0.5 py-2 text-xs relative ${
              mobileTab === "play" ? "text-accent" : "text-muted"
            }`}
            onClick={() => setMobileTab("play")}
          >
            <ScrollText className="w-5 h-5" />
            Play
            {hasJourney && (
              <span className="absolute top-1.5 right-[calc(50%-1.25rem)] w-2 h-2 rounded-full bg-accent" />
            )}
          </button>
        )}
      </nav>

      <SettingsDialog
        open={settingsOpen}
        session={session}
        roster={roster}
        onClose={() => setSettingsOpen(false)}
        onRosterSwitch={refresh}
        onSaved={(s, header) => {
          setSession(s);
          if (header) setHeader(header);
          loadBrambletrek();
        }}
      />
    </div>
  );
}
