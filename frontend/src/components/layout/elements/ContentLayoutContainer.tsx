import React from "react";

interface ContentLayoutContainerProps {
  children: React.ReactNode;
}

export function ContentLayoutContainer({
  children,
}: ContentLayoutContainerProps) {
  return (
    <div className="flex-1 grid grid-cols-[1fr_auto] overflow-hidden gap-0.5">
      {children}
    </div>
  );
}
