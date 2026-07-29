from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_session
from app.services.ticket import (
    create_ticket as svc_create_ticket,
    get_ticket as svc_get_ticket,
    list_tickets as svc_list_tickets,
    update_ticket as svc_update_ticket,
    delete_ticket as svc_delete_ticket,
)

router = APIRouter()


class CreateTicketRequest(BaseModel):
    title: str
    description: str = ""
    priority: str = "medium"


class UpdateTicketRequest(BaseModel):
    status: str | None = None
    priority: str | None = None
    assigned_to: str | None = None


@router.post("/tickets")
def create_ticket(req: CreateTicketRequest, session: Session = Depends(get_session)):
    ticket = svc_create_ticket(
        session=session,
        title=req.title,
        description=req.description,
        priority=req.priority,
    )
    return {
        "id": str(ticket.id),
        "title": ticket.title,
        "description": ticket.description,
        "status": ticket.status,
        "priority": ticket.priority,
        "created_at": str(ticket.created_at),
        "updated_at": str(ticket.updated_at),
    }


@router.get("/tickets")
def list_tickets(session: Session = Depends(get_session)):
    tickets = svc_list_tickets(session)
    return [
        {
            "id": str(t.id),
            "title": t.title,
            "status": t.status,
            "priority": t.priority,
            "created_at": str(t.created_at),
            "updated_at": str(t.updated_at),
        }
        for t in tickets
    ]


@router.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str, session: Session = Depends(get_session)):
    ticket = svc_get_ticket(session, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {
        "id": str(ticket.id),
        "title": ticket.title,
        "description": ticket.description,
        "status": ticket.status,
        "priority": ticket.priority,
        "assigned_to": ticket.assigned_to,
        "created_at": str(ticket.created_at),
        "updated_at": str(ticket.updated_at),
    }


@router.patch("/tickets/{ticket_id}")
def update_ticket(
    ticket_id: str,
    req: UpdateTicketRequest,
    session: Session = Depends(get_session),
):
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    ticket = svc_update_ticket(session, ticket_id, **updates)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {
        "id": str(ticket.id),
        "title": ticket.title,
        "status": ticket.status,
        "priority": ticket.priority,
        "updated_at": str(ticket.updated_at),
    }


@router.delete("/tickets/{ticket_id}")
def delete_ticket(ticket_id: str, session: Session = Depends(get_session)):
    ticket = svc_get_ticket(session, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    svc_delete_ticket(session, ticket_id)
    return {"ok": True}
