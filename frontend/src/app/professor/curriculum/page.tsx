"use client";

import { useEffect, useState } from "react";
import { getProfessorCourses, type ProfessorCourse } from "@/features/instructor/demo";
import { FetchClient, getErrorDisplayMessage } from "@/lib/fetch-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/Input";

const client = new FetchClient();

export default function ProfessorCurriculumPage() {
  const [courses, setCourses] = useState<ProfessorCourse[]>([]);
  const [title, setTitle] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");

  useEffect(() => {
    getProfessorCourses().then(setCourses).catch(() => setCourses([]));
  }, []);

  async function createCourse(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const created = await client.post<ProfessorCourse>("/api/professor/courses", {
        title,
        description: "",
        language: "python",
      });
      setCourses((prev) => [...prev, created]);
      setTitle("");
    } catch (err) {
      setError(getErrorDisplayMessage(err) || "Create failed");
    }
  }

  async function saveEdit(id: string) {
    setError(null);
    try {
      await client.put(`/api/professor/courses/${id}`, { title: editTitle });
      setCourses((prev) =>
        prev.map((c) => (c.id === id ? { ...c, title: editTitle } : c)),
      );
      setEditingId(null);
    } catch (err) {
      setError(getErrorDisplayMessage(err) || "Update failed");
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Curriculum</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Your owned courses (ANIMATION gate enforced on publish).
        </p>
      </div>

      <section aria-label="Create a course">
        <form
          onSubmit={createCourse}
          className="flex flex-wrap items-center gap-2 rounded-2xl border border-border bg-card p-4"
        >
          <div className="flex-1 min-w-48">
            <Input
              aria-label="New course title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="New course title"
              className="w-full"
            />
          </div>
          <Button type="submit" size="sm">
            Create course
          </Button>
        </form>
      </section>

      {error && (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      )}

      <section aria-label="Owned courses">
        <div
          className="grid grid-cols-1 gap-4 md:grid-cols-2"
          data-testid="prof-curriculum"
        >
          {courses.map((c) => (
            <div
              key={c.id}
              className="rounded-2xl border border-border bg-card p-4"
            >
              {editingId === c.id ? (
                <div className="flex flex-wrap gap-2">
                  <div className="flex-1 min-w-40">
                    <Input
                      aria-label="Edit course title"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      className="w-full"
                    />
                  </div>
                  <Button size="sm" onClick={() => saveEdit(c.id)}>
                    Save
                  </Button>
                </div>
              ) : (
                <div className="flex items-center justify-between gap-3">
                  <span className="font-medium">{c.title}</span>
                  <button
                    onClick={() => {
                      setEditingId(c.id);
                      setEditTitle(c.title);
                    }}
                    className="text-xs font-medium rounded-full px-3 py-1.5 hover:bg-muted transition-colors"
                  >
                    Edit
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
