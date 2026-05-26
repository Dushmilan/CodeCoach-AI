'use client';

import { Header } from '@/components/header/Header';
import Link from 'next/link';
import { useCurriculum } from '@/features/curriculum/use-curriculum.hook';

const iconMap: Record<string, string> = {
  python: '🐍',
  c: '⚡',
  java: '☕',
};

const languageColors: Record<string, string> = {
  python: 'from-blue-500/20 to-blue-600/5 ring-blue-500/20',
  c: 'from-amber-500/20 to-amber-600/5 ring-amber-500/20',
  java: 'from-red-500/20 to-red-600/5 ring-red-500/20',
};

export default function LearnPage() {
  const { courses, isLoading, error } = useCurriculum();

  return (
    <div className="min-h-[100dvh] bg-background text-foreground">
      <Header />

      <main className="max-w-4xl mx-auto px-4 pt-16 pb-24">
        <div className="mb-10">
          <h1 className="text-3xl font-semibold tracking-tight text-foreground/90">Learning Paths</h1>
          <p className="text-sm text-muted-foreground/60 mt-2">
            Choose a language to start learning from scratch
          </p>
        </div>

        {isLoading && (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse rounded-2xl bg-white/[0.03] ring-1 ring-white/5 p-6 h-28" />
            ))}
          </div>
        )}

        {error && (
          <div className="rounded-2xl bg-red-500/10 ring-1 ring-red-500/20 p-6 text-sm text-red-400">
            {error}
          </div>
        )}

        {!isLoading && !error && (
          <div className="space-y-4">
            {courses.map((course) => (
              <Link
                key={course.id}
                href={`/learn/${course.id}`}
                className={`block rounded-2xl bg-gradient-to-br ${languageColors[course.language] || 'from-white/[0.04] to-white/[0.02]'} ring-1 ring-white/10 hover:ring-white/20 p-6 transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] hover:scale-[1.01]`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <span className="text-2xl mt-0.5">{iconMap[course.language] || '📘'}</span>
                    <div>
                      <h2 className="text-lg font-semibold text-foreground/90">{course.title}</h2>
                      <p className="text-sm text-muted-foreground/60 mt-1">{course.description}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-semibold text-foreground/80">{course.progress}%</div>
                    <div className="w-24 h-1.5 mt-2 rounded-full bg-white/5 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-primary/60 transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)]"
                        style={{ width: `${course.progress}%` }}
                      />
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
