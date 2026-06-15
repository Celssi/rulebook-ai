import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { X } from "lucide-react";
import { api } from "../../api/client";

interface Props {
  open: boolean;
  gameId: string;
  gameLabel: string;
  onClose: () => void;
}

export default function HowToPlayDialog({ open, gameId, gameLabel, onClose }: Props) {
  const [markdown, setMarkdown] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open || gameId === "40k") return;

    let cancelled = false;
    setLoading(true);
    setError(null);
    setMarkdown(null);

    api
      .getHowToPlay(gameId)
      .then((data) => {
        if (!cancelled) setMarkdown(data.markdown);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Ohjetta ei voitu ladata");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [open, gameId]);

  if (!open || gameId === "40k") return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
      onClick={onClose}
      role="presentation"
    >
      <div
        className="panel-elevated w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-labelledby="how-to-play-title"
        aria-modal="true"
      >
        <header className="flex items-start justify-between gap-3 px-5 py-4 border-b border-border shrink-0">
          <div className="min-w-0">
            <h2 id="how-to-play-title" className="text-lg font-semibold">
              Näin pelaat
            </h2>
            <p className="text-sm text-muted truncate">{gameLabel}</p>
          </div>
          <button
            type="button"
            className="btn-ghost p-2 rounded-lg shrink-0"
            onClick={onClose}
            aria-label="Sulje"
          >
            <X className="w-4 h-4" />
          </button>
        </header>

        <div className="flex-1 overflow-y-auto px-5 py-4 text-sm leading-relaxed prose prose-invert prose-sm max-w-none">
          {loading && <p className="text-muted">Ladataan…</p>}
          {error && <p className="text-red-400">{error}</p>}
          {!loading && !error && markdown && <ReactMarkdown>{markdown}</ReactMarkdown>}
        </div>
      </div>
    </div>
  );
}
