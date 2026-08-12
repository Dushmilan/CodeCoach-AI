"""Trees & Recursion questions.

Binary tree problems accept a level-order array (None = missing node) as the
serialized form and return level-order arrays or values, keeping test cases
JSON-native.
"""

from __future__ import annotations

from typing import Any, List, Optional

from ._helpers import is_same_tree, make_spec, tree_from_level, tree_to_level

SPECS = [
    make_spec(
        id="invert-binary-tree",
        title="Invert Binary Tree",
        difficulty="easy",
        category="Trees & Recursion",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="Given the root of a binary tree, invert the tree, and return its root.\n\nIn this environment the tree is given as a level-order array `root` (None means missing node); return the level-order array of the inverted tree.\n\n**Constraints**\n- The number of nodes in the tree is in the range [0, 100].\n- -100 <= Node.val <= 100",
        examples=[
            {
                "input": "root = [4,2,7,1,3,6,9]",
                "output": "[4,7,2,9,6,3,1]",
                "explanation": "Every node's left and right children are swapped.",
            },
            {
                "input": "root = [2,1,3]",
                "output": "[2,3,1]",
                "explanation": "Swap the two children.",
            },
            {"input": "root = []", "output": "[]", "explanation": "Empty tree."},
        ],
        tests=[
            (([4, 2, 7, 1, 3, 6, 9],), False),
            (([2, 1, 3],), False),
            (([],), False),
            (([1],), False),
            (([1, 2],), False),
            (([1, None, 2],), False),
            (([1, 2, 3, 4, 5, 6, 7],), False),
            (([3, 1, 2],), True),
            (([4, 2, 7, 1, 3, 6, 9],), True),
        ],
        ref=lambda *args: _invert_tree(*args),
        starter={
            "python": "def invertTree(root: List[Any]) -> List[Any]:\n    pass",
            "javascript": "function invertTree(root) {\n    // your code here\n}",
            "java": "class Solution {\n    public List<Object> invertTree(List<Object> root) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Swap the left and right children of every node.",
            "A simple recursion works: invert both subtrees first, then swap.",
        ],
        solution="Build the tree from the level-order array, then recursively swap left and right subtrees at every node. Serialize the inverted tree back to level order.",
        time_complexity="O(n)",
        space_complexity="O(h)",
        constraints=["The number of nodes is in the range [0, 100]"],
    ),
    make_spec(
        id="maximum-depth-of-binary-tree",
        title="Maximum Depth of Binary Tree",
        difficulty="easy",
        category="Trees & Recursion",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="Given the root of a binary tree, return its maximum depth.\n\nA binary tree's maximum depth is the number of nodes along the longest path from the root node down to the farthest leaf node.\n\nIn this environment the tree is given as a level-order array `root`; return the maximum depth.\n\n**Constraints**\n- The number of nodes in the tree is in the range [0, 10^4].\n- -100 <= Node.val <= 100",
        examples=[
            {
                "input": "root = [3,9,20,None,None,15,7]",
                "output": "3",
                "explanation": "The longest path has 3 nodes.",
            },
            {
                "input": "root = [1,None,2]",
                "output": "2",
                "explanation": "Path 1 -> 2.",
            },
        ],
        tests=[
            (([3, 9, 20, None, None, 15, 7],), False),
            (([1, None, 2],), False),
            (([],), False),
            (([1],), False),
            (([1, 2, 3, 4, 5],), False),
            (([1, 2, None, 3],), False),
            (([1, 2, 3, 4, None, None, 7],), False),
            (([1, 2, 3, 4, 5, 6, 7, 8],), True),
            (([1, None, 2, None, 3],), True),
        ],
        ref=lambda *args: _max_depth(*args),
        starter={
            "python": "def maxDepth(root: List[Any]) -> int:\n    pass",
            "javascript": "function maxDepth(root) {\n    // your code here\n}",
            "java": "class Solution {\n    public int maxDepth(List<Object> root) {\n        // your code here\n    }\n}",
        },
        hints=[
            "The depth of a node is 1 + max(depth of left, depth of right).",
            "Base case: an empty subtree has depth 0.",
        ],
        solution="Build the tree, then recursively compute depth as 1 + max(depth(left), depth(right)), with empty subtrees contributing 0.",
        time_complexity="O(n)",
        space_complexity="O(h)",
        constraints=["The number of nodes is in the range [0, 10^4]"],
    ),
    make_spec(
        id="same-tree",
        title="Same Tree",
        difficulty="easy",
        category="Trees & Recursion",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="Given the roots of two binary trees `p` and `q`, write a function to check if they are the same or not.\n\nTwo binary trees are considered the same if they are structurally identical, and the nodes have the same value.\n\nIn this environment each tree is given as a level-order array; return `true` if they are the same.\n\n**Constraints**\n- The number of nodes in both trees is in the range [0, 100].\n- -10^4 <= Node.val <= 10^4",
        examples=[
            {
                "input": "p = [1,2,3], q = [1,2,3]",
                "output": "true",
                "explanation": "Identical structure and values.",
            },
            {
                "input": "p = [1,2], q = [1,None,2]",
                "output": "false",
                "explanation": "Different structure.",
            },
            {
                "input": "p = [1,2,1], q = [1,1,2]",
                "output": "false",
                "explanation": "Different values.",
            },
        ],
        tests=[
            (([1, 2, 3], [1, 2, 3]), False),
            (([1, 2], [1, None, 2]), False),
            (([1, 2, 1], [1, 1, 2]), False),
            (([], []), False),
            (([1], [1]), False),
            (([1], []), False),
            (([], [1]), False),
            (([1, 2, 3], [1, 2, 3]), False),
            (([1, None, 2], [1, None, 2]), True),
            (([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]), True),
            (([1, 2], [1, 2]), True),
        ],
        ref=lambda p, q: _same_tree(p, q),
        starter={
            "python": "def isSameTree(p: List[Any], q: List[Any]) -> bool:\n    pass",
            "javascript": "function isSameTree(p, q) {\n    // your code here\n}",
            "java": "class Solution {\n    public boolean isSameTree(List<Object> p, List<Object> q) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Both nodes empty means equal; exactly one empty means unequal.",
            "Compare values then recurse on both children.",
        ],
        solution="Build both trees and compare recursively: two nodes are the same if both are None, or both have equal values and their left/right subtrees are the same.",
        time_complexity="O(min(m, n))",
        space_complexity="O(min(h1, h2))",
        constraints=["The number of nodes is in the range [0, 100]"],
    ),
    make_spec(
        id="balanced-binary-tree",
        title="Balanced Binary Tree",
        difficulty="easy",
        category="Trees & Recursion",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="Given a binary tree, determine if it is height-balanced.\n\nA height-balanced binary tree is a binary tree in which the depth of the two subtrees of every node never differs by more than one.\n\nThe tree is given as a level-order array `root`; return `true` if it is balanced.\n\n**Constraints**\n- The number of nodes in the tree is in the range [0, 5000].\n- -10^4 <= Node.val <= 10^4",
        examples=[
            {
                "input": "root = [3,9,20,None,None,15,7]",
                "output": "true",
                "explanation": "Every subtree differs by at most 1 in depth.",
            },
            {
                "input": "root = [1,2,2,3,3,None,None,4,4]",
                "output": "false",
                "explanation": "The left subtree has depth 4 while the right has depth 1.",
            },
        ],
        tests=[
            (([3, 9, 20, None, None, 15, 7],), False),
            (([1, 2, 2, 3, 3, None, None, 4, 4],), False),
            (([],), False),
            (([1],), False),
            (([1, 2, 2, 3, None, None, 3, 4, None, None, 4],), False),
            (([1, 2, None, 3],), False),
            (([1, 2, 3, 4, 5, 6, None, 8],), False),
            (([1, 2, 3],), True),
            (([1, 2, 2, 3, 3, 3, 3],), True),
            (([1, None, 2, None, 3],), True),
        ],
        ref=lambda *args: _is_balanced(*args),
        starter={
            "python": "def isBalanced(root: List[Any]) -> bool:\n    pass",
            "javascript": "function isBalanced(root) {\n    // your code here\n}",
            "java": "class Solution {\n    public boolean isBalanced(List<Object> root) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Compute the depth of each subtree while checking the balance condition.",
            "Return -1 as a sentinel from an unbalanced subtree.",
        ],
        solution="Build the tree and use a helper that returns the depth, or -1 if the subtree is unbalanced. If either child returns -1 or the difference exceeds 1, propagate -1. The tree is balanced if the helper returns a non-negative value for the root.",
        time_complexity="O(n)",
        space_complexity="O(h)",
        constraints=["The number of nodes is in the range [0, 5000]"],
    ),
    make_spec(
        id="binary-tree-level-order-traversal",
        title="Binary Tree Level Order Traversal",
        difficulty="medium",
        category="Trees & Recursion",
        companies=["Amazon", "Google", "Microsoft", "Facebook", "Apple"],
        description="Given the root of a binary tree, return the level order traversal of its nodes' values (i.e., from left to right, level by level).\n\nThe tree is given as a level-order array `root`; return a list of lists, one inner list per level.\n\n**Constraints**\n- The number of nodes in the tree is in the range [0, 2000].\n- -1000 <= Node.val <= 1000",
        examples=[
            {
                "input": "root = [3,9,20,None,None,15,7]",
                "output": "[[3],[9,20],[15,7]]",
                "explanation": "Values grouped by level.",
            },
            {"input": "root = [1]", "output": "[[1]]", "explanation": "Single level."},
            {"input": "root = []", "output": "[]", "explanation": "Empty tree."},
        ],
        tests=[
            (([3, 9, 20, None, None, 15, 7],), False),
            (([1],), False),
            (([],), False),
            (([1, 2, 3, 4, 5, 6, 7],), False),
            (([1, 2, None, 3],), False),
            (([1, None, 2, None, 3],), False),
            (([1, 2, 3, 4, None, None, 5],), True),
            (([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],), True),
        ],
        ref=lambda *args: _level_order(*args),
        starter={
            "python": "def levelOrder(root: List[Any]) -> List[List[int]]:\n    pass",
            "javascript": "function levelOrder(root) {\n    // your code here\n}",
            "java": "class Solution {\n    public List<List<Integer>> levelOrder(List<Object> root) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Use a queue and process one whole level at a time.",
            "Record the queue size before processing a level.",
        ],
        solution="Build the tree, then BFS with a queue: for each level, capture the current queue length, pop that many nodes collecting their values, and enqueue their children.",
        time_complexity="O(n)",
        space_complexity="O(n)",
        constraints=["The number of nodes is in the range [0, 2000]"],
    ),
    make_spec(
        id="validate-binary-search-tree",
        title="Validate Binary Search Tree",
        difficulty="medium",
        category="Trees & Recursion",
        companies=["Amazon", "Google", "Microsoft", "Facebook", "Apple"],
        description="Given the root of a binary tree, determine if it is a valid binary search tree (BST).\n\nA valid BST is defined as follows:\n- The left subtree of a node contains only nodes with keys less than the node's key.\n- The right subtree of a node contains only nodes with keys greater than the node's key.\n- Both the left and right subtrees must also be binary search trees.\n\nThe tree is given as a level-order array `root`; return `true` if it is a valid BST.\n\n**Constraints**\n- The number of nodes in the tree is in the range [1, 10^4].\n- -2^31 <= Node.val <= 2^31 - 1",
        examples=[
            {"input": "root = [2,1,3]", "output": "true", "explanation": "1 < 2 < 3."},
            {
                "input": "root = [5,1,4,None,None,3,6]",
                "output": "false",
                "explanation": "3 is in the right subtree of 5 but is less than 5.",
            },
        ],
        tests=[
            (([2, 1, 3],), False),
            (([5, 1, 4, None, None, 3, 6],), False),
            (([1],), False),
            (([2, 2, 2],), False),
            (([5, 4, 6, None, None, 3, 7],), False),
            (([5, 3, 8, 2, 4, 6, 10],), False),
            (([1, 2],), False),
            (([0, -1],), False),
            (([2, 1, 3],), True),
            (([5, 3, 8, 2, 4, 6, 10],), True),
            (([2147483647],), True),
        ],
        ref=lambda *args: _is_valid_bst(*args),
        starter={
            "python": "def isValidBST(root: List[Any]) -> bool:\n    pass",
            "javascript": "function isValidBST(root) {\n    // your code here\n}",
            "java": "class Solution {\n    public boolean isValidBST(List<Object> root) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Pass down a valid lower and upper bound to each node.",
            "The left child must stay below the current upper bound; the right above the lower bound.",
        ],
        solution="Build the tree and validate recursively with (low, high) bounds. A node is valid if low < node.val < high; recurse left with (low, node.val) and right with (node.val, high).",
        time_complexity="O(n)",
        space_complexity="O(h)",
        constraints=["The number of nodes is in the range [1, 10^4]"],
    ),
    make_spec(
        id="lowest-common-ancestor-of-a-binary-tree",
        title="Lowest Common Ancestor of a Binary Tree",
        difficulty="medium",
        category="Trees & Recursion",
        companies=["Amazon", "Google", "Microsoft", "Facebook", "Apple"],
        description="Given a binary tree, find the lowest common ancestor (LCA) of two given nodes in the tree.\n\nThe lowest common ancestor is defined between two nodes p and q as the lowest node in T that has both p and q as descendants (where we allow a node to be a descendant of itself).\n\nThe tree is given as a level-order array `root` with node values, and `p` and `q` are node values that are guaranteed to exist; return the LCA node's value.\n\n**Constraints**\n- The number of nodes in the tree is in the range [2, 10^5].\n- All Node.val are unique.",
        examples=[
            {
                "input": "root = [3,5,1,6,2,0,8,None,None,7,4], p = 5, q = 1",
                "output": "3",
                "explanation": "The LCA of 5 and 1 is 3.",
            },
            {
                "input": "root = [3,5,1,6,2,0,8,None,None,7,4], p = 5, q = 4",
                "output": "5",
                "explanation": "A node can be an ancestor of itself.",
            },
        ],
        tests=[
            (([3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 5, 1), False),
            (([3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 5, 4), False),
            (([1, 2], 1, 2), False),
            (([1, 2, 3], 2, 3), False),
            (([6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 2, 8), False),
            (([6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 4, 5), False),
            (([6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 2, 4), True),
            (([3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 6, 4), True),
            (([1, 2, 3, 4, 5], 4, 5), True),
            (([1, 2, 3], 2, 2), True),
        ],
        ref=lambda root, p, q: _lca(root, p, q),
        starter={
            "python": "def lowestCommonAncestor(root: List[Any], p: int, q: int) -> int:\n    pass",
            "javascript": "function lowestCommonAncestor(root, p, q) {\n    // your code here\n}",
            "java": "class Solution {\n    public int lowestCommonAncestor(List<Object> root, int p, int q) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Recursion can find either p or q in a subtree.",
            "If both children report a found node, the current node is the LCA.",
        ],
        solution="Build the tree, then recurse: if the current node equals p or q, return it. Gather the results of the left and right searches; if both are found, the current node is the LCA. Otherwise propagate the non-None result.",
        time_complexity="O(n)",
        space_complexity="O(h)",
        constraints=["The number of nodes is in the range [2, 10^5]"],
    ),
    make_spec(
        id="kth-smallest-element-in-a-bst",
        title="Kth Smallest Element in a BST",
        difficulty="medium",
        category="Trees & Recursion",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="Given the root of a binary search tree, and an integer `k`, return the k-th smallest value (1-indexed) of all the values of the nodes in the tree.\n\nThe tree is given as a level-order array `root`; return the k-th smallest value.\n\n**Constraints**\n- The number of nodes in the tree is n.\n- 1 <= k <= n <= 10^4\n- 0 <= Node.val <= 10^4",
        examples=[
            {
                "input": "root = [3,1,4,None,2], k = 1",
                "output": "1",
                "explanation": "In-order traversal gives [1,2,3,4]; the 1st is 1.",
            },
            {
                "input": "root = [5,3,6,2,4,None,None,1], k = 3",
                "output": "3",
                "explanation": "In-order traversal gives [1,2,3,4,5,6]; the 3rd is 3.",
            },
        ],
        tests=[
            (([3, 1, 4, None, 2], 1), False),
            (([5, 3, 6, 2, 4, None, None, 1], 3), False),
            (([2, 1], 1), False),
            (([2, 1], 2), False),
            (([1], 1), False),
            (([4, 2, 6, 1, 3, 5, 7], 4), False),
            (([4, 2, 6, 1, 3, 5, 7], 7), False),
            (([4, 2, 6, 1, 3, 5, 7], 1), True),
            (([10, 5, 15, 1, 8, 12, 20], 3), True),
        ],
        ref=lambda root, k: _kth_smallest(root, k),
        starter={
            "python": "def kthSmallest(root: List[Any], k: int) -> int:\n    pass",
            "javascript": "function kthSmallest(root, k) {\n    // your code here\n}",
            "java": "class Solution {\n    public int kthSmallest(List<Object> root, int k) {\n        // your code here\n    }\n}",
        },
        hints=[
            "In-order traversal of a BST visits nodes in ascending order.",
            "Stop early once you have visited k nodes.",
        ],
        solution="Build the tree and perform an in-order traversal, decrementing k and returning the value when k reaches 0.",
        time_complexity="O(h + k)",
        space_complexity="O(h)",
        constraints=["1 <= k <= n <= 10^4"],
    ),
    make_spec(
        id="binary-tree-maximum-path-sum",
        title="Binary Tree Maximum Path Sum",
        difficulty="hard",
        category="Trees & Recursion",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="A path in a binary tree is a sequence of nodes where each pair of adjacent nodes in the sequence has an edge connecting them. A node can only appear in the sequence at most once. Note that the path does not need to pass through the root.\n\nThe path sum of a path is the sum of the node's values in the path.\n\nGiven the root of a binary tree, return the maximum path sum.\n\nThe tree is given as a level-order array `root`; return the maximum path sum.\n\n**Constraints**\n- The number of nodes in the tree is in the range [1, 3 * 10^4].\n- -1000 <= Node.val <= 1000",
        examples=[
            {
                "input": "root = [1,2,3]",
                "output": "6",
                "explanation": "The path 2 -> 1 -> 3 has sum 6.",
            },
            {
                "input": "root = [-10,9,20,None,None,15,7]",
                "output": "42",
                "explanation": "The optimal path is 15 -> 20 -> 7 with sum 42.",
            },
        ],
        tests=[
            (([1, 2, 3],), False),
            (([-10, 9, 20, None, None, 15, 7],), False),
            (([-3],), False),
            (([2, -1],), False),
            (([1, 2, 3, 4, 5, 6, 7],), False),
            (([-1, -2, -3],), False),
            (([1, -2, 3, 4, 5],), False),
            (([-5, 10, -4, None, None, 5, 1],), True),
            (([9, 6, -3, None, None, -6, 2, None, None, 2, None, -6, -6, -6],), True),
            (([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, 1],), True),
        ],
        ref=lambda *args: _max_path_sum(*args),
        starter={
            "python": "def maxPathSum(root: List[Any]) -> int:\n    pass",
            "javascript": "function maxPathSum(root) {\n    // your code here\n}",
            "java": "class Solution {\n    public int maxPathSum(List<Object> root) {\n        // your code here\n    }\n}",
        },
        hints=[
            "For each node, the best path through it is node.val + bestLeft + bestRight.",
            "The subtree contribution passed upward is node.val + max(bestLeft, bestRight).",
            "Negative contributions can be ignored by clamping at 0.",
        ],
        solution="Post-order traversal: each node returns the max sum of a single downward path starting at it, while a global variable tracks the max path sum that may pass through any node combining both children.",
        time_complexity="O(n)",
        space_complexity="O(h)",
        constraints=["The number of nodes is in the range [1, 3 * 10^4]"],
    ),
]


def _invert_tree(root: List[Any]) -> List[Any]:
    def invert(node):
        if node is None:
            return None
        node.left, node.right = invert(node.right), invert(node.left)
        return node

    return tree_to_level(invert(tree_from_level(root)))


def _max_depth(root: List[Any]) -> int:
    def depth(node):
        if node is None:
            return 0
        return 1 + max(depth(node.left), depth(node.right))

    return depth(tree_from_level(root))


def _same_tree(p: List[Any], q: List[Any]) -> bool:
    return is_same_tree(tree_from_level(p), tree_from_level(q))


def _is_balanced(root: List[Any]) -> bool:
    def check(node) -> int:
        if node is None:
            return 0
        left = check(node.left)
        if left == -1:
            return -1
        right = check(node.right)
        if right == -1:
            return -1
        if abs(left - right) > 1:
            return -1
        return 1 + max(left, right)

    return check(tree_from_level(root)) != -1


def _level_order(root: List[Any]) -> List[List[int]]:
    from collections import deque

    node = tree_from_level(root)
    if node is None:
        return []
    res: List[List[int]] = []
    q = deque([node])
    while q:
        level = []
        for _ in range(len(q)):
            cur = q.popleft()
            level.append(cur.val)
            if cur.left:
                q.append(cur.left)
            if cur.right:
                q.append(cur.right)
        res.append(level)
    return res


def _is_valid_bst(root: List[Any]) -> bool:
    def validate(node, low, high):
        if node is None:
            return True
        if not (low < node.val < high):
            return False
        return validate(node.left, low, node.val) and validate(
            node.right, node.val, high
        )

    return validate(tree_from_level(root), float("-inf"), float("inf"))


def _lca(root: List[Any], p: int, q: int) -> int:
    def search(node) -> Optional[int]:
        if node is None:
            return None
        if node.val in (p, q):
            return node.val
        left = search(node.left)
        right = search(node.right)
        if left is not None and right is not None:
            return node.val
        return left if left is not None else right

    return search(tree_from_level(root)) or p


def _kth_smallest(root: List[Any], k: int) -> int:
    node = tree_from_level(root)
    stack: List[Any] = []
    count = 0
    cur = node
    while stack or cur is not None:
        while cur is not None:
            stack.append(cur)
            cur = cur.left
        cur = stack.pop()
        count += 1
        if count == k:
            return cur.val
        cur = cur.right
    return -1


def _max_path_sum(root: List[Any]) -> int:
    node = tree_from_level(root)
    best = float("-inf")

    def dfs(n):
        nonlocal best
        if n is None:
            return 0
        left = max(dfs(n.left), 0)
        right = max(dfs(n.right), 0)
        best = max(best, n.val + left + right)
        return n.val + max(left, right)

    dfs(node)
    return int(best)
