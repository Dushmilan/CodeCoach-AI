"""Graph, Heap & Intervals questions.

Graph problems use JSON-native representations (adjacency lists, edge lists, or
grids). Design problems are expressed as operation-sequence functions.
"""

from __future__ import annotations

from typing import List

from ._helpers import make_spec

SPECS = [
    make_spec(
        id="number-of-islands",
        title="Number of Islands",
        difficulty="medium",
        category="Graphs",
        companies=["Amazon", "Google", "Microsoft", "Facebook", "Apple"],
        description="Given an m x n 2D binary grid `grid` which represents a map of '1's (land) and '0's (water), return the number of islands.\n\nAn island is surrounded by water and is formed by connecting adjacent lands horizontally or vertically.\n\nYou may assume all four edges of the grid are all surrounded by water.\n\n**Constraints**\n- m == grid.length\n- n == grid[i].length\n- 1 <= m, n <= 300\n- grid[i][j] is '0' or '1'.",
        examples=[
            {
                "input": 'grid = [["1","1","1","1","0"],["1","1","0","1","0"],["1","1","0","0","0"],["0","0","0","0","0"]]',
                "output": "1",
                "explanation": "All land connects into one island.",
            },
            {
                "input": 'grid = [["1","1","0","0","0"],["1","1","0","0","0"],["0","0","1","0","0"],["0","0","0","1","1"]]',
                "output": "3",
                "explanation": "Three separate islands.",
            },
        ],
        tests=[
            (
                (
                    [
                        ["1", "1", "1", "1", "0"],
                        ["1", "1", "0", "1", "0"],
                        ["1", "1", "0", "0", "0"],
                        ["0", "0", "0", "0", "0"],
                    ],
                ),
                False,
            ),
            (
                (
                    [
                        ["1", "1", "0", "0", "0"],
                        ["1", "1", "0", "0", "0"],
                        ["0", "0", "1", "0", "0"],
                        ["0", "0", "0", "1", "1"],
                    ],
                ),
                False,
            ),
            ([(["1"],)], False),
            ([(["0"],)], False),
            (
                (
                    [
                        ["1", "0", "1", "0", "1"],
                        ["0", "1", "0", "1", "0"],
                        ["1", "0", "1", "0", "1"],
                    ],
                ),
                False,
            ),
            (
                ([["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],),
                False,
            ),
            (
                ([["1", "1", "1"], ["1", "1", "1"], ["1", "1", "1"]],),
                True,
            ),
            (
                ([["1", "0"], ["0", "1"]],),
                True,
            ),
            (
                (
                    [
                        ["1", "0", "0", "0", "1"],
                        ["0", "0", "1", "0", "0"],
                        ["1", "0", "0", "0", "1"],
                    ],
                ),
                True,
            ),
        ],
        ref=lambda *args: _num_islands(*args),
        starter={
            "python": "def numIslands(grid: List[List[str]]) -> int:\n    pass",
            "javascript": "function numIslands(grid) {\n    // your code here\n}",
            "java": "class Solution {\n    public int numIslands(char[][] grid) {\n        // your code here\n    }\n}",
        },
        hints=[
            "DFS or BFS from each unvisited '1' to flood its whole island.",
            "Mark visited cells to avoid recounting.",
        ],
        solution="Iterate over every cell. When a '1' is found, increment the island count and run DFS/BFS from it, flipping every reachable '1' to '0'. Count the number of times a flood was started.",
        time_complexity="O(m * n)",
        space_complexity="O(m * n)",
        constraints=["m == grid.length", "1 <= m, n <= 300"],
    ),
    make_spec(
        id="course-schedule",
        title="Course Schedule",
        difficulty="medium",
        category="Graphs",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="There are a total of `numCourses` courses you have to take, labeled from 0 to `numCourses - 1`. You are given an array `prerequisites` where `prerequisites[i] = [a_i, b_i]` indicates that you must take course `b_i` first if you want to take course `a_i`.\n\nReturn `true` if you can finish all courses. Otherwise, return `false`.\n\n**Constraints**\n- 1 <= numCourses <= 2000\n- 0 <= prerequisites.length <= 5000\n- prerequisites[i].length == 2\n- All the pairs prerequisites[i] are unique.",
        examples=[
            {
                "input": "numCourses = 2, prerequisites = [[1,0]]",
                "output": "true",
                "explanation": "Take 0 first, then 1.",
            },
            {
                "input": "numCourses = 2, prerequisites = [[1,0],[0,1]]",
                "output": "false",
                "explanation": "A cycle exists: 0 depends on 1 and 1 depends on 0.",
            },
        ],
        tests=[
            (([[1, 0]], 2), False),
            (([[1, 0], [0, 1]], 2), False),
            (([], 1), False),
            (([], 5), False),
            (([[1, 0], [2, 1], [3, 2]], 4), False),
            (([[1, 0], [2, 1], [0, 2]], 3), False),
            (([[0, 1], [1, 2], [2, 3], [3, 1]], 4), False),
            (([[1, 0], [2, 0], [3, 1], [3, 2]], 4), True),
            (([[1, 0]], 2), True),
            (([[2, 0], [1, 0], [3, 1], [3, 2], [1, 3]], 4), True),
        ],
        ref=lambda prerequisites, numCourses: _can_finish(numCourses, prerequisites),
        starter={
            "python": "def canFinish(numCourses: int, prerequisites: List[List[int]]) -> bool:\n    pass",
            "javascript": "function canFinish(numCourses, prerequisites) {\n    // your code here\n}",
            "java": "class Solution {\n    public boolean canFinish(int numCourses, int[][] prerequisites) {\n        // your code here\n    }\n}",
        },
        hints=[
            "This is a cycle-detection problem on a directed graph.",
            "Kahn's algorithm (topological sort) processes nodes with in-degree 0.",
            "If some nodes are never processed, a cycle exists.",
        ],
        solution="Build an adjacency list and in-degrees. Use Kahn's algorithm: repeatedly take a node with in-degree 0, remove it, and decrease the in-degrees of its dependents. If the number of processed nodes equals numCourses, there is no cycle.",
        time_complexity="O(V + E)",
        space_complexity="O(V + E)",
        constraints=["1 <= numCourses <= 2000", "0 <= prerequisites.length <= 5000"],
    ),
    make_spec(
        id="course-schedule-ii",
        title="Course Schedule II",
        difficulty="hard",
        category="Graphs",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="There are a total of `numCourses` courses you have to take, labeled from 0 to `numCourses - 1`. You are given an array `prerequisites` where `prerequisites[i] = [a_i, b_i]` indicates that you must take course `b_i` first if you want to take course `a_i`.\n\nReturn the ordering of courses you should take to finish all courses. If there are many valid answers, return any of them. If it is impossible to finish all courses, return an empty array.\n\n**Constraints**\n- 1 <= numCourses <= 2000\n- 0 <= prerequisites.length <= 5000\n- All the pairs prerequisites[i] are unique.",
        examples=[
            {
                "input": "numCourses = 2, prerequisites = [[1,0]]",
                "output": "[0,1]",
                "explanation": "Take 0 first, then 1.",
            },
            {
                "input": "numCourses = 4, prerequisites = [[1,0],[2,0],[3,1],[3,2]]",
                "output": "[0,2,1,3]",
                "explanation": "A valid ordering.",
            },
            {
                "input": "numCourses = 1, prerequisites = []",
                "output": "[0]",
                "explanation": "Only one course.",
            },
        ],
        tests=[
            (([[1, 0]], 2), False),
            (([[1, 0], [0, 1]], 2), False),
            (([], 1), False),
            (([], 4), False),
            (([[1, 0], [2, 0], [3, 1], [3, 2]], 4), False),
            (([[1, 0], [2, 1], [0, 2]], 3), False),
            (([[1, 0], [2, 0], [3, 1], [3, 2]], 4), True),
            (([[0, 1]], 2), True),
            (([[1, 0], [2, 1], [3, 2]], 4), True),
        ],
        ref=lambda prerequisites, numCourses: _find_order(numCourses, prerequisites),
        starter={
            "python": "def findOrder(numCourses: int, prerequisites: List[List[int]]) -> List[int]:\n    pass",
            "javascript": "function findOrder(numCourses, prerequisites) {\n    // your code here\n}",
            "java": "class Solution {\n    public int[] findOrder(int numCourses, int[][] prerequisites) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Kahn's algorithm produces a topological ordering when the graph is acyclic.",
            "Return [] if fewer than numCourses nodes are processed.",
        ],
        solution="Build adjacency and in-degrees, then run Kahn's algorithm collecting the processing order. If the collected order has numCourses elements, return it; otherwise return an empty array.",
        time_complexity="O(V + E)",
        space_complexity="O(V + E)",
        constraints=["1 <= numCourses <= 2000"],
    ),
    make_spec(
        id="clone-graph",
        title="Clone Graph",
        difficulty="medium",
        category="Graphs",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="Given a reference of a node in a connected undirected graph, return a deep copy (clone) of the graph.\n\nThe graph is given as an adjacency list of `n` nodes labeled 0 to n-1, where `adj[i]` is the list of neighbors of node i. Return the adjacency list of the cloned graph.\n\n**Constraints**\n- The number of nodes in the graph is in the range [0, 100].\n- 0 <= Node.val <= 99\n- Node.val is unique for each node.\n- The graph is connected unless empty.",
        examples=[
            {
                "input": "adj = [[2,4],[1,3],[2,4],[1,3]]",
                "output": "[[2,4],[1,3],[2,4],[1,3]]",
                "explanation": "Node 1 (index 0) connects to 2 and 4, etc. The clone preserves all edges.",
            },
            {
                "input": "adj = [[]]",
                "output": "[[]]",
                "explanation": "A single isolated node.",
            },
            {"input": "adj = []", "output": "[]", "explanation": "Empty graph."},
        ],
        tests=[
            (([[2, 4], [1, 3], [2, 4], [1, 3]],), False),
            (([[]],), False),
            (([],), False),
            (([[2], [1]],), False),
            (([[2, 3], [1, 3], [1, 2]],), False),
            (([[2], [1, 3], [2]],), False),
            (([[2, 3], [1], [1]],), True),
            (([[2, 3, 4], [1, 4], [1, 4], [1, 2, 3]],), True),
        ],
        ref=lambda *args: _clone_graph(*args),
        starter={
            "python": "def cloneGraph(adj: List[List[int]]) -> List[List[int]]:\n    pass",
            "javascript": "function cloneGraph(adj) {\n    // your code here\n}",
            "java": "class Solution {\n    public List<List<Integer>> cloneGraph(List<List<Integer>> adj) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Map original nodes to their clones so edges point at the clones.",
            "BFS or DFS over the original graph while building the clone.",
        ],
        solution="Build node objects from the adjacency list, then BFS/DFS copying neighbors using a dictionary from original node to clone. Serialize the clone back to an adjacency list.",
        time_complexity="O(V + E)",
        space_complexity="O(V)",
        constraints=["The number of nodes is in the range [0, 100]"],
    ),
    make_spec(
        id="kth-largest-element-in-an-array",
        title="Kth Largest Element in an Array",
        difficulty="medium",
        category="Heaps & Priority Queues",
        companies=["Amazon", "Google", "Microsoft", "Facebook", "Apple"],
        description="Given an integer array `nums` and an integer `k`, return the k-th largest element in the array.\n\nNote that it is the k-th largest element in the sorted order, not the k-th distinct element.\n\nCan you solve it without sorting?\n\n**Constraints**\n- 1 <= k <= nums.length <= 10^5\n- -10^4 <= nums[i] <= 10^4",
        examples=[
            {
                "input": "nums = [3,2,1,5,6,4], k = 2",
                "output": "5",
                "explanation": "Sorted: [6,5,4,3,2,1]; the 2nd largest is 5.",
            },
            {
                "input": "nums = [3,2,3,1,2,4,5,5,6], k = 4",
                "output": "4",
                "explanation": "Sorted: [6,5,5,4,...]; the 4th largest is 4.",
            },
        ],
        tests=[
            (([3, 2, 1, 5, 6, 4], 2), False),
            (([3, 2, 3, 1, 2, 4, 5, 5, 6], 4), False),
            (([1], 1), False),
            (([1, 2, 3], 1), False),
            (([1, 2, 3], 3), False),
            (([5, 5, 5, 5], 2), False),
            (([3, 1, 2, 4, 5], 2), False),
            (([-1, -2, -3, -4], 2), True),
            (([10, 9, 8, 7, 6, 5, 4, 3, 2, 1], 5), True),
        ],
        ref=lambda nums, k: _kth_largest(nums, k),
        starter={
            "python": "def findKthLargest(nums: List[int], k: int) -> int:\n    pass",
            "javascript": "function findKthLargest(nums, k) {\n    // your code here\n}",
            "java": "class Solution {\n    public int findKthLargest(int[] nums, int k) {\n        // your code here\n    }\n}",
        },
        hints=[
            "A min-heap of size k keeps the k largest elements.",
            "Quickselect achieves O(n) average time.",
        ],
        solution="Push elements into a min-heap keeping its size capped at k; the heap top is then the k-th largest. Alternatively use quickselect for average O(n) time.",
        time_complexity="O(n log k)",
        space_complexity="O(k)",
        constraints=["1 <= k <= nums.length <= 10^5"],
    ),
    make_spec(
        id="k-closest-points-to-origin",
        title="K Closest Points to Origin",
        difficulty="medium",
        category="Heaps & Priority Queues",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="Given an array of `points` where `points[i] = [xi, yi]` represents a point on the X-Y plane and an integer `k`, return the `k` closest points to the origin `(0, 0)`.\n\nThe distance between two points on the X-Y plane is the Euclidean distance.\n\nYou may return the answer in any order.\n\n**Constraints**\n- 1 <= k <= points.length <= 10^4\n- -10^4 <= xi, yi <= 10^4",
        examples=[
            {
                "input": "points = [[1,3],[-2,2]], k = 1",
                "output": "[[-2,2]]",
                "explanation": "Distance of (1,3) is sqrt(10); of (-2,2) is sqrt(8).",
            },
            {
                "input": "points = [[3,3],[5,-1],[-2,4]], k = 2",
                "output": "[[3,3],[-2,4]]",
                "explanation": "The two closest points.",
            },
        ],
        tests=[
            (([[1, 3], [-2, 2]], 1), False),
            (([[3, 3], [5, -1], [-2, 4]], 2), False),
            (([[0, 0], [1, 1]], 1), False),
            (([[0, 0]], 1), False),
            (([[1, 1], [2, 2], [3, 3]], 2), False),
            (([[-1, -1], [1, -1], [-1, 1], [1, 1]], 2), False),
            (([[1, 0], [0, 1], [-1, 0], [0, -1]], 2), True),
            (([[2, 2], [1, 1], [0, 0]], 3), True),
        ],
        ref=lambda points, k: _k_closest(points, k),
        starter={
            "python": "def kClosest(points: List[List[int]], k: int) -> List[List[int]]:\n    pass",
            "javascript": "function kClosest(points, k) {\n    // your code here\n}",
            "java": "class Solution {\n    public int[][] kClosest(int[][] points, int k) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Compare squared distances to avoid floating-point cost.",
            "A max-heap of size k works here: evict the farthest point.",
        ],
        solution="Use a max-heap keyed by squared distance. For each point push (distance, point); when the heap exceeds size k, pop the farthest. The heap holds the k closest points.",
        time_complexity="O(n log k)",
        space_complexity="O(k)",
        constraints=["1 <= k <= points.length <= 10^4"],
    ),
    make_spec(
        id="merge-intervals",
        title="Merge Intervals",
        difficulty="medium",
        category="Intervals",
        companies=["Google", "Facebook", "Amazon", "Uber", "Microsoft"],
        description="Given an array of `intervals` where `intervals[i] = [start_i, end_i]`, merge all overlapping intervals and return an array of the non-overlapping intervals that cover all the intervals in the input.\n\n**Constraints**\n- 1 <= intervals.length <= 10^4\n- intervals[i].length == 2\n- 0 <= start_i <= end_i <= 10^4",
        examples=[
            {
                "input": "intervals = [[1,3],[2,6],[8,10],[15,18]]",
                "output": "[[1,6],[8,10],[15,18]]",
                "explanation": "[1,3] and [2,6] overlap and merge into [1,6].",
            },
            {
                "input": "intervals = [[1,4],[4,5]]",
                "output": "[[1,5]]",
                "explanation": "[1,4] and [4,5] touch and merge.",
            },
        ],
        tests=[
            (([[1, 3], [2, 6], [8, 10], [15, 18]],), False),
            (([[1, 4], [4, 5]],), False),
            (([[1, 4], [0, 4]],), False),
            (([[1, 2]],), False),
            (([[1, 3], [2, 6], [8, 10], [15, 18]],), False),
            (([[1, 4], [0, 1]],), False),
            (([[2, 3], [4, 5], [6, 7]],), False),
            (([[1, 3], [2, 6], [8, 10], [15, 18]],), True),
            (([[1, 10], [2, 3], [4, 5], [6, 7]],), True),
            (([[1, 4], [0, 2], [3, 5]],), True),
        ],
        ref=lambda *args: _merge_intervals(*args),
        starter={
            "python": "def merge(intervals: List[List[int]]) -> List[List[int]]:\n    pass",
            "javascript": "function merge(intervals) {\n    // your code here\n}",
            "java": "class Solution {\n    public int[][] merge(int[][] intervals) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Sort by start time first.",
            "If the next interval's start is <= the current end, extend the current end.",
        ],
        solution="Sort intervals by start. Iterate, merging whenever the current interval overlaps or touches the running one; otherwise push the running interval and start a new one.",
        time_complexity="O(n log n)",
        space_complexity="O(n)",
        constraints=["1 <= intervals.length <= 10^4"],
    ),
    make_spec(
        id="non-overlapping-intervals",
        title="Non-overlapping Intervals",
        difficulty="medium",
        category="Intervals",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="Given an array of intervals `intervals` where `intervals[i] = [start_i, end_i]`, return the minimum number of intervals you need to remove to make the rest of the intervals non-overlapping.\n\n**Constraints**\n- 1 <= intervals.length <= 10^5\n- intervals[i].length == 2\n- -5 * 10^4 <= start_i < end_i <= 5 * 10^4",
        examples=[
            {
                "input": "intervals = [[1,2],[2,3],[3,4],[1,3]]",
                "output": "1",
                "explanation": "Remove [1,3] to make the rest non-overlapping.",
            },
            {
                "input": "intervals = [[1,2],[1,2],[1,2]]",
                "output": "2",
                "explanation": "Keep one, remove the other two.",
            },
            {
                "input": "intervals = [[1,2],[2,3]]",
                "output": "0",
                "explanation": "Already non-overlapping.",
            },
        ],
        tests=[
            (([[1, 2], [2, 3], [3, 4], [1, 3]],), False),
            (([[1, 2], [1, 2], [1, 2]],), False),
            (([[1, 2], [2, 3]],), False),
            (([[1, 100], [11, 22], [1, 11], [2, 12]],), False),
            (([[0, 2], [1, 3], [2, 4], [3, 5], [4, 6]],), False),
            (([[1, 2]],), False),
            (([[1, 5], [2, 3], [3, 4], [4, 5]],), True),
            (([[1, 3], [2, 4], [3, 5]],), True),
        ],
        ref=lambda *args: _erase_overlap(*args),
        starter={
            "python": "def eraseOverlapIntervals(intervals: List[List[int]]) -> int:\n    pass",
            "javascript": "function eraseOverlapIntervals(intervals) {\n    // your code here\n}",
            "java": "class Solution {\n    public int eraseOverlapIntervals(int[][] intervals) {\n        // your code here\n    }\n}",
        },
        hints=[
            "This is an interval-scheduling (greedy) problem.",
            "Sort by end time and always keep the interval that ends earliest.",
        ],
        solution="Sort intervals by end time. Keep a running end; whenever an interval starts before the running end, it overlaps so count a removal; otherwise update the running end and keep it.",
        time_complexity="O(n log n)",
        space_complexity="O(1)",
        constraints=["1 <= intervals.length <= 10^5"],
    ),
    make_spec(
        id="task-scheduler",
        title="Task Scheduler",
        difficulty="hard",
        category="Heaps & Priority Queues",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="Given a characters array `tasks`, representing the tasks a CPU needs to do, where each letter represents a different task. Tasks could be done in any order. Each task is done in one unit of time. For each unit of time, the CPU could complete either one task or just be idle.\n\nHowever, there is a non-negative integer `n` that represents the cooldown period between two same tasks (the same letter in the array), that is that there must be at least n units of time between any two same tasks.\n\nReturn the least number of units of times that the CPU will take to finish all the given tasks.\n\n**Constraints**\n- 1 <= task.length <= 10^4\n- tasks[i] is an uppercase English letter.\n- 0 <= n <= 100",
        examples=[
            {
                "input": 'tasks = ["A","A","A","B","B","B"], n = 2',
                "output": "8",
                "explanation": "A -> B -> idle -> A -> B -> idle -> A -> B.",
            },
            {
                "input": 'tasks = ["A","C","A","B","D","B"], n = 1',
                "output": "6",
                "explanation": "A -> B -> C -> D -> A -> B.",
            },
            {
                "input": 'tasks = ["A","A","A","B","B","B"], n = 0',
                "output": "6",
                "explanation": "No cooldown needed.",
            },
        ],
        tests=[
            ((["A", "A", "A", "B", "B", "B"], 2), False),
            ((["A", "C", "A", "B", "D", "B"], 1), False),
            ((["A", "A", "A", "B", "B", "B"], 0), False),
            ((["A"], 0), False),
            ((["A", "A"], 2), False),
            ((["A", "B", "C", "D", "E", "F", "G"], 2), False),
            ((["A", "A", "A", "A", "B", "C", "D"], 3), False),
            ((["A", "A", "A", "B", "B", "C", "C"], 1), True),
            ((["A", "A", "A", "B", "B", "B", "C", "C", "C"], 2), True),
            ((["A", "B", "A", "B"], 2), True),
        ],
        ref=lambda tasks, n: _least_interval(tasks, n),
        starter={
            "python": "def leastInterval(tasks: List[str], n: int) -> int:\n    pass",
            "javascript": "function leastInterval(tasks, n) {\n    // your code here\n}",
            "java": "class Solution {\n    public int leastInterval(char[] tasks, int n) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Only the frequency counts matter, not the task identities.",
            "Greedily schedule the most frequent tasks first.",
            "Formula: (maxCount - 1) * (n + 1) + numberOfMaxTasks, bounded below by len(tasks).",
        ],
        solution="Count frequencies. Let maxFreq be the maximum count and numMax the number of tasks with that count. The answer is max(len(tasks), (maxFreq - 1) * (n + 1) + numMax).",
        time_complexity="O(n)",
        space_complexity="O(26)",
        constraints=["1 <= task.length <= 10^4", "0 <= n <= 100"],
    ),
]


def _num_islands(grid: List[List[str]]) -> int:
    if not grid:
        return 0
    rows, cols = len(grid), len(grid[0])
    count = 0

    def flood(r, c):
        if not (0 <= r < rows and 0 <= c < cols) or grid[r][c] != "1":
            return
        grid[r][c] = "0"
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            flood(r + dr, c + dc)

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == "1":
                count += 1
                flood(r, c)
    return count


def _can_finish(numCourses: int, prerequisites: List[List[int]]) -> bool:
    from collections import deque

    adj = [[] for _ in range(numCourses)]
    indeg = [0] * numCourses
    for a, b in prerequisites:
        adj[b].append(a)
        indeg[a] += 1
    q = deque([i for i in range(numCourses) if indeg[i] == 0])
    processed = 0
    while q:
        cur = q.popleft()
        processed += 1
        for nxt in adj[cur]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                q.append(nxt)
    return processed == numCourses


def _find_order(numCourses: int, prerequisites: List[List[int]]) -> List[int]:
    from collections import deque

    adj = [[] for _ in range(numCourses)]
    indeg = [0] * numCourses
    for a, b in prerequisites:
        adj[b].append(a)
        indeg[a] += 1
    q = deque([i for i in range(numCourses) if indeg[i] == 0])
    order = []
    while q:
        cur = q.popleft()
        order.append(cur)
        for nxt in adj[cur]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                q.append(nxt)
    return order if len(order) == numCourses else []


def _clone_graph(adj: List[List[int]]) -> List[List[int]]:
    # An adjacency-list representation of a graph clone is structurally identical:
    # node labels are unchanged, only the node objects differ.
    return [list(nbrs) for nbrs in adj]


def _kth_largest(nums: List[int], k: int) -> int:
    import heapq

    heap = []
    for v in nums:
        heapq.heappush(heap, v)
        if len(heap) > k:
            heapq.heappop(heap)
    return heap[0]


def _k_closest(points: List[List[int]], k: int) -> List[List[int]]:
    import heapq

    heap = []
    for x, y in points:
        d = x * x + y * y
        heapq.heappush(heap, (-d, x, y))
        if len(heap) > k:
            heapq.heappop(heap)
    return [[x, y] for _, x, y in heap]


def _merge_intervals(intervals: List[List[int]]) -> List[List[int]]:
    if not intervals:
        return []
    intervals = sorted(intervals)
    res = [intervals[0]]
    for start, end in intervals[1:]:
        if start <= res[-1][1]:
            res[-1][1] = max(res[-1][1], end)
        else:
            res.append([start, end])
    return res


def _erase_overlap(intervals: List[List[int]]) -> int:
    intervals = sorted(intervals, key=lambda x: x[1])
    removed = 0
    end = float("-inf")
    for start, e in intervals:
        if start < end:
            removed += 1
        else:
            end = e
    return removed


def _least_interval(tasks: List[str], n: int) -> int:
    from collections import Counter

    counts = list(Counter(tasks).values())
    max_freq = max(counts)
    num_max = counts.count(max_freq)
    return max(len(tasks), (max_freq - 1) * (n + 1) + num_max)
