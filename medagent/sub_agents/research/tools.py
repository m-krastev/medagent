"""
Research Agent Tools - Medical literature and guideline consultation
"""

def tool_consult_guidelines(query: str) -> str:
    """
    [TOOL] Searches medical literature and clinical guidelines.
    
    Args:
        query: The clinical question (e.g., 'Sepsis treatment protocol').
    
    Returns:
        Relevant medical literature and guideline excerpts.
    """
    # Lazy import to avoid initialization at module import time
    from src.medagent.infrastructure.rag.engine import get_rag_engine
    
    engine = get_rag_engine()
    return engine.search(query)
