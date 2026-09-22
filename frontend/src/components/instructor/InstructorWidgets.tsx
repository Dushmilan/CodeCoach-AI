"use client";

import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";

/**
 * Shared role-surface widgets (issues #292/#230).
 * Bento rhythm: stat cells are marked with data-stat, an optional featured
 * cell carries a span className, and progress uses the owned Progress
 * primitive so every meter is an accessible progressbar.
 */
export function StatCard({
  label,
  value,
  sub,
  testId,
  featured = false,
  progress,
  icon: Icon,
  className,
}: {
  label: string;
  value: string | number;
  sub?: string;
  testId?: string;
  /** Visual variation: emerald tinted hero cell with a larger value. */
  featured?: boolean;
  /** Optional meter rendered under the value (0-100). */
  progress?: number;
  icon?: React.ElementType;
  className?: string;
}) {
  return (
    <Card
      data-stat
      className={cn(
        "rounded-2xl p-5",
        featured && "border-primary/20 bg-primary/[0.04]",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <p className="text-xs font-medium text-muted-foreground">{label}</p>
        {Icon && (
          <span
            aria-hidden="true"
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-2xl bg-brand/10 text-brand ring-1 ring-brand/20"
          >
            <Icon className="h-4 w-4" />
          </span>
        )}
      </div>
      <div
        data-testid={testId}
        className={cn(
          "mt-1 text-3xl font-semibold tabular-nums tracking-tight",
          featured && "text-4xl",
        )}
      >
        {value}
      </div>
      {sub && <p className="mt-1 text-xs text-muted-foreground">{sub}</p>}
      {progress !== undefined && (
        <div className="mt-3">
          <Progress value={progress} />
        </div>
      )}
    </Card>
  );
}

export function MasteryBars({
  items,
}: {
  items: Array<{ label: string; avgMastery: number }>;
}) {
  return (
    <div className="space-y-3" data-testid="mastery-bars">
      {items.map((m) => {
        const pct = Math.round(m.avgMastery * 100);
        return (
          <div key={m.label}>
            <div className="flex justify-between text-xs mb-1">
              <span className="font-medium">{m.label}</span>
              <span className="text-muted-foreground">{pct}%</span>
            </div>
            <Progress value={pct} aria-label={m.label} />
          </div>
        );
      })}
    </div>
  );
}

export function RosterTable({
  students,
  detailBase,
}: {
  students: Array<{
    userId: string;
    name: string;
    username: string;
    completionPct: number;
    solved: number;
    attempted: number;
    lastActive: string;
  }>;
  detailBase: string;
}) {
  return (
    <div className="overflow-x-auto" data-testid="roster-table">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-muted-foreground border-b border-border">
            <th className="py-2 pr-4 font-medium">Student</th>
            <th className="py-2 pr-4 font-medium">Completion</th>
            <th className="py-2 pr-4 font-medium">Solved</th>
            <th className="py-2 pr-4 font-medium">Attempts</th>
            <th className="py-2 pr-4 font-medium">Last active</th>
          </tr>
        </thead>
        <tbody>
          {students.map((s) => (
            <tr key={s.userId} className="border-b border-border/50">
              <td className="py-2 pr-4">
                <div className="flex items-center gap-2">
                  <Avatar data-testid="roster-avatar" className="h-7 w-7">
                    <AvatarFallback>
                      {s.name.charAt(0).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <a href={`${detailBase}/${s.userId}`} className="font-medium hover:underline">
                      {s.name}
                    </a>
                    <span className="text-muted-foreground"> @{s.username}</span>
                  </div>
                </div>
              </td>
              <td className="py-2 pr-4">
                <div className="flex items-center gap-2">
                  <Progress
                    value={s.completionPct}
                    aria-label={`${s.name} completion`}
                    className="h-1.5 w-16"
                  />
                  <span className="tabular-nums">{s.completionPct}%</span>
                </div>
              </td>
              <td className="py-2 pr-4">{s.solved}</td>
              <td className="py-2 pr-4">{s.attempted}</td>
              <td className="py-2 pr-4 text-muted-foreground">{s.lastActive}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
