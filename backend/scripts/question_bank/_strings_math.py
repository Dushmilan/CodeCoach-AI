"""Strings, Bit Manipulation & Math questions."""

from __future__ import annotations

from typing import List

from ._helpers import make_spec

SPECS = [
    make_spec(
        id="reverse-string",
        title="Reverse String",
        difficulty="easy",
        category="Strings",
        companies=["Amazon", "Microsoft", "Google", "Facebook"],
        description="Write a function that reverses a string. The input string is given as an array of characters `s`.\n\nYou must do this by modifying the input array in-place with O(1) extra memory.\n\n**Constraints**\n- 1 <= s.length <= 10^5\n- s[i] is a printable ascii character.",
        examples=[
            {
                "input": 's = ["h","e","l","l","o"]',
                "output": '["o","l","l","e","h"]',
                "explanation": "The reversed string.",
            },
            {
                "input": 's = ["H","a","n","n","a","h"]',
                "output": '["h","a","n","n","a","H"]',
                "explanation": "The reversed string.",
            },
        ],
        tests=[
            ((["h", "e", "l", "l", "o"],), False),
            ((["H", "a", "n", "n", "a", "h"],), False),
            ((["a"],), False),
            ((["a", "b"],), False),
            (([],), False),
            ((["A", "B", "C", "D"],), False),
            ((["1", "2", "3", "4", "5"],), False),
            ((["x", "y", "z"],), True),
            ((["a", "b", "c", "d", "e", "f", "g"],), True),
        ],
        ref=lambda *args: _reverse_string(*args),
        starter={
            "python": "def reverseString(s: List[str]) -> List[str]:\n    pass",
            "javascript": "function reverseString(s) {\n    // your code here\n}",
            "java": "class Solution {\n    public char[] reverseString(char[] s) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Swap the two ends and move inward.",
            "Two pointers: left at 0, right at len-1.",
        ],
        solution="Use two pointers at the two ends, swapping characters and moving inward until they meet.",
        time_complexity="O(n)",
        space_complexity="O(1)",
        constraints=["1 <= s.length <= 10^5"],
        in_place=True,
    ),
    make_spec(
        id="valid-anagram",
        title="Valid Anagram",
        difficulty="easy",
        category="Strings",
        companies=["Amazon", "Google", "Microsoft", "Facebook", "Apple"],
        description="Given two strings `s` and `t`, return `true` if `t` is an anagram of `s`, and `false` otherwise.\n\nAn Anagram is a word or phrase formed by rearranging the letters of a different word or phrase, typically using all the original letters exactly once.\n\n**Constraints**\n- 1 <= s.length, t.length <= 5 * 10^4\n- s and t consist of lowercase English letters.",
        examples=[
            {
                "input": 's = "anagram", t = "nagaram"',
                "output": "true",
                "explanation": "Both contain the same letters.",
            },
            {
                "input": 's = "rat", t = "car"',
                "output": "false",
                "explanation": "Different letters.",
            },
        ],
        tests=[
            (("anagram", "nagaram"), False),
            (("rat", "car"), False),
            (("a", "a"), False),
            (("a", "b"), False),
            (("ab", "ba"), False),
            (("abc", "abd"), False),
            (("aacc", "ccac"), False),
            (("listen", "silent"), True),
            (("elvis", "lives"), True),
            (("aa", "aa"), True),
            (("", ""), True),
        ],
        ref=lambda s, t: _is_anagram(s, t),
        starter={
            "python": "def isAnagram(s: str, t: str) -> bool:\n    pass",
            "javascript": "function isAnagram(s, t) {\n    // your code here\n}",
            "java": "class Solution {\n    public boolean isAnagram(String s, String t) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Count the letters of each word.",
            "Anagrams must have identical character counts.",
        ],
        solution="Count the characters of s in one counter, then decrement for each character of t; if any count goes negative or the lengths differ, return false.",
        time_complexity="O(n)",
        space_complexity="O(1)",
        constraints=["1 <= s.length, t.length <= 5 * 10^4"],
    ),
    make_spec(
        id="ransom-note",
        title="Ransom Note",
        difficulty="easy",
        category="Strings",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="Given two strings `ransomNote` and `magazine`, return `true` if `ransomNote` can be constructed by using the letters from `magazine` and `false` otherwise.\n\nEach letter in `magazine` can only be used once in `ransomNote`.\n\n**Constraints**\n- 1 <= ransomNote.length, magazine.length <= 10^5\n- ransomNote and magazine consist of lowercase English letters.",
        examples=[
            {
                "input": 'ransomNote = "a", magazine = "b"',
                "output": "false",
                "explanation": "'b' cannot build 'a'.",
            },
            {
                "input": 'ransomNote = "aa", magazine = "ab"',
                "output": "false",
                "explanation": "Only one 'a' is available.",
            },
            {
                "input": 'ransomNote = "aa", magazine = "aab"',
                "output": "true",
                "explanation": "Two 'a's are available.",
            },
        ],
        tests=[
            (("a", "b"), False),
            (("aa", "ab"), False),
            (("aa", "aab"), False),
            (("a", "a"), False),
            (("abc", "def"), False),
            (("abc", "ab"), False),
            (("ab", "aab"), False),
            (("abc", "abc"), True),
            (("abc", "cba"), True),
            (("abbc", "aabbcc"), True),
            (("a", "aaa"), True),
        ],
        ref=lambda ransomNote, magazine: _can_construct(ransomNote, magazine),
        starter={
            "python": "def canConstruct(ransomNote: str, magazine: str) -> bool:\n    pass",
            "javascript": "function canConstruct(ransomNote, magazine) {\n    // your code here\n}",
            "java": "class Solution {\n    public boolean canConstruct(String ransomNote, String magazine) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Count the magazine's letters, then spend them on the note.",
            "If any letter in the note has no remaining supply, return false.",
        ],
        solution="Count magazine letters. For each character in ransomNote, decrement its count; if the count would go negative, return false. Otherwise return true.",
        time_complexity="O(m + n)",
        space_complexity="O(1)",
        constraints=["1 <= ransomNote.length, magazine.length <= 10^5"],
    ),
    make_spec(
        id="longest-common-prefix",
        title="Longest Common Prefix",
        difficulty="easy",
        category="Strings",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description='Write a function to find the longest common prefix string amongst an array of strings.\n\nIf there is no common prefix, return an empty string `""`.\n\n**Constraints**\n- 1 <= strs.length <= 200\n- 0 <= strs[i].length <= 200\n- strs[i] consists of only lowercase English letters.',
        examples=[
            {
                "input": 'strs = ["flower","flow","flight"]',
                "output": '"fl"',
                "explanation": "Common prefix of all three.",
            },
            {
                "input": 'strs = ["dog","racecar","car"]',
                "output": '""',
                "explanation": "No common prefix.",
            },
        ],
        tests=[
            ((["flower", "flow", "flight"],), False),
            ((["dog", "racecar", "car"],), False),
            ((["a"],), False),
            ((["", "b"],), False),
            ((["a", "a"],), False),
            ((["ab", "abc", "abd"],), False),
            ((["aa", "a"],), False),
            ((["prefix", "pre", "preset"],), True),
            ((["cir", "car"],), True),
            ((["flower", "flower", "flower", "flower"],), True),
            ((["same", "same"],), True),
        ],
        ref=lambda *args: _longest_common_prefix(*args),
        starter={
            "python": "def longestCommonPrefix(strs: List[str]) -> str:\n    pass",
            "javascript": "function longestCommonPrefix(strs) {\n    // your code here\n}",
            "java": "class Solution {\n    public String longestCommonPrefix(String[] strs) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Compare characters position by position across all strings.",
            "Stop at the first mismatch or when a string ends.",
        ],
        solution="Start with the first string as the prefix. For each subsequent string, shorten the prefix until it is a prefix of that string. If the prefix becomes empty, return an empty string.",
        time_complexity="O(s)",
        space_complexity="O(1)",
        constraints=["1 <= strs.length <= 200"],
    ),
    make_spec(
        id="single-number",
        title="Single Number",
        difficulty="easy",
        category="Bit Manipulation",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="Given a non-empty array of integers `nums`, every element appears twice except for one. Find that single one.\n\nYou must implement a solution with a linear runtime complexity and use only constant extra space.\n\n**Constraints**\n- 1 <= nums.length <= 3 * 10^4\n- -3 * 10^4 <= nums[i] <= 3 * 10^4\n- Each element in the array appears twice except for one element which appears only once.",
        examples=[
            {
                "input": "nums = [2,2,1]",
                "output": "1",
                "explanation": "1 appears once.",
            },
            {
                "input": "nums = [4,1,2,1,2]",
                "output": "4",
                "explanation": "4 appears once.",
            },
            {"input": "nums = [1]", "output": "1", "explanation": "Single element."},
        ],
        tests=[
            (([2, 2, 1],), False),
            (([4, 1, 2, 1, 2],), False),
            (([1],), False),
            (([5, 5, 3, 3, 9],), False),
            (([1, 2, 2, 3, 3, 4, 4],), False),
            (([-1, -1, 7],), False),
            (([10, 10, 10],), False),
            (([1, 0, 1],), False),
            (([0, 0, 0, 0, 5],), True),
            (([7, 7, 8],), True),
        ],
        ref=lambda *args: _single_number(*args),
        starter={
            "python": "def singleNumber(nums: List[int]) -> int:\n    pass",
            "javascript": "function singleNumber(nums) {\n    // your code here\n}",
            "java": "class Solution {\n    public int singleNumber(int[] nums) {\n        // your code here\n    }\n}",
        },
        hints=[
            "a XOR a = 0, and XOR is commutative and associative.",
            "XOR all numbers; the paired values cancel out.",
        ],
        solution="Initialize result to 0 and XOR it with every element. Every value that appears twice cancels, leaving the single number.",
        time_complexity="O(n)",
        space_complexity="O(1)",
        constraints=["1 <= nums.length <= 3 * 10^4"],
    ),
    make_spec(
        id="number-of-1-bits",
        title="Number of 1 Bits",
        difficulty="easy",
        category="Bit Manipulation",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="Write a function that takes the binary representation of an unsigned integer and returns the number of '1' bits it has (also known as the Hamming weight).\n\nNote that the integer is given as a 32-bit unsigned integer.\n\n**Constraints**\n- The input must be a binary string of length 32.",
        examples=[
            {
                "input": "n = 11",
                "output": "3",
                "explanation": "11 in binary is 00000000000000000000000000001011, which has 3 set bits.",
            },
            {
                "input": "n = 128",
                "output": "1",
                "explanation": "128 in binary is 10000000..., one set bit.",
            },
            {
                "input": "n = 4294967293",
                "output": "31",
                "explanation": "11111111111111111111111111111101 has 31 set bits.",
            },
        ],
        tests=[
            ((11,), False),
            ((128,), False),
            ((4294967293,), False),
            ((0,), False),
            ((1,), False),
            ((2,), False),
            ((7,), False),
            ((2147483647,), False),
            ((4294967295,), True),
            ((5,), True),
            ((8,), True),
        ],
        ref=lambda *args: _hamming_weight(*args),
        starter={
            "python": "def hammingWeight(n: int) -> int:\n    pass",
            "javascript": "function hammingWeight(n) {\n    // your code here\n}",
            "java": "class Solution {\n    public int hammingWeight(int n) {\n        // your code here\n    }\n}",
        },
        hints=[
            "n & (n - 1) clears the lowest set bit.",
            "Count how many times you can do that before n becomes 0.",
        ],
        solution="Loop while n is non-zero: increment a counter and set n = n & (n-1). Return the counter.",
        time_complexity="O(number of set bits)",
        space_complexity="O(1)",
        constraints=["The input is a 32-bit unsigned integer"],
    ),
    make_spec(
        id="reverse-integer",
        title="Reverse Integer",
        difficulty="medium",
        category="Math",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="Given a signed 32-bit integer `x`, return `x` with its digits reversed. If reversing `x` causes the value to go outside the signed 32-bit integer range [-2^31, 2^31 - 1], then return 0.\n\n**Constraints**\n- -2^31 <= x <= 2^31 - 1",
        examples=[
            {"input": "x = 123", "output": "321", "explanation": "Reversed digits."},
            {
                "input": "x = -123",
                "output": "-321",
                "explanation": "Sign is preserved.",
            },
            {
                "input": "x = 120",
                "output": "21",
                "explanation": "Leading zero dropped.",
            },
        ],
        tests=[
            ((123,), False),
            ((-123,), False),
            ((120,), False),
            ((0,), False),
            ((1534236469,), False),
            ((1463847412,), False),
            ((-2147483648,), False),
            ((9,), False),
            ((100,), False),
            ((2147483647,), True),
            ((-120,), True),
            ((901000,), True),
        ],
        ref=lambda *args: _reverse_int(*args),
        starter={
            "python": "def reverse(x: int) -> int:\n    pass",
            "javascript": "function reverse(x) {\n    // your code here\n}",
            "java": "class Solution {\n    public int reverse(int x) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Repeatedly extract the last digit with % 10 and build the result.",
            "Check overflow before each multiply-accumulate step.",
        ],
        solution="Loop while x is non-zero: pop the last digit, check if multiplying result by 10 and adding the digit would overflow the 32-bit range, then accumulate. Return 0 on overflow.",
        time_complexity="O(log x)",
        space_complexity="O(1)",
        constraints=["-2^31 <= x <= 2^31 - 1"],
    ),
    make_spec(
        id="rotate-image",
        title="Rotate Image",
        difficulty="medium",
        category="Arrays & Hashing",
        companies=["Amazon", "Apple", "Adobe", "Microsoft", "Google"],
        description="You are given an `n x n` 2D matrix representing an image. Rotate the image by 90 degrees clockwise.\n\nYou have to rotate the image in-place, which means you have to modify the input 2D matrix directly. DO NOT allocate another 2D matrix and do the rotation.\n\nReturn the rotated matrix.\n\n**Constraints**\n- n == matrix.length == matrix[i].length\n- 1 <= n <= 20\n- -1000 <= matrix[i][j] <= 1000",
        examples=[
            {
                "input": "matrix = [[1,2,3],[4,5,6],[7,8,9]]",
                "output": "[[7,4,1],[8,5,2],[9,6,3]]",
                "explanation": "90-degree clockwise rotation.",
            },
            {
                "input": "matrix = [[5,1,9,11],[2,4,8,10],[13,3,6,7],[15,14,12,16]]",
                "output": "[[15,13,2,5],[14,3,4,1],[12,6,8,9],[16,7,10,11]]",
                "explanation": "A 4x4 rotation.",
            },
        ],
        tests=[
            (([[1, 2, 3], [4, 5, 6], [7, 8, 9]],), False),
            (([[5, 1, 9, 11], [2, 4, 8, 10], [13, 3, 6, 7], [15, 14, 12, 16]],), False),
            (([[1]],), False),
            (([[1, 2], [3, 4]],), False),
            (([[0, 0], [0, 0]],), False),
            (([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]],), False),
            (([[1, 0], [0, 1]],), True),
            (([[2, 3], [4, 5]],), True),
            (([[10, 20], [30, 40]],), True),
        ],
        ref=lambda *args: _rotate_image(*args),
        starter={
            "python": "def rotate(matrix: List[List[int]]) -> List[List[int]]:\n    pass",
            "javascript": "function rotate(matrix) {\n    // your code here\n}",
            "java": "class Solution {\n    public int[][] rotate(int[][] matrix) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Transpose the matrix (swap matrix[i][j] with matrix[j][i]).",
            "Then reverse each row.",
        ],
        solution="First transpose the matrix in-place, then reverse every row. This produces a 90-degree clockwise rotation.",
        time_complexity="O(n^2)",
        space_complexity="O(1)",
        constraints=["n == matrix.length == matrix[i].length", "1 <= n <= 20"],
        in_place=True,
    ),
    make_spec(
        id="next-permutation",
        title="Next Permutation",
        difficulty="medium",
        category="Arrays & Hashing",
        companies=["Google", "Amazon", "Microsoft", "Facebook"],
        description="A permutation of an array of integers is an arrangement of its members into a sequence or linear order.\n\nThe next permutation of an array of integers is the next lexicographically greater permutation of its integer. If the arrangement is not possible, it must rearrange it as the lowest possible order (i.e., sorted in ascending order).\n\nModify the array in-place and return it.\n\n**Constraints**\n- 1 <= nums.length <= 100\n- 0 <= nums[i] <= 100",
        examples=[
            {
                "input": "nums = [1,2,3]",
                "output": "[1,3,2]",
                "explanation": "The next permutation of 123 is 132.",
            },
            {
                "input": "nums = [3,2,1]",
                "output": "[1,2,3]",
                "explanation": "Already the last permutation, so wrap to the smallest.",
            },
            {
                "input": "nums = [1,1,5]",
                "output": "[1,5,1]",
                "explanation": "The next permutation.",
            },
        ],
        tests=[
            (([1, 2, 3],), False),
            (([3, 2, 1],), False),
            (([1, 1, 5],), False),
            (([1],), False),
            (([1, 2],), False),
            (([2, 1],), False),
            (([1, 3, 2],), False),
            (([2, 3, 1],), False),
            (([1, 2, 3, 4],), True),
            (([4, 3, 2, 1],), True),
            (([1, 5, 1],), True),
        ],
        ref=lambda *args: _next_permutation(*args),
        starter={
            "python": "def nextPermutation(nums: List[int]) -> List[int]:\n    pass",
            "javascript": "function nextPermutation(nums) {\n    // your code here\n}",
            "java": "class Solution {\n    public int[] nextPermutation(int[] nums) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Find the rightmost index where nums[i] < nums[i+1].",
            "Swap it with the smallest larger element to its right, then reverse the suffix.",
        ],
        solution="Scan from the right for the first decrease at index i. If none exists, reverse the whole array. Otherwise find the smallest element to the right that is greater than nums[i], swap, then reverse the suffix after i.",
        time_complexity="O(n)",
        space_complexity="O(1)",
        constraints=["1 <= nums.length <= 100"],
        in_place=True,
    ),
]


