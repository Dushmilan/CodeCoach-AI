"""Unit tests for the exact question-id → algorithm taxonomy."""

from app.services.question_catalog import QUESTION_ALGORITHMS, resolve_by_id
from app.services.reference_solutions import REFERENCE_SOLUTIONS
from app.services.reference_solutions import resolve_algorithm


class TestQuestionCatalog:
    def test_inventory_has_expected_size(self):
        assert len(QUESTION_ALGORITHMS) == 100

    def test_every_question_maps_to_a_known_algorithm(self):
        for qid, algo in QUESTION_ALGORITHMS.items():
            assert algo in REFERENCE_SOLUTIONS, f"{qid} -> unknown {algo}"

    def test_every_algorithm_has_its_own_signature(self):
        # Each algorithm is distinct; two questions can share one algorithm but
        # every algorithm key must be unique in the catalog.
        assert len(set(QUESTION_ALGORITHMS.values())) >= 75

    def test_all_families_are_represented(self):
        families = {
            REFERENCE_SOLUTIONS[a]["family"] for a in QUESTION_ALGORITHMS.values()
        }
        for expected in (
            "array",
            "stack",
            "linked_list",
            "tree",
            "grid",
            "graph",
            "intervals",
            "backtrack",
        ):
            assert expected in families, f"family {expected} has no questions"

    def test_resolve_by_id(self):
        assert resolve_by_id({"id": "two-sum"}) == "two_sum"
        assert resolve_by_id({"id": "koko-eating-bananas"}) == "koko_eating_bananas"
        assert resolve_by_id({"id": "unknown-thing"}) is None
        assert resolve_by_id(None) is None
        assert resolve_by_id({"title": "Two Sum"}) is None

    def test_resolve_algorithm_prefers_id_over_keywords(self):
        # koko is in the Binary Search category: id must win over category scan.
        q = {
            "id": "koko-eating-bananas",
            "title": "Koko Eating Bananas",
            "category": "Binary Search",
            "description": "There are n piles of bananas...",
        }
        assert resolve_algorithm(q) == "koko_eating_bananas"

    def test_categories_no_longer_over_match(self):
        # A question whose id is unknown but title/category are generic must not
        # be silently mis-mapped; keyword fallback still applies.
        q = {
            "id": "zzz-unknown",
            "title": "Array warm-up",
            "category": "Binary Search",
            "description": "Sort the values then check the median.",
        }
        assert resolve_algorithm(q) == "binary_search"
