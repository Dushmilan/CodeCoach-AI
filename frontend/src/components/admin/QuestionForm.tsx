'use client';

import { useState } from 'react';
import { showToast } from '@/components/ui/Toast';
import { Button } from '@/components/ui/button';

interface QuestionFormProps {
  token: string;
  initial?: Record<string, any>;
  onSaved: () => void;
  onCancel: () => void;
}

export default function QuestionForm({ token, initial, onSaved, onCancel }: QuestionFormProps) {
  const isEdit = !!initial;
  const [form, setForm] = useState({
    id: initial?.id || '',
    title: initial?.title || '',
    difficulty: initial?.difficulty || 'medium',
    category: initial?.category || '',
    description: initial?.description || '',
    solution: initial?.solution || '',
    time_complexity: initial?.time_complexity || '',
    space_complexity: initial?.space_complexity || '',
    hints: Array.isArray(initial?.hints) ? initial.hints.join('\n') : '',
    constraints: Array.isArray(initial?.constraints) ? initial.constraints.join('\n') : '',
  });
  const [saving, setSaving] = useState(false);

  const set = (key: string, val: any) => setForm((f) => ({ ...f, [key]: val }));

  const handleSave = async () => {
    if (!form.id || !form.title) {
      showToast('ID and Title are required', 'error');
      return;
    }

    setSaving(true);
    try {
      const body: Record<string, any> = {
        id: form.id,
        title: form.title,
        difficulty: form.difficulty,
        category: form.category,
        description: form.description,
        solution: form.solution || null,
        time_complexity: form.time_complexity,
        space_complexity: form.space_complexity,
        hints: form.hints ? form.hints.split('\n').filter(Boolean) : [],
        constraints: form.constraints ? form.constraints.split('\n').filter(Boolean) : [],
        starter_code: { python: '', javascript: '', java: '' },
        examples: [],
        test_cases: [],
      };

      const url = isEdit ? `/api/admin/questions/${initial.id}` : '/api/admin/questions';
      const method = isEdit ? 'PUT' : 'POST';

      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(isEdit ? body : body),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to save question');
      }

      showToast(isEdit ? 'Question updated' : 'Question created', 'success');
      onSaved();
    } catch (e: any) {
      showToast(e.message, 'error');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="text-xs text-muted-foreground block mb-1">ID *</label>
          <input
            className="w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none font-mono"
            placeholder="unique-question-slug"
            value={form.id}
            onChange={(e) => set('id', e.target.value)}
            disabled={isEdit}
          />
        </div>
        <div>
          <label className="text-xs text-muted-foreground block mb-1">Title *</label>
          <input
            className="w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none"
            placeholder="Reverse a Linked List"
            value={form.title}
            onChange={(e) => set('title', e.target.value)}
          />
        </div>
        <div>
          <label className="text-xs text-muted-foreground block mb-1">Difficulty</label>
          <select
            className="w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none"
            value={form.difficulty}
            onChange={(e) => set('difficulty', e.target.value)}
          >
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
        </div>
        <div>
          <label className="text-xs text-muted-foreground block mb-1">Category</label>
          <input
            className="w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none"
            placeholder="arrays, strings, trees..."
            value={form.category}
            onChange={(e) => set('category', e.target.value)}
          />
        </div>
      </div>

      <div>
        <label className="text-xs text-muted-foreground block mb-1">Description</label>
        <textarea
          className="w-full h-28 text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none resize-y font-mono"
          placeholder="Problem description (markdown)"
          value={form.description}
          onChange={(e) => set('description', e.target.value)}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="text-xs text-muted-foreground block mb-1">Time Complexity</label>
          <input
            className="w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none"
            placeholder="O(n)"
            value={form.time_complexity}
            onChange={(e) => set('time_complexity', e.target.value)}
          />
        </div>
        <div>
          <label className="text-xs text-muted-foreground block mb-1">Space Complexity</label>
          <input
            className="w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none"
            placeholder="O(1)"
            value={form.space_complexity}
            onChange={(e) => set('space_complexity', e.target.value)}
          />
        </div>
      </div>

      <div>
        <label className="text-xs text-muted-foreground block mb-1">Solution</label>
        <textarea
          className="w-full h-20 text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none resize-y"
          placeholder="Solution explanation..."
          value={form.solution}
          onChange={(e) => set('solution', e.target.value)}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="text-xs text-muted-foreground block mb-1">Hints (one per line)</label>
          <textarea
            className="w-full h-24 text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none resize-y"
            placeholder="Try using a hash map...&#10;Think about two-pointer technique..."
            value={form.hints}
            onChange={(e) => set('hints', e.target.value)}
          />
        </div>
        <div>
          <label className="text-xs text-muted-foreground block mb-1">
            Constraints (one per line)
          </label>
          <textarea
            className="w-full h-24 text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none resize-y"
            placeholder="1 <= n <= 10^5&#10;-10^9 <= arr[i] <= 10^9"
            value={form.constraints}
            onChange={(e) => set('constraints', e.target.value)}
          />
        </div>
      </div>

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
