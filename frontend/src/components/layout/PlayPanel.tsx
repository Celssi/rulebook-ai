import { useEffect, useState } from "react";
import DeckPanel from "../brambletrek/DeckPanel";
import JourneyPanel from "../brambletrek/JourneyPanel";
import ShortcutGroups from "../brambletrek/ShortcutGroups";
import GameStatePanel from "../warhammer40k/GameStatePanel";
import type { PendingJourney, Shortcut } from "../../types";

type Tab = "journey" | "deck" | "shortcuts";

interface Props {
  hasCharacterSheet: boolean;
  hasGameState: boolean;
  journey: PendingJourney | null;
  shortcuts: Shortcut[];
  shortcutLoading: string | null;
  deckRemaining: number;
  cardSource: string;
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
  on40kUpdate: (game_state: Record<string, unknown>, summary: string) => void;
}

export default function PlayPanel({
  hasCharacterSheet,
  hasGameState,
  journey,
  shortcuts,
  shortcutLoading,
  deckRemaining,
  cardSource,
  state40k,
  onJourneyApply,
  onJourneyDrawItem,
  onJourneyFinish,
  onJourneyDiscard,
  onDeckAction,
  onShortcut,
  on40kUpdate,
}: Props) {
  const hasJourney = Boolean(journey?.events?.length);
  const [tab, setTab] = useState<Tab>("journey");

  useEffect(() => {
    if (hasJourney) setTab("journey");
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

  if (!hasCharacterSheet) return null;

  const tabs: { id: Tab; label: string }[] = [
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
            className={tab === t.id ? "tab-btn-active" : "tab-btn hover:text-gray-200"}
            onClick={() => setTab(t.id)}
          >
            {t.label}
            {t.id === "journey" && hasJourney && (
              <span className="ml-1 inline-block w-1.5 h-1.5 rounded-full bg-accent" />
            )}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-3 min-h-0">
        {tab === "journey" && (
          <JourneyPanel
            journey={journey}
            onApply={onJourneyApply}
            onDrawItem={onJourneyDrawItem}
            onFinish={onJourneyFinish}
            onDiscard={onJourneyDiscard}
            embedded
          />
        )}
        {tab === "deck" && (
          <DeckPanel
            remaining={deckRemaining}
            cardSource={cardSource}
            onAction={onDeckAction}
            embedded
          />
        )}
        {tab === "shortcuts" && (
          <ShortcutGroups
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
