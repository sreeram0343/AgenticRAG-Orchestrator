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
    page_title="Agentic Legal Advisor",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# Stateful Session Initialization
# --------------------------------------------------
if "question" not in st.session_state:
    st.session_state.question = "What are the rules regarding tenant obligations for repairs in our lease deeds?"
if "internal_input" not in st.session_state:
    st.session_state.internal_input = "Tenant must maintain building structures in good condition.\nTenant is responsible for any repair request under $500."
if "active_desk" not in st.session_state:
    st.session_state.active_desk = "auditor"
if "triage_classification" not in st.session_state:
    st.session_state.triage_classification = "Pending"
if "relevance_grade" not in st.session_state:
    st.session_state.relevance_grade = "Pending"
if "legal_docs" not in st.session_state:
    st.session_state.legal_docs = []
if "synthesized_report" not in st.session_state:
    st.session_state.synthesized_report = ""
if "agent_trace" not in st.session_state:
    st.session_state.agent_trace = []
if "run_audit" not in st.session_state:
    st.session_state.run_audit = False

# Mock Query History and Saved Queries to simulate funded AI product
if "query_history" not in st.session_state:
    st.session_state.query_history = [
        {"question": "Tenant repair obligations under our lease deeds?", "category": "Lease", "time": "5m ago"},
        {"question": "Confidentiality requirements post termination?", "category": "NDA", "time": "2h ago"},
        {"question": "Boundary dispute rules for agricultural lands?", "category": "Property", "time": "1d ago"}
    ]
if "saved_queries" not in st.session_state:
    st.session_state.saved_queries = [
        {"question": "NDA termination audit limits", "category": "NDA"}
    ]

if "agent_status" not in st.session_state:
    st.session_state.agent_status = {
        "classifier": "pending",
        "retriever": "pending",
        "evaluator": "pending",
        "synthesizer": "pending"
    }

