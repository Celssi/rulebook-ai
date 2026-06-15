import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { rosterEntryLabel } from "../../lib/rosterLabel";
import type { ScionHeader } from "../../types";

interface Props {
  entity: Record<string, unknown>;
  roster: { id: string; name: string }[];
  activeId: string;
  header: ScionHeader | null;
  onSwitch: () => void;
}

export default function ScionPanel({ entity, roster, activeId, header, onSwitch }: Props) {
  const [local, setLocal] = useState(entity);

  useEffect(() => {
    setLocal(entity);
  }, [entity]);

  const displayName = rosterEntryLabel(String(local.name || ""));
  const scionClass = String(local.scion_class || header?.scion_class || "");
  const pwr = Number(header?.pwr ?? local.pwr ?? 0);
  const intStat = Number(header?.int ?? local.int ?? 0);
  const agl = Number(header?.agl ?? local.agl ?? 0);
  const hp = Number(header?.hp ?? local.hp ?? 0);
  const maxHp = Number(header?.max_hp ?? local.max_hp ?? 0);
  const rooms = Number(header?.rooms_cleared ?? local.rooms_cleared ?? 0);
  const ember = Number(header?.ember ?? local.ember ?? 0);
  const emberToLevel = header?.ember_to_level;
  const trials = header?.active_trials ?? [];

  const switchScion = async (id: string) => {
    await api.switchAshesScion(id);
    onSwitch();
  };

  return (
    <div className="panel flex flex-col h-full min-h-0 overflow-hidden">
      <div className="px-4 py-2.5 border-b border-border section-title">Scion</div>

      <div className="flex-1 overflow-y-auto p-3 space-y-3 text-sm min-h-0">
        <select
          className="select text-sm py-1"
          value={activeId}
          onChange={(e) => switchScion(e.target.value)}
        >
          {roster.map((r) => (
            <option key={r.id} value={r.id}>
              {rosterEntryLabel(r.name)}
            </option>
          ))}
        </select>

        <div className="font-medium text-sm truncate">{displayName}</div>
        {scionClass && <p className="text-xs text-muted italic capitalize">{scionClass}</p>}

        <div className="grid grid-cols-3 gap-2 text-xs">
          <div>
            <div className="label">PWR</div>
            <div>{pwr}</div>
          </div>
          <div>
            <div className="label">INT</div>
            <div>{intStat}</div>
          </div>
          <div>
            <div className="label">AGL</div>
            <div>{agl}</div>
          </div>
        </div>

        <div className="text-xs text-muted">
          HP <span className="text-gray-200 font-medium">{hp}/{maxHp}</span>
          {header?.level != null && (
            <span className="ml-2">
              · Lv {header.level} · Ember {ember}
              {emberToLevel != null && (
                <span className="text-muted"> (need {emberToLevel} to level)</span>
              )}
            </span>
          )}
        </div>

        {rooms > 0 && (
          <div className="text-xs text-muted">
            Rooms cleared: <span className="text-gray-200">{rooms}</span>
          </div>
        )}

        {trials.length > 0 && (
          <div className="text-xs">
            <div className="label mb-1">Active trials ({trials.length}/10)</div>
            <ul className="space-y-1 text-muted">
              {trials.slice(0, 4).map((t, i) => (
                <li key={`${t.card}-${i}`} className="line-clamp-2">
                  <span className="capitalize text-gray-400">{t.color}</span>: {t.trial}
                </li>
              ))}
              {trials.length > 4 && <li className="italic">+{trials.length - 4} more…</li>}
            </ul>
          </div>
        )}

        {(header?.starting_weapon_melee || header?.starting_weapon_ranged) && (
          <div className="text-xs">
            <div className="label mb-1">Weapons</div>
            {header?.starting_weapon_melee && (
              <p className="text-muted line-clamp-2">Melee: {header.starting_weapon_melee}</p>
            )}
            {header?.starting_weapon_ranged && (
              <p className="text-muted line-clamp-2">Ranged: {header.starting_weapon_ranged}</p>
            )}
          </div>
        )}

        {header?.last_room_name && (
          <div className="text-xs">
            <div className="label mb-1">Last room</div>
            <p className="text-muted">{header.last_room_name}</p>
          </div>
        )}

        {header?.fate_gift && (
          <div className="text-xs">
            <div className="label mb-1">Fate&apos;s Gift</div>
            <p className="text-muted line-clamp-3">{header.fate_gift}</p>
          </div>
        )}
      </div>
    </div>
  );
}
