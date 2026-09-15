import demo from "@/data/instructor-demo.json";

export type InstructorRole = "professor" | "ta" | "admin" | "super_admin" | "user";

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

export function getProfessors() {
  return db.professors;
}

export function getCourses() {
  return db.courses;
}

export function getClassrooms(ownerId?: string) {
  if (!ownerId) return db.classrooms;
  return db.classrooms.filter((c) => c.ownerId === ownerId);
}

export function getClassroom(id: string) {
  return db.classrooms.find((c) => c.id === id) ?? null;
}

export function getClassroomStudents(classroomId: string) {
  const enrolled = db.enrollments.filter((e) => e.classroomId === classroomId);
  const total = getClassroom(classroomId)?.totalLessons ?? 1;
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

export function getClassAnalytics(classroomId: string) {
  const students = getClassroomStudents(classroomId);
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
  const atRisk = students.filter(
    (s) => s.completionPct < 35 || s.attempted - s.solved >= 10,
  );
  const skillMastery = db.skillMastery.filter((m) => m.classroomId === classroomId);
  const signals = db.plateauSignals.filter((s) => s.classroomId === classroomId);
  return { totalStudents, avgCompletion, avgSolved, students, atRisk, skillMastery, signals };
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
