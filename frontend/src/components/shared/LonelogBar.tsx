import { useCallback, useEffect, useRef, useState } from "react";
import { ChevronDown, ChevronUp, GripHorizontal } from "lucide-react";

interface Props {
  lines: string[];
  collapsed?: boolean;
}

const STORAGE_KEY = "rulebook-ai.lonelog-height";
const DEFAULT_HEIGHT = 160;
const MIN_HEIGHT = 72;
const MAX_HEIGHT = 480;

function renderLine(line: string) {
  const t = line.trim();
  if (t.startsWith("=>"))
    return <span className="text-moss font-medium">{t.slice(2).trim()}</span>;
  if (t.startsWith("->"))
    return <span className="text-muted">{t.slice(2).trim()}</span>;
  if (t.startsWith("?"))
    return <span className="italic text-accent/80">{t}</span>;
  if (t.startsWith("d:"))
    return <span className="text-stat-morale">{t}</span>;
  if (t.startsWith("@"))
    return <span className="text-accent font-medium">{t}</span>;
  return <span className="text-gray-300">{t}</span>;
}

export default function LonelogBar({ lines, collapsed = false }: Props) {
  const [open, setOpen] = useState(!collapsed);
  const [height, setHeight] = useState(DEFAULT_HEIGHT);
  const heightRef = useRef(DEFAULT_HEIGHT);
  const dragRef = useRef<{ startY: number; startH: number } | null>(null);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const n = Number(saved);
        if (n >= MIN_HEIGHT && n <= MAX_HEIGHT) {
          setHeight(n);
          heightRef.current = n;
        }
      }
    } catch {
      /* ignore */
    }
  }, []);

  const persistHeight = useCallback((h: number) => {
    heightRef.current = h;
    try {
      localStorage.setItem(STORAGE_KEY, String(h));
    } catch {
      /* ignore */
    }
  }, []);

  const onResizeStart = (e: React.PointerEvent<HTMLDivElement>) => {
    e.preventDefault();
    dragRef.current = { startY: e.clientY, startH: heightRef.current };
    e.currentTarget.setPointerCapture(e.pointerId);
  };

  const onResizeMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!dragRef.current) return;
    const delta = dragRef.current.startY - e.clientY;
    const next = Math.min(
      MAX_HEIGHT,
      Math.max(MIN_HEIGHT, dragRef.current.startH + delta)
    );
    setHeight(next);
    heightRef.current = next;
  };

  const onResizeEnd = (e: React.PointerEvent<HTMLDivElement>) => {
    if (dragRef.current) persistHeight(heightRef.current);
    dragRef.current = null;
    e.currentTarget.releasePointerCapture(e.pointerId);
  };

  const visible = lines.filter((l) => {
    const t = l.trim();
    return t && !t.startsWith("#") && t !== "_Lonelog session log_" && t !== "```" && t !== "---";
  });

  return (
    <div className="panel shrink-0 border-t-0 rounded-none rounded-t-xl overflow-hidden">
      <button
        type="button"
        className="w-full px-4 py-2 flex items-center justify-between section-title border-b border-border hover:bg-elevated/50 transition-colors"
        onClick={() => setOpen((v) => !v)}
      >
        <span>Lonelog · {visible.length} lines</span>
        {open ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>

      {open && (
        <>
          <div
            role="separator"
            aria-orientation="horizontal"
            aria-label="Resize lonelog"
            className="h-2 flex items-center justify-center cursor-ns-resize bg-elevated/40 border-b border-border hover:bg-accent/10 active:bg-accent/20 touch-none select-none"
            onPointerDown={onResizeStart}
            onPointerMove={onResizeMove}
            onPointerUp={onResizeEnd}
            onPointerCancel={onResizeEnd}
          >
            <GripHorizontal className="w-4 h-4 text-muted/60" />
          </div>
          <div
            style={{ height }}
            className="overflow-y-auto p-4 text-xs space-y-1.5 font-mono leading-relaxed bg-surface/50"
          >
            {visible.length === 0 ? (
              <span className="text-muted">No log entries yet.</span>
            ) : (
              visible.map((line, i) => <div key={i}>{renderLine(line)}</div>)
            )}
          </div>
        </>
      )}
    </div>
  );
}
