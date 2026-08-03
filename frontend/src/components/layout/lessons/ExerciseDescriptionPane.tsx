import { MarkdownRenderer } from '@/components/learn/MarkdownRenderer';
import { LessonSummary, Question } from '@/types';

export interface ExerciseTestCase {
  input: string;
  expected_output: string;
  description?: string;
}

interface ExerciseDescriptionPaneProps {
  lesson: LessonSummary;
  linkedQuestion: Question | null;
  testCases: ExerciseTestCase[];
}

export function ExerciseDescriptionPane({
  lesson,
  linkedQuestion,
  testCases,
}: ExerciseDescriptionPaneProps) {
  return (
    <div>
      <div className="border border-white/[0.04] rounded-2xl p-6">
        <h3 className="text-[11px] uppercase tracking-widest text-muted-foreground/40 mb-3 font-mono">
          Lesson
        </h3>
        <MarkdownRenderer content={lesson.content} />
      </div>

      {linkedQuestion?.description && (
        <div className="mt-6 pt-5 border-t border-white/[0.04]">
          <h3 className="text-[11px] uppercase tracking-widest text-muted-foreground/40 mb-3 font-mono">
            Problem
          </h3>
          <MarkdownRenderer content={linkedQuestion.description} />
        </div>
      )}

      {testCases.length > 0 && (
        <div className="mt-6 pt-5 border-t border-white/[0.04]">
          <h3 className="text-[11px] uppercase tracking-widest text-muted-foreground/40 mb-3 font-mono">
            Test Cases
          </h3>
          <div className="space-y-2">
            {testCases.map((tc, i) => (
              <div key={i} className="border border-white/[0.04] rounded-lg px-3 py-2">
                <p className="text-xs text-foreground/70 font-medium">{tc.description}</p>
                <p className="text-[11px] font-mono text-muted-foreground/40 mt-1 tabular-nums">
                  input: &ldquo;{tc.input}&rdquo; &rarr; expected: &ldquo;
                  {tc.expected_output}&rdquo;
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
