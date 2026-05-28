'use client';

import { motion } from 'framer-motion';
import { ReaderIcon, LightningBoltIcon, StarIcon } from '@radix-ui/react-icons';
import Link from 'next/link';
import { useAuth } from '@/providers';
import { useCurriculum } from '@/features/curriculum/use-curriculum.hook';
import { Header } from '@/components/header/Header';
import { useEffect, useState, memo, ReactNode } from 'react';
import { FetchClient } from '@/lib/fetch-client';
import { cn } from '@/lib/utils';
import type { CourseSummary } from '@/types';

const api = new FetchClient();

interface ProgressMap {
  [courseId: string]: {
    completed_lessons: string[];
    last_accessed_lesson_id: string | null;
  };
}

const languageConfig: Record<string, { icon: ReactNode; label: string }> = {
  python: { icon: <ReaderIcon width={20} height={20} />, label: 'Python' },
  c: { icon: <LightningBoltIcon width={20} height={20} />, label: 'C' },
  java: { icon: <StarIcon width={20} height={20} />, label: 'Java' },
};

const staggerVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.7,
      ease: [0.32, 0.72, 0, 1] as const,
      delay: 0.1 + i * 0.12,
    },
  }),
};

const ProgressBar = memo(function ProgressBar({ value }: { value: number }) {
  return (
    <div className="w-full h-[3px] rounded-full bg-white/5 overflow-hidden">
      <motion.div
        className="h-full rounded-full bg-primary/50"
        initial={{ width: 0 }}
        animate={{ width: `${value}%` }}
        transition={{ duration: 1.2, ease: [0.32, 0.72, 0, 1], delay: 0.4 }}
      />
    </div>
  );
});

interface CourseCardProps {
  course: CourseSummary;
  completedCount: number;
  lastLessonId: string | null;
  isAuthenticated: boolean;
  accentBorder: string;
}

const CourseCard = memo(function CourseCard({
  course,
  completedCount,
  lastLessonId,
  isAuthenticated,
  accentBorder,
}: CourseCardProps) {
  const config = languageConfig[course.language];
  const [hovered, setHovered] = useState(false);

  return (
    <motion.div
      layout
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <Link
        href={lastLessonId ? `/learn/lesson/${lastLessonId}` : `/learn/${course.id}`}
        className={cn(
          'group relative block rounded-3xl border border-white/[0.06] bg-white/[0.02] p-8',
          'transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)]',
          'hover:bg-white/[0.04]',
          accentBorder
        )}
        style={{
          boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.06)',
        }}
      >
        <div className="flex items-start justify-between mb-5">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/[0.04] text-foreground/60 ring-1 ring-white/5">
              {config?.icon || <ReaderIcon width={20} height={20} />}
            </span>
            <div>
              <h2 className="text-base font-medium tracking-tight text-foreground/90">
                {course.title}
              </h2>
              <span className="text-[11px] uppercase tracking-widest text-muted-foreground/40">
                {config?.label || course.language}
              </span>
            </div>
          </div>
          <div className="text-right">
            <span className="text-lg font-semibold tracking-tight text-foreground/70">
              {course.progress}%
            </span>
          </div>
        </div>

        <p className="text-sm text-muted-foreground/60 leading-relaxed mb-6 line-clamp-2">
          {course.description}
        </p>

        <ProgressBar value={course.progress} />

        <div className="flex items-center justify-between mt-3">
          {isAuthenticated && completedCount > 0 && (
            <span className="text-[11px] text-muted-foreground/40">
              {completedCount} completed
            </span>
          )}
          {isAuthenticated && lastLessonId && (
            <span className="ml-auto text-[11px] text-primary/60 flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity duration-500">
              Continue
              <span className="inline-block transition-transform duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] group-hover:translate-x-0.5">
                &rarr;
              </span>
            </span>
          )}
        </div>
      </Link>
    </motion.div>
  );
});

function SkeletonCard({ className }: { className?: string }) {
  return (
    <div className={cn('rounded-3xl border border-white/[0.04] bg-white/[0.01] p-8', className)}>
      <div className="flex items-center gap-3 mb-5">
        <div className="h-10 w-10 rounded-xl bg-white/[0.03] animate-pulse" />
        <div className="space-y-2">
          <div className="h-4 w-32 rounded-full bg-white/[0.03] animate-pulse" />
          <div className="h-3 w-16 rounded-full bg-white/[0.02] animate-pulse" />
        </div>
      </div>
      <div className="space-y-2 mb-6">
        <div className="h-3 w-full rounded-full bg-white/[0.02] animate-pulse" />
        <div className="h-3 w-3/4 rounded-full bg-white/[0.02] animate-pulse" />
      </div>
      <div className="h-[3px] w-full rounded-full bg-white/[0.02] animate-pulse" />
    </div>
  );
}

export default function LearnPage() {
  const { courses, isLoading, error } = useCurriculum();
  const { isAuthenticated } = useAuth();
  const [progressMap, setProgressMap] = useState<ProgressMap>({});

  useEffect(() => {
    if (!isAuthenticated) return;
    const fetchProgress = async () => {
      try {
        const data = await api.get<{ progress: any[] }>('/api/progress/');
        const map: ProgressMap = {};
        data.progress.forEach((p: any) => {
          map[p.course_id] = {
            completed_lessons: p.completed_lessons || [],
            last_accessed_lesson_id: p.last_accessed_lesson_id || null,
          };
        });
        setProgressMap(map);
      } catch (err) {
        console.error('Failed to fetch progress:', err);
      }
    };
    fetchProgress();
  }, [isAuthenticated]);

  return (
    <div className="min-h-[100dvh] bg-background text-foreground">
      <Header />

      <main className="max-w-6xl mx-auto px-6 pt-20 pb-32">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.32, 0.72, 0, 1] }}
          className="mb-14"
        >
          <h1 className="text-5xl md:text-6xl font-medium tracking-tighter leading-none text-foreground/90">
            Learning Paths
          </h1>
          <p className="text-sm text-muted-foreground/50 mt-4 max-w-[45ch] leading-relaxed">
            Choose a language to begin. Each path combines structured theory with hands-on coding exercises.
          </p>
        </motion.div>

        {isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <SkeletonCard className="md:col-span-2" />
            <SkeletonCard />
            <SkeletonCard />
          </div>
        )}

        {error && (
          <div className="rounded-2xl bg-red-500/5 border border-red-500/10 p-6">
            <p className="text-sm text-red-400/80">{error}</p>
          </div>
        )}

        {!isLoading && !error && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {courses.map((course, i) => {
              const prog = progressMap[course.id];
              const completedCount = prog?.completed_lessons?.length || 0;
              const lastLessonId = prog?.last_accessed_lesson_id;

              const isHero = i === 0;

              return (
                <motion.div
                  key={course.id}
                  custom={i}
                  initial="hidden"
                  animate="visible"
                  variants={staggerVariants}
                  className={isHero ? 'md:col-span-2' : ''}
                >
                  <CourseCard
                    course={course}
                    completedCount={completedCount}
                    lastLessonId={lastLessonId}
                    isAuthenticated={isAuthenticated}
                    accentBorder={
                      isHero
                        ? 'md:hover:border-primary/20'
                        : 'md:hover:border-white/[0.12]'
                    }
                  />
                </motion.div>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
