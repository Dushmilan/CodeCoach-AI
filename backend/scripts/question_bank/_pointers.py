"""Two Pointers & Sliding Window questions."""

from __future__ import annotations

from typing import List

from ._helpers import make_spec

SPECS = [
    make_spec(
        id="valid-palindrome",
        title="Valid Palindrome",
        difficulty="easy",
        category="Two Pointers",
        companies=["Amazon", "Facebook", "Google", "Microsoft"],
        description="A phrase is a palindrome if, after converting all uppercase letters into lowercase letters and removing all non-alphanumeric characters, it reads the same forward and backward. Alphanumeric characters include letters and numbers.\n\nGiven a string `s`, return `true` if it is a palindrome, or `false` otherwise.\n\n**Constraints**\n- 1 <= s.length <= 2 * 10^5\n- s consists only of printable ASCII characters.",
        examples=[
            {
                "input": 's = "A man, a plan, a canal: Panama"',
                "output": "true",
                "explanation": "After cleaning, s becomes 'amanaplanacanalpanama', which is a palindrome.",
            },
            {
                "input": 's = "race a car"',
                "output": "false",
                "explanation": "Cleaned s = 'raceacar', which is not a palindrome.",
            },
            {
                "input": 's = " "',
                "output": "true",
                "explanation": "After removing non-alphanumerics s is empty, and an empty string is a palindrome.",
            },
        ],
        tests=[
            (("A man, a plan, a canal: Panama",), False),
            (("race a car",), False),
            ((" ",), False),
            (("ab_a",), False),
            (("0P",), False),
            (("a",), False),
            (("aa",), False),
            ((".,",), False),
            (("Madam, I'm Adam",), True),
            (("12321",), True),
            (("Able was I ere I saw Elba",), True),
            (("Never odd or even",), True),
            (("racecar",), True),
            (("not a palindrome",), True),
        ],
        ref=lambda s: _is_palindrome(s),
        starter={
            "python": "def isPalindrome(s: str) -> bool:\n    pass",
            "javascript": "function isPalindrome(s) {\n    // your code here\n}",
            "java": "class Solution {\n    public boolean isPalindrome(String s) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Use two pointers moving from both ends toward the middle.",
            "Skip non-alphanumeric characters and compare lowercased letters.",
            "If any pair mismatches, return false.",
        ],
        solution="Move left and right pointers inward, skipping any non-alphanumeric characters. Compare the lowercased characters; if a mismatch is found return false. If the pointers cross, the string is a valid palindrome.",
        time_complexity="O(n)",
        space_complexity="O(1)",
        constraints=["1 <= s.length <= 2 * 10^5"],
    ),
    make_spec(
        id="is-subsequence",
        title="Is Subsequence",
        difficulty="easy",
        category="Two Pointers",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="Given two strings `s` and `t`, return `true` if `s` is a subsequence of `t`, or `false` otherwise.\n\n**Rules**\n- A subsequence is a sequence that can be derived from `t` by deleting some or no elements without changing the order of the remaining characters.\n\n**Constraints**\n- 0 <= s.length <= 100\n- 0 <= t.length <= 10^4\n- s and t consist only of lowercase English letters.",
        examples=[
            {
                "input": 's = "abc", t = "ahbgdc"',
                "output": "true",
                "explanation": "a then b then c appear in order in t.",
            },
            {
                "input": 's = "axc", t = "ahbgdc"',
                "output": "false",
                "explanation": "There is no x in t after a.",
            },
        ],
        tests=[
            (("abc", "ahbgdc"), False),
            (("axc", "ahbgdc"), False),
            (("", "ahbgdc"), False),
            (("", ""), False),
            (("b", "abc"), False),
            (("abc", "abc"), False),
            (("abc", "ababc"), False),
            (("aaaaaa", "bbaaaa"), False),
            (("ace", "abcde"), True),
            (("aec", "abcde"), True),
            (("leeeeetcode", "leeeeeetcode"), True),
        ],
        ref=lambda s, t: _is_subsequence(s, t),
        starter={
            "python": "def isSubsequence(s: str, t: str) -> bool:\n    pass",
            "javascript": "function isSubsequence(s, t) {\n    // your code here\n}",
            "java": "class Solution {\n    public boolean isSubsequence(String s, String t) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Scan t once, advancing through s whenever a character matches.",
            "If you consume all of s, it is a subsequence.",
        ],
        solution="Use two pointers i (on s) and j (on t). While both are in range, if s[i] == t[j] advance i; always advance j. Return true iff i reached the end of s.",
        time_complexity="O(len(t))",
        space_complexity="O(1)",
        constraints=["0 <= s.length <= 100", "0 <= t.length <= 10^4"],
    ),
    make_spec(
        id="two-sum-ii-input-array-is-sorted",
        title="Two Sum II - Input Array Is Sorted",
        difficulty="medium",
        category="Two Pointers",
        companies=["Amazon", "Google", "Facebook", "Microsoft"],
        description="Given a 1-indexed array of integers `numbers` that is already sorted in non-decreasing order, find two numbers such that they add up to a specific target number.\n\nReturn the indices of the two numbers as an integer array `[index1, index2]` of length 2 (1-indexed).\n\n**Rules**\n- The tests are generated such that there is exactly one solution.\n- You may not use the same element twice.\n\n**Constraints**\n- 2 <= numbers.length <= 3 * 10^4\n- -1000 <= numbers[i] <= 1000\n- numbers is sorted in non-decreasing order.",
        examples=[
            {
                "input": "numbers = [2,7,11,15], target = 9",
                "output": "[1,2]",
                "explanation": "2 + 7 = 9, at 1-indexed positions 1 and 2.",
            },
            {
                "input": "numbers = [2,3,4], target = 6",
                "output": "[1,3]",
                "explanation": "2 + 4 = 6.",
            },
            {
                "input": "numbers = [-1,0], target = -1",
                "output": "[1,2]",
                "explanation": "-1 + 0 = -1.",
            },
        ],
        tests=[
            (([2, 7, 11, 15], 9), False),
            (([2, 3, 4], 6), False),
            (([-1, 0], -1), False),
            (([1, 2, 3, 4, 4, 9, 56, 90], 8), False),
            (([5, 25, 75], 100), False),
            (([-3, 3, 4, 90], 0), False),
            (([1, 3, 4, 5, 7, 10, 11], 9), True),
            (([0, 1, 2, 3, 4, 5], 5), True),
            (([-10, -5, 0, 5, 10], 0), True),
        ],
        ref=lambda numbers, target: _two_sum_ii(numbers, target),
        starter={
            "python": "def twoSum(numbers: List[int], target: int) -> List[int]:\n    pass",
            "javascript": "function twoSum(numbers, target) {\n    // your code here\n}",
            "java": "class Solution {\n    public int[] twoSum(int[] numbers, int target) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Because the array is sorted, use two pointers from both ends.",
            "If the sum is too large, move the right pointer left; if too small, move the left pointer right.",
        ],
        solution="Place left at index 0 and right at the last index. Compute the sum; if it equals the target return [left+1, right+1], if too small increment left, otherwise decrement right. Continue until the pointers meet.",
        time_complexity="O(n)",
        space_complexity="O(1)",
        constraints=[
            "2 <= numbers.length <= 3 * 10^4",
            "numbers is sorted in non-decreasing order",
        ],
    ),
    make_spec(
        id="container-with-most-water",
        title="Container With Most Water",
        difficulty="medium",
        category="Two Pointers",
        companies=["Amazon", "Google", "Facebook", "Microsoft"],
        description="You are given an integer array `height` of length n. There are n vertical lines drawn such that the two endpoints of the i-th line are (i, 0) and (i, height[i]).\n\nFind two lines that together with the x-axis form a container, such that the container contains the most water.\n\nReturn the maximum amount of water a container can store.\n\n**Constraints**\n- n == height.length\n- 2 <= n <= 10^5\n- 0 <= height[i] <= 10^4",
        examples=[
            {
                "input": "height = [1,8,6,2,5,4,8,3,7]",
                "output": "49",
                "explanation": "Lines at indices 1 and 8 form a container of area min(8,7)*7 = 49.",
            },
            {
                "input": "height = [1,1]",
                "output": "1",
                "explanation": "The only container has area 1.",
            },
        ],
        tests=[
            (([1, 8, 6, 2, 5, 4, 8, 3, 7],), False),
            (([1, 1],), False),
            (([4, 3, 2, 1, 4],), False),
            (([1, 2, 1],), False),
            (([1, 2, 4, 3],), False),
            (([2, 3, 4, 5, 18, 17, 6],), False),
            (([1, 3, 2, 5, 25, 24, 5],), False),
            (([1, 1000, 1000, 1],), False),
            (([0, 1, 0, 1, 0],), True),
            (([2, 3, 4, 5, 6, 1],), True),
        ],
        ref=lambda *args: _max_area(*args),
        starter={
            "python": "def maxArea(height: List[int]) -> int:\n    pass",
            "javascript": "function maxArea(height) {\n    // your code here\n}",
            "java": "class Solution {\n    public int maxArea(int[] height) {\n        // your code here\n    }\n}",
        },
        hints=[
            "The area is width times the shorter of the two heights.",
            "Start with the widest container (both ends) and shrink inward.",
            "Always move the pointer with the smaller height.",
        ],
        solution="Use two pointers at both ends. At each step compute the area using the shorter line as the height. Move the pointer that points to the shorter line inward. Track the maximum area seen.",
        time_complexity="O(n)",
        space_complexity="O(1)",
        constraints=["n == height.length", "2 <= n <= 10^5"],
    ),
    make_spec(
        id="three-sum-closest",
        title="Three Sum Closest",
        difficulty="medium",
        category="Two Pointers",
        companies=["Amazon", "Google", "Facebook", "Apple"],
        description="Given an integer array `nums` of length n and an integer `target`, find three integers in `nums` such that the sum is closest to `target`.\n\nReturn the sum of the three integers.\n\n**Rules**\n- You may assume that each input would have exactly one solution.\n\n**Constraints**\n- 3 <= nums.length <= 500\n- -1000 <= nums[i] <= 1000\n- -10^4 <= target <= 10^4",
        examples=[
            {
                "input": "nums = [-1,2,1,-4], target = 1",
                "output": "2",
                "explanation": "The sum that is closest to the target is 2 (-1 + 2 + 1 = 2).",
            },
            {
                "input": "nums = [0,0,0], target = 1",
                "output": "0",
                "explanation": "The only sum is 0.",
            },
        ],
        tests=[
            (([-1, 2, 1, -4], 1), False),
            (([0, 0, 0], 1), False),
            (([1, 1, 1, 0], -100), False),
            (([4, 0, 5, -5, 3, 3, 0, -4, -5], 1), False),
            (([1, 1, 1, 1], -100), False),
            (([1, 1, 1, 0], 100), False),
            (([-3, -2, -5, 3, -4], -1), False),
            (([2, 2, 2, 2], 6), True),
            (([-1, 0, 1, 1], 100), True),
        ],
        ref=lambda nums, target: _three_sum_closest(nums, target),
        starter={
            "python": "def threeSumClosest(nums: List[int], target: int) -> int:\n    pass",
            "javascript": "function threeSumClosest(nums, target) {\n    // your code here\n}",
            "java": "class Solution {\n    public int threeSumClosest(int[] nums, int target) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Sort the array, then fix one element and two-pointer the rest.",
            "Track the closest sum as you go; if you hit the target exactly, return immediately.",
        ],
        solution="Sort nums. For each i, run two pointers lo and hi over the rest, updating the best (closest) sum each iteration based on |current - target|. Adjust pointers by comparing the current sum to target.",
        time_complexity="O(n^2)",
        space_complexity="O(1)",
        constraints=["3 <= nums.length <= 500", "-10^4 <= target <= 10^4"],
    ),
    make_spec(
        id="partition-labels",
        title="Partition Labels",
        difficulty="medium",
        category="Two Pointers",
        companies=["Amazon", "Google", "Facebook", "Microsoft"],
        description="You are given a string `s`. We want to partition the string into as many parts as possible so that each letter appears in at most one part.\n\nReturn a list of integers representing the size of these parts.\n\n**Constraints**\n- 1 <= s.length <= 500\n- s consists of lowercase English letters.",
        examples=[
            {
                "input": 's = "ababcbacadefegdehijhklij"',
                "output": "[9,7,8]",
                "explanation": "The partition is 'ababcbaca', 'defegde', 'hijhklij'.",
            },
            {
                "input": 's = "eccbbbbdec"',
                "output": "[10]",
                "explanation": "All letters share partitions, so the whole string is one part.",
            },
        ],
        tests=[
            (("ababcbacadefegdehijhklij",), False),
            (("eccbbbbdec",), False),
            (("a",), False),
            (("aa",), False),
            (("ab",), False),
            (("aba",), False),
            (("caedbdedda",), False),
            (("qiejxqfnqceocmy",), True),
            (("aaaaabbbbb",), True),
        ],
        ref=lambda *args: _partition_labels(*args),
        starter={
            "python": "def partitionLabels(s: str) -> List[int]:\n    pass",
            "javascript": "function partitionLabels(s) {\n    // your code here\n}",
            "java": "class Solution {\n    public List<Integer> partitionLabels(String s) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Record the last occurrence index of each character.",
            "Extend the current partition's right bound to the max last occurrence seen.",
        ],
        solution="First record the last index of every character. Then scan s, tracking the current partition start and the furthest last-occurrence seen so far. Whenever the scan index reaches that bound, close the partition, record its size, and start a new one.",
        time_complexity="O(n)",
        space_complexity="O(1)",
        constraints=["1 <= s.length <= 500"],
    ),
    make_spec(
        id="trapping-rain-water",
        title="Trapping Rain Water",
        difficulty="hard",
        category="Two Pointers",
        companies=["Google", "Amazon", "Apple", "Microsoft"],
        description="Given n non-negative integers representing an elevation map where the width of each bar is 1, compute how much water it can trap after raining.\n\n**Constraints**\n- n == height.length\n- 1 <= n <= 2 * 10^4\n- 0 <= height[i] <= 10^5",
        examples=[
            {
                "input": "height = [0,1,0,2,1,0,1,3,2,1,2,1]",
                "output": "6",
                "explanation": "Water trapped between the bars totals 6 units.",
            },
            {
                "input": "height = [4,2,0,3,2,5]",
                "output": "9",
                "explanation": "Water trapped totals 9 units.",
            },
        ],
        tests=[
            (([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1],), False),
            (([4, 2, 0, 3, 2, 5],), False),
            (([0, 0, 0, 0],), False),
            (([5, 5, 5, 5],), False),
            (([1, 2, 3, 4, 5],), False),
            (([5, 4, 3, 2, 1],), False),
            (([2, 0, 2],), False),
            (([3, 0, 0, 2, 0, 4],), True),
            (([0, 1, 0, 1, 0, 1, 0],), True),
            (([1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1],), True),
        ],
        ref=lambda *args: _trap(*args),
        starter={
            "python": "def trap(height: List[int]) -> int:\n    pass",
            "javascript": "function trap(height) {\n    // your code here\n}",
            "java": "class Solution {\n    public int trap(int[] height) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Water above index i is min(maxLeft[i], maxRight[i]) - height[i].",
            "Use two pointers to track running max from both sides in O(1) space.",
        ],
        solution="Maintain left and right pointers with running leftMax and rightMax. At each step, if height[left] <= height[right], water trapped at left is leftMax - height[left]; update leftMax and advance left. Otherwise mirror on the right. Accumulate the total.",
        time_complexity="O(n)",
        space_complexity="O(1)",
        constraints=["n == height.length", "1 <= n <= 2 * 10^4"],
    ),
    make_spec(
        id="longest-substring-without-repeating-characters",
        title="Longest Substring Without Repeating Characters",
        difficulty="medium",
        category="Sliding Window",
        companies=["Amazon", "Google", "Apple", "Microsoft", "Facebook"],
        description="Given a string `s`, find the length of the longest substring without repeating characters.\n\n**Constraints**\n- 0 <= s.length <= 5 * 10^4\n- s consists of English letters, digits, symbols and spaces.",
        examples=[
            {
                "input": 's = "abcabcbb"',
                "output": "3",
                "explanation": "The answer is 'abc'.",
            },
            {
                "input": 's = "bbbbb"',
                "output": "1",
                "explanation": "The answer is 'b'.",
            },
            {
                "input": 's = "pwwkew"',
                "output": "3",
                "explanation": "The answer is 'wke'.",
            },
        ],
        tests=[
            (("abcabcbb",), False),
            (("bbbbb",), False),
            (("pwwkew",), False),
            (("",), False),
            (("au",), False),
            (("dvdf",), False),
            (("tmmzuxt",), False),
            (("abba",), False),
            (("abcde",), False),
            (("aab",), False),
            (("qrsvbspk",), True),
            (("abcdeabcdef",), True),
        ],
        ref=lambda *args: _length_of_longest_substring(*args),
        starter={
            "python": "def lengthOfLongestSubstring(s: str) -> int:\n    pass",
            "javascript": "function lengthOfLongestSubstring(s) {\n    // your code here\n}",
            "java": "class Solution {\n    public int lengthOfLongestSubstring(String s) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Use a sliding window with a hash set tracking characters in the window.",
            "When a repeat appears, shrink the left edge until the window is unique again.",
        ],
        solution="Expand a right pointer, adding characters to a set. When a duplicate is encountered, move the left pointer and remove characters until the set no longer contains the duplicate. Track the maximum window size.",
        time_complexity="O(n)",
        space_complexity="O(min(n, charset))",
        constraints=["0 <= s.length <= 5 * 10^4"],
    ),
    make_spec(
        id="longest-repeating-character-replacement",
        title="Longest Repeating Character Replacement",
        difficulty="medium",
        category="Sliding Window",
        companies=["Amazon", "Google", "Facebook", "Apple"],
        description="You are given a string `s` and an integer `k`. You can choose any character of the string and change it to any other uppercase English character. You can perform this operation at most `k` times.\n\nReturn the length of the longest substring containing the same letter you can get after performing the above operations.\n\n**Constraints**\n- 1 <= s.length <= 10^5\n- s consists of only uppercase English letters.\n- 0 <= k <= s.length",
        examples=[
            {
                "input": 's = "ABAB", k = 2',
                "output": "4",
                "explanation": "Replace the two 'A's with 'B's or vice versa.",
            },
            {
                "input": 's = "AABABBA", k = 1',
                "output": "4",
                "explanation": "Replace the 'A' at index 2 with 'B' to get 'AABBBBA'.",
            },
        ],
        tests=[
            (("ABAB", 2), False),
            (("AABABBA", 1), False),
            (("A", 0), False),
            (("A", 1), False),
            (("AAAA", 2), False),
            (("ABCDE", 1), False),
            (("BAAA", 0), False),
            (("AABAA", 1), False),
            (("ABBB", 2), True),
            (("KRSCDCSONAJNHLBMDQGIFCPEOTVDLHZOHHJWBULTAFI", 4), True),
        ],
        ref=lambda s, k: _character_replacement(s, k),
        starter={
            "python": "def characterReplacement(s: str, k: int) -> int:\n    pass",
            "javascript": "function characterReplacement(s, k) {\n    // your code here\n}",
            "java": "class Solution {\n    public int characterReplacement(String s, int k) {\n        // your code here\n    }\n}",
        },
        hints=[
            "A window is valid if windowSize - maxFreq <= k.",
            "Track the max frequency of any character within the current window.",
        ],
        solution="Use a sliding window with a frequency counter. The window is feasible when window length minus the most frequent character count is at most k. Expand the right edge; when infeasible, shrink from the left. Track the longest feasible window.",
        time_complexity="O(n)",
        space_complexity="O(26)",
        constraints=[
            "1 <= s.length <= 10^5",
            "s consists of uppercase English letters",
        ],
    ),
    make_spec(
        id="permutation-in-string",
        title="Permutation in String",
        difficulty="medium",
        category="Sliding Window",
        companies=["Amazon", "Google", "Facebook", "Apple"],
        description="Given two strings `s1` and `s2`, return `true` if `s2` contains a permutation of `s1`, or `false` otherwise.\n\nIn other words, return `true` if one of `s1`'s permutations is the substring of `s2`.\n\n**Constraints**\n- 1 <= s1.length, s2.length <= 10^4\n- s1 and s2 consist of lowercase English letters.",
        examples=[
            {
                "input": 's1 = "ab", s2 = "eidbaooo"',
                "output": "true",
                "explanation": "s2 contains one permutation of s1 ('ba').",
            },
            {
                "input": 's1 = "ab", s2 = "eidboaoo"',
                "output": "false",
                "explanation": "No permutation of s1 appears as a substring.",
            },
        ],
        tests=[
            (("ab", "eidbaooo"), False),
            (("ab", "eidboaoo"), False),
            (("adc", "dcda"), False),
            (("a", "a"), False),
            (("a", "b"), False),
            (("ab", "ba"), False),
            (("hello", "ooolleoooleh"), False),
            (("abc", "ccccbbbbaaaa"), False),
            (("abc", "bbbca"), True),
            (("ab", "eidbaooo"), True),
            (("intention", "execution"), True),
        ],
        ref=lambda s1, s2: _check_inclusion(s1, s2),
        starter={
            "python": "def checkInclusion(s1: str, s2: str) -> bool:\n    pass",
            "javascript": "function checkInclusion(s1, s2) {\n    // your code here\n}",
            "java": "class Solution {\n    public boolean checkInclusion(String s1, String s2) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Count the characters of s1, then slide a window of the same length over s2.",
            "A permutation matches when the character counts are identical.",
        ],
        solution="Build a frequency counter for s1. Slide a window of length len(s1) over s2, maintaining a running counter and the number of matching characters. When the matching count equals 26, return true.",
        time_complexity="O(len(s1) + len(s2))",
        space_complexity="O(26)",
        constraints=["1 <= s1.length, s2.length <= 10^4"],
    ),
    make_spec(
        id="minimum-window-substring",
        title="Minimum Window Substring",
        difficulty="hard",
        category="Sliding Window",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description='Given two strings `s` and `t`, return the minimum window substring of `s` such that every character in `t` (including duplicates) is included in the window.\n\nIf there is no such substring, return the empty string `""`.\n\nThe test cases will generate the answer unique.\n\n**Constraints**\n- m == s.length, n == t.length\n- 1 <= m, n <= 10^5\n- s and t consist of uppercase and lowercase English letters.',
        examples=[
            {
                "input": 's = "ADOBECODEBANC", t = "ABC"',
                "output": '"BANC"',
                "explanation": "The minimum window substring that contains all of A, B, and C is 'BANC'.",
            },
            {
                "input": 's = "a", t = "a"',
                "output": '"a"',
                "explanation": "The only character matches.",
            },
            {
                "input": 's = "a", t = "aa"',
                "output": '""',
                "explanation": "There is only one 'a' but two are needed.",
            },
        ],
        tests=[
            (("ADOBECODEBANC", "ABC"), False),
            (("a", "a"), False),
            (("a", "aa"), False),
            (("ab", "b"), False),
            (("bbaa", "aba"), False),
            (("cabwefgewcwaefgcf", "cae"), False),
            (("abc", "b"), False),
            (("a", "b"), False),
            (("ba", "b"), True),
            (("ADOBECODEBANC", "ABBC"), True),
            (("abc", "abc"), True),
            (("x", "x"), True),
            (("xxxy", "yxx"), True),
        ],
        ref=lambda s, t: _min_window(s, t),
        starter={
            "python": "def minWindow(s: str, t: str) -> str:\n    pass",
            "javascript": "function minWindow(s, t) {\n    // your code here\n}",
            "java": "class Solution {\n    public String minWindow(String s, String t) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Track required counts for characters in t and how many are satisfied.",
            "Expand the right edge until all characters are covered, then shrink the left edge.",
            "Record the smallest valid window.",
        ],
        solution="Use a hash map for t's character requirements and a counter of satisfied requirements. Expand right until all are satisfied, then contract left while requirements stay satisfied, updating the minimal window. Return that window or an empty string if none exists.",
        time_complexity="O(m + n)",
        space_complexity="O(n)",
        constraints=["1 <= m, n <= 10^5", "s and t consist of English letters"],
    ),
]


