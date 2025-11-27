import os
import sys
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datasets import load_dataset
from llama_index.core import Document, VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.gemini import GeminiEmbedding
import chromadb
from medagent.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DataIngestion")

Settings.embed_model = GeminiEmbedding(model_name=settings.MODEL_EMBEDDING)

def ingest_medqa():
    logger.info("Downloading MedQA (USMLE) Dataset...")
    try:
        # Streaming subset to avoid massive download
        dataset = load_dataset("GBaker/MedQA-USMLE-4-options", split="train")
        
        docs = []
        count = 0
        logger.info("Processing cases...")
        
        for row in dataset:
            if count >= 50: break # Limit for foundation demo
            
            text = (
                f"CLINICAL VIGNETTE:\n{row['question']}\n"
                f"CORRECT ANSWER/DIAGNOSIS:\n{row['answer']}"
            )
            docs.append(Document(text=text, metadata={"source": "MedQA", "id": count}))
            count += 1
            
        logger.info(f"Initializing ChromaDB at {settings.CHROMA_DB_DIR}...")
        db = chromadb.PersistentClient(path=settings.CHROMA_DB_DIR)
        collection = db.get_or_create_collection("medical_guidelines")
        vector_store = ChromaVectorStore(chroma_collection=collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        logger.info("Embedding and Indexing...")
        VectorStoreIndex.from_documents(docs, storage_context=storage_context)
        logger.info("✅ Data Ingestion Complete.")
        
    except Exception as e:
        logger.error(f"❌ Error loading data: {e}", exc_info=True)

if __name__ == "__main__":
    if not settings.GOOGLE_API_KEY:
        logger.error("Error: GOOGLE_API_KEY not set in .env or environment variables.")
    else:
        ingest_medqa()
