import os
import sys
import json
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# Add the project root to the import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.graph import app as graph_app
from src.config import Config

# Initialize FastAPI App
app = FastAPI(
    title="Agentic Legal Advisor API",
    description="Production-quality multi-agent RAG system for legal compliance audits",
    version="1.0.0"
)

# Configure CORS Middleware
# Allows Streamlit UI (port 8501) or React UIs to communicate with our FastAPI backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific trusted domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Request & Response Schemas (Pydantic Models)
# --------------------------------------------------
class AuditRequest(BaseModel):
    question: str = Field(
        ..., 
        description="The legal query or compliance question to analyze.",
        example="What are the tenant obligations for repairs in our lease deeds?"
    )
    internal_docs: List[str] = Field(
        default=[], 
        description="Optional list of internal policies/rules to align against.",
        example=[]
    )

class AuditResponse(BaseModel):
    question: str
    document_type: str
    legal_docs: List[Dict[str, Any]]
    internal_docs: List[str]
    retrieval_grade: str
    audit_report: str
    retry_count: int

# --------------------------------------------------
# Endpoints
# --------------------------------------------------
@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    """
    Performs service health checks.
    Verifies that configuration keys and database storage paths are accessible.
    """
    try:
        # Check if local persistent Qdrant database directory is writable/existent
        QDRANT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "qdrant_storage"))
        db_healthy = os.path.exists(QDRANT_PATH)
        
        # Check Gemini API setup
        api_healthy = bool(Config.GEMINI_API_KEY)
        
        if not db_healthy or not api_healthy:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                detail="Database storage or LLM API keys are misconfigured."
            )
            
        return {
            "status": "healthy",
            "database_persistent_path": QDRANT_PATH,
            "llm_api_key_loaded": api_healthy,
            "models_configured": {
                "default": Config.DEFAULT_MODEL,
                "advanced": Config.ADVANCED_MODEL
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )

@app.post("/api/audit", response_model=AuditResponse, tags=["Legal Auditor"])
async def run_compliance_audit(request: AuditRequest):
    """
    Executes the complete multi-agent compliance audit workflow synchronously.
    Returns the final graph state after all nodes finish execution.
    """
    # Build initial LangGraph state from the API request
    initial_state = {
        "question": request.question,
        "legal_docs": [],
        "internal_docs": request.internal_docs,
        "retrieval_grade": "fail",
        "retry_count": 0,
        "search_query": "",
        "audit_report": ""
    }
    
    print(f"\n⚡ FastAPI: Invoking graph query: '{request.question}'")
    
    try:
        # Run graph asynchronously to prevent blocking the event loop
        final_state = await graph_app.ainvoke(initial_state)
        
        return AuditResponse(
            question=final_state.get("question", ""),
            document_type=final_state.get("document_type", ""),
            legal_docs=final_state.get("legal_docs", []),
            internal_docs=final_state.get("internal_docs", []),
            retrieval_grade=final_state.get("retrieval_grade", "fail"),
            audit_report=final_state.get("audit_report", ""),
            retry_count=final_state.get("retry_count", 0)
        )
    except Exception as e:
        print(f"❌ FastAPI Error during graph execution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal agent execution failure: {str(e)}"
        )

@app.post("/api/audit/stream", tags=["Legal Auditor"])
async def stream_compliance_audit(request: AuditRequest):
    """
    Streams multi-agent node updates in real-time as they execute.
    Leverages Server-Sent Events (SSE) to send updates back to the client.
    """
    initial_state = {
        "question": request.question,
        "legal_docs": [],
        "internal_docs": request.internal_docs,
        "retrieval_grade": "fail",
        "retry_count": 0,
        "search_query": "",
        "audit_report": ""
    }
    
    print(f"\n⚡ FastAPI: Opening real-time stream for query: '{request.question}'")

    async def event_generator():
        try:
            # Stream graph updates after each node execution
            async for chunk in graph_app.astream(initial_state, stream_mode="updates"):
                # chunk format: {"node_name": {updated_state_fields}}
                # Yield as an SSE data payload
                yield f"data: {json.dumps(chunk)}\n\n"
                # Brief sleep to allow smooth flushing of outputs to client
                await asyncio.sleep(0.01)
        except Exception as e:
            error_data = {"error": f"Stream execution error: {str(e)}"}
            yield f"data: {json.dumps(error_data)}\n\n"
            
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

# --------------------------------------------------
# Entry Point
# --------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    # Start the server on port 8000
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
