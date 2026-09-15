"use client";

import { useEffect, useState } from "react";
import {
  getClassroom,
  getClassrooms,
  getClassAnalytics,
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
      const rooms = await getClassrooms();
      if (!live) return;
      setClassrooms(rooms);
      const pairs = await Promise.all(
        rooms.map(async (c) => ({ id: c.id, a: await getClassAnalytics(c.id) })),
      );
      if (!live) return;
      setAnalytics(Object.fromEntries(pairs.map((p) => [p.id, p.a])));
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
      const room = await getClassroom(id);
      if (!live) return;
      setClassroom(room);
      if (room) {
        const a = await getClassAnalytics(id);
        if (live) setAnalytics(a);
      }
    })();
    return () => {
      live = false;
    };
  }, [id]);

  return { classroom, analytics };
}
