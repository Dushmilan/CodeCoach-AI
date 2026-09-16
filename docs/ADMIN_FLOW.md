# Cross-role UI flow conventions (Issue #180)

Admin is top level: courses, professors, classrooms, analytics — one coherent
flow. Shared rules every role layout follows:

- Role checks go through `frontend/src/lib/roles.ts`
  (`isAdmin` / `isProfessor` / `isTA` / `isInstructor`). No inline
  `['admin', ...].includes(...)` arrays in layouts, headers, or sidebars.
- Sign-in routing goes through `frontend/src/lib/auth/roleHome.ts`:
  `roleHomePath(role)` for homes, `signInPathFor(pathname)` for guards
  (admin area → `/admin/login`, everywhere else → `/login`).
- Guards redirect unauthenticated users with `router.replace` (never a
  dead-end panel). Authenticated users lacking the role see Access Denied
  **with** `Back to home` + `Go to sign-in` links.
- Admin drill-down (`Professors` sidebar → roster → classrooms → analytics)
  is backed by `GET /api/admin/hierarchy`. Owner-scoped course mutations
  (#175), batch analytics (#179), and professor analytics access (#176) are
  implemented in their own issues and linked here, not duplicated.
