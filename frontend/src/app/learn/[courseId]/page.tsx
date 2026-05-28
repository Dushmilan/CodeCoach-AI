'use client';

import { motion } from 'framer-motion';
import {
  ReaderIcon,
  LightningBoltIcon,
  StarIcon,
  ChevronRightIcon,
  CheckIcon,
  DotFilledIcon,
} from '@radix-ui/react-icons';
import { useParams } from 'next/navigation';
import { Header } from '@/components/header/Header';
import { useAuth } from '@/providers';
import Link from 'next/link';
import { ArrowLeftIcon } from '@radix-ui/react-icons';
import { useCourse } from '@/features/curriculum/use-curriculum.hook';
import { useEffect, useState, memo, ReactNode } from 'react';
import { FetchClient } from '@/lib/fetch-client';
import { cn } from '@/lib/utils';

const api = new FetchClient();

const languageIcon: Record<string, ReactNode> = {
  python: <ReaderIcon width={20} height={20} />,
  c: <LightningBoltIcon width={20} height={20} />,
  java: <StarIcon width={20} height={20} />,
};

const staggerItem = {
  hidden: { opacity: 0, y: 16 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: [0.32, 0.72, 0, 1] as const, delay: 0.1 + i * 0.08 },
  }),
};

const StaggeredProgressBar = memo(function StaggeredProgressBar({
  completed,
  total,
}: {
  completed: number;
  total: number;
}) {
  const pct = total > 0 ? (completed / total) * 100 : 0;
  return (
    <div>
      <div className="flex items-baseline justify-between mb-2">
        <span className="text-xs text-muted-foreground/50">Progress</span>
        <span className="text-sm font-medium text-foreground/60 tabular-nums font-mono">
          {completed}/{total}
        </span>
      </div>
      <div className="w-full h-[3px] rounded-full bg-white/5 overflow-hidden">
        <motion.div
          className="h-full rounded-full bg-primary/50"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 1.2, ease: [0.32, 0.72, 0, 1], delay: 0.3 }}
        />
      </div>
    </div>
  );
});

function SkeletonSidebar() {
  return (
    <aside className="w-72 flex-shrink-0 space-y-4">
      <div className="h-4 w-24 rounded-full bg-white/[0.03] animate-pulse" />
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-xl bg-white/[0.03] animate-pulse" />
        <div className="space-y-2">
          <div className="h-5 w-40 rounded-full bg-white/[0.03] animate-pulse" />
          <div className="h-3 w-56 rounded-full bg-white/[0.02] animate-pulse" />
        </div>
      </div>
      <div className="space-y-2">
        <div className="h-3 w-full rounded-full bg-white/[0.02] animate-pulse" />
        <div className="h-3 w-3/4 rounded-full bg-white/[0.02] animate-pulse" />
      </div>
    </aside>
  );
}

