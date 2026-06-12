import { Heart, Package, Settings, Smile } from "lucide-react";
import type { CharacterHeader } from "../../types";

interface Props {
  header: CharacterHeader | null;
  gameLabel: string;
  onOpenSettings: () => void;
}

function StatChip({
  icon: Icon,
  value,
  color,
}: {
  icon: typeof Heart;
  value: number;
  color: string;
}) {
  const pct = Math.min(100, Math.max(0, (value / 20) * 100));
  return (
    <div className="flex items-center gap-1.5 min-w-[4.5rem]" title={`${value}/20`}>
      <Icon className="w-3.5 h-3.5 shrink-0" style={{ color }} />
      <div className="flex-1 min-w-0">
        <div className="text-xs font-semibold tabular-nums">{value}</div>
        <div className="stat-bar mt-0.5">
          <div className="stat-bar-fill" style={{ width: `${pct}%`, backgroundColor: color }} />
        </div>
      </div>
    </div>
  );
}

export default function StatsBar({ header, gameLabel, onOpenSettings }: Props) {
  return (
    <header className="flex items-center gap-3 px-4 py-2.5 border-b border-border bg-panel shrink-0">
      <div className="font-semibold text-sm whitespace-nowrap text-accent">{gameLabel}</div>

      {header && (
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <div className="min-w-0 hidden sm:block">
            <div className="font-medium text-sm truncate">{header.name || "Unnamed"}</div>
            {header.legacy && (
              <div className="text-xs text-muted truncate">{header.legacy}</div>
            )}
          </div>

          <div className="flex items-center gap-4 ml-auto shrink-0">
            <StatChip icon={Heart} value={header.health} color="#e05a5a" />
            <StatChip icon={Smile} value={header.morale} color="#6b9fff" />
            <StatChip icon={Package} value={header.supplies} color="#d4a24c" />
            <span className="text-xs text-muted whitespace-nowrap hidden md:inline">
              Day {header.journey_day}
            </span>
            {header.in_aldwund && <span className="badge-accent">Depths</span>}
          </div>
        </div>
      )}

      {!header && <div className="flex-1" />}

      <button
        type="button"
        className="btn-ghost p-2 rounded-lg shrink-0"
        onClick={onOpenSettings}
        title="Settings"
      >
        <Settings className="w-4 h-4" />
      </button>
    </header>
  );
}
