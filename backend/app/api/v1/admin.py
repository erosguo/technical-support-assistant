from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.conversation import Conversation, Message
from app.models.knowledge import KnowledgeDocument
from app.models.ticket import Ticket
from app.models.user import User
from app.services.auth import require_role
from app.services.knowledge_discovery import discover_patterns_from_tickets
from app.services.quality_eval import evaluate_batch, evaluate_response

router = APIRouter()


class EvaluateRequest(BaseModel):
    query: str
    response: str


class BatchEvaluateRequest(BaseModel):
    responses: list[dict]


class QualityScoreResponse(BaseModel):
    relevance: int
    accuracy: int
    completeness: int
    clarity: int
    overall: float


@router.post("/admin/quality/evaluate", response_model=QualityScoreResponse)
async def quality_evaluate(
    req: EvaluateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role("admin", "manager")),
):
    score = await evaluate_response(query=req.query, response=req.response)
    return QualityScoreResponse(
        relevance=score.relevance,
        accuracy=score.accuracy,
        completeness=score.completeness,
        clarity=score.clarity,
        overall=score.overall,
    )


@router.post("/admin/quality/evaluate-batch", response_model=list[QualityScoreResponse])
async def quality_evaluate_batch(
    req: BatchEvaluateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role("admin", "manager")),
):
    scores = await evaluate_batch(responses=req.responses)
    return [
        QualityScoreResponse(
            relevance=s.relevance,
            accuracy=s.accuracy,
            completeness=s.completeness,
            clarity=s.clarity,
            overall=s.overall,
        )
        for s in scores
    ]


@router.post("/admin/knowledge/discover")
def knowledge_discover(
    min_tickets: int = Query(default=2),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role("admin", "l2_engineer")),
):
    return discover_patterns_from_tickets(session=session, min_tickets=min_tickets)


@router.get("/admin/stats")
def system_stats(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_role("admin", "manager")),
):
    total_conversations = session.query(func.count(Conversation.id)).scalar() or 0
    total_messages = session.query(func.count(Message.id)).scalar() or 0
    total_documents = session.query(func.count(KnowledgeDocument.id)).scalar() or 0
    total_tickets = session.query(func.count(Ticket.id)).scalar() or 0

    tickets_by_status = (
        session.query(Ticket.status, func.count(Ticket.id))
        .group_by(Ticket.status)
        .all()
    )
    tickets_by_status = dict(tickets_by_status)

    users_by_role = (
        session.query(User.role, func.count(User.id)).group_by(User.role).all()
    )
    users_by_role = dict(users_by_role)

    return {
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "total_documents": total_documents,
        "total_tickets": total_tickets,
        "tickets_by_status": tickets_by_status,
        "users_by_role": users_by_role,
    }
