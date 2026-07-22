import { Skeleton } from "@/components/ui/Skeleton";

export default function CourseLoading() {
  return (
    <div className="min-h-[100dvh] bg-background text-foreground">
      <div className="max-w-6xl mx-auto px-6 pt-20 pb-32">
        <div className="flex flex-col lg:flex-row gap-16">
          {/* Sidebar skeleton */}
          <aside className="w-full lg:w-72 flex-shrink-0 space-y-4">
            <Skeleton variant="text" className="w-20 h-3 opacity-40 mb-4" />
            <div className="flex items-center gap-3">
              <Skeleton
                variant="circle"
                width={40}
                height={40}
                className="rounded-xl"
              />
              <div className="space-y-2">
                <Skeleton variant="text" className="w-40 h-5" />
                <Skeleton variant="text" className="w-16 h-3 opacity-50" />
              </div>
            </div>
            <Skeleton variant="text" className="w-full h-3 mt-4" />
            <Skeleton variant="text" className="w-3/4 h-3 opacity-60" />
            <div className="mt-6 space-y-2">
              <div className="flex justify-between">
                <Skeleton variant="text" className="w-16 h-3 opacity-40" />
                <Skeleton variant="text" className="w-10 h-3 opacity-40" />
              </div>
              <Skeleton
                variant="text"
                className="w-full h-[3px] rounded-full"
              />
            </div>
          </aside>

          {/* Modules skeleton */}
          <div className="flex-1 space-y-8">
            {[1, 2, 3].map((m) => (
              <div
                key={m}
                className="space-y-3 pt-8 border-t border-white/[0.04]"
              >
                <div className="flex justify-between items-center">
                  <Skeleton variant="text" className="w-32 h-4" />
                  <Skeleton variant="text" className="w-8 h-3 opacity-30" />
                </div>
                <Skeleton variant="text" className="w-48 h-3 opacity-40" />
                {[1, 2, 3].map((l) => (
                  <div key={l} className="flex items-center gap-3 py-2.5 px-3">
                    <Skeleton variant="circle" width={16} height={16} />
                    <Skeleton variant="text" className="w-10 h-3 opacity-30" />
                    <Skeleton variant="text" className="flex-1 h-3.5" />
                    <Skeleton
                      variant="text"
                      className="w-3.5 h-3.5 opacity-15"
                    />
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
