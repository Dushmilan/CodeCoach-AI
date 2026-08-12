"""Arrays & Hashing questions."""

from __future__ import annotations

from typing import List

from ._helpers import make_spec

SPECS = [
    make_spec(
        id="two-sum",
        title="Two Sum",
        difficulty="easy",
        category="Arrays & Hashing",
        companies=["Amazon", "Google", "Apple", "Adobe", "Microsoft"],
        description="Given an array of integers `nums` and an integer `target`, return the indices of the two numbers such that they add up to `target`.\n\n**Rules**\n- You may assume that each input has exactly one solution, and you may not use the same element twice.\n- Return the answer in the form `[index1, index2]` (any order).\n\n**Constraints**\n- 2 <= nums.length <= 10^4\n- -10^9 <= nums[i] <= 10^9\n- -10^9 <= target <= 10^9\n- Exactly one valid answer exists.",
        examples=[
            {
                "input": "nums = [2,7,11,15], target = 9",
                "output": "[0,1]",
                "explanation": "nums[0] + nums[1] == 9, so we return [0, 1].",
            },
            {
                "input": "nums = [3,2,4], target = 6",
                "output": "[1,2]",
                "explanation": "nums[1] + nums[2] == 6, so we return [1, 2].",
            },
            {
                "input": "nums = [3,3], target = 6",
                "output": "[0,1]",
                "explanation": "The only pair is nums[0] and nums[1].",
            },
        ],
        tests=[
            (([2, 7, 11, 15], 9), False),
            (([3, 2, 4], 6), False),
            (([3, 3], 6), False),
            (([1, 2, 3, 4, 5], 9), False),
            (([-3, 4, 3, 90], 0), False),
            (([5, 75, 25], 100), False),
            (([0, 4, 3, 0], 0), True),
            (([-1, -2, -3, -4, -5], -8), True),
            (([1, 5, 9, 2, 8], 10), True),
            (([100, 200, 300], 300), True),
            (([2, 5, 5, 11], 10), True),
            (([7, 1, 5, 3, 6, 4], 13), True),
        ],
        ref=lambda nums, target: _two_sum(nums, target),
        starter={
            "python": "def twoSum(nums: List[int], target: int) -> List[int]:\n    pass",
            "javascript": "function twoSum(nums, target) {\n    // your code here\n}",
            "java": "class Solution {\n    public int[] twoSum(int[] nums, int target) {\n        // your code here\n    }\n}",
        },
        hints=[
            "A brute force checks every pair — that is O(n^2).",
            "Store each value together with its index in a hash map as you scan.",
            "For nums[i], you only need to know whether target - nums[i] was seen earlier.",
        ],
        solution="Scan the array once, keeping a hash map from value to index. For each nums[i], check whether target - nums[i] already exists in the map; if it does, return [map[target - nums[i]], i]. Otherwise store nums[i] -> i and continue.",
        time_complexity="O(n)",
        space_complexity="O(n)",
        constraints=[
            "2 <= nums.length <= 10^4",
            "-10^9 <= nums[i] <= 10^9",
            "Exactly one valid answer exists.",
        ],
    ),
    make_spec(
        id="contains-duplicate",
        title="Contains Duplicate",
        difficulty="easy",
        category="Arrays & Hashing",
        companies=["Amazon", "Microsoft", "Google", "Facebook", "Apple"],
        description="Given an integer array `nums`, return `true` if any value appears at least twice in the array, and return `false` if every element is distinct.\n\n**Constraints**\n- 1 <= nums.length <= 10^5\n- -10^9 <= nums[i] <= 10^9",
        examples=[
            {
                "input": "nums = [1,2,3,1]",
                "output": "true",
                "explanation": "The value 1 appears twice.",
            },
            {
                "input": "nums = [1,2,3,4]",
                "output": "false",
                "explanation": "All elements are distinct.",
            },
            {
                "input": "nums = [1,1,1,3,3,4,3,2,4,2]",
                "output": "true",
                "explanation": "Several values repeat.",
            },
        ],
        tests=[
            (([1, 2, 3, 1],), False),
            (([1, 2, 3, 4],), False),
            (([1, 1, 1, 3, 3, 4, 3, 2, 4, 2],), False),
            (([],), False),
            (([1],), False),
            (([1, 2, 3, 4, 5, 6, 7, 8, 9, 10],), False),
            (([-1, 0, 1, -1],), True),
            (([2, 2],), True),
            (([100, 100, 100],), True),
            (([7, 7, 7, 7],), True),
        ],
        ref=lambda nums: len(set(nums)) != len(nums),
        starter={
            "python": "def containsDuplicate(nums: List[int]) -> bool:\n    pass",
            "javascript": "function containsDuplicate(nums) {\n    // your code here\n}",
            "java": "class Solution {\n    public boolean containsDuplicate(int[] nums) {\n        // your code here\n    }\n}",
        },
        hints=[
            "A set lets you track seen values in O(1).",
            "If inserting into a set ever fails because the value is already present, return true.",
        ],
        solution="Insert every element into a hash set as you scan. If an element is already in the set, return true immediately; otherwise add it. If the loop finishes, every element was unique, so return false.",
        time_complexity="O(n)",
        space_complexity="O(n)",
        constraints=["1 <= nums.length <= 10^5", "-10^9 <= nums[i] <= 10^9"],
    ),
    make_spec(
        id="majority-element",
        title="Majority Element",
        difficulty="easy",
        category="Arrays & Hashing",
        companies=["Amazon", "Google", "Facebook", "Microsoft", "Apple"],
        description="Given an array `nums` of size n, return the majority element — the element that appears more than n / 2 times.\n\n**Rules**\n- You may assume that the majority element always exists in the array.\n\n**Constraints**\n- n == nums.length\n- 1 <= n <= 5 * 10^4\n- -10^9 <= nums[i] <= 10^9",
        examples=[
            {
                "input": "nums = [3,2,3]",
                "output": "3",
                "explanation": "3 appears 2 times out of 3.",
            },
            {
                "input": "nums = [2,2,1,1,1,2,2]",
                "output": "2",
                "explanation": "2 appears 4 times out of 7.",
            },
        ],
        tests=[
            (([3, 2, 3],), False),
            (([2, 2, 1, 1, 1, 2, 2],), False),
            (([1],), False),
            (([5, 5, 5, 1],), False),
            (([6, 5, 5],), False),
            (([-1, -1, -1, 2],), False),
            (([10, 10, 10, 20, 10],), True),
            (([0, 0, 0, 1, 1, 0],), True),
        ],
        ref=lambda nums: _majority(nums),
        starter={
            "python": "def majorityElement(nums: List[int]) -> int:\n    pass",
            "javascript": "function majorityElement(nums) {\n    // your code here\n}",
            "java": "class Solution {\n    public int majorityElement(int[] nums) {\n        // your code here\n    }\n}",
        },
        hints=[
            "A hash map of counts is the simplest correct approach.",
            "Boyer-Moore voting tracks a candidate and a count in O(1) space.",
        ],
        solution="Use Boyer-Moore voting: maintain a candidate and a counter. For each element, if the counter is 0 pick it as the new candidate; then increment the counter if it matches the candidate, otherwise decrement. The surviving candidate is the majority element.",
        time_complexity="O(n)",
        space_complexity="O(1)",
        constraints=["n == nums.length", "1 <= n <= 5 * 10^4"],
    ),
    make_spec(
        id="three-sum",
        title="Three Sum",
        difficulty="medium",
        category="Arrays & Hashing",
        companies=["Google", "Facebook", "Amazon", "Microsoft", "Adobe"],
        description="Given an integer array `nums`, return all unique triplets `[nums[i], nums[j], nums[k]]` such that `i`, `j`, `k` are distinct indices and `nums[i] + nums[j] + nums[k] == 0`.\n\n**Rules**\n- The solution set must not contain duplicate triplets.\n- The order of triplets (and elements within a triplet) does not matter.\n\n**Constraints**\n- 0 <= nums.length <= 3000\n- -10^5 <= nums[i] <= 10^5",
        examples=[
            {
                "input": "nums = [-1,0,1,2,-1,-4]",
                "output": "[[-1,-1,2],[-1,0,1]]",
                "explanation": "The distinct triplets summing to zero are [-1,-1,2] and [-1,0,1].",
            },
            {
                "input": "nums = [0,1,1]",
                "output": "[]",
                "explanation": "No three numbers sum to zero.",
            },
            {
                "input": "nums = [0,0,0]",
                "output": "[[0,0,0]]",
                "explanation": "The only triplet is [0,0,0].",
            },
        ],
        tests=[
            (([-1, 0, 1, 2, -1, -4],), False),
            (([0, 1, 1],), False),
            (([0, 0, 0],), False),
            (([],), False),
            (([0],), False),
            (([-2, 0, 1, 1, 2],), False),
            (([3, 0, -2, -1, 1, 2],), True),
            (([-4, -2, -2, -2, 0, 1, 2, 2, 2, 3, 3, 4, 4, 6, 6],), True),
            (([1, 2, -2, -1],), True),
            (([-1, 0, 1, 0],), True),
        ],
        ref=lambda *args: _three_sum(*args),
        starter={
            "python": "def threeSum(nums: List[int]) -> List[List[int]]:\n    pass",
            "javascript": "function threeSum(nums) {\n    // your code here\n}",
            "java": "class Solution {\n    public List<List<Integer>> threeSum(int[] nums) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Sort the array first so duplicate handling is easy.",
            "Fix one number, then use a two-pointer sweep for the remaining pair.",
            "Skip duplicates after fixing each index to keep triplets unique.",
        ],
        solution="Sort nums. For each i, run two pointers (lo = i+1, hi = n-1) seeking a pair that sums to -nums[i]. Move lo up and hi down while adjusting for duplicates so no triplet repeats. Collect every valid triple.",
        time_complexity="O(n^2)",
        space_complexity="O(1) excluding output",
        constraints=["0 <= nums.length <= 3000", "-10^5 <= nums[i] <= 10^5"],
    ),
    make_spec(
        id="product-of-array-except-self",
        title="Product of Array Except Self",
        difficulty="medium",
        category="Arrays & Hashing",
        companies=["Amazon", "Apple", "Adobe", "Microsoft", "Facebook"],
        description="Given an integer array `nums`, return an array `answer` such that `answer[i]` is equal to the product of all the elements of `nums` except `nums[i]`.\n\n**Rules**\n- The product of any prefix or suffix of `nums` fits in a 32-bit integer.\n- You must solve it without using the division operator.\n\n**Constraints**\n- 2 <= nums.length <= 10^5\n- -30 <= nums[i] <= 30",
        examples=[
            {
                "input": "nums = [1,2,3,4]",
                "output": "[24,12,8,6]",
                "explanation": "For index 0 the product of the rest is 2*3*4 = 24, and so on.",
            },
            {
                "input": "nums = [-1,1,0,-3,3]",
                "output": "[0,0,9,0,0]",
                "explanation": "Elements to the left/right of the only zero multiply to 0 except at its own index.",
            },
        ],
        tests=[
            (([1, 2, 3, 4],), False),
            (([-1, 1, 0, -3, 3],), False),
            (([1, 1],), False),
            (([0, 0],), False),
            (([2, 3, 4, 5],), False),
            (([-1, -1, -1, -1],), False),
            (([1, 2, 3, 4, 5, 6],), False),
            (([10, 20, 30],), True),
            (([-2, 3, -4, 5],), True),
        ],
        ref=lambda *args: _product_except_self(*args),
        starter={
            "python": "def productExceptSelf(nums: List[int]) -> List[int]:\n    pass",
            "javascript": "function productExceptSelf(nums) {\n    // your code here\n}",
            "java": "class Solution {\n    public int[] productExceptSelf(int[] nums) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Think left-to-right: product of everything to the left of i.",
            "Then right-to-left: multiply by the product of everything to the right.",
            "Two passes with a running product and no division.",
        ],
        solution="Create answer filled with 1s. First pass: for each i, set answer[i] to the running product of all elements to the left. Second pass: track a right product and multiply answer[i] by it, updating the right product with nums[i]. Return answer.",
        time_complexity="O(n)",
        space_complexity="O(1) ignoring output",
        constraints=["2 <= nums.length <= 10^5", "-30 <= nums[i] <= 30"],
    ),
    make_spec(
        id="subarray-sum-equals-k",
        title="Subarray Sum Equals K",
        difficulty="medium",
        category="Arrays & Hashing",
        companies=["Google", "Facebook", "Amazon", "Microsoft"],
        description="Given an array of integers `nums` and an integer `k`, return the total number of contiguous subarrays whose sum equals `k`.\n\n**Constraints**\n- 1 <= nums.length <= 2 * 10^4\n- -1000 <= nums[i] <= 1000\n- -10^7 <= k <= 10^7",
        examples=[
            {
                "input": "nums = [1,1,1], k = 2",
                "output": "2",
                "explanation": "Subarrays [1,1] at indices 0-1 and 1-2.",
            },
            {
                "input": "nums = [1,2,3], k = 3",
                "output": "2",
                "explanation": "Subarrays [1,2] and [3].",
            },
        ],
        tests=[
            (([1, 1, 1], 2), False),
            (([1, 2, 3], 3), False),
            (([1], 0), False),
            (([0, 0, 0], 0), False),
            (([-1, -1, 1], 0), False),
            (([1, -1, 0], 0), False),
            (([2, 2, 2, 2], 4), True),
            (([1, 2, 1, 2, 1], 3), True),
            (([3, 4, 7, 2, -3, 1, 4, 2], 7), True),
        ],
        ref=lambda nums, k: _subarray_sum(nums, k),
        starter={
            "python": "def subarraySum(nums: List[int], k: int) -> int:\n    pass",
            "javascript": "function subarraySum(nums, k) {\n    // your code here\n}",
            "java": "class Solution {\n    public int subarraySum(int[] nums, int k) {\n        // your code here\n    }\n}",
        },
        hints=[
            "A prefix sum lets you express any subarray sum as one subtraction.",
            "If you have seen prefix - k before, every such occurrence forms a valid subarray.",
            "Count prefix-sum frequencies in a hash map, initialized with {0: 1}.",
        ],
        solution="Keep a running prefix sum and a hash map counting how many times each prefix has appeared (start with {0:1}). For each element, add nums[i] to the prefix, then add map[prefix - k] (if present) to the answer, and increment the count of prefix.",
        time_complexity="O(n)",
        space_complexity="O(n)",
        constraints=["1 <= nums.length <= 2 * 10^4", "-1000 <= nums[i] <= 1000"],
    ),
    make_spec(
        id="group-anagrams",
        title="Group Anagrams",
        difficulty="medium",
        category="Arrays & Hashing",
        companies=["Amazon", "Microsoft", "Google", "Facebook", "Apple"],
        description="Given an array of strings `strs`, group the anagrams together. You can return the answer in any order.\n\n**Rules**\n- An anagram is a word formed by rearranging the letters of another, using all the original letters exactly once.\n\n**Constraints**\n- 1 <= strs.length <= 10^4\n- 0 <= strs[i].length <= 100\n- strs[i] consists of lowercase English letters.",
        examples=[
            {
                "input": 'strs = ["eat","tea","tan","ate","nat","bat"]',
                "output": '[["bat"],["nat","tan"],["ate","eat","tea"]]',
                "explanation": "eat, tea, and ate are anagrams, as are tan and nat; bat is alone.",
            },
            {
                "input": 'strs = [""]',
                "output": '[[""]]',
                "explanation": "The empty string forms its own group.",
            },
            {
                "input": 'strs = ["a"]',
                "output": '[["a"]]',
                "explanation": "A single character is its own group.",
            },
        ],
        tests=[
            ((["eat", "tea", "tan", "ate", "nat", "bat"],), False),
            (([""],), False),
            ((["a"],), False),
            (([],), False),
            ((["ab", "ba", "abc", "cba", "bca"],), False),
            ((["list", "silt", "silt"],), False),
            ((["xx", "x"],), True),
            ((["", "", "a", "a"],), True),
        ],
        ref=lambda *args: _group_anagrams(*args),
        starter={
            "python": "def groupAnagrams(strs: List[str]) -> List[List[str]]:\n    pass",
            "javascript": "function groupAnagrams(strs) {\n    // your code here\n}",
            "java": "class Solution {\n    public List<List<String>> groupAnagrams(String[] strs) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Two words are anagrams iff their sorted versions are identical.",
            "Group by the sorted string as a hash-map key.",
        ],
        solution="Build a hash map keyed by the sorted version of each string. For every string, append it to the bucket for its sorted key. Return the buckets as a list of lists.",
        time_complexity="O(n * k log k)",
        space_complexity="O(n * k)",
        constraints=["1 <= strs.length <= 10^4", "0 <= strs[i].length <= 100"],
    ),
    make_spec(
        id="top-k-frequent-elements",
        title="Top K Frequent Elements",
        difficulty="medium",
        category="Arrays & Hashing",
        companies=["Amazon", "Google", "Facebook", "Microsoft", "Apple"],
        description="Given an integer array `nums` and an integer `k`, return the `k` most frequent elements. You may return the answer in any order.\n\n**Constraints**\n- 1 <= nums.length <= 10^5\n- -10^4 <= nums[i] <= 10^4\n- k is in the range [1, the number of unique elements in the array].\n- It is guaranteed that the answer is unique.",
        examples=[
            {
                "input": "nums = [1,1,1,2,2,3], k = 2",
                "output": "[1,2]",
                "explanation": "1 appears three times and 2 twice; 3 appears once.",
            },
            {
                "input": "nums = [1], k = 1",
                "output": "[1]",
                "explanation": "Only one distinct element.",
            },
        ],
        tests=[
            (([1, 1, 1, 2, 2, 3], 2), False),
            (([1], 1), False),
            (([4, 4, 4, 4], 1), False),
            (([1, 2, 3, 1, 2, 1], 2), False),
            (([5, 5, 5, 6, 6, 7], 3), False),
            (([-1, -1, 0, 1, 1, 1], 2), False),
            (([9, 9, 9, 8, 8, 7], 2), True),
            (([1, 2, 2, 3, 3, 3, 4, 4, 4, 4], 2), True),
        ],
        ref=lambda nums, k: _top_k_frequent(nums, k),
        starter={
            "python": "def topKFrequent(nums: List[int], k: int) -> List[int]:\n    pass",
            "javascript": "function topKFrequent(nums, k) {\n    // your code here\n}",
            "java": "class Solution {\n    public int[] topKFrequent(int[] nums, int k) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Count frequencies with a hash map first.",
            "A min-heap of size k keeps the k most frequent elements.",
            "Bucket sort by frequency is an O(n) alternative.",
        ],
        solution="Count frequencies in a hash map. Push (frequency, value) pairs into a min-heap, keeping its size at k by popping the smallest. At the end the heap holds the k most frequent elements; return them as a list.",
        time_complexity="O(n log k)",
        space_complexity="O(n)",
        constraints=[
            "1 <= nums.length <= 10^5",
            "k is in [1, number of unique elements]",
        ],
    ),
    make_spec(
        id="longest-consecutive-sequence",
        title="Longest Consecutive Sequence",
        difficulty="medium",
        category="Arrays & Hashing",
        companies=["Google", "Amazon", "Microsoft", "Facebook"],
        description="Given an unsorted array of integers `nums`, return the length of the longest consecutive elements sequence.\n\n**Rules**\n- You must write an algorithm that runs in O(n) time.\n\n**Constraints**\n- 0 <= nums.length <= 10^5\n- -10^9 <= nums[i] <= 10^9",
        examples=[
            {
                "input": "nums = [100,4,200,1,3,2]",
                "output": "4",
                "explanation": "The longest sequence is [1,2,3,4].",
            },
            {
                "input": "nums = [0,3,7,2,5,8,4,6,0,1]",
                "output": "9",
                "explanation": "The sequence [0,1,2,3,4,5,6,7,8] has length 9.",
            },
        ],
        tests=[
            (([100, 4, 200, 1, 3, 2],), False),
            (([0, 3, 7, 2, 5, 8, 4, 6, 0, 1],), False),
            (([],), False),
            (([1],), False),
            (([1, 2, 0, 1],), False),
            (([9, 1, 4, 7, 3, -1, 0, 5, 8, -1, 6],), False),
            (([1, 3, 5, 7, 9],), True),
            (([5, 4, 3, 2, 1],), True),
            (([1, 2, 3, 100, 101, 102, 103],), True),
        ],
        ref=lambda *args: _longest_consecutive(*args),
        starter={
            "python": "def longestConsecutive(nums: List[int]) -> int:\n    pass",
            "javascript": "function longestConsecutive(nums) {\n    // your code here\n}",
            "java": "class Solution {\n    public int longestConsecutive(int[] nums) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Put every number into a set for O(1) lookups.",
            "Only start counting a run from a number whose predecessor is absent.",
            "Then walk up one step at a time and measure the run length.",
        ],
        solution="Insert all numbers into a set. For each number that has no predecessor (n-1 not in the set), count how many consecutive numbers n, n+1, n+2, ... exist. Track the maximum run length.",
        time_complexity="O(n)",
        space_complexity="O(n)",
        constraints=["0 <= nums.length <= 10^5", "-10^9 <= nums[i] <= 10^9"],
    ),
    make_spec(
        id="first-missing-positive",
        title="First Missing Positive",
        difficulty="hard",
        category="Arrays & Hashing",
        companies=["Google", "Amazon", "Apple", "Microsoft"],
        description="Given an unsorted integer array `nums`, return the smallest positive integer that is missing from the array.\n\n**Rules**\n- You must implement an algorithm that runs in O(n) time and uses O(1) auxiliary space.\n\n**Constraints**\n- 1 <= nums.length <= 10^5\n- -2^31 <= nums[i] <= 2^31 - 1",
        examples=[
            {
                "input": "nums = [1,2,0]",
                "output": "3",
                "explanation": "1 and 2 are present, so the smallest missing positive is 3.",
            },
            {
                "input": "nums = [3,4,-1,1]",
                "output": "2",
                "explanation": "1 is present but 2 is missing.",
            },
            {
                "input": "nums = [7,8,9,11,12]",
                "output": "1",
                "explanation": "1 is missing.",
            },
        ],
        tests=[
            (([1, 2, 0],), False),
            (([3, 4, -1, 1],), False),
            (([7, 8, 9, 11, 12],), False),
            (([1],), False),
            (([1, 2, 3],), False),
            (([-1, -2, 0, 5],), False),
            (([2, 1],), True),
            (([0, 2, 2, 1, 1],), True),
            (([1, 1],), True),
        ],
        ref=lambda *args: _first_missing_positive(*args),
        starter={
            "python": "def firstMissingPositive(nums: List[int]) -> int:\n    pass",
            "javascript": "function firstMissingPositive(nums) {\n    // your code here\n}",
            "java": "class Solution {\n    public int firstMissingPositive(int[] nums) {\n        // your code here\n    }\n}",
        },
        hints=[
            "The answer lies in the range [1, n+1] for an array of size n.",
            "Use the array itself as a hash table via sign marking.",
            "If nums[i] is a positive integer in range, mark index nums[i]-1 as visited.",
        ],
        solution="For each element, if it is a positive integer within [1, n], place it at its sorted index by swapping (or mark with a sign). Then scan: the first index i whose value does not correspond to i+1 gives the missing number i+1. If all are in place, return n+1.",
        time_complexity="O(n)",
        space_complexity="O(1)",
        constraints=["1 <= nums.length <= 10^5"],
    ),
    make_spec(
        id="find-the-duplicate-number",
        title="Find the Duplicate Number",
        difficulty="hard",
        category="Arrays & Hashing",
        companies=["Amazon", "Google", "Microsoft", "Apple", "Facebook"],
        description="Given an array of integers `nums` containing n + 1 integers where each integer is in the range [1, n] inclusive, return the duplicate number.\n\n**Rules**\n- There is only one repeated number in `nums`, but it may be repeated more than once.\n- You must solve the problem without modifying the array and using only constant extra space.\n\n**Constraints**\n- 1 <= n <= 10^5\n- nums.length == n + 1\n- 1 <= nums[i] <= n",
        examples=[
            {
                "input": "nums = [1,3,4,2,2]",
                "output": "2",
                "explanation": "2 is repeated.",
            },
            {
                "input": "nums = [3,1,3,4,2]",
                "output": "3",
                "explanation": "3 is repeated.",
            },
            {"input": "nums = [1,1]", "output": "1", "explanation": "1 is repeated."},
            {"input": "nums = [1,1,2]", "output": "1", "explanation": "1 is repeated."},
        ],
        tests=[
            (([1, 3, 4, 2, 2],), False),
            (([3, 1, 3, 4, 2],), False),
            (([1, 1],), False),
            (([1, 1, 2],), False),
            (([2, 2, 2, 2, 2],), False),
            (([1, 2, 3, 4, 5, 5],), False),
            (([5, 5, 1, 2, 3, 4],), True),
            (([4, 3, 2, 4, 1],), True),
        ],
        ref=lambda *args: _find_duplicate(*args),
        starter={
            "python": "def findDuplicate(nums: List[int]) -> int:\n    pass",
            "javascript": "function findDuplicate(nums) {\n    // your code here\n}",
            "java": "class Solution {\n    public int findDuplicate(int[] nums) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Treat the array as a linked list where value is the next index.",
            "The duplicate corresponds to the start of the cycle.",
            "Use Floyd's slow/fast pointer technique.",
        ],
        solution="Interpret each index as a node whose next pointer is the value at that index; this forms a linked list with a cycle. Use two pointers moving at speeds 1 and 2 to find where they meet, then reset one pointer to the start and advance both by 1 until they meet again — that meeting point is the duplicate.",
        time_complexity="O(n)",
        space_complexity="O(1)",
        constraints=["1 <= n <= 10^5", "nums.length == n + 1"],
    ),
    make_spec(
        id="find-all-duplicates-in-an-array",
        title="Find All Duplicates in an Array",
        difficulty="medium",
        category="Arrays & Hashing",
        companies=["Amazon", "Microsoft", "Google", "Facebook"],
        description="Given an integer array `nums` of length n where all the integers of `nums` are in the range [1, n] and each integer appears once or twice, return an array of all the integers that appear twice.\n\nYou must write an algorithm that runs in O(n) time and uses only constant extra space.\n\n**Constraints**\n- n == nums.length\n- 1 <= n <= 10^5\n- 1 <= nums[i] <= n",
        examples=[
            {
                "input": "nums = [4,3,2,7,8,2,3,1]",
                "output": "[2,3]",
                "explanation": "2 and 3 appear twice.",
            },
            {
                "input": "nums = [1,1,2]",
                "output": "[1]",
                "explanation": "1 appears twice.",
            },
            {"input": "nums = [1]", "output": "[]", "explanation": "No duplicates."},
        ],
        tests=[
            (([4, 3, 2, 7, 8, 2, 3, 1],), False),
            (([1, 1, 2],), False),
            (([1],), False),
            (([2, 2],), False),
            (([1, 2, 3, 4],), False),
            (([5, 5, 4, 3, 2, 1],), False),
            (([1, 2, 2, 3, 3, 4],), False),
            (([3, 3, 3],), False),
            (([1, 1, 1, 2],), True),
            (([4, 4, 2, 2, 1, 3],), True),
            (([2, 1, 2, 1],), True),
        ],
        ref=lambda *args: _find_duplicates(*args),
        starter={
            "python": "def findDuplicates(nums: List[int]) -> List[int]:\n    pass",
            "javascript": "function findDuplicates(nums) {\n    // your code here\n}",
            "java": "class Solution {\n    public List<Integer> findDuplicates(int[] nums) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Since values are in [1, n], use the array itself as a marker.",
            "Flip nums[value - 1] to negative; a negative marker means the value was seen before.",
        ],
        solution="For each number, take its absolute value v and mark nums[v - 1] as negative. If it was already negative, v is a duplicate. Collect all duplicates and return them.",
        time_complexity="O(n)",
        space_complexity="O(1)",
        constraints=["n == nums.length", "1 <= nums[i] <= n"],
    ),
    make_spec(
        id="contiguous-array",
        title="Contiguous Array",
        difficulty="medium",
        category="Arrays & Hashing",
        companies=["Facebook", "Amazon", "Microsoft", "Google"],
        description="Given a binary array `nums`, return the maximum length of a contiguous subarray with an equal number of 0s and 1s.\n\n**Constraints**\n- 1 <= nums.length <= 10^5\n- nums[i] is either 0 or 1.",
        examples=[
            {
                "input": "nums = [0,1]",
                "output": "2",
                "explanation": "[0,1] has equal 0s and 1s.",
            },
            {
                "input": "nums = [0,1,0]",
                "output": "2",
                "explanation": "[0,1] or [1,0] is the longest.",
            },
            {
                "input": "nums = [0,1,1,0,1,1,1,0]",
                "output": "4",
                "explanation": "The subarray [0,1,1,0] has two 0s and two 1s.",
            },
        ],
        tests=[
            (([0, 1],), False),
            (([0, 1, 0],), False),
            (([0, 1, 1, 0, 1, 1, 1, 0],), False),
            (([0],), False),
            (([1],), False),
            (([0, 0, 0, 0],), False),
            (([1, 1, 1, 1],), False),
            (([0, 0, 1, 0, 0, 0, 1, 1],), False),
            (([1, 0, 1, 0, 1],), False),
            (([0, 0, 1, 0, 0, 0, 1, 1],), True),
            (([1, 0, 0, 1, 0, 1],), True),
        ],
        ref=lambda *args: _find_max_length(*args),
        starter={
            "python": "def findMaxLength(nums: List[int]) -> int:\n    pass",
            "javascript": "function findMaxLength(nums) {\n    // your code here\n}",
            "java": "class Solution {\n    public int findMaxLength(int[] nums) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Treat 0 as -1; a subarray with equal 0s and 1s has a sum of 0.",
            "Track the first index where each prefix sum appears.",
        ],
        solution="Map 0 to -1. Keep a running sum and a hash map of the first index where each sum occurred (starting with {0: -1}). When a sum repeats, the segment between the two indices has equal 0s and 1s; track the maximum length.",
        time_complexity="O(n)",
        space_complexity="O(n)",
        constraints=["1 <= nums.length <= 10^5"],
    ),
]


