import { useEffect, useState } from "react";
import DeckPanel from "../shared/DeckPanel";
import JourneyPanel from "../brambletrek/JourneyPanel";
import BrambletrekShortcutGroups from "../brambletrek/ShortcutGroups";
import DayPanel from "../sansibilia/DayPanel";
import ShortcutList from "../shared/ShortcutList";
import AshesShortcutGroups from "../ashes/ShortcutGroups";
import AilmentPanel from "../apothecaria/AilmentPanel";
import ApothecariaShortcutGroups from "../apothecaria/ShortcutGroups";
import GameStatePanel from "../warhammer40k/GameStatePanel";
import type { CottageHeader, PendingJourney, Shortcut, VisitHeader } from "../../types";

type BrambletrekTab = "journey" | "deck" | "shortcuts";
type SansibiliaTab = "day" | "deck" | "shortcuts";
type LighthouseTab = "deck" | "shortcuts";
type ApothecariaTab = "ailment" | "deck" | "shortcuts";

interface Props {
  gameId: string;
  hasCharacterSheet: boolean;
  hasGameState: boolean;
  journey: PendingJourney | null;
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
  onDeckAction: (formatted: string) => void;
  onShortcut: (id: string) => void;
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
  onDeckAction,
  onShortcut,
  onDayDraw,
  onVisitUpdate,
  onCottageUpdate,
  onApothecariaForage,
  on40kUpdate,
}: Props) {
  const hasJourney = Boolean(journey?.events?.length);
  const [btTab, setBtTab] = useState<BrambletrekTab>("journey");
  const [ssTab, setSsTab] = useState<SansibiliaTab>("day");
  const [lhTab, setLhTab] = useState<LighthouseTab>("shortcuts");
  const [apoTab, setApoTab] = useState<ApothecariaTab>("ailment");

  useEffect(() => {
    if (hasJourney) setBtTab("journey");
  }, [hasJourney]);

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
