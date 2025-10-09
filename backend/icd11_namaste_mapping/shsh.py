# fetch_icd11_full.py

import requests
import pandas as pd
import time
from tqdm import tqdm

# =======================
# CONFIG
# =======================
TOKEN = "YOUR_API_KEY"  # Replace with your WHO ICD-11 API key
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json"
}

RELEASE_ID = "2024-01"  # Adjust if needed
LINEARIZATION = "mms"   # e.g., "mms", "tm2"
BASE_URL = f"https://id.who.int/icd/release/11/{RELEASE_ID}/{LINEARIZATION}/"

INPUT_CSV = "D:/IMP-Projects/MapModel/data/icd11_clean.csv"
OUTPUT_CSV = "D:/IMP-Projects/MapModel/data/icd11_full.csv"

# =======================
# FUNCTIONS
# =======================
def fetch_icd_details(code, retries=3, delay=0.5):
    """Fetch ICD-11 details for a given code with retries."""
    url = f"{BASE_URL}codeinfo/{code}"
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                data = r.json()
                title = data.get("title", {}).get("@value", "") if data.get("title") else ""
                definition = data.get("definition", {}).get("@value", "") if data.get("definition") else ""
                synonyms = "; ".join(s.get("@value", "") for s in data.get("synonym", [])) if data.get("synonym") else ""
                return {"code": code, "title": title, "description": definition, "synonyms": synonyms}
            elif r.status_code == 429:
                print(f"⚠️ Rate limit hit, sleeping {delay} seconds...")
                time.sleep(delay)
            else:
                print(f"⚠️ Failed for {code}: {r.status_code}")
                break
        except requests.RequestException as e:
            print(f"⚠️ Exception for {code}: {e}")
            time.sleep(delay)
    return {"code": code, "title": "", "description": "", "synonyms": ""}

# =======================
# MAIN SCRIPT
# =======================
def main():
    # Load existing ICD-11 CSV
    df = pd.read_csv(INPUT_CSV)
    if "code" not in df.columns:
        raise ValueError("Input CSV must have a 'code' column.")

    enriched = []
    print(f"📥 Fetching details for {len(df)} ICD-11 codes...")
    for code in tqdm(df["code"].tolist()):
        details = fetch_icd_details(code)
        enriched.append(details)
        time.sleep(0.2)  # prevent rate-limiting

    enriched_df = pd.DataFrame(enriched)
    enriched_df.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ Saved enriched ICD-11 data to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
