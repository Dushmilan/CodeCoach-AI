import {defineConfig, type PluginOption} from 'vite';
import motionCanvas from '@motion-canvas/vite-plugin';
import ffmpeg from '@motion-canvas/ffmpeg';

// The chrome-less viewer (viewer.html) imports `./src/viewer-project?project`,
// which the Motion Canvas plugin resolves generically at build time, so it does
// not need to be listed in `project` (that list is only for the editor's
// project index and rollup inputs). We DO add viewer.html itself as a rollup
// input here, otherwise `vite build` would only emit the project modules.
const viewerProjectPlugin: PluginOption = {
  name: 'codecoach-viewer-html-entry',
  enforce: 'post',
  config(config) {
    return {
      build: {
        rollupOptions: {
          input: {
            ...config.build?.rollupOptions?.input,
            viewer: new URL('./viewer.html', import.meta.url).pathname,
          },
        },
      },
    };
  },
};

export default defineConfig({
  plugins: [
    motionCanvas({
      project: ['./src/project.ts'],
    }),
    ffmpeg(),
    viewerProjectPlugin,
  ],
});
