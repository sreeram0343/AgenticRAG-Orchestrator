from typing import Dict, Any

# We import the state definition we created earlier
# This is the "shared memory" all agents will use
from src.state import AuditorState

def retrieve_legal_frameworks(state: AuditorState, vector_store) -> Dict[str, Any]:
    """
    Agent 1: The Legal Librarian
    Takes the current state, reads the user's question, and searches the vector database
    for the exact legal clauses needed to answer it.
    """
    print("🕵️‍♂️ [Agent: Legal Librarian] Analyzing question and searching legal database...")
    
    question = state["question"]
    
    # We ask Qdrant to find the 4 most mathematically relevant chunks of text
    # related to the user's question using Gemini's vector embeddings.
    retrieved_docs = vector_store.similarity_search(question, k=4)
    
    # Extract just the raw text from the LangChain Document objects
    doc_texts = [doc.page_content for doc in retrieved_docs]
    
    print(f"📚 [Agent: Legal Librarian] Found {len(doc_texts)} relevant legal clauses.")
    
    # We return a dictionary that updates the 'legal_docs' variable in our LangGraph State
    return {"legal_docs": doc_texts}