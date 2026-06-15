import { useState } from "react";
import { api } from "../../api/client";
import type { VisitHeader } from "../../types";

interface Props {
  entity: Record<string, unknown>;
  header: VisitHeader | null;
  onDrawDay?: () => Promise<void>;
  onUpdate: (entity: Record<string, unknown>, header: VisitHeader) => void;
  embedded?: boolean;
}

export default function DayPanel({ entity, header, onDrawDay, onUpdate, embedded }: Props) {
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const run = async (
    action: () => Promise<{ entity: Record<string, unknown>; header: VisitHeader }>,
  ) => {
    setLoading("run");
    setError(null);
    try {
      const res = await action();
      onUpdate(res.entity, res.header);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Action failed");
    } finally {
      setLoading(null);
    }
  };

  const drawDay = async () => {
    if (!onDrawDay) return;
    setLoading("draw");
    setError(null);
    try {
      await onDrawDay();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Draw failed");
    } finally {
      setLoading(null);
    }
  };

  const content = (
    <>
      <div className="section-title mb-3">Journal day</div>

      {error && <p className="text-xs text-red-400 mb-2">{error}</p>}

      <div className="space-y-2">
        <button
          type="button"
          className="btn btn-primary w-full"
          disabled={Boolean(loading) || Boolean(header?.visit_complete)}
          onClick={drawDay}
        >
          Draw day&apos;s cards (2)
        </button>

        <button
          type="button"
          className="btn w-full"
          disabled={Boolean(loading) || !entity.last_cards}
          onClick={() => run(() => api.recordCityChange())}
        >
          Check off city change
        </button>

        <button
          type="button"
          className="btn w-full"
          disabled={Boolean(loading)}
          onClick={() => run(() => api.advanceVisitDay())}
        >
          Advance to next day
        </button>
      </div>

      {(entity.last_adjective || entity.last_location_event) && (
        <div className="mt-4 p-2 rounded-lg bg-elevated/50 border border-border text-xs">
          <div className="text-muted mb-1">Current prompt</div>
          <div className="font-medium">
            {String(entity.last_adjective)} · {String(entity.last_location_event)}
          </div>
        </div>
      )}
    </>
  );

  if (embedded) return <div>{content}</div>;
  return <div className="panel p-3">{content}</div>;
}
