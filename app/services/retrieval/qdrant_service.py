import logfire
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.config import settings
from app.services.retrieval.embedding import embed_query, embed_query_sparse


# Initialize Qdrant Client
client = QdrantClient(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY,
    timeout=60,
    check_compatibility=False
)

def search_enterprise_knowledge(query: str, limit: int = 8):
    """
    Performs a Hybrid Search (Dense Semantic + Sparse BM25 Keyword) 
    in the enterprise knowledge base using Reciprocal Rank Fusion (RRF).
    """
    try:
        
        dense_query_vector = embed_query(query)
        sparse_query_dict = embed_query_sparse(query)

        # Using query_points - the modern standard for Qdrant
        response = client.query_points(
            collection_name=settings.QDRANT_COLLECTION,
            prefetch=[
                models.Prefetch(
                    query=dense_query_vector,
                    using="dense",
                    limit=limit
                ),
                models.Prefetch(
                    query=models.SparseVector(
                        indices=sparse_query_dict["indices"],
                        values=sparse_query_dict["values"]
                    ),
                    using="sparse",
                    limit=limit
                ),
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=limit,
            with_payload=True # JSON
        )

        results = []
        for res in response.points:
            results.append({
                "content": res.payload.get("text", ""),
                "source": res.payload.get("source", "Unknown"),
                "score": float(res.score)
            })
        
        return results
    except Exception as e:
        logfire.error(f"Qdrant Search Failed: {e}")
        return []
