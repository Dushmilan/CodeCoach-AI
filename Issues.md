1. When the cose is right the out put is getting wrong.


For example. def find_duplicates(nums):
    """
    Find all elements that appear more than once in the list.
    
    Args:
        nums: List of elements (typically integers)
    
    Returns:
        List of duplicate elements (without repetition)
    """
    seen = set()
    duplicates = set()
    
    for num in nums:
        if num in seen:
            duplicates.add(num)
        else:
            seen.add(num)
    
    return list(duplicates)

    ---
    Output
    ----
    Run Results: 0/3 passed

❌ No duplicates in the array:
   Status: Fail
   Input: [1, 2, 3, 2, 4, 5, 6]
   Expected Output: []
   Actual Output: ["2", ",", " "]

❌ Duplicates in the array:
   Status: Fail
   Input: [1, 1, 1, 2, 2, 3]
   Expected Output: [1, 2]
   Actual Output: ["1", "2", ",", " "]

❌ One duplicate in the array:
   Status: Fail
   Input: [1, 2, 3, 4, 5, 6]
   Expected Output: [2]
   Actual Output: [" ", ","]