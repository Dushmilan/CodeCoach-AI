"""Additional easy & hard questions to complete the 100-question bank."""

from __future__ import annotations

from typing import List

from ._helpers import make_spec

SPECS = [
    make_spec(
        id="best-time-to-buy-and-sell-stock",
        title="Best Time to Buy and Sell Stock",
        difficulty="easy",
        category="Sliding Window",
        companies=["Amazon", "Google", "Microsoft", "Facebook", "Apple"],
        description="You are given an array `prices` where `prices[i]` is the price of a given stock on the i-th day.\n\nYou want to maximize your profit by choosing a single day to buy one stock and choosing a different day in the future to sell that stock.\n\nReturn the maximum profit you can achieve from this transaction. If you cannot achieve any profit, return `0`.\n\n**Constraints**\n- 1 <= prices.length <= 10^5\n- 0 <= prices[i] <= 10^4",
        examples=[
            {
                "input": "prices = [7,1,5,3,6,4]",
                "output": "5",
                "explanation": "Buy at 1 (day 2), sell at 6 (day 5), profit 5.",
            },
            {
                "input": "prices = [7,6,4,3,1]",
                "output": "0",
                "explanation": "No profit possible.",
            },
        ],
        tests=[
            (([7, 1, 5, 3, 6, 4],), False),
            (([7, 6, 4, 3, 1],), False),
            (([1],), False),
            (([1, 2],), False),
            (([2, 1],), False),
            (([3, 3],), False),
            (([1, 2, 3, 4, 5],), False),
            (([5, 4, 3, 2, 1],), False),
            (([2, 4, 1],), False),
            (([3, 2, 6, 5, 0, 3],), False),
            (([1, 5, 2, 8],), True),
            (([100, 1, 50, 100],), True),
            (([2, 9, 1, 5],), True),
        ],
        ref=lambda *args: _max_profit(*args),
        starter={
            "python": "def maxProfit(prices: List[int]) -> int:\n    pass",
            "javascript": "function maxProfit(prices) {\n    // your code here\n}",
            "java": "class Solution {\n    public int maxProfit(int[] prices) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Track the minimum price seen so far.",
            "Profit at day i is prices[i] - min_so_far; maximize it.",
        ],
        solution="Scan the array tracking the minimum price seen so far. For each day, compute the potential profit and keep the maximum.",
        time_complexity="O(n)",
        space_complexity="O(1)",
        constraints=["1 <= prices.length <= 10^5"],
    ),
    make_spec(
        id="move-zeroes",
        title="Move Zeroes",
        difficulty="easy",
        category="Two Pointers",
        companies=["Amazon", "Google", "Microsoft", "Facebook", "Apple"],
        description="Given an integer array `nums`, move all `0`'s to the end of it while maintaining the relative order of the non-zero elements.\n\nNote that you must do this in-place without making a copy of the array.\n\nReturn the modified array.\n\n**Constraints**\n- 1 <= nums.length <= 10^4\n- -2^31 <= nums[i] <= 2^31 - 1",
        examples=[
            {
                "input": "nums = [0,1,0,3,12]",
                "output": "[1,3,12,0,0]",
                "explanation": "Non-zeros keep order, zeros moved to the end.",
            },
            {"input": "nums = [0]", "output": "[0]", "explanation": "Single zero."},
        ],
        tests=[
            (([0, 1, 0, 3, 12],), False),
            (([0],), False),
            (([1, 0],), False),
            (([0, 0, 1],), False),
            (([1, 2, 3],), False),
            (([0, 0, 0],), False),
            (([1, 0, 0, 1],), False),
            (([4, 2, 4, 0, 0, 3, 0, 5, 1, 0],), False),
            (([0, 1, 0, 3, 12],), True),
            (([5, 0, 7, 0, 9],), True),
            (([0, 0, 1, 0],), True),
        ],
        ref=lambda *args: _move_zeroes(*args),
        starter={
            "python": "def moveZeroes(nums: List[int]) -> List[int]:\n    pass",
            "javascript": "function moveZeroes(nums) {\n    // your code here\n}",
            "java": "class Solution {\n    public int[] moveZeroes(int[] nums) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Use a slow pointer that marks where the next non-zero should go.",
            "Swap or overwrite non-zeros forward.",
        ],
        solution="Maintain a write index. For each non-zero element, write it at the write index and increment. After the scan, fill the rest with zeros.",
        time_complexity="O(n)",
        space_complexity="O(1)",
        constraints=["1 <= nums.length <= 10^4"],
        in_place=True,
    ),
    make_spec(
        id="missing-number",
        title="Missing Number",
        difficulty="easy",
        category="Bit Manipulation",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="Given an array `nums` containing n distinct numbers in the range [0, n], return the only number in the range that is missing from the array.\n\n**Constraints**\n- n == nums.length\n- 1 <= n <= 10^4\n- 0 <= nums[i] <= n\n- All the numbers of nums are unique.",
        examples=[
            {
                "input": "nums = [3,0,1]",
                "output": "2",
                "explanation": "The range is [0,3]; 2 is missing.",
            },
            {
                "input": "nums = [0,1]",
                "output": "2",
                "explanation": "n = 2, so 2 is missing.",
            },
            {
                "input": "nums = [9,6,4,2,3,5,7,0,1]",
                "output": "8",
                "explanation": "8 is the missing number.",
            },
        ],
        tests=[
            (([3, 0, 1],), False),
            (([0, 1],), False),
            (([9, 6, 4, 2, 3, 5, 7, 0, 1],), False),
            (([0],), False),
            (([1],), False),
            (([1, 0],), False),
            (([2, 0],), False),
            (([0, 1, 2, 3],), False),
            (([0, 1, 2, 4],), True),
            (([3, 2, 1],), True),
        ],
        ref=lambda *args: _missing_number(*args),
        starter={
            "python": "def missingNumber(nums: List[int]) -> int:\n    pass",
            "javascript": "function missingNumber(nums) {\n    // your code here\n}",
            "java": "class Solution {\n    public int missingNumber(int[] nums) {\n        // your code here\n    }\n}",
        },
        hints=[
            "The expected sum of [0..n] is n*(n+1)/2.",
            "Subtract the actual sum to find the missing number.",
            "XOR is an O(1)-space alternative.",
        ],
        solution="Compute n*(n+1)//2 and subtract the sum of the array; the difference is the missing number.",
        time_complexity="O(n)",
        space_complexity="O(1)",
        constraints=["n == nums.length", "1 <= n <= 10^4"],
    ),
    make_spec(
        id="power-of-two",
        title="Power of Two",
        difficulty="easy",
        category="Bit Manipulation",
        companies=["Amazon", "Google", "Microsoft"],
        description="Given an integer `n`, return `true` if it is a power of two. Otherwise, return `false`.\n\nAn integer n is a power of two, if there exists an integer x such that n == 2^x.\n\n**Constraints**\n- -2^31 <= n <= 2^31 - 1",
        examples=[
            {"input": "n = 1", "output": "true", "explanation": "1 = 2^0."},
            {"input": "n = 16", "output": "true", "explanation": "16 = 2^4."},
            {
                "input": "n = 3",
                "output": "false",
                "explanation": "3 is not a power of two.",
            },
        ],
        tests=[
            ((1,), False),
            ((16,), False),
            ((3,), False),
            ((0,), False),
            ((-16,), False),
            ((2,), False),
            ((4,), False),
            ((8,), False),
            ((32,), False),
            ((1024,), False),
            ((6,), True),
            ((2147483647,), True),
            ((64,), True),
        ],
        ref=lambda *args: _is_power_of_two(*args),
        starter={
            "python": "def isPowerOfTwo(n: int) -> bool:\n    pass",
            "javascript": "function isPowerOfTwo(n) {\n    // your code here\n}",
            "java": "class Solution {\n    public boolean isPowerOfTwo(int n) {\n        // your code here\n    }\n}",
        },
        hints=[
            "A power of two has exactly one set bit.",
            "n & (n - 1) == 0 for positive powers of two.",
        ],
        solution="Return n > 0 and n & (n - 1) == 0.",
        time_complexity="O(1)",
        space_complexity="O(1)",
        constraints=["-2^31 <= n <= 2^31 - 1"],
    ),
    make_spec(
        id="happy-number",
        title="Happy Number",
        difficulty="easy",
        category="Bit Manipulation",
        companies=["Amazon", "Google", "Microsoft"],
        description="Write an algorithm to determine if a number `n` is happy.\n\nA happy number is a number defined by the following process:\n- Starting with any positive integer, replace the number by the sum of the squares of its digits.\n- Repeat the process until the number equals 1 (where it will stay), or it loops endlessly in a cycle which does not include 1.\n- Those numbers for which this process ends in 1 are happy.\n\nReturn `true` if n is a happy number, and `false` if not.\n\n**Constraints**\n- 1 <= n <= 2^31 - 1",
        examples=[
            {
                "input": "n = 19",
                "output": "true",
                "explanation": "1^2 + 9^2 = 82 -> 68 -> 100 -> 1.",
            },
            {
                "input": "n = 2",
                "output": "false",
                "explanation": "The process loops without reaching 1.",
            },
        ],
        tests=[
            ((19,), False),
            ((2,), False),
            ((1,), False),
            ((7,), False),
            ((4,), False),
            ((100,), False),
            ((68,), False),
            ((20,), False),
            ((49,), False),
            ((32,), False),
            ((13,), True),
            ((91,), True),
            ((999,), True),
        ],
        ref=lambda *args: _is_happy(*args),
        starter={
            "python": "def isHappy(n: int) -> bool:\n    pass",
            "javascript": "function isHappy(n) {\n    // your code here\n}",
            "java": "class Solution {\n    public boolean isHappy(int n) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Simulate the process with a set to detect cycles.",
            "If you ever see a number twice, it is not happy.",
        ],
        solution="Repeatedly replace n with the sum of the squares of its digits, tracking visited numbers in a set. Return true when n reaches 1 and false when a repeat is detected.",
        time_complexity="O(log n) per iteration, bounded cycles",
        space_complexity="O(cycle length)",
        constraints=["1 <= n <= 2^31 - 1"],
    ),
    make_spec(
        id="sliding-window-maximum",
        title="Sliding Window Maximum",
        difficulty="hard",
        category="Heaps & Priority Queues",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="You are given an array of integers `nums`, there is a sliding window of size `k` which is moving from the very left of the array to the very right. You can only see the `k` numbers in the window. Each time the sliding window moves right by one position.\n\nReturn the max sliding window.\n\n**Constraints**\n- 1 <= nums.length <= 10^5\n- 1 <= k <= nums.length",
        examples=[
            {
                "input": "nums = [1,3,-1,-3,5,3,6,7], k = 3",
                "output": "[3,3,5,5,6,7]",
                "explanation": "Each window's maximum.",
            },
            {
                "input": "nums = [1], k = 1",
                "output": "[1]",
                "explanation": "Single element.",
            },
        ],
        tests=[
            (([1, 3, -1, -3, 5, 3, 6, 7], 3), False),
            (([1], 1), False),
            (([1, -1], 1), False),
            (([9, 11], 2), False),
            (([4, -2], 2), False),
            (([1, 2, 3, 4, 5], 3), False),
            (([5, 4, 3, 2, 1], 3), False),
            (([1, 3, 1, 2, 0, 5], 3), False),
            (([7, 2, 4], 2), True),
            (([1, 2, 3, 4, 5, 6, 7], 4), True),
            (([8, 7, 6, 5, 4], 2), True),
        ],
        ref=lambda nums, k: _max_sliding_window(nums, k),
        starter={
            "python": "def maxSlidingWindow(nums: List[int], k: int) -> List[int]:\n    pass",
            "javascript": "function maxSlidingWindow(nums, k) {\n    // your code here\n}",
            "java": "class Solution {\n    public int[] maxSlidingWindow(int[] nums, int k) {\n        // your code here\n    }\n}",
        },
        hints=[
            "A monotonic decreasing deque keeps candidate maximums.",
            "Pop from the back while the new element is larger; expire indices from the front.",
        ],
        solution="Maintain a deque of indices whose values are decreasing. For each new element, pop smaller elements from the back, push the new index, and remove the front if it falls outside the window. The front is the window's max.",
        time_complexity="O(n)",
        space_complexity="O(k)",
        constraints=["1 <= nums.length <= 10^5", "1 <= k <= nums.length"],
    ),
    make_spec(
        id="longest-valid-parentheses",
        title="Longest Valid Parentheses",
        difficulty="hard",
        category="Stack & Queue",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="Given a string containing just the characters `'('` and `')'`, return the length of the longest valid (well-formed) parentheses substring.\n\n**Constraints**\n- 0 <= s.length <= 3 * 10^4\n- s[i] is '(' or ')'.",
        examples=[
            {
                "input": 's = "(()"',
                "output": "2",
                "explanation": "The longest valid substring is '()'.",
            },
            {
                "input": 's = ")()())"',
                "output": "4",
                "explanation": "The longest valid substring is '()()'.",
            },
            {"input": 's = ""', "output": "0", "explanation": "Empty string."},
        ],
        tests=[
            (("(()",), False),
            ((")()())",), False),
            (("",), False),
            (("()",), False),
            (("()(())",), False),
            (("())",), False),
            (("))(()((",), False),
            (("(()))())(",), False),
            (("((()))",), False),
            (("()()()",), True),
            (("((()))",), True),
            ((")()()(",), True),
            (("()((())",), True),
        ],
        ref=lambda *args: _longest_valid_parentheses(*args),
        starter={
            "python": "def longestValidParentheses(s: str) -> int:\n    pass",
            "javascript": "function longestValidParentheses(s) {\n    // your code here\n}",
            "java": "class Solution {\n    public int longestValidParentheses(String s) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Push indices onto a stack, seeding with -1.",
            "A valid substring length is the difference between the current index and the stack top.",
        ],
        solution="Maintain a stack of indices, starting with -1. On '(', push the index. On ')', pop; if the stack is empty push the current index, otherwise the valid length ending here is i - stack[-1]. Track the maximum.",
        time_complexity="O(n)",
        space_complexity="O(n)",
        constraints=["0 <= s.length <= 3 * 10^4"],
    ),
    make_spec(
        id="edit-distance",
        title="Edit Distance",
        difficulty="hard",
        category="Dynamic Programming",
        companies=["Amazon", "Google", "Microsoft", "Facebook", "Apple"],
        description="Given two strings `word1` and `word2`, return the minimum number of operations required to convert `word1` to `word2`.\n\nYou have the following three operations permitted on a word:\n- Insert a character\n- Delete a character\n- Replace a character\n\n**Constraints**\n- 0 <= word1.length, word2.length <= 500\n- word1 and word2 consist of lowercase English letters.",
        examples=[
            {
                "input": 'word1 = "horse", word2 = "ros"',
                "output": "3",
                "explanation": "horse -> rorse (replace h) -> rose (remove r) -> ros (remove e).",
            },
            {
                "input": 'word1 = "intention", word2 = "execution"',
                "output": "5",
                "explanation": "Five operations are needed.",
            },
        ],
        tests=[
            (("horse", "ros"), False),
            (("intention", "execution"), False),
            (("", ""), False),
            (("a", ""), False),
            (("", "a"), False),
            (("a", "a"), False),
            (("ab", "ba"), False),
            (("abc", "abc"), False),
            (("cat", "cut"), True),
            (("kitten", "sitting"), True),
            (("flaw", "lawn"), True),
            (("distance", "editing"), True),
        ],
        ref=lambda word1, word2: _min_distance(word1, word2),
        starter={
            "python": "def minDistance(word1: str, word2: str) -> int:\n    pass",
            "javascript": "function minDistance(word1, word2) {\n    // your code here\n}",
            "java": "class Solution {\n    public int minDistance(String word1, String word2) {\n        // your code here\n    }\n}",
        },
        hints=[
            "dp[i][j] = edits to convert word1[:i] to word2[:j].",
            "If characters match, carry the diagonal; otherwise min of insert/delete/replace.",
        ],
        solution="Use a 2D dp where dp[i][j] is the edit distance between prefixes. If word1[i-1] == word2[j-1] copy dp[i-1][j-1]; otherwise take 1 + min of the three neighbors. Answer is dp[m][n].",
        time_complexity="O(m * n)",
        space_complexity="O(m * n)",
        constraints=["0 <= word1.length, word2.length <= 500"],
    ),
    make_spec(
        id="word-ladder",
        title="Word Ladder",
        difficulty="hard",
        category="Graphs",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="A transformation sequence from word `beginWord` to word `endWord` using a dictionary `wordList` is a sequence of words such that:\n- The first word is beginWord.\n- The last word is endWord.\n- Only one letter is different between each adjacent pair of words.\n- Every intermediate word is in wordList.\n\nReturn the number of words in the shortest transformation sequence from beginWord to endWord, or `0` if no such sequence exists.\n\n**Constraints**\n- 1 <= beginWord.length <= 10\n- wordList contains all lowercase English words of length beginWord.length.\n- beginWord, endWord, and wordList[i] consist of lowercase English letters.",
        examples=[
            {
                "input": 'beginWord = "hit", endWord = "cog", wordList = ["hot","dot","dog","lot","log","cog"]',
                "output": "5",
                "explanation": "hit -> hot -> dot -> dog -> cog is the shortest (5 words).",
            },
            {
                "input": 'beginWord = "hit", endWord = "cog", wordList = ["hot","dot","dog","lot","log"]',
                "output": "0",
                "explanation": "cog is not in the list.",
            },
        ],
        tests=[
            (("hit", "cog", ["hot", "dot", "dog", "lot", "log", "cog"]), False),
            (("hit", "cog", ["hot", "dot", "dog", "lot", "log"]), False),
            (("a", "c", ["a", "b", "c"]), False),
            (("hot", "dog", ["hot", "dog"]), False),
            (("hit", "cog", ["hot", "dot", "dog", "lot", "log"]), False),
            (
                (
                    "toon",
                    "plea",
                    ["poon", "plee", "same", "poie", "plea", "plie", "poin"],
                ),
                False,
            ),
            (("a", "c", ["b", "c"]), True),
            (("hit", "cog", ["hot", "dot", "dog", "lot", "log", "cog"]), True),
            (("cat", "dog", ["bat", "cot", "dot", "dog"]), True),
            (("hot", "dog", ["hot", "dot", "dog"]), True),
        ],
        ref=lambda beginWord, endWord, wordList: _ladder_length(
            beginWord, endWord, wordList
        ),
        starter={
            "python": "def ladderLength(beginWord: str, endWord: str, wordList: List[str]) -> int:\n    pass",
            "javascript": "function ladderLength(beginWord, endWord, wordList) {\n    // your code here\n}",
            "java": "class Solution {\n    public int ladderLength(String beginWord, String endWord, List<String> wordList) {\n        // your code here\n    }\n}",
        },
        hints=[
            "BFS from beginWord to endWord over words differing by one letter.",
            "Use a set for O(1) neighbor checks by mutating each character position.",
        ],
        solution="BFS over the word graph. For each word, try replacing each position with every letter a-z; if the result is in the word set and unvisited, enqueue it with the next depth. Return the depth when endWord is reached, else 0.",
        time_complexity="O(n * L * 26)",
        space_complexity="O(n)",
        constraints=["1 <= beginWord.length <= 10"],
    ),
    make_spec(
        id="burst-balloons",
        title="Burst Balloons",
        difficulty="hard",
        category="Dynamic Programming",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="You are given `n` balloons, indexed from 0 to n - 1. Each balloon is painted with a number on it represented by an array `nums`. You are asked to burst all the balloons.\n\nIf you burst the i-th balloon, you will get `nums[left] * nums[i] * nums[right]` coins. Here `left` and `right` are adjacent indices of i. After the burst, the `left` and `right` then becomes adjacent.\n\nReturn the maximum coins you can collect by bursting the balloons wisely.\n\n**Constraints**\n- n == nums.length\n- 1 <= n <= 300\n- 0 <= nums[i] <= 100",
        examples=[
            {
                "input": "nums = [3,1,5,8]",
                "output": "167",
                "explanation": "Burst in an optimal order yields 167 coins.",
            },
            {
                "input": "nums = [1,5]",
                "output": "10",
                "explanation": "Burst either balloon first yields 10.",
            },
        ],
        tests=[
            (([3, 1, 5, 8],), False),
            (([1, 5],), False),
            (([1],), False),
            (([1, 2, 3],), False),
            (([5, 5],), False),
            (([3, 1, 5, 8],), False),
            (([1, 2, 3, 4, 5],), False),
            (([7, 9, 8, 0, 7, 1, 3, 5, 5, 2, 3],), False),
            (([2, 2],), True),
            (([1, 2, 3, 4],), True),
            (([9, 76, 64, 21],), True),
        ],
        ref=lambda *args: _max_coins(*args),
        starter={
            "python": "def maxCoins(nums: List[int]) -> int:\n    pass",
            "javascript": "function maxCoins(nums) {\n    // your code here\n}",
            "java": "class Solution {\n    public int maxCoins(int[] nums) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Append virtual balloons of value 1 at both ends.",
            "dp[i][j] = max coins from bursting all balloons between i and j.",
            "Think about which balloon is the last one burst in a range.",
        ],
        solution="Extend nums with 1s at both ends. Use interval DP: dp[i][j] is the max coins obtained by bursting all balloons strictly inside (i, j). For the last balloon k in the range, dp[i][j] = max(dp[i][k] + nums[i]*nums[k]*nums[j] + dp[k][j]).",
        time_complexity="O(n^3)",
        space_complexity="O(n^2)",
        constraints=["n == nums.length", "1 <= n <= 300"],
    ),
]


