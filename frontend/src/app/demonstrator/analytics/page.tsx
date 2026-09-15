"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MasteryBars, StatCard } from "@/components/instructor/InstructorWidgets";
import { useClassrooms } from "@/features/instructor/use-instructor";

export default function DemonstratorAnalyticsPage() {
  const { classrooms, analytics, ready } = useClassrooms();
  if (!ready || classrooms === null) {
    return <p className="text-sm text-muted-foreground">Loading analytics…</p>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Class Analytics</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Same class signals professors see — coaching context for your sections.
        </p>
      </div>

      {classrooms.map((c) => {
        const a = analytics[c.id];
        return (
          <Card key={c.id} data-testid={`ta-analytics-${c.id}`}>
            <CardHeader>
              <CardTitle className="flex flex-wrap items-center justify-between gap-2">
                <span>{c.name}</span>
                <Link
                  href={`/demonstrator/classrooms/${c.id}`}
                  className="text-xs font-medium text-primary hover:underline"
                >
                  Open classroom →
                </Link>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <StatCard label="Students" value={a.totalStudents} />
                <StatCard label="Avg completion" value={`${a.avgCompletion}%`} />
                <StatCard label="Avg solved / student" value={a.avgSolved} />
              </div>
              <div>
                <h3 className="text-sm font-medium mb-2">Skill mastery</h3>
                <MasteryBars items={a.skillMastery} />
              </div>
              <div>
                <h3 className="text-sm font-medium mb-2">Students to coach</h3>
                {a.atRisk.length === 0 ? (
                  <p className="text-xs text-muted-foreground">No at-risk students.</p>
                ) : (
                  <ul className="space-y-2">
                    {a.atRisk.map((s) => (
                      <li key={s.userId} className="text-xs p-2 rounded-lg bg-muted/50">
                        <span className="font-medium">{s.name}</span>
                        <span className="text-muted-foreground">
                          {" "}— {s.completionPct}% completion, {s.solved}/{s.attempted} solved
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
