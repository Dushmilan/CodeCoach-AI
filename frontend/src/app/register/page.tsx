"use client";

import { Header } from "@/components/header/Header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/providers/AuthProvider";
import { motion } from "framer-motion";
import { Lock, Mail, User, UserPlus } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const getPasswordStrength = (
    pwd: string,
  ): { label: string; color: string } => {
    if (pwd.length < 6) return { label: "Weak", color: "text-red-400" };
    if (pwd.length < 10) return { label: "Medium", color: "text-yellow-400" };
    return { label: "Strong", color: "text-green-400" };
  };

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setError("");

      // Client-side validation
      if (username.length < 3) {
        setError("Username must be at least 3 characters");
        return;
      }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        setError("Please enter a valid email address");
        return;
      }
      if (password.length < 6) {
        setError("Password must be at least 6 characters");
        return;
      }

      setIsLoading(true);
      try {
        await register(username, email, password);
        router.push("/");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Registration failed");
      } finally {
        setIsLoading(false);
      }
    },
    [username, email, password, register, router],
  );

  const passwordStrength = getPasswordStrength(password);

  return (
    <div className="min-h-[100dvh] bg-background text-foreground flex flex-col">
      <Header />

      <main className="flex-1 flex items-center justify-center px-4 pt-20 pb-32">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.32, 0.72, 0, 1] }}
          className="w-full max-w-sm"
        >
          <div className="p-1.5 rounded-[2rem] bg-white/[0.03] ring-1 ring-white/5">
            <div className="rounded-[calc(2rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)] p-8">
              {/* Branding */}
              <div className="text-center mb-8">
                <div className="mb-4 flex justify-center">
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 ring-1 ring-primary/20">
                    <UserPlus
                      className="h-6 w-6 text-primary/80"
                      strokeWidth={1.5}
                    />
                  </div>
                </div>
                <h1 className="text-2xl font-semibold tracking-tight text-foreground/90">
                  Create account
                </h1>
                <p className="text-sm text-muted-foreground/60 mt-1.5">
                  Start practicing with CodeCoach AI
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <Input
                  id="username"
                  type="text"
                  label="Username"
                  placeholder="Choose a username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  icon={User}
                  required
                  minLength={3}
                  maxLength={50}
                  autoComplete="username"
                />

                <Input
                  id="email"
                  type="email"
                  label="Email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  icon={Mail}
                  required
                  autoComplete="email"
                />

                <div>
                  <Input
                    id="password"
                    type="password"
                    label="Password"
                    placeholder="At least 6 characters"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    icon={Lock}
                    required
                    minLength={6}
                    autoComplete="new-password"
                  />
                  {password && (
                    <div className="mt-2 flex items-center gap-2">
                      <div className="flex-1 h-1 bg-white/[0.04] rounded-full overflow-hidden">
                        <div
                          className={`h-full transition-all duration-300 ${
                            passwordStrength.label === "Weak"
                              ? "w-1/3 bg-red-400"
                              : passwordStrength.label === "Medium"
                                ? "w-2/3 bg-yellow-400"
                                : "w-full bg-green-400"
                          }`}
                        />
                      </div>
                      <span className={`text-xs ${passwordStrength.color}`}>
                        {passwordStrength.label}
                      </span>
                    </div>
                  )}
                </div>

                {error && (
                  <div className="text-xs text-red-400 bg-red-500/10 rounded-full px-4 py-2 text-center ring-1 ring-red-500/20">
                    {error}
                  </div>
                )}

                <Button type="submit" className="w-full" disabled={isLoading}>
                  {isLoading ? "Creating account..." : "Create account"}
                </Button>
              </form>

              <p className="text-center text-xs text-muted-foreground/60 mt-6">
                Already have an account?{" "}
                <Link
                  href="/login"
                  className="text-primary/80 hover:text-primary transition-colors font-medium"
                >
                  Sign in
                </Link>
              </p>
            </div>
          </div>
        </motion.div>
      </main>
    </div>
  );
}
