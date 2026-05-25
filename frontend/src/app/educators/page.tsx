import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'For Educators - CodeCoach AI',
  description: 'Why professors recommend CodeCoach AI to their students',
};

export default function EducatorsPage() {
  return (
    <div className="min-h-[100dvh] bg-background text-foreground">
      {/* Fluid Island Nav */}
      <div className="flex items-center justify-center pt-6">
        <div className="inline-flex items-center gap-4 px-5 py-2 rounded-full bg-card/70 backdrop-blur-2xl ring-1 ring-white/10 shadow-[inset_0_1px_1px_rgba(255,255,255,0.1)]">
          <Link href="/" className="text-sm font-semibold tracking-tight text-foreground/90">
            CodeCoach AI
          </Link>
          <Link href="/" className="text-xs text-muted-foreground/70 hover:text-foreground hover:bg-white/5 px-3 py-1 rounded-full transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]">
            Back to editor
          </Link>
        </div>
      </div>

      <main className="mx-auto max-w-4xl px-4 py-16">
        <div className="text-center mb-16">
          <span className="inline-block text-[10px] uppercase tracking-[0.25em] font-medium text-muted-foreground/60 mb-4 px-3 py-1 rounded-full bg-white/[0.03] ring-1 ring-white/5">For Educators</span>
          <h1 className="text-4xl font-semibold tracking-tight text-foreground/90 mb-3">A free platform your students will actually use</h1>
          <p className="text-base text-muted-foreground/60 max-w-xl mx-auto leading-relaxed">
            No subscriptions. No ads. No setup. Just coding practice with optional AI coaching.
          </p>
        </div>

        <section className="grid gap-4 md:grid-cols-2 mb-16">
          {[
            { title: 'Free for Students', desc: 'No subscriptions, no hidden fees. Students bring their own free NVIDIA API key for AI coaching — or practice without AI entirely.' },
            { title: 'Curriculum Aligned', desc: '100 DSA questions across 14 standard topics + planned C, Python, and Java language curricula with structured lessons.' },
            { title: 'Multi-Language', desc: 'Every question includes Python, JavaScript, and Java starter code. Students write and run code directly in the browser.' },
            { title: 'AI Coaching', desc: '24/7 AI-powered hints, code reviews, explanations, and debugging help — like a TA that never sleeps.' },
            { title: 'Privacy First', desc: 'No ads, no tracking, no data selling. Minimal data collection. FERPA/GDPR alignment on the roadmap.' },
            { title: 'Zero Setup', desc: 'No roster upload, no IT overhead, no accounts for professors. Just share the URL and students sign up on their own.' },
          ].map((item, i) => (
            <div key={i} className="p-1.5 rounded-[2rem] bg-white/[0.03] ring-1 ring-white/5">
              <div className="rounded-[calc(2rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)] p-6">
                <h2 className="text-sm font-semibold text-foreground/80 mb-2 tracking-wide">{item.title}</h2>
                <p className="text-sm text-muted-foreground/60 leading-relaxed">{item.desc}</p>
              </div>
            </div>
          ))}
        </section>

        <section className="mb-16 p-1.5 rounded-[2rem] bg-white/[0.03] ring-1 ring-white/5">
          <div className="rounded-[calc(2rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)] p-8">
            <h2 className="text-base font-semibold text-foreground/80 mb-5 tracking-wide">How to recommend it</h2>
            <ol className="list-decimal pl-5 space-y-2.5 text-sm text-muted-foreground/60">
              <li>Share the platform URL with your students</li>
              <li>They create an account with email/password</li>
              <li>Optional: add a free NVIDIA API key for AI coaching</li>
              <li>They start solving problems or working through curricula</li>
            </ol>
            <p className="mt-4 text-sm text-muted-foreground/60">
              That&apos;s it. No class codes, no permissions, no paperwork.
            </p>
          </div>
        </section>

        <section>
          <h2 className="text-base font-semibold text-foreground/80 mb-6 tracking-wide">Roadmap</h2>
          <div className="space-y-4">
            <div className="p-1.5 rounded-[2rem] bg-white/[0.03] ring-1 ring-white/5">
              <div className="rounded-[calc(2rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)] p-5 border-l-[3px] border-primary">
                <h3 className="text-sm font-medium text-foreground/80 mb-1">Phase 1 — DSA Practice</h3>
                <p className="text-sm text-muted-foreground/60">100 coding questions across 14 topics. Google OAuth. Privacy policy. <em>Current.</em></p>
              </div>
            </div>
            <div className="p-1.5 rounded-[2rem] bg-white/[0.03] ring-1 ring-white/5">
              <div className="rounded-[calc(2rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)] p-5 border-l-[3px] border-white/5">
                <h3 className="text-sm font-medium text-foreground/80 mb-1">Phase 2 — Language Curricula</h3>
                <p className="text-sm text-muted-foreground/60">C, Python, and Java with structured lessons + coding exercises.</p>
              </div>
            </div>
            <div className="p-1.5 rounded-[2rem] bg-white/[0.03] ring-1 ring-white/5">
              <div className="rounded-[calc(2rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)] p-5 border-l-[3px] border-white/5">
                <h3 className="text-sm font-medium text-foreground/80 mb-1">Phase 3 — CS Modules</h3>
                <p className="text-sm text-muted-foreground/60">DBMS/SQL, OOP, Web Development (React, Node), theory/MCQ.</p>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="mt-20 pb-8">
        <div className="mx-auto max-w-4xl px-4 text-center text-xs text-muted-foreground/40">
          <p>CodeCoach AI — Open source. Free for students. Built for education.</p>
        </div>
      </footer>
    </div>
  );
}
