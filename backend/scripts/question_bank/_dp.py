"""Dynamic Programming questions."""

from __future__ import annotations

from typing import List

from ._helpers import make_spec

SPECS = [
    make_spec(
        id="climbing-stairs",
        title="Climbing Stairs",
        difficulty="easy",
        category="Dynamic Programming",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="You are climbing a staircase. It takes `n` steps to reach the top.\n\nEach time you can either climb 1 or 2 steps. In how many distinct ways can you climb to the top?\n\n**Constraints**\n- 1 <= n <= 45",
        examples=[
            {
                "input": "n = 2",
                "output": "2",
                "explanation": "1 step + 1 step, or 2 steps.",
            },
            {"input": "n = 3", "output": "3", "explanation": "1+1+1, 1+2, or 2+1."},
        ],
        tests=[
            ((2,), False),
            ((3,), False),
            ((1,), False),
            ((4,), False),
            ((5,), False),
            ((6,), False),
            ((10,), False),
            ((45,), False),
            ((7,), True),
            ((20,), True),
        ],
        ref=lambda *args: _climb_stairs(*args),
        starter={
            "python": "def climbStairs(n: int) -> int:\n    pass",
            "javascript": "function climbStairs(n) {\n    // your code here\n}",
            "java": "class Solution {\n    public int climbStairs(int n) {\n        // your code here\n    }\n}",
        },
        hints=[
            "This is the Fibonacci sequence in disguise.",
            "ways(n) = ways(n-1) + ways(n-2).",
        ],
        solution="Define dp[i] as the number of ways to reach step i. dp[0]=1, dp[1]=1, and dp[i] = dp[i-1] + dp[i-2]. Compute iteratively with two rolling variables.",
        time_complexity="O(n)",
        space_complexity="O(1)",
        constraints=["1 <= n <= 45"],
    ),
    make_spec(
        id="house-robber",
        title="House Robber",
        difficulty="hard",
        category="Dynamic Programming",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="You are a professional robber planning to rob houses along a street. Each house has a certain amount of money stashed, the only constraint stopping you from robbing each of them is that adjacent houses have security systems connected and it will automatically contact the police if two adjacent houses were broken into on the same night.\n\nGiven an integer array `nums` representing the amount of money of each house, return the maximum amount of money you can rob tonight without alerting the police.\n\n**Constraints**\n- 1 <= nums.length <= 100\n- 0 <= nums[i] <= 400",
        examples=[
            {
                "input": "nums = [1,2,3,1]",
                "output": "4",
                "explanation": "Rob house 1 (1) and house 3 (3).",
            },
            {
                "input": "nums = [2,7,9,3,1]",
                "output": "12",
                "explanation": "Rob 2, 9, and 1.",
            },
        ],
        tests=[
            (([1, 2, 3, 1],), False),
            (([2, 7, 9, 3, 1],), False),
            (([1],), False),
            (([1, 2],), False),
            (([2, 1, 1, 2],), False),
            (([5, 3, 4, 11, 2],), False),
            (([4, 1, 2, 7, 5, 3, 1],), False),
            (([0],), False),
            (([1, 3, 1, 3, 100],), True),
            (([2, 4, 6, 8, 10],), True),
        ],
        ref=lambda *args: _rob(*args),
        starter={
            "python": "def rob(nums: List[int]) -> int:\n    pass",
            "javascript": "function rob(nums) {\n    // your code here\n}",
            "java": "class Solution {\n    public int rob(int[] nums) {\n        // your code here\n    }\n}",
        },
        hints=[
            "For each house, you either rob it or skip it.",
            "dp[i] = max(dp[i-1], dp[i-2] + nums[i]).",
        ],
        solution="Iterate with prev2 and prev1 representing the best we can do up to two and one houses back. For each house, cur = max(prev1, prev2 + nums[i]); shift prev2 = prev1 and prev1 = cur. Return prev1.",
        time_complexity="O(n)",
        space_complexity="O(1)",
        constraints=["1 <= nums.length <= 100"],
    ),
    make_spec(
        id="coin-change",
        title="Coin Change",
        difficulty="medium",
        category="Dynamic Programming",
        companies=["Amazon", "Google", "Microsoft", "Facebook", "Apple"],
        description="You are given an integer array `coins` representing coins of different denominations and an integer `amount` representing a total amount of money.\n\nReturn the fewest number of coins that you need to make up that amount. If that amount of money cannot be made up by any combination of the coins, return `-1`.\n\nYou may assume that you have an infinite number of each kind of coin.\n\n**Constraints**\n- 1 <= coins.length <= 12\n- 1 <= coins[i] <= 2^31 - 1\n- 0 <= amount <= 10^4",
        examples=[
            {
                "input": "coins = [1,2,5], amount = 11",
                "output": "3",
                "explanation": "11 = 5 + 5 + 1.",
            },
            {
                "input": "coins = [2], amount = 3",
                "output": "-1",
                "explanation": "Cannot make 3 with only 2s.",
            },
            {
                "input": "coins = [1], amount = 0",
                "output": "0",
                "explanation": "Zero coins for zero amount.",
            },
        ],
        tests=[
            (([1, 2, 5], 11), False),
            (([2], 3), False),
            (([1], 0), False),
            (([1, 2, 5], 100), False),
            (([2, 5, 10, 1], 27), False),
            (([3, 5, 7], 11), False),
            (([1], 2), False),
            (([186, 419, 83, 408], 6249), False),
            (([2, 4, 6], 7), True),
            (([5, 3], 4), True),
        ],
        ref=lambda coins, amount: _coin_change(coins, amount),
        starter={
            "python": "def coinChange(coins: List[int], amount: int) -> int:\n    pass",
            "javascript": "function coinChange(coins, amount) {\n    // your code here\n}",
            "java": "class Solution {\n    public int coinChange(int[] coins, int amount) {\n        // your code here\n    }\n}",
        },
        hints=[
            "dp[a] = fewest coins to reach amount a.",
            "For each coin, dp[a] = min(dp[a], dp[a - coin] + 1).",
        ],
        solution="Initialize dp[0]=0 and everything else to a large sentinel. For each amount from 1 to target, try every coin: if the coin fits, update dp[amount] with dp[amount-coin]+1. Return dp[target] if reachable else -1.",
        time_complexity="O(amount * coins)",
        space_complexity="O(amount)",
        constraints=["1 <= coins.length <= 12", "0 <= amount <= 10^4"],
    ),
    make_spec(
        id="longest-increasing-subsequence",
        title="Longest Increasing Subsequence",
        difficulty="hard",
        category="Dynamic Programming",
        companies=["Amazon", "Google", "Microsoft", "Facebook", "Apple"],
        description="Given an integer array `nums`, return the length of the longest strictly increasing subsequence.\n\n**Constraints**\n- 1 <= nums.length <= 2500\n- -10^4 <= nums[i] <= 10^4",
        examples=[
            {
                "input": "nums = [10,9,2,5,3,7,101,18]",
                "output": "4",
                "explanation": "The LIS is [2,3,7,101].",
            },
            {
                "input": "nums = [0,1,0,3,2,3]",
                "output": "4",
                "explanation": "LIS is [0,1,2,3].",
            },
            {
                "input": "nums = [7,7,7,7,7,7,7]",
                "output": "1",
                "explanation": "Strictly increasing means equal values don't count.",
            },
        ],
        tests=[
            (([10, 9, 2, 5, 3, 7, 101, 18],), False),
            (([0, 1, 0, 3, 2, 3],), False),
            (([7, 7, 7, 7, 7, 7, 7],), False),
            (([1],), False),
            (([1, 2, 3, 4, 5],), False),
            (([5, 4, 3, 2, 1],), False),
            (([3, 5, 6, 2, 5, 4, 19, 5, 6, 7, 12],), False),
            (([1, 3, 6, 7, 9, 4, 10, 5, 6],), False),
            (([2, 2, 2, 2],), True),
            (([-1, 0, -2, 1, 2],), True),
            (([4, 10, 4, 3, 8, 9],), True),
        ],
        ref=lambda *args: _length_of_lis(*args),
        starter={
            "python": "def lengthOfLIS(nums: List[int]) -> int:\n    pass",
            "javascript": "function lengthOfLIS(nums) {\n    // your code here\n}",
            "java": "class Solution {\n    public int lengthOfLIS(int[] nums) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Classic O(n^2) DP: dp[i] is the LIS ending at i.",
            "A patience-sorting approach with binary search reaches O(n log n).",
        ],
        solution="Maintain an array `tails` where tails[i] is the smallest tail of an increasing subsequence of length i+1. For each number, binary-search its position in tails and replace/extend. The length of tails is the answer.",
        time_complexity="O(n log n)",
        space_complexity="O(n)",
        constraints=["1 <= nums.length <= 2500"],
    ),
    make_spec(
        id="word-break",
        title="Word Break",
        difficulty="medium",
        category="Dynamic Programming",
        companies=["Amazon", "Google", "Microsoft", "Facebook", "Apple"],
        description="Given a string `s` and a dictionary of strings `wordDict`, return `true` if `s` can be segmented into a space-separated sequence of one or more dictionary words.\n\nNote that the same word in the dictionary may be reused multiple times in the segmentation.\n\n**Constraints**\n- 1 <= s.length <= 300\n- 1 <= wordDict.length <= 1000\n- 1 <= wordDict[i].length <= 20\n- s and wordDict[i] consist of only lowercase English letters.",
        examples=[
            {
                "input": 's = "leetcode", wordDict = ["leet","code"]',
                "output": "true",
                "explanation": "leet + code.",
            },
            {
                "input": 's = "applepenapple", wordDict = ["apple","pen"]',
                "output": "true",
                "explanation": "apple + pen + apple.",
            },
            {
                "input": 's = "catsandog", wordDict = ["cats","dog","sand","and","cat"]',
                "output": "false",
                "explanation": "No valid segmentation.",
            },
        ],
        tests=[
            (("leetcode", ["leet", "code"]), False),
            (("applepenapple", ["apple", "pen"]), False),
            (("catsandog", ["cats", "dog", "sand", "and", "cat"]), False),
            (("a", ["a"]), False),
            (("a", ["b"]), False),
            (("", ["a"]), False),
            (("aaaaaaa", ["aaaa", "aa"]), False),
            (("catsand", ["cats", "and"]), False),
            (("cars", ["car", "ca", "rs"]), True),
            (("aaaa", ["a", "aa"]), True),
            (("leetcode", ["leetc", "code"]), True),
            (("aaaaaaaaaaaaaaaaaaaaaaaaaaab", ["a", "aa", "aaa", "aaaa"]), True),
        ],
        ref=lambda s, wordDict: _word_break(s, wordDict),
        starter={
            "python": "def wordBreak(s: str, wordDict: List[str]) -> bool:\n    pass",
            "javascript": "function wordBreak(s, wordDict) {\n    // your code here\n}",
            "java": "class Solution {\n    public boolean wordBreak(String s, List<String> wordDict) {\n        // your code here\n    }\n}",
        },
        hints=[
            "dp[i] = can prefix s[:i] be segmented?",
            "dp[i] is true if dp[j] and s[j:i] is a dictionary word for some j < i.",
        ],
        solution="Turn wordDict into a set. Compute dp[i] for each prefix length; dp[0]=true. For i from 1 to len(s), dp[i] is true if any j < i has dp[j] and s[j:i] in the set. Return dp[len(s)].",
        time_complexity="O(n^2)",
        space_complexity="O(n)",
        constraints=["1 <= s.length <= 300"],
    ),
    make_spec(
        id="maximum-product-subarray",
        title="Maximum Product Subarray",
        difficulty="medium",
        category="Dynamic Programming",
        companies=["Amazon", "Google", "Microsoft", "Facebook", "Apple"],
        description="Given an integer array `nums`, find a subarray that has the largest product, and return the product.\n\nThe test cases are generated so that the answer will fit in a 32-bit integer.\n\n**Constraints**\n- 1 <= nums.length <= 2 * 10^4\n- -10 <= nums[i] <= 10",
        examples=[
            {
                "input": "nums = [2,3,-2,4]",
                "output": "6",
                "explanation": "The subarray [2,3] has the largest product 6.",
            },
            {
                "input": "nums = [-2,0,-1]",
                "output": "0",
                "explanation": "The largest product is 0.",
            },
            {
                "input": "nums = [-2,3,-4]",
                "output": "24",
                "explanation": "The whole array product is 24.",
            },
        ],
        tests=[
            (([2, 3, -2, 4],), False),
            (([-2, 0, -1],), False),
            (([-2, 3, -4],), False),
            (([1],), False),
            (([0, 2],), False),
            (([-1, -1, -1],), False),
            (([2, 3, 4, 5],), False),
            (([-2, -3, -4, -5],), False),
            (([1, 0, -1, 0, 5],), False),
            (([-3, -1, -1],), True),
            (([2, -5, 3, -2],), True),
            (([0, 0, 0],), True),
        ],
        ref=lambda *args: _max_product(*args),
        starter={
            "python": "def maxProduct(nums: List[int]) -> int:\n    pass",
            "javascript": "function maxProduct(nums) {\n    // your code here\n}",
            "java": "class Solution {\n    public int maxProduct(int[] nums) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Track both the current max and current min product (negatives flip them).",
            "Reset the running products to 1 when a zero is crossed.",
        ],
        solution="Keep cur_max and cur_min initialized to nums[0]. For each number, the new candidates are num, cur_max*num, cur_min*num; set cur_max to the max and cur_min to the min. Track the overall max.",
        time_complexity="O(n)",
        space_complexity="O(1)",
        constraints=["1 <= nums.length <= 2 * 10^4"],
    ),
    make_spec(
        id="decode-ways",
        title="Decode Ways",
        difficulty="medium",
        category="Dynamic Programming",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="A message containing letters from A-Z can be encoded into numbers using the following mapping: 'A' -> \"1\", 'B' -> \"2\", ..., 'Z' -> \"26\".\n\nTo decode an encoded message, all the digits must be grouped then mapped back into letters using the reverse of the mapping above (there may be multiple ways).\n\nGiven a string `s` containing only digits, return the number of ways to decode it.\n\n**Constraints**\n- 1 <= s.length <= 100\n- s contains only digits and may contain leading zero(s).",
        examples=[
            {
                "input": 's = "12"',
                "output": "2",
                "explanation": "It could be decoded as 'AB' (1 2) or 'L' (12).",
            },
            {
                "input": 's = "226"',
                "output": "3",
                "explanation": "'BZ' (2 26), 'VF' (22 6), or 'BBF' (2 2 6).",
            },
            {
                "input": 's = "06"',
                "output": "0",
                "explanation": "06 cannot be mapped because leading zeros are not allowed.",
            },
        ],
        tests=[
            (("12",), False),
            (("226",), False),
            (("06",), False),
            (("1",), False),
            (("0",), False),
            (("10",), False),
            (("27",), False),
            (("101",), False),
            (("111",), False),
            (("1111111111111111111111111111111111111111",), True),
            (("2101",), True),
            (("12345",), True),
        ],
        ref=lambda *args: _num_decodings(*args),
        starter={
            "python": "def numDecodings(s: str) -> int:\n    pass",
            "javascript": "function numDecodings(s) {\n    // your code here\n}",
            "java": "class Solution {\n    public int numDecodings(String s) {\n        // your code here\n    }\n}",
        },
        hints=[
            "dp[i] = ways to decode s[:i].",
            "A single digit 1-9 is valid; a two-digit 10-26 is valid.",
            "Leading zeros invalidate a decode.",
        ],
        solution="dp[0]=1. For each i, if s[i-1] is '1'..'9' add dp[i-1]; if the two-digit s[i-2:i] is 10..26 add dp[i-2]. Return dp[n].",
        time_complexity="O(n)",
        space_complexity="O(n)",
        constraints=["1 <= s.length <= 100"],
    ),
]


