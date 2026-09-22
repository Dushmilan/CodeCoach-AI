"use client";

/*
 * Design read: learning-platform marketing for students and professors,
 * education-playful language, Tailwind v3 + shadcn owned primitives + Geist.
 * Dials: DESIGN_VARIANCE 6 / MOTION_INTENSITY 5 / VISUAL_DENSITY 4.
 * Shape lock: interactive elements are pill (rounded-full), surfaces are
 * rounded-2xl/3xl. Accent lock: emerald only. One eyebrow pill on this page.
 * IA preserved: same routes, nav labels, CTA labels, section headings.
 */

import { Header } from "@/components/header/Header";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { MotionConfig, motion, useReducedMotion } from "framer-motion";
import {
  BookOpen,
  Code,
  Globe,
  GraduationCap,
  Rocket,
  Star,
  Zap,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";

const EASE = [0.32, 0.72, 0, 1] as const;

function Reveal({
  children,
  delay = 0,
  className,
}: {
  children: React.ReactNode;
  delay?: number;
  className?: string;
}) {
  const reduce = useReducedMotion();
  if (reduce) return <div className={className}>{children}</div>;
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.7, ease: EASE, delay }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

const features = [
  {
    icon: Zap,
    title: "100% Free",
    description:
      "No paywalls, no premium tiers. AI coaching powered by Groq, built in.",
    span: false,
    visual: false,
  },
  {
    icon: BookOpen,
    title: "AI Coaching",
    description:
      "Context-aware hints and explanations powered by Groq, like a teaching assistant that never sleeps.",
    span: false,
    visual: false,
  },
  {
    icon: Code,
    title: "Language Curriculum",
    description:
      "Structured C, Python, and Java paths blending theory with hands-on coding exercises.",
    span: true,
    visual: true,
  },
  {
    icon: Globe,
    title: "Open Source and Professor-Ready",
    description:
      "Curriculum-mapped, privacy-first, and free for every institution to recommend.",
    span: false,
    visual: false,
  },
];

const studentPaths = [
  {
    icon: Rocket,
    title: "Interview Grinders",
    description: "Prepare for tech internships and jobs with DSA practice.",
  },
  {
    icon: BookOpen,
    title: "Struggling Students",
    description: "Get hand-holding through the basics with instant AI feedback.",
  },
  {
    icon: Star,
    title: "Curious Learners",
    description: "Non-CS majors who want to learn programming on their own.",
  },
];

function HeroVisual() {
  return (
    <div data-testid="hero-visual" className="relative">
      <div className="overflow-hidden rounded-3xl border border-border bg-card shadow-sm">
        <Image
          src="https://picsum.photos/seed/codecoach-hero/880/1100"
          alt="Student writing code with an AI coach beside the editor"
          width={880}
          height={1100}
          priority
          className="aspect-[4/5] w-full object-cover"
        />
      </div>
      {/* mock illustration: example gamification overlay, not real user data */}
      <div
        aria-hidden="true"
        className="absolute -bottom-6 -left-4 w-64 rounded-2xl border border-border bg-card p-4 shadow-lg md:-left-8"
      >
        <p className="text-xs font-medium text-foreground">12 day streak</p>
        <div className="mt-2">
          <Progress value={68} />
        </div>
        <p className="mt-2 text-[11px] text-muted-foreground">
          2,400 XP this week
        </p>
      </div>
    </div>
  );
}

export default function LandingPage() {
  return (
    <MotionConfig reducedMotion="user">
      <div className="min-h-[100dvh] overflow-x-hidden bg-background text-foreground">
        <Header />

        {/* Hero: asymmetric split, left copy / right visual */}
        <section className="px-6 pb-20 pt-24">
          <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 lg:grid-cols-2 lg:gap-8">
            <div>
              <Reveal>
                <span className="mb-6 inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-[11px] font-medium uppercase tracking-widest text-primary">
                  Free, Open Source, AI-Powered
                </span>
              </Reveal>
              <Reveal delay={0.1}>
                <h1 className="max-w-xl text-4xl font-medium leading-[1.05] tracking-tighter text-foreground md:text-5xl lg:text-6xl">
                  A free AI-powered coding platform
                </h1>
              </Reveal>
              <Reveal delay={0.2}>
                <p
                  data-testid="hero-subtext"
                  className="mt-5 max-w-[52ch] text-base leading-relaxed text-muted-foreground"
                >
                  Built for university students. Practice DSA problems and
                  learn C, Python, and Java with real-time AI coaching. Free
                  forever.
                </p>
              </Reveal>
              <Reveal delay={0.3}>
                <div className="mt-8 flex flex-wrap items-center gap-3">
                  <Link
                    href="/problems"
                    className="inline-flex items-center gap-2 rounded-full bg-primary px-6 py-3 text-sm font-medium text-primary-foreground shadow-lg shadow-primary/10 transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] hover:bg-primary/90 active:scale-[0.98]"
                  >
                    <Code className="h-4 w-4" />
                    Start Practicing
                  </Link>
                  <Link
                    href="/learn"
                    className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-6 py-3 text-sm font-medium text-foreground transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] hover:bg-accent active:scale-[0.98]"
                  >
                    <BookOpen className="h-4 w-4" />
                    View Curriculum
                  </Link>
                </div>
              </Reveal>
            </div>
            <Reveal delay={0.2} className="pb-8 lg:pb-0">
              <HeroVisual />
            </Reveal>
          </div>
        </section>

        {/* Features: asymmetric bento, 4 items in 4 cells */}
        <section className="px-6 pb-24">
          <div className="mx-auto max-w-6xl">
            <Reveal className="mb-10">
              <h2 className="text-3xl font-medium tracking-tight text-foreground md:text-4xl">
                Why CodeCoach AI?
              </h2>
              <p className="mt-3 max-w-[45ch] text-sm leading-relaxed text-muted-foreground">
                Everything you need to level up your coding without paying a
                cent.
              </p>
            </Reveal>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              {features.map((feature, i) => (
                <Reveal
                  key={feature.title}
                  delay={i * 0.08}
                  className={cn(feature.span && "md:col-span-2")}
                >
                  <div
                    className={cn(
                      "group relative h-full overflow-hidden rounded-3xl border border-border bg-card p-7 transition-colors duration-500 hover:bg-accent/50 md:p-8",
                      feature.visual && "border-primary/20 bg-primary/[0.04]",
                    )}
                  >
                    {feature.visual && (
                      <Image
                        src="https://picsum.photos/seed/codecoach-code/1200/500"
                        alt="Curriculum artwork"
                        width={1200}
                        height={500}
                        loading="lazy"
                        className="mb-5 h-36 w-full rounded-2xl border border-border object-cover"
                      />
                    )}
                    <div className="flex items-center gap-3">
                      <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary/10 text-primary ring-1 ring-primary/20">
                        <feature.icon className="h-4 w-4" />
                      </span>
                      <h3 className="text-base font-medium tracking-tight text-foreground">
                        {feature.title}
                      </h3>
                    </div>
                    <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                      {feature.description}
                    </p>
                  </div>
                </Reveal>
              ))}
            </div>
          </div>
        </section>

        {/* Animation showcase: full-width panel with real still */}
        <section className="px-6 pb-24">
          <div className="mx-auto max-w-6xl">
            <Reveal className="mb-8">
              <h2 className="text-3xl font-medium tracking-tight text-foreground md:text-4xl">
                See algorithms come alive
              </h2>
              <p className="mt-3 max-w-[45ch] text-sm leading-relaxed text-muted-foreground">
                Every solution runs as a step-by-step animation you can scrub
                and replay.
              </p>
            </Reveal>

            <Reveal>
              <div className="overflow-hidden rounded-3xl border border-border bg-card">
                <Image
                  src="https://picsum.photos/seed/codecoach-animate/1600/800"
                  alt="Step-by-step animation of a sorting algorithm"
                  width={1600}
                  height={800}
                  loading="lazy"
                  className="aspect-[2/1] w-full object-cover"
                />
                <p className="px-7 py-5 text-xs leading-relaxed text-muted-foreground md:px-9">
                  From bubble sort to Dijkstra, pick any problem and watch the
                  canonical solution animate.
                </p>
              </div>
            </Reveal>
          </div>
        </section>

        {/* Audience: grouped rows, students plus educators */}
        <section className="px-6 pb-24">
          <div className="mx-auto max-w-6xl">
            <Reveal className="mb-10">
              <h2 className="text-3xl font-medium tracking-tight text-foreground md:text-4xl">
                Built for everyone
              </h2>
              <p className="mt-3 max-w-[45ch] text-sm leading-relaxed text-muted-foreground">
                Grinding for interviews or writing your first loop, there is a
                path for you.
              </p>
            </Reveal>

            <div className="grid grid-cols-1 gap-10 lg:grid-cols-2">
              <Reveal>
                <h3 className="mb-4 text-sm font-medium text-foreground">
                  For students
                </h3>
                <ul className="rounded-3xl border border-border bg-card px-7">
                  {studentPaths.map((item, i) => (
                    <li key={item.title}>
                      {i > 0 && <Separator />}
                      <div className="flex items-start gap-4 py-5">
                        <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary ring-1 ring-primary/20">
                          <item.icon className="h-3.5 w-3.5" />
                        </span>
                        <div>
                          <p className="text-sm font-medium text-foreground">
                            {item.title}
                          </p>
                          <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                            {item.description}
                          </p>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </Reveal>
              <Reveal delay={0.1}>
                <h3 className="mb-4 text-sm font-medium text-foreground">
                  For educators
                </h3>
                <div className="rounded-3xl border border-primary/20 bg-primary/[0.04] p-7">
                  <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary/10 text-primary ring-1 ring-primary/20">
                    <GraduationCap className="h-4 w-4" />
                  </span>
                  <p className="mt-4 text-base font-medium text-foreground">
                    Professors
                  </p>
                  <p className="mt-1 max-w-[40ch] text-sm leading-relaxed text-muted-foreground">
                    A free, curriculum-aligned tool to recommend to your class,
                    with progress you can actually follow.
                  </p>
                  <Link
                    href="/learn"
                    className="mt-5 inline-flex items-center gap-2 rounded-full border border-border bg-card px-5 py-2.5 text-sm font-medium text-foreground transition-all duration-500 hover:bg-accent active:scale-[0.98]"
                  >
                    <BookOpen className="h-4 w-4" />
                    View Curriculum
                  </Link>
                </div>
              </Reveal>
            </div>
          </div>
        </section>

        {/* Bottom CTA: single centered panel */}
        <section className="px-6 pb-24">
          <Reveal className="mx-auto max-w-3xl">
            <div className="rounded-3xl border border-border bg-card p-10 text-center md:p-14">
              <h2 className="text-3xl font-medium tracking-tight text-foreground md:text-4xl">
                Start coding, for free.
              </h2>
              <p className="mx-auto mb-8 mt-4 max-w-[40ch] text-sm leading-relaxed text-muted-foreground">
                No credit card. No premium tier. Just you, the code, and an AI
                coach that stays awake.
              </p>
              <div className="flex flex-wrap items-center justify-center gap-3">
                <Link
                  href="/problems"
                  className="inline-flex items-center gap-2 rounded-full bg-primary px-6 py-3 text-sm font-medium text-primary-foreground shadow-lg shadow-primary/10 transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] hover:bg-primary/90 active:scale-[0.98]"
                >
                  <Code className="h-4 w-4" />
                  Start Practicing
                </Link>
                <Link
                  href="/learn"
                  className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-6 py-3 text-sm font-medium text-foreground transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] hover:bg-accent active:scale-[0.98]"
                >
                  <BookOpen className="h-4 w-4" />
                  View Curriculum
                </Link>
              </div>
            </div>
          </Reveal>
        </section>

        {/* Footer */}
        <footer className="border-t border-border px-6 py-10">
          <div className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-6 sm:flex-row sm:items-center">
            <div>
              <p className="text-sm font-semibold tracking-tight text-foreground">
                CodeCoach AI
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                Free and open source for every student.
              </p>
            </div>
            <nav className="flex items-center gap-5 text-sm text-muted-foreground">
              <Link href="/problems" className="transition-colors hover:text-foreground">
                Problems
              </Link>
              <Link href="/learn" className="transition-colors hover:text-foreground">
                Learn
              </Link>
              <Link href="/privacy" className="transition-colors hover:text-foreground">
                Privacy
              </Link>
            </nav>
          </div>
        </footer>
      </div>
    </MotionConfig>
  );
}
