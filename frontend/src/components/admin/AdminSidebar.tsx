"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuth } from "@/providers";
import { useTheme } from "next-themes";

import {
  LayoutDashboard,
  Users,
  FileText,
  Database,
} from "lucide-react";

interface NavItem {
  title: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  permission?: "admin" | "super_admin";
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
  const { theme, setTheme } = useTheme();

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
      title: "Questions",
      href: "/admin/questions",
      icon: FileText,
      permission: "admin",
    },
    {
      title: "Curriculum",
      href: "/admin/curriculum",
      icon: Database,
      permission: "admin",
    },
  ];

  const hasPermission = (permission: "admin" | "super_admin" | undefined) => {
    if (!permission) return true;
    if (permission === "super_admin") return user?.role === "super_admin";
    return !!user?.role && ["admin", "super_admin"].includes(user.role);
  };

  const filteredNavItems = navItems.filter((item) =>
    hasPermission(item.permission),
  );

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 h-full w-64 bg-card border-r border-border",
        "transform transition-transform duration-300",
        open ? "translate-x-0" : "-translate-x-full",
        "md:translate-x-0",
      )}
    >
      <div className="flex flex-col h-full">
        {/* Logo */}
        <div className="h-16 flex items-center px-6 border-b border-border">
          <Link href="/admin" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">A</span>
            </div>
            <span className="font-bold text-lg">Admin</span>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-1">
          {filteredNavItems.map((item) => {
            const isActive =
              pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => window.innerWidth < 768 && onClose()}
                className={cn(
                  "flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200",
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

        {/* User Info */}
        <div className="p-4 border-t border-border">
          <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-muted/50">
            <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
              <span className="text-sm font-medium">
                {user?.username.charAt(0).toUpperCase()}
              </span>
            </div>
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
