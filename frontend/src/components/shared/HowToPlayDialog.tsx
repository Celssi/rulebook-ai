import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { api } from "../../api/client";
import AppDialog from "./AppDialog";

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

  if (gameId === "40k") return null;

  return (
    <AppDialog
      open={open}
      title="Näin pelaat"
      subtitle={gameLabel}
      onClose={onClose}
      closeLabel="Sulje"
    >
      <div className="flex-1 overflow-y-auto px-5 py-4 text-sm leading-relaxed prose prose-invert prose-sm max-w-none">
        {loading && <p className="text-muted">Ladataan…</p>}
        {error && <p className="text-red-400">{error}</p>}
        {!loading && !error && markdown && <ReactMarkdown>{markdown}</ReactMarkdown>}
      </div>
    </AppDialog>
  );
}