def _two_sum(nums: List[int], target: int) -> List[int]:
    seen = {}
    for i, v in enumerate(nums):
        need = target - v
        if need in seen:
            return [seen[need], i]
        seen[v] = i
    return []


def _majority(nums: List[int]) -> int:
    candidate, count = None, 0
    for v in nums:
        if count == 0:
            candidate = v
        count += 1 if v == candidate else -1
    return candidate


def _three_sum(nums: List[int]) -> List[List[int]]:
    nums = sorted(nums)
    n = len(nums)
    res = []
    for i in range(n - 2):
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        lo, hi = i + 1, n - 1
        while lo < hi:
            s = nums[i] + nums[lo] + nums[hi]
            if s < 0:
                lo += 1
            elif s > 0:
                hi -= 1
            else:
                res.append([nums[i], nums[lo], nums[hi]])
                while lo < hi and nums[lo] == nums[lo + 1]:
                    lo += 1
                while lo < hi and nums[hi] == nums[hi - 1]:
                    hi -= 1
                lo += 1
                hi -= 1
    return res


def _product_except_self(nums: List[int]) -> List[int]:
    n = len(nums)
    res = [1] * n
    left = 1
    for i in range(n):
        res[i] = left
        left *= nums[i]
    right = 1
    for i in range(n - 1, -1, -1):
        res[i] *= right
        right *= nums[i]
    return res


