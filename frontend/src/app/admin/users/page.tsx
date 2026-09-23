"use client";
export const dynamic = "force-dynamic";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/providers";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/Skeleton";
import {
  Search,
  Shield,
  ShieldOff,
  UserCheck,
  UserX,
} from "lucide-react";

interface UserItem {
  id: string;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
  oauth_provider?: string | null;
}

const ROLE_BADGE: Record<string, string> = {
  super_admin: "bg-brand/10 text-brand ring-brand/20",
  admin: "bg-secondary text-secondary-foreground ring-border",
  user: "bg-muted text-muted-foreground ring-border",
};

export default function UsersPage() {
  const { user: authUser, token } = useAuth();
  const [users, setUsers] = useState<UserItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 15;

  const fetchUsers = useCallback(async () => {
    try {
      const params = new URLSearchParams({
        page: String(page),
        per_page: String(pageSize),
      });
      if (search) params.set("search", search);
      const res = await fetch(`/api/admin/users?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to fetch");
      const data = (await res.json()) as { users?: UserItem[]; total?: number };
      setUsers(data.users || []);
      setTotal(data.total || 0);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, [page, search, token]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const updateRole = async (userId: string, role: string) => {
    const res = await fetch(`/api/admin/users/${userId}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ role }),
    });
    if (res.ok) fetchUsers();
  };

  const toggleStatus = async (userId: string, current: boolean) => {
    const res = await fetch(`/api/admin/users/${userId}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ is_active: !current }),
    });
    if (res.ok) fetchUsers();
  };

  const roleBadge = (role: string) => (
    <span
      className={`text-xs font-medium px-2 py-0.5 rounded-full ring-1 ring-inset ${ROLE_BADGE[role] ?? ROLE_BADGE.user}`}
    >
      {role}
    </span>
  );

  return (
    <div className="space-y-6">
      <section aria-label="Directory controls">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Users</h1>
            <p className="text-muted-foreground text-sm mt-1">
              {total} total users
            </p>
          </div>
          <div className="flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2">
            <Search className="h-4 w-4 text-muted-foreground" />
            <input
              aria-label="Search users"
              className="bg-transparent border-none outline-none text-sm w-40 md:w-48 placeholder:text-muted-foreground"
              placeholder="Search users..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
            />
          </div>
        </div>
      </section>

      {loading ? (
        <div className="space-y-3" aria-busy="true">
          {[0, 1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-14 rounded-2xl" />
          ))}
        </div>
      ) : users.length === 0 ? (
        <Card className="rounded-2xl">
          <CardContent className="py-12 text-center text-muted-foreground">
            No users found.
          </CardContent>
        </Card>
      ) : (
        <section aria-label="User directory">
          <Card className="rounded-2xl">
            <CardHeader className="pb-0">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                All Users
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-muted-foreground text-xs uppercase">
                      <th className="text-left pb-3 font-medium">Username</th>
                      <th className="text-left pb-3 font-medium">Email</th>
                      <th className="text-left pb-3 font-medium">Role</th>
                      <th className="text-left pb-3 font-medium">Status</th>
                      <th className="text-right pb-3 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((u) => (
                      <tr
                        key={u.id}
                        className="border-b border-border/50 hover:bg-muted/20 transition-colors"
                      >
                        <td className="py-3">
                          <div className="flex items-center gap-2.5">
                            <Avatar data-testid="user-avatar" className="h-7 w-7">
                              <AvatarFallback>
                                {u.username.charAt(0).toUpperCase()}
                              </AvatarFallback>
                            </Avatar>
                            <span className="font-medium">
                              {u.username}
                              {u.id === authUser?.id ? (
                                <span className="text-xs text-muted-foreground ml-1">
                                  (you)
                                </span>
                              ) : (
                                ""
                              )}
                            </span>
                          </div>
                        </td>
                        <td className="py-3 text-muted-foreground">{u.email}</td>
                        <td className="py-3">{roleBadge(u.role)}</td>
                        <td className="py-3">
                          {u.is_active ? (
                            <span className="text-success text-xs flex items-center gap-1">
                              <UserCheck className="h-3 w-3" aria-hidden="true" />{" "}
                              Active
                            </span>
                          ) : (
                            <span className="text-destructive text-xs flex items-center gap-1">
                              <UserX className="h-3 w-3" aria-hidden="true" />{" "}
                              Inactive
                            </span>
                          )}
                        </td>
                        <td className="py-3 text-right">
                          <div className="flex items-center justify-end gap-2">
                            {authUser?.role === "super_admin" &&
                              u.id !== authUser?.id && (
                                <>
                                  <select
                                    aria-label={`Role for ${u.username}`}
                                    value={u.role}
                                    onChange={(e) =>
                                      updateRole(u.id, e.target.value)
                                    }
                                    className="text-xs bg-card rounded-full px-2.5 py-1 border border-border outline-none"
                                  >
                                    <option value="user">user</option>
                                    <option value="admin">admin</option>
                                    <option value="super_admin">
                                      super_admin
                                    </option>
                                  </select>
                                  <button
                                    onClick={() =>
                                      toggleStatus(u.id, u.is_active)
                                    }
                                    className="text-xs p-1.5 rounded-full hover:bg-muted transition-colors"
                                    title={
                                      u.is_active ? "Deactivate" : "Activate"
                                    }
                                  >
                                    {u.is_active ? (
                                      <ShieldOff
                                        className="h-3.5 w-3.5 text-muted-foreground"
                                        aria-hidden="true"
                                      />
                                    ) : (
                                      <Shield
                                        className="h-3.5 w-3.5 text-success"
                                        aria-hidden="true"
                                      />
                                    )}
                                  </button>
                                </>
                              )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {total > pageSize && (
                <>
                  <Separator className="mt-4" />
                  <div className="flex items-center justify-between mt-4">
                    <span className="text-xs text-muted-foreground">
                      Page {page} of {Math.ceil(total / pageSize)}
                    </span>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={page === 1}
                        onClick={() => setPage((p) => p - 1)}
                      >
                        Previous
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={page >= Math.ceil(total / pageSize)}
                        onClick={() => setPage((p) => p + 1)}
                      >
                        Next
                      </Button>
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </section>
      )}
    </div>
  );
}
