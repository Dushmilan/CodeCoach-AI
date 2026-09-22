"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { StatCard } from "@/components/instructor/InstructorWidgets";
import { apiClient, type ClassroomDetail } from "@/lib/api-client";
import { Code2, Users } from "lucide-react";

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
      } catch {
        // Status-only handling: unknown ids (404) and other failures both
        // render the not-found state. The status check stays trivial to
        // re-add via HttpError if a future detail message is needed.
        if (live) {
          setDetail(null);
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
          <h1 className="text-2xl font-bold tracking-tight">
            Classroom not found
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            No classroom matches this id.
          </p>
        </div>
        <Link
          href="/admin/professors"
          className="inline-block text-xs font-medium px-4 py-2 rounded-full bg-muted hover:bg-muted/70"
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
        <h1 className="text-2xl font-bold tracking-tight mt-1">
          {classroom.name}
        </h1>
        <p className="text-muted-foreground text-sm mt-1 font-mono">
          {classroom.invite_code}
        </p>
        {[classroom.term, classroom.schedule].filter(Boolean).length > 0 && (
          <p className="text-muted-foreground text-xs mt-1">
            {[classroom.term, classroom.schedule].filter(Boolean).join(" · ")}
          </p>
        )}
      </div>

      {/* Stats: bento rhythm, featured meter spans two columns */}
      <section aria-label="Classroom statistics">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            icon={Users}
            label="Students"
            value={analytics.total_students}
            testId="classroom-students"
          />
          <StatCard
            featured
            className="lg:col-span-2"
            label="Avg completion"
            value={`${analytics.avg_completion}%`}
            testId="classroom-avg-completion"
            progress={analytics.avg_completion}
          />
          <StatCard
            icon={Code2}
            label="Avg solved"
            value={analytics.avg_solved}
          />
        </div>
      </section>

      <section aria-label="Roster">
        <Card className="rounded-2xl">
          <CardHeader>
            <CardTitle className="text-base">Roster</CardTitle>
          </CardHeader>
          <CardContent>
            {analytics.students.length === 0 ? (
              <p className="text-sm text-muted-foreground">No students yet.</p>
            ) : (
              <ul className="text-sm">
                {analytics.students.map((student, i) => (
                  <li key={student.user_id}>
                    {i > 0 && <Separator />}
                    <div className="flex items-center gap-3 py-2.5">
                      <Avatar data-testid="roster-avatar" className="h-7 w-7">
                        <AvatarFallback>
                          {student.user_id.charAt(0).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      <span className="font-medium">{student.user_id}</span>
                      <span className="text-muted-foreground">
                        ({student.completion_pct}% · {student.solved} solved)
                      </span>
                      <Progress
                        value={student.completion_pct}
                        aria-label={`${student.user_id} completion`}
                        className="ml-auto h-1.5 w-24"
                      />
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </section>

      <section id="analytics" data-testid="classroom-analytics">
        <Card className="rounded-2xl">
          <CardHeader>
            <CardTitle className="text-base">Analytics</CardTitle>
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
