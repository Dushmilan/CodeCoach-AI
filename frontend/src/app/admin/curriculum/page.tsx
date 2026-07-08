'use client';
export const dynamic = 'force-dynamic';

import { useEffect, useState, useCallback } from 'react';
import { useAuth } from '@/providers';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { showToast } from '@/components/ui/Toast';
import QuestionForm from '@/components/admin/QuestionForm';
import {
  Database,
  BookOpen,
  FileText,
  Trash2,
  Plus,
  Edit3,
  ChevronRight,
  ChevronDown,
  X,
  Code2,
} from 'lucide-react';

interface Course {
  id: string;
  title: string;
  description?: string;
  language?: string;
  icon?: string;
  order?: number;
}
interface Module {
  id: string;
  course_id: string;
  title: string;
  description?: string;
  order?: number;
}
interface Lesson {
  id: string;
  course_id: string;
  module_id: string;
  title: string;
  type?: string;
  order?: number;
  question_id?: string;
  language?: string;
}
interface CourseTree {
  courses: Course[];
  modules: Module[];
  lessons: Lesson[];
}
type EntityType = 'course' | 'module' | 'lesson' | 'question';

export default function CurriculumPage() {
  const { user, token } = useAuth();
  const [tree, setTree] = useState<CourseTree>({ courses: [], modules: [], lessons: [] });
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  // Form state
  const [formEntity, setFormEntity] = useState<{
    type: EntityType;
    initial?: any;
    parentId?: string;
  } | null>(null);
  const [questionFormForLesson, setQuestionFormForLesson] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const fetchTree = useCallback(async () => {
    try {
      const res = await fetch('/api/admin/courses/tree', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Failed');
      const data = await res.json();
      setTree(data);
    } catch {
      showToast('Failed to load curriculum', 'error');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchTree();
  }, [fetchTree]);

  const toggle = (id: string) => setExpanded((e) => ({ ...e, [id]: !e[id] }));
  const openForm = (type: EntityType, initial?: any, parentId?: string) => {
    setFormEntity({ type, initial, parentId });
  };
  const closeForm = () => setFormEntity(null);

  const del = async (type: string, id: string) => {
    if (!confirm(`Delete this ${type}?`)) return;
    const endpoints: Record<string, string> = {
      course: `/api/admin/courses/${id}`,
      module: `/api/admin/modules/${id}`,
      lesson: `/api/admin/lessons/${id}`,
    };
    const res = await fetch(endpoints[type], {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) {
      showToast(`${type} deleted`, 'success');
      fetchTree();
    } else {
      showToast(`Failed to delete ${type}`, 'error');
    }
  };

  const handleFormSave = async (formData: Record<string, any>) => {
    setSaving(true);
    try {
      const { type, initial, parentId } = formEntity || {};
      const isEdit = !!initial;

      let url = '';
      let method = 'POST';
      let body = { ...formData };

      if (type === 'course') {
        url = isEdit ? `/api/admin/courses/${initial.id}` : '/api/admin/courses';
        method = isEdit ? 'PUT' : 'POST';
      } else if (type === 'module') {
        url = isEdit ? `/api/admin/modules/${initial.id}` : '/api/admin/modules';
        method = isEdit ? 'PUT' : 'POST';
        if (!isEdit) body.course_id = parentId;
      } else if (type === 'lesson') {
        url = isEdit ? `/api/admin/lessons/${initial.id}` : '/api/admin/lessons';
        method = isEdit ? 'PUT' : 'POST';
        if (!isEdit) {
          body.course_id = tree.modules.find((m) => m.id === parentId)?.course_id || '';
          body.module_id = parentId || '';
        }
      }

      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(isEdit ? body : body),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Failed to save ${type}`);
      }

      showToast(`${type} saved`, 'success');
      closeForm();
      fetchTree();
    } catch (e: any) {
      showToast(e.message, 'error');
    } finally {
      setSaving(false);
    }
  };

  // ── Form components ──────────────────────────────────

  const CourseForm = ({ initial }: { initial?: any }) => {
    const [f, setF] = useState({
      id: initial?.id || '',
      title: initial?.title || '',
      description: initial?.description || '',
      language: initial?.language || '',
      icon: initial?.icon || 'code',
      order: initial?.order ?? 1,
    });
    const set = (k: string, v: any) => setF((p) => ({ ...p, [k]: v }));
    return (
      <div className="space-y-3 p-4 bg-muted/20 rounded-lg border border-border/50 ml-0 mt-2">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-muted-foreground block mb-1">ID *</label>
            <input
              className="w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none font-mono"
              value={f.id}
              onChange={(e) => set('id', e.target.value)}
              disabled={!!initial}
              placeholder="python-fundamentals"
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground block mb-1">Title *</label>
            <input
              className="w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none"
              value={f.title}
              onChange={(e) => set('title', e.target.value)}
              placeholder="Python Fundamentals"
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground block mb-1">Language</label>
            <input
              className="w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none"
              value={f.language}
              onChange={(e) => set('language', e.target.value)}
              placeholder="python"
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground block mb-1">Order</label>
            <input
              type="number"
              className="w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none"
              value={f.order}
              onChange={(e) => set('order', Number(e.target.value))}
            />
          </div>
        </div>
        <div>
          <label className="text-xs text-muted-foreground block mb-1">Description</label>
          <textarea
            className="w-full h-20 text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none resize-y"
            value={f.description}
            onChange={(e) => set('description', e.target.value)}
          />
        </div>
        <div className="flex gap-2">
          <Button size="sm" onClick={() => handleFormSave(f)} disabled={saving}>
            {saving ? 'Saving...' : initial ? 'Update' : 'Create'}
          </Button>
          <Button variant="outline" size="sm" onClick={closeForm}>
            Cancel
          </Button>
        </div>
      </div>
    );
  };

  const ModuleForm = ({ initial, courseId }: { initial?: any; courseId?: string }) => {
    const [f, setF] = useState({
      id: initial?.id || '',
      title: initial?.title || '',
      description: initial?.description || '',
      order: initial?.order ?? 1,
    });
    const set = (k: string, v: any) => setF((p) => ({ ...p, [k]: v }));
    return (
      <div className="space-y-3 p-4 bg-muted/20 rounded-lg border border-border/50 ml-8 mt-2">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-muted-foreground block mb-1">ID *</label>
            <input
              className="w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none font-mono"
              value={f.id}
              onChange={(e) => set('id', e.target.value)}
              disabled={!!initial}
              placeholder="getting-started"
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground block mb-1">Order</label>
            <input
              type="number"
              className="w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none"
              value={f.order}
              onChange={(e) => set('order', Number(e.target.value))}
            />
          </div>
        </div>
        <div>
          <label className="text-xs text-muted-foreground block mb-1">Title *</label>
          <input
            className="w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none"
            value={f.title}
            onChange={(e) => set('title', e.target.value)}
            placeholder="Getting Started"
          />
        </div>
        <div>
          <label className="text-xs text-muted-foreground block mb-1">Description</label>
          <textarea
            className="w-full h-16 text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none resize-y"
            value={f.description}
            onChange={(e) => set('description', e.target.value)}
          />
        </div>
        <div className="flex gap-2">
          <Button
            size="sm"
            onClick={() => {
              const d = { ...f };
              if (courseId) (d as any).course_id = courseId;
              handleFormSave(d);
            }}
            disabled={saving}
          >
            {saving ? 'Saving...' : initial ? 'Update' : 'Create'}
          </Button>
          <Button variant="outline" size="sm" onClick={closeForm}>
            Cancel
          </Button>
        </div>
      </div>
    );
  };

  const LessonForm = ({ initial, moduleId }: { initial?: any; moduleId?: string }) => {
    const [f, setF] = useState({
      id: initial?.id || '',
      title: initial?.title || '',
      type: initial?.type || 'theory',
      content: initial?.content || '',
      order: initial?.order ?? 1,
      language: initial?.language || '',
      starter_code: initial?.starter_code || '',
      question_id: initial?.question_id || '',
    });
    const set = (k: string, v: any) => setF((p) => ({ ...p, [k]: v }));

    return (
      <div className="space-y-3 p-4 bg-muted/20 rounded-lg border border-border/50 ml-16 mt-2">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className="text-xs text-muted-foreground block mb-1">ID *</label>
            <input
              className="w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none font-mono"
              value={f.id}
              onChange={(e) => set('id', e.target.value)}
              disabled={!!initial}
              placeholder="hello-world"
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground block mb-1">Order</label>
            <input
              type="number"
              className="w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none"
              value={f.order}
              onChange={(e) => set('order', Number(e.target.value))}
            />
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
            className="w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none"
            value={f.title}
            onChange={(e) => set('title', e.target.value)}
            placeholder="Hello, World!"
          />
        </div>
        {f.type === 'exercise' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-muted-foreground block mb-1">Starter Code</label>
              <textarea
                className="w-full h-24 text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none resize-y font-mono"
                value={f.starter_code}
                onChange={(e) => set('starter_code', e.target.value)}
                placeholder="def solution():&#10;    pass"
              />
            </div>
            <div>
              <label className="text-xs text-muted-foreground block mb-1">
                Question ID (linked)
              </label>
              <input
                className="w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none font-mono"
                value={f.question_id}
                onChange={(e) => set('question_id', e.target.value)}
                placeholder="optional-linked-question-id"
              />
            </div>
          </div>
        )}
        <div>
          <label className="text-xs text-muted-foreground block mb-1">
            Content (Markdown)
            {f.type === 'exercise' && !f.question_id && (
              <span className="ml-2 text-yellow-400">
                No question linked — you can create one below
              </span>
            )}
          </label>
          <textarea
            className="w-full h-40 text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none resize-y font-mono"
            value={f.content}
            onChange={(e) => set('content', e.target.value)}
            placeholder="# Lesson title&#10;&#10;Content here..."
          />
        </div>
        {f.type === 'exercise' && (
          <div>
            <label className="text-xs text-muted-foreground block mb-1">Language</label>
            <input
              className="w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none"
              value={f.language}
              onChange={(e) => set('language', e.target.value)}
              placeholder="python"
            />
          </div>
        )}
        <div className="flex items-center justify-between">
          <div className="flex gap-2">
            <Button size="sm" onClick={() => handleFormSave(f)} disabled={saving}>
              {saving ? 'Saving...' : initial ? 'Update' : 'Create'}
            </Button>
            <Button variant="outline" size="sm" onClick={closeForm}>
              Cancel
            </Button>
          </div>
          {f.type === 'exercise' && !initial && (
            <Button variant="outline" size="sm" onClick={() => setQuestionFormForLesson(f.id)}>
              <Code2 className="h-3.5 w-3.5 mr-1" /> Create Question
            </Button>
          )}
        </div>
        {questionFormForLesson === f.id && (
          <div className="mt-4 p-4 bg-muted/20 rounded-lg border border-primary/20">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium">
                New Question for lesson &quot;{f.id}&quot;
              </span>
              <button
                onClick={() => setQuestionFormForLesson(null)}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <QuestionForm
              token={token || ''}
              onSaved={() => {
                setQuestionFormForLesson(null);
              }}
              onCancel={() => setQuestionFormForLesson(null)}
            />
          </div>
        )}
      </div>
    );
  };

  // ── Render ───────────────────────────────────────────

  if (loading)
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Curriculum</h1>
          <p className="text-muted-foreground text-sm mt-1">
            {tree.courses.length} courses, {tree.modules.length} modules, {tree.lessons.length}{' '}
            lessons
          </p>
        </div>
        <Button size="sm" onClick={() => openForm('course')}>
          <Plus className="h-4 w-4 mr-1" /> Add Course
        </Button>
      </div>

      {/* Inline course creation form */}
      {formEntity?.type === 'course' && !formEntity.initial && <CourseForm />}

      {tree.courses.length === 0 && !formEntity ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No courses found. Click &ldquo;Add Course&rdquo; to create one.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {tree.courses.map((course) => (
            <Card key={course.id}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                      <Database className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <CardTitle className="text-base">{course.title}</CardTitle>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {course.language} &middot; order {course.order}
                        {course.description && <span> &middot; {course.description}</span>}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => openForm('course', course)}
                      className="text-xs p-1.5 rounded hover:bg-muted transition-colors"
                      title="Edit course"
                    >
                      <Edit3 className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => del('course', course.id)}
                      className="text-xs p-1.5 rounded hover:bg-red-500/10 text-red-400 transition-colors"
                      title="Delete course"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => toggle(course.id)}
                      className="text-xs p-1.5 rounded hover:bg-muted transition-colors"
                    >
                      {expanded[course.id] ? (
                        <ChevronDown className="h-4 w-4" />
                      ) : (
                        <ChevronRight className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>
              </CardHeader>

              {/* Inline course edit form */}
              {formEntity?.type === 'course' && formEntity.initial?.id === course.id && (
                <CardContent className="pt-0 pb-3">
                  <CourseForm initial={formEntity.initial} />
                </CardContent>
              )}

              {expanded[course.id] && (
                <CardContent className="pt-0 space-y-3">
                  {/* Add Module button */}
                  <div className="ml-6">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => openForm('module', undefined, course.id)}
                    >
                      <Plus className="h-3.5 w-3.5 mr-1" /> Add Module
                    </Button>
                  </div>

                  {/* Inline module creation form */}
                  {formEntity?.type === 'module' &&
                    formEntity.parentId === course.id &&
                    !formEntity.initial && (
                      <div className="ml-6">
                        <ModuleForm courseId={course.id} />
                      </div>
                    )}

                  {tree.modules.filter((m) => m.course_id === course.id).length === 0 ? (
                    <p className="text-xs text-muted-foreground pl-13 ml-6">No modules</p>
                  ) : (
                    tree.modules
                      .filter((m) => m.course_id === course.id)
                      .sort((a, b) => (a.order || 0) - (b.order || 0))
                      .map((mod) => (
                        <div key={mod.id} className="ml-6 pl-4 border-l-2 border-border/50">
                          <div className="flex items-center justify-between py-1">
                            <div className="flex items-center gap-2">
                              <BookOpen className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm font-medium">{mod.title}</span>
                              {mod.description && (
                                <span className="text-xs text-muted-foreground hidden sm:inline">
                                  &middot; {mod.description}
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-1">
                              <button
                                onClick={() => openForm('module', mod)}
                                className="text-xs p-1 rounded hover:bg-muted transition-colors"
                                title="Edit module"
                              >
                                <Edit3 className="h-3 w-3" />
                              </button>
                              <button
                                onClick={() => del('module', mod.id)}
                                className="text-xs p-1 rounded hover:bg-red-500/10 text-red-400 transition-colors"
                                title="Delete module"
                              >
                                <Trash2 className="h-3 w-3" />
                              </button>
                              <button
                                onClick={() => toggle(mod.id)}
                                className="text-xs p-1 rounded hover:bg-muted transition-colors"
                              >
                                {expanded[mod.id] ? (
                                  <ChevronDown className="h-3.5 w-3.5" />
                                ) : (
                                  <ChevronRight className="h-3.5 w-3.5" />
                                )}
                              </button>
                            </div>
                          </div>

                          {/* Inline module edit form */}
                          {formEntity?.type === 'module' && formEntity.initial?.id === mod.id && (
                            <div className="mt-2">
                              <ModuleForm initial={formEntity.initial} />
                            </div>
                          )}

                          {expanded[mod.id] && (
                            <div className="ml-6 mt-2 space-y-1">
                              {/* Add Lesson button */}
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => openForm('lesson', undefined, mod.id)}
                              >
                                <Plus className="h-3 h-3.5 w-3.5 mr-1" /> Add Lesson
                              </Button>

                              {/* Inline lesson creation form */}
                              {formEntity?.type === 'lesson' &&
                                formEntity.parentId === mod.id &&
                                !formEntity.initial && (
                                  <div className="mt-2">
                                    <LessonForm moduleId={mod.id} />
                                  </div>
                                )}

                              {tree.lessons.filter((l) => l.module_id === mod.id).length === 0 ? (
                                <p className="text-xs text-muted-foreground py-1">No lessons</p>
                              ) : (
                                tree.lessons
                                  .filter((l) => l.module_id === mod.id)
                                  .sort((a, b) => (a.order || 0) - (b.order || 0))
                                  .map((les) => (
                                    <div key={les.id}>
                                      <div className="flex items-center justify-between py-1">
                                        <div className="flex items-center gap-2">
                                          <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                                          <span className="text-sm">{les.title}</span>
                                          {les.type && (
                                            <span
                                              className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                                                les.type === 'exercise'
                                                  ? 'bg-blue-500/20 text-blue-400'
                                                  : 'bg-muted/50 text-muted-foreground'
                                              }`}
                                            >
                                              {les.type}
                                            </span>
                                          )}
                                        </div>
                                        <div className="flex items-center gap-1">
                                          <button
                                            onClick={() => openForm('lesson', les)}
                                            className="text-xs p-1 rounded hover:bg-muted transition-colors"
                                            title="Edit lesson"
                                          >
                                            <Edit3 className="h-3 w-3" />
                                          </button>
                                          <button
                                            onClick={() => del('lesson', les.id)}
                                            className="text-xs p-1 rounded hover:bg-red-500/10 text-red-400 transition-colors"
                                            title="Delete lesson"
                                          >
                                            <Trash2 className="h-3 w-3" />
                                          </button>
                                        </div>
                                      </div>

                                      {/* Inline lesson edit form */}
                                      {formEntity?.type === 'lesson' &&
                                        formEntity.initial?.id === les.id && (
                                          <div className="mt-2">
                                            <LessonForm initial={formEntity.initial} />
                                          </div>
                                        )}
                                    </div>
                                  ))
                              )}
                            </div>
                          )}
                        </div>
                      ))
                  )}
                </CardContent>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
