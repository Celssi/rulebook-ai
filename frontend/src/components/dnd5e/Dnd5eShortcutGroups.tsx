import { useState } from "react";
import type { Shortcut } from "../../types";

interface Props {
  shortcuts: Shortcut[];
  loading: string | null;
  onRun: (id: string, params?: Record<string, unknown>) => void;
  embedded?: boolean;
}

export default function Dnd5eShortcutGroups({ shortcuts, loading, onRun, embedded }: Props) {
  const [targetAc, setTargetAc] = useState("");

  const content = (
    <div className="grid gap-2">
      {shortcuts.map((s) => {
        if (s.id === "attack_roll") {
          return (
            <div key={s.id} className="flex gap-2 items-stretch">
              <label className="flex-1 min-w-0">
                <span className="sr-only">Target AC</span>
                <input
                  type="number"
                  min={1}
                  max={40}
                  placeholder="Target AC"
                  className="input w-full text-sm py-2 px-3 h-full"
                  value={targetAc}
                  onChange={(e) => setTargetAc(e.target.value)}
                />
              </label>
              <button
                type="button"
                className="btn text-left text-sm py-2 px-3 shrink-0"
                disabled={loading === s.id}
                onClick={() => {
                  const ac = targetAc.trim() ? Number(targetAc) : undefined;
                  onRun(s.id, ac != null && !Number.isNaN(ac) ? { target_ac: ac } : undefined);
                }}
              >
                {loading === s.id ? "…" : s.label}
              </button>
            </div>
          );
        }
        return (
          <button
            key={s.id}
            type="button"
            className="btn text-left text-sm py-2 px-3"
            disabled={loading === s.id}
            onClick={() => onRun(s.id)}
          >
            {loading === s.id ? "…" : s.label}
          </button>
        );
      })}
    </div>
  );

  if (embedded) return <div>{content}</div>;
  return <div className="panel p-3">{content}</div>;
}
