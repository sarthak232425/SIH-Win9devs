# src/embed.py

import os
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

# Relative paths (portable across systems)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ICD_PATH = os.path.join(BASE_DIR,"icd11_namaste_mapping", "data", "icd11_clean.csv")
EMBED_SAVE_PATH = os.path.join(BASE_DIR, "icd11_namaste_mapping","embeddings", "icd11_embeddings.npy")
META_SAVE_PATH = os.path.join(BASE_DIR, "icd11_namaste_mapping", "embeddings", "icd11_metadata.csv")

def load_icd_data(icd_path: str):
    """Load ICD-11 dataset and prepare text for embedding."""
    df = pd.read_csv(icd_path)

    df.columns = [c.lower() for c in df.columns]
    if not {"code", "title"}.issubset(df.columns):
        raise ValueError("CSV must contain 'code' and 'title' columns")

    df["text"] = df["code"].astype(str) + " - " + df["title"].astype(str)
    return df

def generate_embeddings(texts, model_name="sentence-transformers/LaBSE", batch_size=32):
    """Generate LaBSE embeddings for given texts."""
    model = SentenceTransformer(model_name)
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        convert_to_numpy=True,
        show_progress_bar=True,
        normalize_embeddings=True
    )
    return embeddings

def main():
    print("📥 Loading ICD-11 clean data...")
    df = load_icd_data(ICD_PATH)
    print(f"✅ Loaded {len(df)} ICD-11 records")

    print("🔎 Generating embeddings with LaBSE...")
    embeddings = generate_embeddings(df["text"].tolist())

    # Save embeddings + metadata
    os.makedirs(os.path.join(BASE_DIR, "embeddings"), exist_ok=True)
    np.save(EMBED_SAVE_PATH, embeddings)
    df[["code", "title"]].to_csv(META_SAVE_PATH, index=False)

    print(f"💾 Saved embeddings → {EMBED_SAVE_PATH}")
    print(f"💾 Saved metadata → {META_SAVE_PATH}")
    print("🎉 Done!")

if __name__ == "__main__":
    main()
