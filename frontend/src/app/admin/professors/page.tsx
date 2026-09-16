"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiClient, type HierarchyProfessor } from "@/lib/api-client";

export default function ProfessorsPage() {
  const [professors, setProfessors] = useState<HierarchyProfessor[] | null>(
    null,
  );

  useEffect(() => {
    let live = true;
    (async () => {
      const hierarchy = await apiClient.getAdminHierarchy();
      if (live) setProfessors(hierarchy.professors);
    })();
    return () => {
      live = false;
    };
  }, []);

  if (professors === null) {
    return <p className="text-sm text-muted-foreground">Loading professors…</p>;
  }

  if (professors.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Professors</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Admin → professors → classrooms drill-down.
          </p>
        </div>
        <p className="text-sm text-muted-foreground">No professors found.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Professors</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Admin → professors → classrooms drill-down.
        </p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {professors.map((prof) => {
          const students = prof.classrooms.reduce(
            (sum, room) => sum + room.students,
            0,
          );
          return (
            <Card key={prof.id}>
              <CardHeader>
                <CardTitle>{prof.username}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <p className="text-xs text-muted-foreground">
                  {prof.courses.length} courses · {prof.classrooms.length}{" "}
                  classrooms · {students} students
                </p>
                <Link
                  href={`/admin/professors/${prof.id}`}
                  data-testid={`professor-link-${prof.id}`}
                  className="inline-block text-xs font-medium px-3 py-1.5 rounded-full bg-primary text-primary-foreground"
                >
                  Open professor
                </Link>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
