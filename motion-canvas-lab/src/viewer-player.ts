import {PlaybackState, Player, Stage} from '@motion-canvas/core';

import project from './viewer-project?project';

// ─────────────────────────────────────────────────────────────────────────────
// CHROME-ENABLED VIEWER ENTRY — used by viewer.html.
//
// Renders the viewer project to a full-viewport canvas using the embeddable
// `Player` + `Stage` from @motion-canvas/core, and adds a lightweight DOM
// overlay (rendered OUTSIDE the canvas) with the playback controls the scene
// cannot provide itself:
//
//   • narration bar + step counter (fed by CODECOACH_VIEWER_STEP messages that
//     the scene broadcasts on every step)
//   • play / pause, restart, and 0.5×–2× speed
//   • a time-based scrubber for jumping to any point of the animation
//   • keyboard shortcuts: Space (play/pause), ← / → (seek ±1s), R (restart),
//     1–4 (speed)
//
// The scene (scenes/viewer.tsx) owns the postMessage handshake: it waits for a
// CODECOACH_ANIMATION / CODECOACH_ANIMATION_ERROR message (token-gated) and
// falls back to a built-in demo when opened directly.
// ─────────────────────────────────────────────────────────────────────────────

const STEP_MESSAGE_TYPE = 'CODECOACH_VIEWER_STEP';

interface StepState {
  state: 'running' | 'complete' | 'error';
  step?: number;
  total?: number;
  narration?: string;
}

const SPEEDS = [
  {label: '0.5×', value: 0.5},
  {label: '1×', value: 1},
  {label: '1.5×', value: 1.5},
  {label: '2×', value: 2},
];

const SEEK_STEP_SECONDS = 1;

function icon(svg: string): string {
  return `<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true">${svg}</svg>`;
}

function fmtTime(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds));
  const m = Math.floor(s / 60);
  return `${m}:${String(s % 60).padStart(2, '0')}`;
}

// Under loop:true the player's `playback.duration` is just the growing playback
// frame counter (it resets to the current frame on every recalculation), so it
// cannot bound the scrubber. The scene's own timeline (lastFrame - firstFrame)
// is the real length; cap it defensively in case a scene reports an unbounded
// timeline.
const MAX_TIMELINE_SECONDS = 120;

function timelineMaxFrames(player: Player): number {
  const cap = player.status.secondsToFrames(MAX_TIMELINE_SECONDS);
  const scene = player.playback.currentScene;
  if (scene) {
    const frames = scene.lastFrame - scene.firstFrame;
    if (Number.isFinite(frames) && frames > 1) {
      return Math.max(1, Math.min(frames, cap));
    }
  }
  return cap;
}

