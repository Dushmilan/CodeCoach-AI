'use client';

import { useParams, useRouter } from 'next/navigation';
import { Header } from '@/components/header/Header';
import Link from 'next/link';
import { ArrowLeft, CheckCircle2, Circle, ChevronRight } from 'lucide-react';
import { useCourse } from '@/features/curriculum/use-curriculum.hook';

const iconMap: Record<string, string> = {
  python: '🐍',
  c: '⚡',
  java: '☕',
};

export default function CoursePage() {
  const params = useParams();
  const router = useRouter();
  const courseId = params.courseId as string;
  const { course, isLoading, error } = useCourse(courseId);

  if (isLoading) {
    return (
      <div className="min-h-[100dvh] bg-background text-foreground">
        <Header />
        <main className="max-w-3xl mx-auto px-4 pt-16 pb-24">
          <div className="animate-pulse space-y-4">
            <div className="h-8 w-48 rounded-full bg-white/[0.03]" />
            <div className="h-4 w-96 rounded-full bg-white/[0.03]" />
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-32 rounded-2xl bg-white/[0.03] ring-1 ring-white/5" />
            ))}
          </div>
        </main>
      </div>
    );
  }

  if (error || !course) {
    return (
      <div className="min-h-[100dvh] bg-background text-foreground">
        <Header />
        <main className="max-w-3xl mx-auto px-4 pt-16 pb-24">
          <div className="rounded-2xl bg-red-500/10 ring-1 ring-red-500/20 p-6 text-sm text-red-400">
            {error || 'Course not found'}
          </div>
          <Link href="/learn" className="inline-flex items-center gap-2 text-sm text-primary/80 hover:text-primary mt-4 transition-colors">
            <ArrowLeft className="h-3.5 w-3.5" /> Back to learning paths
          </Link>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-[100dvh] bg-background text-foreground">
      <Header />

      <main className="max-w-3xl mx-auto px-4 pt-16 pb-24">
        <Link
          href="/learn"
          className="inline-flex items-center gap-2 text-xs text-muted-foreground/60 hover:text-foreground/80 mb-6 transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Back to learning paths
        </Link>

        <div className="flex items-center gap-3 mb-2">
          <span className="text-2xl">{iconMap[course.language] || '📘'}</span>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground/90">{course.title}</h1>
        </div>
        <p className="text-sm text-muted-foreground/60 mb-10">{course.description}</p>

        <div className="space-y-6">
          {course.modules.map((mod) => (
            <div
              key={mod.id}
              className="rounded-2xl bg-white/[0.03] ring-1 ring-white/5 p-6 transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]"
            >
              <h2 className="text-base font-semibold text-foreground/90 mb-1">{mod.title}</h2>
              <p className="text-xs text-muted-foreground/60 mb-4">{mod.description}</p>

              <div className="space-y-1">
                {mod.lessons.map((lesson) => (
                  <Link
                    key={lesson.id}
                    href={`/learn/lesson/${lesson.id}`}
                    className="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-white/[0.04] transition-all duration-300 ease-[cubic-bezier(0.32,0.72,0,1)] group"
                  >
                    {lesson.type === 'theory' ? (
                      <Circle className="h-3.5 w-3.5 text-muted-foreground/40 flex-shrink-0" strokeWidth={1.5} />
                    ) : (
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500/60 flex-shrink-0" strokeWidth={1.5} />
                    )}
                    <span className="text-xs text-muted-foreground/60 w-12 flex-shrink-0 uppercase tracking-wide">
                      {lesson.type === 'theory' ? 'Read' : 'Code'}
                    </span>
                    <span className="text-sm text-foreground/70 group-hover:text-foreground/90 transition-colors flex-1">
                      {lesson.title}
                    </span>
                    <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/20 group-hover:text-muted-foreground/60 transition-all" strokeWidth={1.5} />
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
