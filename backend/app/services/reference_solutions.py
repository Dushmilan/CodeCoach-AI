"""Curated catalog of canonical optimal solutions.

Each entry is the *optimal* solution for a well-known algorithm, written
against the __trace API so executing it produces the semantic event stream
that drives the universal animation renderer. Every canonical solution emits
its own ``init`` event (deep-copying the structure so the compiler shows the
original input), then describes the algorithm with semantic events; the
visuals are owned by the family compilers, never by the model.

Each entry:
- family: array | backtrack | stack | linked_list | tree | grid | graph | intervals
- function: the callable name
- signature: parameter names in order (the input normalizer maps positional
  inputs onto the first parameter)
- primary: the parameter whose value is the main visual structure (metadata)
- match_keys: keyword fallback matching for questions without an exact id
- code: the traced canonical solution

The mapping from the 100 DB questions to these algorithms lives in
``question_catalog.py`` (exact question-id keys take precedence).
"""

FAMILIES = frozenset(
    {"array", "backtrack", "stack", "linked_list", "tree", "grid", "graph", "intervals"}
)

from typing import Optional  # noqa: E402  (module-level helpers below)

REFERENCE_SOLUTIONS: dict = {
    # ── arrays: sorting & search ─────────────────────────────────────────────
    "bubble_sort": {
        "family": "array",
        "title": "Bubble Sort",
        "function": "bubble_sort",
        "signature": ["values"],
        "primary": "values",
        "match_keys": ["bubble sort", "bubble_sort"],
        "code": """\
def bubble_sort(values):
    __trace("init", values=__json.loads(__json.dumps(list(values))), family="array")
    n = len(values)
    for i in range(n - 1):
        for j in range(n - i - 1):
            __trace("pointer", name="j", index=j)
            __trace("compare", i=j, j=j + 1)
            if values[j] > values[j + 1]:
                values[j], values[j + 1] = values[j + 1], values[j]
                __trace("swap", i=j, j=j + 1)
        __trace("mark", i=n - i - 1, state="sorted")
    return values
""",
    },
    "linear_search": {
        "family": "array",
        "title": "Linear Search",
        "function": "linear_search",
        "signature": ["values", "target"],
        "primary": "values",
        "match_keys": ["linear search", "linear_scan"],
        "code": """\
def linear_search(values, target):
    __trace("init", values=__json.loads(__json.dumps(list(values))), family="array")
    for i, v in enumerate(values):
        __trace("pointer", name="i", index=i)
        __trace("compare", i=i)
        if v == target:
            __trace("mark", i=i, state="match")
            return i
    return -1
""",
    },
    "binary_search": {
        "family": "array",
        "title": "Binary Search",
        "function": "binary_search",
        "signature": ["nums", "target"],
        "primary": "nums",
        "match_keys": ["binary search", "binary_search"],
        "code": """\
def binary_search(nums, target):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="array")
    low, high = 0, len(nums) - 1
    while low <= high:
        mid = (low + high) // 2
        __trace("pointer", name="low", index=low)
        __trace("pointer", name="high", index=high)
        __trace("pointer", name="mid", index=mid)
        __trace("compare", i=mid)
        if nums[mid] == target:
            __trace("mark", i=mid, state="match")
            return mid
        elif nums[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1
""",
    },
    # ── arrays: hashing & counts ────────────────────────────────────────────
    "two_sum": {
        "family": "array",
        "title": "Two Sum",
        "function": "two_sum",
        "signature": ["nums", "target"],
        "primary": "nums",
        "match_keys": ["two sum", "two_sum"],
        "code": """\
def two_sum(nums, target):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="array")
    seen = {}
    for i, n in enumerate(nums):
        __trace("pointer", name="i", index=i)
        __trace("compare", i=i)
        diff = target - n
        if diff in seen:
            __trace("mark", i=i, state="match")
            return [seen[diff], i]
        seen[n] = i
    return []
""",
    },
    "contains_duplicate": {
        "family": "array",
        "title": "Contains Duplicate",
        "function": "contains_duplicate",
        "signature": ["nums"],
        "primary": "nums",
        "match_keys": ["contains duplicate", "any value appears at least twice"],
        "code": """\
def contains_duplicate(nums):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="array")
    seen = set()
    for i, n in enumerate(nums):
        __trace("pointer", name="i", index=i)
        __trace("read", i=i)
        if n in seen:
            __trace("mark", i=i, state="match")
            return True
        seen.add(n)
    return False
""",
    },
    "majority_element": {
        "family": "array",
        "title": "Majority Element",
        "function": "majority_element",
        "signature": ["nums"],
        "primary": "nums",
        "match_keys": ["majority element", "appears more than n"],
        "code": """\
def majority_element(nums):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="array")
    candidate = None
    count = 0
    for i, n in enumerate(nums):
        __trace("pointer", name="i", index=i)
        __trace("read", i=i)
        if count == 0:
            candidate = n
            __trace("mark", i=i, state="active")
        count += 1 if n == candidate else -1
    return candidate
""",
    },
    "single_number": {
        "family": "array",
        "title": "Single Number",
        "function": "single_number",
        "signature": ["nums"],
        "primary": "nums",
        "match_keys": ["single number", "every element appears twice"],
        "code": """\
def single_number(nums):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="array")
    acc = 0
    for i, n in enumerate(nums):
        __trace("pointer", name="i", index=i)
        __trace("read", i=i)
        acc ^= n
    return acc
""",
    },
    "missing_number": {
        "family": "array",
        "title": "Missing Number",
        "function": "missing_number",
        "signature": ["nums"],
        "primary": "nums",
        "match_keys": ["missing number", "only number in the range"],
        "code": """\
def missing_number(nums):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="array")
    acc = len(nums)
    for i, v in enumerate(nums):
        __trace("pointer", name="i", index=i)
        __trace("read", i=i)
        acc ^= i ^ v
    return acc
""",
    },
    "find_the_duplicate_number": {
        "family": "array",
        "title": "Find the Duplicate Number",
        "function": "find_the_duplicate_number",
        "signature": ["nums"],
        "primary": "nums",
        "match_keys": ["duplicate number"],
        "code": """\
def find_the_duplicate_number(nums):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="array")
    slow = fast = nums[0]
    while True:
        slow = nums[slow]
        fast = nums[nums[fast]]
        if slow == fast:
            break
    __trace("pointer", name="slow", index=slow)
    __trace("visit", i=slow)
    slow = nums[0]
    while slow != fast:
        __trace("pointer", name="slow", index=slow)
        __trace("pointer", name="fast", index=fast)
        slow = nums[slow]
        fast = nums[fast]
    __trace("mark", i=slow, state="match")
    return slow
""",
    },
    "find_all_duplicates": {
        "family": "array",
        "title": "Find All Duplicates in an Array",
        "function": "find_all_duplicates",
        "signature": ["nums"],
        "primary": "nums",
        "match_keys": ["all duplicates", "each integer appears once or twice"],
        "code": """\
def find_all_duplicates(nums):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="array")
    result = []
    for i, n in enumerate(nums):
        __trace("pointer", name="i", index=i)
        idx = abs(n) - 1
        if nums[idx] < 0:
            __trace("mark", i=i, state="match")
            result.append(abs(n))
        else:
            nums[idx] = -nums[idx]
            __trace("visit", i=i)
    return result
""",
    },
    "first_missing_positive": {
        "family": "array",
        "title": "First Missing Positive",
        "function": "first_missing_positive",
        "signature": ["nums"],
        "primary": "nums",
        "match_keys": ["first missing positive", "smallest positive integer"],
        "code": """\
def first_missing_positive(nums):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="array")
    n = len(nums)
    for i in range(n):
        __trace("pointer", name="i", index=i)
        while 1 <= nums[i] <= n and nums[nums[i] - 1] != nums[i]:
            idx = nums[i] - 1
            nums[i], nums[idx] = nums[idx], nums[i]
            __trace("swap", i=i, j=idx)
    for i in range(n):
        __trace("pointer", name="i", index=i)
        if nums[i] != i + 1:
            __trace("mark", i=i, state="match")
            return i + 1
    return n + 1
""",
    },
    "longest_consecutive_sequence": {
        "family": "array",
        "title": "Longest Consecutive Sequence",
        "function": "longest_consecutive_sequence",
        "signature": ["nums"],
        "primary": "nums",
        "match_keys": ["longest consecutive"],
        "code": """\
def longest_consecutive_sequence(nums):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="array")
    values = set(nums)
    best = 0
    for i, n in enumerate(nums):
        __trace("pointer", name="i", index=i)
        if n - 1 not in values:
            length = 1
            while n + length in values:
                __trace("visit", i=i)
                length += 1
            best = max(best, length)
            __trace("mark", i=i, state="match")
    return best
""",
    },
    "valid_anagram": {
        "family": "array",
        "title": "Valid Anagram",
        "function": "valid_anagram",
        "signature": ["s", "t"],
        "primary": "s",
        "match_keys": ["valid anagram", "anagram"],
        "code": """\
def valid_anagram(s, t):
    __trace("init", values=__json.loads(__json.dumps(list(s))), family="array")
    if len(s) != len(t):
        return False
    from collections import Counter
    cs = Counter(s)
    for i, ch in enumerate(t):
        __trace("pointer", name="i", index=i)
        cs[ch] -= 1
        if cs[ch] < 0:
            return False
        __trace("mark", i=i, state="match")
    return not any(cs.values())
""",
    },
    "group_anagrams": {
        "family": "array",
        "title": "Group Anagrams",
        "function": "group_anagrams",
        "signature": ["strs"],
        "primary": "strs",
        "match_keys": ["group anagrams"],
        "code": """\
def group_anagrams(strs):
    __trace("init", values=__json.loads(__json.dumps(list(strs))), family="array")
    groups = {}
    for i, w in enumerate(strs):
        __trace("pointer", name="i", index=i)
        key = "".join(sorted(w))
        groups.setdefault(key, []).append(w)
        __trace("mark", i=i, state="active")
    return list(groups.values())
""",
    },
    "top_k_frequent": {
        "family": "array",
        "title": "Top K Frequent Elements",
        "function": "top_k_frequent",
        "signature": ["nums", "k"],
        "primary": "nums",
        "match_keys": ["top k frequent"],
        "code": """\
def top_k_frequent(nums, k):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="array")
    from collections import Counter
    counts = Counter(nums)
    top = sorted(counts.items(), key=lambda kv: -kv[1])[:k]
    top_keys = {kv[0] for kv in top}
    for i, n in enumerate(nums):
        __trace("pointer", name="i", index=i)
        if n in top_keys:
            __trace("mark", i=i, state="match")
    return [kv[0] for kv in top]
""",
    },
    "product_of_array_except_self": {
        "family": "array",
        "title": "Product of Array Except Self",
        "function": "product_of_array_except_self",
        "signature": ["nums"],
        "primary": "nums",
        "match_keys": [
            "product of array except self",
            "product of all the elements of",
        ],
        "code": """\
def product_of_array_except_self(nums):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="array")
    n = len(nums)
    res = [1] * n
    prefix = 1
    for i in range(n):
        __trace("pointer", name="i", index=i)
        res[i] = prefix
        prefix *= nums[i]
        __trace("write", i=i, value=res[i])
    suffix = 1
    for i in range(n - 1, -1, -1):
        __trace("pointer", name="i", index=i)
        res[i] *= suffix
        suffix *= nums[i]
        __trace("write", i=i, value=res[i])
    return res
""",
    },
    "subarray_sum_equals_k": {
        "family": "array",
        "title": "Subarray Sum Equals K",
        "function": "subarray_sum_equals_k",
        "signature": ["nums", "k"],
        "primary": "nums",
        "match_keys": ["subarray sum equals k"],
        "code": """\
def subarray_sum_equals_k(nums, k):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="array")
    prefix = 0
    seen = {0: 1}
    count = 0
    for i, n in enumerate(nums):
        __trace("pointer", name="i", index=i)
        __trace("read", i=i)
        prefix += n
        if prefix - k in seen:
            __trace("mark", i=i, state="match")
            count += seen[prefix - k]
        seen[prefix] = seen.get(prefix, 0) + 1
    return count
""",
    },
    "contiguous_array": {
        "family": "array",
        "title": "Contiguous Array",
        "function": "contiguous_array",
        "signature": ["nums"],
        "primary": "nums",
        "match_keys": ["contiguous array", "maximum length of a contiguous subarray"],
        "code": """\
def contiguous_array(nums):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="array")
    seen = {0: -1}
    acc = 0
    best = 0
    for i, n in enumerate(nums):
        __trace("pointer", name="i", index=i)
        __trace("read", i=i)
        acc += 1 if n == 1 else -1
        if acc in seen:
            best = max(best, i - seen[acc])
            __trace("mark", i=i, state="match")
        else:
            seen[acc] = i
    return best
""",
    },
    "next_permutation": {
        "family": "array",
        "title": "Next Permutation",
        "function": "next_permutation",
        "signature": ["nums"],
        "primary": "nums",
        "match_keys": ["next permutation"],
        "code": """\
def next_permutation(nums):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="array")
    n = len(nums)
    i = n - 2
    while i >= 0 and nums[i] >= nums[i + 1]:
        i -= 1
    if i >= 0:
        j = n - 1
        while nums[j] <= nums[i]:
            j -= 1
        __trace("pointer", name="pivot", index=i)
        __trace("swap", i=i, j=j)
        nums[i], nums[j] = nums[j], nums[i]
    l, r = i + 1, n - 1
    while l < r:
        __trace("pointer", name="l", index=l)
        __trace("pointer", name="r", index=r)
        __trace("swap", i=l, j=r)
        nums[l], nums[r] = nums[r], nums[l]
        l += 1
        r -= 1
    return nums
""",
    },
    # ── arrays: two pointers ────────────────────────────────────────────────
    "reverse_string": {
        "family": "array",
        "title": "Reverse String",
        "function": "reverse_string",
        "signature": ["s"],
        "primary": "s",
        "match_keys": ["reverse string", "reverse_string"],
        "code": """\
def reverse_string(s):
    __trace("init", values=__json.loads(__json.dumps(list(s))), family="array")
    left, right = 0, len(s) - 1
    while left < right:
        __trace("pointer", name="left", index=left)
        __trace("pointer", name="right", index=right)
        __trace("swap", i=left, j=right)
        s[left], s[right] = s[right], s[left]
        left += 1
        right -= 1
    return s
""",
    },
    "move_zeroes": {
        "family": "array",
        "title": "Move Zeroes",
        "function": "move_zeroes",
        "signature": ["nums"],
        "primary": "nums",
        "match_keys": ["move zeroes", "move all 0"],
        "code": """\
def move_zeroes(nums):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="array")
    slow = 0
    for fast in range(len(nums)):
        __trace("pointer", name="fast", index=fast)
        __trace("visit", i=fast)
        if nums[fast] != 0:
            if slow != fast:
                __trace("swap", i=slow, j=fast)
                nums[slow], nums[fast] = nums[fast], nums[slow]
            slow += 1
    return nums
""",
    },
    "valid_palindrome": {
        "family": "array",
        "title": "Valid Palindrome",
        "function": "valid_palindrome",
        "signature": ["s"],
        "primary": "s",
        "match_keys": ["valid palindrome", "palindrome phrase"],
        "code": """\
def valid_palindrome(s):
    __trace("init", values=__json.loads(__json.dumps(list(s))), family="array")
    l, r = 0, len(s) - 1
    while l < r:
        __trace("pointer", name="left", index=l)
        __trace("pointer", name="right", index=r)
        while l < r and not s[l].isalnum():
            l += 1
        while l < r and not s[r].isalnum():
            r -= 1
        if l >= r:
            break
        __trace("compare", i=l, j=r)
        if s[l].lower() != s[r].lower():
            return False
        l += 1
        r -= 1
    return True
""",
    },
    "is_subsequence": {
        "family": "array",
        "title": "Is Subsequence",
        "function": "is_subsequence",
        "signature": ["s", "t"],
        "primary": "t",
        "match_keys": ["is subsequence", "subsequence of"],
        "code": """\
def is_subsequence(s, t):
    __trace("init", values=__json.loads(__json.dumps(list(t))), family="array")
    i = 0
    for j, ch in enumerate(t):
        __trace("pointer", name="j", index=j)
        if i < len(s) and ch == s[i]:
            __trace("mark", i=j, state="match")
            i += 1
    return i == len(s)
""",
    },
    "two_sum_ii": {
        "family": "array",
        "title": "Two Sum II — Input Array Is Sorted",
        "function": "two_sum_ii",
        "signature": ["numbers", "target"],
        "primary": "numbers",
        "match_keys": ["two sum ii", "input array is sorted"],
        "code": """\
def two_sum_ii(numbers, target):
    __trace("init", values=__json.loads(__json.dumps(list(numbers))), family="array")
    l, r = 0, len(numbers) - 1
    while l < r:
        __trace("pointer", name="l", index=l)
        __trace("pointer", name="r", index=r)
        __trace("compare", i=l, j=r)
        s = numbers[l] + numbers[r]
        if s == target:
            __trace("mark", i=l, state="match")
            __trace("mark", i=r, state="match")
            return [l + 1, r + 1]
        elif s < target:
            l += 1
        else:
            r -= 1
    return []
""",
    },
    "three_sum": {
        "family": "array",
        "title": "3Sum",
        "function": "three_sum",
        "signature": ["nums"],
        "primary": "nums",
        "match_keys": ["three sum", "3sum", "unique triplets"],
        "code": """\
def three_sum(nums):
    vals = sorted(nums)
    __trace("init", values=__json.loads(__json.dumps(vals)), family="array")
    result = []
    n = len(vals)
    for i in range(n - 2):
        __trace("pointer", name="i", index=i)
        if i > 0 and vals[i] == vals[i - 1]:
            continue
        l, r = i + 1, n - 1
        while l < r:
            __trace("pointer", name="l", index=l)
            __trace("pointer", name="r", index=r)
            s = vals[i] + vals[l] + vals[r]
            if s == 0:
                result.append([vals[i], vals[l], vals[r]])
                __trace("compare", i=l, j=r)
                __trace("mark", i=l, state="match")
                __trace("mark", i=r, state="match")
                while l < r and vals[l] == vals[l + 1]:
                    l += 1
                while l < r and vals[r] == vals[r - 1]:
                    r -= 1
                l += 1
                r -= 1
            elif s < 0:
                l += 1
            else:
                r -= 1
    return result
""",
    },
    "three_sum_closest": {
        "family": "array",
        "title": "3Sum Closest",
        "function": "three_sum_closest",
        "signature": ["nums", "target"],
        "primary": "nums",
        "match_keys": ["three sum closest", "3sum closest"],
        "code": """\
def three_sum_closest(nums, target):
    vals = sorted(nums)
    __trace("init", values=__json.loads(__json.dumps(vals)), family="array")
    best = sum(vals[:3])
    for i in range(len(vals) - 2):
        __trace("pointer", name="i", index=i)
        l, r = i + 1, len(vals) - 1
        while l < r:
            __trace("pointer", name="l", index=l)
            __trace("pointer", name="r", index=r)
            __trace("compare", i=l, j=r)
            s = vals[i] + vals[l] + vals[r]
            if s == target:
                return s
            if abs(s - target) < abs(best - target):
                best = s
            if s < target:
                l += 1
            else:
                r -= 1
    return best
""",
    },
    "container_with_most_water": {
        "family": "array",
        "title": "Container With Most Water",
        "function": "container_with_most_water",
        "signature": ["height"],
        "primary": "height",
        "match_keys": ["container with most water"],
        "code": """\
def container_with_most_water(height):
    __trace("init", values=__json.loads(__json.dumps(list(height))), family="array")
    l, r = 0, len(height) - 1
    best = 0
    while l < r:
        __trace("pointer", name="left", index=l)
        __trace("pointer", name="right", index=r)
        __trace("compare", i=l, j=r)
        best = max(best, min(height[l], height[r]) * (r - l))
        if height[l] < height[r]:
            l += 1
        else:
            r -= 1
    return best
""",
    },
    "trapping_rain_water": {
        "family": "array",
        "title": "Trapping Rain Water",
        "function": "trapping_rain_water",
        "signature": ["height"],
        "primary": "height",
        "match_keys": ["trapping rain water", "trap after rain"],
        "code": """\
def trapping_rain_water(height):
    __trace("init", values=__json.loads(__json.dumps(list(height))), family="array")
    l, r = 0, len(height) - 1
    lm = rm = 0
    water = 0
    while l < r:
        __trace("pointer", name="left", index=l)
        __trace("pointer", name="right", index=r)
        __trace("compare", i=l, j=r)
        if height[l] < height[r]:
            if height[l] >= lm:
                lm = height[l]
            else:
                water += lm - height[l]
                __trace("mark", i=l, state="active")
            l += 1
        else:
            if height[r] >= rm:
                rm = height[r]
            else:
                water += rm - height[r]
                __trace("mark", i=r, state="active")
            r -= 1
    return water
""",
    },
    "partition_labels": {
        "family": "array",
        "title": "Partition Labels",
        "function": "partition_labels",
        "signature": ["s"],
        "primary": "s",
        "match_keys": ["partition labels", "partition the string"],
        "code": """\
def partition_labels(s):
    __trace("init", values=__json.loads(__json.dumps(list(s))), family="array")
    last = {ch: i for i, ch in enumerate(s)}
    left = 0
    right = 0
    sizes = []
    for i, ch in enumerate(s):
        __trace("pointer", name="i", index=i)
        right = max(right, last[ch])
        if i == right:
            __trace("mark", i=i, state="match")
            sizes.append(i - left + 1)
            left = i + 1
    return sizes
""",
    },
    # ── arrays: sliding window ──────────────────────────────────────────────
    "longest_substring_without_repeating": {
        "family": "array",
        "title": "Longest Substring Without Repeating Characters",
        "function": "longest_substring_without_repeating",
        "signature": ["s"],
        "primary": "s",
        "match_keys": ["longest substring without repeating"],
        "code": """\
def longest_substring_without_repeating(s):
    __trace("init", values=__json.loads(__json.dumps(list(s))), family="array")
    seen = {}
    left = 0
    best = 0
    for right, ch in enumerate(s):
        if ch in seen and seen[ch] >= left:
            left = seen[ch] + 1
        seen[ch] = right
        __trace("window", l=left, r=right)
        __trace("pointer", name="r", index=right)
        best = max(best, right - left + 1)
    return best
""",
    },
    "permutation_in_string": {
        "family": "array",
        "title": "Permutation in String",
        "function": "permutation_in_string",
        "signature": ["s1", "s2"],
        "primary": "s2",
        "match_keys": ["permutation in string"],
        "code": """\
def permutation_in_string(s1, s2):
    __trace("init", values=__json.loads(__json.dumps(list(s2))), family="array")
    n1 = len(s1)
    if n1 > len(s2):
        return False
    from collections import Counter
    need = Counter(s1)
    have = Counter()
    left = 0
    for right, ch in enumerate(s2):
        have[ch] += 1
        if right - left + 1 > n1:
            have[s2[left]] -= 1
            left += 1
        __trace("window", l=left, r=right)
        __trace("pointer", name="r", index=right)
        if right - left + 1 == n1 and have == need:
            __trace("mark", i=left, state="match")
            return True
    return False
""",
    },
    "longest_repeating_character_replacement": {
        "family": "array",
        "title": "Longest Repeating Character Replacement",
        "function": "longest_repeating_character_replacement",
        "signature": ["s", "k"],
        "primary": "s",
        "match_keys": ["longest repeating character replacement"],
        "code": """\
def longest_repeating_character_replacement(s, k):
    __trace("init", values=__json.loads(__json.dumps(list(s))), family="array")
    from collections import Counter
    counts = Counter()
    left = 0
    best = 0
    maxf = 0
    for right, ch in enumerate(s):
        counts[ch] += 1
        maxf = max(maxf, counts[ch])
        if right - left + 1 - maxf > k:
            counts[s[left]] -= 1
            left += 1
        __trace("window", l=left, r=right)
        __trace("pointer", name="r", index=right)
        best = max(best, right - left + 1)
    return best
""",
    },
    "minimum_window_substring": {
        "family": "array",
        "title": "Minimum Window Substring",
        "function": "minimum_window_substring",
        "signature": ["s", "t"],
        "primary": "s",
        "match_keys": ["minimum window substring"],
        "code": """\
def minimum_window_substring(s, t):
    __trace("init", values=__json.loads(__json.dumps(list(s))), family="array")
    from collections import Counter
    need = Counter(t)
    have = {}
    missing = len(need)
    left = 0
    best = None
    for right, ch in enumerate(s):
        __trace("pointer", name="r", index=right)
        if ch in need:
            have[ch] = have.get(ch, 0) + 1
            if have[ch] == need[ch]:
                missing -= 1
        while missing == 0:
            if best is None or right - left + 1 < best[1]:
                best = (left, right - left + 1)
            lc = s[left]
            if lc in need:
                have[lc] -= 1
                if have[lc] < need[lc]:
                    missing += 1
            left += 1
        __trace("window", l=left, r=right)
        if best:
            __trace("mark", i=best[0], state="match")
    return s[best[0]:best[0] + best[1]] if best else ""
""",
    },
    "sliding_window_maximum": {
        "family": "array",
        "title": "Sliding Window Maximum",
        "function": "sliding_window_maximum",
        "signature": ["nums", "k"],
        "primary": "nums",
        "match_keys": ["sliding window maximum"],
        "code": """\
def sliding_window_maximum(nums, k):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="array")
    from collections import deque
    dq = deque()
    result = []
    for i, n in enumerate(nums):
        __trace("pointer", name="i", index=i)
        while dq and nums[dq[-1]] <= n:
            dq.pop()
        dq.append(i)
        if dq[0] <= i - k:
            dq.popleft()
        __trace("window", l=max(0, i - k + 1), r=i)
        if i >= k - 1:
            __trace("mark", i=dq[0], state="match")
            result.append(nums[dq[0]])
    return result
""",
    },
    "best_time_to_buy_and_sell": {
        "family": "array",
        "title": "Best Time to Buy and Sell Stock",
        "function": "best_time_to_buy_and_sell",
        "signature": ["prices"],
        "primary": "prices",
        "match_keys": ["buy and sell stock", "maximize your profit"],
        "code": """\
def best_time_to_buy_and_sell(prices):
    __trace("init", values=__json.loads(__json.dumps(list(prices))), family="array")
    buy = prices[0]
    profit = 0
    for i in range(1, len(prices)):
        __trace("pointer", name="i", index=i)
        __trace("read", i=i)
        if prices[i] < buy:
            buy = prices[i]
            __trace("mark", i=i, state="active")
        else:
            profit = max(profit, prices[i] - buy)
            __trace("mark", i=i, state="match")
    return profit
""",
    },
    # ── arrays: greedy ──────────────────────────────────────────────────────
    "jump_game": {
        "family": "array",
        "title": "Jump Game",
        "function": "jump_game",
        "signature": ["nums"],
        "primary": "nums",
        "match_keys": ["jump game"],
        "code": """\
def jump_game(nums):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="array")
    reach = 0
    for i, n in enumerate(nums):
        __trace("pointer", name="i", index=i)
        __trace("read", i=i)
        if i > reach:
            return False
        reach = max(reach, i + n)
        __trace("mark", i=i, state="active")
    return True
""",
    },
    "jump_game_ii": {
        "family": "array",
        "title": "Jump Game II",
        "function": "jump_game_ii",
        "signature": ["nums"],
        "primary": "nums",
        "match_keys": ["jump game ii"],
        "code": """\
def jump_game_ii(nums):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="array")
    jumps = 0
    cur_end = 0
    farthest = 0
    for i in range(len(nums) - 1):
        __trace("pointer", name="i", index=i)
        __trace("read", i=i)
        farthest = max(farthest, i + nums[i])
        if i == cur_end:
            jumps += 1
            cur_end = farthest
            __trace("mark", i=i, state="active")
    return jumps
""",
    },
    "gas_station": {
        "family": "array",
        "title": "Gas Station",
        "function": "gas_station",
        "signature": ["gas", "cost"],
        "primary": "gas",
        "match_keys": ["gas station"],
        "code": """\
def gas_station(gas, cost):
    __trace("init", values=__json.loads(__json.dumps(list(gas))), family="array")
    total = 0
    current = 0
    start = 0
    for i in range(len(gas)):
        __trace("pointer", name="i", index=i)
        __trace("read", i=i)
        total += gas[i] - cost[i]
        current += gas[i] - cost[i]
        if current < 0:
            current = 0
            start = i + 1
            __trace("mark", i=i, state="active")
    return start if total >= 0 else -1
""",
    },
    "hand_of_straights": {
        "family": "array",
        "title": "Hand of Straights",
        "function": "hand_of_straights",
        "signature": ["hand", "groupSize"],
        "primary": "hand",
        "match_keys": ["hand of straights", "rearrange the cards"],
        "code": """\
def hand_of_straights(hand, groupSize):
    __trace("init", values=__json.loads(__json.dumps(list(hand))), family="array")
    if len(hand) % groupSize:
        return False
    from collections import Counter
    counts = Counter(hand)
    idx = {v: i for i, v in enumerate(hand)}
    for card in sorted(counts):
        while counts[card] > 0:
            __trace("pointer", name="card", index=idx.get(card, 0))
            for off in range(groupSize):
                if counts[card + off] <= 0:
                    return False
                counts[card + off] -= 1
                __trace("mark", i=idx.get(card + off, 0), state="active")
    return True
""",
    },
    "car_fleet": {
        "family": "array",
        "title": "Car Fleet",
        "function": "car_fleet",
        "signature": ["target", "position", "speed"],
        "primary": "position",
        "match_keys": ["car fleet"],
        "code": """\
def car_fleet(target, position, speed):
    cars = sorted(zip(position, speed))
    __trace("init", values=__json.loads(__json.dumps([p for p, _ in cars])), family="array")
    time = [(target - p) / s for p, s in cars]
    fleets = 0
    cur = 0.0
    for i in range(len(cars) - 1, -1, -1):
        __trace("pointer", name="i", index=i)
        __trace("read", i=i)
        if time[i] > cur:
            cur = time[i]
            fleets += 1
            __trace("mark", i=i, state="active")
    return fleets
""",
    },
    # ── arrays: strings & math ──────────────────────────────────────────────
    "longest_common_prefix": {
        "family": "array",
        "title": "Longest Common Prefix",
        "function": "longest_common_prefix",
        "signature": ["strs"],
        "primary": "strs",
        "match_keys": ["longest common prefix"],
        "code": """\
def longest_common_prefix(strs):
    if not strs:
        return ""
    __trace("init", values=__json.loads(__json.dumps(list(strs[0]))), family="array")
    for i, ch in enumerate(strs[0]):
        __trace("pointer", name="i", index=i)
        for w in strs[1:]:
            if i >= len(w) or w[i] != ch:
                return strs[0][:i]
        __trace("mark", i=i, state="match")
    return strs[0]
""",
    },
    "ransom_note": {
        "family": "array",
        "title": "Ransom Note",
        "function": "ransom_note",
        "signature": ["ransomNote", "magazine"],
        "primary": "magazine",
        "match_keys": ["ransom note"],
        "code": """\
def ransom_note(ransomNote, magazine):
    __trace("init", values=__json.loads(__json.dumps(list(magazine))), family="array")
    from collections import Counter
    avail = Counter(magazine)
    for i, ch in enumerate(ransomNote):
        __trace("pointer", name="i", index=i)
        if avail[ch] <= 0:
            __trace("visit", i=0)
            return False
        avail[ch] -= 1
    __trace("mark", i=0, state="match")
    return True
""",
    },
    "first_word": {
        "family": "array",
        "title": "First Word",
        "function": "first_word",
        "signature": ["s"],
        "primary": "s",
        "match_keys": ["first word"],
        "code": """\
def first_word(s):
    __trace("init", values=__json.loads(__json.dumps(list(s))), family="array")
    for i, ch in enumerate(s):
        __trace("pointer", name="i", index=i)
        if ch == " ":
            return s[:i]
    __trace("mark", i=0, state="match")
    return s
""",
    },
    "most_frequent_char": {
        "family": "array",
        "title": "Most Frequent Character",
        "function": "most_frequent_char",
        "signature": ["s"],
        "primary": "s",
        "match_keys": ["most frequent character", "appears most frequently"],
        "code": """\
def most_frequent_char(s):
    __trace("init", values=__json.loads(__json.dumps(list(s))), family="array")
    from collections import Counter
    counts = Counter(s)
    best_ch = max(counts, key=lambda c: (counts[c], -s.index(c)))
    for i, ch in enumerate(s):
        __trace("pointer", name="i", index=i)
        if counts[ch] == counts[best_ch] and ch == best_ch:
            __trace("mark", i=i, state="match")
    return best_ch
""",
    },
    "happy_number": {
        "family": "array",
        "title": "Happy Number",
        "function": "happy_number",
        "signature": ["n"],
        "primary": "n",
        "match_keys": ["happy number"],
        "code": """\
def happy_number(n):
    __trace("init", values=[n], family="array")
    seen = set()
    cur = n
    __trace("visit", i=0)
    while cur != 1 and cur not in seen:
        seen.add(cur)
        cur = sum(int(d) ** 2 for d in str(cur))
        __trace("write", i=0, value=cur)
    return cur == 1
""",
    },
    "reverse_integer": {
        "family": "array",
        "title": "Reverse Integer",
        "function": "reverse_integer",
        "signature": ["x"],
        "primary": "x",
        "match_keys": ["reverse integer"],
        "code": """\
def reverse_integer(x):
    __trace("init", values=[x], family="array")
    sign = -1 if x < 0 else 1
    cur = abs(x)
    rev = 0
    __trace("visit", i=0)
    while cur:
        rev = rev * 10 + cur % 10
        __trace("write", i=0, value=sign * rev)
        cur //= 10
    return 0 if not (-2**31 <= sign * rev <= 2**31 - 1) else sign * rev
""",
    },
    "number_of_1_bits": {
        "family": "array",
        "title": "Number of 1 Bits",
        "function": "number_of_1_bits",
        "signature": ["n"],
        "primary": "n",
        "match_keys": ["number of 1 bits", "hamming weight", "number of 1"],
        "code": """\
def number_of_1_bits(n):
    if isinstance(n, int):
        bits = bin(n)[2:]
    else:
        bits = str(n)
    __trace("init", values=__json.loads(__json.dumps(list(bits))), family="array")
    total = 0
    for i, b in enumerate(bits):
        __trace("pointer", name="i", index=i)
        if b == "1":
            total += 1
            __trace("mark", i=i, state="match")
    return total
""",
    },
    "power_of_two": {
        "family": "array",
        "title": "Power of Two",
        "function": "power_of_two",
        "signature": ["n"],
        "primary": "n",
        "match_keys": ["power of two"],
        "code": """\
def power_of_two(n):
    __trace("init", values=[n], family="array")
    __trace("visit", i=0)
    if n <= 0:
        return False
    cur = n
    while cur % 2 == 0:
        cur //= 2
        __trace("write", i=0, value=cur)
    __trace("mark", i=0, state="match")
    return cur == 1
""",
    },
    "kth_largest": {
        "family": "array",
        "title": "Kth Largest Element in an Array",
        "function": "kth_largest",
        "signature": ["nums", "k"],
        "primary": "nums",
        "match_keys": ["kth largest element"],
        "code": """\
def kth_largest(nums, k):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="array")
    vals = sorted(nums, reverse=True)
    for i in range(k):
        __trace("pointer", name="i", index=i)
        __trace("mark", i=i, state="active")
    return vals[k - 1]
""",
    },
    "k_closest": {
        "family": "array",
        "title": "K Closest Points to Origin",
        "function": "k_closest",
        "signature": ["points", "k"],
        "primary": "points",
        "match_keys": ["k closest points"],
        "code": """\
def k_closest(points, k):
    __trace("init", values=__json.loads(__json.dumps(list(points))), family="array")
    ranked = sorted((p[0] ** 2 + p[1] ** 2, idx) for idx, p in enumerate(points))
    for _, idx in ranked[:k]:
        __trace("pointer", name="i", index=idx)
        __trace("mark", i=idx, state="active")
    return [points[idx] for _, idx in ranked[:k]]
""",
    },
    "task_scheduler": {
        "family": "array",
        "title": "Task Scheduler",
        "function": "task_scheduler",
        "signature": ["tasks", "n"],
        "primary": "tasks",
        "match_keys": ["task scheduler"],
        "code": """\
def task_scheduler(tasks, n):
    __trace("init", values=__json.loads(__json.dumps(list(tasks))), family="array")
    from collections import Counter
    counts = Counter(tasks)
    for i, t in enumerate(tasks):
        __trace("pointer", name="i", index=i)
        __trace("read", i=i)
    maxc = max(counts.values())
    maxn = sum(1 for c in counts.values() if c == maxc)
    return max(len(tasks), (maxc - 1) * (n + 1) + maxn)
""",
    },
    "word_ladder": {
        "family": "array",
        "title": "Word Ladder",
        "function": "word_ladder",
        "signature": ["beginWord", "endWord", "wordList"],
        "primary": "wordList",
        "match_keys": ["word ladder"],
        "code": """\
def word_ladder(beginWord, endWord, wordList):
    __trace("init", values=__json.loads(__json.dumps(list(wordList))), family="array")
    words = set(wordList)
    if endWord not in words:
        return 0
    from collections import deque
    queue = deque([(beginWord, 1)])
    while queue:
        word, dist = queue.popleft()
        if word == endWord:
            return dist
        for i in range(len(word)):
            for c in "abcdefghijklmnopqrstuvwxyz":
                nxt = word[:i] + c + word[i + 1:]
                if nxt in words:
                    words.discard(nxt)
                    __trace("visit", i=wordList.index(nxt))
                    queue.append((nxt, dist + 1))
    return 0
""",
    },
    # ── backtracking ────────────────────────────────────────────────────────
    "generate_parentheses": {
        "family": "backtrack",
        "title": "Generate Parentheses",
        "function": "generate_parentheses",
        "signature": ["n"],
        "primary": "n",
        "match_keys": ["generate parentheses"],
        "code": """\
def generate_parentheses(n):
    __trace("init", values=[0] * (2 * n), family="backtrack")
    result = []

    def rec(path, open_c, close_c):
        if len(path) == 2 * n:
            result.append("".join(path))
            return
        if open_c < n:
            path.append("(")
            __trace("choose", i=len(path) - 1)
            rec(path, open_c + 1, close_c)
            __trace("backtrack", i=len(path) - 1)
            path.pop()
        if close_c < open_c:
            path.append(")")
            __trace("choose", i=len(path) - 1)
            rec(path, open_c, close_c + 1)
            __trace("backtrack", i=len(path) - 1)
            path.pop()

    rec([], 0, 0)
    return result
""",
    },
    "permutations": {
        "family": "backtrack",
        "title": "Permutations",
        "function": "permutations",
        "signature": ["nums"],
        "primary": "nums",
        "match_keys": ["permutations"],
        "code": """\
def permutations(nums):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="backtrack")
    result = []

    def rec(perm, remaining):
        if not remaining:
            result.append(list(perm))
            return
        for i in range(len(remaining)):
            __trace("choose", i=i)
            rec(perm + [remaining[i]], remaining[:i] + remaining[i + 1:])
            __trace("backtrack", i=i)

    rec([], nums)
    return result
""",
    },
    "subsets": {
        "family": "backtrack",
        "title": "Subsets",
        "function": "subsets",
        "signature": ["nums"],
        "primary": "nums",
        "match_keys": ["subsets", "power set"],
        "code": """\
def subsets(nums):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="backtrack")
    result = []

    def rec(start, path):
        result.append(list(path))
        for i in range(start, len(nums)):
            __trace("choose", i=i)
            rec(i + 1, path + [nums[i]])
            __trace("backtrack", i=i)

    rec(0, [])
    return result
""",
    },
    "combination_sum": {
        "family": "backtrack",
        "title": "Combination Sum",
        "function": "combination_sum",
        "signature": ["candidates", "target"],
        "primary": "candidates",
        "match_keys": ["combination sum"],
        "code": """\
def combination_sum(candidates, target):
    __trace("init", values=__json.loads(__json.dumps(list(candidates))), family="backtrack")
    result = []

    def rec(start, remaining, path):
        if remaining == 0:
            result.append(list(path))
            return
        if remaining < 0:
            return
        for i in range(start, len(candidates)):
            __trace("choose", i=i)
            rec(i, remaining - candidates[i], path + [candidates[i]])
            __trace("backtrack", i=i)

    rec(0, target, [])
    return result
""",
    },
    # ── dynamic programming (1-D, array visuals) ────────────────────────────
    "max_subarray": {
        "family": "array",
        "title": "Maximum Subarray (Kadane)",
        "function": "max_sub_array",
        "signature": ["nums"],
        "primary": "nums",
        "match_keys": [
            "max subarray",
            "maximum subarray",
            "kadane",
            "largest sum contiguous",
        ],
        "code": """\
def max_sub_array(nums):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="array")
    best = nums[0]
    current = nums[0]
    for i in range(1, len(nums)):
        __trace("pointer", name="i", index=i)
        __trace("compare", i=i)
        current = max(nums[i], current + nums[i])
        if current > best:
            best = current
        __trace("mark", i=i, state="active")
    return best
""",
    },
    "maximum_product_subarray": {
        "family": "array",
        "title": "Maximum Product Subarray",
        "function": "maximum_product_subarray",
        "signature": ["nums"],
        "primary": "nums",
        "match_keys": ["maximum product subarray", "largest product"],
        "code": """\
def maximum_product_subarray(nums):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="array")
    best = nums[0]
    mx = mn = nums[0]
    for i in range(1, len(nums)):
        __trace("pointer", name="i", index=i)
        __trace("read", i=i)
        if nums[i] < 0:
            mx, mn = mn, mx
        mx = max(nums[i], mx * nums[i])
        mn = min(nums[i], mn * nums[i])
        best = max(best, mx)
        __trace("mark", i=i, state="active")
    return best
""",
    },
    "climbing_stairs": {
        "family": "array",
        "title": "Climbing Stairs",
        "function": "climbing_stairs",
        "signature": ["n"],
        "primary": "n",
        "match_keys": ["climbing stairs"],
        "code": """\
def climbing_stairs(n):
    dp = [0] * (n + 1)
    dp[0] = 1
    if n >= 1:
        dp[1] = 1
    __trace("init", values=__json.loads(__json.dumps(dp)), family="array")
    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
        __trace("write", i=i, value=dp[i])
    return dp[n]
""",
    },
    "house_robber": {
        "family": "array",
        "title": "House Robber",
        "function": "house_robber",
        "signature": ["nums"],
        "primary": "nums",
        "match_keys": ["house robber"],
        "code": """\
def house_robber(nums):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="array")
    prev, cur = 0, 0
    for i, n in enumerate(nums):
        __trace("pointer", name="i", index=i)
        __trace("read", i=i)
        cur, prev = max(cur, prev + n), cur
        __trace("write", i=i, value=cur)
    return cur
""",
    },
    "decode_ways": {
        "family": "array",
        "title": "Decode Ways",
        "function": "decode_ways",
        "signature": ["s"],
        "primary": "s",
        "match_keys": ["decode ways"],
        "code": """\
def decode_ways(s):
    __trace("init", values=__json.loads(__json.dumps(list(s))), family="array")
    n = len(s)
    dp = [0] * (n + 1)
    dp[0] = 1
    dp[1] = 1 if s[0] != "0" else 0
    for i in range(2, n + 1):
        one = int(s[i - 1])
        two = int(s[i - 2:i])
        if one != 0:
            dp[i] += dp[i - 1]
        if 10 <= two <= 26:
            dp[i] += dp[i - 2]
        __trace("pointer", name="i", index=i - 1)
        __trace("write", i=i - 1, value=dp[i])
    return dp[n]
""",
    },
    "longest_increasing_subsequence": {
        "family": "array",
        "title": "Longest Increasing Subsequence",
        "function": "longest_increasing_subsequence",
        "signature": ["nums"],
        "primary": "nums",
        "match_keys": ["longest increasing subsequence"],
        "code": """\
def longest_increasing_subsequence(nums):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="array")
    n = len(nums)
    dp = [1] * n
    for i in range(n):
        __trace("pointer", name="i", index=i)
        for j in range(i):
            if nums[j] < nums[i]:
                dp[i] = max(dp[i], dp[j] + 1)
        __trace("write", i=i, value=dp[i])
    return max(dp) if dp else 0
""",
    },
    "word_break": {
        "family": "array",
        "title": "Word Break",
        "function": "word_break",
        "signature": ["s", "wordDict"],
        "primary": "s",
        "match_keys": ["word break"],
        "code": """\
def word_break(s, wordDict):
    __trace("init", values=__json.loads(__json.dumps(list(s))), family="array")
    words = set(wordDict)
    n = len(s)
    dp = [False] * (n + 1)
    dp[0] = True
    for i in range(1, n + 1):
        for j in range(i):
            if dp[j] and s[j:i] in words:
                dp[i] = True
                break
        __trace("write", i=i - 1, value=int(dp[i]))
    return dp[n]
""",
    },
    "coin_change": {
        "family": "array",
        "title": "Coin Change",
        "function": "coin_change",
        "signature": ["coins", "amount"],
        "primary": "amount",
        "match_keys": ["coin change"],
        "code": """\
def coin_change(coins, amount):
    dp = [amount + 1] * (amount + 1)
    dp[0] = 0
    __trace("init", values=__json.loads(__json.dumps(dp)), family="array")
    for i in range(1, amount + 1):
        __trace("pointer", name="i", index=i)
        for c in coins:
            if c <= i:
                dp[i] = min(dp[i], dp[i - c] + 1)
        __trace("write", i=i, value=dp[i])
    return -1 if dp[amount] > amount else dp[amount]
""",
    },
    "burst_balloons": {
        "family": "array",
        "title": "Burst Balloons",
        "function": "burst_balloons",
        "signature": ["nums"],
        "primary": "nums",
        "match_keys": ["burst balloons"],
        "code": """\
def burst_balloons(nums):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="array")
    n = len(nums)
    dp = [[0] * n for _ in range(n)]
    for length in range(1, n + 1):
        for left in range(n - length + 1):
            right = left + length - 1
            __trace("pointer", name="l", index=left)
            __trace("pointer", name="r", index=right)
            for k in range(left, right + 1):
                val = nums[k]
                if left > 0:
                    val *= nums[left - 1]
                if right < n - 1:
                    val *= nums[right + 1]
                score = dp[left][k - 1] if k > left else 0
                score += dp[k + 1][right] if k < right else 0
                dp[left][right] = max(dp[left][right], score + val)
            __trace("mark", i=left, state="active")
    return max(max(row) for row in dp) if dp else 0
""",
    },
    "edit_distance": {
        "family": "array",
        "title": "Edit Distance",
        "function": "edit_distance",
        "signature": ["word1", "word2"],
        "primary": "word1",
        "match_keys": ["edit distance"],
        "code": """\
def edit_distance(word1, word2):
    __trace("init", values=__json.loads(__json.dumps(list(word1))), family="array")
    m, n = len(word1), len(word2)
    prev = list(range(n + 1))
    for i in range(1, m + 1):
        cur = [i] + [0] * n
        __trace("pointer", name="i", index=i - 1)
        for j in range(1, n + 1):
            if word1[i - 1] == word2[j - 1]:
                cur[j] = prev[j - 1]
            else:
                cur[j] = 1 + min(prev[j], cur[j - 1], prev[j - 1])
        prev = cur
        __trace("write", i=i - 1, value=prev[n])
    return prev[n]
""",
    },
    # ── stack family ────────────────────────────────────────────────────────
    "valid_parentheses": {
        "family": "stack",
        "title": "Valid Parentheses",
        "function": "valid_parentheses",
        "signature": ["s"],
        "primary": "s",
        "match_keys": ["valid parentheses"],
        "code": """\
def valid_parentheses(s):
    __trace("init", data=__json.loads(__json.dumps(list(s))), family="stack")
    stack = []
    pairs = {")": "(", "}": "{", "]": "["}
    for i, ch in enumerate(s):
        __trace("visit", i=i)
        if ch in pairs:
            if not stack:
                return False
            top = stack.pop()
            __trace("pop", value=top)
            if pairs[ch] != top:
                return False
        else:
            stack.append(ch)
            __trace("push", value=ch)
    return not stack
""",
    },
    "evaluate_reverse_polish_notation": {
        "family": "stack",
        "title": "Evaluate Reverse Polish Notation",
        "function": "evaluate_reverse_polish_notation",
        "signature": ["tokens"],
        "primary": "tokens",
        "match_keys": ["reverse polish notation", "postfix"],
        "code": """\
def evaluate_reverse_polish_notation(tokens):
    __trace("init", data=__json.loads(__json.dumps(list(tokens))), family="stack")
    stack = []
    for i, t in enumerate(tokens):
        __trace("visit", i=i)
        if t in {"+", "-", "*", "/"}:
            b = stack.pop()
            a = stack.pop()
            __trace("pop", value=a)
            __trace("pop", value=b)
            if t == "+":
                res = a + b
            elif t == "-":
                res = a - b
            elif t == "*":
                res = a * b
            else:
                res = int(a / b)
            stack.append(res)
            __trace("push", value=res)
        else:
            stack.append(int(t))
            __trace("push", value=int(t))
    return stack[0]
""",
    },
    "daily_temperatures": {
        "family": "stack",
        "title": "Daily Temperatures",
        "function": "daily_temperatures",
        "signature": ["temperatures"],
        "primary": "temperatures",
        "match_keys": ["daily temperatures"],
        "code": """\
def daily_temperatures(temperatures):
    __trace("init", data=__json.loads(__json.dumps(list(temperatures))), family="stack")
    n = len(temperatures)
    res = [0] * n
    stack = []
    for i, t in enumerate(temperatures):
        __trace("visit", i=i)
        while stack and temperatures[stack[-1]] < t:
            j = stack.pop()
            res[j] = i - j
            __trace("pop", value=temperatures[j])
        stack.append(i)
        __trace("push", value=temperatures[i])
    return res
""",
    },
    "largest_rectangle_in_histogram": {
        "family": "stack",
        "title": "Largest Rectangle in Histogram",
        "function": "largest_rectangle_in_histogram",
        "signature": ["heights"],
        "primary": "heights",
        "match_keys": ["largest rectangle in histogram"],
        "code": """\
def largest_rectangle_in_histogram(heights):
    __trace("init", data=__json.loads(__json.dumps(list(heights))), family="stack")
    stack = []
    best = 0
    for i, h in enumerate(heights):
        __trace("visit", i=i)
        start = i
        while stack and stack[-1][1] > h:
            idx, hh = stack.pop()
            best = max(best, hh * (i - idx))
            __trace("pop", value=hh)
            start = idx
        stack.append((start, h))
        __trace("push", value=h)
    while stack:
        idx, hh = stack.pop()
        best = max(best, hh * (len(heights) - idx))
        __trace("pop", value=hh)
    return best
""",
    },
    "longest_valid_parentheses": {
        "family": "stack",
        "title": "Longest Valid Parentheses",
        "function": "longest_valid_parentheses",
        "signature": ["s"],
        "primary": "s",
        "match_keys": ["longest valid parentheses"],
        "code": """\
def longest_valid_parentheses(s):
    __trace("init", data=__json.loads(__json.dumps(list(s))), family="stack")
    stack = [-1]
    best = 0
    for i, ch in enumerate(s):
        __trace("visit", i=i)
        if ch == "(":
            stack.append(i)
            __trace("push", value="(")
        else:
            stack.pop()
            if not stack:
                stack.append(i)
            else:
                best = max(best, i - stack[-1])
                __trace("pop", value=")")
    return best
""",
    },
    "min_stack": {
        "family": "stack",
        "title": "Min Stack",
        "function": "min_stack",
        "signature": ["operations", "values"],
        "primary": "operations",
        "match_keys": ["min stack"],
        "code": """\
def min_stack(operations, values):
    __trace("init", data=__json.loads(__json.dumps(list(operations))), family="stack")
    stack = []
    mins = []
    for i, op in enumerate(operations):
        __trace("visit", i=i)
        if op == "push":
            v = values[i][0]
            stack.append(v)
            mins.append(v if not mins else min(v, mins[-1]))
            __trace("push", value=v)
        elif op == "pop":
            v = stack.pop()
            mins.pop()
            __trace("pop", value=v)
    return None
""",
    },
    # ── linked list family ──────────────────────────────────────────────────
    "reverse_linked_list": {
        "family": "linked_list",
        "title": "Reverse Linked List",
        "function": "reverse_linked_list",
        "signature": ["head"],
        "primary": "head",
        "match_keys": ["reverse linked list"],
        "code": """\
def reverse_linked_list(head):
    __trace("init", data=__json.loads(__json.dumps(list(head))), family="linked_list")
    for i in range(len(head)):
        __trace("pointer", name="current", index=i)
        __trace("visit", i=i)
        __trace("mark", i=i, state="reversed")
    return list(reversed(head))
""",
    },
    "linked_list_cycle": {
        "family": "linked_list",
        "title": "Linked List Cycle",
        "function": "linked_list_cycle",
        "signature": ["head", "pos"],
        "primary": "head",
        "match_keys": ["linked list cycle", "cycle exists"],
        "code": """\
def linked_list_cycle(head, pos):
    __trace("init", data=__json.loads(__json.dumps(list(head))), family="linked_list")
    n = len(head)
    for i in range(n):
        __trace("pointer", name="fast", index=(2 * i) % n if n else 0)
        __trace("visit", i=i)
    return pos != -1
""",
    },
    "merge_two_sorted_lists": {
        "family": "linked_list",
        "title": "Merge Two Sorted Lists",
        "function": "merge_two_sorted_lists",
        "signature": ["list1", "list2"],
        "primary": "list1",
        "match_keys": ["merge two sorted lists"],
        "code": """\
def merge_two_sorted_lists(list1, list2):
    merged = sorted(list1 + list2)
    __trace("init", data=__json.loads(__json.dumps(list(merged))), family="linked_list")
    for i in range(len(merged)):
        __trace("visit", i=i)
        __trace("mark", i=i, state="sorted")
    return merged
""",
    },
    "add_two_numbers": {
        "family": "linked_list",
        "title": "Add Two Numbers",
        "function": "add_two_numbers",
        "signature": ["l1", "l2"],
        "primary": "l1",
        "match_keys": ["add two numbers"],
        "code": """\
def add_two_numbers(l1, l2):
    i = 0
    carry = 0
    result = []
    while i < len(l1) or i < len(l2) or carry:
        a = l1[i] if i < len(l1) else 0
        b = l2[i] if i < len(l2) else 0
        s = a + b + carry
        result.append(s % 10)
        carry = s // 10
        i += 1
    __trace("init", data=__json.loads(__json.dumps(list(result))), family="linked_list")
    for idx in range(len(result)):
        __trace("visit", i=idx)
        __trace("mark", i=idx, state="sorted")
    return result
""",
    },
    "merge_k_sorted_lists": {
        "family": "linked_list",
        "title": "Merge k Sorted Lists",
        "function": "merge_k_sorted_lists",
        "signature": ["lists"],
        "primary": "lists",
        "match_keys": ["merge k sorted lists"],
        "code": """\
def merge_k_sorted_lists(lists):
    merged = sorted(v for sub in lists for v in sub)
    __trace("init", data=__json.loads(__json.dumps(list(merged))), family="linked_list")
    for i in range(len(merged)):
        __trace("visit", i=i)
        __trace("mark", i=i, state="sorted")
    return merged
""",
    },
    "remove_nth_node_from_end": {
        "family": "linked_list",
        "title": "Remove Nth Node From End of List",
        "function": "remove_nth_node_from_end",
        "signature": ["head", "n"],
        "primary": "head",
        "match_keys": ["remove nth node"],
        "code": """\
def remove_nth_node_from_end(head, n):
    __trace("init", data=__json.loads(__json.dumps(list(head))), family="linked_list")
    target = len(head) - n
    for i in range(len(head)):
        __trace("pointer", name="current", index=i)
        if i == target:
            __trace("visit", i=i)
            __trace("mark", i=i, state="removed")
    return [v for i, v in enumerate(head) if i != target]
""",
    },
    "reorder_list": {
        "family": "linked_list",
        "title": "Reorder List",
        "function": "reorder_list",
        "signature": ["head"],
        "primary": "head",
        "match_keys": ["reorder list"],
        "code": """\
def reorder_list(head):
    __trace("init", data=__json.loads(__json.dumps(list(head))), family="linked_list")
    result = []
    n = len(head)
    l, r = 0, n - 1
    while l <= r:
        __trace("pointer", name="left", index=l)
        __trace("pointer", name="right", index=r)
        __trace("visit", i=l)
        result.append(head[l])
        if l != r:
            __trace("visit", i=r)
            result.append(head[r])
        l += 1
        r -= 1
    return result
""",
    },
    # ── tree family ─────────────────────────────────────────────────────────
    "maximum_depth_of_binary_tree": {
        "family": "tree",
        "title": "Maximum Depth of Binary Tree",
        "function": "maximum_depth_of_binary_tree",
        "signature": ["root"],
        "primary": "root",
        "match_keys": ["maximum depth of binary tree", "maximum depth"],
        "code": """\
def maximum_depth_of_binary_tree(root):
    __trace("init", data=__json.loads(__json.dumps(list(root))), family="tree")
    best = 0
    for i, v in enumerate(root):
        if v is not None:
            __trace("visit", i=i)
            best = max(best, (i + 1).bit_length())
    return best
""",
    },
    "balanced_binary_tree": {
        "family": "tree",
        "title": "Balanced Binary Tree",
        "function": "balanced_binary_tree",
        "signature": ["root"],
        "primary": "root",
        "match_keys": ["balanced binary tree", "height-balanced"],
        "code": """\
def balanced_binary_tree(root):
    __trace("init", data=__json.loads(__json.dumps(list(root))), family="tree")
    heights = {}
    for i in range(len(root) - 1, -1, -1):
        if root[i] is None:
            continue
        left = heights.get(2 * i + 1, 0)
        right = heights.get(2 * i + 2, 0)
        __trace("visit", i=i)
        if abs(left - right) > 1:
            return False
        heights[i] = max(left, right) + 1
        __trace("mark", i=i, state="active")
    return True
""",
    },
    "invert_binary_tree": {
        "family": "tree",
        "title": "Invert Binary Tree",
        "function": "invert_binary_tree",
        "signature": ["root"],
        "primary": "root",
        "match_keys": ["invert binary tree"],
        "code": """\
def invert_binary_tree(root):
    __trace("init", data=__json.loads(__json.dumps(list(root))), family="tree")
    for i, v in enumerate(root):
        if v is not None:
            __trace("visit", i=i)
    return root
""",
    },
    "same_tree": {
        "family": "tree",
        "title": "Same Tree",
        "function": "same_tree",
        "signature": ["p", "q"],
        "primary": "p",
        "match_keys": ["same tree"],
        "code": """\
def same_tree(p, q):
    __trace("init", data=__json.loads(__json.dumps(list(p))), family="tree")
    for i in range(max(len(p), len(q))):
        a = p[i] if i < len(p) else None
        b = q[i] if i < len(q) else None
        __trace("visit", i=i)
        if a != b:
            return False
        if a is not None:
            __trace("mark", i=i, state="active")
    return True
""",
    },
    "validate_binary_search_tree": {
        "family": "tree",
        "title": "Validate Binary Search Tree",
        "function": "validate_binary_search_tree",
        "signature": ["root"],
        "primary": "root",
        "match_keys": ["validate binary search tree", "valid binary search tree"],
        "code": """\
def validate_binary_search_tree(root):
    __trace("init", data=__json.loads(__json.dumps(list(root))), family="tree")
    def dfs(i, lo, hi):
        if i >= len(root) or root[i] is None:
            return True
        v = root[i]
        __trace("visit", i=i)
        if not (lo < v < hi):
            return False
        ok = dfs(2 * i + 1, lo, v) and dfs(2 * i + 2, v, hi)
        if ok:
            __trace("mark", i=i, state="valid")
        return ok
    return dfs(0, float("-inf"), float("inf"))
""",
    },
    "binary_tree_level_order_traversal": {
        "family": "tree",
        "title": "Binary Tree Level Order Traversal",
        "function": "binary_tree_level_order_traversal",
        "signature": ["root"],
        "primary": "root",
        "match_keys": ["level order traversal"],
        "code": """\
def binary_tree_level_order_traversal(root):
    __trace("init", data=__json.loads(__json.dumps(list(root))), family="tree")
    levels = {}
    for i, v in enumerate(root):
        if v is not None:
            __trace("visit", i=i)
            levels.setdefault(i.bit_length() - 1, []).append(v)
    return list(levels.values())
""",
    },
    "kth_smallest_element_in_a_bst": {
        "family": "tree",
        "title": "Kth Smallest Element in a BST",
        "function": "kth_smallest_element_in_a_bst",
        "signature": ["root", "k"],
        "primary": "root",
        "match_keys": ["kth smallest element in a bst"],
        "code": """\
def kth_smallest_element_in_a_bst(root, k):
    __trace("init", data=__json.loads(__json.dumps(list(root))), family="tree")
    seen = []

    def inorder(i):
        if i >= len(root) or root[i] is None or len(seen) >= k:
            return
        inorder(2 * i + 1)
        if len(seen) < k:
            __trace("visit", i=i)
            seen.append(root[i])
        inorder(2 * i + 2)

    inorder(0)
    return seen[-1]
""",
    },
    "lowest_common_ancestor": {
        "family": "tree",
        "title": "Lowest Common Ancestor of a Binary Tree",
        "function": "lowest_common_ancestor",
        "signature": ["root", "p", "q"],
        "primary": "root",
        "match_keys": ["lowest common ancestor"],
        "code": """\
def lowest_common_ancestor(root, p, q):
    __trace("init", data=__json.loads(__json.dumps(list(root))), family="tree")
    def find(i):
        if i >= len(root) or root[i] is None:
            return None
        __trace("visit", i=i)
        if root[i] in (p, q):
            return root[i]
        lf = find(2 * i + 1)
        rg = find(2 * i + 2)
        if lf and rg:
            __trace("mark", i=i, state="lca")
            return root[i]
        return lf or rg
    return find(0)
""",
    },
    "binary_tree_maximum_path_sum": {
        "family": "tree",
        "title": "Binary Tree Maximum Path Sum",
        "function": "binary_tree_maximum_path_sum",
        "signature": ["root"],
        "primary": "root",
        "match_keys": ["maximum path sum"],
        "code": """\
def binary_tree_maximum_path_sum(root):
    __trace("init", data=__json.loads(__json.dumps(list(root))), family="tree")
    best = [float("-inf")]
    def dfs(i):
        if i >= len(root) or root[i] is None:
            return 0
        __trace("visit", i=i)
        left = max(0, dfs(2 * i + 1))
        right = max(0, dfs(2 * i + 2))
        best[0] = max(best[0], root[i] + left + right)
        __trace("mark", i=i, state="active")
        return root[i] + max(left, right)
    dfs(0)
    return int(best[0])
""",
    },
    # ── grid family ─────────────────────────────────────────────────────────
    "rotate_image": {
        "family": "grid",
        "title": "Rotate Image",
        "function": "rotate_image",
        "signature": ["matrix"],
        "primary": "matrix",
        "match_keys": ["rotate image"],
        "code": """\
def rotate_image(matrix):
    __trace("init", data=__json.loads(__json.dumps(matrix)), family="grid")
    n = len(matrix)
    for i in range(n):
        for j in range(i + 1, n):
            __trace("visit", i=i, j=j)
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
            __trace("write", i=i, j=j, value=matrix[i][j])
            __trace("write", i=j, j=i, value=matrix[j][i])
    for i in range(n):
        for j in range(n // 2):
            matrix[i][j], matrix[i][n - 1 - j] = matrix[i][n - 1 - j], matrix[i][j]
            __trace("write", i=i, j=j, value=matrix[i][j])
            __trace("write", i=i, j=n - 1 - j, value=matrix[i][n - 1 - j])
    return matrix
""",
    },
    "number_of_islands": {
        "family": "grid",
        "title": "Number of Islands",
        "function": "number_of_islands",
        "signature": ["grid"],
        "primary": "grid",
        "match_keys": ["number of islands"],
        "code": """\
def number_of_islands(grid):
    __trace("init", data=__json.loads(__json.dumps(grid)), family="grid")
    rows, cols = len(grid), len(grid[0])
    count = 0
    def flood(r, c):
        if r < 0 or r >= rows or c < 0 or c >= cols or grid[r][c] != "1":
            return
        grid[r][c] = "0"
        __trace("visit", i=r, j=c)
        __trace("mark", i=r, j=c, state="land")
        flood(r + 1, c)
        flood(r - 1, c)
        flood(r, c + 1)
        flood(r, c - 1)
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == "1":
                count += 1
                flood(r, c)
    return count
""",
    },
    "word_search": {
        "family": "grid",
        "title": "Word Search",
        "function": "word_search",
        "signature": ["board", "word"],
        "primary": "board",
        "match_keys": ["word search"],
        "code": """\
def word_search(board, word):
    __trace("init", data=__json.loads(__json.dumps(board)), family="grid")
    rows, cols = len(board), len(board[0])
    seen = set()
    def dfs(r, c, k):
        if k == len(word):
            return True
        if r < 0 or r >= rows or c < 0 or c >= cols or (r, c) in seen or board[r][c] != word[k]:
            return False
        seen.add((r, c))
        __trace("visit", i=r, j=c)
        found = any(dfs(r + dr, c + dc, k + 1) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        seen.remove((r, c))
        if not found:
            __trace("backtrack", i=r, j=c)
        return found
    for r in range(rows):
        for c in range(cols):
            if dfs(r, c, 0):
                __trace("mark", i=r, j=c, state="match")
                return True
    return False
""",
    },
    # ── graph family ────────────────────────────────────────────────────────
    "clone_graph": {
        "family": "graph",
        "title": "Clone Graph",
        "function": "clone_graph",
        "signature": ["adj"],
        "primary": "adj",
        "match_keys": ["clone graph"],
        "code": """\
def clone_graph(adj):
    __trace("init", data=__json.loads(__json.dumps(adj)), family="graph")
    n = len(adj)
    for i in range(n):
        __trace("visit", i=i)
        for b in adj[i]:
            try:
                b = int(b) - 1
            except (TypeError, ValueError):
                continue
            if 0 <= b < n:
                __trace("edge", a=i, b=b)
    return n
""",
    },
    "course_schedule": {
        "family": "graph",
        "title": "Course Schedule",
        "function": "course_schedule",
        "signature": ["numCourses", "prerequisites"],
        "primary": "prerequisites",
        "match_keys": ["course schedule"],
        "code": """\
def course_schedule(numCourses, prerequisites):
    __trace("init", data=__json.loads(__json.dumps(prerequisites)), family="graph", n=numCourses)
    adj = [[] for _ in range(numCourses)]
    for a, b in prerequisites:
        adj[b].append(a)
    indeg = [0] * numCourses
    for nbrs in adj:
        for nbr in nbrs:
            indeg[nbr] += 1
    queue = [i for i in range(numCourses) if indeg[i] == 0]
    order = 0
    while queue:
        u = queue.pop(0)
        __trace("visit", i=u)
        order += 1
        for v in adj[u]:
            __trace("edge", a=u, b=v)
            indeg[v] -= 1
            if indeg[v] == 0:
                queue.append(v)
    return order == numCourses
""",
    },
    "course_schedule_ii": {
        "family": "graph",
        "title": "Course Schedule II",
        "function": "course_schedule_ii",
        "signature": ["numCourses", "prerequisites"],
        "primary": "prerequisites",
        "match_keys": ["course schedule ii"],
        "code": """\
def course_schedule_ii(numCourses, prerequisites):
    __trace("init", data=__json.loads(__json.dumps(prerequisites)), family="graph", n=numCourses)
    adj = [[] for _ in range(numCourses)]
    for a, b in prerequisites:
        adj[b].append(a)
    indeg = [0] * numCourses
    for nbrs in adj:
        for nbr in nbrs:
            indeg[nbr] += 1
    queue = [i for i in range(numCourses) if indeg[i] == 0]
    order = []
    while queue:
        u = queue.pop(0)
        __trace("visit", i=u)
        order.append(u)
        for v in adj[u]:
            __trace("edge", a=u, b=v)
            indeg[v] -= 1
            if indeg[v] == 0:
                queue.append(v)
    return order if len(order) == numCourses else []
""",
    },
    "search_insert_position": {
        "family": "array",
        "title": "Search Insert Position",
        "function": "search_insert_position",
        "signature": ["nums", "target"],
        "primary": "nums",
        "match_keys": ["search insert position"],
        "code": """\
def search_insert_position(nums, target):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="array")
    lo, hi = 0, len(nums)
    while lo < hi:
        mid = (lo + hi) // 2
        __trace("pointer", name="lo", index=lo)
        __trace("pointer", name="hi", index=hi)
        __trace("pointer", name="mid", index=mid)
        __trace("compare", i=mid)
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    __trace("mark", i=min(lo, len(nums) - 1), state="match")
    return lo
""",
    },
    "find_first_and_last": {
        "family": "array",
        "title": "Find First and Last Position of Element in Sorted Array",
        "function": "find_first_and_last",
        "signature": ["nums", "target"],
        "primary": "nums",
        "match_keys": ["first and last position"],
        "code": """\
def find_first_and_last(nums, target):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="array")
    def bs(go_left):
        lo, hi = 0, len(nums) - 1
        idx = -1
        while lo <= hi:
            mid = (lo + hi) // 2
            __trace("pointer", name="lo", index=lo)
            __trace("pointer", name="hi", index=hi)
            __trace("pointer", name="mid", index=mid)
            __trace("compare", i=mid)
            if nums[mid] == target:
                idx = mid
                if go_left:
                    hi = mid - 1
                else:
                    lo = mid + 1
            elif nums[mid] < target:
                lo = mid + 1
            else:
                hi = mid - 1
        return idx
    left = bs(True)
    right = bs(False)
    if left != -1:
        __trace("mark", i=left, state="match")
        __trace("mark", i=right, state="match")
    return [left, right]
""",
    },
    "find_minimum_in_rotated": {
        "family": "array",
        "title": "Find Minimum in Rotated Sorted Array",
        "function": "find_minimum_in_rotated",
        "signature": ["nums"],
        "primary": "nums",
        "match_keys": ["minimum in rotated"],
        "code": """\
def find_minimum_in_rotated(nums):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="array")
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        __trace("pointer", name="lo", index=lo)
        __trace("pointer", name="hi", index=hi)
        __trace("pointer", name="mid", index=mid)
        __trace("compare", i=mid)
        if nums[mid] > nums[hi]:
            lo = mid + 1
        else:
            hi = mid
    __trace("mark", i=lo, state="match")
    return nums[lo]
""",
    },
    "search_in_rotated": {
        "family": "array",
        "title": "Search in Rotated Sorted Array",
        "function": "search_in_rotated",
        "signature": ["nums", "target"],
        "primary": "nums",
        "match_keys": ["search in rotated"],
        "code": """\
def search_in_rotated(nums, target):
    __trace("init", values=__json.loads(__json.dumps(list(nums))), family="array")
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        __trace("pointer", name="lo", index=lo)
        __trace("pointer", name="hi", index=hi)
        __trace("pointer", name="mid", index=mid)
        __trace("compare", i=mid)
        if nums[mid] == target:
            __trace("mark", i=mid, state="match")
            return mid
        if nums[lo] <= nums[mid]:
            if nums[lo] <= target < nums[mid]:
                hi = mid - 1
            else:
                lo = mid + 1
        else:
            if nums[mid] < target <= nums[hi]:
                lo = mid + 1
            else:
                hi = mid - 1
    return -1
""",
    },
    "koko_eating_bananas": {
        "family": "array",
        "title": "Koko Eating Bananas",
        "function": "koko_eating_bananas",
        "signature": ["piles", "h"],
        "primary": "piles",
        "match_keys": ["koko eating bananas", "koko loves to eat bananas"],
        "code": """\
def koko_eating_bananas(piles, h):
    __trace("init", values=__json.loads(__json.dumps(list(piles))), family="array")
    lo, hi = 1, max(piles)
    best = hi
    while lo <= hi:
        mid = (lo + hi) // 2
        __trace("pointer", name="lo", index=lo)
        __trace("pointer", name="hi", index=hi)
        __trace("pointer", name="mid", index=mid)
        hours = sum((p + mid - 1) // mid for p in piles)
        __trace("compare", i=mid)
        if hours <= h:
            best = mid
            hi = mid - 1
        else:
            lo = mid + 1
    __trace("mark", i=min(best, len(piles) - 1), state="match")
    return best
""",
    },
    "median_of_two_sorted_arrays": {
        "family": "array",
        "title": "Median of Two Sorted Arrays",
        "function": "median_of_two_sorted_arrays",
        "signature": ["nums1", "nums2"],
        "primary": "nums1",
        "match_keys": ["median of two sorted arrays"],
        "code": """\
def median_of_two_sorted_arrays(nums1, nums2):
    merged = sorted(nums1 + nums2)
    __trace("init", values=__json.loads(__json.dumps(list(merged))), family="array")
    n = len(merged)
    mid = n // 2
    __trace("pointer", name="mid", index=mid)
    if n % 2:
        __trace("mark", i=mid, state="match")
        return float(merged[mid])
    __trace("mark", i=mid - 1, state="match")
    __trace("mark", i=mid, state="match")
    return (merged[mid - 1] + merged[mid]) / 2
""",
    },
    # ── intervals family ────────────────────────────────────────────────────
    "merge_intervals": {
        "family": "intervals",
        "title": "Merge Intervals",
        "function": "merge_intervals",
        "signature": ["intervals"],
        "primary": "intervals",
        "match_keys": ["merge intervals"],
        "code": """\
def merge_intervals(intervals):
    iv = sorted(intervals, key=lambda x: (x[0], x[1]))
    __trace("init", data=__json.loads(__json.dumps(iv)), family="intervals")
    merged = []
    for i, (s, e) in enumerate(iv):
        __trace("pointer", name="i", index=i)
        __trace("visit", i=i)
        if not merged or merged[-1][1] < s:
            merged.append([s, e])
            __trace("mark", i=i, state="merged")
        else:
            merged[-1][1] = max(merged[-1][1], e)
            __trace("mark", i=i, state="merged")
    return merged
""",
    },
    "non_overlapping_intervals": {
        "family": "intervals",
        "title": "Non-overlapping Intervals",
        "function": "non_overlapping_intervals",
        "signature": ["intervals"],
        "primary": "intervals",
        "match_keys": ["non-overlapping intervals", "non-overlapping"],
        "code": """\
def non_overlapping_intervals(intervals):
    iv = sorted(intervals, key=lambda x: (x[1], x[0]))
    __trace("init", data=__json.loads(__json.dumps(iv)), family="intervals")
    end = float("-inf")
    removed = 0
    for i, (s, e) in enumerate(iv):
        __trace("pointer", name="i", index=i)
        __trace("visit", i=i)
        if s >= end:
            end = e
            __trace("mark", i=i, state="kept")
        else:
            removed += 1
            __trace("mark", i=i, state="removed")
    return removed
""",
    },
}


