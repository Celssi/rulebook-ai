import type { HollowState } from "../../types";

interface Props {
  hollow: HollowState | null;
  onMove: (row: number, col: number) => Promise<void>;
  loading?: boolean;
}

export default function HollowPanel({ hollow, onMove, loading }: Props) {
  if (!hollow?.grid?.length) {
    return (
      <div className="card p-4 text-sm text-muted">
        Not in the Misty Hollow. Use <strong>Enter Misty Hollow</strong> or investigate a (Hollow) tag.
      </div>
    );
  }

  return (
    <div className="card p-3 space-y-3">
      <div className="flex items-center justify-between gap-2 text-xs">
        <span className="font-medium text-accent">Misty Hollow</span>
        <span className="text-muted">
          Fragments {hollow.memory_fragments}/3
          {hollow.awareness && <span className="ml-2 badge-accent">Awareness</span>}
        </span>
      </div>
      {hollow.entry_prompt && (
        <p className="text-[11px] text-muted line-clamp-2">{hollow.entry_prompt}</p>
      )}
      <div className="grid gap-1" style={{ gridTemplateColumns: `repeat(${hollow.grid[0]?.length || 4}, minmax(0, 1fr))` }}>
        {hollow.grid.flat().map((cell) => {
          const isMarker =
            cell.row === hollow.marker_row && cell.col === hollow.marker_col;
          const canMove = hollow.adjacent?.some(
            (a) => a.row === cell.row && a.col === cell.col
          );
          return (
            <button
              key={`${cell.row}-${cell.col}`}
              type="button"
              disabled={loading || !canMove || cell.revealed}
              onClick={() => onMove(cell.row, cell.col)}
              className={`aspect-[3/4] rounded border text-[9px] p-1 truncate ${
                cell.revealed
                  ? "border-moss/40 bg-moss-muted/20"
                  : canMove
                    ? "border-accent/50 bg-accent-muted/10 hover:bg-accent-muted/20"
                    : "border-border bg-elevated/50"
              } ${isMarker ? "ring-2 ring-accent" : ""}`}
              title={cell.revealed ? cell.card : "Hidden"}
            >
              {cell.revealed ? cell.card?.split(" ")[0] : "##"}
            </button>
          );
        })}
      </div>
    </div>
  );
}
