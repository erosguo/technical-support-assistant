from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.user import User
from app.services.auth import require_role
from app.services.external_ticket import (
    get_external_ticket_config,
    sync_ticket_to_external,
)

router = APIRouter()


class SyncTicketRequest(BaseModel):
    ticket_id: str
    provider: str
    config: dict | None = None


@router.post("/external/tickets/sync")
def sync_ticket(
    req: SyncTicketRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role("admin", "l2_engineer")),
):
    try:
        result = sync_ticket_to_external(
            session=session,
            ticket_id=req.ticket_id,
            provider=req.provider,
            config=req.config,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/external/tickets/config/{provider}")
def get_config(
    provider: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role("admin")),
):
    try:
        config = get_external_ticket_config(session, provider)
        return config
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
