import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import type { Shortcut } from "../../types";

const GROUPS: { title: string; ids: string[] }[] = [
  {
    title: "Dungeon",
    ids: [
      "draw_room",
      "draw_journal",
      "draw_room_journal",
      "draw_enemy",
      "sanctuary_check",
      "navigate",
      "boss_entry",
    ],
  },
  {
    title: "Trials & Ember",
    ids: ["draw_starting_trials", "draw_trial", "trials_help", "ember_help"],
  },
  {
    title: "Tables",
    ids: ["roll_trap", "roll_loot"],
  },
  {
    title: "Character",
    ids: [
      "character_gift",
      "character_armour",
      "character_setup",
      "roll_melee_weapon",
      "roll_ranged_weapon",
    ],
  },
  {
    title: "Rules",
    ids: ["dungeon_rules", "checks_help"],
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
        <div className="grid grid-cols-1 gap-1.5 p-2 pt-0">
          {items.map((s) => (
            <button
              key={s.id}
              type="button"
              className="btn-ghost text-left text-xs px-2 py-1.5 border border-transparent hover:border-border rounded-md"
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

  const groups = GROUPS.map((g) => ({
    ...g,
    items: g.ids.map((id) => byId[id]).filter(Boolean) as Shortcut[],
  })).filter((g) => g.items.length > 0);

  const ungrouped = shortcuts.filter((s) => !GROUPS.some((g) => g.ids.includes(s.id)));

  const content = (
    <>
      {!embedded && <div className="section-title mb-3">Shortcuts</div>}
      <div className="space-y-2">
        {groups.map((g, i) => (
          <CollapsibleGroup
            key={g.title}
            title={g.title}
            items={g.items}
            loading={loading}
            onRun={onRun}
            defaultOpen={i === 0}
          />
        ))}
        {ungrouped.length > 0 && (
          <CollapsibleGroup title="More" items={ungrouped} loading={loading} onRun={onRun} defaultOpen={false} />
        )}
      </div>
    </>
  );

  if (embedded) return <div>{content}</div>;
  return <div className="panel p-3">{content}</div>;
}
