import { api } from "../../api/client";

interface Props {
  gameState: Record<string, unknown>;
  options: Record<string, Record<string, string>>;
  summary: string;
  onUpdate: (state: Record<string, unknown>, summary: string) => void;
}

export default function GameStatePanel({ gameState, options, summary, onUpdate }: Props) {
  const patch = async (key: string, value: unknown) => {
    const next = { ...gameState, [key]: value };
    const res = await api.update40kState(next);
    onUpdate(res.game_state, res.summary);
  };

  return (
    <div className="flex flex-col h-full min-h-0 p-4 space-y-4 text-sm">
      <div className="section-title">Battle state</div>
      {summary && <p className="text-xs text-muted">{summary}</p>}
      <div>
        <div className="label mb-1">Your army</div>
        <select
          className="select"
          value={String(gameState.my_army || "")}
          onChange={(e) => patch("my_army", e.target.value)}
        >
          {Object.entries(options.armies || {}).map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </select>
      </div>
      <div>
        <div className="label mb-1">Opponent</div>
        <select
          className="select"
          value={String(gameState.opponent_army || "")}
          onChange={(e) => patch("opponent_army", e.target.value)}
        >
          {Object.entries(options.armies || {}).map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </select>
      </div>
      <div>
        <div className="label mb-1">Battle round</div>
        <input
          type="number"
          min={1}
          max={5}
          className="input"
          value={Number(gameState.battle_round || 1)}
          onChange={(e) => patch("battle_round", Number(e.target.value))}
        />
      </div>
      <div>
        <div className="label mb-1">Phase</div>
        <select
          className="select"
          value={String(gameState.phase || "")}
          onChange={(e) => patch("phase", e.target.value)}
        >
          {Object.entries(options.phases || {}).map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </select>
      </div>
      <div>
        <div className="label mb-1">Active player</div>
        <select
          className="select"
          value={String(gameState.active_player || "")}
          onChange={(e) => patch("active_player", e.target.value)}
        >
          {Object.entries(options.active || {}).map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
