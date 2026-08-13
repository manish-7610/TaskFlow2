"""
mock_parser.py – Intelligent offline rule-based task parser.

No API calls, no network. Fully offline.

Given a natural-language input string it produces:
  title         – short, clean (2-5 meaningful words), Title Cased
  description   – a professional, context-aware sentence (never a raw copy)
  priority      – "high" | "medium" | "low"
  due_date_hint – a date phrase extracted from the input, or None
"""
import re
from typing import Dict, Any, Optional, List, Tuple

# ── Priority keyword maps ─────────────────────────────────────────────────────
PRIORITY_HIGH_WORDS = [
    "urgent", "urgently", "asap", "immediately", "right away",
    "critical", "blocker", "blocking", "top priority", "high priority",
    "must", "right now", "as soon as possible", "emergency",
]
PRIORITY_MEDIUM_WORDS = [
    "important", "should", "need to", "needs to", "required",
]
PRIORITY_LOW_WORDS = [
    "whenever", "low priority", "not urgent", "can wait", "no rush",
    "someday", "eventually", "optional", "later", "when free", "if possible",
]

# ── Due date phrases (longest first to avoid substring collisions) ────────────
DATE_PHRASES = [
    "next monday", "next tuesday", "next wednesday", "next thursday",
    "next friday", "next saturday", "next sunday", "next week", "next month",
    "this week", "this monday", "this tuesday", "this wednesday",
    "this thursday", "this friday", "end of week", "end of month",
    "tomorrow", "today",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
]

# ── Stop-words for title extraction ───────────────────────────────────────────
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "up", "about", "into", "through", "during",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "could", "should", "may", "might",
    "shall", "can", "need", "i", "me", "my", "we", "us", "our", "you", "your",
    "it", "its", "this", "that", "these", "those",
    "make", "create", "write", "build", "complete", "finish", "learn",
    "study", "practice", "prepare", "review", "update", "fix", "add",
    "using", "use", "based", "via", "want",
}

# ── Domain → description template ────────────────────────────────────────────
#
# Each entry: (keyword_triggers, action_verb, subtopics_string)
# Templates produce:  "{verb} {subtopics_string}."
# The title noun-phrase replaces {topic} when the template has one.
#
# Ordering matters: more specific entries must come before generic ones.
#
_DOMAIN_TEMPLATES: List[Tuple[List[str], str, str]] = [
    # Programming languages & runtimes
    (["python", "django", "flask", "fastapi"],
     "Study",
     "{topic} fundamentals including syntax, data structures, OOP and standard libraries."),
    (["javascript", "typescript", "nodejs", "node.js", "node js"],
     "Study",
     "{topic} including ES6+ features, asynchronous programming, modules and best practices."),
    (["react", "vue", "angular", "svelte", "nextjs", "next.js"],
     "Learn",
     "{topic} concepts including components, props, state management, lifecycle and routing."),
    (["docker", "kubernetes", "k8s", "container"],
     "Learn",
     "{topic} fundamentals including images, containers, networking, volumes and orchestration."),
    (["sql", "database", "dbms", "mysql", "postgresql", "postgres", "sqlite", "mongodb"],
     "Revise",
     "{topic} concepts including queries, normalization, indexing, transactions and optimization."),
    (["git", "github", "version control"],
     "Practice",
     "{topic} workflows including branching, merging, rebasing, pull requests and collaboration."),
    (["linux", "bash", "shell", "terminal", "unix"],
     "Learn",
     "{topic} essentials including file system navigation, permissions, scripting and process management."),
    (["aws", "azure", "gcp", "cloud", "devops", "ci/cd", "cicd"],
     "Study",
     "{topic} practices including infrastructure setup, deployment pipelines and monitoring."),
    (["machine learning", "ml", "deep learning", "ai", "neural"],
     "Study",
     "{topic} concepts including model training, evaluation, feature engineering and deployment."),
    (["html", "css", "sass", "scss", "tailwind", "bootstrap"],
     "Practice",
     "{topic} including semantic markup, responsive layout, flexbox, grid and accessibility."),
    # Interview & study
    (["interview", "prep", "preparation"],
     "Prepare",
     "for {topic} by reviewing key concepts, practising problems and studying common questions."),
    (["exam", "test", "quiz", "mock"],
     "Prepare",
     "for the {topic} by reviewing syllabus topics and solving practice questions."),
    # General software / project tasks
    (["portfolio", "website", "landing page", "webpage"],
     "Design and develop",
     "a responsive {topic} showcasing projects, skills and contact information."),
    (["api", "rest", "graphql", "endpoint"],
     "Design and implement",
     "the {topic} including endpoint definitions, authentication, validation and documentation."),
    (["unit test", "testing", "test", "tdd", "jest", "pytest"],
     "Write",
     "{topic} covering edge cases, mocks and assertions to ensure code correctness."),
    (["refactor", "clean up", "cleanup", "improve"],
     "Refactor",
     "the {topic} to improve readability, reduce duplication and follow best practices."),
    (["deploy", "deployment", "release", "publish"],
     "Deploy",
     "the {topic} to the target environment including configuration, health checks and monitoring."),
    (["documentation", "docs", "readme"],
     "Write",
     "clear {topic} covering setup, usage, API reference and contribution guidelines."),
    (["bug", "fix", "issue", "error", "crash", "broken"],
     "Investigate and fix",
     "the {topic} by identifying the root cause, applying a patch and adding regression tests."),
    (["migration", "migrate", "upgrade"],
     "Plan and execute",
     "the {topic} including schema changes, data validation and rollback procedures."),
    (["presentation", "slides", "demo", "showcase"],
     "Prepare",
     "the {topic} with key points, visuals and a live demonstration walkthrough."),
    (["sprint", "planning", "standup", "meeting", "scrum", "kanban"],
     "Organise",
     "the {topic} by defining goals, assigning tasks and updating the project board."),
    (["research", "investigate", "explore", "compare", "evaluate"],
     "Research",
     "options for {topic} and summarise findings with a recommendation."),
    (["read", "reading", "book", "article", "blog", "paper"],
     "Read and summarise",
     "the {topic} extracting key takeaways and actionable insights."),
    (["setup", "set up", "install", "configure", "initialise", "initialize"],
     "Set up",
     "the {topic} including installation, configuration and initial testing."),
    (["design", "mockup", "wireframe", "prototype", "ui", "ux"],
     "Design",
     "the {topic} including wireframes, user flow, component layout and visual style."),
    (["code review", "pr review", "pull request"],
     "Review",
     "the {topic} checking for correctness, style, performance and security issues."),
    (["data", "dataset", "etl", "pipeline", "analytics"],
     "Build",
     "the {topic} pipeline including data ingestion, transformation, validation and output."),
]

