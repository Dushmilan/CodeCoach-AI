import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Privacy Policy - CodeCoach AI',
  description: 'How CodeCoach AI handles your data',
};

export default function PrivacyPage() {
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
        <h1 className="text-3xl font-bold mb-8">Privacy Policy</h1>
        <p className="text-muted-foreground mb-8">Last updated: May 2026</p>

        <section className="space-y-8">
          <div>
            <h2 className="text-xl font-semibold mb-3">What data we collect</h2>
            <ul className="list-disc pl-6 space-y-2 text-muted-foreground">
              <li><strong>Account information:</strong> email address and hashed password (bcrypt) when you register</li>
              <li><strong>Code submissions:</strong> code you write and submit for execution is stored to show your submission history</li>
              <li><strong>AI coaching messages:</strong> messages sent to the AI coach are stored temporarily for conversation context</li>
              <li><strong>NVIDIA API key:</strong> stored in your browser&apos;s local storage — never sent to our server</li>
            </ul>
          </div>

          <div>
            <h2 className="text-xl font-semibold mb-3">What we do NOT collect</h2>
            <ul className="list-disc pl-6 space-y-2 text-muted-foreground">
              <li>No tracking cookies or analytics scripts</li>
              <li>No advertising identifiers</li>
              <li>No location data</li>
              <li>No course grades or academic records</li>
              <li>No third-party data sharing</li>
            </ul>
          </div>

          <div>
            <h2 className="text-xl font-semibold mb-3">How we use your data</h2>
            <ul className="list-disc pl-6 space-y-2 text-muted-foreground">
              <li>To authenticate you and maintain your session</li>
              <li>To display your submission history and progress</li>
              <li>To send code to Piston (code execution engine) and NVIDIA NIM (AI coach)</li>
              <li>To improve the platform (anonymized usage patterns only)</li>
            </ul>
          </div>

          <div>
            <h2 className="text-xl font-semibold mb-3">Data storage & retention</h2>
            <ul className="list-disc pl-6 space-y-2 text-muted-foreground">
              <li>Account data and submissions are stored in JSON files on the server</li>
              <li>Data is retained until you delete your account</li>
              <li>No data is sold, licensed, or shared with third parties</li>
            </ul>
          </div>

          <div>
            <h2 className="text-xl font-semibold mb-3">Your rights</h2>
            <ul className="list-disc pl-6 space-y-2 text-muted-foreground">
              <li><strong>Access:</strong> request a copy of your data at any time</li>
              <li><strong>Deletion:</strong> request permanent deletion of your account and all associated data</li>
              <li><strong>Export:</strong> download your submission history in JSON format</li>
            </ul>
            <p className="mt-4 text-muted-foreground">
              To exercise these rights, contact us through the project&apos;s GitHub repository.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-semibold mb-3">FERPA & GDPR compliance</h2>
            <p className="text-muted-foreground">
              We are committed to aligning with FERPA (US educational privacy law) and GDPR (EU data protection) 
              standards. As an open-source, non-commercial platform with no advertising and no data monetization, 
              we already exceed many baseline requirements. Formal compliance documentation is on the roadmap.
            </p>
          </div>

          <div>
            <h2 className="text-xl font-semibold mb-3">Third-party services</h2>
            <ul className="list-disc pl-6 space-y-2 text-muted-foreground">
              <li><strong>Piston</strong> (self-hosted) — executes submitted code in isolated containers</li>
              <li><strong>NVIDIA NIM</strong> — powers AI coaching; only code context and messages are sent, never personal data</li>
              <li>Both services receive only what is necessary to function. No personal identifiers are shared.</li>
            </ul>
          </div>

          <div>
            <h2 className="text-xl font-semibold mb-3">Changes to this policy</h2>
            <p className="text-muted-foreground">
              We will update this policy as the platform grows. Significant changes will be announced via 
              the project repository. Continued use after changes constitutes acceptance of the updated policy.
            </p>
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
