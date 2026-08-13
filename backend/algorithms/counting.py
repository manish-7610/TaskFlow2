"""
Counting wrappers for algorithms.
"""
from typing import List, Dict, Any


def insertion_sort_count(records: List[Dict[str, Any]], key: str) -> int:
    """
    Sorts a list of dictionaries in place using insertion sort and counts comparisons.

    Returns:
        int: Number of comparisons performed.
    """
    n = len(records)
    comparisons = 0
    for i in range(1, n):
        current = records[i]
        j = i - 1
        while j >= 0:
            comparisons += 1
            if records[j][key] > current[key]:
                records[j + 1] = records[j]
                j -= 1
            else:
                break
        records[j + 1] = current
    return comparisons


def binary_search_count(data: List[Dict[str, Any]], key: str, value: Any) -> dict:
    """
    Performs binary search and counts comparisons.

    Returns:
        dict: {'index': int, 'comparison_count': int}
    """
    low, high = 0, len(data) - 1
    comparisons = 0
    while low <= high:
        mid = (low + high) // 2
        mid_val = data[mid][key]
        comparisons += 1
        if mid_val == value:
            return {"index": mid, "comparison_count": comparisons}
        elif mid_val < value:
            low = mid + 1
        else:
            high = mid - 1
    return {"index": -1, "comparison_count": comparisons}


def linear_search_count(data: List[Dict[str, Any]], key: str, value: Any) -> dict:
    """
    Performs linear search and counts comparisons.

    Returns:
        dict: {'index': int, 'comparison_count': int}
    """
    comparisons = 0
    for idx, item in enumerate(data):
        comparisons += 1
        if item[key] == value:
            return {"index": idx, "comparison_count": comparisons}
    return {"index": -1, "comparison_count": comparisons}