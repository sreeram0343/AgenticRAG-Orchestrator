import os
import sys
import json
import requests
import subprocess
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
    page_title="Agentic Legal Auditor",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium CSS Injection for sleek dark/glassmorphic slate aesthetics
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap');

    /* Main App Container background */
    .stApp {
        background: radial-gradient(circle at 80% 20%, #1e1b4b 0%, #0f172a 100%);
        color: #f1f5f9;
        font-family: 'Inter', sans-serif;
    }

    /* Sidebar Container Deep Black Background */
    [data-testid="stSidebar"] {
        background-color: #030712 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    
    /* Premium Header Banner */
    .header-card {
        background: rgba(30, 41, 59, 0.45);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 32px;
        margin-bottom: 28px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }
    
    .header-title {
        font-family: 'Outfit', sans-serif;
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 6px 0;
        letter-spacing: -0.5px;
    }
    
    .header-subtitle {
        font-size: 1.15rem;
        color: #94a3b8;
        margin: 0;
        font-weight: 400;
    }
    
    /* Sleek Sidebar Card */
    .sidebar-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }

    /* Pulsing Green Circle for API Health */
    .pulse-green {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #22c55e;
        box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7);
        animation: pulse-green-anim 1.8s infinite;
        margin-right: 8px;
    }

    @keyframes pulse-green-anim {
        0% {
            transform: scale(0.95);
            box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7);
        }
        70% {
            transform: scale(1);
            box-shadow: 0 0 0 8px rgba(34, 197, 94, 0);
        }
        100% {
            transform: scale(0.95);
            box-shadow: 0 0 0 0 rgba(34, 197, 94, 0);
        }
    }

    /* Custom Category Badges */
    .category-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .badge-lease { background-color: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }
    .badge-nda { background-color: rgba(167, 139, 250, 0.15); color: #a78bfa; border: 1px solid rgba(167, 139, 250, 0.3); }
    .badge-adoption { background-color: rgba(244, 114, 182, 0.15); color: #f472b6; border: 1px solid rgba(244, 114, 182, 0.3); }
    .badge-trust { background-color: rgba(251, 191, 36, 0.15); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.3); }
    .badge-property { background-color: rgba(52, 211, 153, 0.15); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.3); }
    .badge-other { background-color: rgba(148, 163, 184, 0.15); color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.3); }

    /* Custom Cards for Retrieved Clauses */
    .clause-card {
        background: rgba(30, 41, 59, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 12px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }

    .clause-card:hover {
        border-color: rgba(56, 189, 248, 0.25);
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    /* Clean Sub-Headers */
    .sub-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        color: #f1f5f9;
        margin-top: 15px;
        margin-bottom: 10px;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: rgba(15, 23, 42, 0.4);
        padding: 6px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.03);
    }

    .stTabs [data-baseweb="tab"] {
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        color: #94a3b8;
        padding: 8px 18px;
        border-radius: 6px;
        border: none !important;
        transition: all 0.2s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #38bdf8;
        background-color: rgba(255, 255, 255, 0.03);
    }

    .stTabs [aria-selected="true"] {
        background-color: rgba(56, 189, 248, 0.12) !important;
        color: #38bdf8 !important;
        border: 1px solid rgba(56, 189, 248, 0.25) !important;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Sidebar: Telemetry & Diagnostics
# --------------------------------------------------
st.sidebar.markdown("<h2 style='color: #38bdf8; font-family: \"Outfit\"; margin-bottom: 0px;'>Diagnostics</h2>", unsafe_allow_html=True)
st.sidebar.write("---")

api_online = False
db_persistent_path = "Unknown"
models_configured = {"default": "gemini-3.5-flash", "advanced": "gemini-3.5-flash"}

try:
    health_response = requests.get(f"{BACKEND_URL}/health", timeout=3)
    if health_response.status_code == 200:
        api_online = True
        health_data = health_response.json()
        db_persistent_path = health_data.get("database_persistent_path", "Local RocksDB")
        models_configured = health_data.get("models_configured", models_configured)
except Exception:
    pass

if api_online:
    st.sidebar.markdown(f"""
    <div class="sidebar-card">
        <span class="pulse-green"></span>
        <span style="color: #22c55e; font-weight: bold; font-family: 'Outfit';">API Backend Online</span><br>
        <span style="font-size: 0.85rem; color: #94a3b8;">Orchestrator connected successfully</span>
    </div>
    """, unsafe_allow_html=True)
else:
    st.sidebar.markdown("""
    <div class="sidebar-card" style="border-color: rgba(239, 68, 68, 0.3);">
        <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #ef4444; margin-right: 8px;"></span>
        <span style="color: #ef4444; font-weight: bold; font-family: 'Outfit';">API Backend Offline</span><br>
        <span style="font-size: 0.85rem; color: #94a3b8;">Run "python src/app.py" to connect</span>
    </div>
    """, unsafe_allow_html=True)

st.sidebar.markdown(f"**Database Storage Path:**\n`{db_persistent_path}`")

st.sidebar.markdown("**Agent Core Configuration:**")
st.sidebar.markdown(f"""
- **Triage (Classifier)**:  
  `{models_configured['default']}`
- **Auditor (Evaluator)**:  
  `{models_configured['default']}`
- **Generator (Synthesizer)**:  
  `{models_configured['advanced']}`
""")

st.sidebar.write("---")
st.sidebar.markdown("""
<div style="font-size: 0.85rem; color: #94a3b8; line-height: 1.4;">
    <strong>System Core Workflow:</strong><br>
    1. Triage query using a gatekeeper classifier.<br>
    2. Retrieve legal context with metadata filters.<br>
    3. Audit context strictness using corrective-evaluations.<br>
    4. Auto-optimize search query on relevance failure.<br>
    5. Draft a formal report complete with citation links.
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Main UI Layout Header
# --------------------------------------------------
st.markdown("""
<div class="header-card">
    <h1 class="header-title">AGENTIC LEGAL COMPLIANCE AUDITOR</h1>
    <p class="header-subtitle">Multi-Agent Self-Correcting RAG Auditor & Citations Engine</p>
</div>
""", unsafe_allow_html=True)

# Tabs
tab_auditor, tab_repository, tab_ingestion = st.tabs([
    "Compliance Auditor", 
    "Document Repository", 
    "Database & Index Settings"
])

# --------------------------------------------------
# Tab 1: Compliance Auditor
# --------------------------------------------------
with tab_auditor:
    st.markdown("<h3 class='sub-title'>Initiate Compliance Audit</h3>", unsafe_allow_html=True)
    
    question_input = st.text_area(
        "Enter your legal question, compliance standard, or policy query:",
        value="What are the rules regarding tenant obligations for repairs in our lease deeds?",
        height=100,
        placeholder="e.g. Do our confidentiality requirements apply after contract termination?"
    )
    
    with st.expander("Optional: Align Audit Against Company Internal Policies", expanded=False):
        internal_input = st.text_area(
            "Paste internal corporate guidelines or rules to compare against (one statement per line):",
            value="Tenant must maintain building structures in good condition.\nTenant is responsible for any repair request under $500.",
            height=100,
            placeholder="Example: Tenant must request approval for renovations."
        )

    # Process internal policy lines
    internal_docs = [line.strip() for line in internal_input.split("\n") if line.strip()]

    # Run Compliance Audit button
    if st.button("Run Multi-Agent Audit", use_container_width=True):
        if not question_input.strip():
            st.warning("Please enter a legal query or question to audit.")
        elif not api_online:
            st.error("Cannot run audit: FastAPI Backend is offline. Start the backend with 'python src/app.py' first.")
        else:
            st.markdown("---")
            st.markdown("<h3 class='sub-title'>Agent Collaboration Trace</h3>", unsafe_allow_html=True)
            
            trace_status = st.status("Initializing agent coordinators...", expanded=True)
            
            # Placeholders for dynamic rendering
            category_placeholder = st.empty()
            docs_expander_placeholder = st.empty()
            report_placeholder = st.empty()
            
            payload = {
                "question": question_input,
                "internal_docs": internal_docs
            }
            
            try:
                stream_url = f"{BACKEND_URL}/api/audit/stream"
                response = requests.post(stream_url, json=payload, stream=True)
                
                document_type = "Pending"
                legal_docs = []
                retrieval_grade = "Pending"
                final_report = ""
                retry_count = 0
                
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith("data: "):
                            event_data = json.loads(decoded_line[6:])
                            
                            if "error" in event_data:
                                trace_status.error(f"Execution Error: {event_data['error']}")
                                st.error(event_data['error'])
                                break
                            
                            for node_name, state_update in event_data.items():
                                if node_name == "classifier":
                                    document_type = state_update.get("document_type", "Other")
                                    trace_status.write(f"**Classifier Agent:** Triage complete. Categorized query domain as `{document_type}`.")
                                    
                                    # Render badge
                                    badge_class = f"badge-{document_type.lower()}"
                                    category_placeholder.markdown(f"""
                                    <div style="margin-top: 10px;">
                                        <span style="color: #94a3b8; font-weight: 500;">Triage Classification:</span>
                                        <span class="category-badge {badge_class}">{document_type}</span>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                elif node_name == "retriever":
                                    legal_docs = state_update.get("legal_docs", [])
                                    trace_status.write(f"**Retriever Agent:** Queried local index. Found `{len(legal_docs)}` candidate chunks.")
                                    
                                elif node_name == "evaluator":
                                    legal_docs = state_update.get("legal_docs", [])
                                    retrieval_grade = state_update.get("retrieval_grade", "fail")
                                    trace_status.write(
                                        f"**Evaluator Agent:** Inspected candidates. Grading status: **{retrieval_grade.upper()}** "
                                        f"({len(legal_docs)} relevant clauses retained)."
                                    )
                                    
                                    # Render the retrieved documents inside the expander live
                                    with docs_expander_placeholder.expander("View Retained Grounding Evidence & Citations", expanded=False):
                                        if not legal_docs:
                                            st.write("No relevant documents retained.")
                                        for idx, doc in enumerate(legal_docs):
                                            st.markdown(f"""
                                            <div class="clause-card">
                                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                                                    <strong style="color: #38bdf8;">Evidence Snippet #{idx + 1}</strong>
                                                    <span style="font-size: 0.8rem; background: rgba(56, 189, 248, 0.1); padding: 2px 8px; border-radius: 4px; border: 1px solid rgba(56, 189, 248, 0.2);">
                                                        Score: {doc['score']:.4f}
                                                    </span>
                                                </div>
                                                <span style="font-size: 0.85rem; color: #94a3b8;">
                                                    Source: <strong>{doc['source']}</strong> | Page: <strong>{doc['page']}</strong>
                                                </span>
                                                <p style="margin-top: 8px; font-style: italic; color: #cbd5e1; line-height: 1.4;">
                                                    "{doc['text']}"
                                                </p>
                                            </div>
                                            """, unsafe_allow_html=True)
                                            
                                elif node_name == "rewrite":
                                    retry_count = state_update.get("retry_count", 0)
                                    rewritten_query = state_update.get("search_query", "")
                                    trace_status.write(
                                        f"**Query Rewriter Agent:** Quality evaluation failed. "
                                        f"Initiating corrective loop `{retry_count}`. Optimizing keywords to: *\"{rewritten_query}\"*"
                                    )
                                    
                                elif node_name == "synthesizer":
                                    final_report = state_update.get("audit_report", "")
                                    trace_status.write("**Synthesizer Agent:** Analysis complete. Formatting citation-backed report...")
                
                if final_report:
                    trace_status.update(label="Audit completed successfully!", state="complete", expanded=False)
                    st.success("Auditing Complete!")
                    
                    st.markdown("---")
                    st.markdown("<h3 class='sub-title'>Citation-Backed Compliance Report</h3>", unsafe_allow_html=True)
                    
                    # Styled report block
                    st.markdown(f"""
                    <div style="background: rgba(30, 41, 59, 0.25); border: 1px solid rgba(255, 255, 255, 0.05); padding: 24px; border-radius: 12px; margin-bottom: 20px;">
                        {final_report}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Download button
                    st.download_button(
                        label="Export Audit Report (Markdown)",
                        data=final_report,
                        file_name="compliance_audit_report.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
                else:
                    trace_status.update(label="Audit failed to compile report.", state="error", expanded=True)
                    st.error("Synthesizer failed to generate the report. Check backend console for API issues.")
                    
            except Exception as e:
                trace_status.update(label="System Connection Error.", state="error", expanded=True)
                st.error(f"Could not connect to FastAPI server: {str(e)}")

# --------------------------------------------------
# Tab 2: Document Repository Manager
# --------------------------------------------------
with tab_repository:
    st.markdown("<h3 class='sub-title'>Document Repository Manager</h3>", unsafe_allow_html=True)
    st.write("Below are the raw PDF documents located in your local raw storage folder:")
    
    raw_docs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "raw_docs"))
    
    if os.path.exists(raw_docs_path):
        files = [f for f in os.listdir(raw_docs_path) if f.lower().endswith(".pdf")]
        
        if not files:
            st.warning("No PDF documents found in `data/raw_docs/` folder.")
        else:
            cols = st.columns(3)
            for idx, file in enumerate(files):
                file_path = os.path.join(raw_docs_path, file)
                file_size_kb = os.path.getsize(file_path) / 1024
                
                with cols[idx % 3]:
                    st.markdown(f"""
                    <div class="clause-card" style="border-left: 4px solid #38bdf8;">
                        <span style="font-size: 1.1rem; font-weight: bold; color: #f1f5f9; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                            {file}
                        </span>
                        <span style="font-size: 0.85rem; color: #94a3b8; display: block; margin-top: 6px;">
                            Size: {file_size_kb:.1f} KB
                        </span>
                        <span style="font-size: 0.85rem; color: #34d399; font-weight: 500; display: block; margin-top: 4px;">
                            Status: Available for Indexing
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.error(f"Raw documents directory not found at: `{raw_docs_path}`")

# --------------------------------------------------
# Tab 3: Database & Index Settings
# --------------------------------------------------
with tab_ingestion:
    st.markdown("<h3 class='sub-title'>Database Settings & Re-Indexing</h3>", unsafe_allow_html=True)
    st.write("Manage your persistent vector storage connection and trigger document re-indexing loops below:")
    
    if api_online:
        st.info(f"Collection Name: `legal_frameworks`  \n"
                f"Storage Type: Local Disk RocksDB  \n"
                f"Persistent Directory Path: `{db_persistent_path}`")
        st.success("Database Status: PERSISTED & ONLINE")
    else:
        st.warning("FastAPI Backend is offline. Ingestion status is currently unavailable.")
        
    st.write("---")
    st.markdown("<h4 class='sub-title'>Vector Database Re-Indexing Tool</h4>", unsafe_allow_html=True)
    st.write("Upload new documents to `data/raw_docs/` and run the script below to rebuild the vector search indexes.")
    
    if st.button("Rebuild Vector Search Indexes", use_container_width=True):
        st.markdown("### Ingestion Console Logs")
        console_placeholder = st.empty()
        
        # Resolve absolute path to ingestion script
        ingest_script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "ingest_to_vector_db.py"))
        
        if not os.path.exists(ingest_script_path):
            st.error(f"Ingestion script not found at: `{ingest_script_path}`")
        else:
            try:
                # Start python script as a subprocess and stream its output live
                process = subprocess.Popen(
                    [sys.executable, "-u", ingest_script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
                )
                
                log_accumulator = []
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        log_accumulator.append(output.strip())
                        # Render cumulative logs to the console container
                        console_placeholder.code("\n".join(log_accumulator[-20:]))
                
                rc = process.poll()
                if rc == 0:
                    st.success("Vector database successfully rebuilt and persisted!")
                else:
                    st.error(f"Ingestion script failed with exit code: {rc}")
            except Exception as ex:
                st.error(f"Error executing ingestion subprocess: {str(ex)}")
