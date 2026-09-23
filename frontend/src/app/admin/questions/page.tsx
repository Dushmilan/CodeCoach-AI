"use client";
export const dynamic = "force-dynamic";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/providers";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/Skeleton";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import QuestionForm from "@/components/admin/QuestionForm";
import { Code2, Trash2 } from "lucide-react";

interface QBrief {
  id: string;
  title: string;
  difficulty: string;
  category: string;
  solution?: string | null;
}

type View = "list" | "create" | "import";

const DIFF_BADGE: Record<string, string> = {
  easy: "bg-success/10 text-success ring-success/20",
  medium: "bg-warning/10 text-warning ring-warning/20",
  hard: "bg-destructive/10 text-destructive ring-destructive/20",
};

export default function QuestionsPage() {
  const { token } = useAuth();
  const [questions, setQuestions] = useState<QBrief[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({
    difficulty: "",
    category: "",
    page: 1,
    per_page: 20,
  });
  const [view, setView] = useState<View>("list");
  const [importJson, setImportJson] = useState("");
  const [importResult, setImportResult] = useState<{
    total?: number;
    successful?: number;
    failed?: number;
    errors?: { message: string }[];
  } | null>(null);

  const fetchQuestions = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: String(filter.page),
        per_page: String(filter.per_page),
      });
      if (filter.difficulty) params.set("difficulty", filter.difficulty);
      if (filter.category) params.set("category", filter.category);
      const res = await fetch(`/api/admin/questions?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed");
      const data = (await res.json()) as { questions?: QBrief[]; total?: number };
      setQuestions(data.questions || []);
      setTotal(data.total || 0);
    } catch {
      /* */
    } finally {
      setLoading(false);
    }
  }, [filter, token]);

  useEffect(() => {
    fetchQuestions();
  }, [fetchQuestions]);

  const deleteQ = async (id: string) => {
    if (!confirm("Delete this question?")) return;
    const res = await fetch(`/api/admin/questions/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) fetchQuestions();
  };

  const doImport = async () => {
    try {
      const data = JSON.parse(importJson);
      const res = await fetch("/api/admin/questions/import", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          questions: Array.isArray(data) ? data : [data],
        }),
      });
      const result = (await res.json()) as {
        total?: number;
        successful?: number;
        failed?: number;
        errors?: { message: string }[];
      };
      setImportResult(result);
      if (res.ok) fetchQuestions();
    } catch {
      setImportResult({
        total: 0,
        successful: 0,
        failed: 1,
        errors: [{ message: "Invalid JSON" }],
      });
    }
  };

  const diffBadge = (d: string) => (
    <span
      className={`text-xs font-medium px-2 py-0.5 rounded-full ring-1 ring-inset ${DIFF_BADGE[d] ?? "bg-muted text-muted-foreground ring-border"}`}
    >
      {d}
    </span>
  );

  return (
    <Tabs
      value={view}
      onValueChange={(v) => setView(v as View)}
      className="space-y-6"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Questions</h1>
          <p className="text-muted-foreground text-sm mt-1">{total} total</p>
        </div>
        <TabsList>
          <TabsTrigger value="list">All questions</TabsTrigger>
          <TabsTrigger value="create">Add question</TabsTrigger>
          <TabsTrigger value="import">Import JSON</TabsTrigger>
        </TabsList>
      </div>

      {/* List */}
      <TabsContent value="list" className="space-y-4">
        <section aria-label="Question filters">
          <div className="flex flex-wrap gap-3">
            <select
              aria-label="Difficulty filter"
              value={filter.difficulty}
              onChange={(e) =>
                setFilter((f) => ({ ...f, difficulty: e.target.value, page: 1 }))
              }
              className="text-sm bg-card rounded-full px-4 py-2 border border-border outline-none"
            >
              <option value="">All Difficulties</option>
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
            <input
              aria-label="Category filter"
              className="text-sm bg-card rounded-full px-4 py-2 border border-border outline-none w-44 placeholder:text-muted-foreground"
              placeholder="Category filter..."
              value={filter.category}
              onChange={(e) =>
                setFilter((f) => ({ ...f, category: e.target.value, page: 1 }))
              }
            />
          </div>
        </section>

        <section aria-label="Question list">
          {loading ? (
            <div className="space-y-3" aria-busy="true">
              {[0, 1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-12 rounded-2xl" />
              ))}
            </div>
          ) : questions.length === 0 ? (
            <Card className="rounded-2xl">
              <CardContent className="py-12 text-center text-muted-foreground">
                No questions found.
              </CardContent>
            </Card>
          ) : (
            <Card className="rounded-2xl">
              <CardContent className="pt-4">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border text-muted-foreground text-xs uppercase">
                        <th className="text-left pb-3 font-medium">Title</th>
                        <th className="text-left pb-3 font-medium">
                          Difficulty
                        </th>
                        <th className="text-left pb-3 font-medium">Category</th>
                        <th className="text-left pb-3 font-medium">
                          Solution
                        </th>
                        <th className="text-right pb-3 font-medium">
                          Actions
                        </th>
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
                          <td className="py-3 text-muted-foreground text-xs">
                            {q.category}
                          </td>
                          <td className="py-3">
                            {q.solution ? (
                              <span className="text-xs text-success">
                                Has solution
                              </span>
                            ) : (
                              <span className="text-xs text-muted-foreground">
                                None
                              </span>
                            )}
                          </td>
                          <td className="py-3 text-right">
                            <button
                              onClick={() => deleteQ(q.id)}
                              className="text-xs p-1.5 rounded-full hover:bg-destructive/10 text-destructive transition-colors"
                              title="Delete"
                            >
                              <Trash2
                                className="h-3.5 w-3.5"
                                aria-hidden="true"
                              />
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
                        onClick={() =>
                          setFilter((f) => ({ ...f, page: f.page - 1 }))
                        }
                      >
                        Previous
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={
                          filter.page >= Math.ceil(total / filter.per_page)
                        }
                        onClick={() =>
                          setFilter((f) => ({ ...f, page: f.page + 1 }))
                        }
                      >
                        Next
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </section>
      </TabsContent>

      {/* Create */}
      <TabsContent value="create">
        <Card className="rounded-2xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Code2 className="h-4 w-4 text-brand" aria-hidden="true" />
              Create New Question
            </CardTitle>
          </CardHeader>
          <CardContent>
            <QuestionForm
              onSaved={() => {
                setView("list");
                fetchQuestions();
              }}
              onCancel={() => setView("list")}
            />
          </CardContent>
        </Card>
      </TabsContent>

      {/* Import */}
      <TabsContent value="import">
        <Card className="rounded-2xl">
          <CardHeader>
            <CardTitle className="text-base">
              Import Questions (JSON)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <textarea
              className="w-full h-32 bg-muted/30 rounded-2xl p-3 text-sm font-mono border border-border outline-none resize-none placeholder:text-muted-foreground"
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
                  setView("list");
                  setImportJson("");
                  setImportResult(null);
                }}
              >
                Cancel
              </Button>
            </div>
            {importResult && (
              <div
                className={`text-sm p-3 rounded-2xl ${
                  (importResult.failed ?? 0) > 0
                    ? "bg-destructive/10 text-destructive"
                    : "bg-success/10 text-success"
                }`}
              >
                {importResult.successful} imported,{" "}
                {importResult.failed} failed
                {importResult.errors?.map((e, i) => (
                  <div key={i} className="text-xs mt-1">
                    {e.message || JSON.stringify(e)}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  );
}
