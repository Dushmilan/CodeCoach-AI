"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function StatCard({
  label,
  value,
  sub,
  testId,
}: {
  label: string;
  value: string | number;
  sub?: string;
  testId?: string;
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold" data-testid={testId}>
          {value}
        </div>
        {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
      </CardContent>
    </Card>
  );
}

export function MasteryBars({
  items,
}: {
  items: Array<{ label: string; avgMastery: number }>;
}) {
  return (
    <div className="space-y-2" data-testid="mastery-bars">
      {items.map((m) => (
        <div key={m.label}>
          <div className="flex justify-between text-xs mb-1">
            <span className="font-medium">{m.label}</span>
            <span className="text-muted-foreground">{Math.round(m.avgMastery * 100)}%</span>
          </div>
          <div className="h-2 rounded-full bg-muted overflow-hidden">
            <div
              className="h-full rounded-full bg-primary"
              style={{ width: `${Math.round(m.avgMastery * 100)}%` }}
            />
          </div>
        </div>
      ))}
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
                <a href={`${detailBase}/${s.userId}`} className="font-medium hover:underline">
                  {s.name}
                </a>
                <span className="text-muted-foreground"> @{s.username}</span>
              </td>
              <td className="py-2 pr-4">{s.completionPct}%</td>
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
