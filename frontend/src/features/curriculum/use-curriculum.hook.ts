"use client";

import { useState, useEffect, useCallback } from "react";
import { FetchClient, getErrorDisplayMessage } from "@/lib/fetch-client";
import {
  CourseLearnSummary,
  CourseDetail,
  LessonSummary,
} from "@/types";

const api = new FetchClient();

// Dedupe concurrent mounts (Learn page + StrictMode double-effects fired
// two identical course-list requests on every load): one module-shared
// in-flight promise, cleared on settle. Never blocks — losers await it.
let coursesInFlight: Promise<CourseLearnSummary[]> | null = null;

function fetchLearnSummaries(): Promise<CourseLearnSummary[]> {
  if (!coursesInFlight) {
    coursesInFlight = fetchWithRetry(
      () =>
        api.get<{ courses: CourseLearnSummary[] }>("/api/courses/?view=learn", {
          timeout: 15000,
        }),
      2,
    ).then(
      (data) => {
        coursesInFlight = null;
        return data.courses;
      },
      (err) => {
        coursesInFlight = null;
        throw err;
      },
    );
  }
  return coursesInFlight;
}

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
  const [courses, setCourses] = useState<CourseLearnSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadCourses = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      setCourses(await fetchLearnSummaries());
    } catch (err) {
      setError(getErrorDisplayMessage(err) || "Failed to load courses");
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
      setError(getErrorDisplayMessage(err) || "Failed to load course");
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
      setError(getErrorDisplayMessage(err) || "Failed to load lesson");
    } finally {
      setIsLoading(false);
    }
  }, [lessonId]);

  useEffect(() => {
    loadLesson();
  }, [loadLesson]);

  return { lesson, isLoading, error, refetch: loadLesson };
}
