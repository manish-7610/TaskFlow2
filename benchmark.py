"""
Benchmark sorting and searching algorithms and save results as a table.
"""
from backend.algorithms.sorting import insertion_sort
from backend.algorithms.counting import (
    insertion_sort_count,
    binary_search_count,
    linear_search_count,
)
from backend.algorithms.benchmark_utils import generate_tasks
from backend.algorithms.searching import binary_search, linear_search


def run_benchmarks():
    results = []
    table = []
    table.append("+---------------------+---------------+")
    table.append("| Algorithm           | Comparisons   |")
    table.append("+---------------------+---------------+")

    # Sorting benchmark
    for size in [10, 500, 3000]:
        tasks = generate_tasks(size)
        priority_map = {"low": 1, "medium": 2, "high": 3}
        for task in tasks:
            task["priority_num"] = priority_map[task["priority"]]

        tasks_copy = [t.copy() for t in tasks]
        comparisons = insertion_sort_count(tasks_copy, "priority_num")
        results.append(f"Sorting {size} tasks: {comparisons} comparisons")
        table.append(f"| Sorting {size:5d} tasks | {comparisons:12d}   |")

    # Searching benchmark (on 1000 tasks sorted by title)
    tasks_for_search = generate_tasks(1000)
    insertion_sort(tasks_for_search, "title")

    import random
    if tasks_for_search:
        target = random.choice(tasks_for_search)["title"]

        # Binary search
        bin_res = binary_search_count(tasks_for_search, "title", target)
        results.append(f"Binary search for '{target}': index={bin_res['index']}, comparisons={bin_res['comparison_count']}")
        table.append(f"| Binary search       | {bin_res['comparison_count']:12d}   |")

        # Linear search
        lin_res = linear_search_count(tasks_for_search, "title", target)
        results.append(f"Linear search for '{target}': index={lin_res['index']}, comparisons={lin_res['comparison_count']}")
        table.append(f"| Linear search       | {lin_res['comparison_count']:12d}   |")

    table.append("+---------------------+---------------+")

    # Print and save
    for line in table:
        print(line)
    with open("benchmark_results.txt", "w") as f:
        f.write("Benchmark Results\n")
        f.write("=" * 40 + "\n")
        for line in table:
            f.write(line + "\n")
        f.write("\nDetailed:\n")
        for line in results:
            f.write(line + "\n")
    print("Benchmark results saved to benchmark_results.txt")


if __name__ == "__main__":
    run_benchmarks()