"use client";

import Link from "next/link";
import { notFound, useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RosterTable, StatCard } from "@/components/instructor/InstructorWidgets";
import { useClassroom } from "@/features/instructor/use-instructor";

export default function DemonstratorClassroomDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const { classroom, analytics } = useClassroom(id);
  if (classroom === null) notFound();
  if (classroom === undefined || analytics === null) {
    return <p className="text-sm text-muted-foreground">Loading classroom…</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">{classroom.name}</h1>
          <p className="text-muted-foreground text-sm mt-1">
            {classroom.term} · {classroom.schedule} · read-only roster
          </p>
        </div>
        <Link
          href="/demonstrator/analytics"
          className="text-xs font-medium px-4 py-2 rounded-full bg-muted hover:bg-muted/70"
        >
          View analytics
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard label="Students" value={analytics.totalStudents} />
        <StatCard label="Avg completion" value={`${analytics.avgCompletion}%`} />
        <StatCard label="At risk" value={analytics.atRisk.length} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Roster (read-only)</CardTitle>
        </CardHeader>
        <CardContent>
          <RosterTable students={analytics.students} detailBase="/demonstrator/students" />
        </CardContent>
      </Card>
    </div>
  );
}
