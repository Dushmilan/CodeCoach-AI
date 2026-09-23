// motion-canvas-lab/tests/viewer-annotation.spec.ts
// #287: the intent callout ("math bubble") in the animation viewer.
//
// The launcher posts a trace-built payload whose decision beats carry
// `annotation: {text}`. The scene draws the bubble near the active shape;
// the DOM overlay mirrors it (same pattern as narration) so the beat's
// "why" is observable — and screen-reader reachable — and it must be gone
// again once the beat passes.
import {test, expect} from '@playwright/test';

test('annotated beat shows the intent callout and later drops it (#287)', async ({page}) => {
  const token = 'test-287-' + Date.now();
  await page.goto(`/viewer.html?token=${token}`);
  await page.waitForTimeout(1500);
  await page.evaluate(([t]) => {
    window.postMessage(
      {
        type: 'CODECOACH_ANIMATION',
        token: t,
        animation: {
          title: 'annotation-probe',
          steps: [
            {
              narration: 'intro',
              shapes: [
                {
                  id: 'cell_0',
                  type: 'rect',
                  x: -200,
                  y: 0,
                  width: 88,
                  height: 88,
                  fill: '#1e293b',
                },
              ],
              motion: [{target: 'cell_0', op: 'appear', duration: 0.4}],
            },
            {
              narration: 'decision',
              camera: {action: 'focus', element: 'cell_0', zoom: 1.25},
              motion: [{target: 'cell_0', op: 'move', to: [-100, 0], duration: 2.5}],
              annotation: {text: '5 < 7 → search right →'},
            },
            {
              narration: 'outro',
              motion: [{target: 'cell_0', op: 'scale', to: 1.0, duration: 0.25}],
            },
          ],
        },
      },
      '*',
    );
  }, [token]);

  const annotation = page.locator('#viewer-annotation');
  await expect(annotation, 'overlay mirrors the beat annotation').toHaveCount(1, {
    timeout: 30000,
  });
  // Appears with the decision beat …
  await expect(annotation).toHaveText('5 < 7 → search right →', {timeout: 30000});
  // … holds while the beat plays …
  await page.waitForTimeout(600);
  await expect(annotation).toHaveText('5 < 7 → search right →');
  // … and disappears once the player advances past the annotated beat.
  await expect(annotation).toHaveText('', {timeout: 30000});
});

test('beats without an annotation never show a callout (#287)', async ({page}) => {
  const token = 'test-287-plain-' + Date.now();
  await page.goto(`/viewer.html?token=${token}`);
  await page.waitForTimeout(1500);
  await page.evaluate(([t]) => {
    window.postMessage(
      {
        type: 'CODECOACH_ANIMATION',
        token: t,
        animation: {
          title: 'plain-probe',
          steps: [
            {narration: 'one'},
            {narration: 'two'},
            {narration: 'three'},
          ],
        },
      },
      '*',
    );
  }, [token]);
  const annotation = page.locator('#viewer-annotation');
  await expect(annotation).toHaveCount(1, {timeout: 30000});
  await expect(annotation).toHaveText('');
});
