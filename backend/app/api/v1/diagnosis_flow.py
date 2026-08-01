"""Diagnosis flow API router — Phase 2 Task 2.7."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.diagnosis_flow import DiagnosisFlow
from app.models.user import User
from app.services.auth import get_current_user

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class FlowStep(BaseModel):
    id: str
    title: str
    description: str = ""
    conditions: list[dict] = []
    next_step: str | None = None


class CreateFlowRequest(BaseModel):
    name: str
    description: str = ""
    steps: list[FlowStep]


class UpdateFlowRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    steps: list[FlowStep] | None = None
    is_active: bool | None = None


class FlowResponse(BaseModel):
    id: str
    name: str
    description: str | None
    steps: list
    version: int
    is_active: bool


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/diagnosis/flows", response_model=FlowResponse, status_code=201)
def create_flow(
    req: CreateFlowRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    flow = DiagnosisFlow(
        name=req.name,
        description=req.description,
        steps=[s.model_dump() for s in req.steps],
    )
    session.add(flow)
    session.commit()
    return FlowResponse(
        id=str(flow.id),
        name=flow.name,
        description=flow.description,
        steps=flow.steps,
        version=flow.version,
        is_active=flow.is_active,
    )


@router.get("/diagnosis/flows", response_model=list[FlowResponse])
def list_flows(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    flows = session.query(DiagnosisFlow).order_by(DiagnosisFlow.created_at.desc()).all()
    return [
        FlowResponse(
            id=str(f.id),
            name=f.name,
            description=f.description,
            steps=f.steps,
            version=f.version,
            is_active=f.is_active,
        )
        for f in flows
    ]


@router.get("/diagnosis/flows/{flow_id}", response_model=FlowResponse)
def get_flow(
    flow_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    flow = session.get(DiagnosisFlow, flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    return FlowResponse(
        id=str(flow.id),
        name=flow.name,
        description=flow.description,
        steps=flow.steps,
        version=flow.version,
        is_active=flow.is_active,
    )


@router.patch("/diagnosis/flows/{flow_id}", response_model=FlowResponse)
def update_flow(
    flow_id: str,
    req: UpdateFlowRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    flow = session.get(DiagnosisFlow, flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    if req.name is not None:
        flow.name = req.name
    if req.description is not None:
        flow.description = req.description
    if req.steps is not None:
        flow.steps = [s.model_dump() for s in req.steps]
        flow.version += 1
    if req.is_active is not None:
        flow.is_active = req.is_active
    session.commit()
    return FlowResponse(
        id=str(flow.id),
        name=flow.name,
        description=flow.description,
        steps=flow.steps,
        version=flow.version,
        is_active=flow.is_active,
    )


@router.delete("/diagnosis/flows/{flow_id}", status_code=204)
def delete_flow(
    flow_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    flow = session.get(DiagnosisFlow, flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    session.delete(flow)
    session.commit()
    return None


@router.post("/diagnosis/flows/{flow_id}/activate", response_model=FlowResponse)
def activate_flow(
    flow_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # Deactivate all other flows, activate the selected one
    session.query(DiagnosisFlow).filter(DiagnosisFlow.is_active.is_(True)).update(
        {"is_active": False}
    )
    flow = session.get(DiagnosisFlow, flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    flow.is_active = True
    session.commit()
    return FlowResponse(
        id=str(flow.id),
        name=flow.name,
        description=flow.description,
        steps=flow.steps,
        version=flow.version,
        is_active=flow.is_active,
    )
