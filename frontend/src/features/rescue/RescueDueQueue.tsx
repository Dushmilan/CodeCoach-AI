"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { rescueService, RescueQueueItem } from "./rescue.service";

interface RescueDueQueueProps {
  /**
   * Maps a question id to its display title. Unresolved ids fall back to the
   * raw id so an item is never rendered as blank.
   */
  resolveTitle?: (questionId: string) => string | undefined;
}

/**
 * "Back tomorrow" — the durable half of the never-alone rescue contract.
 * Problems the learner set aside resurface here as tiny re-entry steps.
 * Renders nothing when there is nothing due (or the API is unavailable).
 */
export function RescueDueQueue({ resolveTitle }: RescueDueQueueProps) {
  const [items, setItems] = useState<RescueQueueItem[] | null>(null);

  useEffect(() => {
    let alive = true;
    rescueService
      .getDue()
      .then((res) => {
        if (alive) setItems(res.items);
      })
      .catch(() => {
        if (alive) setItems([]);
      });
    return () => {
      alive = false;
    };
  }, []);

  if (!items || items.length === 0) return null;

  const handleDismiss = async (questionId: string) => {
    setItems((prev) => prev?.filter((i) => i.question_id !== questionId) ?? []);
    try {
      await rescueService.dismiss(questionId);
    } catch {
      // Server state stays; the item will come back on next load — acceptable
      // for a best-effort UI action (dismissal remains server-authoritative).
    }
  };

  return (
    <section aria-labelledby="rescue-due-heading" className="mb-8">
      <h2 id="rescue-due-heading" className="text-lg font-semibold mb-1">
        Back tomorrow
      </h2>
      <p className="text-sm text-muted-foreground mb-3">
        Problems you set aside — tiny steps to re-enter today.
      </p>
      <ul className="space-y-2">
        {items.map((item) => {
          const title = resolveTitle?.(item.question_id) ?? item.question_id;
          return (
            <li
              key={item.id}
              data-testid="rescue-due-item"
              className="flex items-center justify-between gap-4 rounded-md border px-4 py-3"
            >
              <div className="min-w-0">
                <Link
                  href={`/problems/${encodeURIComponent(item.question_id)}`}
                  className="font-medium hover:underline"
                >
                  {title}
                </Link>
                {item.resurface_count > 0 && (
                  <span className="ml-2 text-xs text-muted-foreground whitespace-nowrap">
                    seen {item.resurface_count + 1} times
                  </span>
                )}
              </div>
              <button
                type="button"
                onClick={() => handleDismiss(item.question_id)}
                className="text-sm text-muted-foreground hover:text-foreground shrink-0"
              >
                Dismiss
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
