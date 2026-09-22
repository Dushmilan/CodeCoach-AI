"use client";
export const dynamic = "force-dynamic";

import { useEffect, useState } from "react";
import { useAuth } from "@/providers";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/Skeleton";
import { StatCard } from "@/components/instructor/InstructorWidgets";
import { getErrorDisplayMessage } from "@/lib/fetch-client";
import { Activity, Database, FileText, Users } from "lucide-react";
import Link from "next/link";

interface AdminStats {
  users?: { total: number; active: number; admin: number; inactive: number };
  questions?: { total: number; by_difficulty: Record<string, number> };
  courses?: { total: number; modules: number; lessons: number };
  system?: { uptime: string; version: string };
  generation?: { total_jobs: number; pending: number; completed: number };
}

interface HierarchyCourse {
  id: string;
  title: string;
  lessons: number;
}

interface HierarchyClassroom {
  id: string;
  name: string;
  invite_code: string;
  tas: string[];
  students: number;
  avg_completion: number;
}

interface HierarchyProfessor {
  id: string;
  username: string;
  courses: HierarchyCourse[];
  classrooms: HierarchyClassroom[];
}

interface HierarchyTree {
  professors?: HierarchyProfessor[];
}

const QUICK_ACTIONS = [
  { href: "/admin/users", label: "Users", hint: "Manage accounts", icon: Users },
  {
    href: "/admin/questions",
    label: "Questions",
    hint: "Review & import",
    icon: FileText,
  },
  {
    href: "/admin/curriculum",
    label: "Curriculum",
    hint: "Manage courses",
    icon: Database,
  },
] as const;

