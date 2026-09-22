"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MasteryBars, StatCard } from "@/components/instructor/InstructorWidgets";
import { useClassrooms } from "@/features/instructor/use-instructor";
import { Users } from "lucide-react";

export default function ProfessorAnalyticsPage() {
  const { classrooms, analytics, ready } = useClassrooms();
  if (!ready || classrooms === null) {
    return <p className="text-sm text-muted-foreground">Loading analytics…</p>;
  }

  if (classrooms.length === 0) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold tracking-tight">Class Analytics</h1>
        <p className="text-sm text-muted-foreground">No classrooms yet.</p>
        <Link
          href="/professor/classrooms"
          className="inline-block text-xs font-medium text-brand hover:underline"
        >
          View classrooms
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Class Analytics</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Read-only aggregates over existing progress, submissions, skill
          mastery, and plateau signals.
        </p>
      </div>

      <section aria-label="Classroom analytics">
        {classrooms.map((c) => {
          const a = analytics[c.id];
          return (
            <div key={c.id} className="mb-4">
              <Card data-testid={`analytics-${c.id}`} className="rounded-2xl">
                <CardHeader>
                  <CardTitle className="flex flex-wrap items-center justify-between gap-2 text-base">
                    <span>{c.name}</span>
                    <Link
                      href={`/professor/classrooms/${c.id}`}
                      className="text-xs font-medium text-brand hover:underline"
                    >
                      Open classroom →
                    </Link>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
                    <StatCard icon={Users} label="Students" value={a.totalStudents} />
                    <StatCard
                      featured
                      label="Avg completion"
                      value={`${a.avgCompletion}%`}
                      progress={a.avgCompletion}
                    />
                    <StatCard
                      label="Avg solved / student"
                      value={a.avgSolved}
                    />
                    <StatCard label="At risk" value={a.atRisk.length} />
                  </div>
                  <div>
                    <h3 className="text-sm font-medium mb-2">Skill mastery</h3>
                    <MasteryBars items={a.skillMastery} />
                  </div>
                  <div>
                    <h3 className="text-sm font-medium mb-2">
                      Plateau & activity signals
                    </h3>
                    {a.signals.length === 0 ? (
                      <p className="text-xs text-muted-foreground">
                        No signals. The class is on track.
                      </p>
                    ) : (
                      <ul className="space-y-2">
                        {a.signals.map((s, i) => (
                          <li key={i} className="text-xs p-3 rounded-2xl bg-muted/50">
                            <span className="font-medium">{s.title}</span>
                            <span className="text-muted-foreground">
                              : {s.detail}
                            </span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          );
        })}
      </section>
    </div>
  );
}
