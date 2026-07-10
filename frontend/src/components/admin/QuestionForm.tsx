'use client';

import { useState } from 'react';
import { showToast } from '@/components/ui/Toast';
import { Button } from '@/components/ui/button';
import { FetchClient } from '@/lib/fetch-client';
import QuestionEditor from './QuestionEditor';

const api = new FetchClient();

interface QuestionFormProps {
  initial?: Record<string, any>;
  onSaved: () => void;
  onCancel: () => void;
}

export default function QuestionForm({ initial, onSaved, onCancel }: QuestionFormProps) {
  const isEdit = !!initial;
  const [saving, setSaving] = useState(false);
  const [questionData, setQuestionData] = useState({
    title: initial?.title || '',
    difficulty: initial?.difficulty || 'medium',
    category: initial?.category || '',
    description: initial?.description || '',
    starter_code: initial?.starter_code || { python: '', javascript: '', java: '' },
    examples: initial?.examples || [],
    test_cases: initial?.test_cases || [],
    hints: initial?.hints || [],
    constraints: initial?.constraints || [],
  });

  const handleSave = async () => {
    if (!questionData.title) {
      showToast('Title is required', 'error');
      return;
    }

    setSaving(true);
    try {
      const body = {
        id:
          initial?.id ||
          questionData.title
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/^-|-$/g, ''),
        title: questionData.title,
        difficulty: questionData.difficulty,
        category: questionData.category,
        description: questionData.description,
        starter_code: questionData.starter_code,
        examples: questionData.examples,
        test_cases: questionData.test_cases,
        hints: questionData.hints,
        constraints: questionData.constraints,
        solution: initial?.solution || null,
        time_complexity: initial?.time_complexity || '',
        space_complexity: initial?.space_complexity || '',
      };

      if (isEdit) {
        await api.put(`/api/admin/questions/${initial.id}`, body);
      } else {
        await api.post('/api/admin/questions', body);
      }

      showToast(isEdit ? 'Question updated' : 'Question created', 'success');
      onSaved();
    } catch (e: any) {
      showToast(e.message || 'Failed to save question', 'error');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <QuestionEditor initial={initial} onChange={(data) => setQuestionData(data)} />
      <div className="flex items-center gap-2 pt-2">
        <Button size="sm" onClick={handleSave} disabled={saving}>
          {saving ? 'Saving...' : isEdit ? 'Update Question' : 'Create Question'}
        </Button>
        <Button variant="outline" size="sm" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </div>
  );
}
