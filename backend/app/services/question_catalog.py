"""Exact question-id → algorithm mapping for the curated animation catalog.

Every question in the live 100-question Supabase inventory is pinned to one
canonical algorithm by its stable id. This exact map runs before any keyword
matching, so category names like "Binary Search" can never over-match a whole
category again — each question is resolved deterministically.

A question with a known id that the keyword scan would otherwise mis-map is
therefore always correct. Unknown ids fall through to keyword matching in
reference_solutions.resolve_algorithm.
"""

from typing import Any, Dict, Optional

QUESTION_ALGORITHMS: Dict[str, str] = {
    "add-two-numbers": "add_two_numbers",
    "balanced-binary-tree": "balanced_binary_tree",
    "best-time-to-buy-and-sell-stock": "best_time_to_buy_and_sell",
    "binary-search": "binary_search",
    "binary-tree-level-order-traversal": "binary_tree_level_order_traversal",
    "binary-tree-maximum-path-sum": "binary_tree_maximum_path_sum",
    "burst-balloons": "burst_balloons",
    "car-fleet": "car_fleet",
    "climbing-stairs": "climbing_stairs",
    "clone-graph": "clone_graph",
    "coin-change": "coin_change",
    "combination-sum": "combination_sum",
    "container-with-most-water": "container_with_most_water",
    "contains-duplicate": "contains_duplicate",
    "contiguous-array": "contiguous_array",
    "course-schedule": "course_schedule",
    "course-schedule-ii": "course_schedule_ii",
    "daily-temperatures": "daily_temperatures",
    "decode-ways": "decode_ways",
    "edit-distance": "edit_distance",
    "evaluate-reverse-polish-notation": "evaluate_reverse_polish_notation",
    "find-all-duplicates-in-an-array": "find_all_duplicates",
    "find-first-and-last-position-in-sorted-array": "find_first_and_last",
    "find-minimum-in-rotated-sorted-array": "find_minimum_in_rotated",
    "find-the-duplicate-number": "find_the_duplicate_number",
    "first-missing-positive": "first_missing_positive",
    "c9d1a3f2-5b6e-4a7f-8c0d-1e2f3a4b5c6d": "first_word",
    "gas-station": "gas_station",
    "generate-parentheses": "generate_parentheses",
    "group-anagrams": "group_anagrams",
    "hand-of-straights": "hand_of_straights",
    "happy-number": "happy_number",
    "house-robber": "house_robber",
    "invert-binary-tree": "invert_binary_tree",
    "is-subsequence": "is_subsequence",
    "jump-game": "jump_game",
    "jump-game-ii": "jump_game_ii",
    "k-closest-points-to-origin": "k_closest",
    "koko-eating-bananas": "koko_eating_bananas",
    "kth-largest-element-in-an-array": "kth_largest",
    "kth-smallest-element-in-a-bst": "kth_smallest_element_in_a_bst",
    "largest-rectangle-in-histogram": "largest_rectangle_in_histogram",
    "linked-list-cycle": "linked_list_cycle",
    "longest-common-prefix": "longest_common_prefix",
    "longest-consecutive-sequence": "longest_consecutive_sequence",
    "longest-increasing-subsequence": "longest_increasing_subsequence",
    "longest-repeating-character-replacement": "longest_repeating_character_replacement",
    "longest-substring-without-repeating-characters": "longest_substring_without_repeating",
    "longest-valid-parentheses": "longest_valid_parentheses",
    "lowest-common-ancestor-of-a-binary-tree": "lowest_common_ancestor",
    "majority-element": "majority_element",
    "maximum-depth-of-binary-tree": "maximum_depth_of_binary_tree",
    "maximum-product-subarray": "maximum_product_subarray",
    "median-of-two-sorted-arrays": "median_of_two_sorted_arrays",
    "merge-intervals": "merge_intervals",
    "merge-k-sorted-lists": "merge_k_sorted_lists",
    "merge-two-sorted-lists": "merge_two_sorted_lists",
    "min-stack": "min_stack",
    "minimum-window-substring": "minimum_window_substring",
    "missing-number": "missing_number",
    "7b9d2c1a-3e4f-5a6b-7c8d-9e0f1a2b3c4d": "most_frequent_char",
    "move-zeroes": "move_zeroes",
    "next-permutation": "next_permutation",
    "non-overlapping-intervals": "non_overlapping_intervals",
    "number-of-1-bits": "number_of_1_bits",
    "number-of-islands": "number_of_islands",
    "partition-labels": "partition_labels",
    "permutation-in-string": "permutation_in_string",
    "permutations": "permutations",
    "power-of-two": "power_of_two",
    "product-of-array-except-self": "product_of_array_except_self",
    "ransom-note": "ransom_note",
    "remove-nth-node-from-end-of-list": "remove_nth_node_from_end",
    "reorder-list": "reorder_list",
    "reverse-integer": "reverse_integer",
    "reverse-linked-list": "reverse_linked_list",
    "reverse-string": "reverse_string",
    "rotate-image": "rotate_image",
    "same-tree": "same_tree",
    "search-in-rotated-sorted-array": "search_in_rotated",
    "search-insert-position": "search_insert_position",
    "single-number": "single_number",
    "sliding-window-maximum": "sliding_window_maximum",
    "subarray-sum-equals-k": "subarray_sum_equals_k",
    "subsets": "subsets",
    "task-scheduler": "task_scheduler",
    "three-sum": "three_sum",
    "three-sum-closest": "three_sum_closest",
    "top-k-frequent-elements": "top_k_frequent",
    "trapping-rain-water": "trapping_rain_water",
    "two-sum": "two_sum",
    "two-sum-ii-input-array-is-sorted": "two_sum_ii",
    "valid-anagram": "valid_anagram",
    "f7e2d4a1-3b5c-4d6e-8f9a-0b1c2d3e4f5a": "valid_palindrome",
    "valid-palindrome": "valid_palindrome",
    "valid-parentheses": "valid_parentheses",
    "validate-binary-search-tree": "validate_binary_search_tree",
    "word-break": "word_break",
    "word-ladder": "word_ladder",
    "word-search": "word_search",
}


def resolve_by_id(question: Optional[Dict[str, Any]]) -> Optional[str]:
    """Return the algorithm pinned to the question's id, or None."""
    if not isinstance(question, dict):
        return None
    qid = question.get("id")
    if isinstance(qid, str):
        return QUESTION_ALGORITHMS.get(qid)
    return None
