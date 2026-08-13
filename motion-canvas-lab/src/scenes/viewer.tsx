import {makeScene2D, Rect, Circle, Line, Txt, View2D} from '@motion-canvas/2d';
import {all, createRef, waitFor, Vector2, ThreadGenerator} from '@motion-canvas/core';

// ─────────────────────────────────────────────────────────────────────────────
// VIEWER SCENE — the runtime the CodeCoach app opens in the in-app modal.
//
// The opener (CodeCoach Animate launcher) opens this page with ?token=<nonce>,
// fetches an animation from /api/coach/animate, then posts it here via
// postMessage:
//
//   { type: "CODECOACH_ANIMATION", token, animation }
//
// or on failure:
//
//   { type: "CODECOACH_ANIMATION_ERROR", token, message }
//
// The animation is a GENERIC declarative scene: vector primitives (shapes)
// plus a per-step motion timeline. There are no animation-type or subject
// catalogs — the model authors the subject and the algorithm visuals fresh
// for every question, and this engine renders whatever data it receives.
//
// If no message arrives (e.g. the lab is opened directly), the scene falls
// back to a small built-in demo so `pnpm dev` always shows something.
// ─────────────────────────────────────────────────────────────────────────────

const MESSAGE_TYPE = 'CODECOACH_ANIMATION';
const ERROR_MESSAGE_TYPE = 'CODECOACH_ANIMATION_ERROR';
const STEP_MESSAGE_TYPE = 'CODECOACH_VIEWER_STEP';
const WAIT_TIMEOUT_MS = 5_000;
const WAIT_TICK_MS = 200;

// Broadcast the current step to the page's own DOM overlay (see
// viewer-player.ts). The overlay renders a narration bar, a step counter and a
// scrubber; it cannot read the scene's internal step index itself.
function postViewerStep(state: {
  state: 'running' | 'complete' | 'error';
  step?: number;
  total?: number;
  narration?: string;
}): void {
  window.postMessage({type: STEP_MESSAGE_TYPE, ...state}, window.location.origin);
}

type ShapeType = 'rect' | 'ellipse' | 'line' | 'polygon' | 'text';

interface SceneShape {
  id: string;
  type: ShapeType;
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  radius?: number;
  points?: [number, number][];
  text?: string;
  fontSize?: number;
  fill?: string;
  stroke?: string;
  lineWidth?: number;
  opacity?: number;
}

type MotionOpName =
  | 'appear'
  | 'disappear'
  | 'move'
  | 'fill'
  | 'stroke'
  | 'scale'
  | 'rotate'
  | 'label';

interface MotionOp {
  target: string;
  op: MotionOpName;
  to?: unknown;
  duration: number;
}

interface AnimationStepData {
  narration?: string;
  shapes?: SceneShape[];
  motion?: MotionOp[];
}

interface AnimationData {
  title?: string;
  data?: Record<string, unknown>;
  steps: AnimationStepData[];
}

