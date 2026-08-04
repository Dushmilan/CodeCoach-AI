import { Question } from '@/types';

export interface ClientJsTestResult {
  index: number;
  passed: boolean;
  input: string;
  expected: string;
  actual: unknown;
  error?: string;
}

export interface ClientJsOutput {
  logs: string[];
  results: ClientJsTestResult[];
  allPassed: boolean;
}

/**
 * Source of the sandbox worker. Exported for tests.
 *
 * Runs inside a dedicated Web Worker so user code:
 *  - never touches the page's `window`, `document`, `localStorage` (JWT
 *    lives there) or cookies,
 *  - cannot reach the network (fetch/XMLHttpRequest/WebSocket/importScripts
 *    are stripped), and
 *  - is killed by `worker.terminate()` when the hard timeout fires, so an
 *    infinite loop cannot freeze the tab.
 */
export function buildWorkerSource(): string {
  return `
"use strict";
self.onmessage = function (event) {
  var data = event.data;
  // Strip network + storage exfiltration surfaces before user code runs.
  try {
    self.fetch = undefined;
    self.XMLHttpRequest = undefined;
    self.WebSocket = undefined;
    self.importScripts = undefined;
    self.sendBeacon = undefined;
    self.localStorage = undefined;
    self.sessionStorage = undefined;
    self.indexedDB = undefined;
    self.caches = undefined;
  } catch (err) {
    /* storage accessors may not be configurable; access throws, which is fine */
  }

  try {
    var logs = [];
    var originalLog = console.log;
    var originalError = console.error;
    var originalWarn = console.warn;
    console.log = function () {
      var args = Array.prototype.map.call(arguments, function (arg) {
        return typeof arg === "object" && arg !== null ? JSON.stringify(arg) : String(arg);
      });
      logs.push(args.join(" "));
    };
    console.error = console.log;
    console.warn = console.log;

    var testRunner = new Function(
      "testCases",
      data.code + "\\n\\n" +
      "if (typeof " + data.functionName + " !== 'function') { throw new Error('Function \\\"" + data.functionName + "\\\" is not defined or is not a function.'); }" +
      "return testCases.map(function (tc, index) {" +
      "  try {" +
      "    var inputLines = tc.input.split('\\\\n');" +
      "    var parsedArgs = inputLines.map(function (line) {" +
      "      try { return JSON.parse(line); } catch (err) { return line; }" +
      "    });" +
      "    var result = " + data.functionName + "(...parsedArgs);" +
      "    var actual = result !== undefined ? result : parsedArgs[0];" +
      "    var expectedOutput;" +
      "    try { expectedOutput = JSON.parse(tc.expected_output); } catch (err) { expectedOutput = tc.expected_output; }" +
      "    var passed = JSON.stringify(actual) === JSON.stringify(expectedOutput);" +
      "    return { index: index + 1, passed: passed, input: tc.input, expected: tc.expected_output, actual: actual };" +
      "  } catch (err) {" +
      "    return { index: index + 1, passed: false, error: (err && err.message) || String(err), input: tc.input };" +
      "  }" +
      "});"
    );

    var results = testRunner(data.testCases);
    console.log = originalLog;
    console.error = originalError;
    console.warn = originalWarn;

    var allPassed = true;
    for (var i = 0; i < results.length; i++) {
      if (!results[i].passed) {
        allPassed = false;
        break;
      }
    }

    self.postMessage({
      ok: true,
      logs: logs,
      results: results,
      allPassed: allPassed,
    });
  } catch (err) {
    self.postMessage({
      ok: false,
      error: (err && err.message) || String(err),
    });
  }
};
`;
}

function detectFunctionName(question: Question, fnName?: string): string | null {
  if (fnName) return fnName;
  const jsStarter = question.starter.javascript;
  if (!jsStarter) return null;
  return (
    jsStarter.match(/function\s+(\w+)\s*\(/)?.[1] ||
    jsStarter.match(/var\s+(\w+)\s*=\s*function/)?.[1] ||
    jsStarter.match(/const\s+(\w+)\s*=/)?.[1] ||
    null
  );
}

const DEFAULT_TIMEOUT_MS = 5000;

/**
 * Run user-authored JavaScript in a sandboxed Web Worker.
 *
 * Resolves with test results or rejects on: unidentifiable target function,
 * worker error, or timeout (infinite loop / long-running code).
 */
export function executeClientJS(
  code: string,
  question: Question,
  fnName?: string,
  timeoutMs: number = DEFAULT_TIMEOUT_MS,
): Promise<ClientJsOutput> {
  const functionName = detectFunctionName(question, fnName);

  if (!functionName) {
    return Promise.reject(new Error('Could not identify the target function name for testing.'));
  }

  return new Promise<ClientJsOutput>((resolve, reject) => {
    let worker: Worker | null = null;
    let blobUrl: string | null = null;
    let settled = false;

    const cleanup = () => {
      if (worker) {
        try {
          worker.terminate();
        } catch {
          /* ignore */
        }
        worker = null;
      }
      if (blobUrl) {
        try {
          URL.revokeObjectURL(blobUrl);
        } catch {
          /* ignore */
        }
        blobUrl = null;
      }
    };

    const fail = (error: Error) => {
      if (settled) return;
      settled = true;
      cleanup();
      reject(error);
    };

    const timeoutId = setTimeout(
      () => fail(new Error('JavaScript execution timed out.')),
      timeoutMs,
    );

    try {
      const blob = new Blob([buildWorkerSource()], {
        type: 'application/javascript',
      });
      blobUrl = URL.createObjectURL(blob);
      worker = new Worker(blobUrl);

      worker.onmessage = (event: MessageEvent) => {
        if (settled) return;
        settled = true;
        clearTimeout(timeoutId);
        cleanup();
        const message = event.data;
        if (message && message.ok) {
          resolve({
            logs: Array.isArray(message.logs) ? message.logs : [],
            results: message.results,
            allPassed: message.allPassed,
          });
        } else {
          reject(new Error(message?.error || 'JavaScript execution failed.'));
        }
      };

      worker.onerror = (event) => {
        clearTimeout(timeoutId);
        fail(new Error(event.message || 'JavaScript execution error.'));
      };

      worker.postMessage({
        code,
        functionName,
        testCases: question.test_cases,
      });
    } catch (error) {
      clearTimeout(timeoutId);
      fail(
        error instanceof Error
          ? error
          : new Error('JavaScript execution is unavailable in this environment.'),
      );
    }
  });
}

export function formatClientJsOutput(output: ClientJsOutput, question: Question): string {
  const lines: string[] = [];

  if (output.logs.length > 0) {
    lines.push(`Console Output:\n${output.logs.join('\n')}\n`);
  }

  lines.push('Test Results:\n');

  for (const r of output.results) {
    const testCase = question.test_cases[r.index - 1];
    const status = r.passed ? 'Pass' : 'Fail';
    lines.push(`${r.passed ? '✅' : '❌'} Test Case ${r.index}:`);
    lines.push(`   Status: ${status}`);
    lines.push(`   Input: ${r.input}`);
    lines.push(`   Expected Output: ${r.expected}`);
    if (r.error) {
      lines.push(`   Actual Output: (Error) ${r.error}`);
    } else {
      lines.push(`   Actual Output: ${JSON.stringify(r.actual)}`);
    }
    lines.push('');
  }

  return lines.join('\n');
}
