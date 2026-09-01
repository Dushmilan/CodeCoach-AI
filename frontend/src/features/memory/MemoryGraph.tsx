"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Brain, AlertCircle } from "lucide-react";
import { EmptyState } from "@/components/ui/EmptyState";
import { Skeleton } from "@/components/ui/Skeleton";
import { memoryService, MemoryGraphResponse, TopicMemoryItem } from "./memory.service";

function energyCopy(topic: TopicMemoryItem): string {
  if (topic.daysSinceLastTouch !== null && topic.daysSinceLastTouch >= 6) {
    return "5-min refresher now, or you relearn it in 30 min later";
  }
  if (topic.dueCount > 0) {
    return `${topic.dueCount} bug${topic.dueCount > 1 ? "s" : ""} due — a minute of recall now saves a re-solve later`;
  }
  return `${topic.totalCards} card${topic.totalCards > 1 ? "s" : ""} tracked`;
}

export function MemoryGraph() {
  const [data, setData] = useState<MemoryGraphResponse | null>(null);
  const [error, setError] = useState(false);
  const router = useRouter();

  const fetchGraph = useCallback(() => {
    setError(false);
    memoryService
      .getGraph()
      .then((res) => setData(res))
      .catch(() => setError(true));
  }, []);

  useEffect(() => {
    let alive = true;
    setError(false);
    memoryService
      .getGraph()
      .then((res) => {
        if (alive) setData(res);
      })
      .catch(() => {
        if (alive) setError(true);
      });
    return () => {
      alive = false;
    };
  }, []);

  if (error) {
    return (
      <section aria-labelledby="memory-graph-heading" className="mb-8">
        <h2 id="memory-graph-heading" className="text-lg font-semibold mb-1">
          Your memory graph
        </h2>
        <EmptyState
          icon={AlertCircle}
          title="Couldn’t load your memory graph"
          description="Check your connection and try again."
          actionLabel="Retry"
          onAction={fetchGraph}
        />
      </section>
    );
  }

  if (!data) {
    return (
      <section aria-labelledby="memory-graph-heading" className="mb-8">
        <h2 id="memory-graph-heading" className="text-lg font-semibold mb-1">
          Your memory graph
        </h2>
        <div data-testid="memory-graph-loading" className="space-y-2" aria-busy="true">
          {[0, 1, 2].map((i) => (
            <div key={i} className="rounded-md border px-4 py-3 flex items-center justify-between gap-4">
              <div className="flex-1 space-y-2">
                <Skeleton width={120} height={14} />
                <Skeleton width={200} height={12} />
              </div>
              <Skeleton width={60} height={28} className="rounded-md" />
            </div>
          ))}
        </div>
      </section>
    );
  }

  if (data.topics.length === 0) {
    return (
      <section aria-labelledby="memory-graph-heading" className="mb-8">
        <h2 id="memory-graph-heading" className="text-lg font-semibold mb-1">
          Your memory graph
        </h2>
        <EmptyState
          icon={Brain}
          title="No memory yet"
          description="Solve a few problems to build your forgetting curve — your review queue will live here."
          actionLabel="Browse problems"
          onAction={() => router.push("/problems")}
        />
      </section>
    );
  }

  const sorted = [...data.topics].sort((a, b) => b.energyCostMinutes - a.energyCostMinutes);

  return (
    <section aria-labelledby="memory-graph-heading" className="mb-8">
      <h2 id="memory-graph-heading" className="text-lg font-semibold mb-1">
        Your memory graph
      </h2>
      <p className="text-sm text-muted-foreground mb-3">
        What you are about to forget — a minute now saves a re-solve later. {data.totalDue > 0 && `${data.totalDue} bug${data.totalDue > 1 ? "s" : ""} due.`}
      </p>
      <ul className="space-y-2">
        {sorted.map((t) => (
          <li
            key={t.topic}
            data-testid="memory-topic"
            className="flex items-center justify-between gap-4 rounded-md border px-4 py-3"
          >
            <div className="min-w-0">
              <div className="font-medium">{t.topic}</div>
              <p className="text-xs text-muted-foreground truncate">
                {t.daysSinceLastTouch !== null ? `${t.daysSinceLastTouch} days since ${t.topic.toLowerCase()}` : `${t.topic} tracked`}
                {" — "}
                {energyCopy(t)}
              </p>
              <p className="text-[11px] text-muted-foreground/70">
                {t.dueCount > 0 ? `${t.dueCount} due` : "no due cards"} · {t.totalCards} total ·{" "}
                {t.lapseCount > 0 ? `slipped ${t.lapseCount} times` : "no lapses"}
              </p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <span className="text-xs text-muted-foreground/60">{t.energyCostMinutes} min</span>
              <Link
                href={`/problems?category=${encodeURIComponent(t.topic)}`}
                className="rounded-md px-2.5 py-1 text-sm ring-1 ring-white/10 hover:bg-white/5"
              >
                Review
              </Link>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
