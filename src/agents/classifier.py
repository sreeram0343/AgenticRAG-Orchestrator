from typing import Dict, Any

from src.state import AuditorState


def classify_document_type(
    state: AuditorState,
    llm
) -> Dict[str, Any]:

    question = state["question"]

    prompt = f"""
    Classify the legal topic.

    Question:
    {question}

    Return ONLY one:

    Lease
    NDA
    Adoption
    Trust
    Property
    Other
    """

    response = llm.invoke(prompt)

    return {
        "document_type": response.content.strip()
    }