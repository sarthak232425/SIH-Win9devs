# src/query.py

import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INDEX_PATH = os.path.join(BASE_DIR, "..", "faiss_index", "icd11_faiss.index")
META_PATH = os.path.join(BASE_DIR, "..", "embeddings", "icd11_metadata.csv")
EMBED_PATH = os.path.join(BASE_DIR, "..", "embeddings", "icd11_embeddings.npy")

from model_manager import ModelManager


# Load LaBSE once
# model = SentenceTransformer("sentence-transformers/LaBSE")
# Initialize these as None

index = None
meta_df = None 
icd_embeddings = None
model = None

def load_resources():
    """Ensure resources are loaded before search"""
    global index, meta_df, icd_embeddings, model

    if index is None:
        index = faiss.read_index(INDEX_PATH)
    if meta_df is None:
        meta_df = pd.read_csv(META_PATH)
    if icd_embeddings is None:
        icd_embeddings = np.load(EMBED_PATH)
    if model is None:
        model = ModelManager.get_model()

def embed_text(text: str):
    """
    Generate normalized LaBSE embedding for query text.
    """
    embedding = model.encode(
        [text],
        convert_to_numpy=True,
        normalize_embeddings=True
    )
    return embedding

def map_icd(query: str, ann_top_k: int = 50, final_top_k: int = 5):
    """
    Hybrid search: ANN shortlist + exact cosine re-ranking.
    """

    # Ensure resources are loaded
    load_resources()

    # Step 1: Embed query
    q_vec = embed_text(query)

    # Step 2: ANN search with FAISS
    D, I = index.search(q_vec, ann_top_k)

    candidate_indices = I[0]
    candidate_embeddings = icd_embeddings[candidate_indices]

    # Step 3: Re-rank with cosine similarity (exact KNN)
    sim_scores = cosine_similarity(q_vec, candidate_embeddings)[0]

    # Step 4: Sort by similarity
    sorted_idx = np.argsort(sim_scores)[::-1]  # descending
    top_indices = candidate_indices[sorted_idx[:final_top_k]]
    top_scores = sim_scores[sorted_idx[:final_top_k]]

    # Step 5: Build results
    results = []
    for rank, (idx, score) in enumerate(zip(top_indices, top_scores)):
        code = meta_df.iloc[idx]["code"]
        title = meta_df.iloc[idx]["title"]
        results.append({
            "rank": rank + 1,
            "code": code,
            "title": title,
            "score": float(score)
        })

    return results