def _is_palindrome(s: str) -> bool:
    left, right = 0, len(s) - 1
    while left < right:
        while left < right and not s[left].isalnum():
            left += 1
        while left < right and not s[right].isalnum():
            right -= 1
        if s[left].lower() != s[right].lower():
            return False
        left += 1
        right -= 1
    return True


def _is_subsequence(s: str, t: str) -> bool:
    i = 0
    if not s:
        return True
    for ch in t:
        if i < len(s) and ch == s[i]:
            i += 1
            if i == len(s):
                return True
    return i == len(s)


def _two_sum_ii(numbers: List[int], target: int) -> List[int]:
    left, right = 0, len(numbers) - 1
    while left < right:
        total = numbers[left] + numbers[right]
        if total == target:
            return [left + 1, right + 1]
        if total < target:
            left += 1
        else:
            right -= 1
    return []


def _max_area(height: List[int]) -> int:
    left, right = 0, len(height) - 1
    best = 0
    while left < right:
        area = min(height[left], height[right]) * (right - left)
        best = max(best, area)
        if height[left] < height[right]:
            left += 1
        else:
            right -= 1
    return best


def _three_sum_closest(nums: List[int], target: int) -> int:
    nums = sorted(nums)
    n = len(nums)
    best = nums[0] + nums[1] + nums[2]
    for i in range(n - 2):
        lo, hi = i + 1, n - 1
        while lo < hi:
            cur = nums[i] + nums[lo] + nums[hi]
            if abs(cur - target) < abs(best - target):
                best = cur
            if cur < target:
                lo += 1
            elif cur > target:
                hi -= 1
            else:
                return cur
    return best


