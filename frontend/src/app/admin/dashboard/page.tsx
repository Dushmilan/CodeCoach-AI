"use client";
export const dynamic = "force-dynamic";

import { useEffect, useState } from "react";
import { useAuth } from "@/providers";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getErrorDisplayMessage } from "@/lib/fetch-client";

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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Welcome back, {user?.username} ({user?.role})
        </p>
      </div>

      {error && (
        <div className="text-sm text-red-400 bg-red-500/10 rounded-lg px-4 py-2">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
        </div>
      ) : (
        <>
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Total Users
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">
                  {stats.users?.total ?? 0}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {stats.users?.active ?? 0} active, {stats.users?.admin ?? 0}{" "}
                  admins
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Questions
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">
                  {stats.questions?.total ?? 0}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {stats.questions?.by_difficulty
                    ? Object.entries(stats.questions.by_difficulty).map(
                        ([d, c]) => (
                          <span key={d} className="mr-2">
                            {d}: {c}
                          </span>
                        ),
                      )
                    : "No data"}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Courses
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">
                  {stats.courses?.total ?? 0}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {stats.courses?.modules ?? 0} modules,{" "}
                  {stats.courses?.lessons ?? 0} lessons
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <a
                href="/admin/users"
                className="flex items-center gap-3 p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
              >
                <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-500 font-bold">
                  U
                </div>
                <div>
                  <div className="text-sm font-medium">Users</div>
                  <div className="text-xs text-muted-foreground">
                    Manage accounts
                  </div>
                </div>
              </a>
              <a
                href="/admin/questions"
                className="flex items-center gap-3 p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
              >
                <div className="w-10 h-10 rounded-lg bg-green-500/10 flex items-center justify-center text-green-500 font-bold">
                  Q
                </div>
                <div>
                  <div className="text-sm font-medium">Questions</div>
                  <div className="text-xs text-muted-foreground">
                    Review & import
                  </div>
                </div>
              </a>
              <a
                href="/admin/curriculum"
                className="flex items-center gap-3 p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
              >
                <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center text-purple-500 font-bold">
                  C
                </div>
                <div>
                  <div className="text-sm font-medium">Curriculum</div>
                  <div className="text-xs text-muted-foreground">
                    Manage courses
                  </div>
                </div>
                </a>
              </CardContent>
            </Card>

          {/* Professor hierarchy: admin → professors → courses/classrooms */}
          <Card data-testid="hierarchy-section">
            <CardHeader>
              <CardTitle>Professor hierarchy</CardTitle>
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
                    className="rounded-lg border border-border p-4 space-y-3"
                  >
                    <div className="font-medium">{prof.username}</div>
                    <div>
                      <div className="text-xs uppercase text-muted-foreground mb-1">
                        Courses
                      </div>
                      {prof.courses.length === 0 ? (
                        <p className="text-sm text-muted-foreground">
                          No courses.
                        </p>
                      ) : (
                        <ul className="text-sm space-y-1">
                          {prof.courses.map((course) => (
                            <li key={course.id}>
                              {course.title}{" "}
                              <span className="text-muted-foreground">
                                ({course.lessons} lessons)
                              </span>
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
                        <ul className="text-sm space-y-1">
                          {prof.classrooms.map((room) => (
                            <li key={room.id}>
                              <span className="font-medium">{room.name}</span>{" "}
                              <span className="text-muted-foreground">
                                {room.invite_code}
                              </span>{" "}
                              <span className="text-muted-foreground">
                                · {room.students} students ·{" "}
                                {room.avg_completion}% avg completion
                              </span>
                              {room.tas.length > 0 && (
                                <span className="text-muted-foreground">
                                  {" "}
                                  · TAs: <span>{room.tas.join(", ")}</span>
                                </span>
                              )}
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
        </>
      )}
    </div>
  );
}
