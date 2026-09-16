"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  BookOpen,
  Users,
  BarChart3,
  GraduationCap,
} from "lucide-react";

export function InstructorSidebar({ base }: { base: "professor" | "demonstrator" }) {
  const pathname = usePathname();
  const items =
    base === "professor"
      ? [
          { title: "Overview", href: "/professor", icon: LayoutDashboard },
          { title: "Courses", href: "/professor/courses", icon: BookOpen },
          { title: "Curriculum", href: "/professor/curriculum", icon: GraduationCap },
          { title: "Classrooms", href: "/professor/classrooms", icon: Users },
          { title: "Class Analytics", href: "/professor/analytics", icon: BarChart3 },
        ]
      : [
          { title: "Overview", href: "/demonstrator", icon: LayoutDashboard },
          { title: "Classrooms", href: "/demonstrator/classrooms", icon: Users },
          { title: "Class Analytics", href: "/demonstrator/analytics", icon: BarChart3 },
        ];

  return (
    <aside className="fixed left-0 top-0 z-40 h-full w-64 bg-card border-r border-border hidden md:block">
      <div className="flex flex-col h-full">
        <div className="h-16 flex items-center px-6 border-b border-border">
          <Link href={base === "professor" ? "/professor" : "/demonstrator"} className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <GraduationCap className="h-4 w-4 text-white" />
            </div>
            <span className="font-bold text-lg capitalize">{base}</span>
          </Link>
        </div>
        <nav className="flex-1 px-4 py-6 space-y-1">
          {items.map((item) => {
            const isActive =
              pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-4 py-3 rounded-lg transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground font-medium"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                )}
              >
                <item.icon className="h-5 w-5" />
                <span>{item.title}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