const DEMO_ANIMATION: AnimationData = {
  title: 'Two cars race to the target',
  steps: [
    {
      narration: 'Two cars race toward the destination.',
      shapes: [
        {id: 'road', type: 'line', x: 0, y: 120, points: [[-900, 0], [900, 0]], stroke: '#334155', lineWidth: 8},
        {id: 'flag_pole', type: 'line', x: 760, y: 120, points: [[0, -180], [0, 0]], stroke: '#facc15', lineWidth: 6},
        {id: 'flag', type: 'polygon', x: 760, y: 120, points: [[0, -180], [80, -160], [0, -140]], fill: '#facc15'},
        {id: 'car1_body', type: 'rect', x: -760, y: 60, width: 180, height: 56, radius: 14, fill: '#ef4444'},
        {id: 'car1_cabin', type: 'polygon', x: -760, y: 60, points: [[-40, -28], [0, -70], [60, -70], [90, -28]], fill: '#7f1d1d'},
        {id: 'car1_wheel1', type: 'ellipse', x: -830, y: 104, width: 48, height: 48, fill: '#0f172a'},
        {id: 'car1_wheel2', type: 'ellipse', x: -690, y: 104, width: 48, height: 48, fill: '#0f172a'},
      ],
      motion: [
        {target: 'road', op: 'appear', duration: 0.4},
        {target: 'flag_pole', op: 'appear', duration: 0.4},
        {target: 'flag', op: 'appear', duration: 0.4},
        {target: 'car1_body', op: 'appear', duration: 0.4},
        {target: 'car1_cabin', op: 'appear', duration: 0.4},
        {target: 'car1_wheel1', op: 'appear', duration: 0.4},
        {target: 'car1_wheel2', op: 'appear', duration: 0.4},
      ],
    },
    {
      narration: 'The red car pulls ahead.',
      shapes: [
        {id: 'car2_body', type: 'rect', x: -760, y: 190, width: 180, height: 56, radius: 14, fill: '#3b82f6'},
        {id: 'car2_cabin', type: 'polygon', x: -760, y: 190, points: [[-40, -28], [0, -70], [60, -70], [90, -28]], fill: '#1e3a8a'},
        {id: 'car2_wheel1', type: 'ellipse', x: -830, y: 234, width: 48, height: 48, fill: '#0f172a'},
        {id: 'car2_wheel2', type: 'ellipse', x: -690, y: 234, width: 48, height: 48, fill: '#0f172a'},
      ],
      motion: [
        {target: 'car2_body', op: 'appear', duration: 0.4},
        {target: 'car2_cabin', op: 'appear', duration: 0.4},
        {target: 'car2_wheel1', op: 'appear', duration: 0.4},
        {target: 'car2_wheel2', op: 'appear', duration: 0.4},
        {target: 'car1_body', op: 'move', to: [300, 60], duration: 2.4},
        {target: 'car1_cabin', op: 'move', to: [300, 60], duration: 2.4},
        {target: 'car1_wheel1', op: 'move', to: [230, 104], duration: 2.4},
        {target: 'car1_wheel2', op: 'move', to: [370, 104], duration: 2.4},
      ],
    },
    {
      narration: 'The blue car catches up.',
      motion: [
        {target: 'car2_body', op: 'move', to: [480, 190], duration: 3.0},
        {target: 'car2_cabin', op: 'move', to: [480, 190], duration: 3.0},
        {target: 'car2_wheel1', op: 'move', to: [410, 234], duration: 3.0},
        {target: 'car2_wheel2', op: 'move', to: [550, 234], duration: 3.0},
      ],
    },
  ],
};

let receivedAnimation: AnimationData | null = null;
let receivedError: string | null = null;

// Register the message bridge at module scope (not on the first playback tick).
// The CodeCoach app posts the animation as soon as the viewer iframe fires its
// `load` event, which can beat the scene generator's first frame — registering
// here guarantees the payload is never missed.
const token = new URLSearchParams(window.location.search).get('token');
setupMessageBridge(token);

function setupMessageBridge(token: string | null): void {
  window.addEventListener('message', (event: MessageEvent) => {
    const data = event.data;
    if (!data || typeof data !== 'object') return;
    // The animation payload only ever comes from the embedding CodeCoach app.
    // Accept it only when a token was requested AND the sender is the parent
    // frame; direct opens of viewer.html run the built-in demo instead.
    if (!token) return;
    if (event.source !== window.parent) return;
    if (data.token !== token) return;
    if (data.type === MESSAGE_TYPE && data.animation) {
      receivedAnimation = data.animation as AnimationData;
    } else if (data.type === ERROR_MESSAGE_TYPE) {
      receivedError = typeof data.message === 'string' ? data.message : 'Failed to generate the animation.';
    }
  });
}

const STEP_HOLD = 0.4;

function buildShapeNode(shape: SceneShape, ref: any, baseOpacity: number): any {
  const common: Record<string, unknown> = {
    x: shape.x ?? 0,
    y: shape.y ?? 0,
    fill: shape.fill,
    stroke: shape.stroke,
    lineWidth: shape.lineWidth,
    opacity: baseOpacity,
  };
  // Rect/ellipse shapes may carry a value in their "text" field (e.g. an array
  // cell "5"); render that label as a child so it moves/scales with the shape.
  const label =
    shape.text && (shape.type === 'rect' || shape.type === 'ellipse') ? (
      <Txt
        text={shape.text}
        fontSize={shape.fontSize ?? 28}
        fontFamily={'JetBrains Mono, monospace'}
        fill={'#e2e8f0'}
        textAlign={'center'}
      />
    ) : null;
  switch (shape.type) {
    case 'rect':
      return (
        <Rect
          ref={ref}
          width={shape.width}
          height={shape.height}
          radius={shape.radius}
          {...common}
        >
          {label}
        </Rect>
      );
    case 'ellipse':
      return (
        <Circle ref={ref} width={shape.width} height={shape.height} {...common}>
          {label}
        </Circle>
      );
    case 'line':
      return <Line ref={ref} points={shape.points as any} {...common} />;
    case 'polygon':
      return <Line ref={ref} points={shape.points as any} closed {...common} />;
    case 'text':
      return (
        <Txt
          ref={ref}
          text={shape.text}
          fontSize={shape.fontSize}
          fontFamily={'JetBrains Mono, monospace'}
          textAlign={'center'}
          {...common}
        />
      );
  }
}

