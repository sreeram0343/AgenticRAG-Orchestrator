from typing import Dict, Any
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from src.state import AuditorState
from src.config import Config

# Define the structured output schema for the classifier
class ClassifyCategory(BaseModel):
    """Classification of the legal topic based on the user's query."""
    category: str = Field(
        description="The primary legal domain of the query. Must be exactly one of: Lease, NDA, Adoption, Trust, Property, Other"
    )

def classify_document_type(state: AuditorState) -> Dict[str, Any]:
    """
    Agent: The Gatekeeper Classifier
    Analyzes the user's question, determines which legal domain it falls under, 
    and sets the 'document_type' state variable.
    """
    print("\n🔮 [Agent: Classifier] Categorizing user legal question...")
    
    question = state["question"]
    
    # Initialize deterministic model (Gemini 1.5 Flash is perfect for high-speed triage)
    llm = ChatGoogleGenerativeAI(
        model=Config.DEFAULT_MODEL,
        api_key=Config.GEMINI_API_KEY,
        temperature=0
    )
    
    # Bind structured output schema to LLM
    structured_llm = llm.with_structured_output(ClassifyCategory)
    
    system_prompt = """You are an expert legal triage system. 
    Analyze the user's question and classify it into exactly one of the following categories:
    
    - Lease: For questions about rental agreements, lease deeds, landlords, tenants, tenant obligations, subletting, etc.
    - NDA: For questions about non-disclosure agreements, confidentiality, disclosing parties, trade secrets, etc.
    - Adoption: For questions about legal adoption processes, parental rights, child custody, guardianship, etc.
    - Trust: For questions about trusts, trustee responsibilities, trust deeds, estate planning, beneficiaries, etc.
    - Property: For questions about land sales, mortgages, deeds, boundary disputes, general property ownership, etc.
    - Other: For general questions that do not belong to any of the specific categories above.
    
    Return ONLY the structured category. Do not add any conversational text or explanation."""
    
    prompt = f"System: {system_prompt}\n\nUser Question:\n{question}\n\nClassification:"
    
    # Invoke structured chain
    result = structured_llm.invoke(prompt)
    category = result.category.strip()
    
    # Validate category falls in accepted set, fallback to Other if LLM output was unexpected
    valid_categories = {"Lease", "NDA", "Adoption", "Trust", "Property", "Other"}
    if category not in valid_categories:
        # Check case-insensitivity
        matching = [c for c in valid_categories if c.lower() == category.lower()]
        category = matching[0] if matching else "Other"
        
    print(f"🏷️ [Agent: Classifier] Classified question category as: {category}")
    
    return {
        "document_type": category
    }