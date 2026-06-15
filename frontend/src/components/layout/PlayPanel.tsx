import { useEffect, useState } from "react";
import DeckPanel from "../shared/DeckPanel";
import JourneyPanel from "../brambletrek/JourneyPanel";
import BrambletrekShortcutGroups from "../brambletrek/ShortcutGroups";
import ExplorationPanel from "../brambletrek_2/ExplorationPanel";
import HollowPanel from "../brambletrek_2/HollowPanel";
import Bt2ShortcutGroups from "../brambletrek_2/ShortcutGroups";
import DayPanel from "../sansibilia/DayPanel";
import ShortcutList from "../shared/ShortcutList";
import AshesShortcutGroups from "../ashes/ShortcutGroups";
import AilmentPanel from "../apothecaria/AilmentPanel";
import ApothecariaShortcutGroups from "../apothecaria/ShortcutGroups";
import GameStatePanel from "../warhammer40k/GameStatePanel";
import { GM_SOLO_PLAY_PANEL, isGmSoloPanelGame } from "../../games/panelRegistry";
import type { GmSoloGameId } from "../../games/gmSoloGames";
import type { CottageHeader, HollowState, PendingExploration, PendingJourney, Shortcut, VisitHeader } from "../../types";

type BrambletrekTab = "journey" | "deck" | "shortcuts";
type Bt2Tab = "exploration" | "hollow" | "deck" | "shortcuts";
type SansibiliaTab = "day" | "deck" | "shortcuts";
type LighthouseTab = "deck" | "shortcuts";
type ApothecariaTab = "ailment" | "deck" | "shortcuts";

interface Props {
  gameId: string;
  hasCharacterSheet: boolean;
  hasGameState: boolean;
  journey: PendingJourney | null;
  exploration?: PendingExploration | null;
  hollow?: HollowState | null;
  shortcuts: Shortcut[];
  shortcutLoading: string | null;
  deckRemaining: number;
  cardSource: string;
  visitEntity?: Record<string, unknown>;
  visitHeader?: VisitHeader | null;
  cottageEntity?: Record<string, unknown>;
  cottageHeader?: CottageHeader | null;
  cottageOptions?: { locales?: { id: string; label: string }[] } | null;
  state40k: {
    game_state: Record<string, unknown>;
    summary: string;
    options: Record<string, Record<string, string>>;
  } | null;
  onJourneyApply: (index: number) => Promise<{ summary?: string; item_error?: string | null }>;
  onJourneyDrawItem: (index: number) => Promise<{ item_error?: string | null }>;
  onJourneyFinish: () => Promise<void>;
  onJourneyDiscard: () => Promise<void>;
  onExplorationApply?: (index: number) => Promise<{ summary?: string }>;
  onExplorationFinish?: () => Promise<void>;
  onExplorationDiscard?: () => Promise<void>;
  onHollowMove?: (row: number, col: number) => Promise<void>;
  onDeckAction: (formatted: string) => void;
  onShortcut: (id: string, params?: Record<string, unknown>) => void;
  onDayDraw?: () => Promise<void>;
  onVisitUpdate?: (entity: Record<string, unknown>, header: VisitHeader) => void;
  onCottageUpdate?: (entity: Record<string, unknown>, header: CottageHeader) => void;
  onApothecariaForage?: () => Promise<void>;
  on40kUpdate: (game_state: Record<string, unknown>, summary: string) => void;
}

