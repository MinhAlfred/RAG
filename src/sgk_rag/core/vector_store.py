"""Vector Store Manager - Store and retrieve chunks"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import json

from langchain_community.vectorstores import Chroma, FAISS
from langchain_core.documents import Document as LangChainDocument
from langchain_community.vectorstores.utils import filter_complex_metadata
from tqdm import tqdm

from ..models.document import Chunk
from .embedding_manager import EmbeddingManager
from config.settings import settings

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Quản lý Vector Store"""

    def __init__(
            self,
            store_type: Optional[str] = None,
            embedding_manager: Optional[EmbeddingManager] = None,
            collection_name: Optional[str] = None,
            persist_directory: Optional[Path] = None
    ):
        """
        Args:
            store_type: "chroma" or "faiss"
            embedding_manager: EmbeddingManager instance
            collection_name: Name for the collection
            persist_directory: Where to save the vector store
        """
        self.store_type = store_type or settings.VECTOR_STORE_TYPE
        self.embedding_manager = embedding_manager or EmbeddingManager()
        self.collection_name = collection_name or settings.COLLECTION_NAME_PREFIX
        self.persist_directory = persist_directory or settings.VECTORSTORE_DIR

        logger.info(f"VectorStoreManager initialized (type={self.store_type})")

    def load_chunks_from_json(self, json_path: str | Path) -> List[Chunk]:
        """Load chunks from JSON file"""
        json_path = Path(json_path)
        logger.info(f"Loading chunks from: {json_path}")

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        chunks = []
        for item in data:
            chunk = Chunk(
                chunk_id=item['chunk_id'],
                content=item['content'],
                metadata=item['metadata'],  # Will be dict
                token_count=item.get('token_count')
            )
            chunks.append(chunk)

        logger.info(f"✓ Loaded {len(chunks)} chunks")
        return chunks

    def chunks_to_langchain_documents(self, chunks: List[Chunk]) -> List[LangChainDocument]:
        """Convert our Chunks to LangChain Documents"""
        documents = []

        for chunk in chunks:
            # Get metadata and ensure it's in dict format
            metadata = chunk.metadata if isinstance(chunk.metadata, dict) else chunk.metadata.to_dict()
            
            # Manually filter complex metadata that ChromaDB can't handle
            filtered_metadata = {}
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)) or value is None:
                    filtered_metadata[key] = value
                # Skip lists, dicts, and other complex types
            
            doc = LangChainDocument(
                page_content=chunk.content,
                metadata=filtered_metadata
            )
            documents.append(doc)

        return documents

    def create_vectorstore(
            self,
            chunks: List[Chunk],
            collection_name: Optional[str] = None,
            batch_size: int = 50
    ):
        """
        Create vector store from chunks

        Args:
            chunks: List of Chunk objects
            collection_name: Override collection name
            batch_size: Batch size for embedding

        Returns:
            Vector store object
        """
        collection_name = collection_name or self.collection_name

        logger.info(f"\n{'=' * 70}")
        logger.info(f"🚀 Creating Vector Store: {self.store_type.upper()}")
        logger.info(f"{'=' * 70}")
        logger.info(f"Collection: {collection_name}")
        logger.info(f"Total chunks: {len(chunks):,}")
        logger.info(f"Batch size: {batch_size}\n")

        # Convert to LangChain documents
        documents = self.chunks_to_langchain_documents(chunks)

        # Test embedding
        logger.info("🧪 Testing embedding model...")
        test_embedding = self.embedding_manager.embed_query("test")
        logger.info(f"   ✓ Embedding dimension: {len(test_embedding)}")

        # Create vector store
        if self.store_type == "chroma":
            vectorstore = self._create_chroma(documents, collection_name, batch_size)
        elif self.store_type == "faiss":
            vectorstore = self._create_faiss(documents, batch_size)
        else:
            raise ValueError(f"Unknown vector store type: {self.store_type}")

        logger.info(f"\n✅ Vector store created successfully!")
        return vectorstore

    def _create_chroma(
            self,
            documents: List[LangChainDocument],
            collection_name: str,
            batch_size: int
    ):
        """Create ChromaDB vector store"""
        persist_path = self.persist_directory / "chroma_db" / collection_name
        persist_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"📦 Creating ChromaDB...")
        logger.info(f"   Path: {persist_path}")

        # Create in batches
        vectorstore = None

        for i in tqdm(range(0, len(documents), batch_size), desc="Creating embeddings"):
            batch = documents[i:i + batch_size]

            if vectorstore is None:
                # Create new vector store
                vectorstore = Chroma.from_documents(
                    documents=batch,
                    embedding=self.embedding_manager.embeddings,
                    collection_name=collection_name,
                    persist_directory=str(persist_path)
                )
            else:
                # Add to existing
                vectorstore.add_documents(batch)

            # Persist after each batch
            # lưu data xuống disk sau mỗi batch để tránh mất mát dữ liệu
            if hasattr(vectorstore, 'persist'):
                vectorstore.persist()

        logger.info(f"   ✓ Saved to: {persist_path}")
        return vectorstore

    def _create_faiss(
            self,
            documents: List[LangChainDocument],
            batch_size: int
    ):
        """Create FAISS vector store"""
        logger.info(f"⚡ Creating FAISS index...")

        # Create index
        vectorstore = FAISS.from_documents(
            documents=documents,
            embedding=self.embedding_manager.embeddings
        )

        # Save to disk
        faiss_path = self.persist_directory / "faiss_index" / self.collection_name
        faiss_path.parent.mkdir(parents=True, exist_ok=True)

        vectorstore.save_local(str(faiss_path))
        logger.info(f"   ✓ Saved to: {faiss_path}")

        return vectorstore

    def load_vectorstore(
            self,
            collection_name: Optional[str] = None
    ):
        """Load existing vector store"""
        collection_name = collection_name or self.collection_name

        logger.info(f"📂 Loading vector store: {collection_name}")

        if self.store_type == "chroma":
            persist_path = self.persist_directory / "chroma_db" / collection_name

            if not persist_path.exists():
                raise FileNotFoundError(f"ChromaDB not found: {persist_path}")

            vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=self.embedding_manager.embeddings,
                persist_directory=str(persist_path)
            )

        elif self.store_type == "faiss":
            faiss_path = self.persist_directory / "faiss_index" / collection_name

            if not faiss_path.exists():
                raise FileNotFoundError(f"FAISS index not found: {faiss_path}")

            vectorstore = FAISS.load_local(
                str(faiss_path),
                self.embedding_manager.embeddings,
                allow_dangerous_deserialization=True
            )

        else:
            raise ValueError(f"Unknown vector store type: {self.store_type}")

        logger.info(f"   ✓ Loaded successfully")
        return vectorstore

    def search(
            self,
            vectorstore,
            query: str,
            k: int = 5,
            filter_dict: Optional[Dict] = None
    ) -> List[LangChainDocument]:
        """
        Search in vector store

        Args:
            vectorstore: Vector store instance
            query: Search query
            k: Number of results
            filter_dict: Metadata filters (e.g., {"grade": 10, "subject_key": "tin_hoc"})

        Returns:
            List of matching documents
        """
        if filter_dict:
            results = vectorstore.similarity_search(query, k=k, filter=filter_dict)
        else:
            results = vectorstore.similarity_search(query, k=k)

        return results

    def get_statistics(self, vectorstore) -> Dict[str, Any]:
        """Get statistics about vector store"""
        stats = {}

        if self.store_type == "chroma":
            collection = vectorstore._collection
            stats['total_documents'] = collection.count()
            stats['collection_name'] = collection.name

        elif self.store_type == "faiss":
            index = vectorstore.index
            stats['total_vectors'] = index.ntotal
            stats['dimension'] = index.d

        return stats