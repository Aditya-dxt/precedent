"""
Embeddings Service
------------------
Loads sentence-transformers model once and provides embedding utilities.
CPU-only inference; model cached after first load.
"""

import numpy as np
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

_model = None
MODEL_NAME = "all-MiniLM-L6-v2"


def load_model():
    """Load the embedding model. Called once at app startup."""
    global _model
    if _model is not None:
        return _model
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME, device="cpu")
        logger.info(f"Loaded sentence-transformer model: {MODEL_NAME}")
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        _model = None
    return _model


def get_model():
    global _model
    if _model is None:
        load_model()
    return _model


def embed_texts(texts: List[str]) -> Optional[np.ndarray]:
    """
    Generate sentence embeddings for a list of texts.
    Returns numpy array of shape (N, embedding_dim) or None on failure.
    """
    if not texts:
        return None
    model = get_model()
    if model is None:
        logger.warning("Embedding model not available; returning None")
        return None
    try:
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False, batch_size=32)
        return embeddings
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return None


def cosine_similarity_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Compute cosine similarity between two sets of embeddings."""
    # Normalize
    a_norm = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-8)
    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-8)
    return a_norm @ b_norm.T


def cluster_questions(
    questions: List[str],
    embeddings: np.ndarray,
    threshold: float = 0.72,
    min_cluster_size: int = 1,
) -> List[List[int]]:
    """
    Group semantically similar questions using greedy cosine-similarity clustering.
    Returns list of clusters, each cluster is a list of question indices.
    threshold: cosine similarity above which two questions are considered the same topic.
    """
    if embeddings is None or len(embeddings) == 0:
        return [[i] for i in range(len(questions))]

    n = len(embeddings)
    visited = [False] * n
    clusters = []

    # Precompute full similarity matrix
    sim_matrix = cosine_similarity_matrix(embeddings, embeddings)

    for i in range(n):
        if visited[i]:
            continue
        cluster = [i]
        visited[i] = True
        for j in range(i + 1, n):
            if not visited[j] and sim_matrix[i, j] >= threshold:
                cluster.append(j)
                visited[j] = True
        if len(cluster) >= min_cluster_size:
            clusters.append(cluster)

    return clusters


def map_clusters_to_topics(
    cluster_embeddings: np.ndarray,  # representative embedding per cluster
    topic_texts: List[str],
    topic_embeddings: np.ndarray,
    top_k: int = 1,
) -> List[int]:
    """
    For each cluster, find the closest syllabus topic index.
    Returns list of topic indices (one per cluster).
    """
    if topic_embeddings is None or cluster_embeddings is None:
        return [0] * len(cluster_embeddings)

    sim = cosine_similarity_matrix(cluster_embeddings, topic_embeddings)
    return [int(np.argmax(row)) for row in sim]
