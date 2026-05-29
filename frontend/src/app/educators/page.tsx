'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { Header } from '@/components/header/Header';
import {
  RadixCheckCircledIcon,
  RadixLightningBoltIcon,
  RadixReaderIcon,
  RadixStarIcon,
} from '@/components/ui/icons';

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.08, delayChildren: 0.2 },
  },
};

const staggerItem = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: [0.32, 0.72, 0, 1] as const },
  },
};

const features = [
  {
    icon: RadixLightningBoltIcon,
    title: 'Free for Students',
    desc: 'No subscriptions, no hidden fees. Students bring their own free NVIDIA API key for AI coaching — or practice without AI entirely.',
  },
  {
    icon: RadixReaderIcon,
    title: 'Curriculum Aligned',
    desc: '100 DSA questions across 14 standard topics + planned C, Python, and Java language curricula with structured lessons.',
  },
  {
    icon: RadixStarIcon,
    title: 'Multi-Language',
    desc: 'Every question includes Python, JavaScript, and Java starter code. Students write and run code directly in the browser.',
  },
  {
    icon: RadixLightningBoltIcon,
    title: 'AI Coaching',
    desc: '24/7 AI-powered hints, code reviews, explanations, and debugging help — like a TA that never sleeps.',
  },
  {
    icon: RadixCheckCircledIcon,
    title: 'Privacy First',
    desc: 'No ads, no tracking, no data selling. Minimal data collection. FERPA/GDPR alignment on the roadmap.',
  },
  {
    icon: RadixStarIcon,
    title: 'Zero Setup',
    desc: 'No roster upload, no IT overhead, no accounts for professors. Just share the URL and students sign up on their own.',
  },
];

const roadmap = [
  {
    phase: 'Phase 1',
    title: 'DSA Practice',
    desc: '100 coding questions across 14 topics. Google OAuth. Privacy policy.',
    status: 'Current',
    active: true,
  },
  {
    phase: 'Phase 2',
    title: 'Language Curricula',
    desc: 'C, Python, and Java with structured lessons + coding exercises.',
    status: 'In Progress',
    active: false,
  },
  {
    phase: 'Phase 3',
    title: 'CS Modules',
    desc: 'DBMS/SQL, OOP, Web Development (React, Node), theory/MCQ.',
    status: 'Planned',
    active: false,
  },
];

