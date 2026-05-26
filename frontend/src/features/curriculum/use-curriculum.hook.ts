'use client';

import { useState, useEffect, useCallback } from 'react';
import { FetchClient } from '@/lib/fetch-client';
import { CourseSummary, CourseDetail, LessonSummary } from '@/types';

const api = new FetchClient();

export function useCurriculum() {
  const [courses, setCourses] = useState<CourseSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadCourses = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.get<{ courses: CourseSummary[] }>('/api/courses/');
      setCourses(data.courses);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load courses');
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
    if (!courseId) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.get<CourseDetail>(`/api/courses/${courseId}`);
      setCourse(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load course');
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
    if (!lessonId) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.get<LessonSummary>(`/api/courses/lessons/${lessonId}`);
      setLesson(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load lesson');
    } finally {
      setIsLoading(false);
    }
  }, [lessonId]);

  useEffect(() => {
    loadLesson();
  }, [loadLesson]);

  return { lesson, isLoading, error, refetch: loadLesson };
}
