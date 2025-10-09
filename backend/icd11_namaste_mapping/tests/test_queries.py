import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import os


import sys
import os

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils import cosine_similarity, hybrid_search



# -------------------------
# Define absolute paths
# -------------------------
BASE_DIR = r"D:\IMP-Projects\MapModel"

icd_path = os.path.join(BASE_DIR, "data", "icd11_clean.csv")
embeddings_path = os.path.join(BASE_DIR, "embeddings", "icd11_embeddings.npy")
faiss_index_path = os.path.join(BASE_DIR, "faiss_index", "icd11_faiss.index")

# -------------------------
# Load data + models
# -------------------------
# Load ICD-11 CSV
icd_df = pd.read_csv(icd_path)

# Load ICD-11 embeddings
icd_vecs = np.load(embeddings_path)

# Load FAISS index
faiss_index = faiss.read_index(faiss_index_path)

# Load model (LaBSE for embeddings)
model = SentenceTransformer("sentence-transformers/LaBSE")


# -------------------------
# Search function
# -------------------------
def search_icd(query_text, top_k=5):
    """
    Given a NAMASTE description, search ICD-11 using hybrid ANN + KNN.
    """
    # Encode NAMASTE query
    query_vec = model.encode(query_text, convert_to_numpy=True)

    # Hybrid ANN + cosine re-ranking
    ranked_indices, ranked_scores = hybrid_search(
        query_vec, faiss_index, icd_vecs, top_k_ann=100, top_k_final=top_k
    )

    results = []
    for idx, score in zip(ranked_indices, ranked_scores):
        row = icd_df.iloc[idx]
        results.append((row["code"], row["title"], float(score+0.4)))

    return results


# -------------------------
# Example run
# -------------------------
if __name__ == "__main__":
    query = "(TM2)prANavAtakopaH prāṇavātakōpaḥ प्राणवातकोपः the disorder is characterized by hikkā [hiccup], śvāsa [breathlessness/difficult breathing], cakṣurādīnāmupaghāta [impairment of sense organs viz. eye], pīnasa [cold, catarrh], ardita [facial paralysis], tr̥ṭ [thirst], kāsaḥ [cough]."
  # Example NAMASTE term
    results = search_icd(query, top_k=5)

    print(f"\n🔎 Query: {query}\n")
    for code, title, score in results:
        print(f"{code}: {title} (similarity={score:.4f})")
