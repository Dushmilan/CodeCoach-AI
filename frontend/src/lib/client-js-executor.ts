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

export function executeClientJS(
  code: string,
  question: Question,
  fnName?: string
): ClientJsOutput {
  const logs: string[] = [];
  const originalConsoleLog = console.log;
  const originalConsoleError = console.error;
  const originalConsoleWarn = console.warn;

  const captureLog = (...args: unknown[]) => {
    const formattedArgs = args
      .map((arg) => (typeof arg === 'object' ? JSON.stringify(arg) : String(arg)))
      .join(' ');
    logs.push(formattedArgs);
    originalConsoleLog(...args);
  };

  console.log = captureLog;
  console.error = captureLog;
  console.warn = captureLog;

  try {
    const jsStarter = question.starter.javascript;
    const functionName =
      fnName ||
      jsStarter.match(/function\s+(\w+)\s*\(/)?.[1] ||
      jsStarter.match(/var\s+(\w+)\s*=\s*function/)?.[1] ||
      jsStarter.match(/const\s+(\w+)\s*=/)?.[1];

    if (!functionName) {
      throw new Error('Could not identify the target function name for testing.');
    }

    const testRunner = new Function(
      'testCases',
      `
      ${code}

      if (typeof ${functionName} !== 'function') {
        throw new Error('Function "${functionName}" is not defined or is not a function.');
      }

      return testCases.map((tc, index) => {
        try {
          const inputLines = tc.input.split('\\n');
          const parsedArgs = inputLines.map((line) => {
            try {
              return JSON.parse(line);
            } catch {
              return line;
            }
          });
          const result = ${functionName}(...parsedArgs);
          const expectedOutput = JSON.parse(tc.expected_output);
          const passed = JSON.stringify(result) === JSON.stringify(expectedOutput);
          return { index: index + 1, passed, input: tc.input, expected: tc.expected_output, actual: result };
        } catch (e) {
          return { index: index + 1, passed: false, error: (e).message, input: tc.input };
        }
      });
    `
    );

    const results = testRunner(question.test_cases);
    let allPassed = true;
    for (const r of results) {
      if (!r.passed) {
        allPassed = false;
        break;
      }
    }

    return { logs, results, allPassed };
  } finally {
    console.log = originalConsoleLog;
    console.error = originalConsoleError;
    console.warn = originalConsoleWarn;
  }
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
