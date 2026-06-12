import sys
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from langgraph.graph import StateGraph, END
from typing import Dict, Any

# Import shared state definition and config
from src.state import AuditorState
from src.config import Config

# Import agent nodes
from src.agents.classifier import classify_document_type
from src.agents.retriever import retrieve_legal_frameworks
from src.agents.evaluator import evaluate_documents
from src.agents.synthesizer import synthesize_report

from langchain_google_genai import ChatGoogleGenerativeAI

# --------------------------------------------------
# Configuration
# --------------------------------------------------
MAX_RETRIES = 3

# --------------------------------------------------
# Helper Node: Query Rewriter
# --------------------------------------------------
def rewrite_query(state: AuditorState) -> Dict[str, Any]:
    """
    Agent: The Search Optimizer (Query Rewriter)
    Rewrites the search query to improve Qdrant retrieval quality.
    Also increments the retry counter to prevent infinite loops.
    """
    question = state["question"]
    current_query = state.get("search_query") or question
    retry_count = state.get("retry_count", 0) + 1
    
    print(f"\n🔄 [Agent: Query Rewriter] Retrieval failed (Retry {retry_count}/{MAX_RETRIES}).")
    print(f"🔄 [Agent: Query Rewriter] Optimizing query for vector similarity search...")
    
    # Initialize LLM for query rewriting
    llm = ChatGoogleGenerativeAI(
        model=Config.DEFAULT_MODEL,
        api_key=Config.GEMINI_API_KEY,
        temperature=0.2 # Low temperature but slight variance for synonyms
    )
    
    prompt = f"""You are a legal database search optimizer. 
    Our previous database query: "{current_query}"
    failed to retrieve relevant document clauses to answer the user's question: "{question}"
    
    Rewrite this question to be an optimal vector search query.
    - Focus on the core legal concepts, nouns, and synonyms.
    - Remove conversational words (e.g. "please find", "do we have", "tell me").
    - Keep it under 15 words.
    
    Return ONLY the rewritten search query text. Do not include any explanations, introduction, or quotes."""
    
    try:
        response = llm.invoke(prompt)
        raw_content = response.content
        if isinstance(raw_content, list):
            content_str = ""
            for block in raw_content:
                if isinstance(block, dict) and "text" in block:
                    content_str += block["text"]
                elif isinstance(block, str):
                    content_str += block
        else:
            content_str = raw_content
        rewritten = content_str.strip()
        print(f"🔄 [Agent: Query Rewriter] Rewrote query to: '{rewritten}'")
    except Exception as e:
        print(f"⚠️ [Agent: Query Rewriter] API call failed: {e}. Re-using previous query.")
        rewritten = current_query
        
    return {
        "search_query": rewritten,
        "retry_count": retry_count
    }

# --------------------------------------------------
# Routing Decisions (Conditional Edges)
# --------------------------------------------------
def route_by_category(state: AuditorState) -> str:
    """
    Routes based on the classified legal category.
    If the question matches one of our indexed legal document categories, we route to retriever.
    Otherwise, we bypass retrieval and go directly to synthesis.
    """
    category = state.get("document_type", "Other")
    
    if category in ["Lease", "NDA", "Adoption", "Trust", "Property"]:
        print(f"🗺️ [Router] Category is '{category}'. Routing to Retriever...")
        return "retriever"
    
    print(f"🗺️ [Router] Category is '{category}'. Skipping database retrieval. Routing directly to Synthesizer...")
    return "synthesizer"

def route_after_evaluation(state: AuditorState) -> str:
    """
    Evaluates retrieval quality and decides next step.
    
    Cases:
    1. Documents are relevant -> Go to Synthesizer.
    2. Documents are irrelevant, but retry limit reached -> Go to Synthesizer (to avoid infinite loops).
    3. Documents are irrelevant, retry limit NOT reached -> Route to Query Rewriter.
    """
    retrieval_grade = state.get("retrieval_grade", "fail")
    retry_count = state.get("retry_count", 0)
    
    print(f"\n🗺️ [Router] Checking quality: Grade={retrieval_grade.upper()} | Retry Count={retry_count}/{MAX_RETRIES}")
    
    if retrieval_grade.lower() == "pass":
        print("✅ [Router] Valid legal clauses available. Routing to Synthesizer...")
        return "synthesizer"
        
    if retry_count >= MAX_RETRIES:
        print(f"⚠️ [Router] Maximum retries ({MAX_RETRIES}) reached. Proceeding to Synthesizer with best available context...")
        return "synthesizer"
        
    print("🔄 [Router] Retrieval failed. Routing to Query Rewriter...")
    return "rewrite"

# --------------------------------------------------
# State Graph Construction
# --------------------------------------------------
workflow = StateGraph(AuditorState)

# 1. Register Nodes
workflow.add_node("classifier", classify_document_type)
workflow.add_node("retriever", retrieve_legal_frameworks)
workflow.add_node("evaluator", evaluate_documents)
workflow.add_node("rewrite", rewrite_query)
workflow.add_node("synthesizer", synthesize_report)

# 2. Set Entry Point
workflow.set_entry_point("classifier")

# 3. Add Edges & Conditional Routing
# Route from Classifier
workflow.add_conditional_edges(
    "classifier",
    route_by_category,
    {
        "retriever": "retriever",
        "synthesizer": "synthesizer"
    }
)

# Route from Retriever
workflow.add_edge("retriever", "evaluator")

# Route from Evaluator (CRAG Decision Point)
workflow.add_conditional_edges(
    "evaluator",
    route_after_evaluation,
    {
        "synthesizer": "synthesizer",
        "rewrite": "rewrite"
    }
)

# Route from Query Rewriter (Back to Retriever)
workflow.add_edge("rewrite", "retriever")

# Route from Synthesizer to Completion
workflow.add_edge("synthesizer", END)

# 4. Compile Graph
app = workflow.compile()

# --------------------------------------------------
# local Test Execution
# --------------------------------------------------
if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()
    
    # Simple test state
    test_state = {
        "question": "What are the rules regarding tenant obligations for repairs in our lease deeds?",
        "legal_docs": [],
        "internal_docs": [],
        "retrieval_grade": "fail",
        "retry_count": 0,
        "search_query": "",
        "audit_report": ""
    }
    
    print("🚀 Running Graph Test Loop...")
    result = app.invoke(test_state)
    
    print("\n" + "=" * 60)
    print("FINAL AUDIT REPORT")
    print("=" * 60)
    print(result.get("audit_report"))