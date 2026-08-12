"""Linked List questions.

Linked-list problems accept an array of node values as the serialized form and
return the resulting array, so they work with JSON-native test cases.
"""

from __future__ import annotations

from typing import List

from ._helpers import list_from_values, make_spec, values_from_list

SPECS = [
    make_spec(
        id="reverse-linked-list",
        title="Reverse Linked List",
        difficulty="easy",
        category="Linked Lists",
        companies=["Amazon", "Microsoft", "Google", "Facebook", "Apple"],
        description="Given the head of a singly linked list, reverse the list and return its head.\n\nIn this environment the linked list is given as an array of node values `head`; return the array of values of the reversed list.\n\n**Constraints**\n- The number of nodes in the list is in the range [0, 5000].\n- -5000 <= Node.val <= 5000",
        examples=[
            {
                "input": "head = [1,2,3,4,5]",
                "output": "[5,4,3,2,1]",
                "explanation": "The list is reversed.",
            },
            {
                "input": "head = [1,2]",
                "output": "[2,1]",
                "explanation": "Two nodes swap order.",
            },
            {"input": "head = []", "output": "[]", "explanation": "Empty list."},
        ],
        tests=[
            (([1, 2, 3, 4, 5],), False),
            (([1, 2],), False),
            (([],), False),
            (([1],), False),
            (([1, 2, 3],), False),
            (([5, 4, 3, 2, 1],), False),
            (([10, 20, 30, 40],), True),
            (([7],), True),
        ],
        ref=lambda *args: _reverse_list(*args),
        starter={
            "python": "def reverseList(head: List[int]) -> List[int]:\n    pass",
            "javascript": "function reverseList(head) {\n    // your code here\n}",
            "java": "class Solution {\n    public int[] reverseList(int[] head) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Iterate with prev, curr, and next pointers.",
            "Alternatively, recursion reverses the rest first then fixes the head.",
        ],
        solution="Build a linked list from the input values, then reverse it iteratively by relinking next pointers. Serialize the result back to an array of values.",
        time_complexity="O(n)",
        space_complexity="O(1)",
        constraints=["The number of nodes is in the range [0, 5000]"],
    ),
    make_spec(
        id="merge-two-sorted-lists",
        title="Merge Two Sorted Lists",
        difficulty="easy",
        category="Linked Lists",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="You are given the heads of two sorted linked lists `list1` and `list2`.\n\nMerge the two lists into one sorted list by splicing together the nodes of the first two lists.\n\nIn this environment the lists are given as arrays of node values `list1` and `list2`; return the array of the merged sorted list.\n\n**Constraints**\n- The number of nodes in both lists is in the range [0, 50].\n- -100 <= Node.val <= 100\n- Both lists are sorted in non-decreasing order.",
        examples=[
            {
                "input": "list1 = [1,2,4], list2 = [1,3,4]",
                "output": "[1,1,2,3,4,4]",
                "explanation": "The merged sorted list.",
            },
            {
                "input": "list1 = [], list2 = []",
                "output": "[]",
                "explanation": "Both empty.",
            },
            {
                "input": "list1 = [], list2 = [0]",
                "output": "[0]",
                "explanation": "Merging empty with [0].",
            },
        ],
        tests=[
            (([1, 2, 4], [1, 3, 4]), False),
            (([], []), False),
            (([], [0]), False),
            (([1, 2, 3], []), False),
            (([5], [1, 2, 6]), False),
            (([1, 1, 1], [2, 2]), False),
            (([-3, 0, 5], [-1, 4]), False),
            (([2], [1, 3, 4]), True),
            (([1, 3, 5], [2, 4, 6]), True),
            (([1], [1]), True),
        ],
        ref=lambda l1, l2: _merge_two(l1, l2),
        starter={
            "python": "def mergeTwoLists(list1: List[int], list2: List[int]) -> List[int]:\n    pass",
            "javascript": "function mergeTwoLists(list1, list2) {\n    // your code here\n}",
            "java": "class Solution {\n    public int[] mergeTwoLists(int[] list1, int[] list2) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Use a dummy head to simplify the merge.",
            "Advance the pointer of whichever list has the smaller value.",
        ],
        solution="Merge with two pointers over the built lists, always attaching the smaller current node. Use a dummy node to start. Serialize the merged list back to an array.",
        time_complexity="O(m + n)",
        space_complexity="O(1)",
        constraints=["The number of nodes is in the range [0, 50]"],
    ),
    make_spec(
        id="linked-list-cycle",
        title="Linked List Cycle",
        difficulty="easy",
        category="Linked Lists",
        companies=["Amazon", "Microsoft", "Google", "Facebook"],
        description="Given `head`, the head of a linked list, determine if the linked list has a cycle in it.\n\nA cycle exists if a node can be reached again by continuously following the next pointer.\n\nThe list is given as an array of node values `head`, together with an integer `pos` representing the 0-indexed node where the tail connects (or `-1` if there is no cycle). Return `true` if the list has a cycle, `false` otherwise.\n\n**Constraints**\n- The number of nodes is in the range [0, 10^4].\n- -10^5 <= Node.val <= 10^5\n- pos is -1 or a valid index in the list.",
        examples=[
            {
                "input": "head = [3,2,0,-4], pos = 1",
                "output": "true",
                "explanation": "The tail connects to index 1, forming a cycle.",
            },
            {
                "input": "head = [1,2], pos = 0",
                "output": "true",
                "explanation": "The tail connects to index 0.",
            },
            {
                "input": "head = [1], pos = -1",
                "output": "false",
                "explanation": "No cycle.",
            },
        ],
        tests=[
            (([3, 2, 0, -4], 1), False),
            (([1, 2], 0), False),
            (([1], -1), False),
            (([], -1), False),
            (([1, 2, 3], -1), False),
            (([1, 2, 3, 4, 5], 2), False),
            (([1], 0), True),
            (([1, 2, 3, 4], 3), True),
            (([-21, 10, 17, 8, 4, 26, 5, 35, 33, -7], -1), True),
            (([1, 2, 3, 4, 5, 6], 0), True),
        ],
        ref=lambda head, pos: _has_cycle(head, pos),
        starter={
            "python": "def hasCycle(head: List[int], pos: int) -> bool:\n    pass",
            "javascript": "function hasCycle(head, pos) {\n    // your code here\n}",
            "java": "class Solution {\n    public boolean hasCycle(int[] head, int pos) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Floyd's tortoise and hare: slow moves 1 step, fast moves 2.",
            "If the two pointers ever meet, a cycle exists.",
        ],
        solution="Build the linked list and optionally connect the tail to the node at pos. Run two pointers, slow and fast. If fast reaches the end, return false; if they meet, return true.",
        time_complexity="O(n)",
        space_complexity="O(1)",
        constraints=["The number of nodes is in the range [0, 10^4]"],
    ),
    make_spec(
        id="remove-nth-node-from-end-of-list",
        title="Remove Nth Node From End of List",
        difficulty="medium",
        category="Linked Lists",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="Given the head of a linked list, remove the n-th node from the end of the list and return its head.\n\nThe list is given as an array of node values `head` together with an integer `n`; return the array of values after removal.\n\n**Constraints**\n- The number of nodes in the list is sz.\n- 1 <= sz <= 30\n- 0 <= Node.val <= 100\n- 1 <= n <= sz",
        examples=[
            {
                "input": "head = [1,2,3,4,5], n = 2",
                "output": "[1,2,3,5]",
                "explanation": "The 2nd node from the end is 4.",
            },
            {
                "input": "head = [1], n = 1",
                "output": "[]",
                "explanation": "Removing the only node leaves an empty list.",
            },
            {
                "input": "head = [1,2], n = 1",
                "output": "[1]",
                "explanation": "Remove the last node.",
            },
        ],
        tests=[
            (([1, 2, 3, 4, 5], 2), False),
            (([1], 1), False),
            (([1, 2], 1), False),
            (([1, 2], 2), False),
            (([1, 2, 3], 3), False),
            (([1, 2, 3, 4], 2), False),
            (([5, 6, 7, 8], 4), False),
            (([1, 2, 3, 4, 5], 5), True),
            (([10, 20, 30], 1), True),
            (([1, 2, 3, 4, 5, 6], 3), True),
        ],
        ref=lambda head, n: _remove_nth(head, n),
        starter={
            "python": "def removeNthFromEnd(head: List[int], n: int) -> List[int]:\n    pass",
            "javascript": "function removeNthFromEnd(head, n) {\n    // your code here\n}",
            "java": "class Solution {\n    public int[] removeNthFromEnd(int[] head, int n) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Advance a fast pointer n steps first, then move both pointers together.",
            "The slow pointer will land just before the target node.",
        ],
        solution="Build the list. Use a dummy node and two pointers: advance fast by n, then advance both until fast reaches the end. The slow pointer points at the node before the one to remove; relink to skip it. Serialize the result.",
        time_complexity="O(n)",
        space_complexity="O(1)",
        constraints=["1 <= n <= sz"],
    ),
    make_spec(
        id="reorder-list",
        title="Reorder List",
        difficulty="medium",
        category="Linked Lists",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="You are given the head of a singly linked-list. The list can be represented as `L0 -> L1 -> ... -> Ln-1 -> Ln`.\n\nReorder the list to `L0 -> Ln -> L1 -> Ln-1 -> L2 -> Ln-2 -> ...`.\n\nThe list is given as an array of node values `head`; return the array of values of the reordered list.\n\n**Constraints**\n- The number of nodes in the list is in the range [1, 5 * 10^4].\n- 1 <= Node.val <= 1000",
        examples=[
            {
                "input": "head = [1,2,3,4]",
                "output": "[1,4,2,3]",
                "explanation": "L0->L3->L1->L2.",
            },
            {
                "input": "head = [1,2,3,4,5]",
                "output": "[1,5,2,4,3]",
                "explanation": "L0->L4->L1->L3->L2.",
            },
        ],
        tests=[
            (([1, 2, 3, 4],), False),
            (([1, 2, 3, 4, 5],), False),
            (([1],), False),
            (([1, 2],), False),
            (([1, 2, 3],), False),
            (([1, 2, 3, 4, 5, 6],), False),
            (([1, 2, 3, 4, 5, 6, 7, 8],), False),
            (([1, 2, 3, 4, 5, 6, 7],), True),
            (([10, 20, 30, 40, 50, 60],), True),
        ],
        ref=lambda *args: _reorder(*args),
        starter={
            "python": "def reorderList(head: List[int]) -> List[int]:\n    pass",
            "javascript": "function reorderList(head) {\n    // your code here\n}",
            "java": "class Solution {\n    public int[] reorderList(int[] head) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Find the middle, split the list, and reverse the second half.",
            "Then interleave the two halves.",
        ],
        solution="Find the midpoint with slow/fast pointers, split into two lists, reverse the second half, then merge by alternating a node from each half. Serialize back to an array.",
        time_complexity="O(n)",
        space_complexity="O(1)",
        constraints=["The number of nodes is in the range [1, 5 * 10^4]"],
    ),
    make_spec(
        id="add-two-numbers",
        title="Add Two Numbers",
        difficulty="medium",
        category="Linked Lists",
        companies=["Amazon", "Google", "Microsoft", "Facebook", "Apple"],
        description="You are given two non-empty linked lists representing two non-negative integers. The digits are stored in reverse order, and each of their nodes contains a single digit. Add the two numbers and return the sum as a linked list.\n\nIn this environment the numbers are given as arrays of digits `l1` and `l2`; return the array of the sum's digits in reverse order.\n\n**Constraints**\n- The number of nodes in each linked list is in the range [1, 100].\n- 0 <= Node.val <= 9\n- The numbers do not contain any leading zero except the number 0 itself.",
        examples=[
            {
                "input": "l1 = [2,4,3], l2 = [5,6,4]",
                "output": "[7,0,8]",
                "explanation": "342 + 465 = 807, stored reversed as [7,0,8].",
            },
            {
                "input": "l1 = [0], l2 = [0]",
                "output": "[0]",
                "explanation": "0 + 0 = 0.",
            },
            {
                "input": "l1 = [9,9,9,9,9,9,9], l2 = [9,9,9,9]",
                "output": "[8,9,9,9,0,0,0,1]",
                "explanation": "9999999 + 9999 = 10009998, stored reversed.",
            },
        ],
        tests=[
            (([2, 4, 3], [5, 6, 4]), False),
            (([0], [0]), False),
            (([9, 9, 9, 9, 9, 9, 9], [9, 9, 9, 9]), False),
            (([1], [1]), False),
            (([9], [1]), False),
            (([9, 9], [1]), False),
            (([5], [5]), False),
            (([1, 2, 3], [4, 5, 6]), False),
            (([9, 9, 9], [1, 1, 1, 1]), True),
            (([1, 8], [0]), True),
            (([2, 4, 3], [5, 6, 4]), True),
        ],
        ref=lambda l1, l2: _add_two(l1, l2),
        starter={
            "python": "def addTwoNumbers(l1: List[int], l2: List[int]) -> List[int]:\n    pass",
            "javascript": "function addTwoNumbers(l1, l2) {\n    // your code here\n}",
            "java": "class Solution {\n    public int[] addTwoNumbers(int[] l1, int[] l2) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Add digit by digit from the head with a carry.",
            "Keep adding until both lists are exhausted and the carry is 0.",
        ],
        solution="Iterate over both lists while either has nodes or a carry remains. Sum the digits plus the carry, create a node with sum % 10, and carry = sum // 10. Serialize the result digits.",
        time_complexity="O(max(m, n))",
        space_complexity="O(max(m, n))",
        constraints=["The numbers do not contain leading zeros except zero itself"],
    ),
    make_spec(
        id="merge-k-sorted-lists",
        title="Merge k Sorted Lists",
        difficulty="hard",
        category="Linked Lists",
        companies=["Amazon", "Google", "Microsoft", "Facebook"],
        description="You are given an array of `k` linked-lists `lists`, each linked-list is sorted in ascending order.\n\nMerge all the linked-lists into one sorted linked-list and return its head.\n\nIn this environment the lists are given as an array of arrays `lists`; return the merged sorted array.\n\n**Constraints**\n- k == lists.length\n- 0 <= k <= 10^4\n- 0 <= lists[i].length <= 500\n- -10^4 <= lists[i][j] <= 10^4",
        examples=[
            {
                "input": "lists = [[1,4,5],[1,3,4],[2,6]]",
                "output": "[1,1,2,3,4,4,5,6]",
                "explanation": "The merged sorted list.",
            },
            {"input": "lists = []", "output": "[]", "explanation": "No lists."},
            {"input": "lists = [[]]", "output": "[]", "explanation": "One empty list."},
        ],
        tests=[
            (([[1, 4, 5], [1, 3, 4], [2, 6]],), False),
            (([],), False),
            (([[]],), False),
            (([[1], [2], [3]],), False),
            (([[1, 2, 3], [], [4, 5]],), False),
            (([[1, 2], [1, 2], [1, 2]],), False),
            (([[10], [1, 5], [3, 7, 9]],), False),
            (([[1, 2, 3, 4, 5], [0, 6, 7], [8]],), True),
            (([[-5, -1], [-3, 0], [-2, 4]],), True),
            (([[1]],), True),
        ],
        ref=lambda *args: _merge_k(*args),
        starter={
            "python": "def mergeKLists(lists: List[List[int]]) -> List[int]:\n    pass",
            "javascript": "function mergeKLists(lists) {\n    // your code here\n}",
            "java": "class Solution {\n    public int[] mergeKLists(int[][] lists) {\n        // your code here\n    }\n}",
        },
        hints=[
            "Use a min-heap of (value, list_index) to always pop the smallest head.",
            "Alternatively, merge two lists at a time with a divide-and-conquer approach.",
        ],
        solution="Build each list, then merge them with a min-heap that always yields the current smallest node. Pop, append, and advance the corresponding list until all nodes are consumed. Serialize the merged list.",
        time_complexity="O(n log k)",
        space_complexity="O(k)",
        constraints=["k == lists.length", "0 <= k <= 10^4"],
    ),
]


