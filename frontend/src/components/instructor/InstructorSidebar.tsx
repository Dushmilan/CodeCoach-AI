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

  // The most specific matching destination wins so /professor/courses
  // highlights Courses instead of also lighting up Overview.
  const activeHref = items
    .map((item) => item.href)
    .filter((href) => pathname === href || pathname.startsWith(`${href}/`))
    .sort((a, b) => b.length - a.length)[0];

  return (
    <aside className="fixed left-0 top-0 z-40 h-full w-64 rounded-r-2xl border-r border-border bg-card hidden md:block">
      <div className="flex flex-col h-full">
        <div className="h-16 flex items-center px-6 border-b border-border">
          <Link
            href={base === "professor" ? "/professor" : "/demonstrator"}
            className="flex items-center gap-2"
          >
            <span
              aria-hidden="true"
              className="flex h-8 w-8 items-center justify-center rounded-2xl bg-brand text-brand-foreground"
            >
              <GraduationCap className="h-4 w-4" />
            </span>
            <span className="font-bold text-lg capitalize">{base}</span>
          </Link>
        </div>
        <nav className="flex-1 px-4 py-6 space-y-1">
          {items.map((item) => {
            const isActive = item.href === activeHref;
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={isActive ? "page" : undefined}
                className={cn(
                  "flex items-center gap-3 rounded-full px-4 py-2.5 text-sm transition-colors",
                  isActive
                    ? "bg-brand text-brand-foreground font-medium shadow-sm"
                    : "text-muted-foreground hover:bg-accent hover:text-foreground",
                )}
              >
                <item.icon className="h-4 w-4" aria-hidden="true" />
                <span>{item.title}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
