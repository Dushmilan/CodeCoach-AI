"use client";
export const dynamic = "force-dynamic";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/providers";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart3, TrendingUp, Users, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";

interface UserAnalytics {
  total_users?: number;
  active_users?: number;
  new_users_30d?: number;
  role_distribution?: Record<string, number>;
}
interface QuestionProgress {
  total?: number;
  solved?: number;
  attempted?: number;
  by_difficulty?: Record<string, number>;
}

export default function AnalyticsPage() {
  const { user, token } = useAuth();
  const [userAnalytics, setUserAnalytics] = useState<UserAnalytics | null>(
    null,
  );
  const [qProgress, setQProgress] = useState<QuestionProgress | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      const headers = { Authorization: `Bearer ${token}` };
      try {
        const [uRes, qRes] = await Promise.all([
          fetch("/api/admin/analytics/users", { headers }),
          fetch("/api/admin/analytics/question-progress", { headers }),
        ]);
        if (uRes.ok) setUserAnalytics(await uRes.json());
        if (qRes.ok) setQProgress(await qRes.json());
      } catch {
        /* */
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [token]);

  if (loading)
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );

  const StatCard = ({ title, value, sub, icon: Icon, color }: any) => (
    <Card>
      <CardHeader className="pb-2 flex flex-row items-center justify-between">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <div
          className={`w-8 h-8 rounded-lg ${color} flex items-center justify-center`}
        >
          <Icon className="h-4 w-4" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold">{value ?? "-"}</div>
        {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Analytics</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Platform usage and performance metrics
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Users"
          value={userAnalytics?.total_users}
          icon={Users}
          color="bg-blue-500/10 text-blue-500"
          sub={`${userAnalytics?.active_users ?? 0} active`}
        />
        <StatCard
          title="New Users (30d)"
          value={userAnalytics?.new_users_30d}
          icon={TrendingUp}
          color="bg-green-500/10 text-green-500"
        />
        <StatCard
          title="Questions Solved"
          value={qProgress?.solved}
          icon={FileText}
          color="bg-purple-500/10 text-purple-500"
          sub={`${qProgress?.total ?? 0} total questions`}
        />
        <StatCard
          title="Attempt Rate"
          value={
            qProgress?.total
              ? Math.round(((qProgress.solved ?? 0) / qProgress.total) * 100) +
                "%"
              : "-"
          }
          icon={BarChart3}
          color="bg-orange-500/10 text-orange-500"
        />
      </div>

      {/* Role Distribution */}
      {userAnalytics?.role_distribution && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">User Role Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(userAnalytics.role_distribution).map(
                ([role, count]: [string, any]) => {
                  const total = userAnalytics.total_users || 1;
                  const pct = Math.round((count / total) * 100);
                  const colors: Record<string, string> = {
                    super_admin: "bg-purple-500",
                    admin: "bg-blue-500",
                    user: "bg-gray-500",
                  };
                  return (
                    <div key={role}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="font-medium capitalize">
                          {role.replace("_", " ")}
                        </span>
                        <span className="text-muted-foreground">
                          {count} ({pct}%)
                        </span>
                      </div>
                      <div className="h-2 bg-muted/30 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${
                            colors[role] || "bg-gray-500"
                          }`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                },
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Difficulty Distribution */}
      {qProgress?.by_difficulty && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">
              Question Difficulty Distribution
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4">
              {Object.entries(qProgress.by_difficulty).map(
                ([d, c]: [string, any]) => {
                  const colors: Record<string, string> = {
                    easy: "text-green-500 border-green-500/30 bg-green-500/5",
                    medium:
                      "text-yellow-500 border-yellow-500/30 bg-yellow-500/5",
                    hard: "text-red-500 border-red-500/30 bg-red-500/5",
                  };
                  return (
                    <div
                      key={d}
                      className={`text-center p-4 rounded-xl border ${colors[d] || ""}`}
                    >
                      <div className="text-2xl font-bold">{c}</div>
                      <div className="text-xs capitalize mt-1">{d}</div>
                    </div>
                  );
                },
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
