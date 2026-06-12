import { useState } from "react";
import { Dices, Layers, RotateCcw } from "lucide-react";
import { api } from "../../api/client";

interface Props {
  remaining: number;
  cardSource: string;
  onAction: (formatted: string) => void;
  embedded?: boolean;
}

export default function DeckPanel({ remaining, cardSource, onAction, embedded }: Props) {
  const [rollExpr, setRollExpr] = useState("d6");
  const [reportCard, setReportCard] = useState("");
  const physical = cardSource === "physical";

  const content = (
    <>
      <div className="flex items-center justify-between mb-3">
        <div className="section-title">Table deck</div>
        <span className="badge bg-elevated text-muted border border-border">
          <Layers className="w-3 h-3" />
          {remaining} left
        </span>
      </div>

      <div className="flex gap-2 mb-3">
        <button
          type="button"
          className="btn btn-primary flex-1"
          onClick={async () => {
            const res = await api.drawDeck(1);
            onAction(res.formatted);
          }}
        >
          Draw 1
        </button>
        <button
          type="button"
          className="btn flex-1 flex items-center justify-center gap-1"
          onClick={async () => {
            await api.resetDeck();
          }}
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Reset
        </button>
      </div>

      {physical && (
        <div className="flex gap-2 mb-3">
          <input
            className="input flex-1"
            placeholder="Queen of Hearts"
            value={reportCard}
            onChange={(e) => setReportCard(e.target.value)}
          />
          <button
            type="button"
            className="btn"
            onClick={async () => {
              if (!reportCard.trim()) return;
              const res = await api.reportCard(reportCard);
              onAction(res.formatted);
              setReportCard("");
            }}
          >
            Record
          </button>
        </div>
      )}

      <div className="flex gap-2">
        <input
          className="input flex-1 font-mono text-xs"
          value={rollExpr}
          onChange={(e) => setRollExpr(e.target.value)}
          placeholder="d6, 2d6+1…"
        />
        <button
          type="button"
          className="btn flex items-center gap-1"
          onClick={async () => {
            const res = await api.rollDice(rollExpr);
            onAction(res.formatted);
          }}
        >
          <Dices className="w-3.5 h-3.5" />
          Roll
        </button>
      </div>
    </>
  );

  if (embedded) return <div>{content}</div>;
  return <div className="panel p-3">{content}</div>;
}
