"""Stack & Queue questions."""

from __future__ import annotations

from typing import List

from ._helpers import make_spec

SPECS = [
    make_spec(
        id="valid-parentheses",
        title="Valid Parentheses",
        difficulty="easy",
        category="Stack & Queue",
        companies=["Amazon", "Google", "Microsoft", "Facebook", "Apple"],
        description="Given a string `s` containing just the characters `(`, `)`, `{`, `}`, `[` and `]`, determine if the input string is valid.\n\nAn input string is valid if:\n- Open brackets must be closed by the same type of brackets.\n- Open brackets must be closed in the correct order.\n- Every close bracket has a corresponding open bracket of the same type.\n\n**Constraints**\n- 1 <= s.length <= 10^4\n- s consists of parentheses only `()[]{}`.",
        examples=[
            {
                "input": 's = "()"',
                "output": "true",
                "explanation": "Simple matching pair.",
            },
            {
                "input": 's = "()[]{}"',
                "output": "true",
                "explanation": "All pairs match in order.",
            },
            {
                "input": 's = "(]"',
                "output": "false",
                "explanation": "Mismatched brackets.",
            },
        ],
        tests=[
            (("()",), False),
            (("()[]{}",), False),
            (("(]",), False),
            (("([)]",), False),
            (("{[]}",), False),
            (("(",), False),
            (("",), False),
            (("((",), False),
            (("))",), False),
            (("([]){()}[]",), False),
            (("((()))",), False),
            (("()(",), True),
            (("{([])}",), True),
            (("([{{}}])",), True),
        ],
        ref=lambda *args: _is_valid(*args),
        starter={
            "python": "def isValid(s: str) -> bool:\n    pass",
            "javascript": "function isValid(s) {\n    // your code here\n}",
            "java": "class Solution {\n    public boolean isValid(String s) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Use a stack to track open brackets.",
            "When a closing bracket appears, it must match the top of the stack.",
            "The stack must be empty at the end.",
        ],
        solution="Push opening brackets onto a stack. On a closing bracket, if the stack is empty or its top doesn't match, return false; otherwise pop. Return whether the stack is empty at the end.",
        time_complexity="O(n)",
        space_complexity="O(n)",
        constraints=["1 <= s.length <= 10^4"],
    ),
    make_spec(
        id="min-stack",
        title="Min Stack",
        difficulty="medium",
        category="Stack & Queue",
        companies=["Amazon", "Google", "Microsoft", "Facebook", "Apple"],
        description="Design a stack that supports push, pop, top, and retrieving the minimum element in constant time.\n\nImplement the following operations against a single stack object using a series of commands:\n- `push(val)` pushes val onto the stack.\n- `pop()` removes the top element.\n- `top()` returns the top element.\n- `getMin()` retrieves the minimum element in the stack.\n\nYou are given two arrays: `operations` (list of method names, always starting with `MinStack`) and `values` (parallel list of arguments; push passes a single value, all other operations pass an empty list). Return the output of every non-mutating call (`top` and `getMin` return values; `null` represents no output for push/pop).\n\n**Constraints**\n- -2^31 <= val <= 2^31 - 1\n- Methods pop, top and getMin will always be called on non-empty stacks.",
        examples=[
            {
                "input": 'operations = ["MinStack","push","push","getMin","push","getMin","getMin","top","getMin","pop","getMin"]\nvalues = [[],[-2],[0],[],[-3],[],[],[],[],[],[]]',
                "output": "[-2,-3,-3,-3,-3,-2]",
                "explanation": "After pushing -2, 0 the min is -2. After pushing -3 the min is -3; top is -3. After popping -3, the min returns to -2.",
            },
        ],
        tests=[
            (
                (
                    [
                        "MinStack",
                        "push",
                        "push",
                        "getMin",
                        "push",
                        "getMin",
                        "getMin",
                        "top",
                        "getMin",
                        "pop",
                        "getMin",
                    ],
                    [[], [-2], [0], [], [-3], [], [], [], [], [], []],
                ),
                False,
            ),
            ((["MinStack", "push", "getMin", "pop"], [[], [5], [], []]), False),
            (
                (
                    ["MinStack", "push", "push", "push", "getMin", "pop", "getMin"],
                    [[], [1], [2], [0], [], [], []],
                ),
                False,
            ),
            ((["MinStack", "push", "top", "getMin"], [[], [-1], [], []]), False),
            (
                (
                    [
                        "MinStack",
                        "push",
                        "push",
                        "top",
                        "getMin",
                        "pop",
                        "top",
                        "getMin",
                    ],
                    [[], [3], [7], [], [], [], [], []],
                ),
                False,
            ),
            (
                (
                    [
                        "MinStack",
                        "push",
                        "push",
                        "getMin",
                        "push",
                        "getMin",
                        "pop",
                        "getMin",
                    ],
                    [[], [10], [5], [], [8], [], [], []],
                ),
                True,
            ),
            (
                (
                    [
                        "MinStack",
                        "push",
                        "push",
                        "getMin",
                        "push",
                        "getMin",
                        "pop",
                        "getMin",
                    ],
                    [[], [-10], [-5], [], [8], [], [], []],
                ),
                True,
            ),
        ],
        ref=lambda *args: _min_stack(*args),
        starter={
            "python": "def minStack(operations: List[str], values: List[List[int]]) -> List[int]:\n    pass",
            "javascript": "function minStack(operations, values) {\n    // your code here\n}",
            "java": "class Solution {\n    public List<Integer> minStack(List<String> operations, List<List<Integer>> values) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Keep a second stack that stores the minimum seen so far.",
            "When pushing, push min(val, currentMin) onto the min stack.",
            "When popping, pop both stacks.",
        ],
        solution="Maintain a data stack and a min stack. push adds val to data and min(current_min, val) to min stack; pop removes from both; top returns the data stack top; getMin returns the min stack top.",
        time_complexity="O(1) per operation",
        space_complexity="O(n)",
        constraints=[
            "-2^31 <= val <= 2^31 - 1",
            "Operations are valid on non-empty stacks",
        ],
    ),
    make_spec(
        id="evaluate-reverse-polish-notation",
        title="Evaluate Reverse Polish Notation",
        difficulty="medium",
        category="Stack & Queue",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="You are given an array of strings `tokens` that represents an arithmetic expression in Reverse Polish Notation (postfix).\n\nEvaluate the expression and return an integer that represents the value of the expression.\n\n**Rules**\n- The valid operators are `+`, `-`, `*`, and `/`.\n- Division between two integers should truncate toward zero.\n- The tokens represent an arithmetic expression in RPN that is always valid.\n\n**Constraints**\n- 1 <= tokens.length <= 10^4\n- tokens[i] is either an operator or an integer in the range [-200, 200].",
        examples=[
            {
                "input": 'tokens = ["2","1","+","3","*"]',
                "output": "9",
                "explanation": "(2 + 1) * 3 = 9.",
            },
            {
                "input": 'tokens = ["4","13","5","/","+"]',
                "output": "6",
                "explanation": "4 + (13 / 5) = 4 + 2 = 6.",
            },
            {
                "input": 'tokens = ["10","6","9","3","+","-11","*","/","*","17","+","5","+"]',
                "output": "22",
                "explanation": "Evaluates to 22.",
            },
        ],
        tests=[
            ((["2", "1", "+", "3", "*"],), False),
            ((["4", "13", "5", "/", "+"],), False),
            (
                (
                    [
                        "10",
                        "6",
                        "9",
                        "3",
                        "+",
                        "-11",
                        "*",
                        "/",
                        "*",
                        "17",
                        "+",
                        "5",
                        "+",
                    ],
                ),
                False,
            ),
            ((["3", "4", "+"],), False),
            ((["18"],), False),
            ((["-1", "2", "*"],), False),
            ((["5", "2", "/"],), False),
            ((["4", "3", "-"],), False),
            ((["2", "3", "11", "+", "*"],), True),
            ((["-4", "2", "+"],), True),
            ((["5", "5", "5", "+", "*"],), True),
        ],
        ref=lambda *args: _eval_rpn(*args),
        starter={
            "python": "def evalRPN(tokens: List[str]) -> int:\n    pass",
            "javascript": "function evalRPN(tokens) {\n    // your code here\n}",
            "java": "class Solution {\n    public int evalRPN(String[] tokens) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Use a stack of integers.",
            "On an operator, pop two operands, apply it (right operand second), and push the result.",
            "Truncate division toward zero with int(a / b).",
        ],
        solution="Scan tokens left to right. Push numbers onto the stack. On an operator, pop b then a, compute a op b (with integer truncating division), and push the result. The final stack top is the answer.",
        time_complexity="O(n)",
        space_complexity="O(n)",
        constraints=["1 <= tokens.length <= 10^4"],
    ),
    make_spec(
        id="daily-temperatures",
        title="Daily Temperatures",
        difficulty="medium",
        category="Stack & Queue",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="Given an array of integers `temperatures` representing daily temperatures, return an array `answer` such that `answer[i]` is the number of days you have to wait after the i-th day to get a warmer temperature.\n\nIf there is no future day for which this is possible, keep `answer[i] == 0` instead.\n\n**Constraints**\n- 1 <= temperatures.length <= 10^5\n- 30 <= temperatures[i] <= 100",
        examples=[
            {
                "input": "temperatures = [73,74,75,71,69,72,76,73]",
                "output": "[1,1,4,2,1,1,0,0]",
                "explanation": "Day 0 needs 1 day (74), day 2 needs 4 days (76), etc.",
            },
            {
                "input": "temperatures = [30,40,50,60]",
                "output": "[1,1,1,0]",
                "explanation": "Each day warms the next day except the last.",
            },
            {
                "input": "temperatures = [30,60,90]",
                "output": "[1,1,0]",
                "explanation": "30->60->90.",
            },
        ],
        tests=[
            (([73, 74, 75, 71, 69, 72, 76, 73],), False),
            (([30, 40, 50, 60],), False),
            (([30, 60, 90],), False),
            (([30],), False),
            (([89, 62, 70, 58, 47, 47, 46, 76, 100, 70],), False),
            (([100, 90, 80],), False),
            (([34, 80, 80, 34, 34, 80, 80, 80, 80, 34],), False),
            (([55, 38, 53, 81, 61, 93, 97, 32, 43, 78],), True),
            (([31, 32, 33, 34, 35],), True),
        ],
        ref=lambda *args: _daily_temperatures(*args),
        starter={
            "python": "def dailyTemperatures(temperatures: List[int]) -> List[int]:\n    pass",
            "javascript": "function dailyTemperatures(temperatures) {\n    // your code here\n}",
            "java": "class Solution {\n    public int[] dailyTemperatures(int[] temperatures) {\n        // your code here\n    }\n}",
        },
        hints=[
            "A monotonic decreasing stack of indices helps find the next warmer day.",
            "Pop while the current temperature is greater than the stack top's temperature.",
        ],
        solution="Maintain a stack of indices for days with no warmer day yet. For each day i, while the stack is non-empty and temperatures[i] > temperatures[stack.top()], pop and set answer[popped] = i - popped. Then push i. Days left on the stack keep answer 0.",
        time_complexity="O(n)",
        space_complexity="O(n)",
        constraints=["1 <= temperatures.length <= 10^5"],
    ),
    make_spec(
        id="car-fleet",
        title="Car Fleet",
        difficulty="medium",
        category="Stack & Queue",
        companies=["Amazon", "Google", "Microsoft"],
        description="There are `n` cars going to the same destination along a one-lane road. The destination is `target` miles away.\n\nYou are given two integer arrays `position` and `speed`, both of length n, where `position[i]` is the position of the i-th car and `speed[i]` is the speed of the i-th car (in miles per hour).\n\nA car can never pass another car ahead of it, but it can catch up and drive bumper-to-bumper at the same speed. The faster car will slow down to match the slower car's speed. The distance between these two cars is ignored (i.e., they are assumed to have the same position).\n\nA car fleet is some non-empty set of cars driving at the same position and same speed. Note that a single car is also a car fleet.\n\nReturn the number of car fleets that will arrive at the destination.\n\n**Constraints**\n- n == position.length == speed.length\n- 1 <= n <= 10^5\n- 0 < target <= 10^6\n- 0 <= position[i] < target\n- All the values of position are unique.",
        examples=[
            {
                "input": "target = 12, position = [10,8,0,5,3], speed = [2,4,1,1,3]",
                "output": "3",
                "explanation": "The cars starting at 10 (speed 2) and 8 (speed 4) become one fleet; the cars at 5 and 3 form another; the car at 0 forms a third.",
            },
            {
                "input": "target = 10, position = [3], speed = [3]",
                "output": "1",
                "explanation": "One car is one fleet.",
            },
            {
                "input": "target = 100, position = [0,2,4], speed = [4,2,1]",
                "output": "1",
                "explanation": "All cars catch up and form one fleet.",
            },
        ],
        tests=[
            (([10, 8, 0, 5, 3], [2, 4, 1, 1, 3], 12), False),
            (([3], [3], 10), False),
            (([0, 2, 4], [4, 2, 1], 100), False),
            (([5, 1, 3], [1, 3, 1], 10), False),
            (([0, 4, 2], [2, 1, 3], 10), False),
            (([6, 8], [3, 2], 10), False),
            (([8, 3, 7, 4, 6, 5], [4, 4, 4, 4, 4, 4], 10), False),
            (([1, 9, 5, 3], [2, 1, 2, 3], 10), True),
            (([0, 5, 10], [1, 1, 1], 20), True),
        ],
        ref=lambda position, speed, target: _car_fleet(target, position, speed),
        starter={
            "python": "def carFleet(target: int, position: List[int], speed: List[int]) -> int:\n    pass",
            "javascript": "function carFleet(target, position, speed) {\n    // your code here\n}",
            "java": "class Solution {\n    public int carFleet(int target, int[] position, int[] speed) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Sort cars by starting position descending.",
            "Compute each car's arrival time; a car joins the fleet ahead if it arrives no later.",
            "Count how many 'leaders' (slower arrivals) exist.",
        ],
        solution="Pair position and speed, sort descending by position, and compute arrival times. Iterate from the front: whenever a car's arrival time is strictly greater than the current fleet's time, it starts a new fleet. Return the count of fleets.",
        time_complexity="O(n log n)",
        space_complexity="O(n)",
        constraints=["1 <= n <= 10^5", "0 < target <= 10^6"],
    ),
    make_spec(
        id="largest-rectangle-in-histogram",
        title="Largest Rectangle in Histogram",
        difficulty="hard",
        category="Stack & Queue",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="Given an array of integers `heights` representing the histogram's bar height where the width of each bar is 1, return the area of the largest rectangle in the histogram.\n\n**Constraints**\n- 1 <= heights.length <= 10^5\n- 0 <= heights[i] <= 10^4",
        examples=[
            {
                "input": "heights = [2,1,5,6,2,3]",
                "output": "10",
                "explanation": "The largest rectangle uses bars of height 5 and 6, area 5*2 = 10.",
            },
            {
                "input": "heights = [2,4]",
                "output": "4",
                "explanation": "The bar of height 4 alone gives area 4.",
            },
        ],
        tests=[
            (([2, 1, 5, 6, 2, 3],), False),
            (([2, 4],), False),
            (([1],), False),
            (([1, 2, 3, 4, 5],), False),
            (([5, 4, 3, 2, 1],), False),
            (([2, 1, 2],), False),
            (([6, 2, 5, 4, 5, 1, 6],), False),
            (([1, 1, 1, 1],), False),
            (([3, 6, 5, 7, 4, 8, 1, 0],), True),
            (([2, 2, 2],), True),
        ],
        ref=lambda *args: _largest_rectangle_area(*args),
        starter={
            "python": "def largestRectangleArea(heights: List[int]) -> int:\n    pass",
            "javascript": "function largestRectangleArea(heights) {\n    // your code here\n}",
            "java": "class Solution {\n    public int largestRectangleArea(int[] heights) {\n        // your code here\n    }\n}",
        },
        hints=[
            "For each bar, find the previous smaller and next smaller bar.",
            "A monotonic increasing stack computes these bounds in one pass.",
        ],
        solution="Use a stack of indices. For each bar, while the current height is less than the stack top's height, pop and compute the rectangle using the popped height as the limiting height with width between the new stack top and the current index. Track the max area.",
        time_complexity="O(n)",
        space_complexity="O(n)",
        constraints=["1 <= heights.length <= 10^5"],
    ),
]