function applyMotion(node: any, op: MotionOp): any {
  const duration = op.duration;
  switch (op.op) {
    case 'appear':
      return node.opacity(1, duration);
    case 'disappear':
      return node.opacity(0, duration);
    case 'move':
      return node.position(new Vector2((op.to as [number, number])[0], (op.to as [number, number])[1]), duration);
    case 'fill':
      return node.fill(op.to as string, duration);
    case 'stroke':
      return node.stroke(op.to as string, duration);
    case 'scale':
      return node.scale(op.to as number, duration);
    case 'rotate':
      return node.rotation(op.to as number, duration);
    case 'label':
      if (typeof node.text === 'function') {
        return node.text(op.to as string, duration);
      }
      return node.opacity(node.opacity(), 0);
  }
}

function* renderGenericScene(
  view: View2D,
  animation: AnimationData,
): ThreadGenerator {
  view.fill('#0b0f19');

  const steps = Array.isArray(animation.steps) ? animation.steps : [];
  const title = animation.title || 'Algorithm trace';

  const titleRef = createRef<Txt>();
  const narration = createRef<Txt>();
  const progress = createRef<Txt>();

  view.add(
    <Txt
      ref={titleRef}
      text={title}
      fontSize={40}
      fontWeight={700}
      fill={'#e2e8f0'}
      fontFamily={'JetBrains Mono, monospace'}
      y={-300}
      opacity={0}
      textAlign={'center'}
    />,
  );
  view.add(
    <Txt
      ref={narration}
      text={''}
      fontSize={24}
      fill={'#94a3b8'}
      fontFamily={'JetBrains Mono, monospace'}
      y={280}
      opacity={0}
      textAlign={'center'}
    />,
  );
  view.add(
    <Txt
      ref={progress}
      text={`0 / ${steps.length}`}
      fontSize={20}
      fill={'#64748b'}
      fontFamily={'JetBrains Mono, monospace'}
      y={340}
      opacity={0}
      textAlign={'center'}
    />,
  );

  yield* all(
    titleRef().opacity(1, 0.5),
    narration().opacity(1, 0.5),
    progress().opacity(1, 0.5),
  );
  yield* waitFor(0.3);

  const nodes = new Map<string, any>();

  for (let i = 0; i < steps.length; i++) {
    const step = steps[i];
    const shapes = Array.isArray(step.shapes) ? step.shapes : [];
    const motion = Array.isArray(step.motion) ? step.motion : [];

    const appearing = new Set(
      motion.filter((op) => op.op === 'appear').map((op) => op.target),
    );

    for (const shape of shapes) {
      const ref = createRef<any>();
      const baseOpacity = appearing.has(shape.id) ? 0 : shape.opacity ?? 1;
      const node = buildShapeNode(shape, ref, baseOpacity);
      view.add(node);
      nodes.set(shape.id, ref());
    }

    yield* narration().text(step.narration || '...', 0.25);
    yield* progress().text(`${i + 1} / ${Math.max(steps.length, 1)}`, 0.2);
    postViewerStep({
      state: 'running',
      step: i + 1,
      total: steps.length,
      narration: step.narration || '',
    });
    if (motion.length > 0) {
      yield* all(
        ...motion
          .filter((op) => nodes.has(op.target))
          .map((op) => applyMotion(nodes.get(op.target), op)),
      );
    }
    yield* waitFor(STEP_HOLD);
  }

  postViewerStep({state: 'complete', total: steps.length});
  yield* narration().text('Animation complete.', 0.3);
  yield* waitFor(0.5);
  yield* all(...view.children().map((child) => child.opacity(0, 0.4)));
  yield* waitFor(0.2);
}

