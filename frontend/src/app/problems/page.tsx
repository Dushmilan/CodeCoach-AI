'use client';

import { Header } from '@/components/header/Header';
import { EmptyState } from '@/components/ui/EmptyState';
import { RecommendedQuestions } from '@/features/skill-graph/RecommendedQuestions';
import { RescueDueQueue } from '@/features/rescue/RescueDueQueue';
import { ReviewsDueQueue } from '@/features/review/ReviewsDueQueue';
import { useQuestion } from '@/features/question/question.hook';
import { QuestionSortKey } from '@/features/question/question.types';
import { useLocalStorage } from '@/hooks';
import { getDailySeed, seededShuffle } from '@/lib/shuffle';
import { cn } from '@/lib/utils';
import { QuestionSummary } from '@/types';
import {
  CheckCircle,
  ChevronDown,
  Circle,
  Loader2,
  RotateCcw,
  Search,
  SlidersHorizontal,
  X,
  XCircle,
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { workspaceService } from '@/features/workspace/workspace.service';
import { AuthContext } from '@/providers/AuthProvider';
import { useCallback, useContext, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';

const difficultyStyles: Record<string, string> = {
  easy: 'text-green-400 bg-green-500/10',
  medium: 'text-yellow-400 bg-yellow-500/10',
  hard: 'text-red-400 bg-red-500/10',
};

const difficultyRank: Record<string, number> = {
  easy: 0,
  medium: 1,
  hard: 2,
};

type StatusFilter = 'all' | 'solved' | 'attempted' | 'not_started';
type QuestionStatus = Exclude<StatusFilter, 'all'>;

export default function ProblemsPage() {
  const router = useRouter();
  const { allQuestions, loadQuestions, isLoading, error } = useQuestion();
  const [progress] = useLocalStorage<Record<string, 'attempted' | 'solved'>>('user_progress', {});
  const auth = useContext(AuthContext);
  const isAuthenticated = auth?.isAuthenticated ?? false;
  const [lastVisited, setLastVisited] = useState<{ question_id: string; language: string | null } | null>(null);

  const [search, setSearch] = useState('');
  const [difficulty, setDifficulty] = useState<string>('all');
  const [category, setCategory] = useState<string>('all');
  const [company, setCompany] = useState<string>('all');
  const [status, setStatus] = useState<StatusFilter>('all');
  const [sort, setSort] = useState<QuestionSortKey>('daily');

  useEffect(() => {
    loadQuestions();
  }, [loadQuestions]);

  useEffect(() => {
    if (!isAuthenticated) return;
    workspaceService.getLastVisited().then((data) => {
      if (data?.question_id) setLastVisited(data);
    }).catch(() => {});
  }, [isAuthenticated]);

  const categories = useMemo(() => {
    const set = new Set<string>();
    allQuestions.forEach((q) => set.add(q.category));
    return Array.from(set).sort((a, b) => a.localeCompare(b));
  }, [allQuestions]);

  const companies = useMemo(() => {
    const set = new Set<string>();
    allQuestions.forEach((q) => (q.company_tags ?? []).forEach((c) => set.add(c)));
    return Array.from(set).sort((a, b) => a.localeCompare(b));
  }, [allQuestions]);

  const resolveQuestionTitle = useCallback(
    (questionId: string) => allQuestions.find((q) => q.id === questionId)?.title,
    [allQuestions],
  );

  const getStatus = useCallback(
    (q: QuestionSummary): QuestionStatus => {
      const s = progress[q.id];
      if (s === 'solved') return 'solved';
      if (s === 'attempted') return 'attempted';
      return 'not_started';
    },
    [progress],
  );

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();
    const matches = allQuestions.filter((q) => {
      if (difficulty !== 'all' && q.difficulty !== difficulty) return false;
      if (category !== 'all' && q.category !== category) return false;
      if (company !== 'all' && !(q.company_tags ?? []).includes(company)) return false;
      if (status !== 'all' && getStatus(q) !== status) return false;
      if (query) {
        const haystack = [q.title, q.category, ...(q.company_tags ?? [])].join(' ').toLowerCase();
        if (!haystack.includes(query)) return false;
      }
      return true;
    });

    if (sort === 'daily') {
      return seededShuffle(matches, getDailySeed());
    }

    const sorted = [...matches];
    if (sort === 'title') {
      sorted.sort((a, b) => a.title.localeCompare(b.title));
    } else if (sort === 'difficulty') {
      sorted.sort(
        (a, b) =>
          difficultyRank[a.difficulty] - difficultyRank[b.difficulty] ||
          a.title.localeCompare(b.title),
      );
    } else if (sort === 'category') {
      sorted.sort((a, b) => a.category.localeCompare(b.category) || a.title.localeCompare(b.title));
    } else if (sort === 'status') {
      const rank: Record<QuestionStatus, number> = {
        not_started: 0,
        attempted: 1,
        solved: 2,
      };
      sorted.sort(
        (a, b) => rank[getStatus(a)] - rank[getStatus(b)] || a.title.localeCompare(b.title),
      );
    }
    return sorted;
  }, [allQuestions, search, difficulty, category, company, status, sort, getStatus]);

  const hasActiveFilters =
    difficulty !== 'all' ||
    category !== 'all' ||
    company !== 'all' ||
    status !== 'all' ||
    search.trim() !== '';

  const counts = useMemo(() => {
    const byDifficulty = { easy: 0, medium: 0, hard: 0 };
    const byStatus: Record<QuestionStatus, number> = {
      solved: 0,
      attempted: 0,
      not_started: 0,
    };
    allQuestions.forEach((q) => {
      byDifficulty[q.difficulty as keyof typeof byDifficulty] += 1;
      byStatus[getStatus(q)] += 1;
    });
    return { byDifficulty, byStatus };
  }, [allQuestions, getStatus]);

  const resetFilters = useCallback(() => {
    setSearch('');
    setDifficulty('all');
    setCategory('all');
    setCompany('all');
    setStatus('all');
    setSort('daily');
  }, []);

  const handleSelect = useCallback(
    (q: QuestionSummary) => {
      router.push(`/problems/${q.id}`);
    },
    [router],
  );

  const statusLabel = useCallback(
    (q: QuestionSummary) => {
      const s = progress[q.id];
      if (s === 'solved') return 'Solved';
      if (s === 'attempted') return 'Attempted';
      return 'Not started';
    },
    [progress],
  );

  const statusStyles: Record<string, string> = {
    solved: 'text-green-400',
    attempted: 'text-yellow-400',
    not_started: 'text-muted-foreground/30',
  };

  return (
    <div className="min-h-[100dvh] bg-background text-foreground">
      <Header />
      <main className="max-w-5xl mx-auto px-6 pt-20 pb-32">
        {lastVisited && (
          <div className="mb-4 flex items-center justify-between px-4 py-3 rounded-2xl bg-primary/10 ring-1 ring-primary/20">
            <span className="text-xs text-primary/90">Continue where you left off: <span className="font-medium">{resolveQuestionTitle(lastVisited.question_id) || lastVisited.question_id}</span></span>
            <button onClick={() => router.push(`/problems/${lastVisited.question_id}`)} className="text-xs px-3 py-1 rounded-full bg-primary text-primary-foreground hover:bg-primary/90">Resume</button>
          </div>
        )}
        <RecommendedQuestions />
        <RescueDueQueue resolveTitle={resolveQuestionTitle} />
        <ReviewsDueQueue resolveTitle={resolveQuestionTitle} />
        <div className="flex flex-col rounded-[2rem] bg-white/[0.03] ring-1 ring-white/5 p-1.5">
          <div className="flex flex-col rounded-[calc(2rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)] overflow-hidden">
            {/* ── Page header ─────────────────────────────────────── */}
            <div className="px-6 py-5 border-b border-white/5">
              <div className="flex items-start justify-between gap-4 flex-wrap">
                <div>
                  <h1 className="text-xl font-semibold tracking-tight">Problems</h1>
                  <p className="text-xs text-muted-foreground/60 mt-1">
                    {filtered.length}
                    {hasActiveFilters ? ' of ' : ' '}
                    {hasActiveFilters ? allQuestions.length : ''} questions available
                  </p>
                </div>
                <div className="flex items-center gap-2 text-[10px] text-muted-foreground/70">
                  <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-green-500/10 ring-1 ring-green-500/15">
                    <span className="h-1.5 w-1.5 rounded-full bg-green-400" />
                    {counts.byDifficulty.easy} easy
                  </span>
                  <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-yellow-500/10 ring-1 ring-yellow-500/15">
                    <span className="h-1.5 w-1.5 rounded-full bg-yellow-400" />
                    {counts.byDifficulty.medium} medium
                  </span>
                  <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-500/10 ring-1 ring-red-500/15">
                    <span className="h-1.5 w-1.5 rounded-full bg-red-400" />
                    {counts.byDifficulty.hard} hard
                  </span>
                </div>
              </div>
            </div>

            {/* ── Search + toolbar ────────────────────────────────── */}
            <div className="px-6 py-4 border-b border-white/5 flex flex-col gap-3">
              <div className="relative">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground/40 pointer-events-none" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search by title, category, or company..."
                  aria-label="Search questions"
                  className="w-full h-11 rounded-xl bg-white/[0.03] ring-1 ring-white/10 text-sm pl-10 pr-10 placeholder:text-muted-foreground/40 focus:outline-none focus:ring-2 focus:ring-primary/40 transition-shadow"
                />
                {search && (
                  <button
                    onClick={() => setSearch('')}
                    aria-label="Clear search"
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-full text-muted-foreground/40 hover:text-foreground hover:bg-white/5 transition-colors"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>

              <div className="flex items-center gap-2 flex-wrap">
                <SlidersHorizontal className="h-3.5 w-3.5 text-muted-foreground/40 hidden sm:block" />
                <FilterSelect
                  value={difficulty}
                  onChange={setDifficulty}
                  ariaLabel="Filter by difficulty"
                  className="relative"
                >
                  <option value="all">All difficulties</option>
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="hard">Hard</option>
                </FilterSelect>
                <FilterSelect
                  value={category}
                  onChange={setCategory}
                  ariaLabel="Filter by category"
                  className="max-w-[220px]"
                >
                  <option value="all">All categories</option>
                  {categories.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </FilterSelect>
                <FilterSelect
                  value={company}
                  onChange={setCompany}
                  ariaLabel="Filter by company"
                  className="max-w-[200px]"
                >
                  <option value="all">All companies</option>
                  {companies.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </FilterSelect>
                <FilterSelect
                  value={status}
                  onChange={(v) => setStatus(v as StatusFilter)}
                  ariaLabel="Filter by progress"
                >
                  <option value="all">All statuses</option>
                  <option value="not_started">Not started</option>
                  <option value="attempted">Attempted</option>
                  <option value="solved">Solved</option>
                </FilterSelect>

                <div className="flex-1" />

                <FilterSelect
                  value={sort}
                  onChange={(v) => setSort(v as QuestionSortKey)}
                  ariaLabel="Sort questions"
                >
                  <option value="daily">Daily shuffle</option>
                  <option value="title">Sort by title</option>
                  <option value="difficulty">Sort by difficulty</option>
                  <option value="category">Sort by category</option>
                  <option value="status">Sort by status</option>
                </FilterSelect>
              </div>

              {/* Active filter chips */}
              {hasActiveFilters && (
                <div className="flex items-center gap-2 flex-wrap">
                  {difficulty !== 'all' && (
                    <FilterChip label={difficulty} onClear={() => setDifficulty('all')} />
                  )}
                  {category !== 'all' && (
                    <FilterChip label={category} onClear={() => setCategory('all')} />
                  )}
                  {company !== 'all' && (
                    <FilterChip label={company} onClear={() => setCompany('all')} />
                  )}
                  {status !== 'all' && (
                    <FilterChip label={status.replace('_', ' ')} onClear={() => setStatus('all')} />
                  )}
                  {search.trim() && (
                    <FilterChip label={`"${search.trim()}"`} onClear={() => setSearch('')} />
                  )}
                  <button
                    onClick={resetFilters}
                    className="flex items-center gap-1 text-[11px] text-muted-foreground/60 hover:text-foreground transition-colors px-2 py-1"
                  >
                    <RotateCcw className="h-3 w-3" />
                    Clear all
                  </button>
                </div>
              )}
            </div>

            {/* ── Loading ─────────────────────────────────────────── */}
            {isLoading ? (
              <div className="flex flex-col items-center justify-center py-20 gap-3">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground/40" />
                <span className="text-sm text-muted-foreground/60">Loading questions...</span>
              </div>
            ) : error ? (
              <div className="flex items-center justify-center py-20">
                <div className="text-sm text-red-400/80 bg-red-500/5 px-4 py-3 rounded-2xl ring-1 ring-red-500/10">
                  {error}
                </div>
              </div>
            ) : filtered.length === 0 ? (
              <div className="py-10">
                <EmptyState
                  icon={Search}
                  title="No questions match your filters"
                  description="Try a different search term or clear some filters to see more questions."
                  actionLabel="Clear all filters"
                  onAction={resetFilters}
                />
              </div>
            ) : (
              <>
                {/* ── Desktop table ─────────────────────────────── */}
                <div className="overflow-x-auto hidden md:block">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-white/5">
                        <th className="text-left px-6 py-3 text-[10px] font-semibold tracking-wider text-muted-foreground/60 uppercase w-12">
                          Status
                        </th>
                        <th className="text-left px-4 py-3 text-[10px] font-semibold tracking-wider text-muted-foreground/60 uppercase">
                          Title
                        </th>
                        <th className="text-left px-4 py-3 text-[10px] font-semibold tracking-wider text-muted-foreground/60 uppercase w-24">
                          Difficulty
                        </th>
                        <th className="text-left px-4 py-3 text-[10px] font-semibold tracking-wider text-muted-foreground/60 uppercase w-40">
                          Category
                        </th>
                        <th className="text-left px-4 py-3 text-[10px] font-semibold tracking-wider text-muted-foreground/60 uppercase w-40">
                          Companies
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {filtered.map((q) => {
                        const s = progress[q.id];
                        return (
                          <tr
                            key={q.id}
                            onClick={() => handleSelect(q)}
                            className="border-b border-white/[0.02] hover:bg-white/[0.03] cursor-pointer transition-colors last:border-b-0"
                          >
                            <td className="px-6 py-3.5">
                              <span
                                className={cn(
                                  'flex items-center gap-2 text-[11px]',
                                  statusStyles[s ?? 'not_started'],
                                )}
                              >
                                {s === 'solved' ? (
                                  <CheckCircle className="h-4 w-4 text-green-400" />
                                ) : s === 'attempted' ? (
                                  <XCircle className="h-4 w-4 text-yellow-400" />
                                ) : (
                                  <Circle className="h-4 w-4 text-muted-foreground/30" />
                                )}
                                <span className="hidden xl:inline">{statusLabel(q)}</span>
                              </span>
                            </td>
                            <td className="px-4 py-3.5 font-medium text-foreground/80">
                              {q.title}
                            </td>
                            <td className="px-4 py-3.5">
                              <span
                                className={cn(
                                  'text-[10px] px-2 py-0.5 rounded-full font-medium uppercase tracking-wide',
                                  difficultyStyles[q.difficulty],
                                )}
                              >
                                {q.difficulty}
                              </span>
                            </td>
                            <td className="px-4 py-3.5 text-[11px] text-muted-foreground/60">
                              {q.category}
                            </td>
                            <td className="px-4 py-3.5">
                              <div className="flex items-center gap-1 flex-wrap max-w-[160px]">
                                {(q.company_tags ?? []).slice(0, 2).map((c) => (
                                  <span
                                    key={c}
                                    className="text-[10px] px-1.5 py-0.5 rounded-md bg-white/[0.04] ring-1 ring-white/5 text-muted-foreground/70"
                                  >
                                    {c}
                                  </span>
                                ))}
                                {(q.company_tags ?? []).length > 2 && (
                                  <span className="text-[10px] text-muted-foreground/40">
                                    +{(q.company_tags ?? []).length - 2}
                                  </span>
                                )}
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {/* ── Mobile cards ───────────────────────────────── */}
                <div className="md:hidden divide-y divide-white/[0.03]">
                  {filtered.map((q) => {
                    const s = progress[q.id];
                    return (
                      <button
                        key={q.id}
                        onClick={() => handleSelect(q)}
                        className="w-full text-left px-6 py-4 hover:bg-white/[0.03] transition-colors flex items-start gap-3"
                      >
                        <span className="pt-0.5">
                          {s === 'solved' ? (
                            <CheckCircle className="h-4 w-4 text-green-400" />
                          ) : s === 'attempted' ? (
                            <XCircle className="h-4 w-4 text-yellow-400" />
                          ) : (
                            <Circle className="h-4 w-4 text-muted-foreground/30" />
                          )}
                        </span>
                        <span className="flex-1 min-w-0">
                          <span className="flex items-center gap-2 flex-wrap">
                            <span className="font-medium text-foreground/80 text-sm">
                              {q.title}
                            </span>
                            <span
                              className={cn(
                                'text-[10px] px-2 py-0.5 rounded-full font-medium uppercase tracking-wide',
                                difficultyStyles[q.difficulty],
                              )}
                            >
                              {q.difficulty}
                            </span>
                          </span>
                          <span className="block text-xs text-muted-foreground/60 mt-1.5">
                            {q.category}
                          </span>
                          {(q.company_tags ?? []).length > 0 && (
                            <span className="block text-[10px] text-muted-foreground/40 mt-1 truncate">
                              {(q.company_tags ?? []).slice(0, 3).join(' · ')}
                              {(q.company_tags ?? []).length > 3 ? ' …' : ''}
                            </span>
                          )}
                        </span>
                        <span
                          className={cn(
                            'text-[10px] uppercase tracking-wide shrink-0',
                            statusStyles[s ?? 'not_started'],
                          )}
                        >
                          {statusLabel(q)}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </>
            )}

            {!isLoading && !error && filtered.length > 0 && (
              <div className="px-6 py-3 border-t border-white/5 text-[10px] text-muted-foreground/40 flex items-center justify-between gap-2 flex-wrap">
                <span>
                  {hasActiveFilters
                    ? `Showing ${filtered.length} of ${allQuestions.length} questions`
                    : `${filtered.length} questions available`}
                </span>
                <span>Click any problem to start coding</span>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

function FilterSelect({
  value,
  onChange,
  ariaLabel,
  className,
  children,
}: {
  value: string;
  onChange: (value: string) => void;
  ariaLabel: string;
  className?: string;
  children: ReactNode;
}) {
  return (
    <span className="relative">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-label={ariaLabel}
        className={cn(
          'h-9 rounded-xl bg-white/[0.03] ring-1 ring-white/10 text-xs text-muted-foreground px-3 hover:bg-white/[0.06] focus:outline-none focus:ring-2 focus:ring-primary/40 transition-colors appearance-none pr-8',
          className,
        )}
      >
        {children}
      </select>
      <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground/40 pointer-events-none" />
    </span>
  );
}

function FilterChip({ label, onClear }: { label: string; onClear: () => void }) {
  return (
    <span className="inline-flex items-center gap-1.5 pl-2.5 pr-1.5 py-1 rounded-full bg-primary/10 ring-1 ring-primary/20 text-[11px] text-primary/90">
      {label}
      <button
        onClick={onClear}
        aria-label={`Remove filter ${label}`}
        className="p-0.5 rounded-full hover:bg-primary/20 transition-colors"
      >
        <X className="h-3 w-3" />
      </button>
    </span>
  );
}