def _partition_labels(s: str) -> List[int]:
    last = {c: i for i, c in enumerate(s)}
    res = []
    start = 0
    bound = 0
    for i, c in enumerate(s):
        bound = max(bound, last[c])
        if i == bound:
            res.append(i - start + 1)
            start = i + 1
    return res


def _trap(height: List[int]) -> int:
    left, right = 0, len(height) - 1
    left_max = right_max = 0
    total = 0
    while left < right:
        if height[left] <= height[right]:
            left_max = max(left_max, height[left])
            total += left_max - height[left]
            left += 1
        else:
            right_max = max(right_max, height[right])
            total += right_max - height[right]
            right -= 1
    return total


def _length_of_longest_substring(s: str) -> int:
    seen = {}
    left = 0
    best = 0
    for right, ch in enumerate(s):
        if ch in seen and seen[ch] >= left:
            left = seen[ch] + 1
        seen[ch] = right
        best = max(best, right - left + 1)
    return best


def _character_replacement(s: str, k: int) -> int:
    from collections import Counter

    counts = Counter()
    left = 0
    best = 0
    for right, ch in enumerate(s):
        counts[ch] += 1
        max_freq = max(counts.values())
        if right - left + 1 - max_freq > k:
            counts[s[left]] -= 1
            left += 1
        best = max(best, right - left + 1)
    return best


