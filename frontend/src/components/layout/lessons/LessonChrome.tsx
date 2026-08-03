import Link from 'next/link';
import { ArrowLeft, ArrowRight, BookOpen, Code } from 'lucide-react';
import { cn } from '@/lib/utils';
import { LessonSummary } from '@/types';

interface LessonChromeProps {
  lesson: LessonSummary;
  prevId: string | null;
  nextId: string | null;
}

export function LessonChrome({ lesson, prevId, nextId }: LessonChromeProps) {
  const isExercise = lesson.type === 'exercise';

  return (
    <div className="flex items-center justify-between mb-6">
      <div className="flex items-center gap-3">
        <Link
          href={`/learn/${lesson.course_id}`}
          className="flex items-center gap-1.5 text-xs text-muted-foreground/40 hover:text-foreground/60 transition-colors"
        >
          <ArrowLeft width={12} height={12} /> Back
        </Link>
        <span className="text-muted-foreground/15">/</span>
        <div className="flex items-center gap-2.5">
          <span
            className={cn(
              'flex h-7 w-7 items-center justify-center rounded-lg',
              isExercise ? 'bg-emerald-500/8' : 'bg-white/[0.04]',
            )}
          >
            {isExercise ? (
              <Code width={14} height={14} className="text-emerald-500/60" />
            ) : (
              <BookOpen width={14} height={14} className="text-muted-foreground/40" />
            )}
          </span>
          <div>
            <h1 className="text-sm font-medium tracking-tight text-foreground/80">
              {lesson.title}
            </h1>
            <span
              className={cn(
                'text-[10px] uppercase tracking-widest',
                isExercise ? 'text-emerald-500/50' : 'text-muted-foreground/30',
              )}
            >
              {isExercise ? 'Coding Exercise' : 'Theory Lesson'}
            </span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-1">
        {prevId && (
          <Link
            href={`/learn/lesson/${prevId}`}
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-white/[0.06] hover:bg-white/[0.04] transition-all"
          >
            <ArrowLeft width={14} height={14} className="text-muted-foreground/40" />
          </Link>
        )}
        {nextId && (
          <Link
            href={`/learn/lesson/${nextId}`}
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-white/[0.06] hover:bg-white/[0.04] transition-all"
          >
            <ArrowRight width={14} height={14} className="text-muted-foreground/40" />
          </Link>
        )}
      </div>
    </div>
  );
}
