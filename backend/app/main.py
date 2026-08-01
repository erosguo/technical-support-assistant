from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import (
    admin,
    auth,
    chat,
    diagnosis,
    diagnosis_flow,
    external,
    health,
    knowledge,
    notification,
    ticket,
)

app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["knowledge"])
app.include_router(diagnosis.router, prefix="/api/v1", tags=["diagnosis"])
app.include_router(ticket.router, prefix="/api/v1", tags=["ticket"])
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(diagnosis_flow.router, prefix="/api/v1", tags=["diagnosis-flow"])
app.include_router(external.router, prefix="/api/v1", tags=["external"])
app.include_router(notification.router, prefix="/api/v1", tags=["notification"])
app.include_router(admin.router, prefix="/api/v1", tags=["admin"])
