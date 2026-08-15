'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { showToast } from '@/components/ui/Toast';
import { FetchClient } from '@/lib/fetch-client';
import { validateLessonForm, validateIdUnique, FieldErrors } from '@/lib/validation';
import MarkdownPreview from './MarkdownPreview';
import QuestionEditor from './QuestionEditor';

const api = new FetchClient();

interface QuestionData {
  title: string;
  difficulty: string;
  category: string;
  description: string;
  starter_code: { python: string; javascript: string; java: string };
  examples: { input: string; output: string; explanation: string }[];
  test_cases: {
    input: string;
    expected_output: string;
    description: string;
    hidden: boolean;
  }[];
  hints: string[];
  constraints: string[];
}

interface LessonFormProps {
  initial?: {
    id: string;
    title: string;
    type?: string;
    content?: string;
    order?: number;
    language?: string;
    starter_code?: string;
    question_id?: string;
  };
  initialQuestion?: QuestionData;
  moduleId?: string;
  saving: boolean;
  onSave: (data: Record<string, any>) => void;
  onCancel: () => void;
}

export default function LessonForm({
  initial,
  initialQuestion,
  moduleId,
  saving,
  onSave,
  onCancel,
}: LessonFormProps) {
  const isEdit = !!initial;
  const [f, setF] = useState({
    id: initial?.id || '',
    title: initial?.title || '',
    type: initial?.type || 'theory',
    content: initial?.content || '',
    order: initial?.order ?? 1,
    starter_code: initial?.starter_code || '',
    question_id: initial?.question_id || '',
  });
  const [errors, setErrors] = useState<FieldErrors>({});
  const [idChecking, setIdChecking] = useState(false);
  const [contentTab, setContentTab] = useState<'edit' | 'preview'>('edit');
  const [questionData, setQuestionData] = useState<QuestionData>(
    initialQuestion || {
      title: '',
      difficulty: 'medium',
      category: '',
      description: '',
      starter_code: { python: '', javascript: '', java: '' },
      examples: [],
      test_cases: [],
      hints: [],
      constraints: [],
    },
  );
  const [questionSaving, setQuestionSaving] = useState(false);

  const set = (k: string, v: any) => {
    setF((p) => ({ ...p, [k]: v }));
    setErrors((p) => {
      const next = { ...p };
      delete next[k];
      return next;
    });
  };

  useEffect(() => {
    const syncErrors = validateLessonForm(f);
    setErrors(syncErrors);
  }, [f]);

  const saveQuestion = async (): Promise<string | null> => {
    if (!questionData.title) {
      showToast('Question title is required for exercises', 'error');
      return null;
    }

    setQuestionSaving(true);
    try {
      const questionId =
        f.question_id ||
        questionData.title
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, '-')
          .replace(/^-|-$/g, '');
      const body = {
        id: questionId,
        title: questionData.title,
        difficulty: questionData.difficulty,
        category: questionData.category,
        description: questionData.description,
        starter_code: questionData.starter_code,
        examples: questionData.examples,
        test_cases: questionData.test_cases,
        hints: questionData.hints,
        constraints: questionData.constraints,
      };

      if (f.question_id) {
        await api.put(`/api/admin/questions/${f.question_id}`, body);
      } else {
        await api.post('/api/admin/questions', body);
      }

      return questionId;
    } catch (e: any) {
      showToast(e.message || 'Failed to save question', 'error');
      return null;
    } finally {
      setQuestionSaving(false);
    }
  };

  const handleSave = async () => {
    const syncErrors = validateLessonForm(f);
    if (Object.keys(syncErrors).length > 0) {
      setErrors(syncErrors);
      return;
    }

    if (!isEdit) {
      setIdChecking(true);
      const idErr = await validateIdUnique('lesson', f.id, isEdit);
      setIdChecking(false);
      if (idErr) {
        setErrors({ id: idErr });
        return;
      }
    }

    let lessonData = { ...f };

    if (f.type === 'exercise' && questionData.title) {
      const qId = await saveQuestion();
      if (qId) {
        lessonData.question_id = qId;
      } else {
        return;
      }
    }

    onSave(lessonData);
  };

  const inputClass = (field: string) =>
    `w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border outline-none transition-all duration-200 ${
      errors[field] ? 'border-destructive ring-1 ring-destructive/20' : 'border-border'
    } ${field === 'id' ? 'font-mono' : ''}`;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="text-xs text-muted-foreground block mb-1">ID *</label>
          <input
            className={inputClass('id')}
            value={f.id}
            onChange={(e) => set('id', e.target.value)}
            disabled={isEdit}
            placeholder="hello-world"
          />
          {errors.id && <p className="text-xs text-destructive mt-1">{errors.id}</p>}
        </div>
        <div>
          <label className="text-xs text-muted-foreground block mb-1">Order</label>
          <input
            type="number"
            className={inputClass('order')}
            value={f.order}
            onChange={(e) => set('order', Number(e.target.value))}
          />
          {errors.order && <p className="text-xs text-destructive mt-1">{errors.order}</p>}
        </div>
        <div>
          <label className="text-xs text-muted-foreground block mb-1">Type</label>
          <select
            className="w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none"
            value={f.type}
            onChange={(e) => set('type', e.target.value)}
          >
            <option value="theory">Theory</option>
            <option value="exercise">Exercise</option>
          </select>
        </div>
      </div>
      <div>
        <label className="text-xs text-muted-foreground block mb-1">Title *</label>
        <input
          className={inputClass('title')}
          value={f.title}
          onChange={(e) => set('title', e.target.value)}
          placeholder="Hello, World!"
        />
        {errors.title && <p className="text-xs text-destructive mt-1">{errors.title}</p>}
      </div>

      {/* Content — Split Pane with Edit/Preview Tabs */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <label className="text-xs text-muted-foreground">
            Content (Markdown)
            {f.type === 'exercise' && !questionData.title && (
              <span className="ml-2 text-yellow-400">No question data — add test cases below</span>
            )}
          </label>
          <div className="flex gap-1">
            <button
              onClick={() => setContentTab('edit')}
              className={`text-[10px] px-2 py-0.5 rounded transition-colors ${
                contentTab === 'edit'
                  ? 'bg-primary/10 text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              Edit
            </button>
            <button
              onClick={() => setContentTab('preview')}
              className={`text-[10px] px-2 py-0.5 rounded transition-colors ${
                contentTab === 'preview'
                  ? 'bg-primary/10 text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              Preview
            </button>
          </div>
        </div>
        <div className="border border-border rounded-lg overflow-hidden" style={{ minHeight: 200 }}>
          {contentTab === 'edit' ? (
            <textarea
              className="w-full h-48 text-sm bg-muted/50 px-3 py-2 border-0 outline-none resize-y font-mono"
              value={f.content}
              onChange={(e) => set('content', e.target.value)}
              placeholder="# Lesson title&#10;&#10;Content here..."
            />
          ) : (
            <div className="p-3 bg-card">
              <MarkdownPreview content={f.content} />
            </div>
          )}
        </div>
      </div>

      {/* Exercise: Question Editor with test cases */}
      {f.type === 'exercise' && (
        <div className="border border-border rounded-lg p-4 space-y-4 bg-muted/20">
          <div className="flex items-center justify-between">
            <label className="text-xs font-medium text-muted-foreground">
              Question & Test Cases
            </label>
            {f.question_id && (
              <span className="text-[10px] text-muted-foreground font-mono">
                linked: {f.question_id}
              </span>
            )}
          </div>
          <QuestionEditor
            initial={
              initialQuestion || {
                title: f.title,
                description: '',
                difficulty: 'medium',
                category: '',
                starter_code: { python: '', javascript: '', java: '' },
                examples: [],
                test_cases: [],
                hints: [],
                constraints: [],
              }
            }
            compact
            onChange={(data) => setQuestionData(data)}
          />
        </div>
      )}

      <div className="flex items-center justify-between pt-2">
        <div className="flex gap-2">
          <Button
            size="sm"
            onClick={handleSave}
            disabled={saving || idChecking || questionSaving || Object.keys(errors).length > 0}
          >
            {saving || questionSaving
              ? 'Saving...'
              : idChecking
                ? 'Checking...'
                : initial
                  ? 'Update'
                  : 'Create'}
          </Button>
          <Button variant="outline" size="sm" onClick={onCancel}>
            Cancel
          </Button>
        </div>
      </div>
    </div>
  );
}
