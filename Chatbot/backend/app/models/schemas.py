from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    session_id: str | None = None
    tenant_id: str = "default"
    use_rag: bool | None = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    sources: list[dict] = []
    handoff: bool = False


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionOut(BaseModel):
    id: str
    tenant_id: str
    created_at: datetime
    messages: list[MessageOut] = []

    model_config = {"from_attributes": True}


class DocumentOut(BaseModel):
    id: str
    filename: str
    title: str
    chunk_count: int
    status: str
    created_at: datetime
    error_message: str | None = None

    model_config = {"from_attributes": True}


class PromptConfigUpdate(BaseModel):
    brand_name: str | None = None
    company_description: str | None = None
    system_prompt_tone: str | None = None
    custom_system_prompt: str | None = None


class PromptConfigOut(BaseModel):
    brand_name: str
    company_description: str
    system_prompt_tone: str
    custom_system_prompt: str
    effective_prompt_preview: str


class HealthOut(BaseModel):
    status: Literal["ok", "degraded"]
    app_name: str
    rag_enabled: bool
    documents_count: int
    openai_configured: bool
