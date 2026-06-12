import chromadb
from chromadb.utils import embedding_functions
from config.settings import get_settings
import os
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv
load_dotenv()

settings = get_settings()

os.environ["GROQ_API_KEY"] = settings.groq_api_key
os.environ["GROQ_MODEL"] = settings.groq_model


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200)->list:
    chunks = []
    pos = 0
    while pos < len(text):
        chunk = text[pos:pos+chunk_size]
        chunks.append(chunk)
        pos += chunk_size - overlap
    return chunks

def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )
    
def get_collection():
    client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    collection = client.get_or_create_collection(name=settings.chroma_collection_name,
        metadata={"hnsw:space": "cosine"})
    return collection

def index_document(text: str, doc_id: str, metadata: dict) -> int:
    collection = get_collection()
    embedder = get_embeddings()
    chunks = chunk_text(text)
    ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{**metadata, "chunk_index": i} for i in range(len(chunks))]
    embeddings = embedder.embed_documents(chunks)  # ← embed with Gemini
    collection.upsert(
        documents=chunks,
        ids=ids,
        metadatas=metadatas,
        embeddings=embeddings  
    )
    return len(chunks)
    
def query(query_text: str, n_results: int = 5)->list:
    # get_collection() connects to our vector database
    collection = get_collection()
    embedder = get_embeddings()
    query_embedding = embedder.embed_query(query_text)
    # query() performs semantic search
    results = collection.query(query_embeddings = [query_embedding],n_results=n_results)
    doc = results["documents"][0]
    meta = results["metadatas"][0]
    dist = results["distances"][0]
    return [
        {"text":doc,"metadata":meta,"distance":dist}
        for doc,meta,dist in zip(doc,meta,dist)
    ]  