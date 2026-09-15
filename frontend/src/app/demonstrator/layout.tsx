"use client";

import { Header } from "@/components/header/Header";
import { InstructorSidebar } from "@/components/instructor/InstructorSidebar";
import { useAuth } from "@/providers";

const ALLOWED = ["ta", "professor", "admin", "super_admin"];

export default function DemonstratorLayout({ children }: { children: React.ReactNode }) {
  const { user, isHydrated, isAuthenticated } = useAuth();

  if (!isHydrated) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />
      </div>
    );
  }

  if (!isAuthenticated || !ALLOWED.includes(user?.role ?? "")) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Access Denied</h1>
          <p className="text-muted-foreground">
            You need demonstrator privileges to access this area.
          </p>
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
