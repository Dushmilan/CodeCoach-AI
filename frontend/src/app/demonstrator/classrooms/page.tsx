"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useClassrooms } from "@/features/instructor/use-instructor";

export default function DemonstratorClassroomsPage() {
  const { classrooms, analytics, ready } = useClassrooms();
  if (!ready || classrooms === null) {
    return <p className="text-sm text-muted-foreground">Loading classrooms…</p>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Classrooms</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Your assigned sections — read-only. Roster changes need a professor.
        </p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4" data-testid="ta-classroom-list">
        {classrooms.map((c) => {
          const a = analytics[c.id];
          return (
            <Card key={c.id}>
              <CardHeader>
                <CardTitle>{c.name}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <p className="text-xs text-muted-foreground">
                  {c.term} · {c.schedule}
                </p>
                <p className="text-xs text-muted-foreground">
                  {a.totalStudents} students · {a.avgCompletion}% avg completion
                </p>
                <Link
                  href={`/demonstrator/classrooms/${c.id}`}
                  className="inline-block text-xs font-medium px-3 py-1.5 rounded-full bg-primary text-primary-foreground"
                >
                  Open classroom
                </Link>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
