"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MasteryBars, StatCard } from "@/components/instructor/InstructorWidgets";
import { getClassrooms, getClassAnalytics } from "@/features/instructor/demo";

export default function ProfessorAnalyticsPage() {
  const classrooms = getClassrooms();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Class Analytics</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Read-only aggregates over existing progress, submissions, skill mastery, and plateau signals.
        </p>
      </div>

      {classrooms.map((c) => {
        const a = getClassAnalytics(c.id);
        return (
          <Card key={c.id} data-testid={`analytics-${c.id}`}>
            <CardHeader>
              <CardTitle className="flex flex-wrap items-center justify-between gap-2">
                <span>{c.name}</span>
                <Link
                  href={`/professor/classrooms/${c.id}`}
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
                <h3 className="text-sm font-medium mb-2">Plateau & activity signals</h3>
                {a.signals.length === 0 ? (
                  <p className="text-xs text-muted-foreground">No signals — class is on track.</p>
                ) : (
                  <ul className="space-y-2">
                    {a.signals.map((s, i) => (
                      <li key={i} className="text-xs p-2 rounded-lg bg-muted/50">
                        <span className="font-medium">{s.title}</span>
                        <span className="text-muted-foreground"> — {s.detail}</span>
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
