'use client';
export const dynamic = 'force-dynamic';

import { useEffect, useState, useCallback } from 'react';
import { useAuth } from '@/providers';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileText, Trash2, Upload, Download, Search } from 'lucide-react';

interface QBrief {
  id: string;
  title: string;
  difficulty: string;
  category: string;
  solution?: string | null;
}

export default function QuestionsPage() {
  const { user } = useAuth();
  const [questions, setQuestions] = useState<QBrief[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ difficulty: '', category: '', page: 1, per_page: 20 });
  const [importOpen, setImportOpen] = useState(false);
  const [importJson, setImportJson] = useState('');
  const [importResult, setImportResult] = useState<any>(null);

  const fetchQuestions = useCallback(async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('auth_token');
      const params = new URLSearchParams({
        page: String(filter.page),
        per_page: String(filter.per_page),
      });
      if (filter.difficulty) params.set('difficulty', filter.difficulty);
      if (filter.category) params.set('category', filter.category);
      const res = await fetch(`/api/admin/questions?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Failed');
      const data = await res.json();
      setQuestions(data.questions || []);
      setTotal(data.total || 0);
    } catch {
      /* */
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    fetchQuestions();
  }, [fetchQuestions]);

  const deleteQ = async (id: string) => {
    if (!confirm('Delete this question?')) return;
    const token = localStorage.getItem('auth_token');
    const res = await fetch(`/api/admin/questions/${id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) fetchQuestions();
  };

  const doImport = async () => {
    try {
      const data = JSON.parse(importJson);
      const token = localStorage.getItem('auth_token');
      const res = await fetch('/api/admin/questions/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ questions: Array.isArray(data) ? data : [data] }),
      });
      const result = await res.json();
      setImportResult(result);
      if (res.ok) fetchQuestions();
    } catch {
      setImportResult({
        total: 0,
        successful: 0,
        failed: 1,
        errors: [{ message: 'Invalid JSON' }],
      });
    }
  };

  const diffBadge = (d: string) => {
    const colors: Record<string, string> = {
      easy: 'bg-green-500/20 text-green-500',
      medium: 'bg-yellow-500/20 text-yellow-500',
      hard: 'bg-red-500/20 text-red-500',
    };
    return <span className={`text-xs px-2 py-0.5 rounded-full ${colors[d] || ''}`}>{d}</span>;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Questions</h1>
          <p className="text-muted-foreground text-sm mt-1">{total} total</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => setImportOpen(!importOpen)}>
            <Upload className="h-4 w-4 mr-1" /> Import JSON
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <select
          value={filter.difficulty}
          onChange={(e) => setFilter((f) => ({ ...f, difficulty: e.target.value, page: 1 }))}
          className="text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none"
        >
          <option value="">All Difficulties</option>
          <option value="easy">Easy</option>
          <option value="medium">Medium</option>
          <option value="hard">Hard</option>
        </select>
        <input
          className="text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none w-48"
          placeholder="Category filter..."
          value={filter.category}
          onChange={(e) => setFilter((f) => ({ ...f, category: e.target.value, page: 1 }))}
        />
      </div>

      {/* Import Panel */}
      {importOpen && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Import Questions (JSON)</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <textarea
              className="w-full h-32 bg-muted/30 rounded-lg p-3 text-sm font-mono border border-border outline-none resize-none"
              placeholder='[{ "title": "...", "difficulty": "medium", "category": "arrays", "description": "...", ... }]'
              value={importJson}
              onChange={(e) => setImportJson(e.target.value)}
            />
            <div className="flex gap-2">
              <Button size="sm" onClick={doImport}>
                Import
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setImportOpen(false);
                  setImportJson('');
                  setImportResult(null);
                }}
              >
                Cancel
              </Button>
            </div>
            {importResult && (
              <div
                className={`text-sm p-3 rounded-lg ${
                  importResult.failed > 0
                    ? 'bg-red-500/10 text-red-400'
                    : 'bg-green-500/10 text-green-500'
                }`}
              >
                {importResult.successful} imported, {importResult.failed} failed
                {importResult.errors?.map((e: any, i: number) => (
                  <div key={i} className="text-xs mt-1">
                    {e.message || JSON.stringify(e)}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* List */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
        </div>
      ) : questions.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No questions found.
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="pt-4">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-muted-foreground text-xs uppercase">
                    <th className="text-left pb-3 font-medium">Title</th>
                    <th className="text-left pb-3 font-medium">Difficulty</th>
                    <th className="text-left pb-3 font-medium">Category</th>
                    <th className="text-left pb-3 font-medium">Solution</th>
                    <th className="text-right pb-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {questions.map((q) => (
                    <tr
                      key={q.id}
                      className="border-b border-border/50 hover:bg-muted/20 transition-colors"
                    >
                      <td className="py-3 font-medium">{q.title}</td>
                      <td className="py-3">{diffBadge(q.difficulty)}</td>
                      <td className="py-3 text-muted-foreground text-xs">{q.category}</td>
                      <td className="py-3">
                        {q.solution ? (
                          <span className="text-xs text-green-500">Has solution</span>
                        ) : (
                          <span className="text-xs text-muted-foreground">None</span>
                        )}
                      </td>
                      <td className="py-3 text-right">
                        <button
                          onClick={() => deleteQ(q.id)}
                          className="text-xs p-1.5 rounded hover:bg-red-500/10 text-red-400 transition-colors"
                          title="Delete"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {total > filter.per_page && (
              <div className="flex items-center justify-between mt-4 pt-4 border-t border-border">
                <span className="text-xs text-muted-foreground">
                  Page {filter.page} of {Math.ceil(total / filter.per_page)}
                </span>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={filter.page === 1}
                    onClick={() => setFilter((f) => ({ ...f, page: f.page - 1 }))}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={filter.page >= Math.ceil(total / filter.per_page)}
                    onClick={() => setFilter((f) => ({ ...f, page: f.page + 1 }))}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
