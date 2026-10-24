import hashlib
import httpx
from qdrant_client import QdrantClient, models
from app.config import settings
client = QdrantClient(url=settings.qdrant_url, timeout=10)
def embed(text: str) -> list[float]:
    try:
        response = httpx.post(f"{settings.ollama_url}/api/embed", json={"model": settings.ollama_embed_model, "input": text}, timeout=settings.llm_timeout_seconds)
        response.raise_for_status()
        vectors = response.json().get("embeddings", [])
        if not vectors or not vectors[0]: raise RuntimeError()
        return vectors[0]
    except Exception as exc:
        raise RuntimeError("Embedding service unavailable") from exc
def ensure_collection():
    names = [c.name for c in client.get_collections().collections]
    if settings.qdrant_collection not in names:
        vector = embed("dimension probe")
        client.create_collection(collection_name=settings.qdrant_collection, vectors_config=models.VectorParams(size=len(vector), distance=models.Distance.COSINE))
def upsert_record(owner_id: int, record_type: str, record_id: int, text: str):
    vector = embed(text)
    point_id = int(hashlib.sha256(f"{owner_id}:{record_type}:{record_id}".encode()).hexdigest()[:15], 16)
    client.upsert(collection_name=settings.qdrant_collection, points=[models.PointStruct(id=point_id, vector=vector, payload={"owner_id":owner_id,"record_type":record_type,"record_id":record_id,"text":text})], wait=True)
def search_records(owner_id: int, query: str, limit: int=5):
    vector = embed(query)
    result = client.query_points(collection_name=settings.qdrant_collection, query=vector, query_filter=models.Filter(must=[models.FieldCondition(key="owner_id", match=models.MatchValue(value=owner_id))]), limit=limit, with_payload=True)
    return [{"record_type":p.payload.get("record_type"),"record_id":p.payload.get("record_id"),"text":p.payload.get("text"),"score":p.score} for p in result.points]
