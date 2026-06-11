# 🚀 AgenticRAG-Orchestrator

<div align="center">

### Autonomous Multi-Agent Compliance Auditing System

*Transforming Traditional RAG into an Intelligent Self-Correcting AI Auditor*

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-Agentic%20Workflow-green)
![Gemini](https://img.shields.io/badge/Google-Gemini-orange)
![Qdrant](https://img.shields.io/badge/VectorDB-Qdrant-red)
![FastAPI](https://img.shields.io/badge/API-FastAPI-teal)
![License](https://img.shields.io/badge/License-MIT-yellow)

</div>

---

## 🎯 Vision

Modern enterprises face an overwhelming challenge: ensuring internal policies comply with ever-evolving regulatory frameworks.

Traditional AI systems can retrieve information, but they cannot independently verify, compare, and reason across multiple sources.

**AgenticRAG-Orchestrator** bridges this gap by introducing a multi-agent, self-correcting RAG architecture capable of acting as an autonomous compliance auditor.

Instead of simply answering questions, the system:

✅ Retrieves evidence  
✅ Validates relevance  
✅ Corrects retrieval failures  
✅ Cross-references regulations and policies  
✅ Generates verifiable audit reports  

---

# ⚠️ The Problem

Most Retrieval-Augmented Generation (RAG) systems operate using a linear workflow:

```text
User Query
    ↓
Retrieve Documents
    ↓
Generate Response
```

While effective for basic search applications, this architecture struggles with:

- Hallucinated responses
- Irrelevant document retrieval
- Lack of evidence validation
- Poor reasoning across multiple sources
- No self-correction mechanism

### Example

Imagine an internal company policy states:

> Data should be retained for 90 days.

But a regulatory framework requires:

> Data must not exceed 30 days of retention.

A traditional RAG system may retrieve one document and summarize it.

It cannot autonomously:

- Retrieve both sources
- Compare requirements
- Detect compliance violations
- Explain the discrepancy

---

# 💡 Solution

AgenticRAG-Orchestrator introduces a **cyclic state-machine architecture** powered by LangGraph.

The system continuously evaluates its own retrieval quality and loops back whenever necessary.

```text
User Query
      ↓
 Planner Agent
      ↓
 Retriever Agent
      ↓
 Evaluator Agent
      ↓
  Relevant?
   /      \
 Yes      No
  |         |
  ↓         |
Synthesizer |
  ↓         |
Reflection  |
  ↓         |
 Final Report
     ↑
     |
Self-Correction Loop
```

Unlike traditional RAG, retrieval is not considered successful until evidence quality is verified.

---

# 🧠 Multi-Agent Architecture

## 1️⃣ Planner Agent

Acts as the project manager of the workflow.

### Responsibilities

- Understand user intent
- Decompose complex questions
- Define retrieval strategy
- Select appropriate knowledge sources
- Coordinate downstream agents

### Example

**Query**

```text
Does our cloud infrastructure comply with ISO 27001 encryption requirements?
```

**Planner Output**

```text
Task 1 → Retrieve ISO 27001 controls

Task 2 → Retrieve internal security policy

Task 3 → Compare both datasets

Task 4 → Generate compliance findings
```

---

## 2️⃣ Retriever Agent

Acts as the organization's AI librarian.

### Responsibilities

- Semantic search
- Embedding generation
- Vector similarity search
- Context retrieval

### Supported Vector Databases

- Qdrant
- Pinecone
- ChromaDB

---

## 3️⃣ Evaluator Agent

### Corrective RAG (CRAG)

This agent is the quality control layer.

Before any information is used, it evaluates whether retrieved context actually answers the requested question.

### PASS Example

```text
Retrieved Context:

ISO 27001 requires encryption keys
to be protected using secure key
management processes.

Result:
PASS
```

### FAIL Example

```text
Retrieved Context:

Cloud deployment guide
for virtual machines.

Result:
FAIL
```

### Self-Correction Loop

Whenever retrieval quality is poor:

```text
FAIL
 ↓
Rewrite Query
 ↓
Retrieve Again
 ↓
Re-Evaluate
```

This process continues until acceptable evidence is obtained.

---

## 4️⃣ Synthesizer Agent

After evidence is validated, the Synthesizer performs analysis.

### Responsibilities

- Cross-reference policies
- Compare regulations
- Identify compliance gaps
- Generate findings
- Produce audit reports

### Example Output

```text
Finding #1

Internal Policy:
90-Day Log Retention

ISO Requirement:
30-Day Maximum Retention

Status:
NON-COMPLIANT

Risk Level:
HIGH
```

---

## 5️⃣ Reflection Agent

Inspired by Self-Reflective RAG techniques.

Before releasing the final report, the agent verifies:

- Citation completeness
- Logical consistency
- Evidence support
- Hallucination risk

Only verified conclusions are returned.

---

# ⚙️ Technical Highlights

### 🔄 LangGraph State Machine

Supports cyclic execution and iterative reasoning.

### 🧩 Multi-Agent Collaboration

Agents communicate through shared state.

### 🔍 Dynamic Query Routing

Automatically routes queries to:

- Legal Documents
- Internal Policies
- Compliance Knowledge Bases

### 📑 Citation-Backed Reports

Every finding is linked to supporting evidence.

### 🛡️ Hallucination Reduction

Self-reflection ensures conclusions are evidence-driven.

---

# 🏗️ Technology Stack

| Layer | Technology |
|---------|------------|
| Workflow Orchestration | LangGraph |
| LLM | Google Gemini |
| Embeddings | Gemini Embeddings |
| Backend | Python |
| API Layer | FastAPI |
| Vector Database | Qdrant |
| Environment Management | python-dotenv |
| State Management | LangGraph StateGraph |

---

# 🔄 End-to-End Workflow

```text
User Query
      ↓
Planner Agent
      ↓
Retriever Agent
      ↓
Evaluator Agent
      ↓
 ┌─────────────┐
 │ PASS / FAIL │
 └──────┬──────┘
        │
 FAIL   │   PASS
        │
        ↓
 Retrieval Retry
        │
        ↓
 Synthesizer Agent
        ↓
 Reflection Agent
        ↓
 Final Audit Report
```

---

# 🎯 Real-World Applications

## 📜 Regulatory Compliance

- DPDP Act Auditing
- GDPR Assessments
- ISO 27001 Verification
- SOC 2 Reviews
- PCI DSS Audits

---

## 🛡️ Security Operations Centers (SOC)

- Log Retention Validation
- Incident Response Reviews
- Access Control Audits
- Security Governance Assessments

---

## 🏢 Enterprise Governance

- Internal Policy Verification
- Documentation Gap Analysis
- Risk Assessment Support
- Regulatory Readiness Reviews

---

# 📈 Future Roadmap

### Phase 1

- [ ] Multi-modal document ingestion
- [ ] PDF and image understanding
- [ ] Human-in-the-loop validation

### Phase 2

- [ ] Persistent Agent Memory
- [ ] Long-term compliance tracking
- [ ] Multi-tenant architecture

### Phase 3

- [ ] MCP Integration
- [ ] Autonomous remediation recommendations
- [ ] Real-time compliance monitoring

---

# 🎯 Project Goal

The objective of AgenticRAG-Orchestrator is to evolve Large Language Models from passive search tools into active enterprise auditors capable of:

- Retrieving information
- Evaluating evidence
- Correcting retrieval failures
- Cross-referencing regulations
- Producing trustworthy audit reports

Ultimately, the system aims to provide organizations with an AI-powered compliance analyst that operates with transparency, traceability, and verifiable reasoning.

---

# 📄 Resume Impact

### Built an Agentic AI Compliance Auditor using LangGraph, Gemini, and Qdrant

- Designed a multi-agent RAG architecture
- Implemented Corrective RAG (CRAG)
- Built self-correcting retrieval loops
- Reduced hallucinations using reflection agents
- Generated citation-backed compliance reports
- Developed enterprise-grade AI workflow orchestration

---

# 👨‍💻 Author

### Sreeram M R

**AI/ML Engineer • Applied AI • LLM Engineering • Agentic AI • RAG Systems**

> Building intelligent systems that can reason, verify, and act autonomously.

---

## ⭐ If you find this project useful, consider giving it a star!
