"""Backtracking & Greedy questions."""

from __future__ import annotations

from typing import List

from ._helpers import make_spec

SPECS = [
    make_spec(
        id="subsets",
        title="Subsets",
        difficulty="medium",
        category="Backtracking",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="Given an integer array `nums` of unique elements, return all possible subsets (the power set).\n\nThe solution set must not contain duplicate subsets. Return the solution in any order.\n\n**Constraints**\n- 1 <= nums.length <= 10\n- -10 <= nums[i] <= 10\n- All the numbers of nums are unique.",
        examples=[
            {
                "input": "nums = [1,2,3]",
                "output": "[[],[1],[2],[1,2],[3],[1,3],[2,3],[1,2,3]]",
                "explanation": "All 2^3 subsets.",
            },
            {
                "input": "nums = [0]",
                "output": "[[],[0]]",
                "explanation": "Empty and full.",
            },
        ],
        tests=[
            (([1, 2, 3],), False),
            (([0],), False),
            (([1],), False),
            (([1, 2],), False),
            (([],), False),
            (([1, 2, 3, 4],), False),
            (([1, 2, 3, 4, 5],), False),
            (([1, 2, 3, 4, 5, 6],), True),
            (([5, 6, 7],), True),
        ],
        ref=lambda *args: _subsets(*args),
        starter={
            "python": "def subsets(nums: List[int]) -> List[List[int]]:\n    pass",
            "javascript": "function subsets(nums) {\n    // your code here\n}",
            "java": "class Solution {\n    public List<List<Integer>> subsets(int[] nums) {\n        // your code here\n    }\n}",
        },
        hints=[
            "At each index, either include the element or skip it.",
            "This is naturally a backtracking or iterative accumulation problem.",
        ],
        solution="Start with [[]]. For each number, extend the current result by appending the number to every existing subset. This yields all 2^n subsets.",
        time_complexity="O(2^n)",
        space_complexity="O(2^n)",
        constraints=["1 <= nums.length <= 10"],
    ),
    make_spec(
        id="permutations",
        title="Permutations",
        difficulty="medium",
        category="Backtracking",
        companies=["Amazon", "Google", "Microsoft", "Facebook", "Apple"],
        description="Given an array `nums` of distinct integers, return all the possible permutations. You can return the answer in any order.\n\n**Constraints**\n- 1 <= nums.length <= 6\n- -10 <= nums[i] <= 10\n- All the integers of nums are unique.",
        examples=[
            {
                "input": "nums = [1,2,3]",
                "output": "[[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]",
                "explanation": "All 6 permutations.",
            },
            {
                "input": "nums = [0,1]",
                "output": "[[0,1],[1,0]]",
                "explanation": "Two permutations.",
            },
            {
                "input": "nums = [1]",
                "output": "[[1]]",
                "explanation": "One permutation.",
            },
        ],
        tests=[
            (([1, 2, 3],), False),
            (([0, 1],), False),
            (([1],), False),
            (([1, 2, 3, 4],), False),
            (([1, 2],), False),
            (([1, 2, 3, 4, 5],), False),
            (([1, 2, 3, 4, 5, 6],), True),
            (([5, 4, 3],), True),
        ],
        ref=lambda *args: _permute(*args),
        starter={
            "python": "def permute(nums: List[int]) -> List[List[int]]:\n    pass",
            "javascript": "function permute(nums) {\n    // your code here\n}",
            "java": "class Solution {\n    public List<List<Integer>> permute(int[] nums) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Choose an element for each position and recurse on the remainder.",
            "Track used indices to avoid repeats.",
        ],
        solution="Backtrack by picking one unused element per position, recursing until the permutation is full, then backtracking to try the next choice.",
        time_complexity="O(n * n!)",
        space_complexity="O(n!)",
        constraints=["1 <= nums.length <= 6"],
    ),
    make_spec(
        id="combination-sum",
        title="Combination Sum",
        difficulty="medium",
        category="Backtracking",
        companies=["Amazon", "Google", "Microsoft", "Facebook", "Apple"],
        description="Given an array of distinct integers `candidates` and a target integer `target`, return a list of all unique combinations of `candidates` where the chosen numbers sum to `target`. You may return the combinations in any order.\n\nThe same number may be chosen from `candidates` an unlimited number of times. Two combinations are unique if the frequency of at least one of the chosen numbers is different.\n\n**Constraints**\n- 1 <= candidates.length <= 30\n- 2 <= candidates[i] <= 40\n- 1 <= target <= 40\n- All elements of candidates are distinct.",
        examples=[
            {
                "input": "candidates = [2,3,6,7], target = 7",
                "output": "[[2,2,3],[7]]",
                "explanation": "2+2+3=7 and 7=7.",
            },
            {
                "input": "candidates = [2,3,5], target = 8",
                "output": "[[2,2,2,2],[2,3,3],[3,5]]",
                "explanation": "Three ways to sum to 8.",
            },
            {
                "input": "candidates = [2], target = 1",
                "output": "[]",
                "explanation": "Cannot sum to 1.",
            },
        ],
        tests=[
            (([2, 3, 6, 7], 7), False),
            (([2, 3, 5], 8), False),
            (([2], 1), False),
            (([2, 4, 6], 8), False),
            (([5, 10, 25], 20), False),
            (([3, 5, 8], 11), False),
            (([2, 3, 7], 18), False),
            (([7, 3, 2], 18), True),
            (([2, 3, 5, 7], 7), True),
            (([2], 8), True),
            (([4, 2, 8], 8), True),
        ],
        ref=lambda candidates, target: _combination_sum(candidates, target),
        starter={
            "python": "def combinationSum(candidates: List[int], target: int) -> List[List[int]]:\n    pass",
            "javascript": "function combinationSum(candidates, target) {\n    // your code here\n}",
            "java": "class Solution {\n    public List<List<Integer>> combinationSum(int[] candidates, int target) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Backtrack while subtracting each candidate from the remaining target.",
            "Start the recursion at the current index so the same number can be reused.",
            "Skip candidates that exceed the remaining target.",
        ],
        solution="Sort candidates, then backtrack over indices: at each step choose a candidate, subtract from the remaining target, and recurse from the same index. Add the combination when remaining hits zero.",
        time_complexity="O(2^(target/min))",
        space_complexity="O(target/min)",
        constraints=["1 <= candidates.length <= 30", "1 <= target <= 40"],
    ),
    make_spec(
        id="generate-parentheses",
        title="Generate Parentheses",
        difficulty="hard",
        category="Backtracking",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="Given `n` pairs of parentheses, write a function to generate all combinations of well-formed parentheses.\n\n**Constraints**\n- 1 <= n <= 8",
        examples=[
            {
                "input": "n = 3",
                "output": '["((()))","(()())","(())()","()(())","()()()"]',
                "explanation": "All 5 well-formed combinations.",
            },
            {
                "input": "n = 1",
                "output": '["()"]',
                "explanation": "The only well-formed pair.",
            },
        ],
        tests=[
            ((3,), False),
            ((1,), False),
            ((2,), False),
            ((4,), False),
            ((5,), False),
            ((6,), False),
            ((7,), False),
            ((8,), True),
            ((3,), True),
        ],
        ref=lambda *args: _generate_parenthesis(*args),
        starter={
            "python": "def generateParenthesis(n: int) -> List[str]:\n    pass",
            "javascript": "function generateParenthesis(n) {\n    // your code here\n}",
            "java": "class Solution {\n    public List<String> generateParenthesis(int n) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Only add '(' if open < n.",
            "Only add ')' if close < open.",
            "A combination is complete when open == close == n.",
        ],
        solution="Backtrack with counts of open and close parentheses placed so far. Append '(' when open < n and ')' when close < open, collecting the string when both equal n.",
        time_complexity="O(4^n / sqrt(n))",
        space_complexity="O(4^n / sqrt(n))",
        constraints=["1 <= n <= 8"],
    ),
    make_spec(
        id="word-search",
        title="Word Search",
        difficulty="medium",
        category="Backtracking",
        companies=["Amazon", "Google", "Microsoft", "Facebook", "Apple"],
        description="Given an m x n grid of characters `board` and a string `word`, return `true` if `word` exists in the grid.\n\nThe word can be constructed from letters of sequentially adjacent cells, where adjacent cells are horizontally or vertically neighboring. The same letter cell may not be used more than once.\n\n**Constraints**\n- m == board.length\n- n = board[i].length\n- 1 <= m, n <= 6\n- 1 <= word.length <= 15\n- board and word consists of only lowercase and uppercase English letters.",
        examples=[
            {
                "input": 'board = [["A","B","C","E"],["S","F","C","S"],["A","D","E","E"]], word = "ABCCED"',
                "output": "true",
                "explanation": "The word follows a valid path.",
            },
            {
                "input": 'board = [["A","B","C","E"],["S","F","C","S"],["A","D","E","E"]], word = "SEE"',
                "output": "true",
                "explanation": "The word follows a valid path.",
            },
            {
                "input": 'board = [["A","B","C","E"],["S","F","C","S"],["A","D","E","E"]], word = "ABCB"',
                "output": "false",
                "explanation": "No valid path for ABCB.",
            },
        ],
        tests=[
            (
                (
                    [["A", "B", "C", "E"], ["S", "F", "C", "S"], ["A", "D", "E", "E"]],
                    "ABCCED",
                ),
                False,
            ),
            (
                (
                    [["A", "B", "C", "E"], ["S", "F", "C", "S"], ["A", "D", "E", "E"]],
                    "SEE",
                ),
                False,
            ),
            (
                (
                    [["A", "B", "C", "E"], ["S", "F", "C", "S"], ["A", "D", "E", "E"]],
                    "ABCB",
                ),
                False,
            ),
            (([["a"]], "a"), False),
            (([["a"]], "b"), False),
            (([["a", "b"], ["c", "d"]], "abcd"), False),
            (
                (
                    [["A", "B", "C", "E"], ["S", "F", "C", "S"], ["A", "D", "E", "E"]],
                    "ABCCED",
                ),
                True,
            ),
            (([["a", "a", "a", "a"], ["a", "a", "a", "a"]], "aaaaaaaaaa"), True),
            (([["C", "A", "A"], ["A", "A", "A"], ["B", "C", "D"]], "AAB"), True),
            (([["a", "b"], ["c", "d"]], "acdb"), True),
        ],
        ref=lambda board, word: _exist(board, word),
        starter={
            "python": "def exist(board: List[List[str]], word: str) -> bool:\n    pass",
            "javascript": "function exist(board, word) {\n    // your code here\n}",
            "java": "class Solution {\n    public boolean exist(char[][] board, String word) {\n        // your code here\n    }\n}",
        },
        hints=[
            "DFS from each cell that matches the first letter.",
            "Mark cells visited during a path and unmark when backtracking.",
        ],
        solution="For each starting cell matching word[0], run DFS. At each step match the current letter, temporarily mark the cell visited, and try all four directions. Unmark when backtracking.",
        time_complexity="O(m * n * 4^L)",
        space_complexity="O(L)",
        constraints=["1 <= m, n <= 6", "1 <= word.length <= 15"],
    ),
    make_spec(
        id="jump-game",
        title="Jump Game",
        difficulty="medium",
        category="Greedy",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="You are given an integer array `nums`. You are initially positioned at the array's first index, and each element in the array represents your maximum jump length at that position.\n\nReturn `true` if you can reach the last index, or `false` otherwise.\n\n**Constraints**\n- 1 <= nums.length <= 10^4\n- 0 <= nums[i] <= 10^5",
        examples=[
            {
                "input": "nums = [2,3,1,1,4]",
                "output": "true",
                "explanation": "Jump 1 step to index 1, then 3 steps to the last index.",
            },
            {
                "input": "nums = [3,2,1,0,4]",
                "output": "false",
                "explanation": "You cannot reach the last index.",
            },
        ],
        tests=[
            (([2, 3, 1, 1, 4],), False),
            (([3, 2, 1, 0, 4],), False),
            (([1],), False),
            (([0],), False),
            (([2, 0, 0],), False),
            (([1, 1, 1, 0],), False),
            (([2, 0, 1, 0],), False),
            (([1, 2, 3],), True),
            (([3, 0, 8, 2, 0, 1],), True),
            (([2, 5, 0, 0],), True),
            (([1, 0, 1, 0],), True),
        ],
        ref=lambda *args: _can_jump(*args),
        starter={
            "python": "def canJump(nums: List[int]) -> bool:\n    pass",
            "javascript": "function canJump(nums) {\n    // your code here\n}",
            "java": "class Solution {\n    public boolean canJump(int[] nums) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Track the furthest reachable index as you scan.",
            "If the current index exceeds the furthest reachable index, you're stuck.",
        ],
        solution="Track max_reach starting at 0. For each index i, if i > max_reach return false; otherwise update max_reach = max(max_reach, i + nums[i]). Return true if you finish.",
        time_complexity="O(n)",
        space_complexity="O(1)",
        constraints=["1 <= nums.length <= 10^4"],
    ),
    make_spec(
        id="jump-game-ii",
        title="Jump Game II",
        difficulty="medium",
        category="Greedy",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="You are given a 0-indexed array of integers `nums` of length n. You are initially positioned at `nums[0]`.\n\nEach element `nums[i]` represents the maximum length of a forward jump from index i. In other words, if you are at nums[i], you can jump to any nums[i + j] where 0 <= j <= nums[i] and i + j < n.\n\nReturn the minimum number of jumps to reach `nums[n - 1]`. The test cases are generated such that you can reach `nums[n - 1]`.\n\n**Constraints**\n- 1 <= nums.length <= 10^4\n- 0 <= nums[i] <= 1000",
        examples=[
            {
                "input": "nums = [2,3,1,1,4]",
                "output": "2",
                "explanation": "Jump 1 step to index 1, then 3 steps to the last index.",
            },
            {
                "input": "nums = [2,3,0,1,4]",
                "output": "2",
                "explanation": "Jump 1 step to index 1, then 3 steps.",
            },
        ],
        tests=[
            (([2, 3, 1, 1, 4],), False),
            (([2, 3, 0, 1, 4],), False),
            (([0],), False),
            (([1],), False),
            (([1, 2],), False),
            (([1, 1, 1, 1],), False),
            (([2, 1],), False),
            (([3, 2, 1],), False),
            (([1, 2, 3],), True),
            (([2, 0, 2, 0, 1],), True),
            (([5, 4, 3, 2, 1, 0],), True),
            (([7, 0, 9, 6, 9, 6, 1, 7, 9, 0, 1, 2, 9, 0, 3],), True),
        ],
        ref=lambda *args: _jump(*args),
        starter={
            "python": "def jump(nums: List[int]) -> int:\n    pass",
            "javascript": "function jump(nums) {\n    // your code here\n}",
            "java": "class Solution {\n    public int jump(int[] nums) {\n        // your code here\n    }\n}",
        },
        hints=[
            "BFS-like: each 'jump' extends a window of reachable indices.",
            "Track current jump's end and the furthest index reachable within it.",
        ],
        solution="Use three variables: jumps, current_end, and furthest. For each index within current_end, update furthest. When the index reaches current_end, increment jumps and set current_end = furthest.",
        time_complexity="O(n)",
        space_complexity="O(1)",
        constraints=["1 <= nums.length <= 10^4"],
    ),
    make_spec(
        id="gas-station",
        title="Gas Station",
        difficulty="medium",
        category="Greedy",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="There are n gas stations along a circular route, where the amount of gas at the i-th station is `gas[i]`.\n\nYou have a car with an unlimited gas tank and it costs `cost[i]` of gas to travel from the i-th station to its next station. You begin the journey with an empty tank at one of the gas stations.\n\nGiven two integer arrays `gas` and `cost`, return the starting gas station's index if you can travel around the circuit once in the clockwise direction, otherwise return `-1`. If there exists a solution, it is guaranteed to be unique.\n\n**Constraints**\n- n == gas.length == cost.length\n- 1 <= n <= 10^5\n- 0 <= gas[i], cost[i] <= 10^4",
        examples=[
            {
                "input": "gas = [1,2,3,4,5], cost = [3,4,5,1,2]",
                "output": "3",
                "explanation": "Start at station 3 with enough gas to complete the loop.",
            },
            {
                "input": "gas = [2,3,4], cost = [3,4,3]",
                "output": "-1",
                "explanation": "Total gas is less than total cost.",
            },
        ],
        tests=[
            (([1, 2, 3, 4, 5], [3, 4, 5, 1, 2]), False),
            (([2, 3, 4], [3, 4, 3]), False),
            (([5, 1, 2, 3, 4], [4, 4, 1, 5, 1]), False),
            (([1], [1]), False),
            (([4], [5]), False),
            (([5], [4]), False),
            (([1, 2], [2, 1]), False),
            (([2, 2], [1, 3]), False),
            (([4, 5, 2, 6, 5, 3], [3, 2, 7, 3, 2, 9]), True),
            (([1, 2, 3, 4, 5, 5, 70], [2, 3, 4, 3, 9, 6, 2]), True),
            (([3, 1, 1], [1, 2, 2]), True),
        ],
        ref=lambda gas, cost: _can_complete_circuit(gas, cost),
        starter={
            "python": "def canCompleteCircuit(gas: List[int], cost: List[int]) -> int:\n    pass",
            "javascript": "function canCompleteCircuit(gas, cost) {\n    // your code here\n}",
            "java": "class Solution {\n    public int canCompleteCircuit(int[] gas, int[] cost) {\n        // your code here\n    }\n}",
        },
        hints=[
            "If total gas is less than total cost, no start exists.",
            "Track the running surplus; reset the candidate start when it goes negative.",
        ],
        solution="Compute total gas vs total cost; if total < 0 return -1. Track surplus and a candidate start. When surplus drops below zero, set start to the next index and reset surplus. Return start.",
        time_complexity="O(n)",
        space_complexity="O(1)",
        constraints=["n == gas.length == cost.length", "1 <= n <= 10^5"],
    ),
    make_spec(
        id="hand-of-straights",
        title="Hand of Straights",
        difficulty="hard",
        category="Greedy",
        companies=["Amazon", "Google", "Microsoft"],
        description="Alice has some number of cards and she wants to rearrange the cards into groups so that each group is of size `groupSize`, and consists of `groupSize` consecutive cards.\n\nGiven an integer array `hand` where `hand[i]` is the value written on the i-th card and an integer `groupSize`, return `true` if she can rearrange the cards, or `false` otherwise.\n\n**Constraints**\n- 1 <= hand.length <= 10^4\n- 0 <= hand[i] <= 10^9\n- 1 <= groupSize <= hand.length",
        examples=[
            {
                "input": "hand = [1,2,3,6,2,3,4,7,8], groupSize = 3",
                "output": "true",
                "explanation": "Groups: [1,2,3], [2,3,4], [6,7,8].",
            },
            {
                "input": "hand = [1,2,3,4,5], groupSize = 4",
                "output": "false",
                "explanation": "Cannot form groups of 4 consecutive cards.",
            },
        ],
        tests=[
            (([1, 2, 3, 6, 2, 3, 4, 7, 8], 3), False),
            (([1, 2, 3, 4, 5], 4), False),
            (([1], 1), False),
            (([1, 2, 3], 1), False),
            (([1, 2, 3, 4], 2), False),
            (([8, 10, 12], 3), False),
            (([1, 1, 2, 2, 3, 3], 2), False),
            (([1, 2, 3, 4, 5, 6], 2), False),
            (
                (
                    [
                        9,
                        13,
                        15,
                        23,
                        22,
                        25,
                        4,
                        4,
                        29,
                        15,
                        8,
                        23,
                        22,
                        25,
                        29,
                        9,
                        13,
                        15,
                        8,
                        4,
                        25,
                        8,
                        22,
                        13,
                        9,
                    ],
                    5,
                ),
                False,
            ),
            (([1, 2, 3], 3), True),
            (([1, 1, 2, 2, 3, 3], 3), True),
            (([2, 1], 2), True),
        ],
        ref=lambda hand, groupSize: _is_n_straight_hand(hand, groupSize),
        starter={
            "python": "def isNStraightHand(hand: List[int], groupSize: int) -> bool:\n    pass",
            "javascript": "function isNStraightHand(hand, groupSize) {\n    // your code here\n}",
            "java": "class Solution {\n    public boolean isNStraightHand(int[] hand, int groupSize) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Count cards with a frequency map.",
            "Greedily form groups starting from the smallest remaining card.",
        ],
        solution="Count card frequencies. Repeatedly take the smallest card with a positive count and form a group of groupSize consecutive cards, decrementing counts; return false if any required card is missing.",
        time_complexity="O(n log n)",
        space_complexity="O(n)",
        constraints=["1 <= hand.length <= 10^4", "1 <= groupSize <= hand.length"],
    ),
]


