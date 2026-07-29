from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from app.models.ticket import Ticket


def create_ticket(
    session: Session,
    title: str,
    description: str,
    priority: str = "medium",
    source: str = "chat",
    assigned_to: str = None,
    conversation_id: str = None,
) -> Ticket:
    ticket = Ticket(
        title=title,
        description=description,
        priority=priority,
        source=source,
        assigned_to=assigned_to,
        conversation_id=conversation_id,
    )
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket


def get_ticket(session: Session, ticket_id: str) -> Ticket | None:
    return session.get(Ticket, ticket_id)


def list_tickets(
    session: Session,
    status: str = None,
    priority: str = None,
    limit: int = 50,
) -> list[Ticket]:
    stmt = select(Ticket).order_by(desc(Ticket.updated_at))
    if status:
        stmt = stmt.where(Ticket.status == status)
    if priority:
        stmt = stmt.where(Ticket.priority == priority)
    result = session.execute(stmt.limit(limit))
    return list(result.scalars().all())


def update_ticket(session: Session, ticket_id: str, **updates) -> Ticket | None:
    ticket = session.get(Ticket, ticket_id)
    if not ticket:
        return None
    for key, value in updates.items():
        if hasattr(ticket, key):
            setattr(ticket, key, value)
    session.commit()
    session.refresh(ticket)
    return ticket


def delete_ticket(session: Session, ticket_id: str) -> bool:
    ticket = session.get(Ticket, ticket_id)
    if not ticket:
        return False
    session.delete(ticket)
    session.commit()
    return True
