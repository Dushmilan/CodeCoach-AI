'use client';

import { Header } from '@/components/header/Header';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';
import { BookOpen, Code, Globe, Rocket, Star, Zap } from 'lucide-react';
import Link from 'next/link';

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

const features = [
  {
    icon: Zap,
    title: '100% Free',
    description: 'No paywalls, no premium tiers. AI coaching powered by Groq, built in.',
    accent: 'border-l-emerald-500/40',
  },
  {
    icon: BookOpen,
    title: 'AI Coaching',
    description:
      'Context-aware hints and explanations powered by Groq — like a teaching assistant, 24/7.',
    accent: 'border-l-blue-500/40',
  },
  {
    icon: Code,
    title: 'Language Curriculum',
    description:
      'Structured C, Python, and Java paths blending theory with hands-on coding exercises.',
    accent: 'border-l-violet-500/40',
  },
  {
    icon: Globe,
    title: 'Open Source & Professor-Ready',
    description: 'Curriculum-mapped, privacy-first, and free for every institution to recommend.',
    accent: 'border-l-amber-500/40',
  },
];

const audiences = [
  {
    icon: Rocket,
    title: 'Interview Grinders',
    description: 'Prepare for tech internships and jobs with DSA practice.',
  },
  {
    icon: BookOpen,
    title: 'Struggling Students',
    description: 'Get hand-holding through the basics with instant AI feedback.',
  },
  {
    icon: Star,
    title: 'Curious Learners',
    description: 'Non-CS majors who want to learn programming on their own.',
  },
  {
    icon: Globe,
    title: 'Professors',
    description: 'A free, curriculum-aligned tool to recommend to your class.',
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-[100dvh] bg-background text-foreground overflow-x-hidden">
      <Header />

      {/* Hero */}
      <section className="relative pt-28 pb-20 md:pt-36 md:pb-28 px-6">
        <div className="max-w-5xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 32 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              duration: 0.9,
              ease: [0.32, 0.72, 0, 1] as const,
              delay: 0.15,
            }}
          >
            <span className="inline-flex items-center gap-1.5 px-3 py-1 text-[11px] font-medium tracking-widest uppercase text-emerald-400/80 bg-emerald-500/5 rounded-full border border-emerald-500/10 mb-8">
              Free &bull; Open Source &bull; AI-Powered
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 32 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              duration: 0.9,
              ease: [0.32, 0.72, 0, 1] as const,
              delay: 0.25,
            }}
            className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-medium tracking-tighter leading-[0.9] text-foreground/90 max-w-4xl mx-auto"
          >
            A free AI-powered
            <br />
            coding platform for
            <br />
            <span className="text-primary/80">university students</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              duration: 0.8,
              ease: [0.32, 0.72, 0, 1] as const,
              delay: 0.4,
            }}
            className="mt-6 text-sm md:text-base text-muted-foreground/60 max-w-2xl mx-auto leading-relaxed text-balance"
          >
            Practice DSA problems and learn programming languages through structured lessons with
            real-time AI coaching — no payment needed.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              duration: 0.8,
              ease: [0.32, 0.72, 0, 1] as const,
              delay: 0.55,
            }}
            className="mt-10 flex items-center justify-center gap-4 flex-wrap"
          >
            <Link
              href="/problems"
              className="group relative inline-flex items-center gap-2 px-6 py-3 text-sm font-medium text-white bg-primary/80 hover:bg-primary rounded-full transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] shadow-lg shadow-primary/10"
            >
              <Code className="h-4 w-4" />
              Start Practicing
              <span className="inline-block transition-transform duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] group-hover:translate-x-0.5">
                &rarr;
              </span>
            </Link>
            <Link
              href="/learn"
              className="inline-flex items-center gap-2 px-6 py-3 text-sm font-medium text-foreground/70 hover:text-foreground bg-white/[0.04] hover:bg-white/[0.08] rounded-full transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] border border-white/[0.06]"
            >
              <BookOpen className="h-4 w-4" />
              View Curriculum
            </Link>
          </motion.div>
        </div>

        {/* Subtle scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 1.2 }}
          className="absolute bottom-6 left-1/2 -translate-x-1/2"
        >
          <div className="w-5 h-8 rounded-full border border-white/10 flex items-start justify-center pt-1.5">
            <div className="w-1 h-2 rounded-full bg-white/20 animate-bounce" />
          </div>
        </motion.div>
      </section>

      {/* Features Bento Grid */}
      <section className="px-6 pb-24">
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-80px' }}
            transition={{ duration: 0.7, ease: [0.32, 0.72, 0, 1] as const }}
            className="mb-12"
          >
            <h2 className="text-3xl md:text-4xl font-medium tracking-tight text-foreground/90">
              Why CodeCoach AI?
            </h2>
            <p className="text-sm text-muted-foreground/50 mt-3 max-w-[45ch] leading-relaxed">
              Everything you need to level up your coding — without burning a hole in your wallet.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                custom={i}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: '-60px' }}
                variants={staggerVariants}
              >
                <div
                  className={cn(
                    'group relative rounded-3xl border border-white/[0.06] bg-white/[0.02] p-7 md:p-8',
                    'transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)]',
                    'hover:bg-white/[0.04] hover:border-white/[0.10]',
                    'h-full',
                    feature.accent,
                  )}
                  style={{
                    boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.06)',
                  }}
                >
                  <div className="flex items-center gap-3 mb-4">
                    <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/[0.04] text-foreground/60 ring-1 ring-white/5">
                      <feature.icon className="h-4 w-4" />
                    </span>
                    <h3 className="text-base font-medium tracking-tight text-foreground/90">
                      {feature.title}
                    </h3>
                  </div>
                  <p className="text-sm text-muted-foreground/60 leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Audience */}
      <section className="px-6 pb-24">
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-80px' }}
            transition={{ duration: 0.7, ease: [0.32, 0.72, 0, 1] as const }}
            className="mb-12"
          >
            <h2 className="text-3xl md:text-4xl font-medium tracking-tight text-foreground/90">
              Built for everyone
            </h2>
            <p className="text-sm text-muted-foreground/50 mt-3 max-w-[45ch] leading-relaxed">
              Whether you&apos;re grinding for interviews or writing your first loop.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {audiences.map((item, i) => (
              <motion.div
                key={item.title}
                custom={i}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: '-40px' }}
                variants={staggerVariants}
              >
                <div
                  className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] hover:bg-white/[0.04] h-full"
                  style={{
                    boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.06)',
                  }}
                >
                  <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/[0.04] text-foreground/50 ring-1 ring-white/5 mb-3">
                    <item.icon className="h-3.5 w-3.5" />
                  </span>
                  <h3 className="text-sm font-medium tracking-tight text-foreground/80 mb-1.5">
                    {item.title}
                  </h3>
                  <p className="text-xs text-muted-foreground/50 leading-relaxed">
                    {item.description}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Bottom CTA */}
      <section className="px-6 pb-32">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-80px' }}
          transition={{ duration: 0.8, ease: [0.32, 0.72, 0, 1] as const }}
          className="max-w-3xl mx-auto text-center"
        >
          <div className="rounded-3xl border border-white/[0.06] bg-white/[0.02] p-10 md:p-14">
            <h2 className="text-3xl md:text-4xl font-medium tracking-tight text-foreground/90 mb-4">
              Start coding, for free.
            </h2>
            <p className="text-sm text-muted-foreground/50 max-w-[40ch] mx-auto leading-relaxed mb-8">
              No credit card. No premium tier. Just you, the code, and an AI coach that&apos;s
              powered by Groq and always awake.
            </p>
            <div className="flex items-center justify-center gap-4 flex-wrap">
              <Link
                href="/problems"
                className="inline-flex items-center gap-2 px-6 py-3 text-sm font-medium text-white bg-primary/80 hover:bg-primary rounded-full transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] shadow-lg shadow-primary/10"
              >
                <Code className="h-4 w-4" />
                Start Practicing
              </Link>
              <Link
                href="/learn"
                className="inline-flex items-center gap-2 px-6 py-3 text-sm font-medium text-foreground/70 hover:text-foreground bg-white/[0.04] hover:bg-white/[0.08] rounded-full transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] border border-white/[0.06]"
              >
                <BookOpen className="h-4 w-4" />
                View Curriculum
              </Link>
            </div>
          </div>
        </motion.div>
      </section>
    </div>
  );
}
