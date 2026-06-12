from typing import Dict, Any

from src.state import AuditorState

from langchain_google_genai import ChatGoogleGenerativeAI


def synthesize_report(
    state: AuditorState
) -> Dict[str, Any]:

    print(
        "📝 [Synthesizer] Creating compliance report..."
    )

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        temperature=0
    )

    question = state["question"]

    legal_docs = "\n\n".join(
        state.get("legal_docs", [])
    )

    internal_docs = "\n\n".join(
        state.get("internal_docs", [])
    )

    prompt = f"""
You are a senior compliance auditor.

Question:
{question}

Legal Requirements:
{legal_docs}

Internal Policies:
{internal_docs}

Generate:

1. Executive Summary

2. Findings

3. Compliance Status

4. Risk Assessment

5. Recommendations

6. Final Verdict

Support all conclusions using evidence.
"""

    response = llm.invoke(prompt)

    print(
        "✅ [Synthesizer] Report completed."
    )

    return {
        "audit_report": response.content
    }