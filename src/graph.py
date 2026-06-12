from langgraph.graph import StateGraph, END

from src.state import AuditorState

from src.agents.retriever import retrieve_legal_frameworks
from src.agents.evaluator import evaluate_documents
from src.agents.synthesizer import synthesize_report


# --------------------------------------------------
# Retry Configuration
# --------------------------------------------------

MAX_RETRIES = 3


# --------------------------------------------------
# Routing Logic (CRAG Brain)
# --------------------------------------------------

def route_after_evaluation(state: AuditorState):
    """
    Decides what happens after document evaluation.

    Cases:

    1. Documents are relevant
       -> Go to Synthesizer

    2. Documents are irrelevant
       -> Retry retrieval

    3. Too many retries
       -> Force Synthesizer to avoid infinite loops
    """

    retrieval_grade = state.get("retrieval_grade", "fail")

    retry_count = state.get("retry_count", 0)

    print(
        f"🔍 Evaluation Result: {retrieval_grade} | Retry Count: {retry_count}"
    )

    # Documents passed evaluation
    if retrieval_grade.lower() == "pass":
        print("✅ Documents accepted.")
        return "synthesizer"

    # Retry limit reached
    if retry_count >= MAX_RETRIES:
        print(
            f"⚠️ Maximum retries ({MAX_RETRIES}) reached."
        )
        print(
            "⚠️ Proceeding with best available context."
        )

        return "synthesizer"

    # Retry retrieval
    print("🔄 Retrieval failed. Retrying...")

    return "retriever"


# --------------------------------------------------
# Create Workflow
# --------------------------------------------------

workflow = StateGraph(AuditorState)


# --------------------------------------------------
# Register Nodes
# --------------------------------------------------

workflow.add_node(
    "retriever",
    retrieve_legal_frameworks
)

workflow.add_node(
    "evaluator",
    evaluate_documents
)

workflow.add_node(
    "synthesizer",
    synthesize_report
)


# --------------------------------------------------
# Entry Point
# --------------------------------------------------

workflow.set_entry_point(
    "retriever"
)


# --------------------------------------------------
# Fixed Edges
# --------------------------------------------------

workflow.add_edge(
    "retriever",
    "evaluator"
)


# --------------------------------------------------
# Conditional Edge (CRAG Loop)
# --------------------------------------------------

workflow.add_conditional_edges(
    "evaluator",
    route_after_evaluation,
    {
        "retriever": "retriever",
        "synthesizer": "synthesizer"
    }
)


# --------------------------------------------------
# Final Edge
# --------------------------------------------------

workflow.add_edge(
    "synthesizer",
    END
)


# --------------------------------------------------
# Compile Graph
# --------------------------------------------------

app = workflow.compile()


# --------------------------------------------------
# Debug Entry Point
# --------------------------------------------------

if __name__ == "__main__":

    test_state = {
        "question": (
            "Is our current data retention policy compliant?"
        ),

        "legal_docs": [],

        "internal_docs": [],

        "retrieval_grade": "fail",

        "retry_count": 0,

        "audit_report": ""
    }

    result = app.invoke(test_state)

    print("\n" + "=" * 60)
    print("FINAL STATE")
    print("=" * 60)

    print(result)