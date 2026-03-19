'use client';

import { useEffect } from 'react';
import { CodeCoachProvider } from '@/contexts/CodeCoachContext';
import { ProblemSidebar } from '@/components/sidebar/ProblemSidebar';
import { CodeEditor } from '@/components/editor/CodeEditor';
import { AIChatPanel } from '@/components/chat/AIChatPanel';

export default function CodeCoachPage() {
  return (
    <CodeCoachProvider>
      <div className="flex h-screen bg-gray-100">
        {/* Left Sidebar - Questions */}
        <div className="w-80 bg-white border-r border-gray-200 overflow-hidden">
          <ProblemSidebar />
        </div>

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <div className="bg-white border-b border-gray-200 px-6 py-4">
            <h1 className="text-2xl font-bold text-gray-900">CodeCoach AI</h1>
            <p className="text-sm text-gray-600">
              Practice coding with AI assistance
            </p>
          </div>

          {/* Main Content */}
          <div className="flex-1 flex">
            {/* Code Editor Area */}
            <div className="flex-1 flex flex-col">
              <div className="flex-1 bg-white">
                <CodeEditor />
              </div>
            </div>

            {/* AI Chat Panel */}
            <div className="w-96 bg-white border-l border-gray-200">
              <AIChatPanel />
            </div>
          </div>
        </div>
      </div>
    </CodeCoachProvider>
  );
}