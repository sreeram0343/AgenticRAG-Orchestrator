from typing import Dict, Any
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

# Import our shared state and config
from src.state import AuditorState
from src.config import Config

# 1. Define the exact structure we want the AI to return
class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""
    binary_score: str = Field(description="Documents are relevant to the question, 'yes' or 'no'")

def evaluate_legal_relevance(state: AuditorState) -> Dict[str, Any]:
    """
    Agent 2: The Internal Inspector (Evaluator)
    Acts as a filter. Reads the documents pulled by the Retriever and discards
    any that do not actually help answer the specific compliance question.
    """
    print("\n⚖️ [Agent: Evaluator] Grading retrieved legal clauses for strict relevance...")
    
    question = state["question"]
    documents = state.get("legal_docs", [])
    
    # 2. Initialize the "Brain" of the Evaluator (Using Gemini 1.5 Flash for speed)
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        api_key=Config.GEMINI_API_KEY,
        temperature=0 # Temperature 0 makes it deterministic and strict
    )
    
    # 3. Force the LLM to output our Pydantic schema
    structured_llm_grader = llm.with_structured_output(GradeDocuments)
    
    # 4. Give the Agent its strict instructions
    system_prompt = """You are a strict, emotionless legal compliance evaluator. 
    Assess if the retrieved document contains ANY information relevant to answering the user's question. 
    If the document contains keywords, concepts, or clauses mathematically or legally related to the user's question, grade it as 'yes'.
    Otherwise, grade it as 'no'. 
    Do NOT answer the question. You are only grading the relevance of the text."""
    
    grade_prompt = PromptTemplate(
        template="System: {system}\n\nUser Question: {question}\n\nRetrieved Document:\n{document}\n\nGrade:",
        input_variables=["system", "question", "document"],
    )
    
    # Combine the prompt and the LLM into a chain
    retriever_grader = grade_prompt | structured_llm_grader
    
    # 5. Evaluate each document one by one
    filtered_docs = []
    for d in documents:
        # Ask the LLM to grade it
        score = retriever_grader.invoke({"system": system_prompt, "question": question, "document": d})
        grade = score.binary_score
        
        if grade.lower() == "yes":
            print("   ✅ Valid legal clause found. Keeping in memory.")
            filtered_docs.append(d)
        else:
            print("   ❌ Irrelevant legal clause detected. Discarding to prevent hallucinations.")
            
    # 6. Update the shared memory with only the verified, highly-relevant documents
    return {"legal_docs": filtered_docs}