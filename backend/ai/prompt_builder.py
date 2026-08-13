"""
Build prompts for LLM (system and user messages).
"""
from typing import Tuple

def build_prompt(description: str) -> Tuple[str, str]:
    """
    Construct system and user messages for task parsing.

    Returns:
        (system_message, user_message)
    """
    system_message = (
        "You are an AI assistant that extracts task details from natural language descriptions. "
        "Given a description, identify the task title, priority (high/medium/low), and a due date hint. "
        "Return a JSON object with fields: title, priority, due_date_hint. "
        "If no priority is mentioned, set priority to 'medium'. "
        "If no due date hint is found, set due_date_hint to null."
    )
    user_message = f"Parse the following task description: '{description}'"
    return system_message, user_message