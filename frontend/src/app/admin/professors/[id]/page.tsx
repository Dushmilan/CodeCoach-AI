"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { apiClient, type HierarchyProfessor } from "@/lib/api-client";

export default function ProfessorDetailPage() {
  const params = useParams();
  const rawId = (params as { id?: string | string[] } | null)?.id;
  const id = Array.isArray(rawId) ? rawId[0] : (rawId ?? "");
  const [professor, setProfessor] = useState<
    HierarchyProfessor | null | undefined
  >(undefined);

  useEffect(() => {
    let live = true;
    (async () => {
      const hierarchy = await apiClient.getAdminHierarchy();
      if (live) {
        setProfessor(
          hierarchy.professors.find((p) => p.id === id) ?? null,
        );
      }
    })();
    return () => {
      live = false;
    };
  }, [id]);

  if (professor === undefined) {
    return <p className="text-sm text-muted-foreground">Loading professor…</p>;
  }

  if (professor === null) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Professor not found</h1>
          <p className="text-muted-foreground text-sm mt-1">
            No professor matches this id in the hierarchy.
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

  const students = professor.classrooms.reduce(
    (sum, room) => sum + room.students,
    0,
  );

  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/admin/professors"
          className="text-xs text-muted-foreground hover:text-foreground"
        >
          ← Professors
        </Link>
        <div className="mt-2 flex items-center gap-3">
          <Avatar data-testid="professor-detail-avatar" className="h-10 w-10">
            <AvatarFallback>
              {professor.username.charAt(0).toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              {professor.username}
            </h1>
            <p className="text-muted-foreground text-sm mt-0.5">
              {professor.courses.length} courses ·{" "}
              {professor.classrooms.length} classrooms · {students} students
            </p>
          </div>
        </div>
      </div>

      <section aria-label="Courses">
        <Card className="rounded-2xl">
          <CardHeader>
            <CardTitle className="text-base">Courses</CardTitle>
          </CardHeader>
          <CardContent>
            {professor.courses.length === 0 ? (
              <p className="text-sm text-muted-foreground">No courses.</p>
            ) : (
              <ul className="text-sm">
                {professor.courses.map((course, i) => (
                  <li key={course.id}>
                    {i > 0 && <Separator />}
                    <div className="py-2">
                      {course.title}{" "}
                      <span className="text-muted-foreground">
                        ({course.lessons} lessons)
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </section>

      <section aria-label="Classrooms">
        <Card className="rounded-2xl">
          <CardHeader>
            <CardTitle className="text-base">Classrooms</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {professor.classrooms.length === 0 ? (
              <p className="text-sm text-muted-foreground">No classrooms.</p>
            ) : (
              professor.classrooms.map((room, i) => (
                <div key={room.id}>
                  {i > 0 && <Separator />}
                  <div className="rounded-2xl border border-border bg-muted/30 p-4 space-y-2">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-medium">{room.name}</span>
                      <span className="rounded-full bg-muted px-2.5 py-0.5 font-mono text-xs text-muted-foreground">
                        {room.invite_code}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {room.students} students · {room.avg_completion}% avg
                      completion
                    </p>
                    <Progress
                      value={room.avg_completion}
                      aria-label={`${room.name} completion`}
                      className="h-1.5"
                    />
                    <div className="flex flex-wrap gap-2 pt-1">
                      <Link
                        href={`/admin/classrooms/${room.id}`}
                        data-testid={`classroom-link-${room.id}`}
                        className="inline-block text-xs font-medium px-4 py-2 rounded-full bg-brand text-brand-foreground transition-colors hover:bg-brand/90"
                      >
                        Open classroom
                      </Link>
                      <Link
                        href={`/admin/classrooms/${room.id}#analytics`}
                        data-testid={`classroom-analytics-link-${room.id}`}
                        className="inline-block text-xs font-medium px-4 py-2 rounded-full bg-muted hover:bg-muted/70"
                      >
                        View analytics
                      </Link>
                    </div>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
