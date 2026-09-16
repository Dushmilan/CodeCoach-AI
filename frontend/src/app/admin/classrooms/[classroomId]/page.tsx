"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiClient, type ClassroomDetail } from "@/lib/api-client";
import { HttpError } from "@/lib/fetch-client";

export default function AdminClassroomDetailPage() {
  const params = useParams();
  const rawId = (params as { classroomId?: string | string[] } | null)
    ?.classroomId;
  const classroomId = Array.isArray(rawId) ? (rawId[0] ?? "") : (rawId ?? "");
  const [detail, setDetail] = useState<ClassroomDetail | null | undefined>(
    undefined,
  );

  useEffect(() => {
    let live = true;
    (async () => {
      try {
        const loaded = await apiClient.getClassroomDetail(classroomId);
        if (live) setDetail(loaded);
      } catch (error) {
        if (live) {
          if (error instanceof HttpError && error.status === 404) {
            setDetail(null);
          } else {
            setDetail(null);
          }
        }
      }
    })();
    return () => {
      live = false;
    };
  }, [classroomId]);

  if (detail === undefined) {
    return <p className="text-sm text-muted-foreground">Loading classroom…</p>;
  }

  if (detail === null) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Classroom not found</h1>
          <p className="text-muted-foreground text-sm mt-1">
            No classroom matches this id.
          </p>
        </div>
        <Link
          href="/admin/professors"
          className="inline-block text-xs font-medium px-3 py-1.5 rounded-full bg-muted hover:bg-muted/70"
        >
          Back to professors
        </Link>
      </div>
    );
  }

  const { classroom, analytics } = detail;

  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/admin/professors"
          className="text-xs text-muted-foreground hover:text-foreground"
        >
          ← Professors
        </Link>
        <h1 className="text-2xl font-bold mt-1">{classroom.name}</h1>
        <p className="text-muted-foreground text-sm mt-1">{classroom.invite_code}</p>
        {[classroom.term, classroom.schedule].filter(Boolean).length > 0 && (
          <p className="text-muted-foreground text-xs mt-1">
            {[classroom.term, classroom.schedule].filter(Boolean).join(" · ")}
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Students</CardTitle>
          </CardHeader>
          <CardContent>
            <p data-testid="classroom-students" className="text-2xl font-bold">
              {analytics.total_students}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Avg completion</CardTitle>
          </CardHeader>
          <CardContent>
            <p
              data-testid="classroom-avg-completion"
              className="text-2xl font-bold"
            >
              {analytics.avg_completion}%
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Roster</CardTitle>
        </CardHeader>
        <CardContent>
          {analytics.students.length === 0 ? (
            <p className="text-sm text-muted-foreground">No students yet.</p>
          ) : (
            <ul className="text-sm space-y-1">
              {analytics.students.map((student) => (
                <li key={student.user_id}>
                  {student.user_id}{" "}
                  <span className="text-muted-foreground">
                    ({student.completion_pct}% · {student.solved} solved)
                  </span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <section id="analytics" data-testid="classroom-analytics">
        <Card>
          <CardHeader>
            <CardTitle>Analytics</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              {analytics.total_students} students · {analytics.avg_completion}%
              avg completion · {analytics.avg_solved} avg solved
            </p>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
