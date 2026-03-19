'use client';

import { useState, useEffect } from 'react';
import { useCodeCoach } from '@/contexts/CodeCoachContext';
import { CheckCircle, XCircle, AlertCircle, Loader2 } from 'lucide-react';

interface OutputBarProps {
  className?: string;
}

interface TestResult {
  id: string;
  status: 'passed' | 'failed' | 'error' | 'running';
  testCase: string;
  expected: string;
  actual?: string;
  error?: string;
  executionTime?: number;
}

export function OutputBar({ className = '' }: OutputBarProps) {
  const { state } = useCodeCoach();
  const [results, setResults] = useState<TestResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  // Mock test results for demonstration
  const mockResults: TestResult[] = [
    {
      id: '1',
      status: 'passed',
      testCase: 'reverse_string(["h","e","l","l","o"])',
      expected: '["o","l","l","e","h"]',
      actual: '["o","l","l","e","h"]',
      executionTime: 0.12,
    },
    {
      id: '2',
      status: 'passed',
      testCase: 'reverse_string(["H","a","n","n","a","h"])',
      expected: '["h","a","n","n","a","H"]',
      actual: '["h","a","n","n","a","H"]',
      executionTime: 0.08,
    },
    {
      id: '3',
      status: 'failed',
      testCase: 'reverse_string(["A","","B"])',
      expected: '["B","","A"]',
      actual: '["","B","A"]',
      error: 'Empty string handling failed',
      executionTime: 0.15,
    },
  ];

  useEffect(() => {
    // Simulate code execution when code changes
    if (state.code) {
      setIsRunning(true);
      setTimeout(() => {
        setResults(mockResults);
        setIsRunning(false);
      }, 2000);
    }
  }, [state.code]);

  const getStatusIcon = (status: TestResult['status']) => {
    switch (status) {
      case 'passed':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-400" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-yellow-400" />;
      case 'running':
        return <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />;
    }
  };

  const getStatusColor = (status: TestResult['status']) => {
    switch (status) {
      case 'passed':
        return 'text-green-400 bg-green-900/20 border-green-500/30';
      case 'failed':
        return 'text-red-400 bg-red-900/20 border-red-500/30';
      case 'error':
        return 'text-yellow-400 bg-yellow-900/20 border-yellow-500/30';
      case 'running':
        return 'text-blue-400 bg-blue-900/20 border-blue-500/30';
    }
  };

  const getStatusText = (status: TestResult['status']) => {
    switch (status) {
      case 'passed':
        return 'Passed';
      case 'failed':
        return 'Failed';
      case 'error':
        return 'Error';
      case 'running':
        return 'Running';
    }
  };

  const passedCount = results.filter(r => r.status === 'passed').length;
  const totalCount = results.length;

  return (
    <div className={`flex flex-col h-full bg-gray-900 border-t border-gray-700 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        <div className="flex items-center space-x-4">
          <h3 className="text-lg font-semibold text-white">Output</h3>
          <div className="flex items-center space-x-2 text-sm">
            <span className="text-gray-400">Tests:</span>
            <span className="text-green-400">{passedCount}</span>
            <span className="text-gray-400">/</span>
            <span className="text-white">{totalCount}</span>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {isRunning && (
            <div className="flex items-center space-x-2 text-sm text-blue-400">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Running tests...</span>
            </div>
          )}
        </div>
      </div>

      {/* Results */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {results.length === 0 && !isRunning && (
          <div className="text-center py-8">
            <p className="text-gray-400">No test results yet. Run your code to see results.</p>
          </div>
        )}

        {results.map((result) => (
          <div
            key={result.id}
            className={`p-4 rounded-lg border ${getStatusColor(result.status)}`}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                {getStatusIcon(result.status)}
                <span className="font-medium text-sm">{getStatusText(result.status)}</span>
              </div>
              {result.executionTime && (
                <span className="text-xs text-gray-400">
                  {result.executionTime}ms
                </span>
              )}
            </div>

            <div className="space-y-2 text-sm">
              <div>
                <span className="text-gray-400">Test:</span>
                <code className="ml-2 text-white">{result.testCase}</code>
              </div>
              
              <div>
                <span className="text-gray-400">Expected:</span>
                <code className="ml-2 text-green-400">{result.expected}</code>
              </div>

              {result.actual && (
                <div>
                  <span className="text-gray-400">Actual:</span>
                  <code className="ml-2 text-red-400">{result.actual}</code>
                </div>
              )}

              {result.error && (
                <div>
                  <span className="text-gray-400">Error:</span>
                  <span className="ml-2 text-yellow-400">{result.error}</span>
                </div>
              )}
            </div>
          </div>
        ))}

        {isRunning && results.length === 0 && (
          <div className="flex items-center justify-center py-8">
            <div className="text-center">
              <Loader2 className="w-8 h-8 text-blue-400 animate-spin mx-auto mb-2" />
              <p className="text-gray-400">Running tests...</p>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-700">
        <div className="flex items-center justify-between text-sm text-gray-400">
          <span>Click "Run" to execute your code</span>
          <span>{results.length} tests completed</span>
        </div>
      </div>
    </div>
  );
}