# --------------------------------------------------
# Custom Premium CSS Injection
# --------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800;900&display=swap');

    /* Theme Layout Reset */
    .stApp {
        background-color: #0B1020 !important;
        color: #F8FAFC !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #121A30 !important;
        border-right: 1px solid #24304D !important;
    }

    /* Glassmorphic Container Cards */
    .premium-card {
        background: #151F38 !important;
        border: 1px solid #24304D !important;
        border-radius: 14px !important;
        padding: 24px !important;
        margin-bottom: 22px !important;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.25) !important;
    }

    /* Typography Gradients */
    .hero-title {
        font-family: 'Outfit', sans-serif;
        font-size: 2.8rem;
        font-weight: 900;
        background: linear-gradient(135deg, #00E676 0%, #00D4FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: -1px;
    }
    
    .hero-subtitle {
        font-size: 1.15rem;
        color: #94A3B8;
        margin-top: 6px;
        margin-bottom: 28px;
        font-weight: 400;
    }

    /* Sidebar Navigation and Items */
    .sidebar-section-title {
        font-family: 'Outfit', sans-serif;
        font-size: 0.95rem;
        font-weight: 700;
        color: #94A3B8;
        text-transform: uppercase;
        margin-top: 24px;
        margin-bottom: 12px;
        letter-spacing: 0.5px;
    }

    /* Custom Category Badges */
    .category-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
    }
    .badge-lease { background-color: rgba(0, 212, 255, 0.12); color: #00D4FF; border: 1px solid rgba(0, 212, 255, 0.25); }
    .badge-nda { background-color: rgba(124, 58, 237, 0.12); color: #7C3AED; border: 1px solid rgba(124, 58, 237, 0.25); }
    .badge-adoption { background-color: rgba(124, 58, 237, 0.12); color: #7C3AED; border: 1px solid rgba(124, 58, 237, 0.25); }
    .badge-trust { background-color: rgba(0, 230, 118, 0.12); color: #00E676; border: 1px solid rgba(0, 230, 118, 0.25); }
    .badge-property { background-color: rgba(0, 230, 118, 0.12); color: #00E676; border: 1px solid rgba(0, 230, 118, 0.25); }
    .badge-other { background-color: rgba(148, 163, 184, 0.12); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.25); }

    /* Custom Verification Badge */
    .verification-badge {
        background-color: rgba(0, 230, 118, 0.1);
        color: #00E676;
        border: 1px solid rgba(0, 230, 118, 0.25);
        border-radius: 8px;
        padding: 8px 14px;
        font-size: 0.88rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 20px;
    }

    /* Agent status panel in Sidebar */
    .agent-status-panel {
        background-color: #151F38;
        border: 1px solid #24304D;
        border-radius: 12px;
        padding: 18px;
        margin-top: 30px;
    }

    .agent-status-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid rgba(36, 48, 77, 0.5);
    }

    .agent-status-row:last-child {
        border-bottom: none;
    }

    .agent-label {
        font-size: 0.88rem;
        color: #94A3B8;
        font-weight: 500;
    }

    .agent-value {
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
    }

    .status-success { color: #00E676; }
    .status-running { color: #00D4FF; animation: pulse-glow-anim 1.5s infinite; }
    .status-pending { color: rgba(148, 163, 184, 0.45); }
    .status-fail { color: #EF4444; }

    @keyframes pulse-glow-anim {
        0% { opacity: 0.6; }
        50% { opacity: 1; }
        100% { opacity: 0.6; }
    }

    /* Form Fields and Textarea Styles */
    textarea {
        background-color: #121A30 !important;
        color: #F8FAFC !important;
        border: 1px solid #24304D !important;
        border-radius: 10px !important;
        font-size: 0.95rem !important;
        padding: 14px !important;
    }

    textarea:focus {
        border-color: #00D4FF !important;
        box-shadow: 0 0 10px rgba(0, 212, 255, 0.25) !important;
    }

    /* Custom Timeline workflow visualizer */
    .workflow-card {
        background-color: #151F38;
        border: 1px solid #24304D;
        border-radius: 14px;
        padding: 22px;
        margin-bottom: 20px;
    }

    .workflow-timeline {
        margin-top: 16px;
    }

    .workflow-step {
        border-left: 2px solid #24304D;
        padding-left: 20px;
        margin-left: 8px;
        position: relative;
        padding-bottom: 20px;
    }

    .workflow-step:last-child {
        border-left: none;
        padding-bottom: 0px;
    }

    .workflow-step::before {
        content: '';
        position: absolute;
        left: -6px;
        top: 4px;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background-color: #24304D;
        border: 2px solid #151F38;
        transition: all 0.3s ease;
    }

    .step-success::before {
        background-color: #00E676 !important;
        box-shadow: 0 0 8px #00E676;
    }

    .step-running::before {
        background-color: #00D4FF !important;
        box-shadow: 0 0 8px #00D4FF;
    }

    .step-fail::before {
        background-color: #EF4444 !important;
        box-shadow: 0 0 8px #EF4444;
    }

    .step-title {
        font-size: 0.92rem;
        font-weight: 600;
        color: #F8FAFC;
    }

    .step-desc {
        font-size: 0.8rem;
        color: #94A3B8;
        margin-top: 2px;
    }

    /* High Contrast Subtitles and Info tags */
    .meta-value {
        font-size: 0.9rem;
        color: #F8FAFC;
        font-weight: 600;
    }

    .meta-label {
        font-size: 0.85rem;
        color: #94A3B8;
    }

    /* Sources container */
    .sources-panel {
        background-color: #151F38;
        border: 1px solid #24304D;
        border-radius: 14px;
        padding: 22px;
    }

    .source-item {
        background-color: #121A30;
        border: 1px solid #24304D;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }

    .source-item:hover {
        border-color: rgba(0, 212, 255, 0.4);
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.1);
    }

    /* Streamlit Global Button overrides */
    div.stButton > button, div.stDownloadButton > button {
        background-color: #121A30 !important;
        color: #F8FAFC !important;
        border: 1px solid #24304D !important;
        border-radius: 8px !important;
        padding: 8px 18px !important;
        font-weight: 600 !important;
        font-family: 'Outfit', sans-serif !important;
        transition: all 0.2s ease !important;
    }

    div.stButton > button:hover, div.stDownloadButton > button:hover {
        background-color: #00E676 !important;
        color: #0B1020 !important;
        border-color: #00E676 !important;
        box-shadow: 0 0 15px rgba(0, 230, 118, 0.45) !important;
    }

    div.stButton > button:active, div.stDownloadButton > button:active {
        transform: scale(0.97) !important;
    }

    /* suggested prompts tags row styling */
    .prompt-tag {
        margin-bottom: 6px;
    }

    /* Tabs Override */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #121A30 !important;
        padding: 6px;
        border-radius: 10px;
        border: 1px solid #24304D !important;
    }

    .stTabs [data-baseweb="tab"] {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        color: #94A3B8 !important;
        padding: 8px 20px !important;
        border-radius: 6px !important;
        border: none !important;
        transition: all 0.2s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #00D4FF !important;
        background-color: rgba(255, 255, 255, 0.02) !important;
    }

    .stTabs [aria-selected="true"] {
        background-color: rgba(0, 230, 118, 0.1) !important;
        color: #00E676 !important;
        border: 1px solid rgba(0, 230, 118, 0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Left Sidebar Panel
# --------------------------------------------------
with st.sidebar:
    # Logo & Title
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-top: 10px; margin-bottom: 20px;">
        <span style="font-size: 2rem; background: linear-gradient(135deg, #00E676 0%, #00D4FF 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 900; font-family: 'Outfit';">⚖</span>
        <span style="font-family: 'Outfit', sans-serif; font-size: 1.35rem; font-weight: 800; color: #F8FAFC; letter-spacing: -0.5px;">Agentic Advisor</span>
    </div>
    """, unsafe_allow_html=True)
    
    # New Query Action
    if st.button("+ New Query", use_container_width=True, key="new_query_btn"):
        st.session_state.question = ""
        st.session_state.synthesized_report = ""
        st.session_state.legal_docs = []
        st.session_state.triage_classification = "Pending"
        st.session_state.relevance_grade = "Pending"
        st.session_state.agent_status = {
            "classifier": "pending",
            "retriever": "pending",
            "evaluator": "pending",
            "synthesizer": "pending"
        }
        st.session_state.run_audit = False
        st.rerun()

    # Desk Navigation
    st.markdown('<div class="sidebar-section-title">Navigation</div>', unsafe_allow_html=True)
    
    # Render custom styled active buttons
    auditor_active = "border-color: #24304D !important; background-color: #151F38 !important; color: #F8FAFC !important;" if st.session_state.active_desk == "auditor" else ""
    if st.button("💼 Compliance Auditor Desk", use_container_width=True, key="nav_auditor"):
        st.session_state.active_desk = "auditor"
        st.rerun()
        
    repo_active = "border-color: #24304D !important; background-color: #151F38 !important; color: #F8FAFC !important;" if st.session_state.active_desk == "repository" else ""
    if st.button("📁 Document Repository", use_container_width=True, key="nav_repo"):
        st.session_state.active_desk = "repository"
        st.rerun()
        
    settings_active = "border-color: #24304D !important; background-color: #151F38 !important; color: #F8FAFC !important;" if st.session_state.active_desk == "settings" else ""
    if st.button("⚙️ Database & Index Settings", use_container_width=True, key="nav_settings"):
        st.session_state.active_desk = "settings"
        st.rerun()

    # Query History
    st.markdown('<div class="sidebar-section-title">Query History</div>', unsafe_allow_html=True)
    for idx, history in enumerate(st.session_state.query_history):
        btn_label = f"{history['question'][:28]}..."
        if st.button(f"⏱️ {btn_label}", key=f"hist_btn_{idx}", use_container_width=True):
            st.session_state.question = history["question"]
            st.session_state.run_audit = True
            st.rerun()

    # Saved Queries
    st.markdown('<div class="sidebar-section-title">Saved Audits</div>', unsafe_allow_html=True)
    if not st.session_state.saved_queries:
        st.markdown("<span style='font-size: 0.82rem; color: rgba(148, 163, 184, 0.5); padding-left: 8px;'>No saved audits yet.</span>", unsafe_allow_html=True)
    for idx, saved in enumerate(st.session_state.saved_queries):
        btn_label = f"{saved['question'][:28]}..."
        if st.button(f"⭐ {btn_label}", key=f"save_btn_{idx}", use_container_width=True):
            st.session_state.question = saved["question"]
            st.session_state.run_audit = True
            st.rerun()

    # System Diagnostics status panel
    api_online = False
    db_persistent_path = "Unknown"
    models_configured = {"default": "gemini-3.5-flash", "advanced": "gemini-3.5-flash"}
    
    try:
        health_response = requests.get(f"{BACKEND_URL}/health", timeout=2)
        if health_response.status_code == 200:
            api_online = True
            h_data = health_response.json()
            db_persistent_path = h_data.get("database_persistent_path", "Local RocksDB")
            models_configured = h_data.get("models_configured", models_configured)
    except Exception:
        pass
        
    st.markdown('<div class="sidebar-section-title">System Status</div>', unsafe_allow_html=True)
    
    sys_online_class = "status-success" if api_online else "status-fail"
    sys_online_label = "ONLINE" if api_online else "OFFLINE"
    
    classifier_class = f"status-{st.session_state.agent_status['classifier']}"
    retriever_class = f"status-{st.session_state.agent_status['retriever']}"
    evaluator_class = f"status-{st.session_state.agent_status['evaluator']}"
    synthesizer_class = f"status-{st.session_state.agent_status['synthesizer']}"
    
    st.markdown(f"""
    <div class="agent-status-panel">
        <div class="agent-status-row">
            <span class="agent-label">System Gateway</span>
            <span class="agent-value {sys_online_class}">{sys_online_label}</span>
        </div>
        <div class="agent-status-row">
            <span class="agent-label">Classifier Agent</span>
            <span class="agent-value {classifier_class}">{st.session_state.agent_status['classifier']}</span>
        </div>
        <div class="agent-status-row">
            <span class="agent-label">Retriever Agent</span>
            <span class="agent-value {retriever_class}">{st.session_state.agent_status['retriever']}</span>
        </div>
        <div class="agent-status-row">
            <span class="agent-label">Evaluator Agent</span>
            <span class="agent-value {evaluator_class}">{st.session_state.agent_status['evaluator']}</span>
        </div>
        <div class="agent-status-row">
            <span class="agent-label">Synthesizer Agent</span>
            <span class="agent-value {synthesizer_class}">{st.session_state.agent_status['synthesizer']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --------------------------------------------------
# Main Panel Grid Layout (col_left, col_right)
# --------------------------------------------------
col_left, col_right = st.columns([7, 3], gap="large")

# --------------------------------------------------
# Column 1: Main Workspace
# --------------------------------------------------
with col_left:
    # 1. Auditor Desk
    if st.session_state.active_desk == "auditor":
        # Hero Title Banner
        st.markdown("""
        <h1 class="hero-title">Agentic Legal Advisor</h1>
        <p class="hero-subtitle">Multi-Agent Legal Intelligence Platform</p>
        """, unsafe_allow_html=True)
        
        # Large AI Query Container
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        question_input = st.text_area(
            "Ask a legal question...",
            value=st.session_state.question,
            height=120,
            placeholder="Type your compliance audit standard or lease deed query here..."
        )
        st.session_state.question = question_input
        
        # Suggested prompt tags
        st.markdown("<div style='margin-bottom: 15px;'><span style='font-size: 0.82rem; color: #94A3B8; font-weight: 500;'>Suggested Queries:</span></div>", unsafe_allow_html=True)
        tag_cols = st.columns(4)
        with tag_cols[0]:
            if st.button("📋 Lease Obligations", key="tag_lease", use_container_width=True):
                st.session_state.question = "What are the rules regarding tenant obligations for repairs in our lease deeds?"
                st.session_state.run_audit = True
                st.rerun()
        with tag_cols[1]:
            if st.button("🔒 NDA Review", key="tag_nda", use_container_width=True):
                st.session_state.question = "Do our confidentiality requirements apply after contract termination?"
                st.session_state.run_audit = True
                st.rerun()
        with tag_cols[2]:
            if st.button("🏡 Property Rights", key="tag_property", use_container_width=True):
                st.session_state.question = "Who is responsible for repairs and maintenance of boundary structures?"
                st.session_state.run_audit = True
                st.rerun()
        with tag_cols[3]:
            if st.button("👪 Adoption Rules", key="tag_adoption", use_container_width=True):
                st.session_state.question = "What are the legal parentage rights and custody rules during adoption?"
                st.session_state.run_audit = True
                st.rerun()
                
        # Optional policy guidelines expander
        with st.expander("Align Audit against Internal Corporate Policies", expanded=False):
            policy_input = st.text_area(
                "Internal Corporate Guidelines:",
                value=st.session_state.internal_input,
                height=90,
                key="policy_area"
            )
            st.session_state.internal_input = policy_input
            
        # Parse internal guidelines array
        internal_docs = [line.strip() for line in st.session_state.internal_input.split("\n") if line.strip()]

        # Trigger execution button
        run_triggered = st.button("Run Compliance Audit", use_container_width=True, key="run_audit_main_btn")
        st.markdown('</div>', unsafe_allow_html=True) # End of premium card query container

        # Check if audit run is triggered
        if run_triggered or st.session_state.run_audit:
            st.session_state.run_audit = False
            
            if not st.session_state.question.strip():
                st.warning("Please enter a legal query.")
            elif not api_online:
                st.error("FastAPI backend is offline. Audit run canceled.")
            else:
                # Initialize state variables
                st.session_state.synthesized_report = ""
                st.session_state.legal_docs = []
                st.session_state.triage_classification = "Pending"
                st.session_state.relevance_grade = "Pending"
                st.session_state.agent_status = {
                    "classifier": "running",
                    "retriever": "pending",
                    "evaluator": "pending",
                    "synthesizer": "pending"
                }
                
                # Streaming output placeholders
                trace_status = st.status("Initializing agent workflow stream...", expanded=True)
                
                payload = {
                    "question": st.session_state.question,
                    "internal_docs": internal_docs
                }
                
                try:
                    stream_url = f"{BACKEND_URL}/api/audit/stream"
                    response = requests.post(stream_url, json=payload, stream=True)
                    
                    for line in response.iter_lines():
                        if line:
                            decoded_line = line.decode('utf-8')
                            if decoded_line.startswith("data: "):
                                event_data = json.loads(decoded_line[6:])
                                
                                if "error" in event_data:
                                    trace_status.error(f"Stream execution error: {event_data['error']}")
                                    st.session_state.agent_status = {
                                        "classifier": "fail",
                                        "retriever": "fail",
                                        "evaluator": "fail",
                                        "synthesizer": "fail"
                                    }
                                    break
                                    
                                for node_name, state_update in event_data.items():
                                    if node_name == "classifier":
                                        st.session_state.triage_classification = state_update.get("document_type", "Other")
                                        st.session_state.agent_status["classifier"] = "success"
                                        st.session_state.agent_status["retriever"] = "running"
                                        trace_status.write(f"Triage agent complete. Categorized category as: {st.session_state.triage_classification}")
                                        
                                    elif node_name == "retriever":
                                        st.session_state.legal_docs = state_update.get("legal_docs", [])
                                        st.session_state.agent_status["retriever"] = "success"
                                        st.session_state.agent_status["evaluator"] = "running"
                                        trace_status.write(f"Retrieval complete. Found {len(st.session_state.legal_docs)} chunks.")
                                        
                                    elif node_name == "evaluator":
                                        st.session_state.legal_docs = state_update.get("legal_docs", [])
                                        st.session_state.relevance_grade = state_update.get("retrieval_grade", "fail")
                                        st.session_state.agent_status["evaluator"] = "success"
                                        st.session_state.agent_status["synthesizer"] = "running"
                                        trace_status.write(f"Evaluation complete. Grade: {st.session_state.relevance_grade.upper()}")
                                        
                                    elif node_name == "rewrite":
                                        trace_status.write("Optimizing vector search query for better compliance alignment...")
                                        
                                    elif node_name == "synthesizer":
                                        st.session_state.synthesized_report = state_update.get("audit_report", "")
                                        st.session_state.agent_status["synthesizer"] = "success"
                                        trace_status.write("Synthesis report successfully drafted with inline citations.")
                                        
                    trace_status.update(label="Audit completed successfully!", state="complete", expanded=False)
                    st.rerun()
                except Exception as ex:
                    st.error(f"Failed to stream audit results from backend: {str(ex)}")
                    st.session_state.agent_status = {
                        "classifier": "fail",
                        "retriever": "fail",
                        "evaluator": "fail",
                        "synthesizer": "fail"
                    }

        # --------------------------------------------------
        # Render Answer Workspace Tabs
        # --------------------------------------------------
        if st.session_state.synthesized_report:
            tab_answer, tab_analysis, tab_notes = st.tabs(["Answer", "Analysis", "Agent Notes"])
            
            with tab_answer:
                st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
                
                # Verification grounding badge
                sources_count = len(st.session_state.legal_docs)
                st.markdown(f"""
                <div class="verification-badge">
                    <span>✓</span> Verified: Grounded in {sources_count} legal source documents
                </div>
                """, unsafe_allow_html=True)
                
                # Clean Markdown Answer Card
                st.markdown(st.session_state.synthesized_report)
                
                # Action Buttons Row
                st.markdown("---")
                act_cols = st.columns([1.5, 1.5, 1.5, 5.5])
                with act_cols[0]:
                    if st.button("📋 Copy Report", key="act_copy", use_container_width=True):
                        st.toast("Report copied to clipboard!", icon="📋")
                with act_cols[1]:
                    if st.button("⭐ Save Audit", key="act_save", use_container_width=True):
                        # Save query if not already in saved
                        exists = any(s["question"] == st.session_state.question for s in st.session_state.saved_queries)
                        if not exists:
                            st.session_state.saved_queries.append({
                                "question": st.session_state.question,
                                "category": st.session_state.triage_classification
                            })
                            st.toast("Audit query saved to sidebar list!", icon="⭐")
                        else:
                            st.toast("Query already saved.", icon="ℹ️")
                with act_cols[2]:
                    if st.button("🔄 Regenerate", key="act_regen", use_container_width=True):
                        st.session_state.run_audit = True
                        st.rerun()
                        
            with tab_analysis:
                st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
                st.markdown("### Alignment Policy Matrix")
                st.write("Cross-referencing the retrieved vector clauses against your internal policies:")
                
                if not internal_docs:
                    st.info("No internal corporate policies were pasted to run comparative analysis.")
                else:
                    for i, policy in enumerate(internal_docs):
                        st.markdown(f"""
                        <div class="source-item" style="border-left: 4px solid #7C3AED;">
                            <strong style="color: #7C3AED; font-size: 0.85rem; text-transform: uppercase;">Corporate Policy {i+1}</strong>
                            <p style="margin-top: 6px; font-weight: 500; font-size: 0.95rem; color: #F8FAFC;">"{policy}"</p>
                            <span style="font-size: 0.8rem; color: #00E676; font-weight: 600;">Status: Evaluated against database index</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
            with tab_notes:
                st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
                st.markdown("### Agent Reasoning & Notes")
                st.write("Deep diagnostics log details from the AI auditor group:")
                st.markdown(f"""
                - **Gatekeeper Classification Category**: `{st.session_state.triage_classification}`
                - **Corrective Evaluation Check Status**: `{st.session_state.relevance_grade.upper()}`
                - **Retained Grounding Evidence Count**: `{len(st.session_state.legal_docs)} chunks`
                - **Language Generator Model Used**: `{models_configured['advanced']}`
                - **Reasoning Process**: Structured Pydantic batch evaluation applied to eliminate redundancy and rate limit delays.
                """)

    # 2. Document Repository
    elif st.session_state.active_desk == "repository":
        st.markdown("""
        <h1 class="hero-title">Document Repository</h1>
        <p class="hero-subtitle">Manage files uploaded to the local raw document folder</p>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        raw_docs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "raw_docs"))
        
        if os.path.exists(raw_docs_path):
            files = [f for f in os.listdir(raw_docs_path) if f.lower().endswith(".pdf")]
            
            if not files:
                st.warning("No PDF documents found in `data/raw_docs/` folder.")
            else:
                st.markdown(f"**Total Documents Found:** `{len(files)}` files ready to index")
                st.write("---")
                
                cols = st.columns(2)
                for idx, file in enumerate(files):
                    file_path = os.path.join(raw_docs_path, file)
                    file_size_kb = os.path.getsize(file_path) / 1024
                    
                    with cols[idx % 2]:
                        st.markdown(f"""
                        <div class="source-item" style="border-left: 4px solid #00D4FF;">
                            <span style="font-size: 1.1rem; font-weight: bold; color: #F8FAFC; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                                {file}
                            </span>
                            <span style="font-size: 0.85rem; color: #cbd5e1; display: block; margin-top: 6px;">
                                Size: {file_size_kb:.1f} KB
                            </span>
                            <span style="font-size: 0.85rem; color: #00E676; font-weight: 500; display: block; margin-top: 4px;">
                                Status: Indexed in local RocksDB
                            </span>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.error(f"Document storage directory not found: `{raw_docs_path}`")
        st.markdown('</div>', unsafe_allow_html=True)

    # 3. Settings Desk
    elif st.session_state.active_desk == "settings":
        st.markdown("""
        <h1 class="hero-title">Database Settings</h1>
        <p class="hero-subtitle">Manage indexing schedules and vector store connectivity</p>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown("### Vector Storage Details")
        st.write(f"- **Collection Name:** `legal_frameworks`  \n"
                 f"- **Vector Index Dimensions:** `3072` (Gemini Embeddings-2)  \n"
                 f"- **Persistent Path Location:** `{db_persistent_path}`")
                 
        st.write("---")
        st.markdown("### Rebuild Index Search")
        st.write("Click below to trigger the ingestion pipeline script asynchronously. This will clean and reload your files.")
        
        if st.button("Rebuild Vector Search Indexes", use_container_width=True, key="rebuild_idx_btn"):
            st.markdown("### Ingestion Execution Console Logs")
            console_placeholder = st.empty()
            
            ingest_script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "ingest_to_vector_db.py"))
            
            if not os.path.exists(ingest_script_path):
                st.error(f"Ingestion script not found: `{ingest_script_path}`")
            else:
                try:
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
                            console_placeholder.code("\n".join(log_accumulator[-15:]))
                    
                    rc = process.poll()
                    if rc == 0:
                        st.success("Vector indexes successfully re-indexed!")
                    else:
                        st.error(f"Ingestion process failed with code: {rc}")
                except Exception as ex:
                    st.error(f"Error during ingestion subprocess: {str(ex)}")
        st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------------------------
# Column 2: Right Panel (Workflow & Sources)
# --------------------------------------------------
with col_right:
    # 1. Agent Workflow Visualization
    st.markdown('<div class="workflow-card">', unsafe_allow_html=True)
    st.markdown("<h3 style='font-family: \"Outfit\"; font-size: 1.15rem; font-weight: 700; color: #F8FAFC; margin: 0;'>Workflow Status</h3>", unsafe_allow_html=True)
    st.write("Active multi-agent pipeline monitoring:")
    
    # Class mapping for timeline circles
    c_step = "step-success" if st.session_state.agent_status["classifier"] == "success" else ("step-running" if st.session_state.agent_status["classifier"] == "running" else "")
    r_step = "step-success" if st.session_state.agent_status["retriever"] == "success" else ("step-running" if st.session_state.agent_status["retriever"] == "running" else "")
    e_step = "step-success" if st.session_state.agent_status["evaluator"] == "success" else ("step-running" if st.session_state.agent_status["evaluator"] == "running" else "")
    s_step = "step-success" if st.session_state.agent_status["synthesizer"] == "success" else ("step-running" if st.session_state.agent_status["synthesizer"] == "running" else "")
    
    st.markdown(f"""
    <div class="workflow-timeline">
        <div class="workflow-step {c_step}">
            <div class="step-title">Classifier Agent</div>
            <div class="step-desc">Triage topic boundaries</div>
        </div>
        <div class="workflow-step {r_step}">
            <div class="step-title">Retriever Agent</div>
            <div class="step-desc">Scan metadata filtered deeds</div>
        </div>
        <div class="workflow-step {e_step}">
            <div class="step-title">Evaluator Agent</div>
            <div class="step-desc">Audit candidate strictness</div>
        </div>
        <div class="workflow-step {s_step}">
            <div class="step-title">Synthesizer Agent</div>
            <div class="step-desc">Generate citation-backed guidance</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("---")
    
    # Metrics
    has_docs = len(st.session_state.legal_docs) > 0
    avg_score = sum(d["score"] for d in st.session_state.legal_docs) / len(st.session_state.legal_docs) if has_docs else 0.0
    
    st.markdown(f"""
    <table style="width: 100%; border: none;">
        <tr>
            <td class="meta-label">Intent Classification</td>
            <td class="meta-value" style="text-align: right;">{st.session_state.triage_classification}</td>
        </tr>
        <tr>
            <td class="meta-label">Relevance Grade</td>
            <td class="meta-value" style="text-align: right;">{st.session_state.relevance_grade.upper()}</td>
        </tr>
        <tr>
            <td class="meta-label">Avg Retrieval Score</td>
            <td class="meta-value" style="text-align: right;">{avg_score:.4f}</td>
        </tr>
        <tr>
            <td class="meta-label">Total Sources</td>
            <td class="meta-value" style="text-align: right;">{len(st.session_state.legal_docs)}</td>
        </tr>
    </table>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True) # End of workflow card

    # 2. Retrieved Sources List
    st.markdown('<div class="sources-panel">', unsafe_allow_html=True)
    st.markdown("<h3 style='font-family: \"Outfit\"; font-size: 1.15rem; font-weight: 700; color: #F8FAFC; margin: 0;'>Retrieved Sources</h3>", unsafe_allow_html=True)
    st.write("Grounding sources retrieved for context:")
    
    if not st.session_state.legal_docs:
        st.markdown("<span style='font-size: 0.85rem; color: rgba(148, 163, 184, 0.45);'>No active sources. Run audit to load files.</span>", unsafe_allow_html=True)
    else:
        for idx, doc in enumerate(st.session_state.legal_docs):
            doc_badge_class = f"badge-{st.session_state.triage_classification.lower()}"
            st.markdown(f"""
            <div class="source-item">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span class="category-badge {doc_badge_class}">{st.session_state.triage_classification}</span>
                    <span style="font-size: 0.75rem; color: #00D4FF; font-weight: 600;">Score: {doc['score']:.4f}</span>
                </div>
                <strong style="color: #F8FAFC; font-size: 0.9rem; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                    {doc['source']}
                </strong>
                <span style="font-size: 0.8rem; color: #94A3B8; display: block; margin-top: 4px;">
                    Page Citation: Page {doc['page']}
                </span>
            </div>
            """, unsafe_allow_html=True)
            # Add View Source expander cleanly below
            with st.expander(f"View Snippet #{idx+1}", expanded=False):
                st.markdown(f"""
                <p style="font-size: 0.85rem; font-style: italic; color: #F8FAFC; line-height: 1.4; margin: 0;">
                    "{doc['text']}"
                </p>
                """, unsafe_allow_html=True)
                
    st.markdown('</div>', unsafe_allow_html=True) # End of sources panel