# ── Filler openers to strip from description inputs ───────────────────────────
_FILLER_PREFIX = re.compile(
    r'^(please\s+|kindly\s+|i\s+(need|want|have)\s+to\s+|'
    r'we\s+(need|should|have)\s+to\s+|need\s+to\s+|have\s+to\s+|want\s+to\s+)',
    re.IGNORECASE,
)

# ── Action verbs to strip from the beginning of the title base text ───────────
_LEADING_VERBS = re.compile(
    r'^(learn|study|build|create|write|fix|prepare|practice|practise|'
    r'design|implement|deploy|refactor|review|update|research|read|'
    r'setup|set up|configure|explore|complete|finish|develop|make|'
    r'investigate|analyse|analyze|organise|organize)\s+',
    re.IGNORECASE,
)


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _title_case(text: str) -> str:
    """Title-case, preserving existing all-caps acronyms (HTML, CSS, API…)."""
    words = text.split()
    out = []
    for w in words:
        out.append(w if (w.upper() == w and len(w) > 1) else w.capitalize())
    return ' '.join(out)


def _clean_title_base(text: str) -> str:
    """
    Strip date phrases, priority words, time connectors and leading verbs
    from *text* to leave the core noun/topic phrase.
    """
    t = text

    # Remove date phrases
    for phrase in DATE_PHRASES:
        t = re.sub(r'\b' + re.escape(phrase) + r'\b', '', t, flags=re.IGNORECASE)

    # Remove priority keywords (longest first)
    for kw in sorted(PRIORITY_HIGH_WORDS + PRIORITY_MEDIUM_WORDS + PRIORITY_LOW_WORDS,
                     key=len, reverse=True):
        t = re.sub(r'\b' + re.escape(kw) + r'\b', '', t, flags=re.IGNORECASE)

    # Remove "in N days/weeks/hours", "by X", "within Y"
    t = re.sub(r'\b(in|within|over)\s+\d+\s+\w+\b', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\b(by|before|after|for|during)\s+(the\s+)?\w+\b', '', t, flags=re.IGNORECASE)

    # Strip punctuation artefacts and collapse spaces
    t = re.sub(r'[\s,:;!?–\-]+$', '', t.strip())
    t = re.sub(r'^[\s,:;!?–\-]+', '', t.strip())
    t = re.sub(r'\s{2,}', ' ', t).strip()

    return t


def _extract_title(base: str, max_words: int = 5, original_text: str = "") -> str:
    """Extract up to *max_words* content words from *base*, Title Cased.

    If only one content word survives, we augment the title with a contextual
    qualifier (the stripped leading verb or a domain-specific suffix) so the
    minimum title length is two words.
    """
    # Capture the leading verb before stripping it (used as fallback qualifier)
    verb_match = _LEADING_VERBS.match(base)
    leading_verb = verb_match.group(1).capitalize() if verb_match else ""

    # Strip the leading verb
    trimmed = _LEADING_VERBS.sub('', base).strip()

    words = trimmed.split()
    kept = []
    for w in words:
        clean = re.sub(r'[^a-zA-Z0-9]', '', w).lower()
        if clean and clean not in STOP_WORDS:
            kept.append(w)
        if len(kept) >= max_words:
            break

    if not kept:
        kept = words[:max_words]

    title = _title_case(' '.join(kept)) if kept else ""

    # ── Guarantee at least 2 words ───────────────────────────────────────────
    if len(title.split()) < 2:
        lower_orig = original_text.lower() if original_text else base.lower()

        # Pick a domain-aware suffix
        if any(kw in lower_orig for kw in ["docker", "kubernetes", "k8s", "container"]):
            suffix = "Fundamentals"
        elif any(kw in lower_orig for kw in ["deploy", "deployment", "release", "publish"]):
            suffix = "Deployment"
        elif any(kw in lower_orig for kw in ["docs", "documentation", "readme"]):
            suffix = "Review"
        elif any(kw in lower_orig for kw in ["react", "vue", "angular"]):
            suffix = "Basics"
        elif any(kw in lower_orig for kw in ["python", "javascript", "typescript"]):
            suffix = "Fundamentals"
        elif any(kw in lower_orig for kw in ["sql", "database", "dbms"]):
            suffix = "Preparation"
        elif any(kw in lower_orig for kw in ["interview", "exam", "quiz"]):
            suffix = "Preparation"
        elif leading_verb:
            # e.g. "Learn Docker" → leading_verb="Learn"
            suffix = leading_verb
            # Swap order: put leading verb first only if it isn't already the title
            if suffix.lower() != title.lower():
                title = f"{title} {suffix}"
                return title
        else:
            suffix = "Task"

        title = f"{title} {suffix}" if title else suffix

    return title


def _match_domain(lower_input: str) -> Optional[Tuple[str, str, str]]:
    """
    Return the first matching (triggers, verb, template) entry from
    _DOMAIN_TEMPLATES, or None if no domain is recognised.
    """
    for triggers, verb, template in _DOMAIN_TEMPLATES:
        for kw in triggers:
            if kw in lower_input:
                return verb, template, kw
    return None


def _build_description(
    original: str,
    title: str,
    due_hint: Optional[str],
    priority: str,
) -> str:
    """
    Generate a professional one-sentence description.

    Strategy:
    1. Try to match a domain template and fill it with the extracted title.
    2. If no domain match, compose a generic sentence from the cleaned input.
    3. Append due-date and high-priority suffixes when present.
    """
    lower = original.lower()

    match = _match_domain(lower)
    if match:
        verb, template, _kw = match
        # Fill {topic} placeholder with the extracted title
        desc_body = template.replace("{topic}", title)
        # Ensure the sentence always starts with the action verb
        # (templates beginning with {topic} after replacement need the verb prepended)
        if desc_body[0].islower() or desc_body.startswith(title):
            desc = f"{verb} {desc_body}"
        else:
            desc = desc_body
    else:
        # Generic: sentence-case the filler-stripped original
        cleaned = _FILLER_PREFIX.sub('', original).strip()
        desc = cleaned[:1].upper() + cleaned[1:] if cleaned else title
        if not desc.endswith('.'):
            desc += '.'

    # Append due-date context if not already present
    if due_hint and due_hint.lower() not in desc.lower():
        desc = desc.rstrip('. ') + f', due {due_hint}.'

    # Append priority hint for high tasks when not obvious
    if priority == "high" and not any(w in desc.lower() for w in ("urgent", "critical", "asap", "immediately")):
        desc = desc.rstrip('. ') + ' (high priority).'

    # Ensure sentence ends with a period
    if not desc.endswith('.'):
        desc += '.'

    return desc


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def mock_parse(text: str) -> Dict[str, Any]:
    """
    Parse a natural-language task description offline.

    Returns
    -------
    dict with keys:
      title         – str, short Title Cased noun phrase (2-5 words)
      description   – str, professional context-aware sentence
      priority      – "low" | "medium" | "high"
      due_date_hint – str | None
    """
    text = text.strip()
    if not text:
        return {
            "title": "Untitled Task",
            "description": None,
            "priority": "medium",
            "due_date_hint": None,
        }

    lower = text.lower()

    # 1. Priority
    priority = "medium"
    if any(kw in lower for kw in PRIORITY_HIGH_WORDS):
        priority = "high"
    elif any(kw in lower for kw in PRIORITY_LOW_WORDS):
        priority = "low"
    elif any(kw in lower for kw in PRIORITY_MEDIUM_WORDS):
        priority = "medium"

    # 2. Due date
    due_date_hint: Optional[str] = None
    for phrase in DATE_PHRASES:
        if re.search(r'\b' + re.escape(phrase) + r'\b', lower):
            due_date_hint = phrase
            break

    # 3. Title
    base = _clean_title_base(text)
    title = _extract_title(base, max_words=5, original_text=text) or "Untitled Task"

    # 4. Description
    description = _build_description(text, title, due_date_hint, priority)

    return {
        "title": title,
        "description": description,
        "priority": priority,
        "due_date_hint": due_date_hint,
    }
