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
          <h1 className="text-2xl font-bold tracking-tight">Courses</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Courses you created through the verified content pipeline (ANIMATION
            gate enforced).
          </p>
        </div>
        <Link
          href="/professor/curriculum"
          className="text-xs font-medium px-4 py-2 rounded-full bg-brand text-brand-foreground transition-colors hover:bg-brand/90"
        >
          Create / edit in curriculum
        </Link>
      </div>

      <section aria-label="Course catalog">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2" data-testid="prof-courses">
          {courses.map((c) => (
            <Card key={c.id} className="rounded-2xl">
              <CardHeader>
                <CardTitle className="text-base">{c.title}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <p className="text-sm text-muted-foreground">{c.description}</p>
                <p className="text-xs text-muted-foreground">
                  By {ownerName(c.createdBy)} · {c.modules} modules ·{" "}
                  {c.lessons} lessons
                </p>
                <p className="text-xs">
                  <span className="inline-flex items-center rounded-full bg-success/10 text-success ring-1 ring-inset ring-success/20 px-2.5 py-0.5 font-medium">
                    {c.validation.pipeline} · animation{" "}
                    {c.validation.animationGate} ({c.validation.steps} steps)
                  </span>
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
