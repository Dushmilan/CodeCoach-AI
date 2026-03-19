'use client';

import { useState, useEffect } from 'react';
import { useCodeCoach } from '@/contexts/CodeCoachContext';
import { ProblemSidebar } from '@/components/sidebar/ProblemSidebar';
import CodeEditor from '@/components/editor/CodeEditor';
import { AIChatPanel } from '@/components/chat/AIChatPanel';
import { OutputBar } from '@/components/OutputBar';
import { APIKeyModal } from '@/components/APIKeyModal';
import { Header } from '@/components/Header';

export default function LeetCodeClone() {
  const { state } = useCodeCoach();
  const [showApiKeyModal, setShowApiKeyModal] = useState(false);

  useEffect(() => {
    // Show API key modal if no key is set
    if (!state.apiKey) {
      setShowApiKeyModal(true);
    }
  }, [state.apiKey]);

  return (
    <div className="h-screen flex flex-col bg-gray-950">
      {/* Header is now in layout.tsx */}
      
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - Problem List */}
        <div className="w-80 flex-shrink-0 border-r border-gray-700">
          <ProblemSidebar />
        </div>

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col">
          {/* Top - Code Editor */}
          <div className="flex-1 flex">
            <div className="flex-1">
              <CodeEditor />
            </div>
            
            {/* Right Panel - AI Chat */}
            <div className="w-96 flex-shrink-0 border-l border-gray-700">
              <AIChatPanel />
            </div>
          </div>

          {/* Bottom - Output Bar */}
          <div className="h-64 flex-shrink-0 border-t border-gray-700">
            <OutputBar />
          </div>
        </div>
      </div>

      {/* API Key Modal */}
      <APIKeyModal 
        isOpen={showApiKeyModal} 
        onClose={() => setShowApiKeyModal(false)} 
      />
    </div>
  );
}