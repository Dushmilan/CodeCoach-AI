"use client";

import { useEffect, useState } from "react";
import {
  getClassroomDetail,
  getClassroomsAnalytics,
  type ClassAnalytics,
  type Classroom,
} from "./demo";

/** Classrooms + per-class analytics for list/overview pages (live-first). */
export function useClassrooms() {
  const [classrooms, setClassrooms] = useState<Classroom[] | null>(null);
  const [analytics, setAnalytics] = useState<Record<string, ClassAnalytics>>({});

  useEffect(() => {
    let live = true;
    (async () => {
      const batch = await getClassroomsAnalytics();
      if (!live) return;
      setClassrooms(batch.rooms);
      setAnalytics(batch.analyticsById);
    })();
    return () => {
      live = false;
    };
  }, []);

  const ready =
    classrooms !== null &&
    classrooms.every((c) => analytics[c.id] !== undefined);
  return { classrooms, analytics, ready };
}

/** One classroom + its analytics for detail pages (live-first). */
export function useClassroom(id: string) {
  const [classroom, setClassroom] = useState<Classroom | null | undefined>(
    undefined,
  );
  const [analytics, setAnalytics] = useState<ClassAnalytics | null>(null);

  useEffect(() => {
    let live = true;
    (async () => {
      const detail = await getClassroomDetail(id);
      if (!live) return;
      setClassroom(detail?.classroom ?? null);
      setAnalytics(detail?.analytics ?? null);
    })();
    return () => {
      live = false;
    };
  }, [id]);

  return { classroom, analytics };
}
