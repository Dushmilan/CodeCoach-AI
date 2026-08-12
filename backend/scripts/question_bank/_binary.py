"""Binary Search questions."""

from __future__ import annotations

from typing import List

from ._helpers import make_spec

SPECS = [
    make_spec(
        id="binary-search",
        title="Binary Search",
        difficulty="easy",
        category="Binary Search",
        companies=["Amazon", "Google", "Microsoft", "Apple", "Facebook"],
        description="Given an array of integers `nums` which is sorted in ascending order, and an integer `target`, write a function to search `target` in `nums`.\n\nIf `target` exists, return its index; otherwise, return `-1`.\n\nYou must write an algorithm with O(log n) runtime complexity.\n\n**Constraints**\n- 1 <= nums.length <= 10^4\n- -10^4 < nums[i], target < 10^4\n- All the integers in nums are unique.\n- nums is sorted in ascending order.",
        examples=[
            {
                "input": "nums = [-1,0,3,5,9,12], target = 9",
                "output": "4",
                "explanation": "9 exists in nums and its index is 4.",
            },
            {
                "input": "nums = [-1,0,3,5,9,12], target = 2",
                "output": "-1",
                "explanation": "2 does not exist in nums.",
            },
        ],
        tests=[
            (([-1, 0, 3, 5, 9, 12], 9), False),
            (([-1, 0, 3, 5, 9, 12], 2), False),
            (([5], 5), False),
            (([5], 4), False),
            (([1, 2, 3, 4, 5], 1), False),
            (([1, 2, 3, 4, 5], 5), False),
            (([-5, -2, 0, 3, 8], -2), False),
            (([1, 3, 5, 7, 9], 6), False),
            (([2, 4, 6, 8, 10, 12, 14], 14), True),
            (([10, 20, 30, 40, 50], 30), True),
        ],
        ref=lambda nums, target: _binary_search(nums, target),
        starter={
            "python": "def search(nums: List[int], target: int) -> int:\n    pass",
            "javascript": "function search(nums, target) {\n    // your code here\n}",
            "java": "class Solution {\n    public int search(int[] nums, int target) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Set lo and hi to the array bounds.",
            "Compare the middle element with the target and halve the search space.",
            "Update lo/hi while lo <= hi.",
        ],
        solution="Standard binary search: while lo <= hi, compute mid, and if nums[mid] == target return mid; if nums[mid] < target search the right half, else the left half. Return -1 if not found.",
        time_complexity="O(log n)",
        space_complexity="O(1)",
        constraints=["1 <= nums.length <= 10^4", "nums is sorted in ascending order"],
    ),
    make_spec(
        id="search-insert-position",
        title="Search Insert Position",
        difficulty="easy",
        category="Binary Search",
        companies=["Amazon", "Google", "Facebook", "Microsoft", "Apple"],
        description="Given a sorted array of distinct integers and a target value, return the index if the target is found. If not, return the index where it would be if it were inserted in order.\n\nYou must write an algorithm with O(log n) runtime complexity.\n\n**Constraints**\n- 1 <= nums.length <= 10^4\n- -10^4 <= nums[i] <= 10^4\n- nums contains distinct values sorted in ascending order.",
        examples=[
            {
                "input": "nums = [1,3,5,6], target = 5",
                "output": "2",
                "explanation": "5 exists at index 2.",
            },
            {
                "input": "nums = [1,3,5,6], target = 2",
                "output": "1",
                "explanation": "2 would be inserted at index 1.",
            },
            {
                "input": "nums = [1,3,5,6], target = 7",
                "output": "4",
                "explanation": "7 would be appended at the end.",
            },
        ],
        tests=[
            (([1, 3, 5, 6], 5), False),
            (([1, 3, 5, 6], 2), False),
            (([1, 3, 5, 6], 7), False),
            (([1, 3, 5, 6], 0), False),
            (([1], 0), False),
            (([1], 2), False),
            (([2, 5, 8, 10], 8), False),
            (([2, 5, 8, 10], 4), False),
            (([-10, -5, 0, 5], -1), True),
            (([3, 6, 9, 12], 13), True),
        ],
        ref=lambda nums, target: _search_insert(nums, target),
        starter={
            "python": "def searchInsert(nums: List[int], target: int) -> int:\n    pass",
            "javascript": "function searchInsert(nums, target) {\n    // your code here\n}",
            "java": "class Solution {\n    public int searchInsert(int[] nums, int target) {\n        // your code here\n    }\n}",
        },
        hints=[
            "This is binary search where the loop ends with lo == insertion point.",
            "Search for the first position where nums[mid] >= target.",
        ],
        solution="Binary search maintaining lo and hi. The loop finds the leftmost position where the target fits; lo ends up being the insert index whether or not the target exists.",
        time_complexity="O(log n)",
        space_complexity="O(1)",
        constraints=["1 <= nums.length <= 10^4"],
    ),
    make_spec(
        id="find-first-and-last-position-in-sorted-array",
        title="Find First and Last Position of Element in Sorted Array",
        difficulty="medium",
        category="Binary Search",
        companies=["Amazon", "Microsoft", "Facebook", "Google"],
        description="Given an array of integers `nums` sorted in non-decreasing order, find the starting and ending position of a given `target` value.\n\nIf `target` is not found in the array, return `[-1, -1]`.\n\nYou must write an algorithm with O(log n) runtime complexity.\n\n**Constraints**\n- 0 <= nums.length <= 10^5\n- -10^9 <= nums[i] <= 10^9\n- nums is a non-decreasing array.",
        examples=[
            {
                "input": "nums = [5,7,7,8,8,10], target = 8",
                "output": "[3,4]",
                "explanation": "8 appears at indices 3 and 4.",
            },
            {
                "input": "nums = [5,7,7,8,8,10], target = 6",
                "output": "[-1,-1]",
                "explanation": "6 does not appear.",
            },
            {
                "input": "nums = [], target = 0",
                "output": "[-1,-1]",
                "explanation": "Empty array.",
            },
        ],
        tests=[
            (([5, 7, 7, 8, 8, 10], 8), False),
            (([5, 7, 7, 8, 8, 10], 6), False),
            (([], 0), False),
            (([1], 1), False),
            (([2, 2], 2), False),
            (([1, 2, 2, 3, 3, 3, 4], 3), False),
            (([1, 2, 3], 4), False),
            (([1, 2, 3], 0), False),
            (([3, 3, 3, 3, 3], 3), True),
            (([1, 5, 5, 5, 5, 7], 5), True),
        ],
        ref=lambda nums, target: _search_range(nums, target),
        starter={
            "python": "def searchRange(nums: List[int], target: int) -> List[int]:\n    pass",
            "javascript": "function searchRange(nums, target) {\n    // your code here\n}",
            "java": "class Solution {\n    public int[] searchRange(int[] nums, int target) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Find the first occurrence and the last occurrence with two binary searches.",
            "Use a helper that finds the leftmost index where nums[i] >= target.",
        ],
        solution="Write a helper that returns the leftmost index where nums[index] >= target. The first occurrence is leftmost(nums, target); the last occurrence is leftmost(nums, target+1) - 1. Validate the indices against the array.",
        time_complexity="O(log n)",
        space_complexity="O(1)",
        constraints=["0 <= nums.length <= 10^5"],
    ),
    make_spec(
        id="search-in-rotated-sorted-array",
        title="Search in Rotated Sorted Array",
        difficulty="medium",
        category="Binary Search",
        companies=["Amazon", "Google", "Microsoft", "Apple", "Facebook"],
        description="There is an integer array `nums` sorted in ascending order (with distinct values) that has been rotated at an unknown pivot.\n\nGiven the array `nums` after the rotation and an integer `target`, return the index of `target` if it is in `nums`, or `-1` if it is not.\n\nYou must write an algorithm with O(log n) runtime complexity.\n\n**Constraints**\n- 1 <= nums.length <= 5000\n- -10^4 <= nums[i] <= 10^4\n- All values of nums are unique.",
        examples=[
            {
                "input": "nums = [4,5,6,7,0,1,2], target = 0",
                "output": "4",
                "explanation": "0 is at index 4.",
            },
            {
                "input": "nums = [4,5,6,7,0,1,2], target = 3",
                "output": "-1",
                "explanation": "3 is not present.",
            },
            {
                "input": "nums = [1], target = 0",
                "output": "-1",
                "explanation": "Single element array.",
            },
        ],
        tests=[
            (([4, 5, 6, 7, 0, 1, 2], 0), False),
            (([4, 5, 6, 7, 0, 1, 2], 3), False),
            (([1], 0), False),
            (([1, 3], 3), False),
            (([3, 1], 1), False),
            (([5, 1, 2, 3, 4], 1), False),
            (([5, 1, 2, 3, 4], 5), False),
            (([2, 3, 4, 5, 6, 7, 8, 9, 1], 9), False),
            (([6, 7, 1, 2, 3, 4, 5], 6), True),
            (([4, 5, 6, 7, 0, 1, 2], 5), True),
            (([1, 2, 3, 4, 5, 6], 4), True),
        ],
        ref=lambda nums, target: _search_rotated(nums, target),
        starter={
            "python": "def search(nums: List[int], target: int) -> int:\n    pass",
            "javascript": "function search(nums, target) {\n    // your code here\n}",
            "java": "class Solution {\n    public int search(int[] nums, int target) {\n        // your code here\n    }\n}",
        },
        hints=[
            "One half of the array is always sorted.",
            "Decide which half could contain the target using the sorted half's bounds.",
        ],
        solution="Binary search comparing the middle element to nums[lo] to determine whether the left or right segment is sorted, then narrowing toward the segment that can contain the target.",
        time_complexity="O(log n)",
        space_complexity="O(1)",
        constraints=["1 <= nums.length <= 5000", "All values of nums are unique"],
    ),
    make_spec(
        id="find-minimum-in-rotated-sorted-array",
        title="Find Minimum in Rotated Sorted Array",
        difficulty="medium",
        category="Binary Search",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="Suppose an array of length `n` sorted in ascending order is rotated between 1 and n times. Given the rotated array `nums` of unique elements, return the minimum element of this array.\n\nYou must write an algorithm that runs in O(log n) time.\n\n**Constraints**\n- n == nums.length\n- 1 <= n <= 5000\n- All values are unique.",
        examples=[
            {
                "input": "nums = [3,4,5,1,2]",
                "output": "1",
                "explanation": "The minimum is 1.",
            },
            {
                "input": "nums = [4,5,6,7,0,1,2]",
                "output": "0",
                "explanation": "The minimum is 0.",
            },
            {
                "input": "nums = [11,13,15,17]",
                "output": "11",
                "explanation": "The array is not rotated, so 11 is the minimum.",
            },
        ],
        tests=[
            (([3, 4, 5, 1, 2],), False),
            (([4, 5, 6, 7, 0, 1, 2],), False),
            (([11, 13, 15, 17],), False),
            (([1],), False),
            (([2, 1],), False),
            (([5, 1, 2, 3, 4],), False),
            (([1, 2, 3, 4, 5],), False),
            (([2, 3, 4, 5, 6, 1],), True),
            (([10, 20, 30, 5, 7],), True),
        ],
        ref=lambda *args: _find_min(*args),
        starter={
            "python": "def findMin(nums: List[int]) -> int:\n    pass",
            "javascript": "function findMin(nums) {\n    // your code here\n}",
            "java": "class Solution {\n    public int findMin(int[] nums) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Compare the middle element with the right boundary.",
            "If nums[mid] > nums[right], the pivot is in the right half; otherwise search the left half.",
        ],
        solution="Binary search: while lo < hi, if nums[mid] > nums[hi] the minimum is in the right half (lo = mid+1); otherwise it is in the left half (hi = mid). Return nums[lo].",
        time_complexity="O(log n)",
        space_complexity="O(1)",
        constraints=["n == nums.length", "1 <= n <= 5000", "All values are unique"],
    ),
    make_spec(
        id="koko-eating-bananas",
        title="Koko Eating Bananas",
        difficulty="hard",
        category="Binary Search",
        companies=["Amazon", "Google", "Microsoft", "Apple"],
        description="Koko loves to eat bananas. There are `n` piles of bananas, the i-th pile has `piles[i]` bananas. The guards have gone and will come back in `h` hours.\n\nKoko can decide her bananas-per-hour eating speed of `k`. Each hour, she chooses some pile of bananas and eats `k` bananas from that pile. If the pile has less than `k` bananas, she eats all of them instead and will not eat any more bananas during this hour.\n\nReturn the minimum integer `k` such that she can eat all the bananas within `h` hours.\n\n**Constraints**\n- 1 <= piles.length <= 10^4\n- piles.length <= h <= 10^9\n- 1 <= piles[i] <= 10^9",
        examples=[
            {
                "input": "piles = [3,6,7,11], h = 8",
                "output": "4",
                "explanation": "At speed 4 she finishes in ceil(3/4)+ceil(6/4)+ceil(7/4)+ceil(11/4) = 8 hours.",
            },
            {
                "input": "piles = [30,11,23,4,20], h = 5",
                "output": "30",
                "explanation": "At speed 30 she finishes every pile in one hour.",
            },
            {
                "input": "piles = [30,11,23,4,20], h = 6",
                "output": "23",
                "explanation": "At speed 23 she finishes in 6 hours.",
            },
        ],
        tests=[
            (([3, 6, 7, 11], 8), False),
            (([30, 11, 23, 4, 20], 5), False),
            (([30, 11, 23, 4, 20], 6), False),
            (([1], 1), False),
            (([2, 2], 2), False),
            (([5, 5, 5], 5), False),
            (([1, 1, 1, 1], 4), False),
            (([10, 20, 30], 10), False),
            (([3, 6, 7, 11], 7), True),
            (([1000000000], 2), True),
        ],
        ref=lambda piles, h: _min_eating_speed(piles, h),
        starter={
            "python": "def minEatingSpeed(piles: List[int], h: int) -> int:\n    pass",
            "javascript": "function minEatingSpeed(piles, h) {\n    // your code here\n}",
            "java": "class Solution {\n    public int minEatingSpeed(int[] piles, int h) {\n        // your code here\n    }\n}",
        },
        hints=[
            "For a speed k, the hours needed per pile is ceil(piles[i] / k).",
            "Binary search the speed between 1 and the largest pile.",
        ],
        solution="Binary search over the speed k from 1 to max(piles). For each k compute total hours as sum of ceil(piles[i]/k). If the total is <= h, try a smaller speed; otherwise increase. Return the smallest feasible speed.",
        time_complexity="O(n log max(piles))",
        space_complexity="O(1)",
        constraints=["1 <= piles.length <= 10^4", "piles.length <= h <= 10^9"],
    ),
    make_spec(
        id="median-of-two-sorted-arrays",
        title="Median of Two Sorted Arrays",
        difficulty="hard",
        category="Binary Search",
        companies=["Google", "Amazon", "Microsoft", "Facebook", "Apple"],
        description="Given two sorted arrays `nums1` and `nums2` of size m and n respectively, return the median of the two sorted arrays.\n\nThe overall run time complexity should be O(log (m+n)).\n\n**Constraints**\n- nums1.length == m, nums2.length == n\n- 0 <= m <= 1000, 0 <= n <= 1000\n- 1 <= m + n <= 2000\n- -10^6 <= nums1[i], nums2[i] <= 10^6",
        examples=[
            {
                "input": "nums1 = [1,3], nums2 = [2]",
                "output": "2.0",
                "explanation": "The merged array is [1,2,3] with median 2.",
            },
            {
                "input": "nums1 = [1,2], nums2 = [3,4]",
                "output": "2.5",
                "explanation": "The merged array is [1,2,3,4] with median (2+3)/2 = 2.5.",
            },
        ],
        tests=[
            (([1, 3], [2]), False),
            (([1, 2], [3, 4]), False),
            (([0, 0], [0, 0]), False),
            (([], [1]), False),
            (([2], []), False),
            (([1, 3, 5], [2, 4, 6]), False),
            (([1, 2, 3, 4, 5], [6, 7, 8, 9, 10]), False),
            (([1], [2, 3, 4, 5, 6]), False),
            (([1, 2, 3], []), True),
            (([], [1, 2, 3, 4, 5]), True),
            (([1, 4, 5], [2, 3, 6, 7, 8]), True),
        ],
        ref=lambda nums1, nums2: _find_median(nums1, nums2),
        starter={
            "python": "def findMedianSortedArrays(nums1: List[int], nums2: List[int]) -> float:\n    pass",
            "javascript": "function findMedianSortedArrays(nums1, nums2) {\n    // your code here\n}",
            "java": "class Solution {\n    public double findMedianSortedArrays(int[] nums1, int[] nums2) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Partition the smaller array so the left partition total is half.",
            "Use the partition sizes to derive the matching cut in the other array.",
            "Check the cross-boundary ordering to validate the partition.",
        ],
        solution="Binary search a partition in the smaller array such that every element on the left of both arrays is <= every element on the right. The median is computed from the max of the left sides and min of the right sides, handling even/odd total lengths.",
        time_complexity="O(log(min(m, n)))",
        space_complexity="O(1)",
        constraints=["1 <= m + n <= 2000"],
    ),
]


