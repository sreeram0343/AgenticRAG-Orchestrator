import os
import sys
import time
import warnings
from dotenv import load_dotenv

# Suppress deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Force UTF-8 encoding for standard output on Windows to prevent emoji encoding crashes
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add parent directory to path to import Config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from src.config import Config
except ImportError:
    class Config:
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(__file__), 'raw_docs')
COLLECTION_NAME = "legal_frameworks"
QDRANT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'qdrant_storage'))

def classify_chunk_document_type(content: str, filename: str) -> str:
    """
    Deterministic rule-based document type classifier for ingestion metadata.
    This avoids slow/expensive LLM calls during batch ingestion.
    """
    text = (content + " " + filename).lower()
    if "lease" in text or "rent" in text or "landlord" in text or "tenant" in text:
        return "Lease"
    elif "nda" in text or "non-disclosure" in text or "disclosure" in text or "confidential" in text:
        return "NDA"
    elif "adoption" in text or "parent" in text or "child" in text:
        return "Adoption"
    elif "trust" in text or "trustee" in text or "settlor" in text or "beneficiary" in text:
        return "Trust"
    elif "property" in text or "estate" in text or "deed of sale" in text or "mortgage" in text:
        return "Property"
    else:
        return "Other"

def ingest_data():
    print(f"🔍 Looking for PDFs in {DATA_DIR}...")
    
    if not os.path.exists(DATA_DIR):
        print(f"❌ Error: Directory not found.")
        return
        
    loader = PyPDFDirectoryLoader(DATA_DIR)
    docs = loader.load()
    
    if not docs:
        print("❌ No PDFs found.")
        return

    print(f"📄 Loaded {len(docs)} pages. Splitting into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(docs)
    print(f"✂️ Created {len(chunks)} chunks.")

    print("🏷️ Annotating chunks with category metadata...")
    for chunk in chunks:
        source_file = os.path.basename(chunk.metadata.get("source", "unknown"))
        chunk.metadata["document_type"] = classify_chunk_document_type(chunk.page_content, source_file)

    print("🧠 Initializing Gemini Embeddings...")
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-2", 
        google_api_key=Config.GEMINI_API_KEY
    )

    print(f"🔌 Initializing Qdrant Local Persistent DB at: {QDRANT_PATH}")
    client = QdrantClient(path=QDRANT_PATH)
    
    # Recreate the collection if it exists to resolve any dimension mismatches
    if client.collection_exists(collection_name=COLLECTION_NAME):
        print(f"🗑️ Found existing collection '{COLLECTION_NAME}' with potential config mismatch. Recreating to align dimensions...")
        client.delete_collection(collection_name=COLLECTION_NAME)
        
    print(f"📁 Creating collection '{COLLECTION_NAME}' (3072 dimensions, Cosine)...")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
    )

    print(f"☁️ Uploading chunks to Qdrant (Batched to respect Free Tier Limits)...")
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=embeddings,
    )
    
    # Upload batches
    batch_size = 10
    total_batches = (len(chunks) - 1) // batch_size + 1
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        batch_num = i // batch_size + 1
        print(f"   -> Processing batch {batch_num} of {total_batches}...")
        
        while True:
            try:
                vector_store.add_documents(batch)
                time.sleep(3)  # Base delay of 3 seconds between batches
                break
            except Exception as e:
                if "429" in str(e):
                    print(f"⚠️ Quota exceeded! Forcing a full 60-second cooldown...")
                    time.sleep(60)
                    print(f"🔄 Retrying batch {batch_num}...")
                else:
                    client.close()
                    raise e
                    
    client.close()
    print("✅ Ingestion complete! The database is persistently saved.")

if __name__ == "__main__":
    ingest_data()