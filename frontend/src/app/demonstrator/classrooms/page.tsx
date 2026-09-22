"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useClassrooms } from "@/features/instructor/use-instructor";

export default function DemonstratorClassroomsPage() {
  const { classrooms, analytics, ready } = useClassrooms();
  if (!ready || classrooms === null) {
    return <p className="text-sm text-muted-foreground">Loading classrooms…</p>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Classrooms</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Your assigned sections, read-only. Roster changes need a professor.
        </p>
      </div>
      <section aria-label="Assigned classrooms">
        <div
          className="grid grid-cols-1 gap-4 md:grid-cols-2"
          data-testid="ta-classroom-list"
        >
          {classrooms.map((c) => {
            const a = analytics[c.id];
            return (
              <Card key={c.id} className="rounded-2xl">
                <CardHeader>
                  <CardTitle className="text-base">{c.name}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-xs text-muted-foreground">
                    {c.term} · {c.schedule}
                  </p>
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-muted-foreground">
                        {a.totalStudents} students
                      </span>
                      <span className="text-muted-foreground">
                        {a.avgCompletion}% avg completion
                      </span>
                    </div>
                    <Progress
                      value={a.avgCompletion}
                      aria-label={`${c.name} completion`}
                      className="h-1.5"
                    />
                  </div>
                  <Link
                    href={`/demonstrator/classrooms/${c.id}`}
                    className="inline-block text-xs font-medium px-4 py-2 rounded-full bg-brand text-brand-foreground transition-colors hover:bg-brand/90"
                  >
                    Open classroom
                  </Link>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>
    </div>
  );
}
