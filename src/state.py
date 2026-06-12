from typing import List, TypedDict

class AuditorState(TypedDict):

    question: str

    internal_docs: List[str]

    legal_docs: List[str]

    generation: str

    search_retries: int

    compliance_status: int

    