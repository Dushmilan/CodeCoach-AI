"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { isAdmin, isProfessor } from "@/lib/roles";
import { useAuth } from "@/providers";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  LayoutDashboard,
  Users,
  GraduationCap,
  FileText,
  Database,
} from "lucide-react";

interface NavItem {
  title: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  permission?: "admin" | "super_admin" | "course_editor";
}

export default function AdminSidebar({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const pathname = usePathname();
  const { user } = useAuth();

  const navItems: NavItem[] = [
    {
      title: "Dashboard",
      href: "/admin",
      icon: LayoutDashboard,
      permission: "admin",
    },
    {
      title: "Users",
      href: "/admin/users",
      icon: Users,
      permission: "admin",
    },
    {
      title: "Professors",
      href: "/admin/professors",
      icon: GraduationCap,
      permission: "admin",
    },
    {
      title: "Questions",
      href: "/admin/questions",
      icon: FileText,
      permission: "admin",
    },
    {
      title: "Curriculum",
      href: "/admin/curriculum",
      icon: Database,
      permission: "course_editor",
    },
  ];

  const hasPermission = (permission: "admin" | "super_admin" | "course_editor" | undefined) => {
    if (!permission) return true;
    if (permission === "super_admin") return user?.role === "super_admin";
    if (permission === "course_editor")
      return isProfessor(user?.role);
    return isAdmin(user?.role);
  };

  const filteredNavItems = navItems.filter((item) =>
    hasPermission(item.permission),
  );

  // The most specific matching destination wins so /admin/users highlights
  // Users instead of also lighting up the Dashboard root.
  const activeHref = filteredNavItems
    .map((item) => item.href)
    .filter((href) => pathname === href || pathname.startsWith(`${href}/`))
    .sort((a, b) => b.length - a.length)[0];

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 h-full w-64 rounded-r-2xl bg-card border-r border-border",
        "transform transition-transform duration-300",
        open ? "translate-x-0" : "-translate-x-full",
        "md:translate-x-0",
      )}
    >
      <div className="flex flex-col h-full">
        {/* Logo */}
        <div className="h-16 flex items-center px-6 border-b border-border">
          <Link href="/admin" className="flex items-center gap-2">
            <span
              aria-hidden="true"
              className="w-8 h-8 rounded-2xl bg-brand text-brand-foreground flex items-center justify-center font-bold text-sm"
            >
              A
            </span>
            <span className="font-bold text-lg">Admin</span>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-1">
          {filteredNavItems.map((item) => {
            const isActive = item.href === activeHref;
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={isActive ? "page" : undefined}
                onClick={() => window.innerWidth < 768 && onClose()}
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

        {/* User Info */}
        <div className="p-4 border-t border-border">
          <div className="flex items-center gap-3 rounded-full bg-muted/50 py-1.5 pl-1.5 pr-4">
            <Avatar
              data-testid="admin-sidebar-avatar"
              className="h-8 w-8"
            >
              <AvatarFallback>
                {user?.username.charAt(0).toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user?.username}</p>
              <p className="text-xs text-muted-foreground truncate">
                {user?.role}
              </p>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
