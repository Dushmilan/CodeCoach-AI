import {makeScene2D, Rect, Txt, Polygon, Line} from '@motion-canvas/2d';
import {all, chain, createRef, waitFor, Vector2} from '@motion-canvas/core';

// ─────────────────────────────────────────────────────────────────────────────
// TESTING PAPERS — the single file you edit while experimenting with Motion
// Canvas. Nothing here touches the real CodeCoach app. Change the fixture data
// below (TEST_VALUES / TEST_TARGET) or add your own scenes to play around.
//
// To run:
//   cd motion-canvas-lab && pnpm install && pnpm dev
// Then open the printed URL (default http://localhost:9000) in your browser.
// ─────────────────────────────────────────────────────────────────────────────

const TEST_VALUES = [5, 1, 2, 3, 4, 6];
const TEST_TARGET = 4;

// Pause (seconds) after each comparison so the eye can register it.
const STEP_DELAY = 0.6;
// One second of tween for color/scale changes.
const TWEEN_SECONDS = 0.25;

const IDLE_FILL = '#1e293b';
const IDLE_STROKE = '#334155';
const CHECKING_FILL = '#1d4ed8';
const CHECKING_STROKE = '#3b82f6';
const MISMATCH_FILL = '#7f1d1d';
const MISMATCH_STROKE = '#ef4444';
const MATCH_FILL = '#14532d';
const MATCH_STROKE = '#22c55e';
const TEXT_IDLE = '#94a3b8';
const TEXT_ACTIVE = '#ffffff';

export default makeScene2D(function* (view) {
  view.fill('#0b0f19');

  const title = createRef<Txt>();
  const narration = createRef<Txt>();
  const pointer = createRef<Polygon>();
  const cells: Rect[] = [];
  const labels: Txt[] = [];

  const cellSize = new Vector2(88, 88);
  const gap = 12;
  const totalWidth =
    cellsWidth(TEST_VALUES.length, cellSize.x, gap);
  const startX = -totalWidth / 2 + cellSize.x / 2;

  view.add(
    <Txt
      ref={title}
      text={`Linear Search for ${TEST_TARGET}`}
      fontSize={42}
      fontWeight={700}
      fill={'#e2e8f0'}
      fontFamily={'JetBrains Mono, monospace'}
      y={-280}
      opacity={0}
    />,
  );

  view.add(
    <Txt
      ref={narration}
      text={''}
      fontSize={26}
      fill={'#94a3b8'}
      fontFamily={'JetBrains Mono, monospace'}
      y={260}
      opacity={0}
      textAlign={'center'}
    />,
  );

  TEST_VALUES.forEach((value, index) => {
    const x = startX + index * (cellSize.x + gap);
    const cell = createRef<Rect>();
    const label = createRef<Txt>();

    view.add(
      <Rect
        ref={cell}
        width={cellSize.x}
        height={cellSize.y}
        radius={12}
        fill={IDLE_FILL}
        stroke={IDLE_STROKE}
        lineWidth={2}
        x={x}
        y={0}
        opacity={0}
        scale={0.6}
      />,
    );
    view.add(
      <Txt
        ref={label}
        text={String(value)}
        fontSize={36}
        fill={TEXT_IDLE}
        fontFamily={'JetBrains Mono, monospace'}
        x={x}
        y={0}
        opacity={0}
      />,
    );

    cells.push(cell());
    labels.push(label());
  });

  view.add(
    <Polygon
      ref={pointer}
      sides={3}
      radius={14}
      fill={'#facc15'}
      y={-cellSize.y / 2 - 34}
      x={startX}
      opacity={0}
    />,
  );

  // Small legend line under the array.
  view.add(
    <Line
      points={[
        [-totalWidth / 2, cellSize.y / 2 + 26],
        [totalWidth / 2, cellSize.y / 2 + 26],
      ]}
      stroke={'#1e293b'}
      lineWidth={2}
      opacity={0}
    />,
  );

  // ── Intro ──────────────────────────────────────────────────────────────────
  yield* all(
    title().opacity(1, 0.5),
    narration().opacity(1, 0.5),
    pointer().opacity(1, 0.5),
  );
  yield* narration().text('We scan the array left to right, comparing each value to the target.', 0.3);
  yield* waitFor(0.4);

  // Pop in the cells.
  yield* all(
    ...cells.map((cell, i) => chain(waitFor(i * 0.08), cell.scale(1, TWEEN_SECONDS), cell.opacity(1, TWEEN_SECONDS))),
    ...labels.map((label, i) => chain(waitFor(i * 0.08), label.opacity(1, TWEEN_SECONDS))),
  );
  yield* waitFor(0.3);

  // ── Comparisons ─────────────────────────────────────────────────────────────
  for (let i = 0; i < TEST_VALUES.length; i++) {
    const value = TEST_VALUES[i];
    const isMatch = value === TEST_TARGET;

    yield* all(
      pointer().position(new Vector2(startX + i * (cellSize.x + gap), pointer().position().y), 0.35),
      narration().text(
        `Compare index ${i} (value ${value}) against target ${TEST_TARGET}…`,
        0.3,
      ),
    );

    if (isMatch) {
      yield* all(
        cells[i].fill(MATCH_FILL, TWEEN_SECONDS),
        cells[i].stroke(MATCH_STROKE, TWEEN_SECONDS),
        labels[i].fill(TEXT_ACTIVE, TWEEN_SECONDS),
      );
      yield* narration().text('Found it! The value equals the target.', 0.3);
      yield* waitFor(STEP_DELAY + 0.4);
      break;
    }

    // Checking flash.
    yield* all(
      cells[i].fill(CHECKING_FILL, TWEEN_SECONDS),
      cells[i].stroke(CHECKING_STROKE, TWEEN_SECONDS),
      labels[i].fill(TEXT_ACTIVE, TWEEN_SECONDS),
    );
    yield* waitFor(STEP_DELAY / 2);

    // Not a match → mismatch.
    yield* all(
      cells[i].fill(MISMATCH_FILL, TWEEN_SECONDS),
      cells[i].stroke(MISMATCH_STROKE, TWEEN_SECONDS),
      labels[i].fill(TEXT_ACTIVE, TWEEN_SECONDS),
    );
    yield* narration().text(`${value} ≠ ${TEST_TARGET} — keep going.`, 0.3);
    yield* waitFor(STEP_DELAY);
  }

  // ── Outro ───────────────────────────────────────────────────────────────────
  yield* narration().text('Done.', 0.3);
  yield* waitFor(0.6);
  yield* all(
    ...view
      .children()
      .map((child) => child.opacity(0, 0.4)),
  );
  yield* waitFor(0.2);
});

/** Total width needed to lay out `count` cells with a fixed gap. */
function cellsWidth(count: number, cell: number, gap: number): number {
  return count * cell + (count - 1) * gap;
}
