"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { StatCard } from "@/components/instructor/InstructorWidgets";
import { getCourses } from "@/features/instructor/demo";
import { useClassrooms } from "@/features/instructor/use-instructor";
import { BookOpen, LayoutDashboard, Users } from "lucide-react";

export default function ProfessorOverviewPage() {
  const { classrooms, analytics, ready } = useClassrooms();
  const courses = getCourses();
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
          Professor Dashboard
        </h1>
        <p className="text-muted-foreground text-sm mt-1">
          Your courses, classrooms, and class analytics. Invite students with
          classroom codes.
        </p>
      </div>

      {/* Stats: bento rhythm, students cell spans and carries the meter */}
      <section aria-label="Teaching statistics">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          <StatCard
            icon={BookOpen}
            label="Courses created"
            value={courses.length}
            sub="Via verified content pipeline"
          />
          <StatCard
            icon={LayoutDashboard}
            label="Classrooms"
            value={classrooms.length}
            sub="Invite-code enrollment"
          />
          <StatCard
            featured
            className="md:col-span-2"
            icon={Users}
            label="Students enrolled"
            value={totalStudents}
            sub="Across all sections"
            progress={weightedCompletion}
          />
        </div>
      </section>

      <section aria-label="Classrooms">
        <Card className="rounded-2xl">
          <CardHeader>
            <CardTitle className="text-base">Classrooms</CardTitle>
          </CardHeader>
          <CardContent data-testid="prof-classrooms" className="space-y-3">
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
                      completion · Invite: {c.inviteCode}
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
                    href={`/professor/classrooms/${c.id}`}
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
            href="/professor/analytics"
            className="text-xs font-medium px-4 py-2 rounded-full bg-brand text-brand-foreground transition-colors hover:bg-brand/90"
          >
            Class Analytics
          </Link>
          <Link
            href="/professor/courses"
            className="text-xs font-medium px-4 py-2 rounded-full bg-muted hover:bg-muted/70"
          >
            Courses
          </Link>
          <Link
            href="/professor/classrooms"
            className="text-xs font-medium px-4 py-2 rounded-full bg-muted hover:bg-muted/70"
          >
            All classrooms
          </Link>
        </div>
      </section>
    </div>
  );
}
