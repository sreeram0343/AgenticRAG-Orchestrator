import os
import sys
import time
import warnings
from dotenv import load_dotenv

# Suppress annoying deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Add the src directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from src.config import Config
except ImportError:
    class Config:
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        QDRANT_URL = os.getenv("QDRANT_URL")
        QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(__file__), 'raw_docs')
COLLECTION_NAME = "legal_frameworks"

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

    print("🧠 Initializing Gemini Embeddings...")
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-2", 
        google_api_key=Config.GEMINI_API_KEY
    )

    print("🔌 Initializing Qdrant In-Memory Database...")
    client = QdrantClient(":memory:")
    
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
    
    # --- BULLETPROOF RATE LIMIT FIX ---
    batch_size = 10
    total_batches = (len(chunks) - 1) // batch_size + 1
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        batch_num = i // batch_size + 1
        print(f"   -> Processing batch {batch_num} of {total_batches}...")
        
        while True:
            try:
                vector_store.add_documents(batch)
                time.sleep(3) # Base delay of 3 seconds between successful batches
                break # Break out of the while loop if successful
            except Exception as e:
                if "429" in str(e):
                    print(f"⚠️ Quota exceeded! Forcing a full 60-second cooldown to reset the API clock...")
                    time.sleep(60)
                    print(f"🔄 Retrying batch {batch_num}...")
                else:
                    raise e # Crash if it's a completely different error
                 
    print("✅ Ingestion complete! The data is loaded into memory.")

if __name__ == "__main__":
    ingest_data()