"use client";

import Link from "next/link";
import { notFound, useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RosterTable, StatCard } from "@/components/instructor/InstructorWidgets";
import { useClassroom } from "@/features/instructor/use-instructor";
import { AlertTriangle, Users } from "lucide-react";

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
          <h1 className="text-2xl font-bold tracking-tight">{classroom.name}</h1>
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

      {/* Stats: bento rhythm, completion meter spans two columns */}
      <section aria-label="Classroom statistics">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatCard
            icon={Users}
            label="Students"
            value={analytics.totalStudents}
          />
          <StatCard
            featured
            className="lg:col-span-2"
            label="Avg completion"
            value={`${analytics.avgCompletion}%`}
            progress={analytics.avgCompletion}
          />
          <StatCard
            icon={AlertTriangle}
            label="At risk"
            value={analytics.atRisk.length}
          />
        </div>
      </section>

      <section aria-label="Roster">
        <Card className="rounded-2xl">
          <CardHeader>
            <CardTitle className="text-base">Roster (read-only)</CardTitle>
          </CardHeader>
          <CardContent>
            <RosterTable students={analytics.students} detailBase="/demonstrator/students" />
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