def _check_inclusion(s1: str, s2: str) -> bool:
    from collections import Counter

    if len(s1) > len(s2):
        return False
    need = Counter(s1)
    have = Counter(s2[: len(s1)])
    matches = sum(1 for c in set(list(s1) + list(s2[: len(s1)])) if need[c] == have[c])
    for i in range(len(s1), len(s2)):
        if matches == len(need):
            return True
        add = s2[i]
        remove = s2[i - len(s1)]
        if need[add] == have[add]:
            matches -= 1
        have[add] += 1
        if need[add] == have[add]:
            matches += 1
        if need[remove] == have[remove]:
            matches -= 1
        have[remove] -= 1
        if need[remove] == have[remove]:
            matches += 1
    return matches == len(need)


def _min_window(s: str, t: str) -> str:
    from collections import Counter

    if not s or not t:
        return ""
    need = Counter(t)
    have = Counter()
    required = len(need)
    formed = 0
    left = 0
    ans = ""
    min_len = float("inf")
    for right, ch in enumerate(s):
        have[ch] += 1
        if have[ch] == need[ch]:
            formed += 1
        while left <= right and formed == required:
            if right - left + 1 < min_len:
                min_len = right - left + 1
                ans = s[left : right + 1]
            have[s[left]] -= 1
            if have[s[left]] < need[s[left]]:
                formed -= 1
            left += 1
    return ans
