import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # LLM Settings
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    DEFAULT_MODEL = "gemini-1.5-flash"  # Fast and cost-effective for agent loops
    ADVANCED_MODEL = "gemini-1.5-pro"   # Best for complex compliance reasoning
    
    # Vector DB Settings
    QDRANT_URL = os.getenv("QDRANT_URL")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    
    # Validation check to catch missing keys early
    @classmethod
    def validate(cls):
        missing = [key for key, val in {
            "GEMINI_API_KEY": cls.GEMINI_API_KEY
        }.items() if not val]
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

# Validate config immediately upon import
Config.validate()