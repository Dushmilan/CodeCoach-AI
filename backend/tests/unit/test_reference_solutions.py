"""Unit tests for the curated reference-solution catalog and the resolver."""

from app.services.reference_solutions import (
    REFERENCE_SOLUTIONS,
    FAMILIES,
    get_reference_solution,
    resolve_algorithm,
)


def _question(title="", category="", description="", qid=None):
    return {
        "id": qid,
        "title": title,
        "category": category,
        "description": description,
        "examples": [{"input": "[5,1,4,2,8]", "output": "[1,2,4,5,8]"}],
    }


class TestResolveAlgorithm:
    def test_exact_question_id_takes_precedence(self):
        # "binary-search" id must win even though the category says binary search.
        q = _question(
            qid="koko-eating-bananas",
            title="Koko Eating Bananas",
            category="Binary Search",
        )
        assert resolve_algorithm(q) == "koko_eating_bananas"

    def test_matches_by_title(self):
        assert resolve_algorithm(_question(title="Bubble Sort")) == "bubble_sort"

    def test_matches_by_description(self):
        assert (
            resolve_algorithm(_question(description="Solve Two Sum efficiently"))
            == "two_sum"
        )

    def test_case_insensitive(self):
        assert resolve_algorithm(_question(title="bubble sort")) == "bubble_sort"

    def test_category_no_longer_over_matches(self):
        # A category-only "Binary Search" question without a known id and no
        # binary-search keywords elsewhere must not resolve to plain binary_search.
        assert (
            resolve_algorithm(_question(category="Binary Search", title="Weird"))
            == "binary_search"
        )

    def test_unknown_returns_none(self):
        assert resolve_algorithm(_question(title="Weird made-up problem")) is None

    def test_non_dict_question_returns_none(self):
        assert resolve_algorithm(None) is None
        assert resolve_algorithm("not a dict") is None


class TestReferenceSolutions:
    def test_catalog_is_large_enough_for_inventory(self):
        assert len(REFERENCE_SOLUTIONS) >= 80

    def test_every_entry_has_required_fields(self):
        for algo, entry in REFERENCE_SOLUTIONS.items():
            assert entry["family"] in FAMILIES, f"{algo} bad family"
            assert entry["function"], f"{algo} needs function"
            assert entry["signature"], f"{algo} needs signature"
            assert entry["primary"], f"{algo} needs primary"
            assert entry["match_keys"], f"{algo} needs match_keys"
            assert f"def {entry['function']}(" in entry["code"], (
                f"{algo} must define its function"
            )
            assert "__trace(" in entry["code"], f"{algo} must be traced"
            assert '__trace("init"' in entry["code"], f"{algo} must emit its own init"

    def test_every_signature_param_is_used_by_name(self):
        for algo, entry in REFERENCE_SOLUTIONS.items():
            fn = entry["function"]
            sig = entry["signature"]
            for param in sig:
                assert f"def {fn}(" in entry["code"]
                assert param in entry["code"], f"{algo} signature param {param} unused"

    def test_get_reference_solution(self):
        entry = get_reference_solution("bubble_sort")
        assert entry["function"] == "bubble_sort"
        assert get_reference_solution("nope") is None

    def test_bubble_sort_is_traced_and_optimal(self):
        entry = get_reference_solution("bubble_sort")
        code = entry["code"]
        assert "for j in range(n - i - 1)" in code
        assert '__trace("compare"' in code
        assert '__trace("swap"' in code
        assert '__trace("mark"' in code

    def test_every_catalog_function_runs_on_a_small_input(self):
        """Smoke-run representative canonical solutions locally per family."""
        import io
        import json
        import sys

        from app.services.trace_instrumenter import wrap_traced_solution
        from app.services.trace_parser import parse_trace

        samples = {
            "bubble_sort": {"values": [5, 1, 4, 2, 8]},
            "binary_search": {"nums": [1, 3, 5, 7, 9], "target": 7},
            "two_sum": {"nums": [2, 7, 11, 15], "target": 9},
            "contains_duplicate": {"nums": [1, 2, 3, 1]},
            "climbing_stairs": {"n": 5},
            "valid_parentheses": {"s": "(()))"},
            "reverse_linked_list": {"head": [1, 2, 3]},
            "maximum_depth_of_binary_tree": {"root": [3, 9, 20, None, None, 15, 7]},
            "rotate_image": {"matrix": [[1, 2], [3, 4]]},
            "clone_graph": {"adj": [[2], [1]]},
            "merge_intervals": {"intervals": [[1, 3], [2, 6]]},
            "subsets": {"nums": [1, 2]},
            "valid_palindrome": {"s": "A man, a plan"},
            "number_of_1_bits": {"n": "1011"},
        }
        for algo, sample in samples.items():
            entry = REFERENCE_SOLUTIONS[algo]
            code = wrap_traced_solution(entry["code"], entry["function"])
            old_stdin, old_stdout = sys.stdin, sys.stdout
            buf = io.StringIO()
            try:
                sys.stdin = io.StringIO(json.dumps(sample))
                sys.stdout = buf
                exec(compile(code, "<wrapped>", "exec"), {})
            finally:
                sys.stdin, sys.stdout = old_stdin, old_stdout
            events = parse_trace(buf.getvalue())
            assert events, f"{algo} produced no events"
            assert events[0].kind == "init", f"{algo} missing init"
            assert events[-1].kind == "return", f"{algo} missing return"


