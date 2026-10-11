import vertexai
from vertexai.language_models import TextEmbeddingModel
from app.config import settings
from fastembed import SparseTextEmbedding

dense_model = None
sparse_model = None
BATCH_SIZE = 50 


def get_dense_embedding_model():
    global dense_model
    if dense_model is None:
        vertexai.init(project=settings.PROJECT_ID, location=settings.LOCATION)
        dense_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    return dense_model

def get_sparse_embedding_model():
    global sparse_model
    if sparse_model is None:
        # Use SparseTextEmbedding specifically for BM25 / sparse models
        sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")
    return sparse_model


def embed_query(query: str):
    """Embeds a single query string into dense vector."""
    model = get_dense_embedding_model()
    embeddings = model.get_embeddings([query])
    return embeddings[0].values

def embed_query_sparse(query: str):
    """Embeds a single query string into sparse vector."""
    sparse_m = get_sparse_embedding_model()
    # fastembed returns a generator of SparseEmbedding objects
    sparse_emb = list(sparse_m.embed([query]))[0]
    return {"indices": sparse_emb.indices.tolist(), "values": sparse_emb.values.tolist()}


def embed_texts(texts: list[str]):
    """Embeds a list of text strings in batches (Dense)."""
    model = get_dense_embedding_model()
    all_embeddings = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i+BATCH_SIZE]
        embeddings = model.get_embeddings(batch)
        all_embeddings.extend([e.values for e in embeddings])
    return all_embeddings


def embed_texts_sparse(texts: list[str]):
    """Embeds a list of text strings into sparse vectors (BM25)."""
    sparse_m = get_sparse_embedding_model()
    sparse_embeddings = list(sparse_m.embed(texts))
    
    formatted_sparse = []
    for se in sparse_embeddings:
        formatted_sparse.append({
            "indices": se.indices.tolist(),
            "values": se.values.tolist()
        })
    return formatted_sparse
