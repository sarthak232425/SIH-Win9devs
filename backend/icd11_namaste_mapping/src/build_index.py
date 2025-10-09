# src/build_index.py

import os
import numpy as np
import faiss
import pandas as pd

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EMBED_PATH = os.path.join(BASE_DIR, "../embeddings/icd11_embeddings.npy")
META_PATH = os.path.join(BASE_DIR, "../embeddings/icd11_metadata.csv")
INDEX_PATH = os.path.join(BASE_DIR, "../faiss_index/icd11_faiss.index")

def build_faiss_index(embeddings: np.ndarray, use_gpu: bool = False):
    """
    Build a FAISS index for ICD-11 embeddings.
    Using Inner Product (dot product) which works with normalized vectors.
    """
    d = embeddings.shape[1]  # embedding dimension

    # Index for cosine similarity (inner product since embeddings are normalized)
    index = faiss.IndexFlatIP(d)

    if use_gpu:
        print("⚡ Moving FAISS index to GPU")
        res = faiss.StandardGpuResources()
        index = faiss.index_cpu_to_gpu(res, 0, index)

    print("➕ Adding embeddings to FAISS index...")
    index.add(embeddings)

    return index

def main():
    print("📥 Loading ICD-11 embeddings...")
    embeddings = np.load(EMBED_PATH)

    print("📥 Loading metadata...")
    meta_df = pd.read_csv(META_PATH)

    print(f"✅ Loaded {len(embeddings)} embeddings with {len(meta_df)} metadata entries")

    # Ensure directories exist
    os.makedirs("../faiss_index", exist_ok=True)

    # Build FAISS index
    index = build_faiss_index(embeddings, use_gpu=False)

    # Save index to file
    faiss.write_index(index, INDEX_PATH)

    print(f"💾 FAISS index saved to {INDEX_PATH}")
    print("🎉 Done!")

if __name__ == "__main__":
    main()
