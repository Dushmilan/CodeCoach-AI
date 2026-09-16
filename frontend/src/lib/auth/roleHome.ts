/** Shared role-home + sign-in routing (Issue #180).
 *
 * Single source for where each role lands and where guards send
 * unauthenticated users. Layouts and guards must use these instead of
 * hardcoded paths so cross-role flows stay consistent.
 */

export type AppRoleName =
  | "admin"
  | "super_admin"
  | "professor"
  | "ta"
  | "user"
  | string
  | null
  | undefined;

/** Home route for a role. Unknown/anonymous roles go to /login. */
export function roleHomePath(role: AppRoleName): string {
  switch (role) {
    case "admin":
    case "super_admin":
      return "/admin/dashboard";
    case "professor":
      return "/professor";
    case "ta":
      return "/demonstrator";
    default:
      return "/login";
  }
}

/** Sign-in route for a guarded pathname. Admin area -> /admin/login. */
export function signInPathFor(pathname: string | null | undefined): string {
  if (typeof pathname === "string" && pathname.startsWith("/admin")) {
    return "/admin/login";
  }
  return "/login";
}
