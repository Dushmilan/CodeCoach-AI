/** Shared role predicates for the admin → professor → TA hierarchy (Issue #178).
 *
 * Single source of truth for role checks. Header, layouts, and sidebars must
 * use these instead of inline `includes(...)` arrays so the hierarchy stays
 * consistent across surfaces. Mirrors backend `PROFESSOR_ROLES` /
 * `INSTRUCTOR_ROLES` in `app/api/auth_deps.py`.
 */

export type AppRole = string | null | undefined;

function normalize(role: AppRole): string | null {
  return typeof role === "string" ? role : null;
}

/** Admins only: `admin` + `super_admin`. */
export function isAdmin(role: AppRole): boolean {
  const r = normalize(role);
  return r === "admin" || r === "super_admin";
}

/** Professor scope plus admins (admins inherit professor access). */
export function isProfessor(role: AppRole): boolean {
  const r = normalize(role);
  return r === "professor" || r === "admin" || r === "super_admin";
}

/** TA (demonstrator) scope plus admins. Professors are NOT TAs. */
export function isTA(role: AppRole): boolean {
  const r = normalize(role);
  return r === "ta" || r === "admin" || r === "super_admin";
}

/** Any instructor surface: professor, TA, or admin. Students/anonymous denied. */
export function isInstructor(role: AppRole): boolean {
  const r = normalize(role);
  return (
    r === "professor" || r === "ta" || r === "admin" || r === "super_admin"
  );
}
