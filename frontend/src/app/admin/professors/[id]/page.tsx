"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
        <h1 className="text-2xl font-bold mt-1">{professor.username}</h1>
        <p className="text-muted-foreground text-sm mt-1">
          {professor.courses.length} courses · {professor.classrooms.length}{" "}
          classrooms · {students} students
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Courses</CardTitle>
        </CardHeader>
        <CardContent>
          {professor.courses.length === 0 ? (
            <p className="text-sm text-muted-foreground">No courses.</p>
          ) : (
            <ul className="text-sm space-y-1">
              {professor.courses.map((course) => (
                <li key={course.id}>
                  {course.title}{" "}
                  <span className="text-muted-foreground">
                    ({course.lessons} lessons)
                  </span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Classrooms</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {professor.classrooms.length === 0 ? (
            <p className="text-sm text-muted-foreground">No classrooms.</p>
          ) : (
            professor.classrooms.map((room) => (
              <div
                key={room.id}
                className="rounded-lg border border-border p-3 space-y-1"
              >
                <div className="text-sm font-medium">{room.name}</div>
                <p className="text-xs text-muted-foreground">
                  {room.invite_code} · {room.students} students ·{" "}
                  {room.avg_completion}% avg completion
                </p>
                <div className="flex flex-wrap gap-2 pt-1">
                  <Link
                    href={`/admin/classrooms/${room.id}`}
                    data-testid={`classroom-link-${room.id}`}
                    className="inline-block text-xs font-medium px-3 py-1.5 rounded-full bg-primary text-primary-foreground"
                  >
                    Open classroom
                  </Link>
                  <Link
                    href={`/admin/classrooms/${room.id}#analytics`}
                    data-testid={`classroom-analytics-link-${room.id}`}
                    className="inline-block text-xs font-medium px-3 py-1.5 rounded-full bg-muted hover:bg-muted/70"
                  >
                    View analytics
                  </Link>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
