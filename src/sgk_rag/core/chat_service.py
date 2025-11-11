"""Chat Service - Manages conversations and chat memory"""

import logging
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.chat_models import Conversation, ChatMessage
from ..models.chat_dto import (
    ChatMessageRequest, ConversationCreateRequest, ConversationUpdateRequest,
    ChatMessageResponse, ConversationResponse, ConversationWithMessagesResponse,
    ChatResponse, MessageRole
)
from ..core.rag_pipeline import RAGPipeline

logger = logging.getLogger(__name__)


class ChatService:
    """Service for managing chat conversations with memory"""

    def __init__(self, rag_pipeline: RAGPipeline):
        """
        Initialize chat service

        Args:
            rag_pipeline: RAG pipeline for answering questions
        """
        self.rag_pipeline = rag_pipeline

    # -----------------
    # Helpers
    # -----------------
    def _conversation_to_mapping(self, conv: Conversation) -> dict:
        """Convert Conversation ORM object to a plain mapping expected by Pydantic

        We map the DB column 'metadata' which is stored on the ORM as
        `metadata_json` to the expected `metadata` key used by DTOs.
        """
        return {
            "id": conv.id,
            "user_id": conv.user_id,
            "title": conv.title,
            "grade": conv.grade,
            "subject": conv.subject,
            "created_at": conv.created_at,
            "updated_at": conv.updated_at,
            "is_archived": conv.is_archived,
            "metadata": getattr(conv, "metadata_json", None),
        }

    def _message_to_mapping(self, msg: ChatMessage) -> dict:
        """Convert ChatMessage ORM object to mapping expected by Pydantic."""
        return {
            "id": msg.id,
            "conversation_id": msg.conversation_id,
            "role": msg.role,
            "content": msg.content,
            "sources": getattr(msg, "sources", None),
            "retrieval_mode": getattr(msg, "retrieval_mode", None),
            "docs_retrieved": getattr(msg, "docs_retrieved", None),
            "web_search_used": getattr(msg, "web_search_used", None),
            "processing_time": getattr(msg, "processing_time", None),
            "created_at": msg.created_at,
            "metadata": getattr(msg, "metadata_json", None),
        }

    async def create_conversation(
        self,
        db: AsyncSession,
        request: ConversationCreateRequest
    ) -> ConversationResponse:
        """Create a new conversation - Only user_id and title required!"""
        # Generate a friendly default title if not provided
        default_title = f"New Chat {datetime.now().strftime('%b %d, %I:%M %p')}"

        conversation = Conversation(
            user_id=request.user_id,
            title=request.title or default_title,
            grade=None,  # Optional - can be set later
            subject="Tin Học",  # Always Informatics/Computer Science
        )

        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)

        logger.info(f"✅ Created conversation {conversation.id} for user {request.user_id}")

        return ConversationResponse.model_validate(self._conversation_to_mapping(conversation))

    async def get_conversation(
        self,
        db: AsyncSession,
        conversation_id: str,
        user_id: str
    ) -> Optional[ConversationResponse]:
        """Get a conversation by ID"""
        result = await db.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .where(Conversation.user_id == user_id)
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            return None

        # Count messages
        count_result = await db.execute(
            select(func.count(ChatMessage.id))
            .where(ChatMessage.conversation_id == conversation_id)
        )
        message_count = count_result.scalar()

        response = ConversationResponse.model_validate(self._conversation_to_mapping(conversation))
        response.message_count = message_count
        return response

    async def list_conversations(
        self,
        db: AsyncSession,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        include_archived: bool = False
    ) -> tuple[List[ConversationResponse], int]:
        """List conversations for a user"""
        # Build query
        query = select(Conversation).where(Conversation.user_id == user_id)

        if not include_archived:
            query = query.where(Conversation.is_archived == False)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Get paginated results
        query = query.order_by(desc(Conversation.updated_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        conversations = result.scalars().all()

        responses = [ConversationResponse.model_validate(self._conversation_to_mapping(conv)) for conv in conversations]

        return responses, total

    async def update_conversation(
        self,
        db: AsyncSession,
        conversation_id: str,
        user_id: str,
        request: ConversationUpdateRequest
    ) -> Optional[ConversationResponse]:
        """Update conversation metadata"""
        result = await db.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .where(Conversation.user_id == user_id)
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            return None

        # Update fields
        if request.title is not None:
            conversation.title = request.title
        if request.grade is not None:
            conversation.grade = request.grade
        if request.is_archived is not None:
            conversation.is_archived = request.is_archived
        # Note: subject is always "Tin Học" and cannot be changed

        await db.commit()
        await db.refresh(conversation)

        logger.info(f"✅ Updated conversation {conversation_id}")

        return ConversationResponse.model_validate(self._conversation_to_mapping(conversation))

    async def delete_conversation(
        self,
        db: AsyncSession,
        conversation_id: str,
        user_id: str
    ) -> bool:
        """Delete a conversation and all its messages"""
        result = await db.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .where(Conversation.user_id == user_id)
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            return False

        await db.delete(conversation)
        await db.commit()

        logger.info(f"✅ Deleted conversation {conversation_id}")

        return True

    async def get_conversation_messages(
        self,
        db: AsyncSession,
        conversation_id: str,
        user_id: str,
        limit: Optional[int] = None
    ) -> ConversationWithMessagesResponse:
        """Get conversation with messages"""
        # Get conversation
        conv_result = await db.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .where(Conversation.user_id == user_id)
        )
        conversation = conv_result.scalar_one_or_none()

        if not conversation:
            return None

        # Get messages
        query = (
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.asc())
        )

        if limit:
            query = query.limit(limit)

        messages_result = await db.execute(query)
        messages = messages_result.scalars().all()

        # Get total count
        count_result = await db.execute(
            select(func.count(ChatMessage.id))
            .where(ChatMessage.conversation_id == conversation_id)
        )
        total_messages = count_result.scalar()

        return ConversationWithMessagesResponse(
            conversation=ConversationResponse.model_validate(self._conversation_to_mapping(conversation)),
            messages=[ChatMessageResponse.model_validate(self._message_to_mapping(msg)) for msg in messages],
            total_messages=total_messages
        )

    async def send_message(
        self,
        db: AsyncSession,
        request: ChatMessageRequest
    ) -> ChatResponse:
        """
        Send a message and get AI response with conversation memory

        This is the main method that handles:
        1. Creating conversation if needed
        2. Loading conversation history for context
        3. Querying RAG pipeline with context
        4. Storing user and assistant messages
        """
        start_time = time.time()

        try:
            # Step 1: Get or create conversation
            if request.conversation_id:
                # Get existing conversation
                conv_result = await db.execute(
                    select(Conversation)
                    .where(Conversation.id == request.conversation_id)
                    .where(Conversation.user_id == request.user_id)
                )
                conversation = conv_result.scalar_one_or_none()

                if not conversation:
                    raise ValueError(f"Conversation {request.conversation_id} not found")
            else:
                # Create new conversation
                conversation = Conversation(
                    user_id=request.user_id,
                    title=self._generate_title_from_message(request.message),
                    grade=request.grade,
                    subject="Tin Học"  # Always Informatics/Computer Science
                )
                db.add(conversation)
                await db.flush()  # Get ID without committing

            # Step 2: Load conversation history for context
            history_query = (
                select(ChatMessage)
                .where(ChatMessage.conversation_id == conversation.id)
                .order_by(desc(ChatMessage.created_at))
                .limit(request.max_history)
            )
            history_result = await db.execute(history_query)
            history_messages = list(reversed(history_result.scalars().all()))

            # Step 3: Build context from history
            context_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in history_messages
            ]

            # Step 4: Create enhanced question with context
            enhanced_question = self._build_contextual_question(
                request.message,
                context_messages
            )

            # Step 5: Query RAG pipeline
            rag_response = self.rag_pipeline.query(
                enhanced_question,
                grade_filter=request.grade or conversation.grade,
                return_sources=request.return_sources
            )

            # Step 6: Extract response data
            if isinstance(rag_response, dict):
                answer = rag_response.get('answer', str(rag_response))
                sources = rag_response.get('sources', [])
                retrieval_mode = rag_response.get('retrieval_mode')
                docs_retrieved = rag_response.get('docs_retrieved')
                web_search_used = rag_response.get('web_search_used', False)
            else:
                answer = str(rag_response)
                sources = []
                retrieval_mode = None
                docs_retrieved = None
                web_search_used = False

            processing_time = int((time.time() - start_time) * 1000)

            # Step 7: Store user message
            user_message = ChatMessage(
                conversation_id=conversation.id,
                role=MessageRole.USER.value,
                content=request.message,
                created_at=datetime.utcnow()
            )
            db.add(user_message)

            # Step 8: Store assistant message
            assistant_message = ChatMessage(
                conversation_id=conversation.id,
                role=MessageRole.ASSISTANT.value,
                content=answer,
                sources=sources if request.return_sources else None,
                retrieval_mode=retrieval_mode,
                docs_retrieved=docs_retrieved,
                web_search_used=web_search_used,
                processing_time=processing_time,
                created_at=datetime.utcnow()
            )
            db.add(assistant_message)

            # Update conversation timestamp
            conversation.updated_at = datetime.utcnow()

            await db.commit()
            await db.refresh(user_message)
            await db.refresh(assistant_message)

            logger.info(
                f"✅ Processed chat message in conversation {conversation.id} "
                f"(processing_time={processing_time}ms, docs={docs_retrieved})"
            )

            # Step 9: Build response
            return ChatResponse(
                conversation_id=conversation.id,
                message_id=assistant_message.id,
                user_message=ChatMessageResponse.model_validate(self._message_to_mapping(user_message)),
                assistant_message=ChatMessageResponse.model_validate(self._message_to_mapping(assistant_message)),
                status="success"
            )

        except Exception as e:
            logger.error(f"❌ Error processing chat message: {e}")
            await db.rollback()
            raise

    def _generate_title_from_message(self, message: str, max_length: int = 50) -> str:
        """Generate a conversation title from the first message"""
        if len(message) <= max_length:
            return message
        return message[:max_length].rsplit(' ', 1)[0] + "..."

    def _build_contextual_question(
        self,
        current_message: str,
        context_messages: List[Dict[str, str]]
    ) -> str:
        """
        Build an enhanced question that includes conversation context

        Args:
            current_message: Current user message
            context_messages: Previous messages in conversation

        Returns:
            Enhanced question with context
        """
        if not context_messages:
            return current_message

        # Build context summary
        context_parts = []
        for msg in context_messages[-5:]:  # Last 5 messages for context
            role = "User" if msg["role"] == "user" else "Assistant"
            content = msg["content"][:200]  # Truncate long messages
            context_parts.append(f"{role}: {content}")

        context_text = "\n".join(context_parts)

        # Build enhanced question
        enhanced = f"""Dựa vào ngữ cảnh cuộc trò chuyện trước đó:

{context_text}

Câu hỏi hiện tại: {current_message}

Hãy trả lời câu hỏi hiện tại với sự liên kết đến ngữ cảnh cuộc trò chuyện."""

        return enhanced
