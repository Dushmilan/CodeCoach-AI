export const RESCUE_CONFIG = {
  // Idle time before the first (T1) rescue intervention fires.
  t1IdleMs: 4 * 60 * 1000,
  // Additional idle time after T1 before the T2 AI coach offer.
  t2AfterT1Ms: 5 * 60 * 1000,
  // Additional idle time after T2 before the T3 "re-plan your path" offer.
  t3AfterT2Ms: 5 * 60 * 1000,
  // How often the idle timer re-checks while a rescue is pending.
  checkIntervalMs: 30 * 1000,
} as const;

export const RESCUE_STORAGE_KEY = "rescue_abandoned_problems";

export const tierThresholds = {
  t1: RESCUE_CONFIG.t1IdleMs,
  t2: RESCUE_CONFIG.t1IdleMs + RESCUE_CONFIG.t2AfterT1Ms,
  t3:
    RESCUE_CONFIG.t1IdleMs +
    RESCUE_CONFIG.t2AfterT1Ms +
    RESCUE_CONFIG.t3AfterT2Ms,
} as const;
