import { Skeleton } from "@/components/ui/Skeleton";

function SkeletonCard({ className }: { className?: string }) {
  return (
    <div
      className={`rounded-3xl border border-white/[0.04] bg-white/[0.01] p-8 ${className || ""}`}
    >
      <div className="flex items-center gap-3 mb-5">
        <Skeleton
          variant="circle"
          width={40}
          height={40}
          className="rounded-xl"
        />
        <div className="space-y-2">
          <Skeleton variant="text" className="w-32 h-4" />
          <Skeleton variant="text" className="w-16 h-3 opacity-50" />
        </div>
      </div>
      <div className="space-y-2 mb-6">
        <Skeleton variant="text" className="w-full h-3" />
        <Skeleton variant="text" className="w-3/4 h-3" />
      </div>
      <Skeleton variant="text" className="w-full h-[3px] rounded-full" />
    </div>
  );
}

export default function LearnLoading() {
  return (
    <div className="min-h-[100dvh] bg-background text-foreground">
      <div className="max-w-6xl mx-auto px-6 pt-20 pb-32">
        <div className="mb-14">
          <Skeleton variant="text" className="w-64 h-12 mb-4" />
          <Skeleton variant="text" className="w-80 h-3 opacity-50" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <SkeletonCard className="md:col-span-2" />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </div>
    </div>
  );
}
