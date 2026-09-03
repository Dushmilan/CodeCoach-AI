"""Visual Design System tokens — typography, spacing, color, camera.

Single source of truth for how polished 9:16/16:9 social videos look.
Scene Planner reads these; viewer components consume them. Improving tokens
improves every future algorithm video.

Refs: viewer.tsx typography (JetBrains Mono), animation_compiler palette.
"""

# ── Typography — one display + one mono, aggressive hierarchy ──────────────
DISPLAY_FONT = "JetBrains Mono, monospace"
MONO_FONT = "JetBrains Mono, monospace"

# Sizes are canvas units (viewer is 1920x1080, center origin). 9:16 templates
# scale down via camera.zoom.
TITLE_SIZE = 40
NARRATION_SIZE = 24
BADGE_SIZE = 28
CELL_LABEL_SIZE = 28
COMPLEXITY_SIZE = 32

# Hierarchy: short labels beat paragraphs. Max narration already 300 chars in
# AnimationValidator.
MAX_LABEL = 24  # visual primitives truncate to this

# ── Spacing / layout ───────────────────────────────────────────────────────
CELL_GAP = 12.0
ROW_Y = 0.0
BADGE_Y = -260.0
TITLE_Y = -300.0
NARRATION_Y = 280.0

# ── Palette (extends animation_compiler palette for cinematic beats) ───────
PALETTE = {
    "idle_fill": "#1e293b",
    "idle_stroke": "#334155",
    "highlight_fill": "#1d4ed8",
    "highlight_stroke": "#3b82f6",
    "dim_fill": "#0f172a",
    "dim_stroke": "#1e293b",
    "accent": "#facc15",
    "success_fill": "#14532d",
    "success_stroke": "#22c55e",
    "muted": "#94a3b8",
    "text": "#e2e8f0",
}

# ── Motion durations (seconds) — pacing beats, not literal steps ──────────
DURATION = {
    "enter": 0.4,
    "highlight": 0.35,
    "focus": 0.5,
    "dim": 0.3,
    "stagger": 0.08,
}

# ── Camera — reusable focus/zoom/pan/reset (viewer implements) ────────────
CAMERA = {
    "zoom_focus": 1.25,
    "zoom_full": 1.0,
    "pan_duration": 0.5,
}
