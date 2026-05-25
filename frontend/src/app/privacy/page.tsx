import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Privacy Policy - CodeCoach AI',
  description: 'How CodeCoach AI handles your data',
};

export default function PrivacyPage() {
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
          <span className="inline-block text-[10px] uppercase tracking-[0.25em] font-medium text-muted-foreground/60 mb-4 px-3 py-1 rounded-full bg-white/[0.03] ring-1 ring-white/5">Legal</span>
          <h1 className="text-4xl font-semibold tracking-tight text-foreground/90 mb-3">Privacy Policy</h1>
          <p className="text-sm text-muted-foreground/40">Last updated: May 2026</p>
        </div>

        <div className="space-y-8">
          {[
            {
              title: 'What data we collect',
              items: [
                '<strong>Account information:</strong> email address and hashed password (bcrypt) when you register',
                '<strong>Code submissions:</strong> code you write and submit for execution is stored to show your submission history',
                '<strong>AI coaching messages:</strong> messages sent to the AI coach are stored temporarily for conversation context',
                '<strong>NVIDIA API key:</strong> stored in your browser\'s local storage — never sent to our server',
              ],
            },
            {
              title: 'What we do NOT collect',
              items: [
                'No tracking cookies or analytics scripts',
                'No advertising identifiers',
                'No location data',
                'No course grades or academic records',
                'No third-party data sharing',
              ],
            },
            {
              title: 'How we use your data',
              items: [
                'To authenticate you and maintain your session',
                'To display your submission history and progress',
                'To send code to Piston (code execution engine) and NVIDIA NIM (AI coach)',
                'To improve the platform (anonymized usage patterns only)',
              ],
            },
            {
              title: 'Data storage & retention',
              items: [
                'Account data and submissions are stored in JSON files on the server',
                'Data is retained until you delete your account',
                'No data is sold, licensed, or shared with third parties',
              ],
            },
            {
              title: 'Your rights',
              items: [
                '<strong>Access:</strong> request a copy of your data at any time',
                '<strong>Deletion:</strong> request permanent deletion of your account and all associated data',
                '<strong>Export:</strong> download your submission history in JSON format',
              ],
              extra: 'To exercise these rights, contact us through the project\'s GitHub repository.',
            },
            {
              title: 'FERPA & GDPR compliance',
              paragraph: 'We are committed to aligning with FERPA (US educational privacy law) and GDPR (EU data protection) standards. As an open-source, non-commercial platform with no advertising and no data monetization, we already exceed many baseline requirements. Formal compliance documentation is on the roadmap.',
            },
            {
              title: 'Third-party services',
              items: [
                '<strong>Piston</strong> (self-hosted) — executes submitted code in isolated containers',
                '<strong>NVIDIA NIM</strong> — powers AI coaching; only code context and messages are sent, never personal data',
                'Both services receive only what is necessary to function. No personal identifiers are shared.',
              ],
            },
            {
              title: 'Changes to this policy',
              paragraph: 'We will update this policy as the platform grows. Significant changes will be announced via the project repository. Continued use after changes constitutes acceptance of the updated policy.',
            },
          ].map((section, i) => (
            <div key={i} className="p-1.5 rounded-[2rem] bg-white/[0.03] ring-1 ring-white/5">
              <div className="rounded-[calc(2rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)] p-6">
                <h2 className="text-sm font-semibold text-foreground/80 mb-3 tracking-wide">{section.title}</h2>
                {section.items && (
                  <ul className="space-y-1.5">
                    {section.items.map((item, j) => (
                      <li key={j} className="text-sm text-muted-foreground/60 leading-relaxed pl-4 relative before:content-[''] before:absolute before:left-0 before:top-[0.6em] before:w-1 before:h-1 before:rounded-full before:bg-white/10">
                        <span dangerouslySetInnerHTML={{ __html: item }} />
                      </li>
                    ))}
                  </ul>
                )}
                {section.paragraph && (
                  <p className="text-sm text-muted-foreground/60 leading-relaxed">{section.paragraph}</p>
                )}
                {section.extra && (
                  <p className="mt-3 text-sm text-muted-foreground/60 leading-relaxed">{section.extra}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      </main>

      <footer className="mt-20 pb-8">
        <div className="mx-auto max-w-4xl px-4 text-center text-xs text-muted-foreground/40">
          <p>CodeCoach AI — Open source. Free for students. Built for education.</p>
        </div>
      </footer>
    </div>
  );
}
