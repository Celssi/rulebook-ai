import { useCallback, useEffect, useState } from "react";
import { flushSync } from "react-dom";
import { MessageSquare, ScrollText, User } from "lucide-react";
import { api } from "../api/client";
import CharacterPanel from "../components/brambletrek/CharacterPanel";
import Bt2CharacterPanel from "../components/brambletrek_2/CharacterPanel";
import LonelogBar from "../components/shared/LonelogBar";
import VisitPanel from "../components/sansibilia/VisitPanel";
import WatchPanel from "../components/lighthouse/WatchPanel";
import CottagePanel from "../components/apothecaria/CottagePanel";
import InvestigationPanel from "../components/whispers/InvestigationPanel";
import ColostlePanel from "../components/colostle/ColostlePanel";
import ScionPanel from "../components/ashes/ScionPanel";
import ChatPanel from "../components/chat/ChatPanel";
import PlayPanel from "../components/layout/PlayPanel";
import StatsBar from "../components/layout/StatsBar";
import SettingsDialog from "../components/settings/SettingsDialog";
import HowToPlayDialog from "../components/shared/HowToPlayDialog";
import GmSoloPanel from "../components/gm_solo/GmSoloPanel";
import { gmSoloApi } from "../api/gmSolo";
import { isGmSoloGameId, type GmSoloGameId, type GmSoloHeader } from "../games/gmSoloGames";
import { shouldReloadSession } from "../games/registry";
import type {
  CharacterHeader,
  JourneyActionResult,
  LegacyAbility,
  Message,
  PendingJourney,
  PendingExploration,
  HollowState,
  ExplorationActionResult,
  SessionState,
  Shortcut,
  Source,
  VisitHeader,
  WatchHeader,
  ColostleHeader,
  CottageHeader,
  InvestigationHeader,
  ScionHeader,
} from "../types";

type MobileTab = "character" | "chat" | "play";

