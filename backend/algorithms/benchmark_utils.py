"""
Benchmark utilities: generate realistic task datasets.
"""
import random
import string
from typing import List, Dict, Any

PRIORITIES = ["low", "medium", "high"]


def generate_tasks(n: int) -> List[Dict[str, Any]]:
    """
    Generate a list of n task dictionaries with random data.

    Each task has fields:
    - id: sequential integer starting from 1
    - title: random string
    - priority: one of 'low', 'medium', 'high'
    - project_id: random integer 1-5
    """
    tasks = []
    for i in range(1, n + 1):
        title_len = random.randint(5, 20)
        title = ''.join(random.choices(string.ascii_letters, k=title_len))
        priority = random.choice(PRIORITIES)
        project_id = random.randint(1, 5)
        tasks.append({
            "id": i,
            "title": title,
            "priority": priority,
            "project_id": project_id,
        })
    return tasks