export default function EducatorsPage() {
  return (
    <div className="min-h-[100dvh] bg-background text-foreground">
      <Header />

      <main className="max-w-6xl mx-auto px-6 pt-20 pb-32">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.32, 0.72, 0, 1] }}
          className="mb-20"
        >
          <span className="inline-block text-[10px] uppercase tracking-[0.25em] font-medium text-muted-foreground/60 mb-5 px-3 py-1 rounded-full bg-white/[0.03] ring-1 ring-white/5">
            For Educators
          </span>
          <div className="grid grid-cols-1 md:grid-cols-[1.2fr_1fr] gap-12 items-start">
            <div>
              <h1 className="text-4xl md:text-5xl font-medium tracking-tighter leading-[1.1] text-foreground/90">
                A free platform your students will actually use
              </h1>
              <p className="text-sm text-muted-foreground/50 mt-5 max-w-[45ch] leading-relaxed">
                No subscriptions. No ads. No setup. Just coding practice with optional AI coaching.
              </p>
              <div className="flex items-center gap-3 mt-8">
                <Link
                  href="/register"
                  className="inline-flex items-center justify-center h-10 px-5 text-sm font-medium rounded-full bg-primary text-primary-foreground hover:bg-primary/90 shadow-[inset_0_1px_0_rgba(255,255,255,0.15)] transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] active:scale-[0.97]"
                >
                  Get started free
                </Link>
                <Link
                  href="/learn"
                  className="inline-flex items-center justify-center h-10 px-5 text-sm font-medium rounded-full border border-white/10 bg-white/5 hover:bg-white/10 text-foreground/80 backdrop-blur-xl transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] active:scale-[0.97]"
                >
                  Explore curriculum
                </Link>
              </div>
            </div>
            <div className="relative mt-4 md:mt-0">
              <div className="rounded-[2rem] border border-white/[0.06] bg-white/[0.02] p-6 shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]">
                <div className="space-y-3">
                  {[
                    { label: 'Students', value: '2,847', delta: '+12%' },
                    { label: 'Questions solved', value: '18,493', delta: '+8%' },
                    { label: 'Avg. completion', value: '73.2%', delta: '+5%' },
                  ].map((stat) => (
                    <div
                      key={stat.label}
                      className="flex items-center justify-between py-2 border-b border-white/[0.04] last:border-0"
                    >
                      <span className="text-xs text-muted-foreground/50">{stat.label}</span>
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-medium text-foreground/70 tabular-nums font-mono">
                          {stat.value}
                        </span>
                        <span className="text-[10px] text-primary/60 font-mono">{stat.delta}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        <motion.section
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-100px' }}
          className="mb-24"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-10">
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                variants={staggerItem}
                className="group"
              >
                <div className="flex items-start gap-4">
                  <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/[0.04] text-foreground/40 ring-1 ring-white/5 flex-shrink-0 group-hover:text-primary/60 transition-colors duration-500">
                    <feature.icon width={16} height={16} />
                  </span>
                  <div>
                    <h3 className="text-sm font-medium text-foreground/80 mb-1.5 tracking-tight">
                      {feature.title}
                    </h3>
                    <p className="text-xs text-muted-foreground/50 leading-relaxed max-w-[50ch]">
                      {feature.desc}
                    </p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.section>

        <motion.section
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.7, ease: [0.32, 0.72, 0, 1] }}
          className="mb-24"
        >
          <h2 className="text-sm font-medium text-foreground/80 tracking-wide mb-8">
            How to recommend it
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-[1fr_1.5fr] gap-12">
            <ol className="space-y-4">
              {[
                'Share the platform URL with your students',
                'They create an account with email/password',
                'Optional: add a free NVIDIA API key for AI coaching',
                'They start solving problems or working through curricula',
              ].map((step, i) => (
                <li key={i} className="flex items-start gap-3">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-white/[0.04] text-[10px] font-mono text-muted-foreground/40 ring-1 ring-white/5 flex-shrink-0 mt-0.5">
                    {i + 1}
                  </span>
                  <span className="text-xs text-muted-foreground/50 leading-relaxed">{step}</span>
                </li>
              ))}
            </ol>
            <div className="rounded-[2rem] border border-white/[0.06] bg-white/[0.02] p-6 shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]">
              <p className="text-xs text-muted-foreground/50 leading-relaxed">
                That&apos;s it. No class codes, no permissions, no paperwork.
              </p>
              <div className="mt-4 pt-4 border-t border-white/[0.04]">
                <span className="text-[10px] uppercase tracking-widest text-muted-foreground/30 font-mono">
                  Zero friction
                </span>
              </div>
            </div>
          </div>
        </motion.section>

        <motion.section
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.7, ease: [0.32, 0.72, 0, 1] }}
        >
          <h2 className="text-sm font-medium text-foreground/80 tracking-wide mb-8">
            Roadmap
          </h2>
          <div className="space-y-1">
            {roadmap.map((item, i) => (
              <motion.div
                key={item.phase}
                initial={{ opacity: 0, x: -16 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, ease: [0.32, 0.72, 0, 1], delay: i * 0.1 }}
                className="flex items-start gap-6 py-5 border-b border-white/[0.04] last:border-0"
              >
                <span className="text-[10px] font-mono text-muted-foreground/30 uppercase tracking-widest w-16 flex-shrink-0 pt-0.5">
                  {item.phase}
                </span>
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <h3 className="text-sm font-medium text-foreground/80">{item.title}</h3>
                    {item.active && (
                      <span className="text-[9px] uppercase tracking-widest font-mono text-primary/60 px-2 py-0.5 rounded-full bg-primary/5 ring-1 ring-primary/10">
                        {item.status}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground/50 leading-relaxed">{item.desc}</p>
                </div>
                <div
                  className={`w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1.5 ${
                    item.active ? 'bg-primary/60' : 'bg-white/10'
                  }`}
                />
              </motion.div>
            ))}
          </div>
        </motion.section>
      </main>

      <footer className="pb-8">
        <div className="max-w-6xl mx-auto px-6 text-center text-xs text-muted-foreground/40">
          <p>CodeCoach AI — Open source. Free for students. Built for education.</p>
        </div>
      </footer>
    </div>
  );
}
