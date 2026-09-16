import demo from "@/data/instructor-demo.json";
import { FetchClient, HttpError } from "@/lib/fetch-client";

export type InstructorRole = "professor" | "ta" | "admin" | "super_admin" | "user";

/** Page contract for a classroom (camelCase). Live payloads map onto this. */
export interface Classroom {
  id: string;
  name: string;
  courseId: string;
  ownerId: string;
  inviteCode: string;
  term: string;
  schedule: string;
  totalLessons?: number;
}

/** Page contract for a roster row (camelCase). */
export interface ClassStudent {
  userId: string;
  username: string;
  name: string;
  enrolledAt?: string;
  completedLessons: number;
  completionPct: number;
  solved: number;
  attempted: number;
  lastActive: string;
}

/** Page contract for class aggregates (camelCase). */
export interface ClassAnalytics {
  totalStudents: number;
  avgCompletion: number;
  avgSolved: number;
  students: ClassStudent[];
  atRisk: ClassStudent[];
  skillMastery: Array<{
    classroomId: string;
    slug: string;
    label: string;
    avgMastery: number;
  }>;
  signals: Array<{
    classroomId: string;
    userId: string;
    skill: string;
    title: string;
    detail: string;
    severity: string;
  }>;
}

/** Live shapes from GET /api/instructor/classrooms[/{id}] (Issue #159). */
interface LiveClassroomOut {
  id: string;
  course_id: string;
  owner_id?: string | null;
  name: string;
  invite_code: string;
  term?: string | null;
  schedule?: string | null;
}

interface LiveStudentSummary {
  user_id: string;
  username?: string | null;
  completed_lessons: number;
  completion_pct: number;
  attempted: number;
  solved: number;
}

interface LiveClassAnalytics {
  total_students: number;
  avg_completion: number;
  avg_solved: number;
  students: LiveStudentSummary[];
}

interface LiveClassroomDetail {
  classroom: LiveClassroomOut;
  analytics: LiveClassAnalytics;
}

interface DemoDB {
  professors: Array<{
    id: string;
    username: string;
    name: string;
    email: string;
    role: string;
    department: string;
    coursesCreated: string[];
  }>;
  demonstrators: Array<{
    id: string;
    username: string;
    name: string;
    email: string;
    role: string;
    assignedClassrooms: string[];
  }>;
  courses: Array<{
    id: string;
    title: string;
    description: string;
    language: string;
    icon: string;
    order: number;
    createdBy: string;
    modules: number;
    lessons: number;
    validation: { pipeline: string; animationGate: string; steps: number };
  }>;
  classrooms: Array<{
    id: string;
    name: string;
    courseId: string;
    ownerId: string;
    inviteCode: string;
    term: string;
    schedule: string;
    totalLessons: number;
  }>;
  enrollments: Array<{
    classroomId: string;
    userId: string;
    username: string;
    name: string;
    enrolledAt: string;
  }>;
  progress: Array<{
    userId: string;
    classroomId: string;
    completedLessons: number;
    solved: number;
    attempted: number;
    lastActive: string;
  }>;
  skillMastery: Array<{
    classroomId: string;
    slug: string;
    label: string;
    avgMastery: number;
  }>;
  plateauSignals: Array<{
    classroomId: string;
    userId: string;
    skill: string;
    title: string;
    detail: string;
    severity: string;
  }>;
}

const db = demo as unknown as DemoDB;

// Same-origin live API via the Next.js /api/* proxy (see fetch-client).
// Demo JSON below is OFFLINE FALLBACK ONLY — never the primary source.
const api = new FetchClient();

function mapClassroom(room: LiveClassroomOut): Classroom {
  return {
    id: room.id,
    name: room.name,
    courseId: room.course_id,
    ownerId: room.owner_id ?? "",
    inviteCode: room.invite_code,
    term: room.term ?? "",
    schedule: room.schedule ?? "",
  };
}

function mapStudent(s: LiveStudentSummary): ClassStudent {
  // Live rollups carry the display username when known — fall back to the
  // user id so the roster keeps its shape without inventing data.
  const username = s.username || s.user_id;
  return {
    userId: s.user_id,
    username,
    name: username,
    completedLessons: s.completed_lessons,
    completionPct: s.completion_pct,
    solved: s.solved,
    attempted: s.attempted,
    lastActive: "",
  };
}

function atRisk(students: ClassStudent[]): ClassStudent[] {
  return students.filter(
    (s) => s.completionPct < 35 || s.attempted - s.solved >= 10,
  );
}

function mapAnalytics(a: LiveClassAnalytics): ClassAnalytics {
  const students = a.students.map(mapStudent);
  return {
    totalStudents: a.total_students,
    avgCompletion: a.avg_completion,
    avgSolved: a.avg_solved,
    students,
    atRisk: atRisk(students),
    // No live endpoint covers skill mastery / plateau signals yet — live
    // mode reports none rather than mixing demo rows into live views.
    skillMastery: [],
    signals: [],
  };
}

