from typing import Dict, Any
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

# Import our shared state and config
from src.state import AuditorState
from src.config import Config

# Define the structured output schema for the evaluator
class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""
    binary_score: str = Field(
        description="Are the documents relevant to the question? Return 'yes' or 'no'"
    )

def evaluate_documents(state: AuditorState) -> Dict[str, Any]:
    """
    Agent: The Internal Inspector (Evaluator)
    Acts as a filter. Reads the documents pulled by the Retriever and discards
    any that do not actually help answer the specific compliance question.
    Also updates the retrieval_grade in the state.
    """
    print("\n⚖️ [Agent: Evaluator] Grading retrieved legal clauses for strict relevance...")
    
    question = state["question"]
    documents = state.get("legal_docs", [])
    
    if not documents:
        print("⚠️ [Agent: Evaluator] No documents retrieved. Grading search as FAIL.")
        return {"legal_docs": [], "retrieval_grade": "fail"}
    
    # Initialize deterministic Gemini 1.5 Flash model
    llm = ChatGoogleGenerativeAI(
        model=Config.DEFAULT_MODEL,
        api_key=Config.GEMINI_API_KEY,
        temperature=0
    )
    
    # Force structured output using the Pydantic schema
    structured_llm_grader = llm.with_structured_output(GradeDocuments)
    
    system_prompt = """You are a strict, emotionless legal compliance evaluator. 
    Assess if the retrieved document contains ANY information relevant to answering the user's question. 
    If the document contains keywords, concepts, or clauses mathematically or legally related to the user's question, grade it as 'yes'.
    Otherwise, grade it as 'no'. 
    Do NOT answer the question. You are only grading the relevance of the text."""
    
    grade_prompt = PromptTemplate(
        template="System: {system}\n\nUser Question: {question}\n\nRetrieved Document:\n{document}\n\nGrade:",
        input_variables=["system", "question", "document"],
    )
    
    # Chain prompt and structured LLM
    retriever_grader = grade_prompt | structured_llm_grader
    
    # Grade each document
    filtered_docs = []
    for d in documents:
        doc_text = d["text"]
        source_name = d.get("source", "unknown")
        page_num = d.get("page", 0)
        
        try:
            score = retriever_grader.invoke({
                "system": system_prompt, 
                "question": question, 
                "document": doc_text
            })
            grade = score.binary_score
            
            if grade.lower().strip() == "yes":
                print(f"   ✅ Relevant: Chunk from '{source_name}' (Page {page_num}) kept.")
                filtered_docs.append(d)
            else:
                print(f"   ❌ Irrelevant: Chunk from '{source_name}' (Page {page_num}) discarded.")
        except Exception as e:
            # Safe fallback: retain the document if evaluation fails to avoid dropping potential answers
            print(f"   ⚠️ Error grading chunk from '{source_name}' page {page_num}: {e}. Retaining by default.")
            filtered_docs.append(d)
            
    # Determine overall retrieval status
    final_grade = "pass" if len(filtered_docs) > 0 else "fail"
    print(f"⚖️ [Agent: Evaluator] Grading complete. Status: {final_grade.upper()} ({len(filtered_docs)}/{len(documents)} relevant documents).")
    
    return {
        "legal_docs": filtered_docs,
        "retrieval_grade": final_grade
    }