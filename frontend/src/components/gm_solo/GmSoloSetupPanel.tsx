import type { GmSoloGameId } from "../../games/gmSoloGames";
import { gmSoloApi } from "../../api/gmSolo";

import type { PlayHeader, SessionState } from "../../types";

interface Props {
  gameId: GmSoloGameId;
  entity: Record<string, unknown>;
  onSaved: (session: SessionState, header?: PlayHeader) => void;
  session: SessionState;
}

/** Minimal character setup for GM solo games (except outgunned/dnd5e). */
export default function GmSoloSetupPanel({ gameId, entity, onSaved, session }: Props) {
  const api = gmSoloApi(gameId);
  const name = String(entity.name || entity.hero_name || entity.investigator_name || "");

  const saveName = async (newName: string) => {
    const res = await api.updateCharacter({ ...entity, name: newName });
    onSaved({ ...session, entity: res.entity }, res.header);
  };

  return (
    <div className="space-y-3 text-sm">
      <label className="block">
        <span className="text-muted text-xs">Name</span>
        <input
          className="input w-full mt-1"
          defaultValue={name}
          onBlur={(e) => {
            const v = e.target.value.trim();
            if (v && v !== name) void saveName(v);
          }}
        />
      </label>
      <p className="text-xs text-muted">
        Use shortcuts in the Play tab for dice and tables. Enable <strong>AI narrator</strong> in
        Settings for GM scene prose.
      </p>
    </div>
  );
}
