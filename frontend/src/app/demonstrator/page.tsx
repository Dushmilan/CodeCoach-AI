"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatCard } from "@/components/instructor/InstructorWidgets";
import { getClassrooms, getClassAnalytics } from "@/features/instructor/demo";

export default function DemonstratorOverviewPage() {
  const classrooms = getClassrooms();
  const totalStudents = classrooms.reduce(
    (n, c) => n + getClassAnalytics(c.id).totalStudents,
    0,
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Demonstrator Dashboard</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Read-only roster, class analytics, and student coaching for your assigned sections.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <StatCard label="Assigned sections" value={classrooms.length} sub="Read-only access" />
        <StatCard label="Students" value={totalStudents} sub="Across assigned sections" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Assigned classrooms</CardTitle>
        </CardHeader>
        <CardContent data-testid="ta-classrooms" className="space-y-3">
          {classrooms.map((c) => {
            const a = getClassAnalytics(c.id);
            return (
              <div
                key={c.id}
                className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-lg bg-muted/50"
              >
                <div>
                  <div className="font-medium">{c.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {a.totalStudents} students · {a.avgCompletion}% avg completion
                  </div>
                </div>
                <Link
                  href={`/demonstrator/classrooms/${c.id}`}
                  className="text-xs font-medium px-3 py-1.5 rounded-full bg-primary text-primary-foreground"
                >
                  Open classroom
                </Link>
              </div>
            );
          })}
        </CardContent>
      </Card>

      <div className="flex flex-wrap gap-2">
        <Link
          href="/demonstrator/analytics"
          className="text-xs font-medium px-4 py-2 rounded-full bg-primary/90 text-primary-foreground"
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
    </div>
  );
}
