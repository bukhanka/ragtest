"""Pydantic models for API requests and responses."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class MessageRole(str, Enum):
    """Message role in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """Chat message."""
    role: MessageRole
    content: str


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    use_rag: bool = Field(True, description="Enable RAG for documentation")
    use_sql: bool = Field(True, description="Enable SQL queries")
    use_web_search: bool = Field(True, description="Enable web search")


class ToolUsed(BaseModel):
    """Information about tool used."""
    name: str
    description: str
    result_summary: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    conversation_id: str
    tools_used: List[ToolUsed] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)


class DocumentUploadResponse(BaseModel):
    """Document upload response."""
    message: str
    documents_processed: int
    chunks_created: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    llm_available: bool
    vector_store_available: bool
    database_available: bool

