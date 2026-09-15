"use client";

import Link from "next/link";
import { notFound, useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getStudentDetail } from "@/features/instructor/demo";

export default function ProfessorStudentDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const detail = getStudentDetail(id);
  if (!detail.enrollment) notFound();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{detail.enrollment.name}</h1>
        <p className="text-muted-foreground text-sm mt-1">
          @{detail.enrollment.username} · enrolled {detail.enrollment.enrolledAt}
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Progress</CardTitle>
        </CardHeader>
        <CardContent data-testid="student-progress" className="space-y-2">
          {detail.rows.map((r) => (
            <div key={r.userId + r.classroomId} className="text-sm">
              {r.completedLessons} lessons · {r.solved} solved / {r.attempted} attempted · last active {r.lastActive}
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Coaching signals</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {detail.signals.length === 0 ? (
            <p className="text-xs text-muted-foreground">No plateau signals for this student.</p>
          ) : (
            detail.signals.map((s, i) => (
              <div key={i} className="text-xs p-2 rounded-lg bg-muted/50">
                <span className="font-medium">{s.title}</span>
                <span className="text-muted-foreground"> — {s.detail}</span>
              </div>
            ))
          )}
          <Link
            href="/problems"
            className="inline-block text-xs font-medium px-3 py-1.5 rounded-full bg-primary text-primary-foreground"
          >
            Coach this student
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
