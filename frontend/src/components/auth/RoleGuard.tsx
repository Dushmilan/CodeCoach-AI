"use client";

import { useEffect, type ReactNode } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/providers";

interface RoleGuardProps {
  allowedRoles: string[];
  loginHref: string;
  deniedMessage: string;
  children: ReactNode;
}

export function RoleGuard({
  allowedRoles,
  loginHref,
  deniedMessage,
  children,
}: RoleGuardProps) {
  const { user, isAuthenticated, isHydrated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isHydrated && !isAuthenticated) {
      router.replace(loginHref);
    }
  }, [isHydrated, isAuthenticated, router, loginHref]);

  if (!isHydrated) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />
      </div>
    );
  }

  if (!allowedRoles.includes(user?.role ?? "")) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Access Denied</h1>
          <p className="text-muted-foreground">{deniedMessage}</p>
          <Link href="/" className="underline mt-4 inline-block">
            Go home
          </Link>{" "}
          <Link
            href={loginHref}
            className="underline mt-4 inline-block ml-4"
          >
            Go to sign-in
          </Link>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
