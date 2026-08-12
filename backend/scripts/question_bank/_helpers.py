"""Shared helpers for question reference solutions.

Tree and linked-list problems use array-based I/O (level-order / value lists)
so test cases stay JSON-native and work with the suite runners.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .build_bank import QuestionSpec


class ListNode:
    def __init__(self, val: int = 0, next: Optional["ListNode"] = None):
        self.val = val
        self.next = next


class TreeNode:
    def __init__(
        self,
        val: int = 0,
        left: Optional["TreeNode"] = None,
        right: Optional["TreeNode"] = None,
    ):
        self.val = val
        self.left = left
        self.right = right


def list_from_values(values: List[int]) -> Optional[ListNode]:
    if not values:
        return None
    head = ListNode(values[0])
    cur = head
    for v in values[1:]:
        cur.next = ListNode(v)
        cur = cur.next
    return head


def values_from_list(head: Optional[ListNode]) -> List[int]:
    out = []
    while head is not None:
        out.append(head.val)
        head = head.next
    return out


def tree_from_level(values: List[Any]) -> Optional[TreeNode]:
    """Build a binary tree from a level-order array (None = missing node)."""
    if not values or values[0] is None:
        return None
    root = TreeNode(values[0])
    queue: List[Optional[TreeNode]] = [root]
    idx = 1
    while queue and idx < len(values):
        node = queue.pop(0)
        if node is None:
            continue
        if idx < len(values):
            if values[idx] is not None:
                node.left = TreeNode(values[idx])
                queue.append(node.left)
            idx += 1
        if idx < len(values):
            if values[idx] is not None:
                node.right = TreeNode(values[idx])
                queue.append(node.right)
            idx += 1
    return root


def tree_to_level(root: Optional[TreeNode]) -> List[Any]:
    """Serialize a binary tree to a level-order array (None = missing node)."""
    if root is None:
        return []
    out: List[Any] = []
    queue: List[Optional[TreeNode]] = [root]
    while any(queue):
        node = queue.pop(0)
        if node is None:
            out.append(None)
            continue
        out.append(node.val)
        queue.append(node.left)
        queue.append(node.right)
    while out and out[-1] is None:
        out.pop()
    return out


def is_same_tree(p: Optional[TreeNode], q: Optional[TreeNode]) -> bool:
    if p is None or q is None:
        return p is q
    return (
        p.val == q.val
        and is_same_tree(p.left, q.left)
        and is_same_tree(p.right, q.right)
    )


def make_spec(**kwargs: Any) -> QuestionSpec:
    """Build a QuestionSpec from keyword arguments (compact authoring)."""
    defaults: Dict[str, Any] = {
        "examples": [],
        "tests": [],
        "hints": [],
        "solution": "",
        "time_complexity": "",
        "space_complexity": "",
        "constraints": [],
        "in_place": False,
    }
    merged = {**defaults, **kwargs}
    return QuestionSpec(**merged)
