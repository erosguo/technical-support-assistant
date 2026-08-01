"""F25 - Knowledge Auto-Discovery.

Analyzes resolved/closed tickets to automatically extract recurring error
patterns and suggested solutions, persisting them as ``ErrorPattern`` rows.
"""

import asyncio
import re
from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.error_pattern import ErrorPattern
from app.models.ticket import Ticket

# Common English stop words excluded from keyword extraction.
STOP_WORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "if",
    "then",
    "than",
    "so",
    "no",
    "not",
    "can",
    "will",
    "just",
    "should",
    "would",
    "could",
    "may",
    "might",
    "must",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "from",
    "up",
    "about",
    "into",
    "through",
    "during",
    "before",
    "after",
    "above",
    "below",
    "between",
    "this",
    "that",
    "these",
    "those",
    "it",
    "its",
    "as",
    "they",
    "them",
    "their",
    "there",
    "here",
    "when",
    "where",
    "why",
    "how",
    "all",
    "any",
    "both",
    "each",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "only",
    "own",
    "same",
    "very",
    "s",
    "t",
}

_BLOCK_SEPARATOR = re.compile(r"\n\s*---\s*\n")
_PATTERN_LINE = re.compile(r"PATTERN:\s*(.+)", re.IGNORECASE)
_SOLUTION_LINE = re.compile(r"SOLUTION:\s*(.+)", re.IGNORECASE)
_SEVERITY_LINE = re.compile(r"SEVERITY:\s*([A-Za-z]+)", re.IGNORECASE)
_WORD_TOKEN = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]+")


def discover_pattern_keywords(tickets: list) -> list[dict]:
    """Extract the most common meaningful words from ticket titles/descriptions.

    Returns up to 5 patterns whose frequency is greater than 1.
    """
    counter: Counter = Counter()
    for ticket in tickets:
        text = f"{ticket.title or ''} {ticket.description or ''}"
        for word in _WORD_TOKEN.findall(text.lower()):
            if word in STOP_WORDS or len(word) < 3:
                continue
            counter[word] += 1

    patterns: list[dict] = []
    for word, count in counter.most_common(5):
        if count > 1:
            patterns.append(
                {
                    "pattern": word,
                    "solution": "Pending analysis",
                    "severity": "low",
                    "category": "auto-discovered",
                }
            )
    return patterns


def _build_llm_prompt(tickets: list) -> list[dict]:
    summaries = "\n".join(f"- [{t.status}] {t.title}: {t.description}" for t in tickets)
    system = (
        "You are a knowledge discovery assistant. Analyze the resolved/closed "
        "tickets below and identify recurring error patterns. For each pattern, "
        "suggest a solution and a severity. Respond strictly in this format, "
        "one block per pattern, blocks separated by a line containing only "
        "'---':\n"
        "PATTERN: <pattern text>\n"
        "SOLUTION: <solution text>\n"
        "SEVERITY: <low|medium|high|critical>"
    )
    user = f"Tickets:\n{summaries}"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _parse_llm_response(text: str) -> list[dict]:
    """Parse the structured LLM response into pattern dicts."""
    discovered: list[dict] = []
    if not text:
        return discovered

    for block in _BLOCK_SEPARATOR.split(text.strip()):
        pattern_match = _PATTERN_LINE.search(block)
        if not pattern_match:
            continue
        solution_match = _SOLUTION_LINE.search(block)
        severity_match = _SEVERITY_LINE.search(block)
        discovered.append(
            {
                "pattern": pattern_match.group(1).strip(),
                "solution": (
                    solution_match.group(1).strip()
                    if solution_match
                    else "Pending analysis"
                ),
                "severity": (
                    severity_match.group(1).strip().lower()
                    if severity_match
                    else "medium"
                ),
                "category": "auto-discovered",
            }
        )
    return discovered


def discover_patterns_from_tickets(
    session: Session, llm=None, min_tickets: int = 2
) -> list[dict]:
    """Discover recurring error patterns from resolved/closed tickets.

    Fetches tickets whose status is ``resolved`` or ``closed``. If fewer than
    ``min_tickets`` are found, returns an empty list. When ``llm`` is None,
    falls back to simple keyword extraction. Each discovered pattern is
    persisted as an ``ErrorPattern`` (skipping patterns whose text already
    exists). Returns a list of dicts describing each pattern and whether it
    was newly created.
    """
    stmt = select(Ticket).where(Ticket.status.in_(("resolved", "closed")))
    tickets = list(session.execute(stmt).scalars().all())

    if len(tickets) < min_tickets:
        return []

    if llm is None:
        discovered = discover_pattern_keywords(tickets)
    else:
        messages = _build_llm_prompt(tickets)
        response = asyncio.run(llm.chat(messages))
        discovered = _parse_llm_response(response)

    results: list[dict] = []
    for item in discovered:
        pattern_text = item["pattern"]
        existing = (
            session.execute(
                select(ErrorPattern).where(ErrorPattern.pattern == pattern_text)
            )
            .scalars()
            .first()
        )

        if existing:
            results.append(
                {
                    "pattern": existing.pattern,
                    "solution": existing.solution,
                    "severity": existing.severity,
                    "category": existing.category,
                    "created": False,
                }
            )
            continue

        ep = ErrorPattern(
            pattern=pattern_text,
            solution=item.get("solution"),
            severity=item.get("severity", "medium"),
            category=item.get("category", "auto-discovered"),
        )
        session.add(ep)
        session.flush()
        results.append(
            {
                "pattern": ep.pattern,
                "solution": ep.solution,
                "severity": ep.severity,
                "category": ep.category,
                "created": True,
            }
        )

    session.commit()
    return results