def _is_valid(s: str) -> bool:
    stack = []
    pairs = {")": "(", "]": "[", "}": "{"}
    for ch in s:
        if ch in pairs:
            if not stack or stack[-1] != pairs[ch]:
                return False
            stack.pop()
        else:
            stack.append(ch)
    return not stack


def _min_stack(operations: List[str], values: List[List[int]]) -> List[int]:
    stack: List[int] = []
    min_stack: List[int] = []
    out: List[int] = []
    for op, vals in zip(operations, values):
        if op == "MinStack":
            stack, min_stack = [], []
        elif op == "push":
            val = vals[0]
            stack.append(val)
            if not min_stack or val <= min_stack[-1]:
                min_stack.append(val)
        elif op == "pop":
            val = stack.pop()
            if min_stack and val == min_stack[-1]:
                min_stack.pop()
        elif op == "top":
            out.append(stack[-1])
        elif op == "getMin":
            out.append(min_stack[-1])
    return out


def _eval_rpn(tokens: List[str]) -> int:
    stack: List[int] = []
    for t in tokens:
        if t in {"+", "-", "*", "/"}:
            b = stack.pop()
            a = stack.pop()
            if t == "+":
                stack.append(a + b)
            elif t == "-":
                stack.append(a - b)
            elif t == "*":
                stack.append(a * b)
            else:
                stack.append(int(a / b))
        else:
            stack.append(int(t))
    return stack[0]


def _daily_temperatures(temperatures: List[int]) -> List[int]:
    n = len(temperatures)
    ans = [0] * n
    stack: List[int] = []
    for i in range(n):
        while stack and temperatures[i] > temperatures[stack[-1]]:
            j = stack.pop()
            ans[j] = i - j
        stack.append(i)
    return ans


def _car_fleet(target: int, position: List[int], speed: List[int]) -> int:
    pairs = sorted(zip(position, speed), reverse=True)
    fleets = 0
    current_time = 0.0
    for pos, spd in pairs:
        arrival = (target - pos) / spd
        if arrival > current_time:
            fleets += 1
            current_time = arrival
    return fleets


def _largest_rectangle_area(heights: List[int]) -> int:
    stack: List[int] = []
    best = 0
    heights = heights + [0]
    for i, h in enumerate(heights):
        while stack and heights[stack[-1]] > h:
            height = heights[stack.pop()]
            width = i if not stack else i - stack[-1] - 1
            best = max(best, height * width)
        stack.append(i)
    return best