def _reverse_list(head: List[int]) -> List[int]:
    node = list_from_values(head)
    prev = None
    while node is not None:
        nxt = node.next
        node.next = prev
        prev = node
        node = nxt
    return values_from_list(prev)


def _merge_two(l1: List[int], l2: List[int]) -> List[int]:
    a, b = list_from_values(l1), list_from_values(l2)
    dummy = list_from_values([0])
    tail = dummy
    while a is not None and b is not None:
        if a.val <= b.val:
            tail.next = a
            a = a.next
        else:
            tail.next = b
            b = b.next
        tail = tail.next
    tail.next = a if a is not None else b
    return values_from_list(dummy.next)


def _has_cycle(head: List[int], pos: int) -> bool:
    if not head:
        return False
    node = list_from_values(head)
    cycle_node = None
    if pos >= 0 and pos < len(head):
        cycle_node = node
        for _ in range(pos):
            cycle_node = cycle_node.next
    # connect tail to cycle_node
    cur = node
    while cur.next is not None:
        cur = cur.next
    if cycle_node is not None:
        cur.next = cycle_node
    slow = fast = node
    while fast is not None and fast.next is not None:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            return True
    return False


def _remove_nth(head: List[int], n: int) -> List[int]:
    node = list_from_values(head)
    dummy = list_from_values([0])
    dummy.next = node
    fast = dummy
    for _ in range(n):
        fast = fast.next
    slow = dummy
    while fast.next is not None:
        fast = fast.next
        slow = slow.next
    slow.next = slow.next.next
    return values_from_list(dummy.next)


