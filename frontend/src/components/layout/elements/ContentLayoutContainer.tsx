import React from 'react';

interface ContentLayoutContainerProps {
  children: React.ReactNode;
}

export function ContentLayoutContainer({ children }: ContentLayoutContainerProps) {
  return (
    <div className="flex-1 flex overflow-hidden gap-0.5">
      {children}
    </div>
  );
}