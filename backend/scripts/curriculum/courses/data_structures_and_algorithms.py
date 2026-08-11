"""Data Structures and Algorithms — curriculum content module."""

COURSE = {
    "id": "data-structures-and-algorithms",
    "title": "Data Structures and Algorithms",
    "description": (
        "Master the fundamentals of computer science: time complexity, arrays, "
        "linked structures, recursion, searching and sorting, trees, graphs, and "
        "algorithmic problem-solving. Every concept is paired with Python "
        "exercises you can run right here."
    ),
    "language": "python",
    "icon": "code",
    "order": 9,
}

MODULES = [
    {
        "id": "dsa-complexity",
        "course_id": "data-structures-and-algorithms",
        "title": "Complexity and Arrays",
        "description": "Learn to reason about algorithm speed with Big-O, then build on arrays with prefix sums and two-pointer techniques.",
        "order": 1,
    },
    {
        "id": "dsa-linked",
        "course_id": "data-structures-and-algorithms",
        "title": "Linked Structures and Recursion",
        "description": "Understand nodes and pointers, and master recursion — the technique behind linked lists, trees, and more.",
        "order": 2,
    },
    {
        "id": "dsa-search",
        "course_id": "data-structures-and-algorithms",
        "title": "Searching and Sorting",
        "description": "From linear and binary search to selection sort and merge, learn the algorithms that organize and find data.",
        "order": 3,
    },
    {
        "id": "dsa-trees",
        "course_id": "data-structures-and-algorithms",
        "title": "Trees and Graphs",
        "description": "Explore tree terminology, traversals, binary search trees, and graphs with breadth- and depth-first search.",
        "order": 4,
    },
    {
        "id": "dsa-problems",
        "course_id": "data-structures-and-algorithms",
        "title": "Algorithmic Problem Solving",
        "description": "Combine everything in a structured problem-solving method, then apply greedy and dynamic-programming ideas.",
        "order": 5,
    },
]

_PY = "python"


def L(**kw):
    kw.setdefault("language", _PY)
    return kw


