import { useState } from "react";
import { AlertCircle, Check, Loader2 } from "lucide-react";
import PlayingCard from "../brambletrek/PlayingCard";
import type { ExplorationEvent, PendingExploration } from "../../types";

interface Props {
  exploration: PendingExploration | null;
  onApply: (index: number) => Promise<{ summary?: string }>;
  onFinish: () => Promise<void>;
  onDiscard: () => Promise<void>;
  embedded?: boolean;
}

function EventRow({
  ev,
  isLast,
  onApply,
}: {
  ev: ExplorationEvent;
  isLast: boolean;
  onApply: (index: number) => Promise<{ summary?: string }>;
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resultText, setResultText] = useState<string | null>(null);
  const active = !ev.applied && ev.can_apply;

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await onApply(ev.index);
      if (res.summary) setResultText(res.summary);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Apply failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex gap-3">
      <div className="flex flex-col items-center pt-1">
        <div
          className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 ${
            ev.applied ? "bg-moss/20 text-moss" : active ? "bg-accent/20 text-accent ring-2 ring-accent/40" : "bg-elevated text-muted border border-border"
          }`}
        >
          {ev.applied ? <Check className="w-3 h-3" /> : <span className="text-[10px] font-bold">{ev.index + 1}</span>}
        </div>
        {!isLast && <div className="w-px flex-1 min-h-[0.75rem] bg-border mt-1" />}
      </div>
      <div className={`flex-1 min-w-0 mb-3 rounded-xl border p-3 ${ev.applied ? "border-moss/30" : active ? "border-accent/40" : "border-border"}`}>
        <div className="flex gap-3">
          <PlayingCard card={ev.card} applied={ev.applied} active={active} />
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium truncate">{ev.label || ev.card}</div>
            <div className="text-[11px] text-muted mt-0.5">{ev.preview}</div>
            {ev.needs_hollow && <span className="text-[10px] text-accent">(Hollow)</span>}
            {ev.needs_item && !ev.item_card && <span className="text-[10px] text-muted ml-1">(Item on apply)</span>}
            {ev.item_label && <div className="text-[11px] text-moss mt-1">Item: {ev.item_label}</div>}
            {resultText && <p className="text-[11px] mt-2 text-gray-300">{resultText}</p>}
            {error && (
              <p className="text-[11px] mt-1 text-red-300 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                {error}
              </p>
            )}
            {active && (
              <button type="button" className="btn btn-primary mt-2 text-xs py-1 px-2" disabled={loading} onClick={run}>
                {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : "Apply"}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ExplorationPanel({ exploration, onApply, onFinish, onDiscard, embedded }: Props) {
  const [footerLoading, setFooterLoading] = useState<string | null>(null);
  const [footerError, setFooterError] = useState<string | null>(null);

  if (!exploration?.events?.length) {
    return (
      <div className="text-sm text-muted p-2">
        No exploration draws yet. Use <strong>Exploration day</strong> in Shortcuts.
      </div>
    );
  }

  const appliedCount = exploration.events.filter((e) => e.applied).length;
  const total = exploration.events.length;

  const runFooter = async (kind: string, action: () => Promise<void>) => {
    setFooterLoading(kind);
    setFooterError(null);
    try {
      await action();
    } catch (e) {
      setFooterError(e instanceof Error ? e.message : "Failed");
    } finally {
      setFooterLoading(null);
    }
  };

  const content = (
    <div className="flex flex-col min-h-0">
      <div className="mb-3 flex justify-between text-xs">
        <span className="section-title">Today&apos;s draws</span>
        <span className="text-accent tabular-nums">{appliedCount}/{total}</span>
      </div>
      {exploration.events.map((ev, i) => (
        <EventRow key={ev.index} ev={ev} isLast={i === exploration.events.length - 1} onApply={onApply} />
      ))}
      {footerError && <p className="text-xs text-red-300">{footerError}</p>}
      <div className="flex gap-2 mt-2 pt-3 border-t border-border">
        <button type="button" className="btn btn-primary flex-1" disabled={!!footerLoading} onClick={() => runFooter("finish", onFinish)}>
          Finish day
        </button>
        <button type="button" className="btn-ghost flex-1 border border-border rounded-lg" disabled={!!footerLoading} onClick={() => runFooter("discard", onDiscard)}>
          Discard
        </button>
      </div>
    </div>
  );
  return embedded ? content : <div className="panel p-3">{content}</div>;
}
