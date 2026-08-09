"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { UsageInfo } from "./usage.types";
import { usageService } from "./usage.service";

export interface UsageContextValue {
  usage: UsageInfo | null;
  limitReached: boolean;
  upgradeOpen: boolean;
  refreshUsage: () => Promise<void>;
  markLimitReached: () => void;
  clearLimitReached: () => void;
  openUpgrade: () => void;
  closeUpgrade: () => void;
}

const defaultUsageContext: UsageContextValue = {
  usage: null,
  limitReached: false,
  upgradeOpen: false,
  refreshUsage: async () => {},
  markLimitReached: () => {},
  clearLimitReached: () => {},
  openUpgrade: () => {},
  closeUpgrade: () => {},
};

const UsageContext = createContext<UsageContextValue>(defaultUsageContext);

export function UsageProvider({ children }: { children: ReactNode }) {
  const [usage, setUsage] = useState<UsageInfo | null>(null);
  const [limitReached, setLimitReached] = useState(false);
  const [upgradeOpen, setUpgradeOpen] = useState(false);

  const refreshUsage = useCallback(async () => {
    try {
      setUsage(await usageService.getUsage());
    } catch {
      // Quota endpoint is best-effort; keep the last known usage.
    }
  }, []);

  const markLimitReached = useCallback(() => setLimitReached(true), []);
  const clearLimitReached = useCallback(() => setLimitReached(false), []);
  const openUpgrade = useCallback(() => setUpgradeOpen(true), []);
  const closeUpgrade = useCallback(() => setUpgradeOpen(false), []);

  useEffect(() => {
    refreshUsage();
  }, [refreshUsage]);

  return (
    <UsageContext.Provider
      value={{
        usage,
        limitReached,
        upgradeOpen,
        refreshUsage,
        markLimitReached,
        clearLimitReached,
        openUpgrade,
        closeUpgrade,
      }}
    >
      {children}
    </UsageContext.Provider>
  );
}

export function useUsage(): UsageContextValue {
  return useContext(UsageContext);
}
