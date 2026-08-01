from types import SimpleNamespace

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.error_pattern import ErrorPattern
from app.services.knowledge_discovery import (
    discover_pattern_keywords,
    discover_patterns_from_tickets,
)
from app.services.ticket import create_ticket, update_ticket


def _make_resolved_ticket(session: Session, title: str, description: str):
    ticket = create_ticket(session=session, title=title, description=description)
    update_ticket(session=session, ticket_id=ticket.id, status="resolved")
    return ticket


class _MockLLM:
    """Simple async LLM mock returning a canned response string."""

    def __init__(self, response: str):
        self._response = response
        self.calls: list = []

    async def chat(self, messages, **kwargs) -> str:
        self.calls.append(messages)
        return self._response


class TestKnowledgeDiscovery:
    def test_discover_no_tickets_returns_empty(self, db_session: Session):
        results = discover_patterns_from_tickets(db_session)
        assert results == []

    def test_discover_fewer_than_min_returns_empty(self, db_session: Session):
        _make_resolved_ticket(db_session, "Single issue", "Only one ticket here")
        results = discover_patterns_from_tickets(db_session, min_tickets=2)
        assert results == []

    def test_discover_without_llm_creates_patterns(self, db_session: Session):
        _make_resolved_ticket(
            db_session, "Database connection failed", "Cannot connect to database"
        )
        _make_resolved_ticket(
            db_session, "Database timeout", "Database query timed out"
        )
        _make_resolved_ticket(
            db_session, "Database error", "Database returned an error"
        )

        results = discover_patterns_from_tickets(db_session)

        assert len(results) > 0
        patterns = [r["pattern"] for r in results]
        assert "database" in patterns
        assert all(r["created"] is True for r in results)
        assert all(r["category"] == "auto-discovered" for r in results)

        db_patterns = db_session.execute(select(ErrorPattern)).scalars().all()
        db_texts = {ep.pattern for ep in db_patterns}
        assert "database" in db_texts

    def test_discover_with_mock_llm(self, db_session: Session):
        _make_resolved_ticket(db_session, "Network outage", "Service unreachable")
        _make_resolved_ticket(db_session, "Login failure", "Users cannot log in")

        llm_response = (
            "PATTERN: Connection timeout\n"
            "SOLUTION: Check network connectivity and increase timeout\n"
            "SEVERITY: high\n"
            "---\n"
            "PATTERN: Authentication failure\n"
            "SOLUTION: Verify credentials and token validity\n"
            "SEVERITY: medium"
        )
        llm = _MockLLM(response=llm_response)

        results = discover_patterns_from_tickets(db_session, llm=llm)

        assert len(results) == 2
        assert all(r["created"] is True for r in results)
        by_pattern = {r["pattern"]: r for r in results}
        assert "Connection timeout" in by_pattern
        assert by_pattern["Connection timeout"]["solution"].startswith("Check network")
        assert by_pattern["Connection timeout"]["severity"] == "high"
        assert by_pattern["Authentication failure"]["severity"] == "medium"
        assert len(llm.calls) == 1

    def test_discover_skips_existing_patterns(self, db_session: Session):
        _make_resolved_ticket(
            db_session, "Database connection failed", "Cannot connect to database"
        )
        _make_resolved_ticket(
            db_session, "Database timeout", "Database query timed out"
        )
        _make_resolved_ticket(
            db_session, "Database error", "Database returned an error"
        )

        first = discover_patterns_from_tickets(db_session)
        assert len(first) > 0
        assert all(r["created"] is True for r in first)

        second = discover_patterns_from_tickets(db_session)
        assert len(second) == len(first)
        assert all(r["created"] is False for r in second)

        for r in first:
            existing = (
                db_session.execute(
                    select(ErrorPattern).where(ErrorPattern.pattern == r["pattern"])
                )
                .scalars()
                .all()
            )
            assert len(existing) == 1

    def test_discover_keyword_extraction(self):
        tickets = [
            SimpleNamespace(
                title="Database connection failed", description="Database down"
            ),
            SimpleNamespace(title="Database timeout", description="Database slow"),
            SimpleNamespace(title="Database error", description="Database crashed"),
        ]

        results = discover_pattern_keywords(tickets)

        assert len(results) > 0
        patterns = [r["pattern"] for r in results]
        assert "database" in patterns
        assert all(r["solution"] == "Pending analysis" for r in results)
        assert all(r["severity"] == "low" for r in results)
        assert all(r["category"] == "auto-discovered" for r in results)
        assert len(results) <= 5
        for r in results:
            assert len(r["pattern"]) >= 3
