"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { Header } from "@/components/header/Header";
import { InstructorSidebar } from "@/components/instructor/InstructorSidebar";
import { isInstructor } from "@/lib/roles";
import { roleHomePath, signInPathFor } from "@/lib/auth/roleHome";
import { useAuth } from "@/providers";

export default function DemonstratorLayout({ children }: { children: React.ReactNode }) {
  const { user, isHydrated, isAuthenticated } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (isHydrated && !isAuthenticated) {
      router.replace(signInPathFor(pathname));
    }
  }, [isHydrated, isAuthenticated, pathname, router]);

  if (!isHydrated) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />
      </div>
    );
  }

  if (!isAuthenticated || !isInstructor(user?.role)) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Access Denied</h1>
          <p className="text-muted-foreground">
            You need demonstrator privileges to access this area.
          </p>
          <Link href={roleHomePath(user?.role)} className="underline mt-4 inline-block">
            Back to home
          </Link>{" "}
          <Link href={signInPathFor(pathname)} className="underline mt-4 inline-block ml-4">
            Go to sign-in
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <InstructorSidebar base="demonstrator" />
      <div className="md:ml-64">
        <main className="max-w-6xl mx-auto px-6 pt-20 pb-24">{children}</main>
      </div>
    </div>
  );
}