def _reverse_string(s: List[str]) -> List[str]:
    left, right = 0, len(s) - 1
    while left < right:
        s[left], s[right] = s[right], s[left]
        left += 1
        right -= 1
    return s


def _is_anagram(s: str, t: str) -> bool:
    from collections import Counter

    return Counter(s) == Counter(t)


def _can_construct(ransomNote: str, magazine: str) -> bool:
    from collections import Counter

    available = Counter(magazine)
    for ch in ransomNote:
        if available[ch] <= 0:
            return False
        available[ch] -= 1
    return True


def _longest_common_prefix(strs: List[str]) -> str:
    if not strs:
        return ""
    prefix = strs[0]
    for s in strs[1:]:
        while not s.startswith(prefix):
            prefix = prefix[:-1]
            if not prefix:
                return ""
    return prefix


def _single_number(nums: List[int]) -> int:
    result = 0
    for v in nums:
        result ^= v
    return result


def _hamming_weight(n: int) -> int:
    count = 0
    while n:
        n &= n - 1
        count += 1
    return count


def _reverse_int(x: int) -> int:
    sign = -1 if x < 0 else 1
    x = abs(x)
    result = 0
    while x:
        result = result * 10 + (x % 10)
        x //= 10
    result *= sign
    if result < -(2**31) or result > 2**31 - 1:
        return 0
    return result


def _rotate_image(matrix: List[List[int]]) -> List[List[int]]:
    n = len(matrix)
    for i in range(n):
        for j in range(i + 1, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
    for row in matrix:
        row.reverse()
    return matrix


def _next_permutation(nums: List[int]) -> List[int]:
    n = len(nums)
    i = n - 2
    while i >= 0 and nums[i] >= nums[i + 1]:
        i -= 1
    if i >= 0:
        j = n - 1
        while nums[j] <= nums[i]:
            j -= 1
        nums[i], nums[j] = nums[j], nums[i]
    left, right = i + 1, n - 1
    while left < right:
        nums[left], nums[right] = nums[right], nums[left]
        left += 1
        right -= 1
    return nums
