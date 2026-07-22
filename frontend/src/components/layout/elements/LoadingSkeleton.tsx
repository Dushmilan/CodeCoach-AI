import React from "react";

export function LoadingSkeleton() {
  return (
    <main
      className="flex h-[100dvh] bg-background overflow-hidden"
      role="main"
      aria-label="CodeCoach AI Learning Platform"
    >
      <div className="flex w-full gap-0.5 p-2">
        {/* Sidebar Skeleton */}
        <aside className="flex flex-col w-80 p-1">
          <div className="flex-1 flex flex-col rounded-[2rem] bg-white/[0.03] ring-1 ring-white/5 p-1.5 animate-pulse">
            <div className="flex-1 flex flex-col rounded-[calc(2rem-0.375rem)] bg-card overflow-hidden">
              <div className="p-4 border-b border-white/5">
                <div className="h-4 bg-white/5 rounded-full w-20" />
              </div>
              <div className="p-4 space-y-3">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="h-14 bg-white/5 rounded-2xl" />
                ))}
              </div>
            </div>
          </div>
        </aside>

        {/* Main Content Skeleton */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Header */}
          <div className="flex items-center justify-center py-3">
            <div className="h-9 w-40 bg-white/[0.03] ring-1 ring-white/5 rounded-full animate-pulse" />
          </div>

          <div className="flex-1 flex gap-0.5 p-1 overflow-hidden">
            {/* Editor skeleton */}
            <section className="flex-1 flex flex-col p-1 overflow-hidden">
              <div className="flex-1 flex flex-col rounded-[2rem] bg-white/[0.03] ring-1 ring-white/5 p-1.5 animate-pulse">
                <div className="flex-1 rounded-[calc(2rem-0.375rem)] bg-card" />
              </div>
            </section>

            {/* Chat skeleton */}
            <aside className="w-96 flex flex-col p-1">
              <div className="flex-1 flex flex-col rounded-[2rem] bg-white/[0.03] ring-1 ring-white/5 p-1.5 animate-pulse">
                <div className="flex-1 rounded-[calc(2rem-0.375rem)] bg-card p-4">
                  <div className="space-y-3">
                    {[...Array(3)].map((_, i) => (
                      <div
                        key={i}
                        className="h-12 bg-white/5 rounded-2xl w-3/4"
                        style={{ marginLeft: i % 2 === 0 ? 0 : "25%" }}
                      />
                    ))}
                  </div>
                </div>
              </div>
            </aside>
          </div>
        </div>
      </div>
    </main>
  );
}
