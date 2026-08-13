"""Normalization of the JSON-lines execution trace from a traced solution.

A traced canonical solution prints one JSON object per line with an "event"
key. This module parses stdout into typed TraceEvent objects and drops
anything that is not a well-formed, known event (stray prints, blank lines,
unknown event kinds) so the compiler only ever sees a clean, ordered event
stream.

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
