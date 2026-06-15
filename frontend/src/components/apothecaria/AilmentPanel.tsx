import { useEffect, useState } from "react";
import { api } from "../../api/client";
import type { CottageHeader } from "../../types";

interface Props {
  entity: Record<string, unknown>;
  header: CottageHeader | null;
  options: {
    locales?: { id: string; label: string }[];
  } | null;
  onUpdate: (entity: Record<string, unknown>, header: CottageHeader) => void;
  onForage?: () => Promise<void>;
  embedded?: boolean;
}

export default function AilmentPanel({ entity, header, options, onUpdate, onForage, embedded }: Props) {
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [locale, setLocale] = useState(String(header?.current_locale || entity.current_locale || "glimmerwood"));

  useEffect(() => {
    setLocale(String(header?.current_locale || entity.current_locale || "glimmerwood"));
  }, [header?.current_locale, entity.current_locale]);

  const run = async (
    key: string,
    action: () => Promise<{ entity: Record<string, unknown>; header: CottageHeader }>,
  ) => {
    setLoading(key);
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

  const phase = String(header?.phase || entity.phase || "idle");
  const hasAilment = Boolean(header?.ailment_name || entity.ailment_name);
  const locales = options?.locales || [];

  const content = (
    <>
      <div className="section-title mb-3">Ailment & foraging</div>

      {error && <p className="text-xs text-red-400 mb-2">{error}</p>}

      {hasAilment && (
        <div className="text-xs p-2 rounded-lg bg-elevated/60 border border-border mb-3">
          <div className="font-medium">{String(header?.ailment_name || entity.ailment_name)}</div>
          <div className="text-muted mt-1 flex flex-wrap gap-2">
            {header?.ailment_timer != null && <span>Timer {header.ailment_timer}</span>}
            <span>Points {header?.foraging_points ?? 0}</span>
            {header?.hunting_reagent && (
              <span>
                Hunting {header.hunting_reagent} (FV {header.hunting_fv})
              </span>
            )}
            {(header?.inventory_count ?? 0) > 0 && <span>Reagents {header?.inventory_count}</span>}
            {(header?.potion_poison ?? 0) > 0 && <span>Poison {header?.potion_poison}</span>}
            {(header?.potion_sweet ?? 0) > 0 && <span>Sweet {header?.potion_sweet}</span>}
          </div>
        </div>
      )}

      <div className="space-y-2">
        {hasAilment && locales.length > 0 && (
          <div className="flex gap-2">
            <select
              className="select text-xs py-1 flex-1 min-w-0"
              value={locale}
              onChange={(e) => setLocale(e.target.value)}
            >
              {locales.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.label}
                </option>
              ))}
            </select>
            <button
              type="button"
              className="btn text-xs shrink-0"
              disabled={Boolean(loading) || locale === (header?.current_locale || entity.current_locale)}
              onClick={() => run("locale", () => api.changeApothecariaLocale(locale))}
            >
              Go
            </button>
          </div>
        )}

        {hasAilment && (
          <button
            type="button"
            className="btn btn-primary w-full"
            disabled={Boolean(loading)}
            onClick={async () => {
              if (!onForage) return;
              setLoading("forage");
              setError(null);
              try {
                await onForage();
              } catch (e) {
                setError(e instanceof Error ? e.message : "Forage failed");
              } finally {
                setLoading(null);
              }
            }}
          >
            Forage (draw event)
          </button>
        )}

        {hasAilment && (
          <button
            type="button"
            className="btn w-full"
            disabled={Boolean(loading)}
            onClick={() => run("potion", () => api.completeApothecariaPotion())}
          >
            Complete potion
          </button>
        )}

        {phase === "downtime" && (
          <button
            type="button"
            className="btn w-full"
            disabled={Boolean(loading)}
            onClick={() => run("downtime", () => api.advanceApothecariaDowntime())}
          >
            Spend downtime ({header?.downtime_timer ?? 0} left)
          </button>
        )}

        {!hasAilment && phase !== "downtime" && (
          <p className="text-xs text-muted">Draw a new patient from Shortcuts, or advance the calendar below.</p>
        )}

        <button
          type="button"
          className="btn w-full"
          disabled={Boolean(loading)}
          onClick={() => run("week", () => api.advanceApothecariaWeek())}
        >
          Advance week (Wk {header?.week ?? 1}, {header?.season ?? "spring"})
        </button>
      </div>
    </>
  );

  if (embedded) return <div>{content}</div>;
  return <div className="panel p-3">{content}</div>;
}
