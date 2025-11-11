"""Database models for chat history and conversations"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class Conversation(Base):
    """Conversation/Session model - represents a chat session"""
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), nullable=False, index=True)  # User identifier
    title = Column(String(500), nullable=True)  # Conversation title (auto-generated or user-set)
    grade = Column(Integer, nullable=True)  # Grade level for context
    subject = Column(String(100), nullable=True)  # Subject (tin_hoc, toan, etc.)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)

    # Additional context
    # NOTE: SQLAlchemy's Declarative API reserves the attribute name 'metadata'.
    # To store flexible JSON metadata in the DB column named 'metadata' while
    # avoiding the reserved class attribute, map the column to the attribute
    # `metadata_json` but keep the database column name as 'metadata'.
    metadata_json = Column('metadata', JSON, nullable=True)  # Flexible metadata storage

    # Relationships
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Conversation(id='{self.id}', user_id='{self.user_id}', title='{self.title}')>"


class ChatMessage(Base):
    """Chat message model - represents a single message in a conversation"""
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Message content
    role = Column(String(50), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)  # Message text

    # RAG-specific fields
    sources = Column(JSON, nullable=True)  # Source documents used for this response
    retrieval_mode = Column(String(50), nullable=True)  # 'knowledge_base', 'web_search', 'combined'
    docs_retrieved = Column(Integer, nullable=True)  # Number of docs retrieved
    web_search_used = Column(Boolean, default=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processing_time = Column(Integer, nullable=True)  # Processing time in milliseconds
    # See note above about reserved attribute name 'metadata'
    metadata_json = Column('metadata', JSON, nullable=True)  # Flexible metadata (tokens, model, etc.)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage(id='{self.id}', role='{self.role}', conversation_id='{self.conversation_id}')>"
