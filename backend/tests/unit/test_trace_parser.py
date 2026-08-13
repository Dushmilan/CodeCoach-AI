"""Unit tests for trace parsing — the JSON-lines execution trace from the
traced canonical solution is normalized into typed animation events.

The traced solution prints one JSON object per line with an "event" key
(init/compare/swap/pointer/mark/write/return). The parser must ignore stray
non-JSON output lines (e.g. a solution that also prints) and reject events
that are structurally malformed.
"""

import pytest

from app.services.trace_parser import parse_trace, TraceEvent


def _line(event, **fields):
    import json

    payload = {"event": event, **fields}
    return json.dumps(payload, separators=(",", ":"))


class TestParseTrace:
    def test_parses_structured_family_events(self):
        stdout = "\n".join(
            [
                _line("init", data=[3, 2, 1], family="linked_list"),
                _line("visit", i=0),
                _line("pointer", name="fast", index=0),
                _line("visit", i=2),
                _line("return", result=[1, 2, 3]),
            ]
        )
        events = parse_trace(stdout)
        assert [e.kind for e in events] == [
            "init",
            "visit",
            "pointer",
            "visit",
            "return",
        ]
        assert events[0].fields["data"] == [3, 2, 1]
        assert events[0].fields["family"] == "linked_list"

    def test_parses_stack_and_table_events(self):
        stdout = "\n".join(
            [
                _line("init", data="()", family="stack"),
                _line("push", value="("),
                _line("push", value=")"),
                _line("pop", value=")"),
                _line("dp_update", i=1, j=2, value=3),
                _line("window", l=0, r=3),
                _line("partition", i=2),
                _line("edge", a=0, b=2),
                _line("choose", i=1),
                _line("backtrack", i=1),
                _line("read", i=0),
                _line("return", result=True),
            ]
        )
        events = parse_trace(stdout)
        assert [e.kind for e in events] == [
            "init",
            "push",
            "push",
            "pop",
            "dp_update",
            "window",
            "partition",
            "edge",
            "choose",
            "backtrack",
            "read",
            "return",
        ]
        push = events[1]
        assert push.value == "("
        dp = events[4]
        assert dp.i == 1 and dp.j == 2 and dp.value == 3
        win = events[5]
        assert win.l == 0 and win.r == 3
        ed = events[7]
        assert ed.a == 0 and ed.b == 2
        bt = events[9]
        assert bt.i == 1

    def test_structured_events_require_their_fields(self):
        import pytest

        with pytest.raises(ValueError, match="value"):
            parse_trace(_line("push"))
        with pytest.raises(ValueError, match="value"):
            parse_trace(_line("dp_update", i=0, j=1))
        with pytest.raises(ValueError, match="l"):
            parse_trace(_line("window", r=2))
        with pytest.raises(ValueError, match="a"):
            parse_trace(_line("edge", b=1))

    def test_parses_full_bubble_sort_trace(self):
        stdout = "\n".join(
            [
                _line("init", values=[5, 1, 4, 2, 8]),
                _line("pointer", name="j", index=0),
                _line("compare", i=0, j=1),
                _line("swap", i=0, j=1),
                _line("pointer", name="j", index=1),
                _line("compare", i=1, j=2),
                _line("mark", i=4, state="sorted"),
                _line("return", result=[1, 4, 2, 5, 8]),
            ]
        )
        events = parse_trace(stdout)

        assert [e.kind for e in events] == [
            "init",
            "pointer",
            "compare",
            "swap",
            "pointer",
            "compare",
            "mark",
            "return",
        ]
        assert events[0].fields["values"] == [5, 1, 4, 2, 8]
        assert events[2].i == 0
        assert events[2].j == 1
        assert events[3].i == 0
        assert events[3].j == 1
        assert events[5].i == 1
        assert events[5].j == 2
        assert events[6].state == "sorted"
        assert events[7].fields["result"] == [1, 4, 2, 5, 8]

    def test_ignores_non_json_and_stray_output_lines(self):
        stdout = "\n".join(
            [
                "sorting the array now...",
                _line("init", values=[3, 2, 1]),
                "mid-pass",
                _line("compare", i=0, j=1),
                "",
                _line("return", result=[1, 2, 3]),
            ]
        )
        events = parse_trace(stdout)
        assert [e.kind for e in events] == ["init", "compare", "return"]

    def test_parses_single_json_array_of_events(self):
        # The traced solution prints one compact JSON array at the end.
        import json as jsonlib

        payload = [
            {"event": "init", "values": [5, 1, 4]},
            {"event": "compare", "i": 0, "j": 1},
            {"event": "swap", "i": 0, "j": 1},
            {"event": "return", "result": [1, 4, 5]},
        ]
        events = parse_trace(jsonlib.dumps(payload, separators=(",", ":")))
        assert [e.kind for e in events] == ["init", "compare", "swap", "return"]
        assert events[0].fields["values"] == [5, 1, 4]
        assert events[2].i == 0 and events[2].j == 1

    def test_array_trace_ignores_stray_prefixed_lines(self):
        import json as jsonlib

        payload = [{"event": "init", "values": [2]}, {"event": "return", "result": [2]}]
        stdout = "some banner\n" + jsonlib.dumps(payload)
        events = parse_trace(stdout)
        assert [e.kind for e in events] == ["init", "return"]

    def test_skips_unknown_event_kinds(self):
        stdout = _line("noise", foo="bar") + "\n" + _line("compare", i=0, j=1)
        events = parse_trace(stdout)
        assert [e.kind for e in events] == ["compare"]

    def test_malformed_json_line_is_skipped(self):
        stdout = "{not json}\n" + _line("compare", i=0, j=1)
        events = parse_trace(stdout)
        assert [e.kind for e in events] == ["compare"]

    def test_empty_trace_returns_empty_list(self):
        assert parse_trace("") == []
        assert parse_trace("\n\n") == []

    def test_required_index_fields_are_validated(self):
        # compare without i is structurally invalid
        with pytest.raises(ValueError, match="i"):
            parse_trace(_line("compare", j=1))


class TestTraceEvent:
    def test_typed_accessors(self):
        e = TraceEvent(kind="compare", i=2, j=3)
        assert e.i == 2
        assert e.j == 3
        assert e.has("i")

    def test_missing_optional_fields_default(self):
        e = TraceEvent(kind="mark", i=4, state="sorted")
        assert e.i == 4
        assert e.state == "sorted"
        assert e.fields.get("j") is None
