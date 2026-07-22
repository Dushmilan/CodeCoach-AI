"use client";
export const dynamic = "force-dynamic";

import { useEffect, useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { showToast } from "@/components/ui/Toast";
import { FetchClient } from "@/lib/fetch-client";
import CourseForm from "@/components/admin/CourseForm";
import ModuleForm from "@/components/admin/ModuleForm";
import LessonForm from "@/components/admin/LessonForm";
import EntityDrawer from "@/components/admin/EntityDrawer";
import {
  Database,
  BookOpen,
  FileText,
  Trash2,
  Plus,
  Edit3,
  ChevronRight,
  ChevronDown,
} from "lucide-react";

const api = new FetchClient();

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
  lessons?: string[];
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
type EntityType = "course" | "module" | "lesson";

export default function CurriculumPage() {
  const [tree, setTree] = useState<CourseTree>({
    courses: [],
    modules: [],
    lessons: [],
  });
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  // Drawer state
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerEntity, setDrawerEntity] = useState<{
    type: EntityType;
    initial?: any;
    initialQuestion?: any;
    parentId?: string;
  } | null>(null);
  const [saving, setSaving] = useState(false);

  const fetchTree = useCallback(async () => {
    try {
      const data = await api.get<CourseTree>("/api/admin/courses/tree");
      setTree(data);
    } catch {
      showToast("Failed to load curriculum", "error");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTree();
  }, [fetchTree]);

  const toggle = (id: string) => setExpanded((e) => ({ ...e, [id]: !e[id] }));

  const openDrawer = async (
    type: EntityType,
    initial?: any,
    parentId?: string,
  ) => {
    let initialQuestion = undefined;
    if (type === "lesson" && initial?.question_id) {
      try {
        initialQuestion = await api.get(
          `/api/admin/questions/${initial.question_id}`,
        );
      } catch {
        // Question might not exist yet — that's fine
      }
    }
    setDrawerEntity({ type, initial, initialQuestion, parentId });
    setDrawerOpen(true);
  };

  const closeDrawer = () => {
    setDrawerOpen(false);
    setDrawerEntity(null);
  };

  const del = async (type: string, id: string) => {
    if (!confirm(`Delete this ${type}?`)) return;
    const endpoints: Record<string, string> = {
      course: `/api/admin/courses/${id}`,
      module: `/api/admin/modules/${id}`,
      lesson: `/api/admin/lessons/${id}`,
    };
    try {
      await api.delete(endpoints[type]);
      showToast(`${type} deleted`, "success");
      fetchTree();
    } catch {
      showToast(`Failed to delete ${type}`, "error");
    }
  };

  const handleFormSave = async (formData: Record<string, any>) => {
    setSaving(true);
    try {
      const { type, initial, parentId } = drawerEntity || {};
      const isEdit = !!initial;

      let url = "";
      let method = "POST";
      let body = { ...formData };

      if (type === "course") {
        url = isEdit
          ? `/api/admin/courses/${initial.id}`
          : "/api/admin/courses";
        method = isEdit ? "PUT" : "POST";
      } else if (type === "module") {
        url = isEdit
          ? `/api/admin/modules/${initial.id}`
          : "/api/admin/modules";
        method = isEdit ? "PUT" : "POST";
        if (!isEdit) body.course_id = parentId;
      } else if (type === "lesson") {
        url = isEdit
          ? `/api/admin/lessons/${initial.id}`
          : "/api/admin/lessons";
        method = isEdit ? "PUT" : "POST";
        if (!isEdit) {
          body.course_id =
            tree.modules.find((m) => m.id === parentId)?.course_id || "";
          body.module_id = parentId || "";
        }
      }

      if (method === "PUT") {
        await api.put(url, body);
      } else {
        await api.post(url, body);
      }

      showToast(`${type} saved`, "success");
      closeDrawer();
      fetchTree();
    } catch (e: any) {
      showToast(e.message || "Failed to save", "error");
    } finally {
      setSaving(false);
    }
  };

  // ── Render ───────────────────────────────────────────

  if (loading)
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );

  const drawerTitle = drawerEntity
    ? drawerEntity.initial
      ? `Edit ${drawerEntity.type}`
      : `New ${drawerEntity.type}`
    : "";

  const drawerSubtitle = drawerEntity?.initial?.title || undefined;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Curriculum</h1>
          <p className="text-muted-foreground text-sm mt-1">
            {tree.courses.length} courses, {tree.modules.length} modules,{" "}
            {tree.lessons.length} lessons
          </p>
        </div>
        <Button size="sm" onClick={() => openDrawer("course")}>
          <Plus className="h-4 w-4 mr-1" /> Add Course
        </Button>
      </div>

      {tree.courses.length === 0 && !drawerOpen ? (
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
                      <CardTitle className="text-base">
                        {course.title}
                      </CardTitle>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {course.language} &middot; order {course.order}
                        {course.description && (
                          <span> &middot; {course.description}</span>
                        )}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => openDrawer("course", course)}
                      className="text-xs p-1.5 rounded hover:bg-muted transition-colors"
                      title="Edit course"
                    >
                      <Edit3 className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => del("course", course.id)}
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

              {expanded[course.id] && (
                <CardContent className="pt-0 space-y-3">
                  <div className="ml-6">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => openDrawer("module", undefined, course.id)}
                    >
                      <Plus className="h-3.5 w-3.5 mr-1" /> Add Module
                    </Button>
                  </div>

                  {tree.modules.filter((m) => m.course_id === course.id)
                    .length === 0 ? (
                    <p className="text-xs text-muted-foreground pl-13 ml-6">
                      No modules
                    </p>
                  ) : (
                    tree.modules
                      .filter((m) => m.course_id === course.id)
                      .sort((a, b) => (a.order || 0) - (b.order || 0))
                      .map((mod) => (
                        <div
                          key={mod.id}
                          className="ml-6 pl-4 border-l-2 border-border/50"
                        >
                          <div className="flex items-center justify-between py-1">
                            <div className="flex items-center gap-2">
                              <BookOpen className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm font-medium">
                                {mod.title}
                              </span>
                              {mod.description && (
                                <span className="text-xs text-muted-foreground hidden sm:inline">
                                  &middot; {mod.description}
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-1">
                              <button
                                onClick={() => openDrawer("module", mod)}
                                className="text-xs p-1 rounded hover:bg-muted transition-colors"
                                title="Edit module"
                              >
                                <Edit3 className="h-3 w-3" />
                              </button>
                              <button
                                onClick={() => del("module", mod.id)}
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

                          {expanded[mod.id] && (
                            <div className="ml-6 mt-2 space-y-1">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() =>
                                  openDrawer("lesson", undefined, mod.id)
                                }
                              >
                                <Plus className="h-3 h-3.5 w-3.5 mr-1" /> Add
                                Lesson
                              </Button>

                              {tree.lessons.filter(
                                (l) => l.module_id === mod.id,
                              ).length === 0 ? (
                                <p className="text-xs text-muted-foreground py-1">
                                  No lessons
                                </p>
                              ) : (
                                tree.lessons
                                  .filter((l) => l.module_id === mod.id)
                                  .sort(
                                    (a, b) => (a.order || 0) - (b.order || 0),
                                  )
                                  .map((les) => (
                                    <div key={les.id}>
                                      <div className="flex items-center justify-between py-1">
                                        <div className="flex items-center gap-2">
                                          <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                                          <span className="text-sm">
                                            {les.title}
                                          </span>
                                          {les.type && (
                                            <span
                                              className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                                                les.type === "exercise"
                                                  ? "bg-blue-500/20 text-blue-400"
                                                  : "bg-muted/50 text-muted-foreground"
                                              }`}
                                            >
                                              {les.type}
                                            </span>
                                          )}
                                        </div>
                                        <div className="flex items-center gap-1">
                                          <button
                                            onClick={() =>
                                              openDrawer("lesson", les)
                                            }
                                            className="text-xs p-1 rounded hover:bg-muted transition-colors"
                                            title="Edit lesson"
                                          >
                                            <Edit3 className="h-3 w-3" />
                                          </button>
                                          <button
                                            onClick={() =>
                                              del("lesson", les.id)
                                            }
                                            className="text-xs p-1 rounded hover:bg-red-500/10 text-red-400 transition-colors"
                                            title="Delete lesson"
                                          >
                                            <Trash2 className="h-3 w-3" />
                                          </button>
                                        </div>
                                      </div>
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

      {/* Side Panel Drawer */}
      <EntityDrawer
        open={drawerOpen}
        onClose={closeDrawer}
        title={drawerTitle}
        subtitle={drawerSubtitle}
        wide={drawerEntity?.type === "lesson"}
      >
        {drawerEntity?.type === "course" && (
          <CourseForm
            initial={drawerEntity.initial}
            saving={saving}
            onSave={handleFormSave}
            onCancel={closeDrawer}
          />
        )}
        {drawerEntity?.type === "module" && (
          <ModuleForm
            initial={drawerEntity.initial}
            courseId={drawerEntity.parentId}
            saving={saving}
            onSave={handleFormSave}
            onCancel={closeDrawer}
          />
        )}
        {drawerEntity?.type === "lesson" && (
          <LessonForm
            initial={drawerEntity.initial}
            initialQuestion={drawerEntity.initialQuestion}
            moduleId={drawerEntity.parentId}
            saving={saving}
            onSave={handleFormSave}
            onCancel={closeDrawer}
          />
        )}
      </EntityDrawer>
    </div>
  );
}
