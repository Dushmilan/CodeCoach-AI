"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/Input";
import { motion } from "framer-motion";
import { BookOpen, Code2, Home, Search } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function NotFound() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/problems?search=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  return (
    <div className="min-h-[100dvh] bg-background text-foreground flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.32, 0.72, 0, 1] }}
        className="max-w-md w-full"
      >
        <div className="p-1.5 rounded-[2rem] bg-white/[0.03] ring-1 ring-white/5">
          <div className="rounded-[calc(2rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)] p-10 text-center">
            {/* 404 illustration */}
            <div className="mb-6 flex justify-center">
              <div className="relative">
                <div className="absolute inset-0 bg-primary/20 blur-2xl rounded-full" />
                <div className="relative flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 ring-1 ring-primary/20">
                  <span className="text-2xl font-bold text-primary/80">?</span>
                </div>
              </div>
            </div>

            {/* Error code */}
            <div className="mb-3">
              <span className="text-6xl font-bold tracking-tight text-foreground/90">
                404
              </span>
            </div>

            {/* Error message */}
            <h2 className="text-lg font-semibold text-foreground/80 mb-2">
              Page not found
            </h2>
            <p className="text-sm text-muted-foreground/60 mb-8 max-w-sm mx-auto">
              The page you&apos;re looking for doesn&apos;t exist or has been
              moved.
            </p>

            {/* Search bar */}
            <form onSubmit={handleSearch} className="mb-6">
              <Input
                type="text"
                placeholder="Search problems..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                icon={Search}
                className="w-full"
              />
            </form>

            {/* Quick links */}
            <div className="grid grid-cols-3 gap-3">
              <Link href="/problems">
                <Button
                  variant="ghost"
                  className="w-full flex-col gap-2 h-auto py-3"
                >
                  <Code2 className="h-5 w-5" />
                  <span className="text-xs">Problems</span>
                </Button>
              </Link>
              <Link href="/learn">
                <Button
                  variant="ghost"
                  className="w-full flex-col gap-2 h-auto py-3"
                >
                  <BookOpen className="h-5 w-5" />
                  <span className="text-xs">Learn</span>
                </Button>
              </Link>
              <Link href="/">
                <Button
                  variant="ghost"
                  className="w-full flex-col gap-2 h-auto py-3"
                >
                  <Home className="h-5 w-5" />
                  <span className="text-xs">Home</span>
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
