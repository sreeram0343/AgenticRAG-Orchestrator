from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from src.state import AuditorState
from src.config import Config

def synthesize_report(state: AuditorState) -> Dict[str, Any]:
    """
    Agent: The Legal Clerk (Synthesizer)
    Reads the verified legal documents, analyzes them against the user's question,
    and drafts a formal, citation-backed legal compliance report.
    """
    print("\n📝 [Agent: Synthesizer] Draft compliance audit report with inline citations...")
    
    question = state["question"]
    legal_docs = state.get("legal_docs", [])
    internal_docs = state.get("internal_docs", [])
    
    if not legal_docs:
        print("⚠️ [Agent: Synthesizer] No legal context available. Drafting warning report.")
        legal_docs_text = "No relevant legal clauses were successfully retrieved from the database."
    else:
        # Format the retrieved legal documents into a readable block with explicit metadata headers
        formatted_chunks = []
        for idx, doc in enumerate(legal_docs):
            formatted_chunks.append(
                f"--- LEGAL DOCUMENT CHUNK {idx + 1} ---\n"
                f"Source Document: {doc['source']}\n"
                f"Page Number: {doc['page']}\n"
                f"Content:\n{doc['text']}"
            )
        legal_docs_text = "\n\n".join(formatted_chunks)
        
    # Format internal documents if any exist
    internal_docs_text = "\n\n".join(internal_docs) if internal_docs else "No internal policies provided."
    
    prompt = f"""You are a Senior Legal Compliance Auditor. 
    Review the user's question, the retrieved legal frameworks, and any internal policies. 
    Draft a comprehensive, citation-backed Legal Guidance Report.
    
    User Question:
    {question}
    
    Retrieved Legal Framework Documents (Grounding Context):
    {legal_docs_text}
    
    Internal Policies (Grounding Context):
    {internal_docs_text}
    
    Requirements for the Report:
    1. Organize the report into the following exact sections:
       - **Executive Summary**: A high-level overview of the compliance check.
       - **Findings**: The specific facts and clauses found.
       - **Compliance Status**: A clear assessment of whether the condition is compliant (e.g. COMPLIANT, NON-COMPLIANT, or PARTIALLY COMPLIANT).
       - **Risk Assessment**: The risks of non-compliance.
       - **Recommendations**: Concrete action steps.
       - **Final Verdict**: A concluding summary.
       
    2. CRITICAL CITATION REQUIREMENT: For every legal rule, finding, or conclusion you state, you MUST cite the source document and page number in inline brackets immediately following the sentence, e.g., "[Source: test_data.pdf, Page: 5]".
    3. Rely ONLY on the provided legal documents and internal policies. Do NOT make up any legal terms, rules, or agreements. If information is missing, state it clearly as a risk or gap in the Findings section.
    
    Write the report in professional, objective legal tone in markdown format:"""

    # Model invocation with rate-limit and quota fallback
    try:
        # Attempt to use the advanced model first
        llm = ChatGoogleGenerativeAI(
            model=Config.ADVANCED_MODEL,
            api_key=Config.GEMINI_API_KEY,
            temperature=0
        )
        response = llm.invoke(prompt)
    except Exception as e:
        error_msg = str(e).lower()
        if "429" in error_msg or "quota" in error_msg or "exhausted" in error_msg or "limit" in error_msg:
            print(f"⚠️ [Agent: Synthesizer] Advanced model ({Config.ADVANCED_MODEL}) quota exceeded. Falling back to default model ({Config.DEFAULT_MODEL})...")
            llm = ChatGoogleGenerativeAI(
                model=Config.DEFAULT_MODEL,
                api_key=Config.GEMINI_API_KEY,
                temperature=0
            )
            response = llm.invoke(prompt)
        else:
            raise e
            
    raw_content = response.content
    if isinstance(raw_content, list):
        report_content = ""
        for block in raw_content:
            if isinstance(block, dict) and "text" in block:
                report_content += block["text"]
            elif isinstance(block, str):
                report_content += block
    else:
        report_content = raw_content
    
    print("✅ [Agent: Synthesizer] Compliance report successfully generated.")
    
    return {
        "audit_report": report_content
    }