LESSONS = [
    # ── Module 1: Complexity and Arrays ─────────────────────────────────
    L(
        id="dsa-complexity-big-o",
        course_id="data-structures-and-algorithms",
        module_id="dsa-complexity",
        title="Big-O Notation and Why It Matters",
        type="theory",
        order=1,
        content="""## Big-O Notation and Why It Matters

Big-O notation describes how an algorithm's **runtime or memory grows** as the input size grows. It lets you compare algorithms by their *growth rate*, not by wall-clock time, which depends on hardware.

### Reading Big-O

| Notation | Name        | Example                         |
|----------|-------------|---------------------------------|
| `O(1)`   | constant    | indexing a list                 |
| `O(log n)` | logarithmic | binary search                 |
| `O(n)`   | linear      | a single pass through the input |
| `O(n log n)` | linearithmic | efficient sorting            |
| `O(n²)`  | quadratic   | nested loops over the input     |
| `O(2ⁿ)`  | exponential | naive recursion                 |

### Why n² beats n when n is small

Big-O is about **large** inputs. A slow constant (`10n`) beats a fast quadratic (`n²`) once `n` grows past 10:

```python
def linear(items):      # O(n)
    total = 0
    for x in items:
        total += x
    return total

def quadratic(items):   # O(n^2)
    total = 0
    for x in items:
        for y in items:
            total += x + y
    return total
```

### Dropping constants

We keep only the dominant term and drop constant factors: `3n² + 5n + 20` is `O(n²)`.

### A mental model

If `n` doubles:

- `O(1)` stays the same.
- `O(n)` doubles.
- `O(n²)` quadruples.

That difference is why an `O(n²)` solution can take minutes where an `O(n)` solution takes milliseconds.

### Space complexity

Big-O also describes memory. Building a second copy of the input is `O(n)` space; an in-place algorithm is `O(1)`.

Always ask two questions before solving a problem: **What is the best possible time?** and **What is my solution's complexity?** Most interview and competition problems reward pushing from `O(n²)` down to `O(n)` or `O(n log n)`.

---

**Next up:** arrays — the data structure nearly every algorithm builds on."""
    ),
    L(
        id="dsa-complexity-arrays",
        course_id="data-structures-and-algorithms",
        module_id="dsa-complexity",
        title="Arrays: The Workhorse Data Structure",
        type="theory",
        order=2,
        content="""## Arrays: The Workhorse Data Structure

An **array** is a contiguous block of memory holding elements of the same type. Python's `list` is a dynamic array: it grows automatically while keeping the same guarantees.

### Reading by index is O(1)

```python
scores = [70, 80, 90, 100]
print(scores[0])   # 70
print(scores[-1])  # 100
```

Because elements sit side by side in memory, computing the address of element `i` is a single arithmetic step: `O(1)`.

### Appending is amortized O(1)

```python
scores.append(110)   # usually O(1)
```

When the array fills, Python allocates a bigger block and copies — occasionally `O(n)`. On average, though, appends are constant time.

### Inserting and deleting in the middle is O(n)

```python
scores.insert(1, 75)   # shifts everything after index 1
```

Every element to the right must move, so insert and delete are `O(n)`. This is the classic array trade-off: **fast reads, slow middle edits**.

### Slicing creates copies

```python
left = scores[:2]      # new list of 2 elements
```

Slicing is `O(k)` for the number of elements copied.

### Operations cheat sheet

| Operation            | Complexity |
|----------------------|------------|
| index by position    | `O(1)`     |
| append               | `O(1)` amortized |
| insert / delete mid  | `O(n)`     |
| search (unsorted)    | `O(n)`     |
| search (sorted)      | `O(log n)` |

### Choosing arrays

Use arrays when:

- You need fast random access.
- The size is roughly known in advance.
- You mostly append and read.

When you need frequent middle insertions or deletions, a linked structure (next lesson's topic) or a deque may serve better.

---

**Next up:** prefix sums for instant range queries."""
    ),
    L(
        id="dsa-complexity-prefix",
        course_id="data-structures-and-algorithms",
        module_id="dsa-complexity",
        title="Prefix Sums and Range Queries",
        type="theory",
        order=3,
        content="""## Prefix Sums and Range Queries

A **prefix sum** array stores the running total. Once built, it answers "what is the sum of elements `i` through `j`?" in `O(1)`.

### Building a prefix array

```python
nums = [1, 2, 3, 4]
prefix = [0]
for x in nums:
    prefix.append(prefix[-1] + x)
# prefix = [0, 1, 3, 6, 10]
```

`prefix[k]` is the sum of the first `k` elements.

### Answering range queries

The sum of `nums[i]` through `nums[j]` (inclusive) is:

```python
def range_sum(prefix, i, j):
    return prefix[j + 1] - prefix[i]
```

For `nums = [1, 2, 3, 4]`, the sum of indexes 1–2 (`2 + 3`) is `prefix[3] - prefix[1] = 6 - 1 = 5`.

### Why it matters

Without prefix sums, each query walks the range: `O(n)` per query. With them, the precompute is `O(n)` and **every query is O(1)**:

```python
queries = [(1, 3), (0, 2), (2, 3)]
answers = [range_sum(prefix, i, j) for i, j in queries]
```

If you answer thousands of queries, this transforms a slow loop into instant lookups.

### The general pattern

The prefix technique generalizes:

- **Prefix products** for multiplicative ranges.
- **Prefix minimums** for sliding minimums.
- **2D prefix sums** for rectangle sums on a grid.

### Checklist

1. Precompute prefix sums once: `O(n)`.
2. Replace every range-sum loop with two array reads.
3. Total complexity: `O(n + q)` instead of `O(n × q)`.

Anytime a problem asks for many range sums, range products, or range minimums, reach for a prefix array before you reach for a loop.

---

**Next up:** two pointers and sliding windows."""
    ),
    L(
        id="dsa-complexity-two-pointers",
        course_id="data-structures-and-algorithms",
        module_id="dsa-complexity",
        title="Two Pointers and Sliding Window",
        type="theory",
        order=4,
        content="""## Two Pointers and Sliding Window

Many array problems become trivially fast with **two pointers**: keep two indices and move them intelligently. The classic example is **Two Sum on a sorted array**.

### Two pointers on sorted input

```python
def has_pair(nums, target):      # nums is sorted
    left, right = 0, len(nums) - 1
    while left < right:
        total = nums[left] + nums[right]
        if total == target:
            return True
        elif total < target:
            left += 1
        else:
            right -= 1
    return False
```

Each step shrinks the search space, so this is `O(n)` — much better than the `O(n²)` double loop.

### The sliding window

A **window** is a contiguous slice of the array. Slide its start or end to track a running property:

```python
def max_k_sum(nums, k):
    window = sum(nums[:k])
    best = window
    for i in range(k, len(nums)):
        window += nums[i] - nums[i - k]
        best = max(best, window)
    return best
```

The window "slides" by adding one element and dropping one, keeping the sum updated in `O(1)` per step — `O(n)` total.

### Choosing the right tool

| Pattern        | Best for                                       | Complexity |
|----------------|------------------------------------------------|------------|
| two pointers   | sorted arrays, pairs, partitioning             | `O(n)`     |
| sliding window | contiguous subarrays with a constraint          | `O(n)`     |
| nested loops   | tiny inputs, all pairs without constraints      | `O(n²)`    |

### When two pointers won't work

- Unsorted input with no room to pre-sort.
- Windows that must shrink and grow while keeping a count (a hash map helps there).

### The habit

Before writing a nested loop over an array, ask: *can a second pointer or a sliding window do this in one pass?* It is one of the highest-leverage speed-ups in all of algorithm design.

---

**Next up:** exercises — Two Sum, maximum subarray, and prefix-sum ranges."""
    ),
    L(
        id="dsa-complexity-exercise-two-sum",
        course_id="data-structures-and-algorithms",
        module_id="dsa-complexity",
        title="Exercise: Two Sum",
        type="exercise",
        order=5,
        content="""## Exercise: Two Sum

Write a function `solve(nums, target)` that returns the **indices** of two numbers that add up to `target`. You may assume exactly one solution exists, and you may not use the same element twice.

### Worked sample

Input:

```text
[2,7,11,15]
9
```

Output:

```text
[0,1]
```

Because `nums[0] + nums[1] == 9`.

### How your code runs

The runner parses the first input line as the list and the second as the target, then calls `solve(nums, target)`. Return the two indices as a list — list outputs serialize as compact JSON like `[0,1]`.

### Think

A hash map (`dict`) stores each number with its index as you scan. When you meet `num`, check whether `target - num` is already in the map. This runs in `O(n)`.

### Starter code

```python
def solve(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []


def main():
    import sys
    import json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    parts = raw.split("\\n")
    nums = json.loads(parts[0])
    target = json.loads(parts[1])
    result = solve(nums, target)
    if isinstance(result, list):
        print(json.dumps(result, separators=(",", ":")))
    else:
        print(result)


if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []


def main():
    import sys
    import json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    parts = raw.split("\\n")
    nums = json.loads(parts[0])
    target = json.loads(parts[1])
    result = solve(nums, target)
    if isinstance(result, list):
        print(json.dumps(result, separators=(",", ":")))
    else:
        print(result)


if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": "[2,7,11,15]\n9", "expected_output": "[0,1]", "description": "Classic pair"},
            {"input": "[3,2,4]\n6", "expected_output": "[1,2]", "description": "Not the first two"},
            {"input": "[3,3]\n6", "expected_output": "[0,1]", "description": "Duplicate values"},
        ],
    ),
    L(
        id="dsa-complexity-exercise-max-subarray",
        course_id="data-structures-and-algorithms",
        module_id="dsa-complexity",
        title="Exercise: Maximum Subarray",
        type="exercise",
        order=6,
        content="""## Exercise: Maximum Subarray

Write a function `solve(nums)` that returns the sum of the **contiguous subarray** with the largest sum (Kadane's algorithm).

### Worked sample

Input:

```text
[-2,1,-3,4,-1,2,1,-5,4]
```

Output:

```text
6
```

The best subarray is `[4,-1,2,1]`, which sums to `6`.

### How your code runs

The runner parses the single input line as a list and calls `solve(nums)`. Return the maximum sum as an integer.

### Think

Keep two values as you scan: `current` — the best sum ending at the current element — and `best` — the best seen so far. For each element, either extend the current run (`current + num`) or start fresh (`num`).

```python
def solve(nums):
    best = current = nums[0]
    for num in nums[1:]:
        current = max(num, current + num)
        best = max(best, current)
    return best
```

This is `O(n)`.

### Starter code

```python
def solve(nums):
    best = current = nums[0]
    for num in nums[1:]:
        current = max(num, current + num)
        best = max(best, current)
    return best


def main():
    import sys
    import json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    nums = json.loads(raw)
    print(solve(nums))


if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(nums):
    best = current = nums[0]
    for num in nums[1:]:
        current = max(num, current + num)
        best = max(best, current)
    return best


def main():
    import sys
    import json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    nums = json.loads(raw)
    print(solve(nums))


if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": "[-2,1,-3,4,-1,2,1,-5,4]", "expected_output": "6", "description": "Classic Kadane input"},
            {"input": "[1]", "expected_output": "1", "description": "Single element"},
            {"input": "[5,4,-1,7,8]", "expected_output": "23", "description": "Whole array is best"},
        ],
    ),
    L(
        id="dsa-complexity-exercise-prefix-sum",
        course_id="data-structures-and-algorithms",
        module_id="dsa-complexity",
        title="Exercise: Prefix Sum Range",
        type="exercise",
        order=7,
        content="""## Exercise: Prefix Sum Range

Write a function `solve(nums, start, end)` that returns the sum of `nums[start]` through `nums[end]` **inclusive**, using a prefix sum array for `O(1)` queries.

### Worked sample

Input:

```text
[1,2,3,4,5]
1
3
```

Output:

```text
9
```

Because `2 + 3 + 4 = 9`.

### How your code runs

The runner parses each input line as a JSON value and calls `solve(nums, start, end)`. Return the range sum as an integer.

### Think

Build `prefix` where `prefix[k]` is the sum of the first `k` elements. The answer is `prefix[end + 1] - prefix[start]`.

```python
def solve(nums, start, end):
    prefix = [0]
    for num in nums:
        prefix.append(prefix[-1] + num)
    return prefix[end + 1] - prefix[start]
```

### Starter code

```python
def solve(nums, start, end):
    prefix = [0]
    for num in nums:
        prefix.append(prefix[-1] + num)
    return prefix[end + 1] - prefix[start]


def main():
    import sys
    import json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    parts = raw.split("\\n")
    nums = json.loads(parts[0])
    start = json.loads(parts[1])
    end = json.loads(parts[2])
    print(solve(nums, start, end))


if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(nums, start, end):
    prefix = [0]
    for num in nums:
        prefix.append(prefix[-1] + num)
    return prefix[end + 1] - prefix[start]


def main():
    import sys
    import json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    parts = raw.split("\\n")
    nums = json.loads(parts[0])
    start = json.loads(parts[1])
    end = json.loads(parts[2])
    print(solve(nums, start, end))


if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": "[1,2,3,4,5]\n1\n3", "expected_output": "9", "description": "Middle range"},
            {"input": "[10,20,30]\n0\n0", "expected_output": "10", "description": "Single index"},
            {"input": "[1,2,3]\n0\n2", "expected_output": "6", "description": "Full array"},
        ],
    ),
    # ── Module 2: Linked Structures and Recursion ───────────────────────
    L(
        id="dsa-linked-nodes",
        course_id="data-structures-and-algorithms",
        module_id="dsa-linked",
        title="Nodes and Pointers",
        type="theory",
        order=1,
        content="""## Nodes and Pointers

A **linked structure** is built from **nodes**, where each node holds a value and a **pointer** to the next node. Unlike an array, there is no contiguous block of memory — nodes can live anywhere, chained together by references.

### A node in Python

```python
class Node:
    def __init__(self, value, next_node=None):
        self.value = value
        self.next = next_node

head = Node(1)
head.next = Node(2)
head.next.next = Node(3)
```

### The cost trade-off

| Operation             | Array   | Linked list |
|-----------------------|---------|-------------|
| read by index         | `O(1)`  | `O(n)`      |
| insert at head        | `O(n)`  | `O(1)`      |
| delete at head        | `O(n)`  | `O(1)`      |
| search                | `O(n)`  | `O(n)`      |

Linked lists shine when you constantly insert or delete at the **front**, because no elements shift — you just rewire a pointer.

### Traversal

Linked structures have no indices. You walk the chain:

```python
def traverse(head):
    current = head
    while current is not None:
        print(current.value)
        current = current.next
```

### Danger: lost references

Reordering nodes means updating pointers carefully:

```python
head.next.next = head.next   # BAD — you just pointed node 2 at itself
```

A classic bug: saving the next node before re-pointing, so you do not lose the rest of the list.

### Everywhere in CS

Nodes appear as linked lists, but the same "value + pointer" idea underlies trees (left/right child pointers), graphs (adjacency), and hash-map buckets. Once you can reason about chained nodes, all of these feel familiar.

---

**Next up:** recursion — the natural way to process nested structures."""
    ),
    L(
        id="dsa-linked-recursion",
        course_id="data-structures-and-algorithms",
        module_id="dsa-linked",
        title="Recursion: Divide and Conquer Thinking",
        type="theory",
        order=2,
        content="""## Recursion: Divide and Conquer Thinking

**Recursion** is a function that calls itself. Every recursive function needs two parts: a **base case** that stops the recursion, and a **recursive case** that breaks the problem into a smaller version of itself.

### Anatomy of a recursive function

```python
def countdown(n):
    if n <= 0:          # base case
        return
    print(n)
    countdown(n - 1)    # recursive case — smaller input
```

Each call creates a new frame on the **call stack**, then unwinds when the base case is reached.

### A mathematical example

```python
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
```

`factorial(4)` expands to `4 * factorial(3)` → `4 * (3 * factorial(2))` → `4 * (3 * (2 * 1))`.

### The three laws

1. **A base case** that ends the recursion.
2. **A change of state** — each call moves toward the base case.
3. **A call to itself** on the smaller input.

If you violate rule 2, you get infinite recursion (Python raises `RecursionError`).

### Thinking recursively

To solve `f(n)`:

- What is the trivial version I can answer directly? (base case)
- How can I express `f(n)` in terms of `f(smaller)`? (recursive case)

### When recursion shines

- Trees and graphs — nested structures match recursion naturally.
- Divide-and-conquer algorithms: merge sort, quicksort, binary search.
- Backtracking problems: permutations, mazes, pathfinding.

### When it struggles

Python's default recursion limit is around 1000 frames. Deep recursion overflows the stack — that is when you convert to an explicit loop or use iteration instead.

---

**Next up:** stacks and queues — the workhorse containers."""
    ),
    L(
        id="dsa-linked-stacks",
        course_id="data-structures-and-algorithms",
        module_id="dsa-linked",
        title="Stacks and Queues",
        type="theory",
        order=3,
        content="""## Stacks and Queues

**Stacks** and **queues** are restricted lists with strict rules about where you can add and remove items. These restrictions make them predictable and powerful.

### Stack: last in, first out (LIFO)

Like a stack of plates — you take the top plate first. Python lists make perfect stacks:

```python
stack = []
stack.append(1)      # push
stack.append(2)
top = stack.pop()    # pop -> 2
```

Operations: `push` and `pop`, both `O(1)`.

**Uses:** the function call stack, undo/redo, matching brackets, expression evaluation, backtracking.

### Queue: first in, first out (FIFO)

Like a line at the checkout — first come, first served. Use `collections.deque`:

```python
from collections import deque
queue = deque()
queue.append(1)          # enqueue
queue.append(2)
first = queue.popleft()  # dequeue -> 1
```

Both `append` and `popleft` are `O(1)` — unlike `list.pop(0)` which shifts everything.

### Matching brackets with a stack

```python
def is_balanced(text):
    stack = []
    pairs = {")": "(", "]": "[", "}": "{"}
    for ch in text:
        if ch in "([{":
            stack.append(ch)
        elif ch in ")]}":
            if not stack or stack.pop() != pairs[ch]:
                return False
    return not stack
```

### Choosing a container

| Need                               | Use         |
|------------------------------------|-------------|
| most recent item first             | stack       |
| oldest item first                  | queue       |
| push/pop at both ends              | deque       |
| fast indexed access + append       | list        |

### Implementation note

You can implement a stack with either an array or a linked list — both give `O(1)` push/pop. That is the elegant thing: the *interface* (LIFO/FIFO) is what matters, and the implementation just has to honor it.

---

**Next up:** recursion vs iteration — when to use which."""
    ),
    L(
        id="dsa-linked-iteration",
        course_id="data-structures-and-algorithms",
        module_id="dsa-linked",
        title="Recursion vs Iteration",
        type="theory",
        order=4,
        content="""## Recursion vs Iteration

Anything you can do with recursion you can also do with a loop — and vice versa. Choosing between them is about clarity, stack limits, and performance.

### The same problem, two ways

```python
# Iterative
def factorial_iter(n):
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

# Recursive
def factorial_rec(n):
    if n <= 1:
        return 1
    return n * factorial_rec(n - 1)
```

### Why iteration sometimes wins

- **No stack risk.** Deep recursion hits Python's ~1000-frame limit and raises `RecursionError`.
- **No overhead.** Each recursive call allocates a stack frame; loops reuse one frame.
- **Easier to predict.** State lives in plain variables.

### Why recursion sometimes wins

- **Matches the structure.** Trees and graphs are naturally recursive; an iterative version needs a manual stack.
- **Less code for branching problems.** Backtracking and divide-and-conquer read much more clearly as recursion.
- **No bookkeeping.** The call stack remembers where you were for free.

### Converting recursion to a loop

Rewrite recursion iteratively with an explicit stack:

```python
def sum_range(n):
    # iterative version of: if n == 0: return 0; return n + sum_range(n-1)
    total = 0
    for i in range(1, n + 1):
        total += i
    return total
```

### The practical rule

- Tail-style linear recursion (factorial, sum) → prefer a loop.
- Tree/graph traversal and divide-and-conquer → recursion is usually clearer and the depth is logarithmic anyway.

### Memoization blurs the line

Cached recursion (dynamic programming) combines the clarity of recursion with near-iterative performance. You will see this pattern again in the final module.

---

**Next up:** exercises — factorial, Fibonacci, and recursive reversal."""
    ),
    L(
        id="dsa-linked-exercise-factorial",
        course_id="data-structures-and-algorithms",
        module_id="dsa-linked",
        title="Exercise: Factorial",
        type="exercise",
        order=5,
        content="""## Exercise: Factorial

Write a recursive function `solve(n)` that returns `n!` (the product of all integers from 1 to n). By definition, `0! = 1`.

### Worked sample

Input:

```text
5
```

Output:

```text
120
```

Because `5! = 5 × 4 × 3 × 2 × 1 = 120`.

### How your code runs

The runner parses the input line as an integer and calls `solve(n)`. Return the factorial as an integer.

### Think

Base case: `n <= 1` returns `1`. Recursive case: `n * solve(n - 1)`.

### Starter code

```python
def solve(n):
    if n <= 1:
        return 1
    return n * solve(n - 1)


def main():
    import sys
    raw = sys.stdin.read().strip()
    if not raw:
        return
    n = int(raw)
    print(solve(n))


if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(n):
    if n <= 1:
        return 1
    return n * solve(n - 1)


def main():
    import sys
    raw = sys.stdin.read().strip()
    if not raw:
        return
    n = int(raw)
    print(solve(n))


if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": "5", "expected_output": "120", "description": "Five"},
            {"input": "0", "expected_output": "1", "description": "Zero by definition"},
            {"input": "10", "expected_output": "3628800", "description": "Ten"},
        ],
    ),
    L(
        id="dsa-linked-exercise-fibonacci",
        course_id="data-structures-and-algorithms",
        module_id="dsa-linked",
        title="Exercise: Fibonacci",
        type="exercise",
        order=6,
        content="""## Exercise: Fibonacci

Write a function `solve(n)` that returns the **nth Fibonacci number** with `fib(0) = 0` and `fib(1) = 1`.

### Worked sample

Input:

```text
10
```

Output:

```text
55
```

The Fibonacci sequence is `0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, ...`.

### How your code runs

The runner parses the input line as an integer and calls `solve(n)`. Return the Fibonacci number as an integer.

### Think

The recursive definition is `fib(n) = fib(n-1) + fib(n-2)`, but plain recursion recomputes the same values many times. Prefer the iterative version: keep two variables and slide them forward — `O(n)` time.

### Starter code

```python
def solve(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def main():
    import sys
    raw = sys.stdin.read().strip()
    if not raw:
        return
    n = int(raw)
    print(solve(n))


if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def main():
    import sys
    raw = sys.stdin.read().strip()
    if not raw:
        return
    n = int(raw)
    print(solve(n))


if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": "0", "expected_output": "0", "description": "Base case zero"},
            {"input": "1", "expected_output": "1", "description": "Base case one"},
            {"input": "10", "expected_output": "55", "description": "Tenth Fibonacci"},
        ],
    ),
    L(
        id="dsa-linked-exercise-reverse",
        course_id="data-structures-and-algorithms",
        module_id="dsa-linked",
        title="Exercise: Reverse a List Recursively",
        type="exercise",
        order=7,
        content="""## Exercise: Reverse a List Recursively

Write a recursive function `solve(nums)` that returns a **new list** with the elements in reverse order.

### Worked sample

Input:

```text
[1,2,3,4]
```

Output:

```text
[4,3,2,1]
```

### How your code runs

The runner parses the input line as a list and calls `solve(nums)`. List outputs serialize as compact JSON like `[4,3,2,1]`.

### Think

Base case: an empty list reverses to itself. Recursive case: the reverse of `[first, *rest]` is the reverse of `rest` followed by `first`.

```python
def solve(nums):
    if not nums:
        return []
    return solve(nums[1:]) + [nums[0]]
```

Note this builds new lists — that is expected for this exercise, even though a loop would be more efficient.

### Starter code

```python
def solve(nums):
    if not nums:
        return []
    return solve(nums[1:]) + [nums[0]]


def main():
    import sys
    import json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    nums = json.loads(raw)
    result = solve(nums)
    if isinstance(result, list):
        print(json.dumps(result, separators=(",", ":")))
    else:
        print(result)


if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(nums):
    if not nums:
        return []
    return solve(nums[1:]) + [nums[0]]


def main():
    import sys
    import json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    nums = json.loads(raw)
    result = solve(nums)
    if isinstance(result, list):
        print(json.dumps(result, separators=(",", ":")))
    else:
        print(result)


if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": "[1,2,3,4]", "expected_output": "[4,3,2,1]", "description": "Four elements"},
            {"input": "[7]", "expected_output": "[7]", "description": "Single element"},
            {"input": "[1,2]", "expected_output": "[2,1]", "description": "Two elements"},
        ],
    ),
    # ── Module 3: Searching and Sorting ─────────────────────────────────
    L(
        id="dsa-search-linear",
        course_id="data-structures-and-algorithms",
        module_id="dsa-search",
        title="Linear Search",
        type="theory",
        order=1,
        content="""## Linear Search

**Linear search** checks every element in order until it finds the target (or reaches the end). It is the simplest search algorithm and the only one that works on **unsorted** data.

### Implementation

```python
def linear_search(items, target):
    for i, item in enumerate(items):
        if item == target:
            return i
    return -1
```

### Complexity

- Worst case: the target is last or absent → every element examined → `O(n)`.
- Best case: the target is first → `O(1)`.
- Average: `O(n)`.

There is no way around it for unsorted data: with no ordering to exploit, you must look at each candidate.

### When to use linear search

- The list is **unsorted** (sorting would cost `O(n log n)`).
- The list is small — a linear scan is fast in practice.
- You search only a few times, so the cost of sorting or hashing is not worth it.
- The data is a stream you can only see once.

### The n vs log n trade

| Search     | Sorted? | Complexity |
|------------|---------|------------|
| linear     | no      | `O(n)`     |
| binary     | yes     | `O(log n)` |

If you search many times, sorting once (`O(n log n)`) and then using binary search beats linear search for large `n`.

### A common variant

Linear search also covers *find the maximum* or *find the first element matching a condition* — any problem that must inspect every candidate. The pattern is identical: iterate, compare, remember the best.

Linear search is rarely the headline algorithm, but it is the baseline every faster search is measured against.

---

**Next up:** binary search — exponentially faster on sorted data."""
    ),
    L(
        id="dsa-search-binary",
        course_id="data-structures-and-algorithms",
        module_id="dsa-search",
        title="Binary Search",
        type="theory",
        order=2,
        content="""## Binary Search

**Binary search** finds a target in a **sorted** array by repeatedly halving the search range. Each step eliminates half the remaining elements, giving `O(log n)` time.

### The core idea

1. Look at the middle element.
2. If it equals the target — done.
3. If it is greater, the target must be in the left half.
4. If it is smaller, the target must be in the right half.

### Implementation

```python
def binary_search(nums, target):
    low, high = 0, len(nums) - 1
    while low <= high:
        mid = (low + high) // 2
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1
```

### Why log n

Each comparison halves the search space. After `k` steps you have reduced `n` to `n / 2ᵏ`. Setting that equal to 1 gives `k = log₂(n)`.

For a million elements, linear search may need a million steps; binary search needs about 20.

### The two classic bugs

1. **Off-by-one in the loop condition.** `while low < high` drops the last element. Use `low <= high` for the "found exact index" version.
2. **`mid` overflow.** `(low + high) // 2` is fine in Python; in other languages use `low + (high - low) // 2`.

### Variants

- First occurrence of a value.
- Last occurrence.
- Insertion point for a new value (`bisect` module does exactly this).
- Search on the *answer space*: binary search the smallest valid answer when the check is monotonic.

### Monotonicity is the key

Binary search only works when the predicate is **monotonic** — once the condition becomes true, it stays true. That single property is what makes "half the space is safe to discard."

---

**Next up:** selection sort and the family of simple sorts."""
    ),
    L(
        id="dsa-search-basic-sorts",
        course_id="data-structures-and-algorithms",
        module_id="dsa-search",
        title="Selection and Insertion Sort",
        type="theory",
        order=3,
        content="""## Selection and Insertion Sort

The simple sorts are easy to understand, easy to write, and too slow for big data — but they build intuition that merge sort and quicksort rely on.

### Selection sort

Repeatedly find the smallest element in the unsorted part and swap it into place:

```python
def selection_sort(arr):
    for i in range(len(arr)):
        smallest = i
        for j in range(i + 1, len(arr)):
            if arr[j] < arr[smallest]:
                smallest = j
        arr[i], arr[smallest] = arr[smallest], arr[i]
    return arr
```

- The outer loop runs `n` times; the inner scan is `n - i` → `O(n²)` always.
- Swaps are minimal — at most `n - 1`.

### Insertion sort

Build the sorted portion one element at a time, inserting each new element into its correct place:

```python
def insertion_sort(arr):
    for i in range(1, len(arr)):
        current = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > current:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = current
    return arr
```

- Worst case `O(n²)`, but **near-sorted input is nearly O(n)**.
- Excellent for small arrays — Python's own sort uses it for tiny runs.

### Comparing the two

| Sort            | Best     | Average  | Worst    | Stable |
|-----------------|----------|----------|----------|--------|
| selection       | `O(n²)`  | `O(n²)`  | `O(n²)`  | no     |
| insertion       | `O(n)`   | `O(n²)`  | `O(n²)`  | yes    |
| merge           | `O(n log n)` | `O(n log n)` | `O(n log n)` | yes |

*Stable* means equal elements keep their relative order — important when sorting on one key while preserving another.

### The lesson

`O(n²)` sorting is fine for a few dozen elements and hopeless for a million. That is why the next lesson's divide-and-conquer sorts exist.

---

**Next up:** merge sort — the O(n log n) breakthrough."""
    ),
    L(
        id="dsa-search-divide-conquer",
        course_id="data-structures-and-algorithms",
        module_id="dsa-search",
        title="Merge Sort and Beyond",
        type="theory",
        order=4,
        content="""## Merge Sort and Beyond

**Merge sort** is the canonical divide-and-conquer sort: split the array, sort each half, then merge. It guarantees `O(n log n)` on every input.

### Divide, conquer, combine

```python
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)


def merge(a, b):
    result = []
    i = j = 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            result.append(a[i]); i += 1
        else:
            result.append(b[j]); j += 1
    result.extend(a[i:])
    result.extend(b[j:])
    return result
```

### Why O(n log n)

Each level of recursion touches all `n` elements during the merges, and there are `log n` levels. Hence `n log n`.

### Space cost

`merge` builds new lists, so merge sort uses `O(n)` extra memory. That is its main drawback versus in-place sorts.

### The Python way

For real code you rarely hand-write sorts — Python's built-in sort is a hybrid (Timsort) that is `O(n log n)` worst case and near-`O(n)` on sorted data:

```python
sorted([5, 2, 9, 1])        # [1, 2, 5, 9]
data.sort()                 # in place
data.sort(key=len)          # sort by a key
data.sort(reverse=True)     # descending
```

### Beyond merge sort

| Sort       | Average      | Worst       | Space | Notes                     |
|------------|--------------|-------------|-------|---------------------------|
| quicksort  | `O(n log n)` | `O(n²)`     | `O(log n)` | fast in practice, in place |
| heapsort   | `O(n log n)` | `O(n log n)` | `O(1)` | in place, not stable      |
| counting   | `O(n + k)`   | `O(n + k)`   | `O(k)` | only for small-range ints |

The pattern to internalize: **divide the problem, solve the pieces, combine the results** — it powers search, sort, and the tree algorithms coming next.

---

**Next up:** exercises — binary search, selection sort, and merging."""
    ),
    L(
        id="dsa-search-exercise-binary",
        course_id="data-structures-and-algorithms",
        module_id="dsa-search",
        title="Exercise: Binary Search",
        type="exercise",
        order=5,
        content="""## Exercise: Binary Search

Write a function `solve(nums, target)` that returns the index of `target` in the **sorted** list `nums`, or `-1` if it is absent.

### Worked sample

Input:

```text
[1,3,5,7,9]
5
```

Output:

```text
2
```

### How your code runs

The runner parses the first line as the list and the second as the target, then calls `solve(nums, target)`. Return the index as an integer.

### Think

Use `low` and `high` pointers, check the middle, and discard half the range each step. Remember the loop condition `low <= high` so the final element is not skipped.

### Starter code

```python
def solve(nums, target):
    low, high = 0, len(nums) - 1
    while low <= high:
        mid = (low + high) // 2
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1


def main():
    import sys
    import json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    parts = raw.split("\\n")
    nums = json.loads(parts[0])
    target = json.loads(parts[1])
    print(solve(nums, target))


if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(nums, target):
    low, high = 0, len(nums) - 1
    while low <= high:
        mid = (low + high) // 2
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1


def main():
    import sys
    import json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    parts = raw.split("\\n")
    nums = json.loads(parts[0])
    target = json.loads(parts[1])
    print(solve(nums, target))


if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": "[1,3,5,7,9]\n5", "expected_output": "2", "description": "Found in the middle"},
            {"input": "[1,3,5]\n4", "expected_output": "-1", "description": "Not present"},
            {"input": "[2]\n2", "expected_output": "0", "description": "Single element"},
        ],
    ),
    L(
        id="dsa-search-exercise-selection-sort",
        course_id="data-structures-and-algorithms",
        module_id="dsa-search",
        title="Exercise: Selection Sort",
        type="exercise",
        order=6,
        content="""## Exercise: Selection Sort

Write a function `solve(nums)` that returns `nums` sorted in ascending order **using selection sort** (do not call the built-in `sort`/`sorted`).

### Worked sample

Input:

```text
[5,2,9,1,5]
```

Output:

```text
[1,2,5,5,9]
```

### How your code runs

The runner parses the input line as a list and calls `solve(nums)`. List outputs serialize as compact JSON like `[1,2,5,5,9]`.

### Think

For each position `i`, scan the rest of the list for the smallest element and swap it into place. Copy the input first (`list(nums)`) so you do not mutate the caller's list.

### Starter code

```python
def solve(nums):
    arr = list(nums)
    for i in range(len(arr)):
        smallest = i
        for j in range(i + 1, len(arr)):
            if arr[j] < arr[smallest]:
                smallest = j
        arr[i], arr[smallest] = arr[smallest], arr[i]
    return arr


def main():
    import sys
    import json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    nums = json.loads(raw)
    result = solve(nums)
    if isinstance(result, list):
        print(json.dumps(result, separators=(",", ":")))
    else:
        print(result)


if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(nums):
    arr = list(nums)
    for i in range(len(arr)):
        smallest = i
        for j in range(i + 1, len(arr)):
            if arr[j] < arr[smallest]:
                smallest = j
        arr[i], arr[smallest] = arr[smallest], arr[i]
    return arr


def main():
    import sys
    import json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    nums = json.loads(raw)
    result = solve(nums)
    if isinstance(result, list):
        print(json.dumps(result, separators=(",", ":")))
    else:
        print(result)


if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": "[5,2,9,1,5]", "expected_output": "[1,2,5,5,9]", "description": "Duplicates preserved"},
            {"input": "[3,2,1]", "expected_output": "[1,2,3]", "description": "Reverse sorted"},
            {"input": "[1]", "expected_output": "[1]", "description": "Single element"},
        ],
    ),
    L(
        id="dsa-search-exercise-merge",
        course_id="data-structures-and-algorithms",
        module_id="dsa-search",
        title="Exercise: Merge Two Sorted Lists",
        type="exercise",
        order=7,
        content="""## Exercise: Merge Two Sorted Lists

Write a function `solve(a, b)` that merges two **already-sorted** lists into one sorted list.

### Worked sample

Input:

```text
[1,3,5]
[2,4,6]
```

Output:

```text
[1,2,3,4,5,6]
```

### How your code runs

The runner parses each input line as a list and calls `solve(a, b)`. List outputs serialize as compact JSON like `[1,2,3,4,5,6]`.

### Think

Use two indices and repeatedly append the smaller front element. When one list is exhausted, append the rest of the other. This merge is the heart of merge sort.

### Starter code

```python
def solve(a, b):
    result = []
    i = j = 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            result.append(a[i])
            i += 1
        else:
            result.append(b[j])
            j += 1
    result.extend(a[i:])
    result.extend(b[j:])
    return result


def main():
    import sys
    import json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    parts = raw.split("\\n")
    a = json.loads(parts[0])
    b = json.loads(parts[1])
    result = solve(a, b)
    if isinstance(result, list):
        print(json.dumps(result, separators=(",", ":")))
    else:
        print(result)


if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(a, b):
    result = []
    i = j = 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            result.append(a[i])
            i += 1
        else:
            result.append(b[j])
            j += 1
    result.extend(a[i:])
    result.extend(b[j:])
    return result


def main():
    import sys
    import json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    parts = raw.split("\\n")
    a = json.loads(parts[0])
    b = json.loads(parts[1])
    result = solve(a, b)
    if isinstance(result, list):
        print(json.dumps(result, separators=(",", ":")))
    else:
        print(result)


if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": "[1,3,5]\n[2,4,6]", "expected_output": "[1,2,3,4,5,6]", "description": "Interleaved"},
            {"input": "[1,2]\n[]", "expected_output": "[1,2]", "description": "One empty"},
            {"input": "[1,1,2]\n[1,2,3]", "expected_output": "[1,1,1,2,2,3]", "description": "Duplicates"},
        ],
    ),
    # ── Module 4: Trees and Graphs ──────────────────────────────────────
    L(
        id="dsa-trees-terminology",
        course_id="data-structures-and-algorithms",
        module_id="dsa-trees",
        title="Tree Terminology",
        type="theory",
        order=1,
        content="""## Tree Terminology

A **tree** is a connected, acyclic graph with a single **root**. Trees model hierarchies: file systems, HTML documents, organization charts, and search indexes.

### The vocabulary

| Term        | Meaning                                      |
|-------------|----------------------------------------------|
| root        | the topmost node, no parent                  |
| node        | an element in the tree                       |
| edge        | a connection between parent and child        |
| parent      | a node directly above another                |
| child       | a node directly below its parent             |
| leaf        | a node with no children                      |
| subtree     | a node and all of its descendants            |
| depth       | number of edges from root to a node          |
| height      | number of edges from a node down to a leaf   |

### Representing a binary tree in code

A **binary tree** has at most two children. A common compact encoding uses nested lists: `[value, left, right]` where a missing child is `None`.

```python
tree = [1, [2, None, None], [3, None, None]]
```

### Height and depth

```python
def height(tree):
    if not tree:
        return 0
    value, left, right = tree
    return 1 + max(height(left), height(right))
```

A single-node tree has height 1; an empty one has height 0.

### Properties worth memorizing

- A tree with `n` nodes has exactly `n - 1` edges.
- Every node except the root has exactly one parent.
- Adding one edge to a tree creates a cycle; removing one edge splits it into two trees.

### Balanced vs skewed

A **balanced** tree keeps height near `log n` — that is what keeps operations fast. A **skewed** tree (every node one child) degenerates to a linked list with height `n`.

Tree structure determines performance everywhere it appears, so the first step is always identifying the shape.

---

**Next up:** traversing trees — preorder, inorder, and postorder."""
    ),
    L(
        id="dsa-trees-traversal",
        course_id="data-structures-and-algorithms",
        module_id="dsa-trees",
        title="Tree Traversals",
        type="theory",
        order=2,
        content="""## Tree Traversals

A **traversal** visits every node in a tree exactly once. The three classic depth-first orders differ only in *when* you visit the current node.

### The three orders

```python
def preorder(tree):          # root, left, right
    if not tree:
        return []
    value, left, right = tree
    return [value] + preorder(left) + preorder(right)

def inorder(tree):           # left, root, right
    if not tree:
        return []
    value, left, right = tree
    return inorder(left) + [value] + inorder(right)

def postorder(tree):         # left, right, root
    if not tree:
        return []
    value, left, right = tree
    return postorder(left) + postorder(right) + [value]
```

### What each is good for

| Order     | When you use it                              |
|-----------|----------------------------------------------|
| preorder  | copying a tree, prefix notation, serializing |
| inorder   | reading a BST in sorted order                |
| postorder | freeing nodes, postfix notation, computing size |

### A worked example

For the tree `[1, [2, None, None], [3, None, None]]`:

- preorder: `[1, 2, 3]`
- inorder: `[2, 1, 3]`
- postorder: `[2, 3, 1]`

### Level-order (breadth-first)

Visit nodes top to bottom, left to right, using a queue:

```python
from collections import deque

def level_order(root):
    if not root:
        return []
    result = []
    queue = deque([root])
    while queue:
        node = queue.popleft()
        value, left, right = node
        result.append(value)
        if left:
            queue.append(left)
        if right:
            queue.append(right)
    return result
```

### Why order matters

The same tree printed in different orders is used to reconstruct trees, serialize them for storage, and evaluate arithmetic expressions. Choosing the right traversal is often half of a tree problem.

---

**Next up:** binary search trees — sorted data, logarithmic speed."""
    ),
    L(
        id="dsa-trees-bst",
        course_id="data-structures-and-algorithms",
        module_id="dsa-trees",
        title="Binary Search Trees",
        type="theory",
        order=3,
        content="""## Binary Search Trees

A **binary search tree (BST)** is a binary tree with one ordering rule: every node's left subtree holds **smaller** values and its right subtree holds **larger** values. The rule makes search as fast as binary search on a sorted array.

### The invariant

For every node `n`:

- everything in `n.left` is `< n.value`
- everything in `n.right` is `> n.value`

### Searching

```python
def search(node, target):
    if not node:
        return None
    value, left, right = node
    if target == value:
        return node
    elif target < value:
        return search(left, target)
    else:
        return search(right, target)
```

Each step discards one entire subtree, so search is `O(log n)` — on a balanced tree.

### Inorder gives sorted order

Because of the invariant, an **inorder traversal** visits values in ascending order:

```python
def inorder_values(node):
    if not node:
        return []
    value, left, right = node
    return inorder_values(left) + [value] + inorder_values(right)
```

### Insertion

Walk down comparing values; when you reach an empty spot, attach the new node there.

### The fatal weakness

If values are inserted in sorted order, every node has only a right child and the tree is a **skewed** chain — search degrades to `O(n)`. Balanced variants (AVL trees, red-black trees) rebalance after each insertion to keep height `O(log n)`.

### BST vs hash table

| Operation | BST (balanced) | Hash table |
|-----------|----------------|------------|
| search    | `O(log n)`     | `O(1)` avg |
| find min/max | `O(log n)`  | `O(n)`     |
| sorted traversal | `O(n)`  | not directly |

Hash tables win on raw speed; BSTs win when you need **order** — sorted ranges, min/max, nearest neighbors.

---

**Next up:** graphs and breadth- and depth-first search."""
    ),
    L(
        id="dsa-trees-graphs",
        course_id="data-structures-and-algorithms",
        module_id="dsa-trees",
        title="Graphs and BFS/DFS",
        type="theory",
        order=4,
        content="""## Graphs and BFS/DFS

A **graph** is a set of nodes connected by edges. Trees are a special case: connected, acyclic graphs. Graphs model networks, maps, social connections, and dependencies.

### Representations

The **adjacency list** — a list of neighbors for each node — is the most common:

```python
graph = [
    [1, 2],      # node 0 connects to 1 and 2
    [0, 3],      # node 1 connects to 0 and 3
    [0],         # node 2 connects to 0
    [1],         # node 3 connects to 1
]
```

### Depth-first search (DFS)

Explore as far as possible before backtracking. Use a stack — explicitly or via recursion:

```python
def dfs(graph, start):
    visited = set()
    order = []

    def visit(node):
        if node in visited:
            return
        visited.add(node)
        order.append(node)
        for nxt in graph[node]:
            visit(nxt)

    visit(start)
    return order
```

### Breadth-first search (BFS)

Explore level by level. Use a queue:

```python
from collections import deque

def bfs(graph, start):
    visited = {start}
    order = []
    queue = deque([start])
    while queue:
        node = queue.popleft()
        order.append(node)
        for nxt in graph[node]:
            if nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)
    return order
```

### DFS vs BFS

|              | DFS                          | BFS                          |
|--------------|------------------------------|------------------------------|
| structure    | stack / recursion            | queue                        |
| best for     | path existence, mazes, backtracking | shortest path (unweighted), levels |
| memory       | depth of search              | width of frontier            |
| order        | go deep first                | go wide first                |

### The one thing to remember

**BFS finds the shortest path in an unweighted graph** because it explores all distance-1 nodes before distance-2 nodes. DFS cannot guarantee that.

Both traverse every reachable node in `O(V + E)` — that complexity bound underlies most graph problems.

---

**Next up:** exercises — heap parents, tree levels, and neighbor counts."""
    ),
    L(
        id="dsa-trees-exercise-parent",
        course_id="data-structures-and-algorithms",
        module_id="dsa-trees",
        title="Exercise: Parent in a Heap",
        type="exercise",
        order=5,
        content="""## Exercise: Parent in a Heap

A binary heap stores a tree in a plain array. Node at index `i` has its parent at index `(i - 1) // 2` (for `i > 0`); the root at index `0` has no parent.

Write a function `solve(arr, i)` that returns the **value** of the parent of node at index `i`, or `-1` if the node is the root.

### Worked sample

Input:

```text
[3,9,20,15,7]
2
```

Output:

```text
3
```

The node at index 2 (`20`) has parent at index `(2-1)//2 = 0`, whose value is `3`.

### How your code runs

The runner parses the first line as the heap array and the second as the index, then calls `solve(arr, i)`. Return the parent value as an integer.

### Think

Return `-1` for index `0`. Otherwise compute `parent_index = (i - 1) // 2` and return `arr[parent_index]`.

### Starter code

```python
def solve(arr, i):
    if i <= 0:
        return -1
    return arr[(i - 1) // 2]


def main():
    import sys
    import json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    parts = raw.split("\\n")
    arr = json.loads(parts[0])
    i = json.loads(parts[1])
    print(solve(arr, i))


if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(arr, i):
    if i <= 0:
        return -1
    return arr[(i - 1) // 2]


def main():
    import sys
    import json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    parts = raw.split("\\n")
    arr = json.loads(parts[0])
    i = json.loads(parts[1])
    print(solve(arr, i))


if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": "[3,9,20,15,7]\n2", "expected_output": "3", "description": "Parent of index 2"},
            {"input": "[3,9,20,15,7]\n0", "expected_output": "-1", "description": "Root has no parent"},
            {"input": "[3,9,20]\n1", "expected_output": "3", "description": "Parent of index 1"},
        ],
    ),
    L(
        id="dsa-trees-exercise-levels",
        course_id="data-structures-and-algorithms",
        module_id="dsa-trees",
        title="Exercise: Number of Levels",
        type="exercise",
        order=6,
        content="""## Exercise: Number of Levels

Write a function `solve(arr)` that returns the number of **levels** (height in nodes) in a complete binary tree stored as a flat array.

### Worked sample

Input:

```text
[1,2,3,4,5,6,7]
```

Output:

```text
3
```

An array of 7 elements forms a tree with levels `[1]`, `[2,3]`, `[4,5,6,7]` — three levels total.

### How your code runs

The runner parses the input line as a list and calls `solve(arr)`. Return the number of levels as an integer.

### Think

For `n` nodes, the number of complete levels is `floor(log2(n)) + 1`. With Python's `math` module: `math.log2(n)` for `n >= 1`.

### Starter code

```python
import math


def solve(arr):
    n = len(arr)
    return int(math.log2(n)) + 1


def main():
    import sys
    import json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    arr = json.loads(raw)
    print(solve(arr))


if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''import math


def solve(arr):
    n = len(arr)
    return int(math.log2(n)) + 1


def main():
    import sys
    import json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    arr = json.loads(raw)
    print(solve(arr))


if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": "[1,2,3,4,5,6,7]", "expected_output": "3", "description": "Seven nodes"},
            {"input": "[1]", "expected_output": "1", "description": "Single node"},
            {"input": "[1,2,3]", "expected_output": "2", "description": "Three nodes"},
        ],
    ),
    L(
        id="dsa-trees-exercise-neighbors",
        course_id="data-structures-and-algorithms",
        module_id="dsa-trees",
        title="Exercise: Count Neighbors",
        type="exercise",
        order=7,
        content="""## Exercise: Count Neighbors

Write a function `solve(adj, i)` that returns the number of **neighbors** (degree) of node `i` in an adjacency-list graph.

### Worked sample

Input:

```text
[[1,2],[0,3],[0],[1]]
1
```

Output:

```text
2
```

Node 1 connects to nodes `0` and `3`, so it has degree 2.

### How your code runs

The runner parses the first line as the adjacency list and the second as the node index, then calls `solve(adj, i)`. Return the degree as an integer.

### Think

In an adjacency list, `adj[i]` is already the list of node `i`'s neighbors. Its length is the degree.

### Starter code

```python
def solve(adj, i):
    return len(adj[i])


def main():
    import sys
    import json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    parts = raw.split("\\n")
    adj = json.loads(parts[0])
    i = json.loads(parts[1])
    print(solve(adj, i))


if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(adj, i):
    return len(adj[i])


def main():
    import sys
    import json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    parts = raw.split("\\n")
    adj = json.loads(parts[0])
    i = json.loads(parts[1])
    print(solve(adj, i))


if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": "[[1,2],[0,3],[0],[1]]\n1", "expected_output": "2", "description": "Two neighbors"},
            {"input": "[[1,2],[0,3],[0],[1]]\n3", "expected_output": "1", "description": "Single neighbor"},
            {"input": "[[],[0],[0]]\n0", "expected_output": "0", "description": "Isolated node"},
        ],
    ),
    # ── Module 5: Algorithmic Problem Solving ───────────────────────────
    L(
        id="dsa-problems-method",
        course_id="data-structures-and-algorithms",
        module_id="dsa-problems",
        title="The Problem-Solving Method",
        type="theory",
        order=1,
        content="""## The Problem-Solving Method

Good algorithm design is a **process**, not a flash of inspiration. A structured method turns intimidating problems into a sequence of small, verifiable steps.

### The four-phase loop

1. **Understand** — restate the problem in your own words. What are the inputs, outputs, and edge cases?
2. **Plan** — sketch an approach and its complexity before writing code.
3. **Implement** — write the solution.
4. **Verify** — test on examples, then on edge cases.

### Understand: examples first

Before any code, build a small worked example by hand:

```text
Input:  [3, 1, 4, 1, 5]
Output: ?
```

Hand-computing the answer forces you to pin down the exact rules — most bugs are misunderstanding the spec, not the code.

### Plan: name the technique

Map the problem to a known pattern:

| You see...                          | Pattern          |
|-------------------------------------|------------------|
| pair sums in a sorted array         | two pointers     |
| contiguous subarray sums            | prefix / sliding |
| find in sorted data                 | binary search    |
| shortest path in a graph            | BFS              |
| "can we reach / all paths"          | DFS              |

### Complexity as a filter

Estimate `n` from the constraints, then choose a target:

| n           | allowed complexity |
|-------------|--------------------|
| ≤ 20        | `O(2ⁿ)`, factorial |
| ≤ 10³       | `O(n²)`            |
| ≤ 10⁵       | `O(n log n)`       |
| ≤ 10⁶+      | `O(n)` or better   |

### Verify: edge cases first

Test the embarrassing cases: empty input, one element, duplicates, negatives, and the maximum size. Solutions that pass examples but fail edge cases are the most common failure mode.

### Write it small

Break the solution into functions with one job each. Small functions are easy to test and easy to explain — and explaining is how you confirm you truly understand the algorithm.

---

**Next up:** common patterns that recur across problems."""
    ),
    L(
        id="dsa-problems-patterns",
        course_id="data-structures-and-algorithms",
        module_id="dsa-problems",
        title="Common Patterns",
        type="theory",
        order=2,
        content="""## Common Patterns

A small set of **patterns** solves an enormous fraction of algorithmic problems. Recognizing the pattern is more than half the battle.

### 1. Sliding window

For contiguous subarray problems with a constraint, keep a window and slide it:

```python
def longest_without_repeat(text):
    seen = set()
    left = longest = 0
    for right, ch in enumerate(text):
        while ch in seen:
            seen.remove(text[left])
            left += 1
        seen.add(ch)
        longest = max(longest, right - left + 1)
    return longest
```

### 2. Two pointers

Sorted arrays and "find a pair" problems:

```python
def has_pair_sum(nums, target):
    left, right = 0, len(nums) - 1
    while left < right:
        total = nums[left] + nums[right]
        if total == target:
            return True
        if total < target:
            left += 1
        else:
            right -= 1
    return False
```

### 3. Hash map lookup

Turn "is this present?" from `O(n)` into `O(1)`. The two-sum solution from module 1 is the canonical example: store each value with its index as you go.

### 4. Prefix / accumulate

Range sums, running products, cumulative counts. Precompute once, query in `O(1)`.

### 5. Frequency counting

Count occurrences with a `dict` or `Counter`:

```python
from collections import Counter

counts = Counter("mississippi")
most = counts.most_common(1)
```

### Choosing quickly

1. Contiguous window → sliding window.
2. Pair / triples in sorted data → two pointers.
3. "Has seen before" → hash map.
4. Many range queries → prefix array.
5. Counts and frequencies → Counter.

If none fit, the next lessons introduce greedy and dynamic programming — the two ideas that cover almost everything left.

---

**Next up:** greedy algorithms — making the locally best choice."""
    ),
    L(
        id="dsa-problems-greedy",
        course_id="data-structures-and-algorithms",
        module_id="dsa-problems",
        title="Greedy Algorithms",
        type="theory",
        order=3,
        content="""## Greedy Algorithms

A **greedy** algorithm makes the locally optimal choice at each step, hoping it leads to the globally optimal answer. When it works, it is simple and fast. When it does not, it silently returns a wrong answer.

### The canonical example: best profit

Given daily prices, buy once and sell once later for maximum profit. The greedy insight: track the lowest price seen so far, and at each day compute the profit if you sell today:

```python
def max_profit(prices):
    lowest = prices[0]
    best = 0
    for price in prices[1:]:
        if price < lowest:
            lowest = price
        else:
            best = max(best, price - lowest)
    return best
```

This is `O(n)` — and it is correct because buying at the historical minimum is always optimal for a given sell day.

### When greedy works

Greedy is correct when the problem has **optimal substructure** *and* a **greedy choice property**: the locally best choice is part of some globally best solution. Classic examples:

- Coin change with canonical denominations.
- Interval scheduling (pick the earliest-finishing job).
- Huffman coding.
- Minimum spanning trees (Kruskal, Prim).

### When greedy fails

Consider "find the max sum path in a grid by always moving to the larger neighbor" — a local choice can steer you away from the global optimum. For counterexamples like this, use **dynamic programming** (next lesson).

### How to test a greedy idea

1. Write the greedy rule in one sentence.
2. Build a counterexample by hand — try to construct input where the greedy choice is wrong.
3. If you cannot, implement and verify against brute force on small inputs.

### The mindset

Greedy rewards confidence with simplicity. Ask: *if I make the best immediate choice, can that ever hurt me later?* If the answer is never, greedy is likely your fastest correct solution.

---

**Next up:** dynamic programming — caching overlapping subproblems."""
    ),
    L(
        id="dsa-problems-dp",
        course_id="data-structures-and-algorithms",
        module_id="dsa-problems",
        title="Introduction to Dynamic Programming",
        type="theory",
        order=4,
        content="""## Introduction to Dynamic Programming

**Dynamic programming (DP)** solves problems by combining solutions to **overlapping subproblems** — and caching those solutions so each is computed once. It turns exponential recursion into polynomial time.

### The classic: climbing stairs

To reach step `n`, you can come from step `n-1` (one step) or `n-2` (two steps), so:

```python
def climb(n):
    if n <= 2:
        return n
    a, b = 1, 2
    for _ in range(3, n + 1):
        a, b = b, a + b
    return b
```

The sequence `1, 2, 3, 5, 8, ...` is Fibonacci in disguise.

### The two DP styles

1. **Top-down (memoization):** recursion plus a cache.

```python
def climb(n, memo=None):
    if memo is None:
        memo = {}
    if n in memo:
        return memo[n]
    if n <= 2:
        return n
    memo[n] = climb(n - 1, memo) + climb(n - 2, memo)
    return memo[n]
```

2. **Bottom-up (tabulation):** fill a table from small to large.

```python
def climb(n):
    if n <= 2:
        return n
    dp = [0] * (n + 1)
    dp[1], dp[2] = 1, 2
    for i in range(3, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    return dp[n]
```

### The DP recipe

1. **Define the state** — what does `dp[i]` mean?
2. **Find the recurrence** — how does `dp[i]` relate to smaller states?
3. **Set base cases** — the values you know directly.
4. **Choose the order** — fill bottom-up or memoize top-down.

### When to reach for DP

- The problem asks for *count*, *maximum*, or *minimum*.
- It decomposes into overlapping subproblems (recursion recomputes the same inputs).
- A greedy guess feels risky.

### Complexity

With memoization, each subproblem is solved once: state count × work per state. Climbing stairs is `O(n)` time and `O(1)` (or `O(n)`) space.

---

**Next up:** final exercises — palindrome, climbing stairs, and max profit."""
    ),
    L(
        id="dsa-problems-exercise-palindrome",
        course_id="data-structures-and-algorithms",
        module_id="dsa-problems",
        title="Exercise: Palindrome Check",
        type="exercise",
        order=5,
        content="""## Exercise: Palindrome Check

Write a function `solve(text)` that returns `True` if `text` reads the same forwards and backwards, otherwise `False`. Case and non-letter characters count.

### Worked sample

Input:

```text
racecar
```

Output:

```text
true
```

### How your code runs

The runner passes the raw input text as a single argument to `solve(text)`. Return a boolean — bool outputs serialize as `true`/`false`.

### Think

Compare the string to its reverse: `text == text[::-1]`. The slicing `[::-1]` is a fast, idiomatic reverse.

### Starter code

```python
def solve(text):
    return text == text[::-1]


def main():
    import sys
    raw = sys.stdin.read().strip()
    if not raw:
        return
    result = solve(raw)
    print(str(result).lower())


if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(text):
    return text == text[::-1]


def main():
    import sys
    raw = sys.stdin.read().strip()
    if not raw:
        return
    result = solve(raw)
    print(str(result).lower())


if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": "racecar", "expected_output": "true", "description": "Classic palindrome"},
            {"input": "hello", "expected_output": "false", "description": "Not a palindrome"},
            {"input": "abba", "expected_output": "true", "description": "Even-length palindrome"},
        ],
    ),
    L(
        id="dsa-problems-exercise-stairs",
        course_id="data-structures-and-algorithms",
        module_id="dsa-problems",
        title="Exercise: Climbing Stairs",
        type="exercise",
        order=6,
        content="""## Exercise: Climbing Stairs

Write a function `solve(n)` that returns the number of distinct ways to climb a staircase of `n` steps if you can take **1 or 2 steps** at a time.

### Worked sample

Input:

```text
3
```

Output:

```text
3
```

The ways for 3 steps: `1+1+1`, `1+2`, `2+1` — three total.

### How your code runs

The runner parses the input line as an integer and calls `solve(n)`. Return the count as an integer.

### Think

`ways(n) = ways(n-1) + ways(n-2)` with `ways(1) = 1` and `ways(2) = 2`. Slide two variables forward — no recursion depth worries.

### Starter code

```python
def solve(n):
    if n <= 2:
        return n
    a, b = 1, 2
    for _ in range(3, n + 1):
        a, b = b, a + b
    return b


def main():
    import sys
    raw = sys.stdin.read().strip()
    if not raw:
        return
    n = int(raw)
    print(solve(n))


if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(n):
    if n <= 2:
        return n
    a, b = 1, 2
    for _ in range(3, n + 1):
        a, b = b, a + b
    return b


def main():
    import sys
    raw = sys.stdin.read().strip()
    if not raw:
        return
    n = int(raw)
    print(solve(n))


if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": "2", "expected_output": "2", "description": "Two steps"},
            {"input": "3", "expected_output": "3", "description": "Three steps"},
            {"input": "10", "expected_output": "89", "description": "Ten steps"},
        ],
    ),
    L(
        id="dsa-problems-exercise-max-profit",
        course_id="data-structures-and-algorithms",
        module_id="dsa-problems",
        title="Exercise: Best Time to Buy and Sell",
        type="exercise",
        order=7,
        content="""## Exercise: Best Time to Buy and Sell

Write a function `solve(prices)` that returns the **maximum profit** from buying once and selling once later. If no profit is possible, return `0`.

### Worked sample

Input:

```text
[7,1,5,3,6,4]
```

Output:

```text
5
```

Buy at `1` (day 2) and sell at `6` (day 5) for a profit of `5`.

### How your code runs

The runner parses the input line as a list and calls `solve(prices)`. Return the profit as an integer.

### Think

Track the lowest price seen so far. For each later price, the profit `price - lowest` is the best you could have done by selling today. Keep the maximum.

### Starter code

```python
def solve(prices):
    lowest = prices[0]
    best = 0
    for price in prices[1:]:
        if price < lowest:
            lowest = price
        else:
            best = max(best, price - lowest)
    return best


def main():
    import sys
    import json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    prices = json.loads(raw)
    print(solve(prices))


if __name__ == "__main__":
    main()
```

Good luck!""",
        starter_code='''def solve(prices):
    lowest = prices[0]
    best = 0
    for price in prices[1:]:
        if price < lowest:
            lowest = price
        else:
            best = max(best, price - lowest)
    return best


def main():
    import sys
    import json
    raw = sys.stdin.read().strip()
    if not raw:
        return
    prices = json.loads(raw)
    print(solve(prices))


if __name__ == "__main__":
    main()
''',
        test_cases=[
            {"input": "[7,1,5,3,6,4]", "expected_output": "5", "description": "Classic buy low sell high"},
            {"input": "[7,6,4,3,1]", "expected_output": "0", "description": "Always falling"},
            {"input": "[1,2,3,4,5]", "expected_output": "4", "description": "Always rising"},
        ],
    ),
]
