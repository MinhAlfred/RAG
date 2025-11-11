"""DTOs for Chat with Memory API"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Message role enum"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# ========== Request Models ==========

class ChatMessageRequest(BaseModel):
    """Request to send a chat message"""
    conversation_id: Optional[str] = Field(None, description="Conversation ID (omit to create new)")
    user_id: str = Field(..., description="User identifier")
    message: str = Field(..., description="User message", min_length=1)
    grade: Optional[int] = Field(None, description="Grade level for context", ge=3, le=12)
    return_sources: bool = Field(default=True, description="Whether to return source documents")
    max_history: int = Field(default=10, description="Max previous messages to include as context", ge=0, le=50)
    # Note: subject is automatically "Tin Học" (Informatics)


class ConversationCreateRequest(BaseModel):
    """Request to create a new conversation - Only user_id required!"""
    user_id: str = Field(..., description="User identifier")
    title: Optional[str] = Field(None, description="Conversation title (auto-generated if not provided)")


class ConversationUpdateRequest(BaseModel):
    """Request to update a conversation"""
    title: Optional[str] = Field(None, description="New title")
    grade: Optional[int] = Field(None, description="New grade level", ge=3, le=12)
    is_archived: Optional[bool] = Field(None, description="Archive status")
    # Note: subject is fixed as "Tin Học" and cannot be changed


# ========== Response Models ==========

class ChatMessageResponse(BaseModel):
    """Single chat message"""
    id: str
    conversation_id: str
    role: MessageRole
    content: str
    sources: Optional[List[Dict[str, Any]]] = None
    retrieval_mode: Optional[str] = None
    docs_retrieved: Optional[int] = None
    web_search_used: Optional[bool] = None
    processing_time: Optional[int] = None
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Conversation details"""
    id: str
    user_id: str
    title: Optional[str]
    grade: Optional[int]
    subject: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_archived: bool
    metadata: Optional[Dict[str, Any]]
    message_count: Optional[int] = None

    class Config:
        from_attributes = True


class ConversationWithMessagesResponse(BaseModel):
    """Conversation with messages"""
    conversation: ConversationResponse
    messages: List[ChatMessageResponse]
    total_messages: int


class ChatResponse(BaseModel):
    """Response after sending a chat message"""
    conversation_id: str
    message_id: str
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse
    status: str = "success"
    error: Optional[str] = None


class ConversationListResponse(BaseModel):
    """List of conversations"""
    conversations: List[ConversationResponse]
    total: int
    page: int
    page_size: int


class DeleteResponse(BaseModel):
    """Response after deleting a resource"""
    success: bool
    message: str
    deleted_id: str
