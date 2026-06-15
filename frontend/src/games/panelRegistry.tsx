import GmSoloPanel from "../components/gm_solo/GmSoloPanel";
import Dnd5eShortcutGroups from "../components/dnd5e/Dnd5eShortcutGroups";
import ShortcutList from "../components/shared/ShortcutList";
import type { GmSoloGameId } from "./gmSoloGames";

export interface GmSoloPlayPanelProps {
  gameId: GmSoloGameId;
  shortcuts: { id: string; label: string }[];
  shortcutLoading: string | null;
  onShortcut: (id: string, params?: Record<string, unknown>) => void;
}

export function GmSoloPlayPanel({
  gameId,
  shortcuts,
  shortcutLoading,
  onShortcut,
}: GmSoloPlayPanelProps) {
  return (
    <div className="flex flex-col h-full min-h-0">
      <div className="px-4 py-2.5 border-b border-border section-title">Shortcuts</div>
      <div className="flex-1 overflow-y-auto p-3 min-h-0">
        {gameId === "dnd5e" ? (
          <Dnd5eShortcutGroups
            shortcuts={shortcuts}
            loading={shortcutLoading}
            onRun={onShortcut}
            embedded
          />
        ) : (
          <ShortcutList shortcuts={shortcuts} loading={shortcutLoading} onRun={onShortcut} embedded />
        )}
      </div>
    </div>
  );
}

export const GM_SOLO_CHARACTER_PANEL = GmSoloPanel;

export const GM_SOLO_PLAY_PANEL = GmSoloPlayPanel;

export function isGmSoloPanelGame(gameId: string): gameId is GmSoloGameId {
  return ["outgunned", "tor", "coriolis", "cosmere", "mlp", "dnd5e"].includes(gameId);
}
