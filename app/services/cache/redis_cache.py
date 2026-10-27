import redis
from redis.commands.search.field import VectorField, TextField
from redis.commands.search.index_definition import IndexDefinition, IndexType

# Redis connection
redis_client = redis.Redis(host='localhost', port=6380, decode_responses=True)

INDEX_NAME = "semantic_cache_idx"
PREFIX = "cache:"
VECTOR_DIMENSION = 768  # Tera jo bhi embedding dimension ho (jaise vertexai text-embedding-004 ka)

def create_redis_cache_index():
    try:
        # Check if index already exists
        redis_client.ft(INDEX_NAME).info()
    except Exception:
        # Schema definition for semantic cache
        schema = [
            TextField("query"),
            TextField("response"),
            VectorField("vector", "FLAT", {
                "TYPE": "FLOAT32",
                "DIM": VECTOR_DIMENSION,
                "DISTANCE_METRIC": "COSINE"
            })
        ]
        definition = IndexDefinition(prefix=[PREFIX], index_type=IndexType.HASH)
        redis_client.ft(INDEX_NAME).create_index(schema, definition=definition)




import numpy as np

def check_semantic_cache(query_vector: list[float], threshold: float = 0.92):
    # Vector search query using Redis FT.SEARCH
    base_query = f"*=>[KNN 1 @vector $vec AS score]"
    query_params = {"vec": np.array(query_vector, dtype=np.float32).tobytes()}
    
    try:
        results = redis_client.ft(INDEX_NAME).search(base_query, query_params=query_params)
        if results.docs:
            top_doc = results.docs[0]
            raw_score = float(top_doc.score)
            calculated_similarity = 1 - raw_score
            print(f"🔍 [REDIS DEBUG] Raw Distance: {raw_score} | Calculated Similarity: {calculated_similarity}")
            
            if calculated_similarity >= threshold:
                return top_doc.response
    except Exception as e:
        print(f"Cache search error: {e}")
    
    return None




import uuid

def store_in_semantic_cache(query: str, response: str, query_vector: list[float]):
    cache_id = str(uuid.uuid4())
    key = f"{PREFIX}{cache_id}"
    
    mapping = {
        "query": query,
        "response": response,
        "vector": np.array(query_vector, dtype=np.float32).tobytes()
    }
    
    redis_client.hset(key, mapping=mapping)
    # TTL set kar sakte hain taaki purana data apne aap expire ho jaye (jaise 7 days)
    redis_client.expire(key, 60 * 60 * 24 * 7)