export default function PlayPanel({
  gameId,
  hasCharacterSheet,
  hasGameState,
  journey,
  exploration = null,
  hollow = null,
  shortcuts,
  shortcutLoading,
  deckRemaining,
  cardSource,
  visitEntity,
  visitHeader,
  cottageEntity,
  cottageHeader,
  cottageOptions,
  state40k,
  onJourneyApply,
  onJourneyDrawItem,
  onJourneyFinish,
  onJourneyDiscard,
  onExplorationApply,
  onExplorationFinish,
  onExplorationDiscard,
  onHollowMove,
  onDeckAction,
  onShortcut,
  onDayDraw,
  onVisitUpdate,
  onCottageUpdate,
  onApothecariaForage,
  on40kUpdate,
}: Props) {
  const hasJourney = Boolean(journey?.events?.length);
  const hasExploration = Boolean(exploration?.events?.length);
  const [btTab, setBtTab] = useState<BrambletrekTab>("journey");
  const [bt2Tab, setBt2Tab] = useState<Bt2Tab>("exploration");
  const [ssTab, setSsTab] = useState<SansibiliaTab>("day");
  const [lhTab, setLhTab] = useState<LighthouseTab>("shortcuts");
  const [apoTab, setApoTab] = useState<ApothecariaTab>("ailment");

  useEffect(() => {
    if (hasJourney) setBtTab("journey");
  }, [hasJourney]);

  useEffect(() => {
    if (hasExploration) setBt2Tab("exploration");
  }, [hasExploration]);

  if (isGmSoloPanelGame(gameId) && hasCharacterSheet) {
    const GmPlay = GM_SOLO_PLAY_PANEL;
    return (
      <GmPlay
        gameId={gameId as GmSoloGameId}
        shortcuts={shortcuts}
        shortcutLoading={shortcutLoading}
        onShortcut={onShortcut}
      />
    );
  }

  if (gameId === "brambletrek_2" && hasCharacterSheet) {
    const tabs: { id: Bt2Tab; label: string }[] = [
      { id: "exploration", label: "Exploration" },
      { id: "hollow", label: "Hollow" },
      { id: "deck", label: "Deck" },
      { id: "shortcuts", label: "Shortcuts" },
    ];
    return (
      <div className="panel flex flex-col h-full min-h-0 overflow-hidden">
        <div className="flex border-b border-border shrink-0">
          {tabs.map((t) => (
            <button
              key={t.id}
              type="button"
              className={bt2Tab === t.id ? "tab-btn-active" : "tab-btn hover:text-gray-200"}
              onClick={() => setBt2Tab(t.id)}
            >
              {t.label}
              {t.id === "exploration" && hasExploration && (
                <span className="ml-1 inline-block w-1.5 h-1.5 rounded-full bg-accent" />
              )}
            </button>
          ))}
        </div>
        <div className="flex-1 overflow-y-auto p-3 min-h-0">
          {bt2Tab === "exploration" && (
            <ExplorationPanel
              exploration={exploration}
              onApply={onExplorationApply!}
              onFinish={onExplorationFinish!}
              onDiscard={onExplorationDiscard!}
              embedded
            />
          )}
          {bt2Tab === "hollow" && (
            <HollowPanel hollow={hollow} onMove={onHollowMove!} />
          )}
          {bt2Tab === "deck" && (
            <DeckPanel remaining={deckRemaining} cardSource={cardSource} onAction={onDeckAction} embedded />
          )}
          {bt2Tab === "shortcuts" && (
            <Bt2ShortcutGroups shortcuts={shortcuts} loading={shortcutLoading} onRun={onShortcut} embedded />
          )}
        </div>
      </div>
    );
  }

  if (hasGameState && state40k) {
    return (
      <div className="panel flex flex-col h-full min-h-0 overflow-hidden">
        <div className="flex-1 overflow-y-auto min-h-0">
          <GameStatePanel
            gameState={state40k.game_state}
            options={state40k.options}
            summary={state40k.summary}
            onUpdate={on40kUpdate}
          />
        </div>
      </div>
    );
  }

  if (gameId === "apothecaria" && hasCharacterSheet && cottageEntity) {
    const tabs: { id: ApothecariaTab; label: string }[] = [
      { id: "ailment", label: "Play" },
      { id: "deck", label: "Deck" },
      { id: "shortcuts", label: "Shortcuts" },
    ];
    return (
      <div className="panel flex flex-col h-full min-h-0 overflow-hidden">
        <div className="flex border-b border-border shrink-0">
          {tabs.map((t) => (
            <button
              key={t.id}
              type="button"
              className={apoTab === t.id ? "tab-btn-active" : "tab-btn hover:text-gray-200"}
              onClick={() => setApoTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
        <div className="flex-1 overflow-y-auto p-3 min-h-0">
          {apoTab === "ailment" && (
            <AilmentPanel
              entity={cottageEntity}
              header={cottageHeader ?? null}
              options={cottageOptions ?? null}
              onUpdate={(e, h) => onCottageUpdate?.(e, h)}
              onForage={onApothecariaForage}
              embedded
            />
          )}
          {apoTab === "deck" && (
            <DeckPanel
              remaining={deckRemaining}
              cardSource={cardSource}
              onAction={onDeckAction}
              embedded
            />
          )}
          {apoTab === "shortcuts" && (
            <ApothecariaShortcutGroups
              shortcuts={shortcuts}
              loading={shortcutLoading}
              onRun={onShortcut}
              embedded
            />
          )}
        </div>
      </div>
    );
  }

  if (gameId === "lighthouse" && hasCharacterSheet) {
    const tabs: { id: LighthouseTab; label: string }[] = [
      { id: "shortcuts", label: "Shortcuts" },
      { id: "deck", label: "Deck" },
    ];
    return (
      <div className="panel flex flex-col h-full min-h-0 overflow-hidden">
        <div className="flex border-b border-border shrink-0">
          {tabs.map((t) => (
            <button
              key={t.id}
              type="button"
              className={lhTab === t.id ? "tab-btn-active" : "tab-btn hover:text-gray-200"}
              onClick={() => setLhTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
        <div className="flex-1 overflow-y-auto p-3 min-h-0">
          {lhTab === "deck" && (
            <DeckPanel
              remaining={deckRemaining}
              cardSource={cardSource}
              onAction={onDeckAction}
              embedded
            />
          )}
          {lhTab === "shortcuts" && (
            <ShortcutList
              shortcuts={shortcuts}
              loading={shortcutLoading}
              onRun={onShortcut}
              embedded
            />
          )}
        </div>
      </div>
    );
  }

  if ((gameId === "colostle" || gameId === "whispers") && hasCharacterSheet) {
    const tabs: { id: LighthouseTab; label: string }[] = [
      { id: "shortcuts", label: "Shortcuts" },
      { id: "deck", label: "Deck" },
    ];
    return (
      <div className="panel flex flex-col h-full min-h-0 overflow-hidden">
        <div className="flex border-b border-border shrink-0">
          {tabs.map((t) => (
            <button
              key={t.id}
              type="button"
              className={lhTab === t.id ? "tab-btn-active" : "tab-btn hover:text-gray-200"}
              onClick={() => setLhTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
        <div className="flex-1 overflow-y-auto p-3 min-h-0">
          {lhTab === "deck" && gameId !== "whispers" && (
            <DeckPanel
              remaining={deckRemaining}
              cardSource={cardSource}
              onAction={onDeckAction}
              embedded
            />
          )}
          {lhTab === "shortcuts" && (
            <ShortcutList
              shortcuts={shortcuts}
              loading={shortcutLoading}
              onRun={onShortcut}
              embedded
            />
          )}
        </div>
      </div>
    );
  }

  if (gameId === "ashes" && hasCharacterSheet) {
    const tabs: { id: LighthouseTab; label: string }[] = [
      { id: "shortcuts", label: "Shortcuts" },
      { id: "deck", label: "Deck" },
    ];
    return (
      <div className="panel flex flex-col h-full min-h-0 overflow-hidden">
        <div className="flex border-b border-border shrink-0">
          {tabs.map((t) => (
            <button
              key={t.id}
              type="button"
              className={lhTab === t.id ? "tab-btn-active" : "tab-btn hover:text-gray-200"}
              onClick={() => setLhTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
        <div className="flex-1 overflow-y-auto p-3 min-h-0">
          {lhTab === "deck" && (
            <DeckPanel
              remaining={deckRemaining}
              cardSource={cardSource}
              onAction={onDeckAction}
              embedded
            />
          )}
          {lhTab === "shortcuts" && (
            <AshesShortcutGroups
              shortcuts={shortcuts}
              loading={shortcutLoading}
              onRun={onShortcut}
              embedded
            />
          )}
        </div>
      </div>
    );
  }

  if (gameId === "sansibilia" && hasCharacterSheet && visitEntity) {
    const tabs: { id: SansibiliaTab; label: string }[] = [
      { id: "day", label: "Day" },
      { id: "deck", label: "Deck" },
      { id: "shortcuts", label: "Shortcuts" },
    ];

    return (
      <div className="panel flex flex-col h-full min-h-0 overflow-hidden">
        <div className="flex border-b border-border shrink-0">
          {tabs.map((t) => (
            <button
              key={t.id}
              type="button"
              className={ssTab === t.id ? "tab-btn-active" : "tab-btn hover:text-gray-200"}
              onClick={() => setSsTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
        <div className="flex-1 overflow-y-auto p-3 min-h-0">
          {ssTab === "day" && (
            <DayPanel
              entity={visitEntity}
              header={visitHeader ?? null}
              onDrawDay={onDayDraw}
              onUpdate={(e, h) => onVisitUpdate?.(e, h)}
              embedded
            />
          )}
          {ssTab === "deck" && (
            <DeckPanel
              remaining={deckRemaining}
              cardSource={cardSource}
              onAction={onDeckAction}
              embedded
            />
          )}
          {ssTab === "shortcuts" && (
            <ShortcutList
              shortcuts={shortcuts}
              loading={shortcutLoading}
              onRun={onShortcut}
              embedded
            />
          )}
        </div>
      </div>
    );
  }

  if (!hasCharacterSheet) return null;

  if (gameId !== "brambletrek") return null;

  const tabs: { id: BrambletrekTab; label: string }[] = [
    { id: "journey", label: "Journey" },
    { id: "deck", label: "Deck" },
    { id: "shortcuts", label: "Shortcuts" },
  ];

  return (
    <div className="panel flex flex-col h-full min-h-0 overflow-hidden">
      <div className="flex border-b border-border shrink-0">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            className={btTab === t.id ? "tab-btn-active" : "tab-btn hover:text-gray-200"}
            onClick={() => setBtTab(t.id)}
          >
            {t.label}
            {t.id === "journey" && hasJourney && (
              <span className="ml-1 inline-block w-1.5 h-1.5 rounded-full bg-accent" />
            )}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-3 min-h-0">
        {btTab === "journey" && (
          <JourneyPanel
            journey={journey}
            onApply={onJourneyApply}
            onDrawItem={onJourneyDrawItem}
            onFinish={onJourneyFinish}
            onDiscard={onJourneyDiscard}
            embedded
          />
        )}
        {btTab === "deck" && (
          <DeckPanel
            remaining={deckRemaining}
            cardSource={cardSource}
            onAction={onDeckAction}
            embedded
          />
        )}
        {btTab === "shortcuts" && (
          <BrambletrekShortcutGroups
            shortcuts={shortcuts}
            loading={shortcutLoading}
            onRun={onShortcut}
            embedded
          />
        )}
      </div>
    </div>
  );
}
