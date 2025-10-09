# src/preprocess.py

import pandas as pd
import os
import re

# ---------- Helpers ----------
def normalize_text(text: str) -> str:
    """
    Normalize text:
    - Lowercase English
    - Strip spaces
    - Remove multiple spaces
    """
    if pd.isna(text):
        return ""
    text = str(text).strip()
    text = re.sub(r"\s+", " ", text)
    return text.lower()

def combine_icd_fields(row) -> str:
    """
    Build a single string for embedding:
    Title | Description (if available)
    """
    parts = [
        normalize_text(row.get("title", "")),
        normalize_text(row.get("description", "")),
    ]
    return " | ".join([p for p in parts if p])

# ---------- Main ----------
def preprocess_icd(icd_path="D:\IMP-Projects\MapModel\data\icd11_mms.csv", output_path="D:\IMP-Projects\MapModel\data\icd11_clean.csv"):
    try:
        # First try utf-8
        icd_df = pd.read_csv(icd_path, encoding="utf-8")
    except UnicodeDecodeError:
        print("[INFO] UTF-8 failed, trying latin1...")
        icd_df = pd.read_csv(icd_path, encoding="latin1")

    # Normalize column names
    icd_df.columns = [col.strip().lower().replace(" ", "_") for col in icd_df.columns]

    # Pick only relevant columns (if they exist)
    keep_cols = []
    for col in ["code", "title", "description"]:
        if col in icd_df.columns:
            keep_cols.append(col)
    icd_df = icd_df[keep_cols]

    # Drop rows with missing codes or titles
    icd_df = icd_df.dropna(subset=["code", "title"])

    # Save cleaned version
    icd_df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"[INFO] Cleaned ICD-11 saved to {output_path} with {len(icd_df)} rows.")

    return icd_df

if __name__ == "__main__":
    df = preprocess_icd()
    print(df.head())
