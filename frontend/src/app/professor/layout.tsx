"use client";

import { Header } from "@/components/header/Header";
import { InstructorSidebar } from "@/components/instructor/InstructorSidebar";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { MotionConfig } from "framer-motion";
import { usePathname } from "next/navigation";

function ProfessorContent({ children }: { children: React.ReactNode }) {
  return (
    <MotionConfig reducedMotion="user">
      <div className="min-h-screen bg-background">
        <Header />
        <InstructorSidebar base="professor" />
        <div className="md:ml-64">
          <main className="max-w-6xl mx-auto px-6 pt-20 pb-24">{children}</main>
        </div>
      </div>
    </MotionConfig>
  );
}

export default function ProfessorLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isLoginPage = pathname === "/login";

  if (isLoginPage) {
    return <>{children}</>;
  }

  return (
    <RoleGuard
      allowedRoles={["professor", "admin", "super_admin"]}
      loginHref="/login"
      deniedMessage="You need professor privileges to access this area."
    >
      <ProfessorContent>{children}</ProfessorContent>
    </RoleGuard>
  );
}
