import os
from typing import Dict, Any
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

from src.state import AuditorState
from src.config import Config

def retrieve_legal_frameworks(state: AuditorState) -> Dict[str, Any]:
    """
    Agent: The Legal Librarian (Retriever)
    Takes the current state, reads the user's question and document_type,
    and queries the Qdrant persistent database using metadata filters.
    """
    print("\n🕵️‍♂️ [Agent: Retriever] Analyzing question and searching legal database...")
    
    # Read search_query (rewritten) if available, otherwise fall back to original question
    question = state.get("search_query") or state["question"]
    document_type = state.get("document_type", "Other")
    
    # Initialize embeddings (must match dimensions of ingestion)
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-2", 
        google_api_key=Config.GEMINI_API_KEY
    )
    
    # Resolve absolute path to qdrant_storage relative to this file
    QDRANT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "qdrant_storage"))
    
    # Open local persistent connection
    client = QdrantClient(path=QDRANT_PATH)
    
    try:
        vector_store = QdrantVectorStore(
            client=client,
            collection_name="legal_frameworks",
            embedding=embeddings
        )
        
        # Build metadata filter if category is recognized and not "Other"
        filter_query = None
        if document_type and document_type != "Other":
            print(f"🎯 [Agent: Retriever] Applying metadata filter for document_type: '{document_type}'")
            filter_query = qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="metadata.document_type",
                        match=qdrant_models.MatchValue(value=document_type)
                    )
                ]
            )
        else:
            print("🌐 [Agent: Retriever] Category is 'Other' or unspecified. Searching globally...")
            
        # Perform similarity search with score
        results = vector_store.similarity_search_with_score(
            query=question, 
            k=4, 
            filter=filter_query
        )
        
        # Format results into structured dictionaries for state
        legal_docs = []
        for doc, score in results:
            legal_docs.append({
                "text": doc.page_content,
                "source": os.path.basename(doc.metadata.get("source", "unknown_document")),
                "page": doc.metadata.get("page", 0) + 1,  # Convert 0-indexed PDF page to 1-indexed
                "score": float(score)
            })
            
        print(f"📚 [Agent: Retriever] Found {len(legal_docs)} matching clauses.")
        return {"legal_docs": legal_docs}
        
    except Exception as e:
        print(f"❌ [Agent: Retriever] Error during retrieval: {e}")
        # Return empty list on failure to let graph proceed safely
        return {"legal_docs": []}
    finally:
        # Crucial to release local SQLite/RocksDB locks on Windows
        client.close()