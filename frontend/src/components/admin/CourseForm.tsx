"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  validateCourseForm,
  validateIdUnique,
  FieldErrors,
} from "@/lib/validation";

interface CourseFormProps {
  initial?: {
    id: string;
    title: string;
    description?: string;
    language?: string;
    icon?: string;
    order?: number;
  };
  saving: boolean;
  onSave: (data: Record<string, any>) => void;
  onCancel: () => void;
}

export default function CourseForm({
  initial,
  saving,
  onSave,
  onCancel,
}: CourseFormProps) {
  const isEdit = !!initial;
  const [f, setF] = useState({
    id: initial?.id || "",
    title: initial?.title || "",
    description: initial?.description || "",
    language: initial?.language || "",
    icon: initial?.icon || "code",
    order: initial?.order ?? 1,
  });
  const [errors, setErrors] = useState<FieldErrors>({});
  const [idChecking, setIdChecking] = useState(false);

  const set = (k: string, v: any) => {
    setF((p) => ({ ...p, [k]: v }));
    // Clear error on edit
    setErrors((p) => {
      const next = { ...p };
      delete next[k];
      return next;
    });
  };

  // Validate on change
  useEffect(() => {
    const syncErrors = validateCourseForm({
      id: f.id,
      title: f.title,
      order: f.order,
    });
    setErrors(syncErrors);
  }, [f.id, f.title, f.order]);

  const handleSave = async () => {
    // Sync validation
    const syncErrors = validateCourseForm(f);
    if (Object.keys(syncErrors).length > 0) {
      setErrors(syncErrors);
      return;
    }

    // Async ID uniqueness check
    if (!isEdit) {
      setIdChecking(true);
      const idErr = await validateIdUnique("course", f.id, isEdit);
      setIdChecking(false);
      if (idErr) {
        setErrors({ id: idErr });
        return;
      }
    }

    onSave(f);
  };

  const inputClass = (field: string) =>
    `w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border outline-none transition-all duration-200 ${
      errors[field]
        ? "border-destructive ring-1 ring-destructive/20"
        : "border-border"
    } ${field === "id" ? "font-mono" : ""}`;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="text-xs text-muted-foreground block mb-1">
            ID *
          </label>
          <input
            className={inputClass("id")}
            value={f.id}
            onChange={(e) => set("id", e.target.value)}
            disabled={isEdit}
            placeholder="python-fundamentals"
          />
          {errors.id && (
            <p className="text-xs text-destructive mt-1">{errors.id}</p>
          )}
        </div>
        <div>
          <label className="text-xs text-muted-foreground block mb-1">
            Title *
          </label>
          <input
            className={inputClass("title")}
            value={f.title}
            onChange={(e) => set("title", e.target.value)}
            placeholder="Python Fundamentals"
          />
          {errors.title && (
            <p className="text-xs text-destructive mt-1">{errors.title}</p>
          )}
        </div>
        <div>
          <label className="text-xs text-muted-foreground block mb-1">
            Language
          </label>
          <input
            className={inputClass("language")}
            value={f.language}
            onChange={(e) => set("language", e.target.value)}
            placeholder="python"
          />
        </div>
        <div>
          <label className="text-xs text-muted-foreground block mb-1">
            Order
          </label>
          <input
            type="number"
            className={inputClass("order")}
            value={f.order}
            onChange={(e) => set("order", Number(e.target.value))}
          />
          {errors.order && (
            <p className="text-xs text-destructive mt-1">{errors.order}</p>
          )}
        </div>
      </div>
      <div>
        <label className="text-xs text-muted-foreground block mb-1">
          Description
        </label>
        <textarea
          className="w-full h-20 text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none resize-y"
          value={f.description}
          onChange={(e) => set("description", e.target.value)}
        />
      </div>
      <div className="flex gap-2 pt-2">
        <Button
          size="sm"
          onClick={handleSave}
          disabled={saving || idChecking || Object.keys(errors).length > 0}
        >
          {saving
            ? "Saving..."
            : idChecking
              ? "Checking..."
              : initial
                ? "Update"
                : "Create"}
        </Button>
        <Button variant="outline" size="sm" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </div>
  );
}
