"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { reviewService, ReviewCardItem } from "./review.service";

interface ReviewsDueQueueProps {
  /**
   * Maps a question id to its display title. Unresolved ids fall back to the
   * raw id so an item is never rendered as blank.
   */
  resolveTitle?: (questionId: string) => string | undefined;
}

/** SM-2 quality for each button. "Forgot" re-opens the bug server-side. */
const GRADE_ACTIONS = [
  { label: "Forgot", quality: 2 },
  { label: "Got it", quality: 4 },
  { label: "Easy", quality: 5 },
] as const;

/**
 * "Review your past bugs" — mistake-memory's spaced-repetition queue.
 * Cards resurface the learner's own recurring errors at SM-2 intervals.
 * Renders nothing when there is nothing due (or the API is unavailable).
 */
export function ReviewsDueQueue({ resolveTitle }: ReviewsDueQueueProps) {
  const [cards, setCards] = useState<ReviewCardItem[] | null>(null);

  useEffect(() => {
    let alive = true;
    reviewService
      .getDue()
      .then((res) => {
        if (alive) setCards(res.cards);
      })
      .catch(() => {
        if (alive) setCards([]);
      });
    return () => {
      alive = false;
    };
  }, []);

  if (!cards || cards.length === 0) return null;

  const handleGrade = async (cardId: string, quality: number) => {
    // Optimistic removal; on failure re-sync from the server rather than
    // replaying possibly-stale local state (rapid multi-card edits).
    setCards((prev) => prev?.filter((c) => c.id !== cardId) ?? []);
    try {
      await reviewService.grade(cardId, quality);
    } catch {
      try {
        const res = await reviewService.getDue();
        setCards(res.cards);
      } catch {
        // Keep optimistic removal; the queue reappears on next load.
      }
    }
  };

  return (
    <section aria-labelledby="reviews-due-heading" className="mb-8">
      <h2 id="reviews-due-heading" className="text-lg font-semibold mb-1">
        Review your past bugs
      </h2>
      <p className="text-sm text-muted-foreground mb-3">
        Errors you have conquered — a minute of recall now saves a re-solve
        later.
      </p>
      <ul className="space-y-2">
        {cards.map((card) => {
          const title = resolveTitle?.(card.question_id) ?? card.question_id;
          return (
            <li
              key={card.id}
              data-testid="review-due-item"
              className="flex items-center justify-between gap-4 rounded-md border px-4 py-3"
            >
              <div className="min-w-0">
                <Link
                  href={`/problems/${encodeURIComponent(card.question_id)}`}
                  className="font-medium hover:underline"
                >
                  {title}
                </Link>
                <p className="text-xs text-muted-foreground truncate">
                  {card.error_signature}
                  {card.lapses > 0 && (
                    <span className="ml-2 whitespace-nowrap">
                      slipped {card.lapses}{" "}
                      {card.lapses === 1 ? "time" : "times"}
                    </span>
                  )}
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {GRADE_ACTIONS.map(({ label, quality }) => (
                  <button
                    key={quality}
                    type="button"
                    onClick={() => handleGrade(card.id, quality)}
                    className="rounded-md px-2.5 py-1 text-sm ring-1 ring-white/10 hover:bg-white/5"
                  >
                    {label}
                  </button>
                ))}
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