function SkeletonModules() {
  return (
    <div className="flex-1 space-y-8">
      {[1, 2, 3].map((m) => (
        <div key={m} className="space-y-3 pt-8 border-t border-white/[0.04]">
          <div className="h-5 w-32 rounded-full bg-white/[0.03] animate-pulse" />
          <div className="h-3 w-48 rounded-full bg-white/[0.02] animate-pulse" />
          {[1, 2, 3].map((l) => (
            <div key={l} className="flex items-center gap-3 py-2">
              <div className="h-4 w-4 rounded-full bg-white/[0.02] animate-pulse" />
              <div className="h-3 w-12 rounded-full bg-white/[0.02] animate-pulse" />
              <div className="h-3 w-32 rounded-full bg-white/[0.02] animate-pulse" />
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

export default function CoursePage() {
  const params = useParams();
  const courseId = params.courseId as string;
  const { course, isLoading, error } = useCourse(courseId);
  const { isAuthenticated } = useAuth();
  const [completedLessons, setCompletedLessons] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!isAuthenticated || !courseId) return;
    const fetchProgress = async () => {
      try {
        const data = await api.get<{ completed_lessons: string[] }>(`/api/progress/${courseId}`);
        setCompletedLessons(new Set(data.completed_lessons || []));
      } catch (err) {
        console.error('Failed to fetch progress:', err);
      }
    };
    fetchProgress();
  }, [courseId, isAuthenticated]);

  const totalLessons = course?.modules.reduce((acc, m) => acc + m.lessons.length, 0) || 0;

  return (
    <div className="min-h-[100dvh] bg-background text-foreground">
      <Header />

      <main className="max-w-6xl mx-auto px-6 pt-20 pb-32">
        {isLoading && (
          <div className="flex gap-16">
            <SkeletonSidebar />
            <SkeletonModules />
          </div>
        )}

        {error && (
          <div className="rounded-2xl bg-red-500/5 border border-red-500/10 p-6">
            <p className="text-sm text-red-400/80">{error}</p>
            <Link
              href="/learn"
              className="inline-flex items-center gap-1.5 text-xs text-muted-foreground/50 hover:text-foreground/70 mt-3 transition-colors"
            >
              <ArrowLeftIcon /> Back to learning paths
            </Link>
          </div>
        )}

        {!isLoading && !error && course && (
          <div className="flex flex-col lg:flex-row gap-16">
            <motion.aside
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.7, ease: [0.32, 0.72, 0, 1] }}
              className="w-full lg:w-72 flex-shrink-0"
            >
              <Link
                href="/learn"
                className="inline-flex items-center gap-1.5 text-xs text-muted-foreground/40 hover:text-foreground/60 mb-8 transition-colors"
              >
                <ArrowLeftIcon /> All paths
              </Link>

              <div className="flex items-center gap-3 mb-4">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/[0.04] text-foreground/50 ring-1 ring-white/5">
                  {languageIcon[course.language] || <ReaderIcon width={20} height={20} />}
                </span>
                <div>
                  <h1 className="text-lg font-semibold tracking-tight text-foreground/90">
                    {course.title}
                  </h1>
                  <span className="text-[11px] uppercase tracking-widest text-muted-foreground/40">
                    {course.language}
                  </span>
                </div>
              </div>

              <p className="text-sm text-muted-foreground/60 leading-relaxed mb-8">
                {course.description}
              </p>

              {isAuthenticated && (
                <StaggeredProgressBar
                  completed={completedLessons.size}
                  total={totalLessons}
                />
              )}
            </motion.aside>

            <motion.div
              initial="hidden"
              animate="visible"
              className="flex-1 min-w-0"
            >
              {course.modules.map((mod, mi) => {
                const moduleCompleted = mod.lessons.every(l => completedLessons.has(l.id));

                return (
                  <motion.section
                    key={mod.id}
                    custom={mi}
                    variants={staggerItem}
                    className={cn(
                      'pt-8 pb-8',
                      mi < course.modules.length - 1 && 'border-b border-white/[0.04]'
                    )}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <h2 className="text-sm font-medium text-foreground/80">
                        {mod.title}
                      </h2>
                      <span className="text-[10px] font-mono text-muted-foreground/30 tabular-nums">
                        {mi + 1}.{course.modules.length}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground/50 mb-5 leading-relaxed">
                      {mod.description}
                    </p>

                    <div className="space-y-1">
                      {mod.lessons.map((lesson) => {
                        const isComplete = completedLessons.has(lesson.id);

                        return (
                          <Link
                            key={lesson.id}
                            href={`/learn/lesson/${lesson.id}`}
                            className={cn(
                              'flex items-center gap-3 px-3 py-2.5 rounded-xl',
                              'transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]',
                              'hover:bg-white/[0.03] group'
                            )}
                          >
                            {isComplete ? (
                              <span className="flex h-4 w-4 items-center justify-center rounded-full bg-primary/15 text-primary">
                                <CheckIcon width={10} height={10} />
                              </span>
                            ) : (
                              <DotFilledIcon
                                width={16}
                                height={16}
                                className={cn(
                                  'flex-shrink-0',
                                  lesson.type === 'theory'
                                    ? 'text-muted-foreground/20'
                                    : 'text-muted-foreground/30'
                                )}
                              />
                            )}
                            <span className="text-[10px] uppercase tracking-wider text-muted-foreground/40 w-10 flex-shrink-0 font-mono">
                              {lesson.type === 'theory' ? 'Read' : 'Code'}
                            </span>
                            <span
                              className={cn(
                                'text-sm flex-1 transition-colors',
                                isComplete
                                  ? 'text-primary/70'
                                  : 'text-foreground/60 group-hover:text-foreground/80'
                              )}
                            >
                              {lesson.title}
                            </span>
                            <ChevronRightIcon
                              width={14}
                              height={14}
                              className="text-muted-foreground/15 group-hover:text-muted-foreground/40 transition-colors flex-shrink-0"
                            />
                          </Link>
                        );
                      })}
                    </div>
                  </motion.section>
                );
              })}
            </motion.div>
          </div>
        )}
      </main>
    </div>
  );
}