def _climb_stairs(n: int) -> int:
    a, b = 1, 1
    for _ in range(1, n):
        a, b = b, a + b
    return b


def _rob(nums: List[int]) -> int:
    prev2, prev1 = 0, 0
    for v in nums:
        cur = max(prev1, prev2 + v)
        prev2, prev1 = prev1, cur
    return prev1


def _coin_change(coins: List[int], amount: int) -> int:
    dp = [float("inf")] * (amount + 1)
    dp[0] = 0
    for a in range(1, amount + 1):
        for c in coins:
            if a - c >= 0:
                dp[a] = min(dp[a], dp[a - c] + 1)
    return int(dp[amount]) if dp[amount] != float("inf") else -1


def _length_of_lis(nums: List[int]) -> int:
    import bisect

    tails = []
    for v in nums:
        i = bisect.bisect_left(tails, v)
        if i == len(tails):
            tails.append(v)
        else:
            tails[i] = v
    return len(tails)


def _word_break(s: str, wordDict: List[str]) -> bool:
    words = set(wordDict)
    dp = [False] * (len(s) + 1)
    dp[0] = True
    for i in range(1, len(s) + 1):
        for j in range(i):
            if dp[j] and s[j:i] in words:
                dp[i] = True
                break
    return dp[len(s)]


def _max_product(nums: List[int]) -> int:
    cur_max = cur_min = best = nums[0]
    for v in nums[1:]:
        candidates = (v, cur_max * v, cur_min * v)
        cur_max = max(candidates)
        cur_min = min(candidates)
        best = max(best, cur_max)
    return best


def _num_decodings(s: str) -> int:
    n = len(s)
    dp = [0] * (n + 1)
    dp[0] = 1
    dp[1] = 1 if s[0] != "0" else 0
    for i in range(2, n + 1):
        one = int(s[i - 1])
        two = int(s[i - 2 : i])
        if 1 <= one <= 9:
            dp[i] += dp[i - 1]
        if 10 <= two <= 26:
            dp[i] += dp[i - 2]
    return dp[n]
