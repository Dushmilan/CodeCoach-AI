"use client";

import { notFound, useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getStudentDetail } from "@/features/instructor/demo";

export default function DemonstratorStudentDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const detail = getStudentDetail(id);
  if (!detail.enrollment) notFound();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          {detail.enrollment.name}
        </h1>
        <p className="text-muted-foreground text-sm mt-1">
          @{detail.enrollment.username} · enrolled{" "}
          {detail.enrollment.enrolledAt} · read-only
        </p>
      </div>

      <section aria-label="Progress">
        <Card className="rounded-2xl">
          <CardHeader>
            <CardTitle className="text-base">Progress</CardTitle>
          </CardHeader>
          <CardContent data-testid="ta-student-progress" className="space-y-2">
            {detail.rows.map((r) => (
              <div key={r.userId + r.classroomId} className="text-sm">
                {r.completedLessons} lessons · {r.solved} solved /{" "}
                {r.attempted} attempted · last active {r.lastActive}
              </div>
            ))}
          </CardContent>
        </Card>
      </section>

      <section aria-label="Coaching context">
        <Card className="rounded-2xl">
          <CardHeader>
            <CardTitle className="text-base">Coaching context</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {detail.signals.length === 0 ? (
              <p className="text-xs text-muted-foreground">
                No plateau signals for this student.
              </p>
            ) : (
              detail.signals.map((s, i) => (
                <div key={i} className="text-xs p-3 rounded-2xl bg-muted/50">
                  <span className="font-medium">{s.title}</span>
                  <span className="text-muted-foreground">: {s.detail}</span>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
