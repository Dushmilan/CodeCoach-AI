import { Skeleton } from "@/components/ui/Skeleton";

export default function LessonLoading() {
  return (
    <div className="h-dvh bg-background text-foreground flex flex-col overflow-hidden">
      {/* Header area */}
      <div className="px-6 pt-20 pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Skeleton variant="text" className="w-16 h-3 opacity-40" />
            <Skeleton variant="text" className="w-2 h-3 opacity-20" />
            <Skeleton
              variant="circle"
              width={28}
              height={28}
              className="rounded-lg"
            />
            <div className="space-y-1.5">
              <Skeleton variant="text" className="w-40 h-4" />
              <Skeleton variant="text" className="w-20 h-2.5 opacity-40" />
            </div>
          </div>
          <div className="flex gap-2">
            <Skeleton variant="text" className="w-8 h-8 rounded-lg" />
            <Skeleton variant="text" className="w-8 h-8 rounded-lg" />
          </div>
        </div>
      </div>

      {/* Content area */}
      <div data-testid="lesson-content-container" className="flex-1 flex px-6 pb-6 w-full min-h-0">
        {/* Left panel - theory/exercise content */}
        <div className="w-[35%] pr-6 border-r border-white/[0.04] overflow-y-auto">
          <div className="space-y-3">
            <Skeleton variant="text" className="w-3/4 h-6" />
            <Skeleton variant="text" className="w-full h-3" />
            <Skeleton variant="text" className="w-full h-3" />
            <Skeleton variant="text" className="w-5/6 h-3" />
            <Skeleton variant="text" className="w-full h-3 mt-6" />
            <Skeleton variant="text" className="w-4/5 h-3" />
            <Skeleton variant="text" className="w-full h-3" />
          </div>
        </div>

        {/* Right panel - editor/chat */}
        <div className="flex-1 pl-6 flex flex-col min-h-0">
          <div className="flex-1 bg-white/[0.02] rounded-lg p-4">
            <div className="space-y-2">
              {Array.from({ length: 10 }).map((_, i) => (
                <Skeleton
                  key={i}
                  variant="text"
                  className={`h-3 ${i % 3 === 0 ? "w-3/4" : i % 2 === 0 ? "w-5/6" : "w-full"}`}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
