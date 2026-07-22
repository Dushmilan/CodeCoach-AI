import { Skeleton } from "@/components/ui/Skeleton";

export default function Loading() {
  return (
    <div className="min-h-[100dvh] bg-background text-foreground flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="relative">
          <div className="h-10 w-10 rounded-full border-2 border-white/5 border-t-primary/60 animate-spin" />
        </div>
        <div className="flex flex-col items-center gap-2">
          <Skeleton variant="text" className="w-32 h-3" />
          <Skeleton variant="text" className="w-20 h-2.5 opacity-50" />
        </div>
      </div>
    </div>
  );
}
