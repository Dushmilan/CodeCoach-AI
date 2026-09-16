"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/providers";
import { roleHomePath, signInPathFor } from "@/lib/auth/roleHome";

/** Shared guard hook (Issue #180).
 *
 * Convention: unauthenticated users are replaced to the sign-in route for
 * the current pathname; authenticated users without the role see the
 * forbidden UI with a link to their role home (never a dead end).
 */
export function useRoleGuard(options: {
  allow: string[];
  pathname: string | null;
}): { status: "loading" | "unauthenticated" | "forbidden" | "allowed" } {
  const { user, isAuthenticated, isHydrated } = useAuth();
  const router = useRouter();

  const allowed =
    isHydrated && isAuthenticated && options.allow.includes(user?.role ?? "");

  useEffect(() => {
    if (isHydrated && !isAuthenticated) {
      router.replace(signInPathFor(options.pathname));
    }
  }, [isHydrated, isAuthenticated, router, options.pathname]);

  if (!isHydrated) return { status: "loading" };
  if (!isAuthenticated) return { status: "unauthenticated" };
  if (!allowed) return { status: "forbidden" };
  return { status: "allowed" };
}

export { roleHomePath };
