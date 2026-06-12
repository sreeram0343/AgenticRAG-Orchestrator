import os
import sys
import json
import requests
import streamlit as st

# Force UTF-8 encoding for standard output on Windows to prevent emoji encoding crashes
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Backend Endpoint Configuration
BACKEND_URL = "http://127.0.0.1:8000"

# --------------------------------------------------
# Page Configurations & Styling
# --------------------------------------------------
st.set_page_config(
    page_title="Agentic Legal Advisor",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium CSS Injection for sleek dark/corporate slate aesthetics
st.markdown("""
<style>
    /* Main Background & Font Styling */
    .stApp {
        background-color: #0f172a;
        color: #f1f5f9;
    }
    
    /* Header Card */
    .header-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    
    .header-title {
        font-family: 'Outfit', 'Segoe UI', sans-serif;
        font-size: 2.2rem;
        font-weight: 700;
        color: #38bdf8;
        margin: 0 0 8px 0;
    }
    
    .header-subtitle {
        font-size: 1.1rem;
        color: #94a3b8;
        margin: 0;
    }
    
    /* Agent Node Badges */
    .agent-log {
        background-color: #1e293b;
        border-left: 4px solid #38bdf8;
        padding: 12px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 8px;
        font-family: monospace;
        color: #e2e8f0;
    }
    
    /* Custom Sidebar Card */
    .sidebar-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Sidebar: Telemetry & Config Checks
# --------------------------------------------------
st.sidebar.markdown("<h2 style='color: #38bdf8; margin-bottom: 0px;'>⚙️ System Diagnostics</h2>", unsafe_allow_html=True)
st.sidebar.write("---")

# Verify Backend Connection
try:
    health_response = requests.get(f"{BACKEND_URL}/health", timeout=3)
    if health_response.status_code == 200:
        health_data = health_response.json()
        st.sidebar.markdown("""
        <div class="sidebar-card">
            <span style="color: #22c55e; font-weight: bold;">🟢 API Server Healthy</span><br>
            <span style="font-size: 0.85rem; color: #94a3b8;">Connected to local orchestrator</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Display Database & Model details in sidebar
        st.sidebar.markdown(f"**Database Persistent Path:**\n`{health_data.get('database_persistent_path')}`")
        st.sidebar.markdown("**Active Agents Configuration:**")
        st.sidebar.write(f"- Triage: `{health_data['models_configured']['default']}`")
        st.sidebar.write(f"- Quality Evaluator: `{health_data['models_configured']['default']}`")
        st.sidebar.write(f"- Compliance Generator: `{health_data['models_configured']['advanced']}`")
    else:
        st.sidebar.error("🔴 API Health Check Failed: Server misconfigured.")
except Exception:
    st.sidebar.markdown("""
    <div class="sidebar-card" style="border-color: #ef4444;">
        <span style="color: #ef4444; font-weight: bold;">🔴 API Server Offline</span><br>
        <span style="font-size: 0.85rem; color: #94a3b8;">Unable to connect to port 8000. Start backend with 'python src/app.py'</span>
    </div>
    """, unsafe_allow_html=True)

st.sidebar.write("---")
st.sidebar.info("💡 **Guidelines:** Input legal questions related to your PDF repository. The system classified topics, performs metadata-filtered vector lookups, evaluates chunk quality, and writes citation-backed reports.")

# --------------------------------------------------
# Main UI Layout
# --------------------------------------------------
# Injected Title Header
st.markdown("""
<div class="header-card">
    <h1 class="header-title">⚖️ AGENTIC LEGAL ADVISOR</h1>
    <p class="header-subtitle">Production-grade Multi-Agent Legal RAG & Citations System</p>
</div>
""", unsafe_allow_html=True)

# Main Application Tabs
tab_auditor, tab_ingestion = st.tabs(["💼 Compliance Auditor", "📁 Index Metadata"])

with tab_auditor:
    # Form layout
    st.markdown("### 🔍 Initiate Compliance Audit")
    
    question_input = st.text_area(
        "Enter your legal question / compliance standard to audit:",
        value="What are the rules regarding tenant obligations for repairs in our lease deeds?",
        height=100,
        placeholder="Type your question here..."
    )
    
    with st.expander("📝 Optional: Align Against Company Internal Policies", expanded=False):
        internal_input = st.text_area(
            "Paste internal policy guidelines or rules (one statement per line):",
            value="",
            height=80,
            placeholder="Example: Tenant must request approval for changes exceeding $500."
        )

    # Process internal policy lines
    internal_docs = [line.strip() for line in internal_input.split("\n") if line.strip()]

    # Trigger compliance audit
    if st.button("🚀 Run Compliance Audit", use_container_width=True):
        if not question_input.strip():
            st.warning("Please enter a query question.")
        else:
            # Create placeholders for live execution logs and outputs
            st.markdown("### 🕵️‍♂️ Agent Execution Trace")
            trace_status = st.status("Initializing agent coordinators...", expanded=True)
            
            # Placeholders for intermediate values
            category_placeholder = st.empty()
            docs_expander_placeholder = st.empty()
            report_placeholder = st.empty()
            
            # Request payload
            payload = {
                "question": question_input,
                "internal_docs": internal_docs
            }
            
            # Trigger real-time streaming request
            try:
                # Open connection to the FastAPI SSE endpoint
                stream_url = f"{BACKEND_URL}/api/audit/stream"
                response = requests.post(stream_url, json=payload, stream=True)
                
                # State trackers for UI rendering
                document_type = "Pending"
                legal_docs = []
                retrieval_grade = "Pending"
                final_report = ""
                retry_count = 0
                
                for line in response.iter_lines():
                    if line:
                        # Parse Server-Sent Event payload: b"data: {...}"
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith("data: "):
                            event_data = json.loads(decoded_line[6:])
                            
                            # Check for stream errors
                            if "error" in event_data:
                                trace_status.error(f"Execution Error: {event_data['error']}")
                                st.error(event_data['error'])
                                break
                            
                            # Process LangGraph node outputs
                            # Format: {"node_name": {state_updates}}
                            for node_name, state_update in event_data.items():
                                if node_name == "classifier":
                                    document_type = state_update.get("document_type", "Other")
                                    trace_status.write(f"🔮 **Classifier Agent:** Categorized query domain as `{document_type}`.")
                                    category_placeholder.info(f"🏷️ **Classified Document Category:** `{document_type}`")
                                    
                                elif node_name == "retriever":
                                    legal_docs = state_update.get("legal_docs", [])
                                    trace_status.write(f"🕵️‍♂️ **Retriever Agent:** Searched database. Found `{len(legal_docs)}` candidate clauses.")
                                    
                                elif node_name == "evaluator":
                                    legal_docs = state_update.get("legal_docs", [])
                                    retrieval_grade = state_update.get("retrieval_grade", "fail")
                                    trace_status.write(
                                        f"⚖️ **Evaluator Agent:** Inspected candidates. Grading: **{retrieval_grade.upper()}** "
                                        f"({len(legal_docs)} relevant clauses retained)."
                                    )
                                    
                                    # Render the retrieved documents inside the expander live
                                    with docs_expander_placeholder.expander("📚 View Inspected Legal Clauses & Citations", expanded=False):
                                        if not legal_docs:
                                            st.write("No relevant documents retained.")
                                        for idx, doc in enumerate(legal_docs):
                                            st.markdown(f"""
                                            <div style="background-color: #1e293b; padding: 12px; border-radius: 8px; margin-bottom: 12px; border: 1px solid #334155;">
                                                <strong>Snippet #{idx + 1}</strong> (Score: {doc['score']:.4f})<br>
                                                <span style="font-size: 0.85rem; color: #38bdf8;">File: {doc['source']} | Page: {doc['page']}</span>
                                                <p style="margin-top: 8px; font-style: italic; color: #cbd5e1;">"{doc['text']}"</p>
                                            </div>
                                            """, unsafe_allow_html=True)
                                            
                                elif node_name == "rewrite":
                                    retry_count = state_update.get("retry_count", 0)
                                    rewritten_query = state_update.get("search_query", "")
                                    trace_status.write(
                                        f"🔄 **Query Rewriter Agent:** Quality grade failed. "
                                        f"Initiating retry loop `{retry_count}`. Optimizing search keywords to: *\"{rewritten_query}\"*"
                                    )
                                    
                                elif node_name == "synthesizer":
                                    final_report = state_update.get("audit_report", "")
                                    trace_status.write("📝 **Synthesizer Agent:** Drafting report with inline citations...")
                
                # Check if final report was generated
                if final_report:
                    trace_status.update(label="✅ Audit completed successfully!", state="complete", expanded=False)
                    st.success("Analysis Complete!")
                    
                    st.markdown("---")
                    st.markdown("### 📝 Citation-Backed Compliance Report")
                    
                    # Display the Markdown report beautifully
                    st.markdown(final_report)
                    
                    # Add Download Button for report export
                    st.download_button(
                        label="💾 Export Report (Markdown)",
                        data=final_report,
                        file_name="legal_compliance_report.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
                else:
                    trace_status.update(label="❌ Audit failed to compile report.", state="error", expanded=True)
                    st.error("Synthesizer failed to generate a report. Verify vector store data and LLM settings.")
                    
            except Exception as e:
                trace_status.update(label="❌ System Connection Error.", state="error", expanded=True)
                st.error(f"Could not connect to FastAPI server at {BACKEND_URL}: {str(e)}")

with tab_ingestion:
    st.markdown("### 📁 Persistent Document Store Index")
    st.write("Below are the settings and status of the current persistent vector storage:")
    
    try:
        health_response = requests.get(f"{BACKEND_URL}/health", timeout=3)
        if health_response.status_code == 200:
            h_data = health_response.json()
            st.info(f"📂 **Collection Name:** `legal_frameworks`  \n"
                    f"💾 **Storage Type:** Local Disk RocksDB  \n"
                    f"📍 **Persistent Directory Path:** `{h_data.get('database_persistent_path')}`")
            
            # Simple metadata count check
            st.success("Database Status: PERSISTED & ONLINE")
        else:
            st.error("API Server unhealthy.")
    except Exception:
        st.warning("⚠️ FastAPI Backend is offline. Ingestion status unavailable.")
