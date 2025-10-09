import numpy as np
import faiss


def cosine_similarity(query_vec, all_vecs):
    """
    Compute cosine similarity between a query vector and a set of vectors.

    Args:
        query_vec (np.ndarray): shape (d,)
        all_vecs (np.ndarray): shape (N, d)

    Returns:
        np.ndarray: similarity scores, shape (N,)
    """
    # Normalize
    query_vec = query_vec / np.linalg.norm(query_vec)
    all_vecs = all_vecs / np.linalg.norm(all_vecs, axis=1, keepdims=True)

    # Dot product gives cosine similarity
    sims = np.dot(all_vecs, query_vec)  # shape (N,)
    return sims


def ann_search(query_vec, faiss_index, top_k=100):
    """
    Approximate Nearest Neighbor (ANN) search using FAISS.

    Args:
        query_vec (np.ndarray): shape (d,)
        faiss_index: faiss index object
        top_k (int): number of candidates to return

    Returns:
        distances (np.ndarray): shape (top_k,)
        indices (np.ndarray): shape (top_k,)
    """
    query_vec = np.expand_dims(query_vec.astype("float32"), axis=0)
    distances, indices = faiss_index.search(query_vec, top_k)
    return distances[0], indices[0]


def hybrid_search(query_vec, faiss_index, all_vecs, top_k_ann=100, top_k_final=10):
    """
    Hybrid search: ANN shortlist + exact cosine re-ranking.

    Args:
        query_vec (np.ndarray): shape (d,)
        faiss_index: faiss index object
        all_vecs (np.ndarray): full matrix of ICD embeddings
        top_k_ann (int): ANN shortlist size
        top_k_final (int): final number of results to return

    Returns:
        ranked_indices (list[int]): indices of top results after re-ranking
        ranked_scores (list[float]): cosine similarity scores of results
    """
    # Step 1: ANN shortlist
    _, candidate_indices = ann_search(query_vec, faiss_index, top_k=top_k_ann)

    # Step 2: Re-rank with exact cosine similarity
    candidate_vecs = all_vecs[candidate_indices]
    sims = cosine_similarity(query_vec, candidate_vecs)

    # Sort by similarity (descending)
    sorted_idx = np.argsort(-sims)[:top_k_final]

    ranked_indices = candidate_indices[sorted_idx]
    ranked_scores = sims[sorted_idx]

    return ranked_indices.tolist(), ranked_scores.tolist()
