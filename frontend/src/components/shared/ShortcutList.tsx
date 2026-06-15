import type { Shortcut } from "../../types";

interface Props {
  shortcuts: Shortcut[];
  loading: string | null;
  onRun: (id: string) => void;
  embedded?: boolean;
  title?: string;
}

export default function ShortcutList({
  shortcuts,
  loading,
  onRun,
  embedded,
  title = "Shortcuts",
}: Props) {
  const content = (
    <>
      <div className="section-title mb-3">{title}</div>
      <div className="grid gap-2">
        {shortcuts.map((s) => (
          <button
            key={s.id}
            type="button"
            className="btn text-left text-sm py-2 px-3"
            disabled={loading === s.id}
            onClick={() => onRun(s.id)}
          >
            {loading === s.id ? "…" : s.label}
          </button>
        ))}
      </div>
    </>
  );

  if (embedded) return <div>{content}</div>;
  return <div className="panel p-3">{content}</div>;
}