def _max_profit(prices: List[int]) -> int:
    min_price = prices[0]
    best = 0
    for p in prices[1:]:
        best = max(best, p - min_price)
        min_price = min(min_price, p)
    return best


def _move_zeroes(nums: List[int]) -> List[int]:
    write = 0
    for v in nums:
        if v != 0:
            nums[write] = v
            write += 1
    for i in range(write, len(nums)):
        nums[i] = 0
    return nums


def _missing_number(nums: List[int]) -> int:
    n = len(nums)
    return n * (n + 1) // 2 - sum(nums)


def _is_power_of_two(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0


def _is_happy(n: int) -> bool:
    def next_num(x: int) -> int:
        return sum(int(d) ** 2 for d in str(x))

    seen = set()
    while n != 1 and n not in seen:
        seen.add(n)
        n = next_num(n)
    return n == 1


def _max_sliding_window(nums: List[int], k: int) -> List[int]:
    from collections import deque

    dq = deque()
    out = []
    for i, v in enumerate(nums):
        while dq and nums[dq[-1]] <= v:
            dq.pop()
        dq.append(i)
        if dq[0] <= i - k:
            dq.popleft()
        if i >= k - 1:
            out.append(nums[dq[0]])
    return out


def _longest_valid_parentheses(s: str) -> int:
    stack = [-1]
    best = 0
    for i, ch in enumerate(s):
        if ch == "(":
            stack.append(i)
        else:
            stack.pop()
            if not stack:
                stack.append(i)
            else:
                best = max(best, i - stack[-1])
    return best


def _min_distance(word1: str, word2: str) -> int:
    m, n = len(word1), len(word2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if word1[i - 1] == word2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    return dp[m][n]


def _ladder_length(beginWord: str, endWord: str, wordList: List[str]) -> int:
    from collections import deque

    words = set(wordList)
    if endWord not in words:
        return 0
    q = deque([(beginWord, 1)])
    visited = {beginWord}
    while q:
        word, depth = q.popleft()
        if word == endWord:
            return depth
        for i in range(len(word)):
            for c in "abcdefghijklmnopqrstuvwxyz":
                nxt = word[:i] + c + word[i + 1 :]
                if nxt in words and nxt not in visited:
                    visited.add(nxt)
                    q.append((nxt, depth + 1))
    return 0


def _max_coins(nums: List[int]) -> int:
    n = len(nums)
    padded = [1] + nums + [1]
    dp = [[0] * (n + 2) for _ in range(n + 2)]
    for length in range(1, n + 1):
        for i in range(1, n - length + 2):
            j = i + length - 1
            for k in range(i, j + 1):
                dp[i][j] = max(
                    dp[i][j],
                    dp[i][k - 1]
                    + padded[i - 1] * padded[k] * padded[j + 1]
                    + dp[k + 1][j],
                )
    return dp[1][n]
