import { Skeleton } from "@/components/ui/Skeleton";

export default function ProblemsLoading() {
  return (
    <div className="min-h-[100dvh] bg-background text-foreground">
      <div className="max-w-4xl mx-auto px-6 pt-20 pb-32">
        <div className="flex flex-col rounded-[2rem] bg-white/[0.03] ring-1 ring-white/5 p-1.5">
          <div className="flex flex-col rounded-[calc(2rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)] overflow-hidden">
            {/* Header skeleton */}
            <div className="px-6 py-4 border-b border-white/5">
              <Skeleton variant="text" className="w-24 h-5 mb-2" />
              <Skeleton variant="text" className="w-36 h-3 opacity-50" />
            </div>

            {/* Table skeleton */}
            <div className="px-6 py-3 border-b border-white/5">
              <div className="flex gap-4">
                <Skeleton variant="text" className="w-12 h-3 opacity-40" />
                <Skeleton variant="text" className="w-20 h-3 opacity-40" />
                <Skeleton variant="text" className="w-16 h-3 opacity-40" />
                <Skeleton variant="text" className="w-20 h-3 opacity-40" />
              </div>
            </div>

            {/* Row skeletons */}
            {Array.from({ length: 8 }).map((_, i) => (
              <div
                key={i}
                className="flex items-center gap-4 px-6 py-3.5 border-b border-white/[0.02]"
              >
                <Skeleton variant="circle" className="w-4 h-4" />
                <Skeleton variant="text" className="flex-1 h-3.5" />
                <Skeleton variant="text" className="w-16 h-5 rounded-full" />
                <Skeleton variant="text" className="w-24 h-3 opacity-50" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
