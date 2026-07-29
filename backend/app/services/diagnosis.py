import re
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.error_pattern import ErrorPattern

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def match_errors(session: Session, error_text: str) -> list[dict]:
    result = session.execute(select(ErrorPattern))
    patterns = result.scalars().all()

    matches = []
    for ep in patterns:
        try:
            matched = bool(re.search(ep.pattern, error_text, re.IGNORECASE))
        except re.error:
            matched = ep.pattern.lower() in error_text.lower()

        if matched:
            matches.append(
                {
                    "id": str(ep.id),
                    "pattern": ep.pattern,
                    "solution": ep.solution,
                    "severity": ep.severity,
                    "category": ep.category,
                    "tags": ep.tags or [],
                }
            )

    matches.sort(key=lambda m: SEVERITY_ORDER.get(m["severity"], 99))
    return matches
