"""API Models - Main export module for all DTOs

This module re-exports all DTOs from specific modules for backward compatibility.
Import from this module to access all models, or import from specific modules for better organization.

Usage:
    # Import all models (backward compatible)
    from sgk_rag.models.dto import QuestionRequest, SlideRequest, MindmapRequest

    # Or import from specific modules
    from sgk_rag.models.question_dto import QuestionRequest
    from sgk_rag.models.slide_dto import SlideRequest
    from sgk_rag.models.mindmap_dto import MindmapRequest
"""

# Base models and common types
from .base_dto import (
    QuestionType,
    TextAlignment,
    Position,
    SourceInfo,
    HealthResponse,
    ErrorResponse,
)

# Question models
from .question_dto import (
    QuestionRequest,
    QuestionResponse,
    BatchQuestionRequest,
    BatchQuestionResponse,
    EXAMPLE_QUESTION_REQUEST,
    EXAMPLE_QUESTION_RESPONSE,
)

# Slide models
from .slide_dto import (
    SlideFormat,
    SlideType,
    PowerPointLayout,
    PlaceholderType,
    BulletPoint,
    TableCell,
    TableData,
    ImagePlaceholder,
    CodeBlock,
    PlaceholderContent,
    SlideRequest,
    SlideContent,
    JsonSlideMetadata,
    JsonSlideContent,
    JsonSlideResponse,
    SlideResponse,
    EXAMPLE_SLIDE_REQUEST,
    EXAMPLE_JSON_SLIDE_RESPONSE,
)

# Mindmap models
from .mindmap_dto import (
    NodeType,
    MindmapNode,
    MindmapConnection,
    MindmapRequest,
    MindmapResponse,
    EXAMPLE_MINDMAP_REQUEST,
    EXAMPLE_MINDMAP_RESPONSE,
)

# Export all models for backward compatibility
__all__ = [
    # Base
    "QuestionType",
    "TextAlignment",
    "Position",
    "SourceInfo",
    "HealthResponse",
    "ErrorResponse",
    # Question
    "QuestionRequest",
    "QuestionResponse",
    "BatchQuestionRequest",
    "BatchQuestionResponse",
    # Slide
    "SlideFormat",
    "SlideType",
    "PowerPointLayout",
    "PlaceholderType",
    "BulletPoint",
    "TableCell",
    "TableData",
    "ImagePlaceholder",
    "CodeBlock",
    "PlaceholderContent",
    "SlideRequest",
    "SlideContent",
    "JsonSlideMetadata",
    "JsonSlideContent",
    "JsonSlideResponse",
    "SlideResponse",
    # Mindmap
    "NodeType",
    "MindmapNode",
    "MindmapConnection",
    "MindmapRequest",
    "MindmapResponse",
    # Examples
    "EXAMPLE_QUESTION_REQUEST",
    "EXAMPLE_QUESTION_RESPONSE",
    "EXAMPLE_SLIDE_REQUEST",
    "EXAMPLE_JSON_SLIDE_RESPONSE",
    "EXAMPLE_MINDMAP_REQUEST",
    "EXAMPLE_MINDMAP_RESPONSE",
]
