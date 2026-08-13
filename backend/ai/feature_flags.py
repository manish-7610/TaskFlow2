"""
Feature flags for the AI module.
"""
from ..config import settings


def use_real_llm() -> bool:
    """Return True when the real LLM API should be used instead of the mock parser."""
    return getattr(settings, "USE_REAL_LLM", False)