def _subsets(nums: List[int]) -> List[List[int]]:
    res: List[List[int]] = [[]]
    for v in nums:
        res += [s + [v] for s in res]
    return res


def _permute(nums: List[int]) -> List[List[int]]:
    from itertools import permutations

    return [list(p) for p in permutations(nums)]


def _combination_sum(candidates: List[int], target: int) -> List[List[int]]:
    candidates = sorted(candidates)
    res: List[List[int]] = []

    def backtrack(start: int, remaining: int, path: List[int]):
        if remaining == 0:
            res.append(list(path))
            return
        for i in range(start, len(candidates)):
            if candidates[i] > remaining:
                break
            path.append(candidates[i])
            backtrack(i, remaining - candidates[i], path)
            path.pop()

    backtrack(0, target, [])
    return res


def _generate_parenthesis(n: int) -> List[str]:
    res: List[str] = []

    def backtrack(open_count: int, close_count: int, s: str):
        if len(s) == 2 * n:
            res.append(s)
            return
        if open_count < n:
            backtrack(open_count + 1, close_count, s + "(")
        if close_count < open_count:
            backtrack(open_count, close_count + 1, s + ")")

    backtrack(0, 0, "")
    return res


def _exist(board: List[List[str]], word: str) -> bool:
    rows, cols = len(board), len(board[0])

    def dfs(r: int, c: int, idx: int) -> bool:
        if idx == len(word):
            return True
        if not (0 <= r < rows and 0 <= c < cols) or board[r][c] != word[idx]:
            return False
        tmp = board[r][c]
        board[r][c] = "#"
        found = any(
            dfs(r + dr, c + dc, idx + 1)
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
        )
        board[r][c] = tmp
        return found

    for r in range(rows):
        for c in range(cols):
            if board[r][c] == word[0] and dfs(r, c, 0):
                return True
    return False


def _can_jump(nums: List[int]) -> bool:
    max_reach = 0
    for i in range(len(nums)):
        if i > max_reach:
            return False
        max_reach = max(max_reach, i + nums[i])
    return True


def _jump(nums: List[int]) -> int:
    if len(nums) <= 1:
        return 0
    jumps = 0
    current_end = 0
    furthest = 0
    for i in range(len(nums) - 1):
        furthest = max(furthest, i + nums[i])
        if i == current_end:
            jumps += 1
            current_end = furthest
    return jumps


def _can_complete_circuit(gas: List[int], cost: List[int]) -> int:
    total = sum(gas) - sum(cost)
    if total < 0:
        return -1
    start = 0
    surplus = 0
    for i in range(len(gas)):
        surplus += gas[i] - cost[i]
        if surplus < 0:
            start = i + 1
            surplus = 0
    return start


def _is_n_straight_hand(hand: List[int], groupSize: int) -> bool:
    if len(hand) % groupSize != 0:
        return False
    from collections import Counter

    counts = Counter(hand)
    for card in sorted(counts):
        if counts[card] > 0:
            need = counts[card]
            for k in range(groupSize):
                if counts[card + k] < need:
                    return False
                counts[card + k] -= need
    return True