export default function AdminDashboard() {
  const { user, token } = useAuth();
  const [stats, setStats] = useState<AdminStats>({});
  const [hierarchy, setHierarchy] = useState<HierarchyTree>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [statsRes, treeRes] = await Promise.all([
          fetch("/api/admin/stats", {
            headers: { Authorization: `Bearer ${token}` },
          }),
          fetch("/api/admin/hierarchy", {
            headers: { Authorization: `Bearer ${token}` },
          }),
        ]);
        if (!statsRes.ok) throw new Error("Failed to fetch stats");
        const data = (await statsRes.json()) as AdminStats;
        setStats(data);
        if (treeRes.ok) {
          setHierarchy((await treeRes.json()) as HierarchyTree);
        }
      } catch (err) {
        setError(getErrorDisplayMessage(err) || "Error loading stats");
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, [token]);

  const totalUsers = stats.users?.total ?? 0;
  const activePct =
    totalUsers > 0
      ? Math.round(((stats.users?.active ?? 0) / totalUsers) * 100)
      : 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Welcome back, {user?.username} ({user?.role})
        </p>
      </div>

      {error && (
        <div className="text-sm text-destructive bg-destructive/10 rounded-2xl px-4 py-2">
          {error}
        </div>
      )}

      {loading ? (
        <section aria-busy="true" aria-label="Platform statistics">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-36 rounded-2xl" />
            ))}
          </div>
        </section>
      ) : (
        <>
          {/* Stats: bento rhythm, featured cell spans and meters */}
          <section aria-label="Platform statistics">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
              <StatCard
                featured
                icon={Users}
                label="Total Users"
                value={totalUsers}
                sub={`${stats.users?.active ?? 0} active, ${stats.users?.admin ?? 0} admins`}
                progress={activePct}
              />
              <StatCard
                icon={FileText}
                label="Questions"
                value={stats.questions?.total ?? 0}
                sub={
                  stats.questions?.by_difficulty ? (
                    <span className="flex flex-wrap gap-1.5">
                      {Object.entries(stats.questions.by_difficulty).map(
                        ([d, c]) => (
                          <span
                            key={d}
                            className="rounded-full bg-muted px-2 py-0.5 text-foreground/80"
                          >
                            {d}: {c}
                          </span>
                        ),
                      )}
                    </span>
                  ) : (
                    "No data"
                  )
                }
              />
              <StatCard
                icon={Database}
                label="Courses"
                value={stats.courses?.total ?? 0}
                sub={`${stats.courses?.modules ?? 0} modules, ${stats.courses?.lessons ?? 0} lessons`}
              />
              <StatCard
                icon={Activity}
                label="Generation jobs"
                value={stats.generation?.total_jobs ?? 0}
                testId="admin-stat-generation"
                sub={`${stats.generation?.pending ?? 0} pending, ${stats.generation?.completed ?? 0} completed`}
              />
            </div>
          </section>

          {/* Quick Actions: pill action row, one emerald accent */}
          <section aria-label="Quick actions">
            <div className="rounded-2xl border border-border bg-card p-5">
              <h2 className="text-sm font-medium text-muted-foreground mb-3">
                Quick Actions
              </h2>
              <div className="flex flex-wrap gap-3">
                {QUICK_ACTIONS.map((action) => (
                  <Link
                    key={action.href}
                    href={action.href}
                    className="group inline-flex items-center gap-2.5 rounded-full border border-border bg-background py-2 pl-2 pr-5 transition-colors hover:bg-accent"
                  >
                    <span
                      aria-hidden="true"
                      className="flex h-8 w-8 items-center justify-center rounded-2xl bg-brand/10 text-brand ring-1 ring-brand/20"
                    >
                      <action.icon className="h-4 w-4" />
                    </span>
                    <span className="text-sm font-medium">{action.label}</span>
                    <span className="text-xs text-muted-foreground">
                      {action.hint}
                    </span>
                  </Link>
                ))}
              </div>
            </div>
          </section>

          {/* Professor hierarchy: admin → professors → courses/classrooms */}
          <section>
            <Card data-testid="hierarchy-section" className="rounded-2xl">
              <CardHeader>
                <CardTitle className="text-base">
                  Professor hierarchy
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {(hierarchy.professors ?? []).length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No professors found.
                  </p>
                ) : (
                  (hierarchy.professors ?? []).map((prof) => (
                    <div
                      key={prof.id}
                      className="rounded-2xl border border-border bg-muted/30 p-4 space-y-3"
                    >
                      <div className="flex items-center gap-3">
                        <Avatar
                          data-testid="hierarchy-avatar"
                          className="h-8 w-8"
                        >
                          <AvatarFallback>
                            {prof.username.charAt(0).toUpperCase()}
                          </AvatarFallback>
                        </Avatar>
                        <span className="font-medium">{prof.username}</span>
                      </div>
                      <div>
                        <div className="text-xs uppercase text-muted-foreground mb-1">
                          Courses
                        </div>
                        {prof.courses.length === 0 ? (
                          <p className="text-sm text-muted-foreground">
                            No courses.
                          </p>
                        ) : (
                          <ul className="text-sm">
                            {prof.courses.map((course, i) => (
                              <li key={course.id}>
                                {i > 0 && <Separator />}
                                <div className="py-2">
                                  {course.title}{" "}
                                  <span className="text-muted-foreground">
                                    ({course.lessons} lessons)
                                  </span>
                                </div>
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                      <div>
                        <div className="text-xs uppercase text-muted-foreground mb-1">
                          Classrooms
                        </div>
                        {prof.classrooms.length === 0 ? (
                          <p className="text-sm text-muted-foreground">
                            No classrooms.
                          </p>
                        ) : (
                          <ul className="text-sm">
                            {prof.classrooms.map((room, i) => (
                              <li key={room.id}>
                                {i > 0 && <Separator />}
                                <div className="space-y-1.5 py-2">
                                  <div className="flex flex-wrap items-center justify-between gap-2">
                                    <span className="font-medium">
                                      {room.name}
                                    </span>
                                    <span className="rounded-full bg-muted px-2.5 py-0.5 font-mono text-xs text-muted-foreground">
                                      {room.invite_code}
                                    </span>
                                  </div>
                                  <span className="text-muted-foreground">
                                    · {room.students} students ·{" "}
                                    {room.avg_completion}% avg completion
                                    {room.tas.length > 0 && (
                                      <>
                                        {" "}
                                        · TAs:{" "}
                                        <span>
                                          {room.tas.join(", ")}
                                        </span>
                                      </>
                                    )}
                                  </span>
                                  <Progress
                                    value={room.avg_completion}
                                    aria-label={`${room.name} completion`}
                                    className="h-1.5"
                                  />
                                </div>
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </section>
        </>
      )}
    </div>
  );
}