def _reorder(head: List[int]) -> List[int]:
    if not head:
        return []
    node = list_from_values(head)
    # find middle
    slow = fast = node
    while fast.next is not None and fast.next.next is not None:
        slow = slow.next
        fast = fast.next.next
    second = slow.next
    slow.next = None
    # reverse second half
    prev = None
    while second is not None:
        nxt = second.next
        second.next = prev
        prev = second
        second = nxt
    second = prev
    # interleave
    first = node
    while second is not None:
        tmp1, tmp2 = first.next, second.next
        first.next = second
        second.next = tmp1
        first = tmp1
        second = tmp2
    return values_from_list(node)


def _add_two(l1: List[int], l2: List[int]) -> List[int]:
    i = j = carry = 0
    res = []
    while i < len(l1) or j < len(l2) or carry:
        s = carry
        if i < len(l1):
            s += l1[i]
            i += 1
        if j < len(l2):
            s += l2[j]
            j += 1
        res.append(s % 10)
        carry = s // 10
    return res


def _merge_k(lists: List[List[int]]) -> List[int]:
    import heapq

    heap = []
    for li, lst in enumerate(lists):
        if lst:
            heapq.heappush(heap, (lst[0], li, 0))
    res = []
    while heap:
        val, li, idx = heapq.heappop(heap)
        res.append(val)
        if idx + 1 < len(lists[li]):
            heapq.heappush(heap, (lists[li][idx + 1], li, idx + 1))
    return res
