"use client";

import { cn } from "@/lib/utils";
import { Language } from "@/types";
import dynamic from "next/dynamic";
import { CheckCircle, ChevronDown, Play, RotateCcw } from "lucide-react";
import { useRef } from "react";
import { LANGUAGE_OPTIONS } from "./constants";

const Editor = dynamic(() => import("@monaco-editor/react"), {
  ssr: false,
  loading: () => (
    <div className="h-full w-full flex items-center justify-center text-xs text-muted-foreground/40">
      Loading editor…
    </div>
  ),
});

interface CodeEditorProps {
  onReset?: () => void;
  language: Language;
  code: string;
  initialCode: string;
  onCodeChange: (code: string) => void;
  onLanguageChange: (language: Language) => void;
  onRunCode: () => void;
  onSubmitCode: () => void;
  isRunning?: boolean;
  isResizing?: boolean;
  isAuthenticated?: boolean;
}

export function CodeEditor({
  language,
  code,
  initialCode,
  onCodeChange,
  onLanguageChange,
  onRunCode,
  onSubmitCode,
  isRunning,
  isResizing,
  isAuthenticated = true,
  onReset,
}: CodeEditorProps) {
  const editorRef = useRef<any>(null);
  const monacoLanguage = language === "c" ? "cpp" : language;

  const handleEditorDidMount = (editor: any) => {
    editorRef.current = editor;
  };

  const handleLanguageChange = (newLanguage: Language) => {
    onLanguageChange(newLanguage);
  };

  const resetCode = () => {
    if (onReset) {
      onReset();
    } else {
      onCodeChange(initialCode);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-3 py-2 border-b border-white/5">
        <div className="flex items-center gap-1 min-w-0">
          <label
            htmlFor="code-editor-language"
            className="sr-only"
          >
            Programming language
          </label>
          <div className="relative inline-flex min-w-0 max-w-full">
            <select
              id="code-editor-language"
              value={language}
              onChange={(e) => handleLanguageChange(e.target.value as Language)}
              className="w-full min-w-[9rem] max-w-[16rem] appearance-none rounded-md bg-white/[0.04] px-2.5 py-1.5 pr-7 text-xs font-medium tracking-wide text-foreground/80 ring-1 ring-white/10 transition-all duration-300 hover:bg-white/[0.07] hover:ring-white/20 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/60 cursor-pointer truncate"
            >
              {LANGUAGE_OPTIONS.map((option) => (
                <option
                  key={option.value}
                  value={option.value}
                  disabled={option.disabled}
                >
                  {option.label} {option.version}
                  {option.disabled && " (still in progress)"}
                </option>
              ))}
            </select>
            <ChevronDown className="pointer-events-none absolute right-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground/60" />
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            onClick={resetCode}
            disabled={isRunning || !isAuthenticated}
            className="inline-flex items-center gap-1 px-3 py-1.5 text-[10px] font-medium tracking-wide text-muted-foreground/60 bg-white/[0.03] hover:bg-white/[0.07] rounded-full ring-1 ring-white/5 disabled:opacity-40 disabled:pointer-events-none transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] active:scale-[0.97]"
          >
            <RotateCcw className="h-3 w-3" />
            Reset
          </button>
          <button
            onClick={onRunCode}
            disabled={isRunning || !isAuthenticated}
            className="inline-flex items-center gap-1 px-3 py-1.5 text-[10px] font-medium tracking-wide text-muted-foreground/60 bg-white/[0.03] hover:bg-white/[0.07] rounded-full ring-1 ring-white/5 disabled:opacity-40 disabled:pointer-events-none transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] active:scale-[0.97]"
          >
            <Play className="h-3 w-3" />
            Run
          </button>
          <button
            onClick={onSubmitCode}
            disabled={isRunning || !isAuthenticated}
            className="inline-flex items-center gap-1 px-4 py-1.5 text-[10px] font-medium tracking-wide text-emerald-300 bg-emerald-500/10 hover:bg-emerald-500/20 rounded-full ring-1 ring-emerald-500/20 disabled:opacity-40 disabled:pointer-events-none transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] active:scale-[0.97]"
          >
            <CheckCircle className="h-3 w-3" />
            {isRunning ? "Running..." : "Submit"}
          </button>
        </div>
      </div>

      <div
        className={cn(
          "flex-1 min-h-0 rounded-b-[calc(2rem-0.375rem)] overflow-hidden",
          isResizing && "pointer-events-none",
        )}
      >
        <Editor
          height="100%"
          language={monacoLanguage}
          value={code}
          onChange={(value) => onCodeChange(value || "")}
          onMount={handleEditorDidMount}
          theme="vs-dark"
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            lineNumbers: "on",
            roundedSelection: false,
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 2,
            wordWrap: "on",
          }}
        />
      </div>
    </div>
  );
}
