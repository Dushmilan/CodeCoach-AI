"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { StatCard } from "@/components/instructor/InstructorWidgets";
import { useClassrooms } from "@/features/instructor/use-instructor";
import { LayoutDashboard, Users } from "lucide-react";

export default function DemonstratorOverviewPage() {
  const { classrooms, analytics, ready } = useClassrooms();
  if (!ready || classrooms === null) {
    return <p className="text-sm text-muted-foreground">Loading classrooms…</p>;
  }
  const totalStudents = classrooms.reduce(
    (n, c) => n + analytics[c.id].totalStudents,
    0,
  );
  const weightedCompletion = classrooms.length
    ? Math.round(
        classrooms.reduce(
          (n, c) =>
            n + analytics[c.id].avgCompletion * analytics[c.id].totalStudents,
          0,
        ) / Math.max(1, totalStudents),
      )
    : 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          Demonstrator Dashboard
        </h1>
        <p className="text-muted-foreground text-sm mt-1">
          Read-only roster, class analytics, and student coaching for your
          assigned sections.
        </p>
      </div>

      {/* Stats: bento rhythm, students cell carries the meter */}
      <section aria-label="Teaching statistics">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <StatCard
            icon={LayoutDashboard}
            label="Assigned sections"
            value={classrooms.length}
            sub="Read-only access"
          />
          <StatCard
            featured
            icon={Users}
            label="Students"
            value={totalStudents}
            sub="Across assigned sections"
            progress={weightedCompletion}
          />
        </div>
      </section>

      <section aria-label="Assigned classrooms">
        <Card className="rounded-2xl">
          <CardHeader>
            <CardTitle className="text-base">Assigned classrooms</CardTitle>
          </CardHeader>
          <CardContent data-testid="ta-classrooms" className="space-y-3">
            {classrooms.map((c) => {
              const a = analytics[c.id];
              return (
                <div
                  key={c.id}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border bg-muted/40 p-4"
                >
                  <div className="min-w-0 flex-1">
                    <div className="font-medium">{c.name}</div>
                    <div className="text-xs text-muted-foreground">
                      {a.totalStudents} students · {a.avgCompletion}% avg
                      completion
                    </div>
                    <div className="mt-2 max-w-xs">
                      <Progress
                        value={a.avgCompletion}
                        aria-label={`${c.name} completion`}
                        className="h-1.5"
                      />
                    </div>
                  </div>
                  <Link
                    href={`/demonstrator/classrooms/${c.id}`}
                    className="text-xs font-medium px-4 py-2 rounded-full bg-brand text-brand-foreground transition-colors hover:bg-brand/90"
                  >
                    Open classroom
                  </Link>
                </div>
              );
            })}
          </CardContent>
        </Card>
      </section>

      <section aria-label="Jump to">
        <div className="flex flex-wrap gap-2">
          <Link
            href="/demonstrator/analytics"
            className="text-xs font-medium px-4 py-2 rounded-full bg-brand text-brand-foreground transition-colors hover:bg-brand/90"
          >
            Class Analytics
          </Link>
          <Link
            href="/demonstrator/classrooms"
            className="text-xs font-medium px-4 py-2 rounded-full bg-muted hover:bg-muted/70"
          >
            All classrooms
          </Link>
        </div>
      </section>
    </div>
  );
}
