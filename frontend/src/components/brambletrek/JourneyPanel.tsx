import { Check, Circle, Sparkles } from "lucide-react";
import { api } from "../../api/client";
import PlayingCard from "./PlayingCard";
import type { JourneyEvent, PendingJourney } from "../../types";

interface Props {
  journey: PendingJourney | null;
  onChange: () => void;
  embedded?: boolean;
}

function EventRow({
  ev,
  isLast,
  onChange,
}: {
  ev: JourneyEvent;
  isLast: boolean;
  onChange: () => void;
}) {
  const active = !ev.applied && ev.can_apply;

  return (
    <div className="flex gap-3">
      <div className="flex flex-col items-center pt-1">
        <div
          className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 ${
            ev.applied
              ? "bg-moss/20 text-moss"
              : active
                ? "bg-accent/20 text-accent ring-2 ring-accent/40"
                : "bg-elevated text-muted border border-border"
          }`}
        >
          {ev.applied ? (
            <Check className="w-3 h-3" />
          ) : (
            <span className="text-[10px] font-bold">{ev.index + 1}</span>
          )}
        </div>
        {!isLast && <div className="w-px flex-1 min-h-[0.75rem] bg-border mt-1" />}
      </div>

      <div
        className={`flex-1 min-w-0 mb-3 rounded-xl border p-3 transition-colors ${
          ev.applied
            ? "border-moss/30 bg-moss-muted/10"
            : active
              ? "border-accent/40 bg-accent-muted/10"
              : "border-border bg-surface/40"
        }`}
      >
        <div className="flex gap-3">
          <PlayingCard card={ev.card} applied={ev.applied} active={active} />
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <div className="text-[10px] uppercase tracking-wide text-muted mb-0.5">
                  {ev.zone}
                </div>
                {ev.label ? (
                  <h4 className="text-sm font-medium leading-snug">{ev.label}</h4>
                ) : (
                  <h4 className="text-sm font-medium">Event {ev.index + 1}</h4>
                )}
              </div>
              {ev.applied && (
                <span className="badge-moss shrink-0 text-[10px]">
                  <Check className="w-3 h-3" /> Done
                </span>
              )}
            </div>

            {ev.preview && ev.preview !== "—" && (
              <div className="mt-2 inline-flex items-center px-2 py-0.5 rounded-md bg-elevated border border-border text-[11px] text-muted">
                {ev.preview}
              </div>
            )}

            {ev.item_card && (
              <div className="mt-2 text-xs text-accent flex items-center gap-1">
                <Sparkles className="w-3 h-3 shrink-0" />
                <span>{ev.item_label || ev.item_card}</span>
              </div>
            )}

            {!ev.applied && (
              <button
                type="button"
                className="btn btn-primary w-full mt-3 text-xs"
                disabled={!ev.can_apply}
                onClick={async () => {
                  await api.applyJourney(ev.index);
                  onChange();
                }}
              >
                {active ? "Apply to sheet" : "Apply previous first"}
              </button>
            )}
            {ev.applied && ev.needs_item && !ev.item_card && (
              <button
                type="button"
                className="btn w-full mt-3 text-xs"
                onClick={async () => {
                  await api.drawJourneyItem(ev.index);
                  onChange();
                }}
              >
                Draw item
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function JourneyPanel({ journey, onChange, embedded }: Props) {
  if (!journey?.events?.length) {
    return (
      <div
        className={
          embedded ? "text-sm text-muted py-8 text-center" : "panel p-6 text-sm text-muted text-center"
        }
      >
        <Circle className="w-8 h-8 mx-auto mb-2 opacity-30" />
        No journey draws yet. Use the Shortcuts tab or ask for a journey day.
      </div>
    );
  }

  const appliedCount = journey.events.filter((e) => e.applied).length;
  const total = journey.events.length;
  const progress = total > 0 ? (appliedCount / total) * 100 : 0;

  const content = (
    <div className="flex flex-col min-h-0">
      <div className="mb-4">
        <div className="flex items-center justify-between gap-2 mb-2">
          <div className="section-title">Today&apos;s draws</div>
          <span className="text-xs font-medium tabular-nums text-accent">
            {appliedCount}/{total} resolved
          </span>
        </div>
        <div className="stat-bar h-1.5">
          <div
            className="stat-bar-fill bg-accent"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="text-[11px] text-muted mt-2 leading-relaxed">
          Resolve in order. Apply each card before the next — pause for combat between events.
        </p>
      </div>

      <div className="space-y-0">
        {journey.events.map((ev, i) => (
          <EventRow
            key={ev.index}
            ev={ev}
            isLast={i === journey.events.length - 1}
            onChange={onChange}
          />
        ))}
      </div>

      <div className="flex gap-2 mt-2 pt-3 border-t border-border sticky bottom-0 bg-panel/95 backdrop-blur-sm">
        <button
          type="button"
          className="btn btn-primary flex-1"
          onClick={async () => {
            await api.finishJourney();
            onChange();
          }}
        >
          Finish day
        </button>
        <button
          type="button"
          className="btn-ghost flex-1 border border-border rounded-lg py-2"
          onClick={async () => {
            await api.discardJourney();
            onChange();
          }}
        >
          Discard
        </button>
      </div>
    </div>
  );

  if (embedded) return content;
  return <div className="panel p-3">{content}</div>;
}
