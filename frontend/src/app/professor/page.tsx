"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatCard } from "@/components/instructor/InstructorWidgets";
import { getClassrooms, getCourses, getClassAnalytics } from "@/features/instructor/demo";

export default function ProfessorOverviewPage() {
  const classrooms = getClassrooms();
  const courses = getCourses();
  const totalStudents = classrooms.reduce(
    (n, c) => n + getClassAnalytics(c.id).totalStudents,
    0,
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Professor Dashboard</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Your courses, classrooms, and class analytics — invite students with classroom codes.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard label="Courses created" value={courses.length} sub="Via verified content pipeline" />
        <StatCard label="Classrooms" value={classrooms.length} sub="Invite-code enrollment" />
        <StatCard label="Students enrolled" value={totalStudents} sub="Across all sections" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Classrooms</CardTitle>
        </CardHeader>
        <CardContent data-testid="prof-classrooms" className="space-y-3">
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
                    {a.totalStudents} students · {a.avgCompletion}% avg completion · Invite: {c.inviteCode}
                  </div>
                </div>
                <Link
                  href={`/professor/classrooms/${c.id}`}
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
          href="/professor/analytics"
          className="text-xs font-medium px-4 py-2 rounded-full bg-primary/90 text-primary-foreground"
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
    </div>
  );
}
