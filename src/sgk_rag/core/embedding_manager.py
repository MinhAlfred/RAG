"""Embedding Manager - Convert text to vectors"""

import logging
from typing import List, Optional
from pathlib import Path
from tqdm import tqdm

from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

from ..models.document import Chunk
from config.settings import settings

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """Quản lý embeddings cho chunks"""

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None
    ):
        """
        Args:
            model_name: "openai", "multilingual", "vietnamese"
            device: "cpu" or "cuda"
        """
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.device = device or settings.EMBEDDING_DEVICE

        self.embeddings = self._initialize_embeddings()
        logger.info(f"EmbeddingManager initialized (model={self.model_name})")

    def _initialize_embeddings(self):
        """Initialize embedding model"""
        if self.model_name == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not set")

            return OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=settings.OPENAI_API_KEY
            )

        elif self.model_name == "multilingual":
            logger.info("Loading multilingual model (may take 30-60s)...")
            return HuggingFaceEmbeddings(
                model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                model_kwargs={'device': self.device},
                encode_kwargs={'normalize_embeddings': True}
            )

        elif self.model_name == "vietnamese":
            logger.info("Loading Vietnamese model (may take 30-60s)...")
            return HuggingFaceEmbeddings(
                model_name="bkai-foundation-models/vietnamese-bi-encoder",
                model_kwargs={'device': self.device},
                encode_kwargs={'normalize_embeddings': True}
            )

        else:
            raise ValueError(f"Unknown embedding model: {self.model_name}")

    def embed_query(self, query: str) -> List[float]:
        """Embed a single query"""
        return self.embeddings.embed_query(query)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents"""
        return self.embeddings.embed_documents(texts)