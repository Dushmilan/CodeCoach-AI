"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/providers/AuthProvider";

export default function AuthCallbackPage() {
  const router = useRouter();
  const { loginWithSupabase } = useAuth();
  const [error, setError] = useState("");

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
        const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
        if (!supabaseUrl || !supabaseKey) {
          throw new Error(
            "Supabase is not configured. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.",
          );
        }

        const { createBrowserClient } = await import("@supabase/ssr");
        const supabase = createBrowserClient(supabaseUrl, supabaseKey);

        const {
          data: { session },
          error: sessionError,
        } = await supabase.auth.getSession();
        if (sessionError) throw sessionError;
        if (!session?.access_token) throw new Error("No session returned");

        await loginWithSupabase(session.access_token);
        router.push("/");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Authentication failed");
        setTimeout(() => router.push("/login"), 3000);
      }
    };

    handleCallback();
  }, [router, loginWithSupabase]);

  if (error) {
    return (
      <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
        <div className="text-center space-y-2">
          <p className="text-destructive">{error}</p>
          <p className="text-sm text-muted-foreground">
            Redirecting to login...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
      <p className="text-muted-foreground">Completing sign in...</p>
    </div>
  );
}
