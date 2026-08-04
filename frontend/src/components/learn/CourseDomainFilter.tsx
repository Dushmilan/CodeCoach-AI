"use client";

import { useState, ReactNode } from "react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";
import type { CourseSummary } from "@/types";

export type CourseDomain = "se" | "ml" | "ai";

export const DOMAIN_TABS: { value: "all" | CourseDomain; label: string }[] = [
  { value: "all", label: "All" },
  { value: "se", label: "Software Engineering" },
  { value: "ml", label: "Machine Learning" },
  { value: "ai", label: "AI" },
];

interface CourseDomainFilterProps {
  courses: CourseSummary[];
  renderCourse: (course: CourseSummary) => ReactNode;
  className?: string;
}

export function CourseDomainFilter({
  courses,
  renderCourse,
  className,
}: CourseDomainFilterProps) {
  const [active, setActive] = useState<"all" | CourseDomain>("all");
  const filtered =
    active === "all" ? courses : courses.filter((c) => c.domain === active);

  return (
    <div className={className}>
      <Tabs value={active} onValueChange={(v) => setActive(v as "all" | CourseDomain)}>
        <TabsList className="h-auto w-auto gap-1 rounded-full bg-white/[0.03] p-1 ring-1 ring-white/[0.06]">
          {DOMAIN_TABS.map((tab) => (
            <TabsTrigger
              key={tab.value}
              value={tab.value}
              className={cn(
                "rounded-full px-4 py-1.5 text-xs font-medium tracking-wide data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-none",
              )}
            >
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-5">
        {filtered.map((course, i) => (
          <div key={course.id} className={i === 0 && active === "all" ? "md:col-span-2" : ""}>
            {renderCourse(course)}
          </div>
        ))}
      </div>
    </div>
  );
}