function* renderNarrationTimeline(
  view: View2D,
  animation: AnimationData,
): ThreadGenerator {
  view.fill('#0b0f19');
  const title = animation.title || 'Algorithm trace';
  const steps = Array.isArray(animation.steps) ? animation.steps : [];

  const titleRef = createRef<Txt>();
  const card = createRef<Rect>();
  const textRef = createRef<Txt>();
  const progress = createRef<Txt>();

  view.add(
    <Txt
      ref={titleRef}
      text={title}
      fontSize={40}
      fontWeight={700}
      fill={'#e2e8f0'}
      fontFamily={'JetBrains Mono, monospace'}
      y={-260}
      opacity={0}
    />,
  );
  view.add(
    <Rect
      ref={card}
      width={820}
      height={260}
      radius={20}
      fill={'#111827'}
      stroke={'#1f2937'}
      lineWidth={2}
      y={40}
      opacity={0}
    />,
  );
  view.add(
    <Txt
      ref={textRef}
      text={''}
      fontSize={28}
      fill={'#e2e8f0'}
      fontFamily={'JetBrains Mono, monospace'}
      width={720}
      textWrap={true}
      textAlign={'center'}
      y={40}
      opacity={0}
    />,
  );
  view.add(
    <Txt
      ref={progress}
      text={'1 / ' + Math.max(steps.length, 1)}
      fontSize={20}
      fill={'#64748b'}
      fontFamily={'JetBrains Mono, monospace'}
      y={210}
      opacity={0}
    />,
  );

  yield* all(
    titleRef().opacity(1, 0.5),
    card().opacity(1, 0.5),
    textRef().opacity(1, 0.5),
    progress().opacity(1, 0.5),
  );
  yield* waitFor(0.4);

  const frames = steps.length > 0 ? steps : [{narration: 'No steps were provided for this animation.'}];
  for (let i = 0; i < frames.length; i++) {
    const frame = frames[i];
    yield* textRef().text(frame.narration || '...', 0.3);
    yield* progress().text(`${i + 1} / ${frames.length}`, 0.2);
    postViewerStep({
      state: 'running',
      step: i + 1,
      total: frames.length,
      narration: frame.narration || '',
    });
    yield* waitFor(1.1);
  }

  postViewerStep({state: 'complete', total: frames.length});
  yield* textRef().text('Animation complete.', 0.3);
  yield* waitFor(0.6);
  yield* all(...view.children().map((child) => child.opacity(0, 0.4)));
  yield* waitFor(0.2);
}

function isLegacyShape(animation: AnimationData): boolean {
  const steps = Array.isArray(animation.steps) ? animation.steps : [];
  return steps.some((step) => (step as any).operation !== undefined);
}

export default makeScene2D(function* (view) {
  // Re-running loops (loop:true) must start from a clean canvas, otherwise
  // shapes from the previous pass accumulate.
  view.removeChildren();

  // Wait a bounded amount of TIMELINE time for the animation payload. A
  // wall-clock deadline (performance.now()) must not be used here: the scene's
  // duration is measured by fast-forwarding the generator, during which the
  // real clock barely advances, so a wall-clock loop would report an unbounded
  // timeline and break the overlay scrubber.
  const waitTicks = Math.ceil(WAIT_TIMEOUT_MS / WAIT_TICK_MS);
  for (let i = 0; i < waitTicks && !receivedAnimation && !receivedError; i++) {
    yield* waitFor(WAIT_TICK_MS / 1000);
  }

  if (receivedError) {
    postViewerStep({state: 'error', narration: receivedError});
    view.fill('#0b0f19');
    const errorText = createRef<Txt>();
    view.add(
      <Txt
        ref={errorText}
        text={receivedError}
        fontSize={30}
        fill={'#f87171'}
        fontFamily={'JetBrains Mono, monospace'}
        textAlign={'center'}
        width={760}
        textWrap={true}
        opacity={0}
      />,
    );
    yield* errorText().opacity(1, 0.4);
    yield* waitFor(3);
    return;
  }

  const animation = receivedAnimation || DEMO_ANIMATION;
  if (isLegacyShape(animation)) {
    yield* renderNarrationTimeline(view, animation);
  } else {
    yield* renderGenericScene(view, animation);
  }
});
