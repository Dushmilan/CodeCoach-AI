"use client";

import { useEffect, useState } from "react";
import { getProfessorCourses, type ProfessorCourse } from "@/features/instructor/demo";
import { FetchClient, getErrorDisplayMessage } from "@/lib/fetch-client";

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
        <h1 className="text-2xl font-bold">Curriculum</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Your owned courses (ANIMATION gate enforced on publish).
        </p>
      </div>
      <form onSubmit={createCourse} className="flex gap-2">
        <input
          aria-label="New course title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="New course title"
          className="border rounded px-3 py-1.5 text-sm"
        />
        <button
          type="submit"
          className="text-xs font-medium px-4 py-2 rounded-full bg-primary text-primary-foreground"
        >
          Create course
        </button>
      </form>
      {error && <p role="alert" className="text-sm text-red-500">{error}</p>}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4" data-testid="prof-curriculum">
        {courses.map((c) => (
          <div key={c.id} className="border rounded p-4">
            {editingId === c.id ? (
              <div className="flex gap-2">
                <input
                  aria-label="Edit course title"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="border rounded px-3 py-1.5 text-sm"
                />
                <button
                  onClick={() => saveEdit(c.id)}
                  className="text-xs px-3 py-1.5 rounded bg-primary text-primary-foreground"
                >
                  Save
                </button>
              </div>
            ) : (
              <div className="flex items-center justify-between">
                <span className="font-medium">{c.title}</span>
                <button
                  onClick={() => {
                    setEditingId(c.id);
                    setEditTitle(c.title);
                  }}
                  className="text-xs underline"
                >
                  Edit
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
