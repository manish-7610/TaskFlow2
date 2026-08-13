"""
Searching algorithms.
"""
from typing import List, Dict, Any


def binary_search(data: List[Dict[str, Any]], key: str, value: Any) -> int:
    """
    Performs binary search on a list of dictionaries sorted by `key`.

    Args:
        data: List of dictionaries (must be sorted by `key`).
        key: The dictionary key to compare.
        value: The value to search for.

    Returns:
        Index of the first match, or -1 if not found.
    """
    low, high = 0, len(data) - 1
    while low <= high:
        mid = (low + high) // 2
        mid_val = data[mid][key]
        if mid_val == value:
            return mid
        elif mid_val < value:
            low = mid + 1
        else:
            high = mid - 1
    return -1


def linear_search(data: List[Dict[str, Any]], key: str, value: Any) -> int:
    """
    Performs linear search on a list of dictionaries.

    Args:
        data: List of dictionaries.
        key: The dictionary key to compare.
        value: The value to search for.

    Returns:
        Index of the first match, or -1 if not found.
    """
    for idx, item in enumerate(data):
        if item[key] == value:
            return idx
    return -1