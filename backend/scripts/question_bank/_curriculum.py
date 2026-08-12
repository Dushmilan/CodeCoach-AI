"""Curriculum-linked questions.

These IDs are referenced by exercise lessons in backend/data/courses. They are
re-authored with conventional content while preserving their original IDs so
curriculum links keep resolving.
"""

from __future__ import annotations


from ._helpers import make_spec

SPECS = [
    make_spec(
        id="c9d1a3f2-5b6e-4a7f-8c0d-1e2f3a4b5c6d",
        title="First Word",
        difficulty="easy",
        category="Strings",
        companies=["Amazon", "Microsoft", "Google", "Facebook"],
        description="Given a string `s` containing words separated by spaces, return the first word of the string.\n\n**Rules**\n- A word is a maximal sequence of non-space characters.\n- The string may have leading or trailing spaces.\n- If the string is empty or contains only spaces, return an empty string.\n\n**Constraints**\n- 0 <= s.length <= 10^5\n- s consists of printable ASCII characters.",
        examples=[
            {
                "input": 's = "hello world"',
                "output": '"hello"',
                "explanation": "The first word is 'hello'.",
            },
            {
                "input": 's = "  fly me   to   the moon  "',
                "output": '"fly"',
                "explanation": "Leading spaces are ignored.",
            },
            {
                "input": 's = ""',
                "output": '""',
                "explanation": "Empty string yields an empty word.",
            },
        ],
        tests=[
            (("hello world",), False),
            (("  fly me   to   the moon  ",), False),
            (("",), False),
            (("   ",), False),
            (("one",), False),
            (("a b c",), False),
            (("   hello",), False),
            (("hello   ",), False),
            (("luffy is still joyboy",), False),
            (("code coach",), True),
            (("python",), True),
        ],
        ref=lambda *args: _first_word(*args),
        starter={
            "python": "def first_word(s: str) -> str:\n    pass",
            "javascript": "function firstWord(s) {\n    // your code here\n}",
            "java": "class Solution {\n    public String firstWord(String s) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Split the string on whitespace and take the first element.",
            "Remember to handle empty input.",
        ],
        solution="Strip the string, split on whitespace, and return the first word. If no words exist, return an empty string.",
        time_complexity="O(n)",
        space_complexity="O(n)",
        constraints=["0 <= s.length <= 10^5"],
    ),
    make_spec(
        id="f7e2d4a1-3b5c-4d6e-8f9a-0b1c2d3e4f5a",
        title="Valid Palindrome",
        difficulty="easy",
        category="Strings",
        companies=["Amazon", "Facebook", "Google", "Microsoft"],
        description="A phrase is a palindrome if, after converting all uppercase letters into lowercase letters and removing all non-alphanumeric characters, it reads the same forward and backward.\n\nGiven a string `s`, return `true` if it is a palindrome, or `false` otherwise.\n\n**Constraints**\n- 1 <= s.length <= 2 * 10^5\n- s consists only of printable ASCII characters.",
        examples=[
            {
                "input": 's = "A man, a plan, a canal: Panama"',
                "output": "true",
                "explanation": "After cleaning it reads 'amanaplanacanalpanama'.",
            },
            {
                "input": 's = "race a car"',
                "output": "false",
                "explanation": "Cleaned it reads 'raceacar', not a palindrome.",
            },
            {
                "input": 's = " "',
                "output": "true",
                "explanation": "After removing non-alphanumerics it is empty, which is a palindrome.",
            },
        ],
        tests=[
            (("A man, a plan, a canal: Panama",), False),
            (("race a car",), False),
            ((" ",), False),
            (("ab_a",), False),
            (("0P",), False),
            (("a",), False),
            (("a.",), False),
            ((".,",), False),
            (("ab ba",), False),
            (("121",), True),
            (("Was it a car or a cat I saw?",), True),
            (("Never odd or even",), True),
            (("not a palindrome",), True),
        ],
        ref=lambda *args: _valid_palindrome(*args),
        starter={
            "python": "def is_palindrome(s: str) -> bool:\n    pass",
            "javascript": "function isPalindrome(s) {\n    // your code here\n}",
            "java": "class Solution {\n    public boolean isPalindrome(String s) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Use two pointers moving inward, skipping non-alphanumerics.",
            "Compare characters case-insensitively.",
        ],
        solution="Filter to alphanumeric characters, lowercase them, and compare with two pointers from both ends. Return false on the first mismatch.",
        time_complexity="O(n)",
        space_complexity="O(n)",
        constraints=["1 <= s.length <= 2 * 10^5"],
    ),
    make_spec(
        id="7b9d2c1a-3e4f-5a6b-7c8d-9e0f1a2b3c4d",
        title="Most Frequent Character",
        difficulty="easy",
        category="Strings",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="Given a string `s`, return the character that appears most frequently in the string.\n\n**Rules**\n- Only lowercase English letters are considered.\n- If there is a tie, return the character that appears earliest in the string.\n- If the string is empty, return an empty string.\n\n**Constraints**\n- 0 <= s.length <= 10^5\n- s consists of lowercase English letters.",
        examples=[
            {
                "input": 's = "bookkeeper"',
                "output": '"e"',
                "explanation": "'e' appears 3 times, more than any other character.",
            },
            {
                "input": 's = "aabbbcc"',
                "output": '"b"',
                "explanation": "'b' appears 3 times.",
            },
            {
                "input": 's = "abc"',
                "output": '"a"',
                "explanation": "All appear once; 'a' comes first in the string.",
            },
        ],
        tests=[
            (("bookkeeper",), False),
            (("aabbbcc",), False),
            (("abc",), False),
            (("",), False),
            (("a",), False),
            (("zzzz",), False),
            (("aaabbb",), False),
            (("banana",), False),
            (("zzzaa",), True),
            (("mississippi",), True),
            (("aaab",), True),
        ],
        ref=lambda *args: _most_frequent_char(*args),
        starter={
            "python": "def most_frequent_char(s: str) -> str:\n    pass",
            "javascript": "function mostFrequentChar(s) {\n    // your code here\n}",
            "java": "class Solution {\n    public String mostFrequentChar(String s) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Count occurrences of each character.",
            "Tie-break by earliest position in the string.",
        ],
        solution="Count each character. Track the best character by highest count, breaking ties by the earliest first occurrence.",
        time_complexity="O(n)",
        space_complexity="O(26)",
        constraints=["0 <= s.length <= 10^5"],
    ),
]


def _first_word(s: str) -> str:
    words = s.strip().split()
    return words[0] if words else ""


def _valid_palindrome(s: str) -> bool:
    cleaned = "".join(ch.lower() for ch in s if ch.isalnum())
    return cleaned == cleaned[::-1]


def _most_frequent_char(s: str) -> str:
    if not s:
        return ""
    counts = {}
    first_seen = {}
    for i, ch in enumerate(s):
        counts[ch] = counts.get(ch, 0) + 1
        if ch not in first_seen:
            first_seen[ch] = i
    best = max(counts, key=lambda ch: (counts[ch], -first_seen[ch]))
    return best
