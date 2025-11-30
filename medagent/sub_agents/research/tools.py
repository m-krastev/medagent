"""
Research Agent Tools - Medical literature and guideline consultation
"""

import logging
from ...config import settings

logger = logging.getLogger(__name__)

# RAG dependencies are optional
RAG_AVAILABLE = False
try:
    import chromadb
    from llama_index.core import VectorStoreIndex, StorageContext, Settings
    from llama_index.vector_stores.chroma import ChromaVectorStore
    from llama_index.embeddings.gemini import GeminiEmbedding
    from llama_index.llms.gemini import Gemini
    
    # Configure LlamaIndex Global Settings
    Settings.embed_model = GeminiEmbedding(model_name=settings.MODEL_EMBEDDING)
    Settings.llm = Gemini(model_name=f"models/{settings.MODEL_FAST}")
    RAG_AVAILABLE = True
except ImportError as e:
    logger.warning(f"RAG dependencies not available: {e}. Knowledge base search will be disabled.")


class MedicalKnowledgeEngine:
    """
    Enterprise RAG Engine wrapping LlamaIndex and ChromaDB.
    """

    def __init__(self):
        self._index = None
        self._query_engine = None
        if RAG_AVAILABLE:
            self._initialize_db()

    def _initialize_db(self):
        """Initializes connection to ChromaDB."""
        if not RAG_AVAILABLE:
            logger.warning("RAG dependencies not installed. Skipping DB initialization.")
            return
            
        try:
            logger.info(f"Connecting to ChromaDB at {settings.CHROMA_DB_DIR}")
            db_client = chromadb.PersistentClient(path=settings.CHROMA_DB_DIR)

            # We use a specific collection for medical guidelines
            collection = db_client.get_or_create_collection("medical_guidelines")
            vector_store = ChromaVectorStore(chroma_collection=collection)

            # Load index from vector store
            self._index = VectorStoreIndex.from_vector_store(
                vector_store, embed_model=Settings.embed_model
            )

            # Create query engine with similarity top_k=3
            self._query_engine = self._index.as_query_engine(similarity_top_k=3)
            logger.info("RAG Engine initialized successfully.")

        except Exception as e:
            logger.error(f"Failed to initialize RAG Engine: {e}")
            self._query_engine = None

    def search(self, query: str) -> str:
        """
        Executes a semantic search against the medical knowledge base.
        """
        if not RAG_AVAILABLE:
            return (
                "SYSTEM NOTE: RAG dependencies (chromadb, llama-index) are not installed. "
                "Knowledge base search is unavailable. Please install with: "
                "pip install chromadb llama-index-vector-stores-chroma llama-index-embeddings-gemini llama-index-llms-gemini"
            )
        
        if not self._query_engine:
            return (
                "SYSTEM ERROR: Knowledge Base is offline. Cannot retrieve guidelines."
            )

        logger.info(f"Executing RAG Search: {query}")
        response = self._query_engine.query(query)
        logger.info(f"RAG Search completed. Response: {response}")
        return str(response)


# Singleton - Lazy Loaded
_rag_engine_instance = None


def get_rag_engine():
    global _rag_engine_instance
    if _rag_engine_instance is None:
        _rag_engine_instance = MedicalKnowledgeEngine()
    return _rag_engine_instance


def tool_consult_guidelines(query: str) -> str:
    """
    [TOOL] Searches medical literature and clinical guidelines.
    Args:
        query: The clinical question (e.g., 'Sepsis treatment protocol').
    
    Returns:
        str: The retrieved guideline or literature summary.
    """
    engine = get_rag_engine()
    return engine.search(query)
