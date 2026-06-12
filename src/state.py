from typing import TypedDict, List

class AuditorState(TypedDict):
    question: str

    document_type: str

    legal_docs: List[str]

    retrieval_grade: str

    audit_report: str

    retry_count: int