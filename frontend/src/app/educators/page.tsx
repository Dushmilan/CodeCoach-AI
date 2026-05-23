import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'For Educators - CodeCoach AI',
  description: 'Why professors recommend CodeCoach AI to their students',
};

export default function EducatorsPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-4">
          <Link href="/" className="text-xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">
            CodeCoach AI
          </Link>
          <Link href="/" className="text-sm text-muted-foreground hover:text-foreground">
            Back to editor
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-4 py-12">
        <h1 className="text-3xl font-bold mb-2">For Educators</h1>
        <p className="text-lg text-muted-foreground mb-10">
          A free coding practice platform your students will actually use.
        </p>

        <section className="grid gap-8 md:grid-cols-2 mb-12">
          <div className="rounded-lg border border-border bg-card p-6">
            <h2 className="text-lg font-semibold mb-2">Free for Students</h2>
            <p className="text-muted-foreground">
              No subscriptions, no hidden fees. Students bring their own free NVIDIA API key 
              for AI coaching — or practice without AI entirely.
            </p>
          </div>
          <div className="rounded-lg border border-border bg-card p-6">
            <h2 className="text-lg font-semibold mb-2">Curriculum Aligned</h2>
            <p className="text-muted-foreground">
              100 DSA questions across 14 standard topics + planned C, Python, and Java 
              language curricula with structured lessons.
            </p>
          </div>
          <div className="rounded-lg border border-border bg-card p-6">
            <h2 className="text-lg font-semibold mb-2">Multi-Language</h2>
            <p className="text-muted-foreground">
              Every question includes Python, JavaScript, and Java starter code. 
              Students write and run code directly in the browser.
            </p>
          </div>
          <div className="rounded-lg border border-border bg-card p-6">
            <h2 className="text-lg font-semibold mb-2">AI Coaching</h2>
            <p className="text-muted-foreground">
              24/7 AI-powered hints, code reviews, explanations, and debugging help — 
              like a TA that never sleeps.
            </p>
          </div>
          <div className="rounded-lg border border-border bg-card p-6">
            <h2 className="text-lg font-semibold mb-2">Privacy First</h2>
            <p className="text-muted-foreground">
              No ads, no tracking, no data selling. Minimal data collection. 
              FERPA/GDPR alignment on the roadmap.
            </p>
          </div>
          <div className="rounded-lg border border-border bg-card p-6">
            <h2 className="text-lg font-semibold mb-2">Zero Setup</h2>
            <p className="text-muted-foreground">
              No roster upload, no IT overhead, no accounts for professors. 
              Just share the URL and students sign up on their own.
            </p>
          </div>
        </section>

        <section className="rounded-lg border border-border bg-card p-8 mb-12">
          <h2 className="text-xl font-semibold mb-4">How to recommend it</h2>
          <ol className="list-decimal pl-6 space-y-3 text-muted-foreground">
            <li>Share the platform URL with your students</li>
            <li>They create an account with email/password</li>
            <li>Optional: add a free NVIDIA API key for AI coaching</li>
            <li>They start solving problems or working through curricula</li>
          </ol>
          <p className="mt-4 text-muted-foreground">
            That&apos;s it. No class codes, no permissions, no paperwork.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-4">Roadmap</h2>
          <div className="space-y-4">
            <div className="border-l-4 border-primary pl-4">
              <h3 className="font-medium">Phase 1 — DSA Practice</h3>
              <p className="text-sm text-muted-foreground">100 coding questions across 14 topics. Google OAuth. Privacy policy. <em>Current.</em></p>
            </div>
            <div className="border-l-4 border-muted-foreground/30 pl-4">
              <h3 className="font-medium">Phase 2 — Language Curricula</h3>
              <p className="text-sm text-muted-foreground">C, Python, and Java with structured lessons + coding exercises.</p>
            </div>
            <div className="border-l-4 border-muted-foreground/30 pl-4">
              <h3 className="font-medium">Phase 3 — CS Modules</h3>
              <p className="text-sm text-muted-foreground">DBMS/SQL, OOP, Web Development (React, Node), theory/MCQ.</p>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-border mt-16">
        <div className="mx-auto max-w-4xl px-4 py-6 text-center text-sm text-muted-foreground">
          <p>CodeCoach AI — Open source. Free for students. Built for education.</p>
        </div>
      </footer>
    </div>
  );
}
