import React from "react";

interface MainContentContainerProps {
  children: React.ReactNode;
}

export function MainContentContainer({ children }: MainContentContainerProps) {
  return <div className="flex-1 flex flex-col min-w-0">{children}</div>;
}
