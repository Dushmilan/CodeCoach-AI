"use client";

import Link from "next/link";
import { notFound, useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RosterTable, StatCard } from "@/components/instructor/InstructorWidgets";
import { getClassroom, getClassAnalytics } from "@/features/instructor/demo";

export default function ProfessorClassroomDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const classroom = getClassroom(id);
  if (!classroom) notFound();
  const analytics = getClassAnalytics(id);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">{classroom.name}</h1>
          <p className="text-muted-foreground text-sm mt-1">
            {classroom.term} · {classroom.schedule} · Invite code:{" "}
            <span className="font-mono font-medium text-foreground">{classroom.inviteCode}</span>
          </p>
        </div>
        <Link
          href="/professor/analytics"
          className="text-xs font-medium px-4 py-2 rounded-full bg-muted hover:bg-muted/70"
        >
          View analytics
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard label="Students" value={analytics.totalStudents} />
        <StatCard label="Avg completion" value={`${analytics.avgCompletion}%`} />
        <StatCard label="At risk" value={analytics.atRisk.length} sub="Completion < 35% or ≥10 unsolved attempts" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Roster — manage enrollment</CardTitle>
        </CardHeader>
        <CardContent>
          <RosterTable students={analytics.students} detailBase="/professor/students" />
          <p className="text-xs text-muted-foreground mt-3">
            Professors can add/remove students and TAs; demonstrators get read-only access.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
