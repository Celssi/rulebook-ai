const STAT_MAX = 20;
const STAT_MIN = 0;

export interface LegacyDeltas {
  health_delta?: number;
  morale_delta?: number;
  supplies_delta?: number;
}

function clampStat(value: number): number {
  return Math.max(STAT_MIN, Math.min(STAT_MAX, value));
}

export function legacyDeltasFromOption(legacy: LegacyDeltas | undefined): [number, number, number] {
  return [
    Number(legacy?.health_delta ?? 0),
    Number(legacy?.morale_delta ?? 0),
    Number(legacy?.supplies_delta ?? 0),
  ];
}

export function applyLegacyStatSwap(
  stats: { health: number; morale: number; supplies: number },
  oldLegacy: LegacyDeltas | undefined,
  newLegacy: LegacyDeltas | undefined
): { health: number; morale: number; supplies: number } {
  const [oh, om, os] = legacyDeltasFromOption(oldLegacy);
  const [nh, nm, ns] = legacyDeltasFromOption(newLegacy);
  return {
    health: clampStat(stats.health - oh + nh),
    morale: clampStat(stats.morale - om + nm),
    supplies: clampStat(stats.supplies - os + ns),
  };
}
