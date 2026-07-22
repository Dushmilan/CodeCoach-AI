import { Skeleton } from "@/components/ui/Skeleton";

export default function ProblemWorkspaceLoading() {
  return (
    <div className="h-dvh bg-background text-foreground flex flex-col overflow-hidden">
      {/* Breadcrumb area */}
      <div className="px-4 pt-16 pb-2">
        <div className="flex items-center gap-2 px-1">
          <Skeleton variant="text" className="w-20 h-3 opacity-40" />
          <Skeleton variant="text" className="w-2 h-3 opacity-20" />
          <Skeleton variant="text" className="w-32 h-3 opacity-40" />
        </div>
      </div>

      {/* 3-panel skeleton */}
      <div className="flex-1 flex gap-1 px-4 pb-4 min-h-0">
        {/* Description panel */}
        <div className="flex-[28] rounded-[1.5rem] bg-white/[0.03] ring-1 ring-white/5 p-4">
          <Skeleton variant="text" className="w-40 h-5 mb-3" />
          <div className="flex gap-2 mb-5">
            <Skeleton variant="text" className="w-14 h-5 rounded-full" />
            <Skeleton
              variant="text"
              className="w-20 h-5 rounded-full opacity-50"
            />
          </div>
          <div className="space-y-2">
            <Skeleton variant="text" className="w-full h-3" />
            <Skeleton variant="text" className="w-full h-3" />
            <Skeleton variant="text" className="w-3/4 h-3" />
            <Skeleton variant="text" className="w-full h-3 mt-4" />
            <Skeleton variant="text" className="w-5/6 h-3" />
          </div>
        </div>

        {/* Editor panel */}
        <div className="flex-[44] rounded-[1.5rem] bg-white/[0.03] ring-1 ring-white/5 p-4 flex flex-col">
          <div className="flex gap-2 mb-4">
            <Skeleton variant="text" className="w-16 h-6 rounded-full" />
            <Skeleton
              variant="text"
              className="w-16 h-6 rounded-full opacity-50"
            />
          </div>
          <div className="flex-1 bg-white/[0.02] rounded-lg">
            <div className="p-4 space-y-2">
              {Array.from({ length: 12 }).map((_, i) => (
                <Skeleton
                  key={i}
                  variant="text"
                  className={`h-3 ${i % 3 === 0 ? "w-3/4" : i % 2 === 0 ? "w-5/6" : "w-full"}`}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Chat panel */}
        <div className="flex-[28] rounded-[1.5rem] bg-white/[0.03] ring-1 ring-white/5 p-4">
          <Skeleton variant="text" className="w-20 h-4 mb-2" />
          <Skeleton variant="text" className="w-36 h-3 opacity-40 mb-6" />
          <div className="space-y-4">
            <div className="flex gap-2">
              <Skeleton variant="circle" className="w-6 h-6" />
              <div className="flex-1 space-y-1.5">
                <Skeleton variant="text" className="w-full h-3" />
                <Skeleton variant="text" className="w-3/4 h-3" />
              </div>
            </div>
            <div className="flex gap-2">
              <Skeleton variant="circle" className="w-6 h-6" />
              <div className="flex-1 space-y-1.5">
                <Skeleton variant="text" className="w-full h-3" />
                <Skeleton variant="text" className="w-2/3 h-3" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
