import { FetchClient } from "./fetch-client";

const client = new FetchClient();

export interface HierarchyCourse {
  id: string;
  title: string;
  lessons: number;
}

export interface HierarchyClassroom {
  id: string;
  name: string;
  invite_code: string;
  tas: string[];
  students: number;
  avg_completion: number;
}

export interface HierarchyProfessor {
  id: string;
  username: string;
  courses: HierarchyCourse[];
  classrooms: HierarchyClassroom[];
}

export interface AdminHierarchy {
  professors: HierarchyProfessor[];
}

export interface ClassroomDetailClassroom {
  id: string;
  course_id: string;
  owner_id: string | null;
  name: string;
  invite_code: string;
  term: string | null;
  schedule: string | null;
}

export interface ClassroomDetailStudent {
  user_id: string;
  completed_lessons: number;
  completion_pct: number;
  attempted: number;
  solved: number;
}

export interface ClassroomDetailAnalytics {
  total_students: number;
  avg_completion: number;
  avg_solved: number;
  students: ClassroomDetailStudent[];
}

export interface ClassroomDetail {
  classroom: ClassroomDetailClassroom;
  analytics: ClassroomDetailAnalytics;
}

export const apiClient = {
  async get<T>(path: string): Promise<{ data: T }> {
    const data = await client.get<T>(path);
    return { data };
  },

  /** Admin tree for the admin → professors drill-down (Issue #178). */
  async getAdminHierarchy(): Promise<AdminHierarchy> {
    return client.get<AdminHierarchy>("/api/admin/hierarchy");
  },

  /** Room + class aggregates for the admin → classroom drill-down (Issue #178).
   * Backed by GET /api/instructor/classrooms/{id}; admins bypass ownership
   * via the backend passthrough. */
  async getClassroomDetail(classroomId: string): Promise<ClassroomDetail> {
    return client.get<ClassroomDetail>(
      `/api/instructor/classrooms/${encodeURIComponent(classroomId)}`,
    );
  },
};
