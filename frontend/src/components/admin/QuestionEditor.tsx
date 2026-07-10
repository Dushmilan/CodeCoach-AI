'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Plus, Trash2 } from 'lucide-react';

interface Example {
  input: string;
  output: string;
  explanation: string;
}

interface TestCase {
  input: string;
  expected_output: string;
  description: string;
  hidden: boolean;
}

interface QuestionEditorProps {
  initial?: {
    title?: string;
    difficulty?: string;
    category?: string;
    description?: string;
    starter_code?: { python: string; javascript: string; java: string };
    examples?: Example[];
    test_cases?: TestCase[];
    hints?: string[];
    constraints?: string[];
  };
  onChange: (data: {
    title: string;
    difficulty: string;
    category: string;
    description: string;
    starter_code: { python: string; javascript: string; java: string };
    examples: Example[];
    test_cases: TestCase[];
    hints: string[];
    constraints: string[];
  }) => void;
  /** Hide non-essential fields (title, difficulty, category) when embedded in LessonForm */
  compact?: boolean;
}

const LANGUAGES = ['python', 'javascript', 'java'] as const;
const LANG_LABELS: Record<string, string> = {
  python: 'Python',
  javascript: 'JavaScript',
  java: 'Java',
};

export default function QuestionEditor({
  initial,
  onChange,
  compact = false,
}: QuestionEditorProps) {
  const [title, setTitle] = useState(initial?.title || '');
  const [difficulty, setDifficulty] = useState(initial?.difficulty || 'medium');
  const [category, setCategory] = useState(initial?.category || '');
  const [description, setDescription] = useState(initial?.description || '');
  const [activeLang, setActiveLang] = useState<string>('python');
  const [starterCode, setStarterCode] = useState<Record<string, string>>({
    python: initial?.starter_code?.python || '',
    javascript: initial?.starter_code?.javascript || '',
    java: initial?.starter_code?.java || '',
  });
  const [examples, setExamples] = useState<Example[]>(
    initial?.examples?.length ? initial.examples : [{ input: '', output: '', explanation: '' }],
  );
  const [testCases, setTestCases] = useState<TestCase[]>(
    initial?.test_cases?.length
      ? initial.test_cases.map((tc) => ({ ...tc, hidden: tc.hidden ?? false }))
      : [{ input: '', expected_output: '', description: '', hidden: false }],
  );
  const [hints, setHints] = useState(initial?.hints?.join('\n') || '');
  const [constraints, setConstraints] = useState(initial?.constraints?.join('\n') || '');

  const emit = (
    overrides: Partial<{
      title: string;
      difficulty: string;
      category: string;
      description: string;
      starter_code: Record<string, string>;
      examples: Example[];
      test_cases: TestCase[];
      hints: string;
      constraints: string;
    }> = {},
  ) => {
    const next = {
      title: overrides.title ?? title,
      difficulty: overrides.difficulty ?? difficulty,
      category: overrides.category ?? category,
      description: overrides.description ?? description,
      starter_code: (overrides.starter_code ?? starterCode) as {
        python: string;
        javascript: string;
        java: string;
      },
      examples: overrides.examples ?? examples,
      test_cases: overrides.test_cases ?? testCases,
      hints: (overrides.hints ?? hints).split('\n').filter(Boolean),
      constraints: (overrides.constraints ?? constraints).split('\n').filter(Boolean),
    };
    onChange(next);
  };

  const updateStarterCode = (lang: string, code: string) => {
    const next = { ...starterCode, [lang]: code };
    setStarterCode(next);
    emit({ starter_code: next });
  };

  const addExample = () => {
    const next = [...examples, { input: '', output: '', explanation: '' }];
    setExamples(next);
    emit({ examples: next });
  };

  const updateExample = (idx: number, field: keyof Example, value: string) => {
    const next = examples.map((ex, i) => (i === idx ? { ...ex, [field]: value } : ex));
    setExamples(next);
    emit({ examples: next });
  };

  const removeExample = (idx: number) => {
    const next = examples.filter((_, i) => i !== idx);
    setExamples(next.length ? next : [{ input: '', output: '', explanation: '' }]);
    emit({ examples: next.length ? next : [{ input: '', output: '', explanation: '' }] });
  };

  const addTestCase = () => {
    const next = [...testCases, { input: '', expected_output: '', description: '', hidden: false }];
    setTestCases(next);
    emit({ test_cases: next });
  };

  const updateTestCase = (idx: number, field: keyof TestCase, value: string | boolean) => {
    const next = testCases.map((tc, i) => (i === idx ? { ...tc, [field]: value } : tc));
    setTestCases(next);
    emit({ test_cases: next });
  };

  const removeTestCase = (idx: number) => {
    const next = testCases.filter((_, i) => i !== idx);
    setTestCases(
      next.length ? next : [{ input: '', expected_output: '', description: '', hidden: false }],
    );
    emit({
      test_cases: next.length
        ? next
        : [{ input: '', expected_output: '', description: '', hidden: false }],
    });
  };

  return (
    <div className="space-y-5">
      {!compact && (
        <>
          {/* Title + Difficulty + Category */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <label className="text-xs text-muted-foreground block mb-1">Question Title *</label>
              <input
                className="w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none"
                value={title}
                onChange={(e) => {
                  setTitle(e.target.value);
                  emit({ title: e.target.value });
                }}
                placeholder="Two Sum"
              />
            </div>
            <div>
              <label className="text-xs text-muted-foreground block mb-1">Difficulty</label>
              <select
                className="w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none"
                value={difficulty}
                onChange={(e) => {
                  setDifficulty(e.target.value);
                  emit({ difficulty: e.target.value });
                }}
              >
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>
          </div>

          <div>
            <label className="text-xs text-muted-foreground block mb-1">Category</label>
            <input
              className="w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none"
              value={category}
              onChange={(e) => {
                setCategory(e.target.value);
                emit({ category: e.target.value });
              }}
              placeholder="arrays, strings, trees..."
            />
          </div>
        </>
      )}

      {/* Description */}
      <div>
        <label className="text-xs text-muted-foreground block mb-1">Description (Markdown)</label>
        <textarea
          className="w-full h-32 text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none resize-y font-mono"
          value={description}
          onChange={(e) => {
            setDescription(e.target.value);
            emit({ description: e.target.value });
          }}
          placeholder="Given an array of integers, return indices of two numbers that add up to target..."
        />
      </div>

      {/* Starter Code — Language Tabs */}
      <div>
        <label className="text-xs text-muted-foreground block mb-2">Starter Code</label>
        <div className="flex gap-2 mb-2">
          {LANGUAGES.map((lang) => (
            <button
              key={lang}
              onClick={() => setActiveLang(lang)}
              className={`text-xs px-3 py-1.5 rounded-lg border transition-all duration-200 ${
                activeLang === lang
                  ? 'bg-primary/10 text-primary border-primary/20'
                  : 'bg-muted/30 text-muted-foreground border-border hover:bg-muted/50'
              }`}
            >
              {LANG_LABELS[lang]}
            </button>
          ))}
        </div>
        <textarea
          className="w-full h-32 text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none resize-y font-mono"
          value={starterCode[activeLang]}
          onChange={(e) => updateStarterCode(activeLang, e.target.value)}
          placeholder={
            activeLang === 'python'
              ? 'def two_sum(nums, target):\n    pass'
              : activeLang === 'javascript'
              ? 'function twoSum(nums, target) {\n}'
              : 'class Solution {\n    public int[] twoSum(int[] nums, int target) {\n    }\n}'
          }
        />
      </div>

      {/* Examples */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="text-xs text-muted-foreground">Examples</label>
          <Button variant="ghost" size="sm" onClick={addExample} className="h-7 text-xs">
            <Plus className="h-3 w-3 mr-1" /> Add
          </Button>
        </div>
        <div className="space-y-3">
          {examples.map((ex, idx) => (
            <div key={idx} className="bg-muted/30 rounded-lg p-3 border border-border/50 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-muted-foreground">Example {idx + 1}</span>
                {examples.length > 1 && (
                  <button
                    onClick={() => removeExample(idx)}
                    className="text-muted-foreground hover:text-destructive transition-colors"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                )}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                <input
                  className="text-xs bg-muted/50 rounded px-2 py-1.5 border border-border outline-none font-mono"
                  placeholder="Input"
                  value={ex.input}
                  onChange={(e) => updateExample(idx, 'input', e.target.value)}
                />
                <input
                  className="text-xs bg-muted/50 rounded px-2 py-1.5 border border-border outline-none font-mono"
                  placeholder="Expected Output"
                  value={ex.output}
                  onChange={(e) => updateExample(idx, 'output', e.target.value)}
                />
              </div>
              <input
                className="w-full text-xs bg-muted/50 rounded px-2 py-1.5 border border-border outline-none"
                placeholder="Explanation (optional)"
                value={ex.explanation}
                onChange={(e) => updateExample(idx, 'explanation', e.target.value)}
              />
            </div>
          ))}
        </div>
      </div>

      {/* Test Cases */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="text-xs text-muted-foreground">Test Cases</label>
          <Button variant="ghost" size="sm" onClick={addTestCase} className="h-7 text-xs">
            <Plus className="h-3 w-3 mr-1" /> Add
          </Button>
        </div>
        <div className="space-y-3">
          {testCases.map((tc, idx) => (
            <div key={idx} className="bg-muted/30 rounded-lg p-3 border border-border/50 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-muted-foreground">Test Case {idx + 1}</span>
                  <label className="flex items-center gap-1.5 cursor-pointer select-none">
                    <span className="text-[10px] text-muted-foreground">Hidden</span>
                    <button
                      type="button"
                      role="switch"
                      aria-checked={tc.hidden}
                      onClick={() => updateTestCase(idx, 'hidden', !tc.hidden)}
                      className={`relative inline-flex h-4 w-7 shrink-0 cursor-pointer rounded-full border border-transparent transition-colors duration-200 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ${
                        tc.hidden ? 'bg-primary' : 'bg-muted'
                      }`}
                    >
                      <span
                        className={`pointer-events-none inline-block h-3 w-3 transform rounded-full bg-white shadow-lg ring-0 transition-transform duration-200 ease-in-out mt-[1px] ${
                          tc.hidden ? 'translate-x-3.5 ml-[1px]' : 'translate-x-0 ml-[1px]'
                        }`}
                      />
                    </button>
                  </label>
                </div>
                {testCases.length > 1 && (
                  <button
                    onClick={() => removeTestCase(idx)}
                    className="text-muted-foreground hover:text-destructive transition-colors"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                )}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                <textarea
                  className="text-xs bg-muted/50 rounded px-2 py-1.5 border border-border outline-none resize-y font-mono"
                  placeholder="Input"
                  rows={2}
                  value={tc.input}
                  onChange={(e) => updateTestCase(idx, 'input', e.target.value)}
                />
                <textarea
                  className="text-xs bg-muted/50 rounded px-2 py-1.5 border border-border outline-none resize-y font-mono"
                  placeholder="Expected Output"
                  rows={2}
                  value={tc.expected_output}
                  onChange={(e) => updateTestCase(idx, 'expected_output', e.target.value)}
                />
              </div>
              <input
                className="w-full text-xs bg-muted/50 rounded px-2 py-1.5 border border-border outline-none"
                placeholder="Description (optional)"
                value={tc.description}
                onChange={(e) => updateTestCase(idx, 'description', e.target.value)}
              />
            </div>
          ))}
        </div>
      </div>

      {/* Hints + Constraints */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="text-xs text-muted-foreground block mb-1">Hints (one per line)</label>
          <textarea
            className="w-full h-24 text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none resize-y"
            value={hints}
            onChange={(e) => {
              setHints(e.target.value);
              emit({ hints: e.target.value });
            }}
            placeholder="Try using a hash map...&#10;Think about edge cases..."
          />
        </div>
        <div>
          <label className="text-xs text-muted-foreground block mb-1">
            Constraints (one per line)
          </label>
          <textarea
            className="w-full h-24 text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none resize-y"
            value={constraints}
            onChange={(e) => {
              setConstraints(e.target.value);
              emit({ constraints: e.target.value });
            }}
            placeholder="1 <= n <= 10^5&#10;-10^9 <= arr[i] <= 10^9"
          />
        </div>
      </div>
    </div>
  );
}
