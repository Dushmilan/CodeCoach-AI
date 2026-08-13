// Ambient module declarations for the Motion Canvas Vite plugin's virtual
// query modules. `*?scene` is declared by @motion-canvas/core/project; the
// `?project` loader (used by the chrome-less viewer entry) is not, so we
// declare it here to satisfy `tsc --noEmit`.
declare module '*?project' {
  import type {Project} from '@motion-canvas/core';
  const value: Project;
  export = value;
}
