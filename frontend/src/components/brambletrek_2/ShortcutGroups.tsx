import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import type { Shortcut } from "../../types";

const GROUPS: { title: string; ids: string[] }[] = [
  {
    title: "Woods",
    ids: ["exploration_day", "how_did_i_get_here", "item_draw"],
  },
  {
    title: "Misty Hollow",
    ids: ["hollow_enter", "hollow_flip", "hollow_escape_attempt"],
  },
  {
    title: "Combat & recovery",
    ids: [
      "combat_setup",
      "overcome_odds",
      "recovery_health",
      "recovery_morale",
      "recovery_supplies",
    ],
  },
  {
    title: "Reference",
    ids: ["start_playing", "legacy_overview", "random_legacy"],
  },
];

interface Props {
  shortcuts: Shortcut[];
  loading: string | null;
  onRun: (id: string) => void;
  embedded?: boolean;
}

function CollapsibleGroup({
  title,
  items,
  loading,
  onRun,
  defaultOpen,
}: {
  title: string;
  items: Shortcut[];
  loading: string | null;
  onRun: (id: string) => void;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen ?? true);
  if (!items.length) return null;
  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <button
        type="button"
        className="w-full flex items-center gap-2 px-3 py-2 text-xs font-medium text-muted hover:bg-elevated transition-colors"
        onClick={() => setOpen(!open)}
      >
        {open ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
        {title}
        <span className="ml-auto text-[10px] opacity-60">{items.length}</span>
      </button>
      {open && (
        <div className="grid grid-cols-2 gap-1.5 p-2 pt-0">
          {items.map((s) => (
            <button
              key={s.id}
              type="button"
              className="btn-ghost text-left text-xs px-2 py-1.5 border border-transparent hover:border-border rounded-md truncate"
              disabled={loading === s.id}
              onClick={() => onRun(s.id)}
            >
              {loading === s.id ? "…" : s.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ShortcutGroups({ shortcuts, loading, onRun, embedded }: Props) {
  const byId = Object.fromEntries(shortcuts.map((s) => [s.id, s]));
  const content = (
    <div className={embedded ? "space-y-2" : "space-y-2 p-2"}>
      {GROUPS.map((g) => (
        <CollapsibleGroup
          key={g.title}
          title={g.title}
          items={g.ids.map((id) => byId[id]).filter(Boolean) as Shortcut[]}
          loading={loading}
          onRun={onRun}
          defaultOpen={g.title === "Woods"}
        />
      ))}
    </div>
  );
  if (embedded) return content;
  return <div className="card overflow-hidden">{content}</div>;
}
