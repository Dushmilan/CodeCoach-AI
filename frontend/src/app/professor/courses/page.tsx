"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getCourses, getProfessors } from "@/features/instructor/demo";

export default function ProfessorCoursesPage() {
  const courses = getCourses();
  const professors = getProfessors();
  const ownerName = (id: string) => professors.find((p) => p.id === id)?.name ?? id;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Courses</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Courses you created through the verified content pipeline (ANIMATION gate enforced).
          </p>
        </div>
        <Link
          href="/professor/curriculum"
          className="text-xs font-medium px-4 py-2 rounded-full bg-primary text-primary-foreground"
        >
          Create / edit in curriculum
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4" data-testid="prof-courses">
        {courses.map((c) => (
          <Card key={c.id}>
            <CardHeader>
              <CardTitle>{c.title}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <p className="text-sm text-muted-foreground">{c.description}</p>
              <p className="text-xs text-muted-foreground">
                By {ownerName(c.createdBy)} · {c.modules} modules · {c.lessons} lessons
              </p>
              <p className="text-xs">
                <span className="inline-flex items-center rounded-full bg-green-500/10 text-green-500 px-2 py-0.5 font-medium">
                  {c.validation.pipeline} · animation {c.validation.animationGate} ({c.validation.steps} steps)
                </span>
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
