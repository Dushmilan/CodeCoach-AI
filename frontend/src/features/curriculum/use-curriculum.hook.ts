"use client";

import { useState, useEffect, useCallback } from "react";
import { FetchClient } from "@/lib/fetch-client";
import { CourseSummary, CourseDetail, LessonSummary } from "@/types";

const api = new FetchClient();

async function fetchWithRetry<T>(fn: () => Promise<T>, retries = 2): Promise<T> {
  let lastErr: unknown;
  for (let i = 0; i <= retries; i++) {
    try {
      return await fn();
    } catch (err) {
      lastErr = err;
      const isTimeout =
        err instanceof Error &&
        (err.message.includes("timeout") || (err as unknown as { status?: number }).status === 408);
      if (!isTimeout || i === retries) throw err;
      // backoff 400ms * (i+1)
      await new Promise((r) => setTimeout(r, 400 * (i + 1)));
    }
  }
  throw lastErr;
}

export function useCurriculum() {
  const [courses, setCourses] = useState<CourseSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadCourses = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchWithRetry(
        () => api.get<{ courses: CourseSummary[] }>("/api/courses/", { timeout: 15000 }),
        2,
      );
      setCourses(data.courses);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load courses");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCourses();
  }, [loadCourses]);

  return { courses, isLoading, error, refetch: loadCourses };
}

export function useCourse(courseId: string) {
  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadCourse = useCallback(async () => {
    if (!courseId) {
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchWithRetry(
        () => api.get<CourseDetail>(`/api/courses/${courseId}`, { timeout: 15000 }),
        2,
      );
      setCourse(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load course");
    } finally {
      setIsLoading(false);
    }
  }, [courseId]);

  useEffect(() => {
    loadCourse();
  }, [loadCourse]);

  return { course, isLoading, error, refetch: loadCourse };
}

export function useLesson(lessonId: string) {
  const [lesson, setLesson] = useState<LessonSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadLesson = useCallback(async () => {
    if (!lessonId) {
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchWithRetry(
        () => api.get<LessonSummary>(`/api/courses/lessons/${lessonId}`, { timeout: 15000 }),
        2,
      );
      setLesson(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load lesson");
    } finally {
      setIsLoading(false);
    }
  }, [lessonId]);

  useEffect(() => {
    loadLesson();
  }, [loadLesson]);

  return { lesson, isLoading, error, refetch: loadLesson };
}