function buildOverlay(player: Player): void {
  const overlay = document.createElement('div');
  overlay.id = 'viewer-overlay';

  // Narration bar (top)
  const narration = document.createElement('div');
  narration.id = 'viewer-narration';
  const stepChip = document.createElement('span');
  stepChip.id = 'viewer-step-chip';
  stepChip.textContent = '';
  const narrationText = document.createElement('span');
  narrationText.id = 'viewer-narration-text';
  narrationText.textContent = 'Preparing the animation…';
  narration.append(stepChip, narrationText);
  overlay.append(narration);

  // Control bar (bottom)
  const controls = document.createElement('div');
  controls.id = 'viewer-controls';
  controls.setAttribute('role', 'toolbar');
  controls.setAttribute('aria-label', 'Animation controls');

  const restart = document.createElement('button');
  restart.type = 'button';
  restart.className = 'viewer-btn';
  restart.setAttribute('aria-label', 'Restart animation');
  restart.title = 'Restart (R)';
  restart.innerHTML = icon(
    '<path d="M12 5V2L7 6l5 4V7c3.31 0 6 2.69 6 6s-2.69 6-6 6-6-2.69-6-6H4c0 4.42 3.58 8 8 8s8-3.58 8-8-3.58-8-8-8z"/>',
  );

  const play = document.createElement('button');
  play.type = 'button';
  play.id = 'viewer-play';
  play.className = 'viewer-btn viewer-btn-primary';
  play.setAttribute('aria-label', 'Play animation');
  play.title = 'Play / Pause (Space)';
  play.innerHTML = icon('<path d="M8 5v14l11-7z"/>');

  const scrubber = document.createElement('input');
  scrubber.type = 'range';
  scrubber.id = 'viewer-scrubber';
  scrubber.min = '0';
  scrubber.max = '100';
  scrubber.value = '0';
  scrubber.step = '1';
  scrubber.setAttribute('aria-label', 'Animation progress');

  const timeLabel = document.createElement('span');
  timeLabel.id = 'viewer-time';
  timeLabel.textContent = '0:00 / 0:00';

  const speedGroup = document.createElement('div');
  speedGroup.id = 'viewer-speed';
  speedGroup.setAttribute('role', 'group');
  speedGroup.setAttribute('aria-label', 'Playback speed');
  for (const speed of SPEEDS) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'viewer-speed-btn';
    btn.dataset.speed = String(speed.value);
    btn.textContent = speed.label;
    btn.setAttribute('aria-label', `Speed ${speed.label}`);
    btn.title = `Speed ${speed.label}`;
    btn.addEventListener('click', () => {
      player.setSpeed(speed.value);
      if (player.status.state === PlaybackState.Paused) player.togglePlayback(true);
    });
    speedGroup.append(btn);
  }

  controls.append(restart, play, scrubber, timeLabel, speedGroup);
  overlay.append(controls);
  document.body.append(overlay);

  const formatNarration = (state: StepState): string => {
    const step =
      typeof state.step === 'number' && typeof state.total === 'number'
        ? `${state.step} / ${state.total}`
        : '';
    if (state.state === 'error') return 'Generation failed';
    if (state.state === 'complete') return 'Complete';
    return step || '';
  };

  const setNarration = (state: StepState): void => {
    narration.classList.toggle('viewer-narration-error', state.state === 'error');
    narration.classList.toggle('viewer-narration-complete', state.state === 'complete');
    stepChip.textContent = formatNarration(state);
    stepChip.style.display = formatNarration(state) ? '' : 'none';
    narrationText.textContent = state.narration || '';
  };

  const setProgress = (frame: number, duration: number): void => {
    const maxFrames = Math.max(1, Math.min(duration, timelineMaxFrames(player)));
    scrubber.max = String(maxFrames);
    scrubber.value = String(Math.min(frame, maxFrames));
    const total = player.status.framesToSeconds(maxFrames);
    const current = player.status.time;
    timeLabel.textContent = `${fmtTime(current)} / ${fmtTime(total)}`;
  };

  play.addEventListener('click', () => player.togglePlayback());
  restart.addEventListener('click', () => {
    player.requestReset();
    player.togglePlayback(true);
  });

  let scrubbing = false;
  scrubber.addEventListener('pointerdown', () => {
    scrubbing = true;
  });
  scrubber.addEventListener('pointerup', () => {
    scrubbing = false;
  });
  scrubber.addEventListener('input', () => {
    const frame = Math.min(Number(scrubber.value), Number(scrubber.max));
    player.requestSeek(frame);
    timeLabel.textContent = `${fmtTime(player.status.framesToSeconds(frame))} / ${fmtTime(
      player.status.framesToSeconds(Number(scrubber.max)),
    )}`;
  });

  player.onFrameChanged.subscribe((frame) => {
    if (!scrubbing) setProgress(frame, player.playback.duration);
  });
  player.onDurationChanged.subscribe((duration) => {
    setProgress(player.playback.frame, duration);
  });
  player.onStateChanged.subscribe((state) => {
    const playing = !state.paused;
    play.innerHTML = playing
      ? icon('<path d="M6 5h4v14H6zM14 5h4v14h-4z"/>')
      : icon('<path d="M8 5v14l11-7z"/>');
    play.setAttribute('aria-label', playing ? 'Pause animation' : 'Play animation');
    for (const btn of speedGroup.querySelectorAll<HTMLButtonElement>('.viewer-speed-btn')) {
      const isActive = Math.abs(Number(btn.dataset.speed) - state.speed) < 0.01;
      btn.classList.toggle('viewer-speed-btn-active', isActive);
      btn.setAttribute('aria-pressed', String(isActive));
    }
  });

  window.addEventListener('message', (event: MessageEvent) => {
    if (event.source !== window) return;
    const data = event.data;
    if (!data || typeof data !== 'object' || data.type !== STEP_MESSAGE_TYPE) return;
    const state: StepState = {
      state: data.state === 'error' ? 'error' : data.state === 'complete' ? 'complete' : 'running',
      step: data.step,
      total: data.total,
      narration: typeof data.narration === 'string' ? data.narration : '',
    };
    setNarration(state);
  });

  window.addEventListener('keydown', (event: KeyboardEvent) => {
    const target = event.target as HTMLElement | null;
    const isFormControl =
      target instanceof HTMLInputElement || target instanceof HTMLButtonElement;
    const hasModifier = event.ctrlKey || event.metaKey || event.altKey;
    if (event.key === ' ') {
      if (isFormControl || hasModifier) return;
      event.preventDefault();
      player.togglePlayback();
    } else if (event.key.toLowerCase() === 'r') {
      if (isFormControl || hasModifier) return;
      event.preventDefault();
      player.requestReset();
      player.togglePlayback(true);
    } else if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
      if (target instanceof HTMLInputElement || hasModifier) return;
      event.preventDefault();
      const delta =
        (event.key === 'ArrowRight' ? SEEK_STEP_SECONDS : -SEEK_STEP_SECONDS) *
        player.status.fps;
      player.requestSeek(Math.round(player.playback.frame + delta));
      player.togglePlayback(false);
    } else if (/^[1-4]$/.test(event.key)) {
      if (isFormControl || hasModifier) return;
      event.preventDefault();
      player.setSpeed(SPEEDS[Number(event.key) - 1].value);
      if (player.status.state === PlaybackState.Paused) player.togglePlayback(true);
    }
  });
}

declare global {
  interface Window {
    __viewerOverlayBuilt?: boolean;
  }
}

async function main(): Promise<void> {
  const stage = new Stage();
  const canvas = stage.finalBuffer;
  canvas.id = 'stage-canvas';
  document.body.appendChild(canvas);

  const settings = project.meta.getFullRenderingSettings();
  stage.configure(settings);

  const player = new Player(
    project,
    settings,
    {
      loop: true,
      paused: false,
      muted: false,
      volume: 1,
      speed: 1,
    },
    0,
  );
  player.onRender.subscribe(async () => {
    await stage.render(player.playback.currentScene, player.playback.previousScene);
  });

  // Guard against HMR / double-invocation stacking a second overlay (and its
  // global keydown/message listeners) on top of the first.
  if (!window.__viewerOverlayBuilt) {
    buildOverlay(player);
    window.__viewerOverlayBuilt = true;
  }

  player.togglePlayback(true);
}

void main();