// Demo fallback covers network/offline/5xx ONLY. Auth failures (401/403)
// must never render fixture data as if it were the user's — callers surface
// them via the existing empty/null gates (list renders empty, detail 404s).
function isAuthFailure(e: unknown): boolean {
  return e instanceof HttpError && (e.status === 401 || e.status === 403);
}

function emptyAnalytics(): ClassAnalytics {
  return {
    totalStudents: 0,
    avgCompletion: 0,
    avgSolved: 0,
    students: [],
    atRisk: [],
    skillMastery: [],
    signals: [],
  };
}

async function fetchDetail(classroomId: string): Promise<LiveClassroomDetail> {
  return api.get<LiveClassroomDetail>(
    `/api/instructor/classrooms/${encodeURIComponent(classroomId)}`,
  );
}

function demoClassrooms(ownerId?: string): Classroom[] {
  if (!ownerId) return db.classrooms;
  return db.classrooms.filter((c) => c.ownerId === ownerId);
}

function demoClassroom(id: string): Classroom | null {
  return db.classrooms.find((c) => c.id === id) ?? null;
}

function demoClassroomStudents(classroomId: string): ClassStudent[] {
  const enrolled = db.enrollments.filter((e) => e.classroomId === classroomId);
  const total = demoClassroom(classroomId)?.totalLessons ?? 1;
  return enrolled.map((e) => {
    const p = db.progress.find(
      (r) => r.userId === e.userId && r.classroomId === classroomId,
    );
    const completed = p?.completedLessons ?? 0;
    return {
      ...e,
      completedLessons: completed,
      completionPct: Math.round((completed / total) * 100),
      solved: p?.solved ?? 0,
      attempted: p?.attempted ?? 0,
      lastActive: p?.lastActive ?? e.enrolledAt,
    };
  });
}

function demoClassAnalytics(classroomId: string): ClassAnalytics {
  const students = demoClassroomStudents(classroomId);
  const totalStudents = students.length;
  const avgCompletion = totalStudents
    ? Math.round(
        (students.reduce((s, x) => s + x.completionPct, 0) / totalStudents) * 10,
      ) / 10
    : 0;
  const avgSolved = totalStudents
    ? Math.round(
        (students.reduce((s, x) => s + x.solved, 0) / totalStudents) * 100,
      ) / 100
    : 0;
  const skillMastery = db.skillMastery.filter((m) => m.classroomId === classroomId);
  const signals = db.plateauSignals.filter((s) => s.classroomId === classroomId);
  return { totalStudents, avgCompletion, avgSolved, students, atRisk: atRisk(students), skillMastery, signals };
}

export function getProfessors() {
  return db.professors;
}

export function getCourses() {
  return db.courses;
}

export async function getClassrooms(ownerId?: string): Promise<Classroom[]> {
  try {
    const rooms = await api.get<LiveClassroomOut[]>("/api/instructor/classrooms");
    const mapped = rooms.map(mapClassroom);
    if (!ownerId) return mapped;
    return mapped.filter((c) => c.ownerId === ownerId);
  } catch (e) {
    if (isAuthFailure(e)) return [];
    return demoClassrooms(ownerId);
  }
}

export async function getClassroom(id: string): Promise<Classroom | null> {
  try {
    const detail = await fetchDetail(id);
    return mapClassroom(detail.classroom);
  } catch (e) {
    if (isAuthFailure(e)) return null;
    return demoClassroom(id);
  }
}

export async function getClassroomStudents(
  classroomId: string,
): Promise<ClassStudent[]> {
  return (await getClassAnalytics(classroomId)).students;
}

export async function getClassAnalytics(
  classroomId: string,
): Promise<ClassAnalytics> {
  try {
    const detail = await fetchDetail(classroomId);
    return mapAnalytics(detail.analytics);
  } catch (e) {
    if (isAuthFailure(e)) return emptyAnalytics();
    return demoClassAnalytics(classroomId);
  }
}

export function getStudentDetail(userId: string) {
  const enrollment = db.enrollments.find((e) => e.userId === userId) ?? null;
  const rows = db.progress.filter((p) => p.userId === userId);
  const signals = db.plateauSignals.filter((s) => s.userId === userId);
  return { enrollment, rows, signals };
}

const PROFESSOR_ROLES: InstructorRole[] = ["professor", "admin", "super_admin"];
const INSTRUCTOR_ROLES: InstructorRole[] = ["professor", "ta", "admin", "super_admin"];

export function canManageRoster(role?: string) {
  return PROFESSOR_ROLES.includes(role as InstructorRole);
}

export function canEditCourses(role?: string) {
  return PROFESSOR_ROLES.includes(role as InstructorRole);
}

export function canViewAnalytics(role?: string) {
  return INSTRUCTOR_ROLES.includes(role as InstructorRole);
}
