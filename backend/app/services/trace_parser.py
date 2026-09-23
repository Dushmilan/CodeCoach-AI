"""Normalization of the JSON-lines execution trace from a traced solution.

A traced canonical solution prints one JSON object per line with an "event"
key. This module parses stdout into typed TraceEvent objects and drops
anything that is not a well-formed, known event (stray prints, blank lines,
unknown event kinds) so the compiler only ever sees a clean, ordered event
stream.

Any event may additionally carry an optional ``intent`` string (#287): a
causal "why" computed by the reference solution from live runtime values
(e.g. ``"sum 17 > 9 → move right pointer left"``). It rides the event into
the beat's ``annotation`` so the viewer can show real causality — never
hardcoded narration. Only a non-empty string survives parsing, truncated to
200 chars to match ``AnimationStepSpec.annotation``'s cap. Like ``line``,
string fields never enter the __CODE_OFFSET line path.

Known event kinds:

- init:       values/data — the primary structure the algorithm operates on
              (kind: "array"/"linked_list"/"tree"/"grid"/"graph"/"intervals"/"stack"/"backtrack").
- compare:    i, j — indices of two array elements being compared (j optional
              for an array-vs-scalar comparison).
- swap:       i, j — the two elements exchanged.
- write:      i, value — array[i] was assigned value.
- pointer:    name, index — a scan index/loop variable reached `index`.
- mark:       i, state — element i entered a named state (e.g. "sorted").
- read:       i — element i was read (greedy/DP reads).
- push:       value — value pushed onto a stack container.
- pop:        value — value popped off a stack container.
- visit:      i — a node/index was visited (lists, trees, graphs, grids).
- choose:     i — candidate i was chosen (backtracking).
- backtrack:  i — recursion unwound from node/index i.
- dp_update:  i, j, value — DP cell (i, j) was assigned value.
- window:     l, r — the active sliding window covers [l, r].
- partition:  i — pivot/index i defines a partition boundary.
- edge:       a, b — the edge between vertices a and b became active.
- return:     result — the function returned.
"""

import json
from typing import Any, List, Optional

MAX_INTENT_LENGTH = 200  # mirrors AnimationStepSpec.annotation max_length

KNOWN_KINDS = frozenset(
    {
        "init",
        "compare",
        "swap",
        "write",
        "pointer",
        "mark",
        "read",
        "push",
        "pop",
        "visit",
        "choose",
        "backtrack",
        "dp_update",
        "window",
        "partition",
        "edge",
        "return",
    }
)

REQUIRED_FIELDS = {
    "compare": ("i",),
    "swap": ("i", "j"),
    "write": ("i",),
    "pointer": ("name", "index"),
    "mark": ("i", "state"),
    "read": ("i",),
    "push": ("value",),
    "pop": ("value",),
    "visit": ("i",),
    "choose": ("i",),
    "backtrack": ("i",),
    "dp_update": ("i", "j", "value"),
    "window": ("l", "r"),
    "partition": ("i",),
    "edge": ("a", "b"),
}


class TraceEvent:
    """One normalized event from the execution trace."""

    __slots__ = ("kind", "fields")

    def __init__(self, kind: str, **fields):
        self.kind = kind
        self.fields = fields

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"TraceEvent({self.kind}, {self.fields!r})"

    def __getattr__(self, name: str):
        # Typed accessors: event.i, event.j, event.state, ... delegate to fields.
        if name in self.fields:
            return self.fields[name]
        raise AttributeError(name)

    def has(self, name: str) -> bool:
        return name in self.fields

    @property
    def line(self) -> Optional[int]:
        """1-based source line in the canonical solution, or None."""
        value = self.fields.get("line")
        return value if isinstance(value, int) and not isinstance(value, bool) else None

    @property
    def intent(self) -> Optional[str]:
        """Causal intent text (#287), or None when absent or invalid.

        Defensive mirror of the parse-time sanitization: only a non-empty
        string survives, capped at MAX_INTENT_LENGTH.
        """
        value = self.fields.get("intent")
        if not isinstance(value, str) or not value.strip():
            return None
        return value[:MAX_INTENT_LENGTH]


def _parse_payload(payload: Any) -> Optional[TraceEvent]:
    if not isinstance(payload, dict):
        return None
    kind = payload.get("event")
    if kind not in KNOWN_KINDS:
        return None
    for required in REQUIRED_FIELDS.get(kind, ()):
        if required not in payload:
            raise ValueError(f"event {kind!r} missing required field {required!r}")
    fields = dict(payload)
    fields.pop("event", None)
    # A source line is optional metadata: keep it only when it is a positive
    # int, never coerce a string/bool/zero into a misleading line number.
    line = fields.get("line")
    if isinstance(line, bool) or not isinstance(line, int) or line <= 0:
        fields.pop("line", None)
    # Intent (#287) is optional causal text: only a non-empty string is kept
    # (dropped, never coerced), capped so a long trace string can never blow
    # past AnimationStepSpec.annotation's 200-char validation downstream.
    if "intent" in fields:
        intent = fields["intent"]
        if not isinstance(intent, str) or not intent.strip():
            fields.pop("intent", None)
        elif len(intent) > MAX_INTENT_LENGTH:
            fields["intent"] = intent[:MAX_INTENT_LENGTH]
    return TraceEvent(kind, **fields)


def parse_trace(stdout: str) -> List[TraceEvent]:
    """Parse stdout into an ordered list of validated TraceEvents.

    Two trace layouts are accepted:

    - One JSON object per line ({"event": ...}), for ad-hoc debugging.
    - A single top-level JSON array of event objects — the format the traced
      solution emits (it buffers events in memory and prints one compact
      array at the end so the run stays well under the sandbox stdout cap).

    Stray lines (prints, blanks, malformed JSON, unknown event kinds) are
    skipped so a solution that also writes to stdout cannot corrupt the
    trace. A structurally invalid known event (missing a required field)
    raises ValueError because it indicates an instrumentation bug that would
    otherwise produce a silently wrong animation.
    """
    events: List[TraceEvent] = []
    if not stdout:
        return events
    for line in stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(payload, list):
            for item in payload:
                event = _parse_payload(item)
                if event is not None:
                    events.append(event)
            continue
        event = _parse_payload(payload)
        if event is not None:
            events.append(event)
    return events