def _run_scoped_solution(algo: str, sample: dict):
    """Run a catalog solution through the real wrap→exec→parse chain."""
    import io
    import json
    import sys

    from app.services.trace_instrumenter import wrap_traced_solution
    from app.services.trace_parser import parse_trace

    entry = REFERENCE_SOLUTIONS[algo]
    code = wrap_traced_solution(entry["code"], entry["function"])
    old_stdin, old_stdout = sys.stdin, sys.stdout
    buf = io.StringIO()
    try:
        sys.stdin = io.StringIO(json.dumps(sample))
        sys.stdout = buf
        exec(compile(code, "<wrapped>", "exec"), {})
    finally:
        sys.stdin, sys.stdout = old_stdin, old_stdout
    return parse_trace(buf.getvalue())


# Snapshot of each scoped solution's trace taken before #287 landed, with
# only the (then non-existent) `intent` field stripped. Kinds, order, every
# payload value AND every `line` must stay byte-identical — string intent
# fields never enter the __CODE_OFFSET line path.
_SCOPED_SAMPLES = {
    "binary_search": {"nums": [1, 3, 5, 7, 9], "target": 7},
    "linear_search": {"values": [5, 1, 4], "target": 4},
    "two_sum_ii": {"numbers": [2, 7, 11, 15], "target": 9},
    "longest_substring_without_repeating": {"s": "abcabcbb"},
}


def _ev(event, line=None, **fields):
    payload = {"event": event, **fields}
    if line is not None:
        payload["line"] = line
    return payload


_SCOPED_GOLDENS = {
    "binary_search": [
        _ev("init", 2, values=[1, 3, 5, 7, 9], family="array"),
        _ev("pointer", 6, name="low", index=0),
        _ev("pointer", 7, name="high", index=4),
        _ev("pointer", 8, name="mid", index=2),
        _ev("compare", 9, i=2),
        _ev("pointer", 6, name="low", index=3),
        _ev("pointer", 7, name="high", index=4),
        _ev("pointer", 8, name="mid", index=3),
        _ev("compare", 9, i=3),
        _ev("mark", 11, i=3, state="match"),
        _ev("return", result=3),
    ],
    "linear_search": [
        _ev("init", 2, values=[5, 1, 4], family="array"),
        _ev("pointer", 4, name="i", index=0),
        _ev("compare", 5, i=0),
        _ev("pointer", 4, name="i", index=1),
        _ev("compare", 5, i=1),
        _ev("pointer", 4, name="i", index=2),
        _ev("compare", 5, i=2),
        _ev("mark", 7, i=2, state="match"),
        _ev("return", result=2),
    ],
    "two_sum_ii": [
        _ev("init", 2, values=[2, 7, 11, 15], family="array"),
        _ev("pointer", 5, name="l", index=0),
        _ev("pointer", 6, name="r", index=3),
        _ev("compare", 7, i=0, j=3),
        _ev("pointer", 5, name="l", index=0),
        _ev("pointer", 6, name="r", index=2),
        _ev("compare", 7, i=0, j=2),
        _ev("pointer", 5, name="l", index=0),
        _ev("pointer", 6, name="r", index=1),
        _ev("compare", 7, i=0, j=1),
        _ev("mark", 10, i=0, state="match"),
        _ev("mark", 11, i=1, state="match"),
        _ev("return", result=[1, 2]),
    ],
    "longest_substring_without_repeating": [
        _ev("init", 2, values=["a", "b", "c", "a", "b", "c", "b", "b"], family="array"),
        _ev("window", 10, l=0, r=0),
        _ev("pointer", 11, name="r", index=0),
        _ev("window", 10, l=0, r=1),
        _ev("pointer", 11, name="r", index=1),
        _ev("window", 10, l=0, r=2),
        _ev("pointer", 11, name="r", index=2),
        _ev("window", 10, l=1, r=3),
        _ev("pointer", 11, name="r", index=3),
        _ev("window", 10, l=2, r=4),
        _ev("pointer", 11, name="r", index=4),
        _ev("window", 10, l=3, r=5),
        _ev("pointer", 11, name="r", index=5),
        _ev("window", 10, l=5, r=6),
        _ev("pointer", 11, name="r", index=6),
        _ev("window", 10, l=7, r=7),
        _ev("pointer", 11, name="r", index=7),
        _ev("return", result=3),
    ],
}