def _binary_search(nums: List[int], target: int) -> int:
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


def _search_insert(nums: List[int], target: int) -> int:
    lo, hi = 0, len(nums)
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] >= target:
            hi = mid
        else:
            lo = mid + 1
    return lo


def _search_range(nums: List[int], target: int) -> List[int]:
    def leftmost(val: int) -> int:
        lo, hi = 0, len(nums)
        while lo < hi:
            mid = (lo + hi) // 2
            if nums[mid] >= val:
                hi = mid
            else:
                lo = mid + 1
        return lo

    first = leftmost(target)
    if first == len(nums) or nums[first] != target:
        return [-1, -1]
    last = leftmost(target + 1) - 1
    return [first, last]


def _search_rotated(nums: List[int], target: int) -> int:
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        if nums[lo] <= nums[mid]:
            if nums[lo] <= target < nums[mid]:
                hi = mid - 1
            else:
                lo = mid + 1
        else:
            if nums[mid] < target <= nums[hi]:
                lo = mid + 1
            else:
                hi = mid - 1
    return -1


def _find_min(nums: List[int]) -> int:
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] > nums[hi]:
            lo = mid + 1
        else:
            hi = mid
    return nums[lo]


def _min_eating_speed(piles: List[int], h: int) -> int:
    def hours(k: int) -> int:
        return sum((p + k - 1) // k for p in piles)

    lo, hi = 1, max(piles)
    while lo < hi:
        mid = (lo + hi) // 2
        if hours(mid) <= h:
            hi = mid
        else:
            lo = mid + 1
    return lo


def _find_median(nums1: List[int], nums2: List[int]) -> float:
    if len(nums1) > len(nums2):
        nums1, nums2 = nums2, nums1
    m, n = len(nums1), len(nums2)
    lo, hi = 0, m
    while lo <= hi:
        i = (lo + hi) // 2
        j = (m + n + 1) // 2 - i
        if i < m and nums2[j - 1] > nums1[i]:
            lo = i + 1
        elif i > 0 and nums1[i - 1] > nums2[j]:
            hi = i - 1
        else:
            max_left = max(
                nums1[i - 1] if i > 0 else float("-inf"),
                nums2[j - 1] if j > 0 else float("-inf"),
            )
            if (m + n) % 2 == 1:
                return float(max_left)
            min_right = min(
                nums1[i] if i < m else float("inf"), nums2[j] if j < n else float("inf")
            )
            return (max_left + min_right) / 2.0
    return 0.0
