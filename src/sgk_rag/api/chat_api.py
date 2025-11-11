"""Chat API endpoints with conversation memory"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db_session
from ..core.rag_pipeline import RAGPipeline
from ..core.chat_service import ChatService
from ..models.chat_dto import (
    ChatMessageRequest, ConversationCreateRequest, ConversationUpdateRequest,
    ChatResponse, ConversationResponse, ConversationWithMessagesResponse,
    ConversationListResponse, DeleteResponse
)
from .auth import verify_api_key

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/chat", tags=["Chat with Memory"])


def get_chat_service(rag_pipeline: RAGPipeline) -> ChatService:
    """Dependency to get chat service"""
    return ChatService(rag_pipeline)


# ========== Conversation Management ==========

@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key)
):
    """
    Create a new conversation - Super simple!

    **Only user_id is required.** All other fields are optional and will be auto-generated or left empty.

    **Minimal example:**
    ```json
    {
        "user_id": "user123"
    }
    ```

    **With title:**
    ```json
    {
        "user_id": "user123",
        "title": "Learning Python"
    }
    ```

    **With custom title:**
    ```json
    {
        "user_id": "user123",
        "title": "Learning Python Basics"
    }
    ```

    **Note:** Subject is automatically set to "Tin Học" (Informatics)

    Args:
        request: Conversation creation request (only user_id required)
        db: Database session
        api_key: API key for authentication

    Returns:
        ConversationResponse with conversation details including auto-generated title
    """
    from ..api.main import rag_pipeline  # Import from main

    chat_service = get_chat_service(rag_pipeline)
    return await chat_service.create_conversation(db, request)


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    user_id: str = Query(..., description="User identifier"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    include_archived: bool = Query(False, description="Include archived conversations"),
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key)
):
    """
    List conversations for a user

    Args:
        user_id: User identifier
        page: Page number (1-indexed)
        page_size: Number of items per page
        include_archived: Whether to include archived conversations
        db: Database session
        api_key: API key for authentication

    Returns:
        ConversationListResponse with paginated conversations
    """
    from ..api.main import rag_pipeline

    chat_service = get_chat_service(rag_pipeline)
    conversations, total = await chat_service.list_conversations(
        db, user_id, page, page_size, include_archived
    )

    return ConversationListResponse(
        conversations=conversations,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    user_id: str = Query(..., description="User identifier"),
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key)
):
    """
    Get a specific conversation

    Args:
        conversation_id: Conversation ID
        user_id: User identifier
        db: Database session
        api_key: API key for authentication

    Returns:
        ConversationResponse with conversation details
    """
    from ..api.main import rag_pipeline

    chat_service = get_chat_service(rag_pipeline)
    conversation = await chat_service.get_conversation(db, conversation_id, user_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation


@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    request: ConversationUpdateRequest,
    user_id: str = Query(..., description="User identifier"),
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key)
):
    """
    Update conversation metadata

    Args:
        conversation_id: Conversation ID
        request: Update request
        user_id: User identifier
        db: Database session
        api_key: API key for authentication

    Returns:
        ConversationResponse with updated conversation
    """
    from ..api.main import rag_pipeline

    chat_service = get_chat_service(rag_pipeline)
    conversation = await chat_service.update_conversation(
        db, conversation_id, user_id, request
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation


@router.delete("/conversations/{conversation_id}", response_model=DeleteResponse)
async def delete_conversation(
    conversation_id: str,
    user_id: str = Query(..., description="User identifier"),
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key)
):
    """
    Delete a conversation and all its messages

    Args:
        conversation_id: Conversation ID
        user_id: User identifier
        db: Database session
        api_key: API key for authentication

    Returns:
        DeleteResponse with success status
    """
    from ..api.main import rag_pipeline

    chat_service = get_chat_service(rag_pipeline)
    success = await chat_service.delete_conversation(db, conversation_id, user_id)

    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return DeleteResponse(
        success=True,
        message="Conversation deleted successfully",
        deleted_id=conversation_id
    )


# ========== Message Management ==========

@router.get("/conversations/{conversation_id}/messages", response_model=ConversationWithMessagesResponse)
async def get_conversation_messages(
    conversation_id: str,
    user_id: str = Query(..., description="User identifier"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Limit number of messages"),
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key)
):
    """
    Get all messages in a conversation

    Args:
        conversation_id: Conversation ID
        user_id: User identifier
        limit: Optional limit on number of messages
        db: Database session
        api_key: API key for authentication

    Returns:
        ConversationWithMessagesResponse with conversation and messages
    """
    from ..api.main import rag_pipeline

    chat_service = get_chat_service(rag_pipeline)
    response = await chat_service.get_conversation_messages(
        db, conversation_id, user_id, limit
    )

    if not response:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return response


@router.post("/messages", response_model=ChatResponse)
async def send_message(
    request: ChatMessageRequest,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key)
):
    """
    Send a message and get AI response with conversation memory

    This endpoint:
    - Creates a new conversation if conversation_id is not provided
    - Loads conversation history for context
    - Uses RAG pipeline with context to generate response
    - Stores both user message and AI response
    - Returns the complete chat exchange

    Args:
        request: Chat message request
        db: Database session
        api_key: API key for authentication

    Returns:
        ChatResponse with user and assistant messages

    Example request:
        {
            "conversation_id": "uuid-here",  # Optional, omit to create new
            "user_id": "user123",
            "message": "What is a variable in programming?",
            "grade": 6,
            "subject": "tin_hoc",
            "return_sources": true,
            "max_history": 10
        }
    """
    from ..api.main import rag_pipeline

    try:
        chat_service = get_chat_service(rag_pipeline)
        response = await chat_service.send_message(db, request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")
