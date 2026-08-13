"""
Validation script for algorithms – each case prints PASS/FAIL.
"""
from backend.algorithms.sorting import insertion_sort
from backend.algorithms.searching import binary_search, linear_search
from backend.algorithms.counting import insertion_sort_count, binary_search_count, linear_search_count

def run_test(case_name, expected, actual):
    if actual == expected:
        print(f"PASS: {case_name}")
        return True
    else:
        print(f"FAIL: {case_name} — expected {expected}, got {actual}")
        return False

def test_sorting():
    all_pass = True
    # Empty list
    arr = []
    insertion_sort(arr, "key")
    all_pass &= run_test("Insertion Sort - Empty List", [], arr)

    # Single element
    arr = [{"key": 5}]
    insertion_sort(arr, "key")
    all_pass &= run_test("Insertion Sort - Single Element", [{"key": 5}], arr)

    # Already sorted
    arr = [{"key": 1}, {"key": 2}, {"key": 3}]
    insertion_sort(arr, "key")
    all_pass &= run_test("Insertion Sort - Already Sorted", [{"key": 1}, {"key": 2}, {"key": 3}], arr)

    # Reverse sorted
    arr = [{"key": 3}, {"key": 2}, {"key": 1}]
    insertion_sort(arr, "key")
    all_pass &= run_test("Insertion Sort - Reverse Sorted", [{"key": 1}, {"key": 2}, {"key": 3}], arr)

    return all_pass

def test_binary_search():
    all_pass = True
    data = [{"title": "alpha"}, {"title": "beta"}, {"title": "gamma"}]
    insertion_sort(data, "title")  # ensure sorted

    # First
    idx = binary_search(data, "title", "alpha")
    all_pass &= run_test("Binary Search - First", 0, idx)

    # Middle
    idx = binary_search(data, "title", "beta")
    all_pass &= run_test("Binary Search - Middle", 1, idx)

    # Last
    idx = binary_search(data, "title", "gamma")
    all_pass &= run_test("Binary Search - Last", 2, idx)

    # Not Found
    idx = binary_search(data, "title", "delta")
    all_pass &= run_test("Binary Search - Not Found", -1, idx)

    return all_pass

def test_linear_search():
    all_pass = True
    data = [{"id": 10}, {"id": 20}, {"id": 30}]

    # Found
    idx = linear_search(data, "id", 20)
    all_pass &= run_test("Linear Search - Found", 1, idx)

    # Not Found
    idx = linear_search(data, "id", 99)
    all_pass &= run_test("Linear Search - Not Found", -1, idx)

    return all_pass

def test_counting():
    all_pass = True
    # Insertion sort count: returns int > 0 for non-empty
    arr = [{"prio": 3}, {"prio": 1}, {"prio": 2}]
    count = insertion_sort_count(arr, "prio")
    # Check return type is int and positive
    all_pass &= run_test("Counting - insertion_sort_count returns int", True, isinstance(count, int) and count > 0)
    # Also ensure array is sorted
    all_pass &= run_test("Counting - insertion_sort_count sorts correctly", [{"prio": 1}, {"prio": 2}, {"prio": 3}], arr)

    # Binary search count: returns dict with index and comparison_count
    sorted_data = [{"title": "a"}, {"title": "b"}, {"title": "c"}]
    res = binary_search_count(sorted_data, "title", "b")
    expected_dict = {"index": 1, "comparison_count": res["comparison_count"]}  # we can't know exact count, but verify structure
    all_pass &= run_test("Counting - binary_search_count returns dict with index", True, isinstance(res, dict) and "index" in res and "comparison_count" in res)
    all_pass &= run_test("Counting - binary_search_count index correct", 1, res["index"])
    all_pass &= run_test("Counting - binary_search_count comparison_count >0", True, res["comparison_count"] > 0)

    # Linear search count: check structure and count for not found
    res2 = linear_search_count(sorted_data, "title", "d")
    all_pass &= run_test("Counting - linear_search_count returns dict with index", True, isinstance(res2, dict) and "index" in res2 and "comparison_count" in res2)
    all_pass &= run_test("Counting - linear_search_count index -1 for not found", -1, res2["index"])
    all_pass &= run_test("Counting - linear_search_count comparison_count equals length (3)", 3, res2["comparison_count"])

    return all_pass

def run_all_tests():
    print("Running algorithm validation...")
    tests = [
        ("Sorting", test_sorting),
        ("Binary Search", test_binary_search),
        ("Linear Search", test_linear_search),
        ("Counting Wrappers", test_counting),
    ]
    overall = True
    for name, func in tests:
        print(f"\n--- {name} ---")
        overall &= func()
    if overall:
        print("\nALL TESTS PASSED")
    else:
        print("\nSome tests failed.")

if __name__ == "__main__":
    run_all_tests()