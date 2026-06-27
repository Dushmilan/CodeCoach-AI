'use client';
export const dynamic = 'force-dynamic';

import { useEffect, useState, useCallback } from 'react';
import { useAuth } from '@/providers';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Database, BookOpen, FileText, Trash2, ChevronRight, ChevronDown } from 'lucide-react';

interface Course {
  id: string;
  title: string;
  description?: string;
  language?: string;
}
interface Module {
  id: string;
  course_id: string;
  title: string;
  order?: number;
}
interface Lesson {
  id: string;
  course_id: string;
  module_id: string;
  title: string;
  type?: string;
  order?: number;
}
interface CourseTree {
  courses: Course[];
  modules: Module[];
  lessons: Lesson[];
}

export default function CurriculumPage() {
  const { user } = useAuth();
  const [tree, setTree] = useState<CourseTree>({ courses: [], modules: [], lessons: [] });
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  const fetchTree = useCallback(async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const res = await fetch('/api/admin/courses/tree', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Failed');
      const data = await res.json();
      setTree(data);
    } catch {
      /* */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTree();
  }, [fetchTree]);

  const del = async (type: string, id: string) => {
    if (!confirm(`Delete this ${type}?`)) return;
    const token = localStorage.getItem('auth_token');
    const endpoints: Record<string, string> = {
      course: `/api/admin/courses/${id}`,
      module: `/api/admin/modules/${id}`,
      lesson: `/api/admin/lessons/${id}`,
    };
    const res = await fetch(endpoints[type], {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) fetchTree();
  };

  const toggle = (id: string) => setExpanded((e) => ({ ...e, [id]: !e[id] }));

  if (loading)
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Curriculum</h1>
        <p className="text-muted-foreground text-sm mt-1">
          {tree.courses.length} courses, {tree.modules.length} modules, {tree.lessons.length}{' '}
          lessons
        </p>
      </div>

      {tree.courses.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No courses found.
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
                      {course.description && (
                        <p className="text-xs text-muted-foreground mt-0.5">{course.description}</p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => del('course', course.id)}
                      className="text-xs p-1.5 rounded hover:bg-red-500/10 text-red-400 transition-colors"
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
              {expanded[course.id] && (
                <CardContent className="pt-0 space-y-3">
                  {tree.modules.filter((m) => m.course_id === course.id).length === 0 ? (
                    <p className="text-xs text-muted-foreground pl-13">No modules</p>
                  ) : (
                    tree.modules
                      .filter((m) => m.course_id === course.id)
                      .map((mod) => (
                        <div key={mod.id} className="ml-6 pl-4 border-l-2 border-border/50">
                          <div className="flex items-center justify-between py-1">
                            <div className="flex items-center gap-2">
                              <BookOpen className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm font-medium">{mod.title}</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <button
                                onClick={() => del('module', mod.id)}
                                className="text-xs p-1 rounded hover:bg-red-500/10 text-red-400 transition-colors"
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
                          {expanded[mod.id] && (
                            <div className="ml-6 mt-2 space-y-1">
                              {tree.lessons.filter((l) => l.module_id === mod.id).length === 0 ? (
                                <p className="text-xs text-muted-foreground">No lessons</p>
                              ) : (
                                tree.lessons
                                  .filter((l) => l.module_id === mod.id)
                                  .map((les) => (
                                    <div
                                      key={les.id}
                                      className="flex items-center justify-between py-1"
                                    >
                                      <div className="flex items-center gap-2">
                                        <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                                        <span className="text-sm">{les.title}</span>
                                        {les.type && (
                                          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-muted/50 text-muted-foreground">
                                            {les.type}
                                          </span>
                                        )}
                                      </div>
                                      <button
                                        onClick={() => del('lesson', les.id)}
                                        className="text-xs p-1 rounded hover:bg-red-500/10 text-red-400 transition-colors"
                                      >
                                        <Trash2 className="h-3 w-3" />
                                      </button>
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
