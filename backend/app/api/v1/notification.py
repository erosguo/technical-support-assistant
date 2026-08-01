from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.user import User
from app.services.auth import get_current_user, require_role
from app.services.notification import notify_escalation, send_notification

router = APIRouter()


class SendNotificationRequest(BaseModel):
    provider: str
    webhook_url: str
    title: str
    content: str


class EscalationRequest(BaseModel):
    provider: str
    webhook_url: str
    ticket_title: str
    ticket_description: str


@router.post("/notification/send")
def send(
    req: SendNotificationRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return send_notification(
        provider=req.provider,
        webhook_url=req.webhook_url,
        title=req.title,
        content=req.content,
    )


@router.post("/notification/escalation")
def escalation(
    req: EscalationRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role("admin", "manager", "l2_engineer")),
):
    return notify_escalation(
        provider=req.provider,
        webhook_url=req.webhook_url,
        ticket_title=req.ticket_title,
        ticket_description=req.ticket_description,
    )
