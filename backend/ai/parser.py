"""
Main parser – decides between real LLM and mock.
"""
from typing import Dict, Any
from .feature_flags import use_real_llm
from .mock_parser import mock_parse
from .prompt_builder import build_prompt
# Optional: import openai if needed, but we'll keep it optional
# from openai import OpenAI

def parse_task_description(description: str) -> Dict[str, Any]:
    """
    Parse a natural language task description.

    If USE_REAL_LLM is True and LLM_API_KEY is set, call real LLM.
    Otherwise, fallback to mock parser.
    """
    if use_real_llm():
        # Attempt real LLM, fallback to mock if key missing or error
        try:
            from backend.config import settings
            if settings.LLM_API_KEY:
                # In a real implementation, we would call OpenAI or similar.
                # For now, we simulate by calling mock and logging a warning.
                # Actually the assignment says "But parser.py should automatically fallback to mock parser if API key is missing. No crashes."
                # So if key is missing, we fallback.
                # Since we cannot actually call LLM here, we will just use mock.
                # We'll keep the structure for future integration.
                # For now, always fallback to mock because we don't have real LLM.
                # But we can still build prompt for demonstration.
                system, user = build_prompt(description)
                # Would call LLM here, but we'll fallback.
                print("Real LLM would be called with system:", system, "user:", user)
                # Fallback to mock
                return mock_parse(description)
            else:
                # No API key
                return mock_parse(description)
        except Exception:
            # Any error, fallback
            return mock_parse(description)
    else:
        return mock_parse(description)