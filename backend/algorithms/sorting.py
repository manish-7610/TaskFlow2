"""
Sorting algorithms (in-place).
"""
from typing import List, Dict, Any


def insertion_sort(records: List[Dict[str, Any]], key: str) -> None:
    """
    Sorts a list of dictionaries in place using insertion sort.

    Args:
        records: List of dictionaries to sort.
        key: The dictionary key to sort by (must be comparable).
    """
    n = len(records)
    for i in range(1, n):
        current = records[i]
        j = i - 1
        # Shift elements greater than current[key] to the right
        while j >= 0 and records[j][key] > current[key]:
            records[j + 1] = records[j]
            j -= 1
        records[j + 1] = current