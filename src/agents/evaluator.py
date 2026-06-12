from typing import Dict, Any, List
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

# Import our shared state and config
from src.state import AuditorState
from src.config import Config

# Define the structured output schema for a single graded document
class GradeDocumentItem(BaseModel):
    index: int = Field(description="The 0-based index of the document chunk in the provided list.")
    relevant: bool = Field(description="Is the document chunk relevant to the user query? True if yes, False if no.")

# Define the structured output schema for the batch evaluator
class GradeDocumentsBatch(BaseModel):
    results: List[GradeDocumentItem] = Field(description="The grading results for each document chunk.")

def evaluate_documents(state: AuditorState) -> Dict[str, Any]:
    """
    Agent: The Internal Inspector (Evaluator)
    Filters retrieved documents by grading their relevance to the user's question.
    Optimized to evaluate all documents in a single batched LLM call to conserve API quota.
    """
    print("\n⚖️ [Agent: Evaluator] Grading retrieved legal clauses for strict relevance...")
    
    question = state["question"]
    documents = state.get("legal_docs", [])
    
    if not documents:
        print("⚠️ [Agent: Evaluator] No documents retrieved. Grading search as FAIL.")
        return {"legal_docs": [], "retrieval_grade": "fail"}
    
    # Initialize deterministic Gemini 3.5 Flash model
    llm = ChatGoogleGenerativeAI(
        model=Config.DEFAULT_MODEL,
        api_key=Config.GEMINI_API_KEY,
        temperature=0
    )
    
    # Force structured output using the batched Pydantic schema
    structured_llm_grader = llm.with_structured_output(GradeDocumentsBatch)
    
    system_prompt = """You are a strict, emotionless legal compliance evaluator.
    You will be given a user's question and a list of retrieved document chunks.
    Assess which of the retrieved chunks contain ANY information relevant to answering the user's question.
    Grade each document chunk by its index. Mark it as relevant (true) if it contains keywords, concepts, 
    or clauses mathematically or legally related to the user's question. Otherwise, mark it as irrelevant (false).
    Do NOT answer the question. You are only grading the relevance of the text."""
    
    # Format all retrieved documents into a list with index headers
    formatted_docs = []
    for idx, d in enumerate(documents):
        formatted_docs.append(
            f"--- DOCUMENT INDEX {idx} ---\n"
            f"Source: {d.get('source', 'unknown')}\n"
            f"Content:\n{d['text']}"
        )
    documents_block = "\n\n".join(formatted_docs)
    
    prompt = f"""System: {system_prompt}

User Question: {question}

Retrieved Documents List:
{documents_block}

Grade the relevance of each document by index in the expected structured schema:"""
    
    filtered_docs = []
    try:
        # Invoke batched grader
        response = structured_llm_grader.invoke(prompt)
        
        # Create a lookup map for results
        results_map = {res.index: res.relevant for res in response.results}
        
        for idx, d in enumerate(documents):
            source_name = d.get("source", "unknown")
            page_num = d.get("page", 0)
            
            # Retrieve relevant grade, default to True (safe fallback) if index not found in output
            is_relevant = results_map.get(idx, True)
            
            if is_relevant:
                print(f"   ✅ Relevant: Chunk from '{source_name}' (Page {page_num}) kept.")
                filtered_docs.append(d)
            else:
                print(f"   ❌ Irrelevant: Chunk from '{source_name}' (Page {page_num}) discarded.")
                
    except Exception as e:
        # Safe fallback: retain all documents if evaluation fails to avoid breaking downstream nodes
        print(f"   ⚠️ Error during batched grading: {e}. Retaining all chunks as fallback.")
        filtered_docs = documents
        
    # Determine overall retrieval status
    final_grade = "pass" if len(filtered_docs) > 0 else "fail"
    print(f"⚖️ [Agent: Evaluator] Grading complete. Status: {final_grade.upper()} ({len(filtered_docs)}/{len(documents)} relevant documents).")
    
    return {
        "legal_docs": filtered_docs,
        "retrieval_grade": final_grade
    }