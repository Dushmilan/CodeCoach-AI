"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
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
          <h1 className="text-2xl font-bold tracking-tight">Professors</h1>
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
        <h1 className="text-2xl font-bold tracking-tight">Professors</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Admin → professors → classrooms drill-down.
        </p>
      </div>
      <section aria-label="Professor roster">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {professors.map((prof) => {
            const students = prof.classrooms.reduce(
              (sum, room) => sum + room.students,
              0,
            );
            return (
              <Card key={prof.id} className="rounded-2xl">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <Avatar data-testid="professor-avatar" className="h-9 w-9">
                      <AvatarFallback>
                        {prof.username.charAt(0).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    <CardTitle className="text-base">
                      {prof.username}
                    </CardTitle>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-xs text-muted-foreground">
                    {prof.courses.length} courses · {prof.classrooms.length}{" "}
                    classrooms · {students} students
                  </p>
                  <Link
                    href={`/admin/professors/${prof.id}`}
                    data-testid={`professor-link-${prof.id}`}
                    className="inline-block text-xs font-medium px-4 py-2 rounded-full bg-brand text-brand-foreground transition-colors hover:bg-brand/90"
                  >
                    Open professor
                  </Link>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>
    </div>
  );
}
