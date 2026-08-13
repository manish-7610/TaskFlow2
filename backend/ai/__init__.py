

"""
AI module for parsing natural language task descriptions.
"""
from .parser import parse_task_description
from .mock_parser import mock_parse
from .feature_flags import use_real_llm