export default function PlayPage() {
  const [session, setSession] = useState<SessionState | null>(null);
  const [games, setGames] = useState<Record<string, string>>({});
  const [btHeader, setBtHeader] = useState<CharacterHeader | null>(null);
  const [ssHeader, setSsHeader] = useState<VisitHeader | null>(null);
  const [lhHeader, setLhHeader] = useState<WatchHeader | null>(null);
  const [apoHeader, setApoHeader] = useState<CottageHeader | null>(null);
  const [apoOptions, setApoOptions] = useState<{ locales?: { id: string; label: string }[] } | null>(
    null,
  );
  const [wHeader, setWHeader] = useState<InvestigationHeader | null>(null);
  const [colHeader, setColHeader] = useState<ColostleHeader | null>(null);
  const [ashHeader, setAshHeader] = useState<ScionHeader | null>(null);
  const [gmHeader, setGmHeader] = useState<GmSoloHeader | null>(null);
  const [abilities, setAbilities] = useState<LegacyAbility[]>([]);
  const [roster, setRoster] = useState<{ id: string; name: string }[]>([]);
  const [journey, setJourney] = useState<PendingJourney | null>(null);
  const [exploration, setExploration] = useState<PendingExploration | null>(null);
  const [hollow, setHollow] = useState<HollowState | null>(null);
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
  const [howToPlayOpen, setHowToPlayOpen] = useState(false);
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
    setBtHeader(h);
    setSsHeader(null);
    setLhHeader(null);
    setApoHeader(null);
    setWHeader(null);
    setColHeader(null);
    setAbilities(char.abilities);
    setRoster(rosterRes.entries);
    setJourney(journeyRes.pending_journey);
    setShortcuts(shortcutsRes.shortcuts);
    setLonelog(lonelogRes.lines);
    setDeckRemaining(deckRes.remaining);
    setCardSource(deckRes.card_source);
  }, []);

  const loadBrambletrek2 = useCallback(async () => {
    const [h, char, rosterRes, explorationRes, shortcutsRes, lonelogRes, hollowRes, deckRes] =
      await Promise.all([
        api.getBt2Header(),
        api.getBt2Character(),
        api.getBt2Roster(),
        api.getBt2Exploration(),
        api.getBt2Shortcuts(),
        api.getBt2Lonelog(),
        api.getBt2Hollow(),
        api.deckStatus(),
      ]);
    setBtHeader(h);
    setSsHeader(null);
    setLhHeader(null);
    setApoHeader(null);
    setWHeader(null);
    setColHeader(null);
    setAshHeader(null);
    setAbilities(char.abilities);
    setRoster(rosterRes.entries);
    setJourney(null);
    setExploration(explorationRes.pending_exploration);
    setHollow(hollowRes.hollow);
    setShortcuts(shortcutsRes.shortcuts);
    setLonelog(lonelogRes.lines);
    setDeckRemaining(deckRes.remaining);
    setCardSource(deckRes.card_source);
    setSession((s) => (s ? { ...s, entity: char.entity, settings: char.settings } : s));
  }, []);

  const loadSansibilia = useCallback(async () => {
    const [h, visit, rosterRes, shortcutsRes, lonelogRes, deckRes] = await Promise.all([
      api.getVisitHeader(),
      api.getVisit(),
      api.getSansibiliaRoster(),
      api.getSansibiliaShortcuts(),
      api.getSansibiliaLonelog(),
      api.deckStatus(),
    ]);
    setSsHeader(h);
    setLhHeader(null);
    setApoHeader(null);
    setWHeader(null);
    setColHeader(null);
    setBtHeader(null);
    setAbilities([]);
    setRoster(rosterRes.entries);
    setJourney(null);
    setShortcuts(shortcutsRes.shortcuts);
    setLonelog(lonelogRes.lines);
    setDeckRemaining(deckRes.remaining);
    setCardSource(deckRes.card_source);
    setSession((s) => (s ? { ...s, entity: visit.entity, settings: visit.settings } : s));
  }, []);

  const loadLighthouse = useCallback(async () => {
    const [h, watch, rosterRes, shortcutsRes, lonelogRes, deckRes] = await Promise.all([
      api.getLighthouseHeader(),
      api.getLighthouseWatch(),
      api.getLighthouseRoster(),
      api.getLighthouseShortcuts(),
      api.getLighthouseLonelog(),
      api.deckStatus(),
    ]);
    setLhHeader(h);
    setBtHeader(null);
    setSsHeader(null);
    setApoHeader(null);
    setWHeader(null);
    setColHeader(null);
    setAbilities([]);
    setRoster(rosterRes.entries);
    setJourney(null);
    setShortcuts(shortcutsRes.shortcuts);
    setLonelog(lonelogRes.lines);
    setDeckRemaining(deckRes.remaining);
    setCardSource(deckRes.card_source);
    setSession((s) => (s ? { ...s, entity: watch.entity, settings: watch.settings } : s));
  }, []);

  const loadApothecaria = useCallback(async () => {
    const [h, cottage, rosterRes, shortcutsRes, lonelogRes, deckRes] = await Promise.all([
      api.getApothecariaHeader(),
      api.getApothecariaCottage(),
      api.getApothecariaRoster(),
      api.getApothecariaShortcuts(),
      api.getApothecariaLonelog(),
      api.deckStatus(),
    ]);
    setApoHeader(h);
    setApoOptions((cottage.options as { locales?: { id: string; label: string }[] }) || null);
    setBtHeader(null);
    setSsHeader(null);
    setLhHeader(null);
    setWHeader(null);
    setColHeader(null);
    setAbilities([]);
    setRoster(rosterRes.entries);
    setJourney(null);
    setShortcuts(shortcutsRes.shortcuts);
    setLonelog(lonelogRes.lines);
    setDeckRemaining(deckRes.remaining);
    setCardSource(deckRes.card_source);
    setSession((s) => (s ? { ...s, entity: cottage.entity, settings: cottage.settings } : s));
  }, []);

  const loadWhispers = useCallback(async () => {
    const [h, inv, rosterRes, shortcutsRes, lonelogRes] = await Promise.all([
      api.getWhispersHeader(),
      api.getWhispersInvestigation(),
      api.getWhispersRoster(),
      api.getWhispersShortcuts(),
      api.getWhispersLonelog(),
    ]);
    setWHeader(h);
    setBtHeader(null);
    setSsHeader(null);
    setLhHeader(null);
    setApoHeader(null);
    setAbilities([]);
    setRoster(rosterRes.entries);
    setJourney(null);
    setShortcuts(shortcutsRes.shortcuts);
    setLonelog(lonelogRes.lines);
    setDeckRemaining(h.cards_remaining ?? 0);
    setCardSource(inv.settings?.card_source || "virtual");
    setSession((s) => (s ? { ...s, entity: inv.entity, settings: inv.settings } : s));
  }, []);

  const loadColostle = useCallback(async () => {
    const [h, character, rosterRes, shortcutsRes, lonelogRes, deckRes] = await Promise.all([
      api.getColostleHeader(),
      api.getColostleCharacter(),
      api.getColostleRoster(),
      api.getColostleShortcuts(),
      api.getColostleLonelog(),
      api.deckStatus(),
    ]);
    setColHeader(h);
    setBtHeader(null);
    setSsHeader(null);
    setLhHeader(null);
    setApoHeader(null);
    setWHeader(null);
    setAshHeader(null);
    setAbilities([]);
    setRoster(rosterRes.entries);
    setJourney(null);
    setShortcuts(shortcutsRes.shortcuts);
    setLonelog(lonelogRes.lines);
    setDeckRemaining(deckRes.remaining);
    setCardSource(deckRes.card_source);
    setSession((s) => (s ? { ...s, entity: character.entity, settings: character.settings } : s));
  }, []);

  const loadAshes = useCallback(async () => {
    const [h, scion, rosterRes, shortcutsRes, lonelogRes, deckRes] = await Promise.all([
      api.getAshesHeader(),
      api.getAshesScion(),
      api.getAshesRoster(),
      api.getAshesShortcuts(),
      api.getAshesLonelog(),
      api.deckStatus(),
    ]);
    setAshHeader(h);
    setBtHeader(null);
    setSsHeader(null);
    setLhHeader(null);
    setApoHeader(null);
    setWHeader(null);
    setColHeader(null);
    setAbilities([]);
    setRoster(rosterRes.entries);
    setJourney(null);
    setShortcuts(shortcutsRes.shortcuts);
    setLonelog(lonelogRes.lines);
    setDeckRemaining(deckRes.remaining);
    setCardSource(deckRes.card_source);
    setSession((s) => (s ? { ...s, entity: scion.entity, settings: scion.settings } : s));
  }, []);

  const load40k = useCallback(async () => {
    const res = await api.get40kState();
    setState40k(res);
    setBtHeader(null);
    setSsHeader(null);
    setGmHeader(null);
  }, []);

  const loadGmSolo = useCallback(async (gameId: GmSoloGameId) => {
    const gApi = gmSoloApi(gameId);
    const [h, character, rosterRes, shortcutsRes, lonelogRes, deckRes] = await Promise.all([
      gApi.getHeader(),
      gApi.getCharacter(),
      gApi.getRoster(),
      gApi.getShortcuts(),
      gApi.getLonelog(),
      api.deckStatus(),
    ]);
    setGmHeader(h);
    setBtHeader(null);
    setSsHeader(null);
    setLhHeader(null);
    setApoHeader(null);
    setWHeader(null);
    setColHeader(null);
    setAshHeader(null);
    setAbilities([]);
    setRoster(rosterRes.entries);
    setJourney(null);
    setShortcuts(shortcutsRes.shortcuts);
    setLonelog(lonelogRes.lines);
    setDeckRemaining(deckRes.remaining);
    setCardSource(deckRes.card_source);
    setSession((s) => (s ? { ...s, entity: character.entity, settings: character.settings } : s));
  }, []);

  const loadPlayData = useCallback(
    async (gameId: string, hasCharacterSheet: boolean, hasGameState: boolean) => {
      if (gameId === "brambletrek" && hasCharacterSheet) {
        await loadBrambletrek();
      } else if (gameId === "brambletrek_2" && hasCharacterSheet) {
        await loadBrambletrek2();
      } else if (gameId === "sansibilia" && hasCharacterSheet) {
        await loadSansibilia();
      } else if (gameId === "lighthouse" && hasCharacterSheet) {
        await loadLighthouse();
      } else if (gameId === "apothecaria" && hasCharacterSheet) {
        await loadApothecaria();
      } else if (gameId === "whispers" && hasCharacterSheet) {
        await loadWhispers();
      } else if (gameId === "colostle" && hasCharacterSheet) {
        await loadColostle();
      } else if (gameId === "ashes" && hasCharacterSheet) {
        await loadAshes();
      } else if (isGmSoloGameId(gameId) && hasCharacterSheet) {
        await loadGmSolo(gameId);
      } else if (hasGameState) {
        await load40k();
      }
    },
    [loadBrambletrek, loadBrambletrek2, loadSansibilia, loadLighthouse, loadApothecaria, loadWhispers, loadColostle, loadAshes, loadGmSolo, load40k]
  );

  const refresh = useCallback(async () => {
    try {
      setError(null);
      const s = await api.getSession();
      setSession(s);
      setMessages(s.messages || []);
      setSources(s.last_sources || []);
      const g = await api.getGames();
      setGames(Object.fromEntries(g.games.map((x) => [x.id, x.label])));
      await loadPlayData(s.selected_game_id, s.has_character_sheet, s.has_game_state);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load session");
    }
  }, [loadPlayData]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    if (journey?.events?.length) setMobileTab("play");
  }, [journey?.events?.length]);

  const reloadCurrentGame = useCallback(async () => {
    if (!session) return;
    const gameId = session.selected_game_id;
    await loadPlayData(gameId, session.has_character_sheet, session.has_game_state);
    if (shouldReloadSession(gameId)) {
      const s = await api.getSession();
      setMessages(s.messages || []);
      setSession(s);
    }
  }, [session, loadPlayData]);

  const handleSend = async (prompt: string) => {
    setLoading(true);
    try {
      const res = await api.chat(prompt);
      setMessages(res.messages);
      setSources(res.sources);
      setLastRoute(res.route);
      if (session?.has_character_sheet) await reloadCurrentGame();
    } finally {
      setLoading(false);
    }
  };

  const handleShortcut = async (id: string, params?: Record<string, unknown>) => {
    const label = shortcuts.find((s) => s.id === id)?.label || id;
    const gameId = session?.selected_game_id;
    setShortcutLoading(id);
    setMobileTab("chat");
    setLastRoute(`${gameId}:${id}`);
    flushSync(() => {
      setMessages((m) => [...m, { role: "user", content: `**${label}**` }]);
    });
    setLoading(true);
    try {
      const res =
        isGmSoloGameId(gameId || "")
          ? await gmSoloApi(gameId as GmSoloGameId).runShortcut(id, params)
          : gameId === "sansibilia"
          ? await api.runSansibiliaShortcut(id)
          : gameId === "brambletrek_2"
            ? await api.runBt2Shortcut(id)
          : gameId === "lighthouse"
            ? await api.runLighthouseShortcut(id)
            : gameId === "apothecaria"
              ? await api.runApothecariaShortcut(id)
              : gameId === "whispers"
                ? await api.runWhispersShortcut(id)
                : gameId === "ashes"
                  ? await api.runAshesShortcut(id)
                  : gameId === "colostle"
                    ? await api.runColostleShortcut(id)
                : await api.runShortcut(id);
      setMessages(res.messages);
      setSources(res.sources);
      setLastRoute(res.route);
      if (isGmSoloGameId(gameId || "")) {
        setGmHeader(res.header as GmSoloHeader);
      } else if (gameId === "sansibilia") {
        setSsHeader(res.header as VisitHeader);
      } else if (gameId === "lighthouse") {
        setLhHeader(res.header as WatchHeader);
      } else if (gameId === "apothecaria") {
        setApoHeader(res.header as CottageHeader);
      } else if (gameId === "whispers") {
        setWHeader(res.header as InvestigationHeader);
      } else if (gameId === "ashes") {
        setAshHeader(res.header as ScionHeader);
      } else if (gameId === "colostle") {
        setColHeader(res.header as ColostleHeader);
      } else if (gameId === "brambletrek") {
        setBtHeader(res.header as CharacterHeader);
        setJourney("pending_journey" in res ? res.pending_journey : null);
      } else if (gameId === "brambletrek_2") {
        setBtHeader(res.header as CharacterHeader);
        setExploration("pending_exploration" in res ? res.pending_exploration : null);
        setHollow("hollow" in res ? res.hollow : null);
      }
      if (res.entity) setSession((s) => (s ? { ...s, entity: res.entity } : s));
      await reloadCurrentGame();
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
    if (res.header) setBtHeader(res.header);
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

  const applyExplorationResult = useCallback((res: ExplorationActionResult) => {
    if (res.header) setBtHeader(res.header);
    if (res.pending_exploration !== undefined) setExploration(res.pending_exploration);
    if (res.entity) setSession((s) => (s ? { ...s, entity: res.entity } : s));
  }, []);

  const handleExplorationApply = async (eventIndex: number) => {
    const res = await api.applyBt2Exploration(eventIndex);
    applyExplorationResult(res);
    const lonelogRes = await api.getBt2Lonelog();
    setLonelog(lonelogRes.lines);
    return { summary: res.summary };
  };

  const handleExplorationFinish = async () => {
    const res = await api.finishBt2Exploration();
    applyExplorationResult(res);
    const lonelogRes = await api.getBt2Lonelog();
    setLonelog(lonelogRes.lines);
  };

  const handleExplorationDiscard = async () => {
    const res = await api.discardBt2Exploration();
    applyExplorationResult(res);
  };

  const handleHollowMove = async (row: number, col: number) => {
    const res = await api.moveBt2Hollow(row, col);
    if (res.header) setBtHeader(res.header);
    if (res.hollow !== undefined) setHollow(res.hollow);
    if (res.entity) setSession((s) => (s ? { ...s, entity: res.entity } : s));
    const lonelogRes = await api.getBt2Lonelog();
    setLonelog(lonelogRes.lines);
  };

  const handleJourneyDiscard = async () => {
    const res = await api.discardJourney();
    applyJourneyResult(res);
  };

  const handleDeckAction = (formatted: string) => {
    setMessages((m) => [...m, { role: "assistant", content: formatted }]);
    reloadCurrentGame();
  };

  const handleDayDraw = async () => {
    setMobileTab("chat");
    setLastRoute("sansibilia:draw_day");
    flushSync(() => {
      setMessages((m) => [...m, { role: "user", content: "**Draw day's cards**" }]);
    });
    setLoading(true);
    try {
      const res = await api.drawVisitDay();
      setMessages(res.messages);
      setSession((s) =>
        s ? { ...s, entity: res.entity, messages: res.messages } : s,
      );
      setSsHeader(res.header);
      const lonelogRes = await api.getSansibiliaLonelog();
      setLonelog(lonelogRes.lines);
      const deckRes = await api.deckStatus();
      setDeckRemaining(deckRes.remaining);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Draw failed";
      setMessages((m) => [
        ...m,
        { role: "assistant", content: `**Draw error:** ${msg}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleVisitUpdate = (
    entity: Record<string, unknown>,
    header: VisitHeader,
  ) => {
    setSession((s) => (s ? { ...s, entity } : s));
    setSsHeader(header);
    reloadCurrentGame();
  };

  const handleCottageUpdate = (
    entity: Record<string, unknown>,
    header: CottageHeader,
  ) => {
    setSession((s) => (s ? { ...s, entity } : s));
    setApoHeader(header);
    reloadCurrentGame();
  };

  const handleApothecariaForage = async () => {
    setMobileTab("chat");
    setLastRoute("apothecaria:forage_event");
    flushSync(() => {
      setMessages((m) => [...m, { role: "user", content: "**Forage / draw event**" }]);
    });
    setLoading(true);
    try {
      const res = await api.runApothecariaShortcut("forage_event");
      setMessages(res.messages);
      setSources(res.sources);
      setLastRoute(res.route);
      setApoHeader(res.header);
      if (res.entity) setSession((s) => (s ? { ...s, entity: res.entity } : s));
      await reloadCurrentGame();
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Forage failed";
      setMessages((m) => [
        ...m,
        { role: "assistant", content: `**Forage error:** ${msg}` },
      ]);
    } finally {
      setLoading(false);
    }
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

  const gameId = session.selected_game_id;
  const gameLabel = games[gameId] || gameId;
  const showCharacter = session.has_character_sheet && session.entity;
  const showPlay = session.has_character_sheet || session.has_game_state;
  const hasJourney = Boolean(journey?.events?.length);
  const statsHeader =
    gameId === "sansibilia"
      ? ssHeader
      : gameId === "lighthouse"
        ? lhHeader
        : gameId === "apothecaria"
          ? apoHeader
          : gameId === "whispers"
            ? wHeader
            : gameId === "colostle"
              ? colHeader
            : gameId === "ashes"
              ? ashHeader
              : isGmSoloGameId(gameId)
                ? gmHeader
            : btHeader;

  const chatPlaceholder =
    gameId === "sansibilia"
      ? "Journal prompts, city changes, rules… or /roll d6, /draw 1"
      : gameId === "lighthouse"
        ? "Light the lamp, maintenance, observation… or /roll d6"
        : gameId === "apothecaria"
          ? "Draw ailments, forage locales, reagents… or /roll d6"
          : gameId === "whispers"
            ? "Build Whispers deck, draw prompts, oracle… or /roll 2d6"
            : gameId === "colostle"
              ? "Exploration phase, combat setup, oracle… or /draw 1"
            : gameId === "ashes"
              ? "Draw rooms, journal prompts, enemies… or /roll 3d6, /draw 1"
              : isGmSoloGameId(gameId)
                ? "Rules, shortcuts, dice… or /roll d20, /roll 2d6"
            : gameId === "brambletrek_2"
              ? "Exploration, Hollow, rules… or /day, /roll d6"
            : session.has_character_sheet
        ? "Journey, @ action, rules… or /day, /roll d20"
        : "Ask about rules… or /roll 2d6+1, /draw 1";

  const desktopGridClass = showCharacter
    ? "lg:grid-cols-[minmax(220px,16rem)_minmax(0,1fr)_minmax(18rem,24rem)]"
    : showPlay
      ? "lg:grid-cols-[minmax(0,1fr)_minmax(18rem,22rem)]"
      : "lg:grid-cols-1";

  const playPanel = (
    <PlayPanel
      gameId={gameId}
      hasCharacterSheet={session.has_character_sheet}
      hasGameState={session.has_game_state}
      journey={journey}
      shortcuts={shortcuts}
      shortcutLoading={shortcutLoading}
      deckRemaining={deckRemaining}
      cardSource={cardSource}
      visitEntity={session.entity}
      visitHeader={ssHeader}
      cottageEntity={session.entity}
      cottageHeader={apoHeader}
      cottageOptions={apoOptions}
      state40k={state40k}
      onJourneyApply={handleJourneyApply}
      onJourneyDrawItem={handleJourneyDrawItem}
      onJourneyFinish={handleJourneyFinish}
      onJourneyDiscard={handleJourneyDiscard}
      exploration={exploration}
      hollow={hollow}
      onExplorationApply={handleExplorationApply}
      onExplorationFinish={handleExplorationFinish}
      onExplorationDiscard={handleExplorationDiscard}
      onHollowMove={handleHollowMove}
      onDeckAction={handleDeckAction}
      onShortcut={handleShortcut}
      onDayDraw={handleDayDraw}
      onVisitUpdate={handleVisitUpdate}
      onCottageUpdate={handleCottageUpdate}
      onApothecariaForage={handleApothecariaForage}
      on40kUpdate={(game_state, summary) =>
        setState40k((s) => (s ? { ...s, game_state, summary } : s))
      }
    />
  );

  const sidebar =
    gameId === "sansibilia" && showCharacter ? (
      <VisitPanel
        entity={session.entity!}
        roster={roster}
        activeId={session.slot_id || ""}
        header={ssHeader}
        onUpdate={handleVisitUpdate}
        onSwitch={refresh}
      />
    ) : gameId === "lighthouse" && showCharacter ? (
      <WatchPanel
        entity={session.entity!}
        roster={roster}
        activeId={session.slot_id || ""}
        header={lhHeader}
        onSwitch={refresh}
      />
    ) : gameId === "apothecaria" && showCharacter ? (
      <CottagePanel
        entity={session.entity!}
        roster={roster}
        activeId={session.slot_id || ""}
        header={apoHeader}
        onSwitch={refresh}
      />
    ) : gameId === "colostle" && showCharacter ? (
      <ColostlePanel
        entity={session.entity!}
        roster={roster}
        activeId={session.slot_id || ""}
        header={colHeader}
        onSwitch={refresh}
      />
    ) : gameId === "whispers" && showCharacter ? (
      <InvestigationPanel
        entity={session.entity!}
        roster={roster}
        activeId={session.slot_id || ""}
        header={wHeader}
        onSwitch={refresh}
      />
    ) : gameId === "ashes" && showCharacter ? (
      <ScionPanel
        entity={session.entity!}
        roster={roster}
        activeId={session.slot_id || ""}
        header={ashHeader}
        onSwitch={refresh}
      />
    ) : isGmSoloGameId(gameId) && showCharacter ? (
      <GmSoloPanel
        gameId={gameId}
        entity={session.entity!}
        roster={roster}
        activeId={session.slot_id || ""}
        header={gmHeader}
        onSwitch={refresh}
      />
    ) : gameId === "brambletrek_2" && showCharacter ? (
      <Bt2CharacterPanel
        entity={session.entity!}
        abilities={abilities}
        roster={roster}
        activeId={session.slot_id || ""}
        onUpdate={(entity, h) => {
          setSession({ ...session, entity });
          setBtHeader(h);
        }}
        onSwitch={refresh}
      />
    ) : gameId === "brambletrek" && showCharacter ? (
      <CharacterPanel
        entity={session.entity!}
        abilities={abilities}
        roster={roster}
        activeId={session.slot_id || ""}
        onUpdate={(entity, h) => {
          setSession({ ...session, entity });
          setBtHeader(h);
        }}
        onSwitch={refresh}
      />
    ) : null;

  return (
    <div className="h-screen flex flex-col bg-surface">
      <StatsBar
        gameId={gameId}
        header={statsHeader}
        gameLabel={gameLabel}
        onOpenSettings={() => setSettingsOpen(true)}
        onOpenHowToPlay={gameId !== "40k" ? () => setHowToPlayOpen(true) : undefined}
      />

      {session.has_game_state && state40k?.summary && (
        <div className="px-4 py-1.5 text-xs text-muted border-b border-border bg-panel truncate">
          {state40k.summary}
        </div>
      )}

      <div
        className={`hidden lg:grid flex-1 w-full gap-2 p-2 min-h-0 overflow-hidden ${desktopGridClass}`}
      >
        {sidebar && <div className="min-h-0">{sidebar}</div>}

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
            placeholder={chatPlaceholder}
          />
        </div>

        {showPlay && <div className="min-h-0">{playPanel}</div>}
      </div>

      <div className="lg:hidden flex-1 flex flex-col min-h-0 overflow-hidden pb-14">
        {mobileTab === "character" && sidebar && (
          <div className="flex-1 min-h-0 p-2">{sidebar}</div>
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
              placeholder={chatPlaceholder}
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
            {gameId === "sansibilia"
              ? "Visit"
              : gameId === "lighthouse"
                ? "Watch"
                : gameId === "apothecaria"
                  ? "Cottage"
                  : gameId === "whispers"
                    ? "Case"
                    : "Character"}
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
          if (header) {
            if (gameId === "sansibilia") setSsHeader(header as VisitHeader);
            else if (gameId === "lighthouse") setLhHeader(header as WatchHeader);
            else if (gameId === "apothecaria") setApoHeader(header as CottageHeader);
            else if (gameId === "whispers") setWHeader(header as InvestigationHeader);
            else if (gameId === "ashes") setAshHeader(header as ScionHeader);
            else if (gameId === "colostle") setColHeader(header as ColostleHeader);
            else setBtHeader(header as CharacterHeader);
          }
          reloadCurrentGame();
        }}
      />

      <HowToPlayDialog
        open={howToPlayOpen}
        gameId={gameId}
        gameLabel={gameLabel}
        onClose={() => setHowToPlayOpen(false)}
      />
    </div>
  );
}