def get_reference_solution(algorithm: Optional[str]) -> Optional[dict]:
    return REFERENCE_SOLUTIONS.get(algorithm) if algorithm else None


def resolve_algorithm(question: Optional[dict]) -> Optional[str]:
    """Return the catalog algorithm matching a question, or None.

    Matching order (deterministic):
    1. Exact question-id mapping (see question_catalog.QUESTION_ALGORITHMS).
    2. Keyword scan of the lowercased title/category/description against each
       entry's match_keys.

    The keyword scan is a fallback only: category names like "Binary Search"
    no longer over-match whole categories because every known DB question is
    pinned by id first.
    """
    if not isinstance(question, dict):
        return None
    from app.services.question_catalog import resolve_by_id

    by_id = resolve_by_id(question)
    if by_id:
        return by_id
    parts = [
        str(question.get("title") or ""),
        str(question.get("category") or ""),
        str(question.get("description") or ""),
    ]
    text = " ".join(parts).lower()
    title_desc = " ".join([parts[0], parts[2]]).lower()

    def _best_match(needle: str) -> Optional[str]:
        matches = [
            (algo, key)
            for algo, entry in REFERENCE_SOLUTIONS.items()
            for key in entry["match_keys"]
            if key in needle
        ]
        if not matches:
            return None
        # Longest matched key wins so "two sum ii" beats "two sum".
        matches.sort(key=lambda m: len(m[1]), reverse=True)
        return matches[0][0]

    # Pass 1: title + description only (the strongest signal). A category like
    # "Binary Search" must never redirect a question whose title names a
    # different algorithm.
    algo = _best_match(title_desc)
    if algo:
        return algo
    return _best_match(text)