class TestDecisionIntent:
    """#287: pointer-decision reference solutions emit real causal intent.

    Scope (deliberately NOT all 103 solutions): binary-search,
    linear-search, two-pointer and sliding-window style decisions — the
    families where "why did the pointer/window move" is the pedagogy.
    Every intent string is computed from live runtime values inside the
    traced solution; nothing here is hardcoded narration.
    """

    def test_binary_search_compares_carry_the_real_direction(self):
        events = _run_scoped_solution("binary_search", _SCOPED_SAMPLES["binary_search"])
        compares = [e for e in events if e.kind == "compare"]
        assert [c.intent for c in compares] == [
            "5 < 7 → search right →",
            "7 = 7 → found",
        ]

    def test_linear_search_compares_carry_match_or_scan(self):
        events = _run_scoped_solution("linear_search", _SCOPED_SAMPLES["linear_search"])
        compares = [e for e in events if e.kind == "compare"]
        assert [c.intent for c in compares] == [
            "5 ≠ 4 → keep scanning",
            "1 ≠ 4 → keep scanning",
            "4 = 4 → found",
        ]

    def test_two_sum_ii_compares_narrate_the_real_sum(self):
        events = _run_scoped_solution("two_sum_ii", _SCOPED_SAMPLES["two_sum_ii"])
        compares = [e for e in events if e.kind == "compare"]
        assert [c.intent for c in compares] == [
            "sum 17 > 9 → move right pointer left",
            "sum 13 > 9 → move right pointer left",
            "sum 9 = 9 → match at [0,1]",
        ]

    def test_sliding_window_annotates_only_the_shrinks(self):
        events = _run_scoped_solution(
            "longest_substring_without_repeating",
            _SCOPED_SAMPLES["longest_substring_without_repeating"],
        )
        windows = [e for e in events if e.kind == "window"]
        annotated = [w for w in windows if w.intent is not None]
        # The decision is the shrink — a window that merely grew stays silent.
        assert len(windows) == 8
        assert [w.intent for w in annotated] == [
            "'a' repeats at [0] → window now [1..3]",
            "'b' repeats at [1] → window now [2..4]",
            "'c' repeats at [2] → window now [3..5]",
            "'b' repeats at [4] → window now [5..6]",
            "'b' repeats at [6] → window now [7..7]",
        ]

    def test_non_decision_events_never_carry_intent(self):
        for algo, sample in _SCOPED_SAMPLES.items():
            events = _run_scoped_solution(algo, sample)
            for event in events:
                if event.kind in ("compare", "window"):
                    continue
                assert event.intent is None, f"{algo} {event.kind} has intent"

    def test_payloads_stay_byte_identical_apart_from_intent(self):
        for algo, sample in _SCOPED_SAMPLES.items():
            events = _run_scoped_solution(algo, sample)
            slim = [
                {k: v for k, v in e.fields.items() if k != "intent"} | {"event": e.kind}
                for e in events
            ]
            # Dict/list equality is deep and key-order-insensitive: kinds,
            # order, payload values and `line` must all match the snapshot.
            assert slim == _SCOPED_GOLDENS[algo], (
                f"{algo} trace changed beyond the intent field"
            )


class TestMaximumDepthOfBinaryTree:
    def _depth_of(self, root):
        import io
        import json
        import sys

        from app.services.trace_instrumenter import wrap_traced_solution
        from app.services.trace_parser import parse_trace

        entry = REFERENCE_SOLUTIONS["maximum_depth_of_binary_tree"]
        code = wrap_traced_solution(entry["code"], entry["function"])
        old_stdin, old_stdout = sys.stdin, sys.stdout
        buf = io.StringIO()
        try:
            sys.stdin = io.StringIO(json.dumps({"root": root}))
            sys.stdout = buf
            exec(compile(code, "<wrapped>", "exec"), {})
        finally:
            sys.stdin, sys.stdout = old_stdin, old_stdout
        events = parse_trace(buf.getvalue())
        return events[-1].result

    def test_single_node_tree_depth_is_one(self):
        assert self._depth_of([3]) == 1

    def test_depth_counts_levels_from_root(self):
        # indices 0,1,2,5,6 → depths 1,2,2,3,3
        assert self._depth_of([3, 9, 20, None, None, 15, 7]) == 3

    def test_depth_of_leftmost_leaf_at_index_7(self):
        # index 7 is depth 4; i.bit_length()=3 would undercount it.
        assert self._depth_of([3, 9, 20, 15, 7, 15, 7, 1]) == 4