def _subarray_sum(nums: List[int], k: int) -> int:
    counts = {0: 1}
    prefix = 0
    ans = 0
    for v in nums:
        prefix += v
        ans += counts.get(prefix - k, 0)
        counts[prefix] = counts.get(prefix, 0) + 1
    return ans


def _group_anagrams(strs: List[str]) -> List[List[str]]:
    buckets = {}
    for s in strs:
        key = "".join(sorted(s))
        buckets.setdefault(key, []).append(s)
    return list(buckets.values())


def _top_k_frequent(nums: List[int], k: int) -> List[int]:
    import heapq
    from collections import Counter

    counts = Counter(nums)
    heap = []
    for value, cnt in counts.items():
        heapq.heappush(heap, (cnt, value))
        if len(heap) > k:
            heapq.heappop(heap)
    return [v for _, v in heap]


def _longest_consecutive(nums: List[int]) -> int:
    s = set(nums)
    best = 0
    for n in s:
        if n - 1 not in s:
            cur = n
            length = 1
            while cur + 1 in s:
                cur += 1
                length += 1
            best = max(best, length)
    return best


def _first_missing_positive(nums: List[int]) -> int:
    n = len(nums)
    for i in range(n):
        while 1 <= nums[i] <= n and nums[nums[i] - 1] != nums[i]:
            nums[nums[i] - 1], nums[i] = nums[i], nums[nums[i] - 1]
    for i in range(n):
        if nums[i] != i + 1:
            return i + 1
    return n + 1


def _find_duplicate(nums: List[int]) -> int:
    slow = nums[0]
    fast = nums[nums[0]]
    while slow != fast:
        slow = nums[slow]
        fast = nums[nums[fast]]
    slow = 0
    while slow != fast:
        slow = nums[slow]
        fast = nums[fast]
    return slow


def _find_duplicates(nums: List[int]) -> List[int]:
    res = []
    for v in nums:
        idx = abs(v) - 1
        if nums[idx] < 0:
            res.append(abs(v))
        nums[idx] = -nums[idx]
    return res


def _find_max_length(nums: List[int]) -> int:
    first = {0: -1}
    total = 0
    best = 0
    for i, v in enumerate(nums):
        total += 1 if v == 1 else -1
        if total in first:
            best = max(best, i - first[total])
        else:
            first[total] = i
    return best
