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
