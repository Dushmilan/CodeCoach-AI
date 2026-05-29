import React, { useState, useEffect, useRef } from 'react';

interface TerminalProps {
  output: string;
}

const TerminalSimulation: React.FC<TerminalProps> = ({ output }) => {
  const [displayedText, setDisplayedText] = useState<string>('');
  const [index, setIndex] = useState(0);
  const terminalRef = useRef<HTMLDivElement>(null);

  // Progressive typing effect
  useEffect(() => {
    if (index < output.length) {
      const timer = setTimeout(() => {
        setDisplayedText((prev) => prev + output[index]);
        setIndex((prev) => prev + 1);
      }, 15); // Typing speed
      return () => clearTimeout(timer);
    }
  }, [index, output]);

  // Auto-scroll
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [displayedText]);

  return (
    <div className="relative w-full h-[300px] bg-[#0d0d0d] p-6 rounded-lg font-mono text-sm overflow-hidden shadow-2xl border border-gray-800">
      {/* Scanline Effect */}
      <div className="absolute inset-0 pointer-events-none bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] bg-[length:100%_4px,3px_100%] z-10" />
      
      {/* CRT Flicker Overlay */}
      <div className="absolute inset-0 pointer-events-none bg-green-500/5 animate-pulse z-0" />

      <div
        ref={terminalRef}
        className="relative z-20 h-full overflow-y-auto text-[#33ff33] whitespace-pre-wrap leading-relaxed"
      >
        <span className="block">{displayedText}</span>
        {index < output.length && (
          <span className="inline-block w-2 h-4 bg-[#33ff33] animate-pulse ml-1" />
        )}
      </div>
    </div>
  );
};

export default TerminalSimulation;
