import os
import requests
import sqlite3
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import time
import pandas as pd
import json

# ---------------------------
# Logging
# ---------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------
# Google AI Studio (Gemini) API configuration
# ---------------------------
GEMINI_MODEL = "gemini-1.5-flash"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
GEMINI_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv("GoogleAI.env")

    GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

    if GEMINI_API_KEY:
        GEMINI_AVAILABLE = True
        logger.info("Google AI Studio API is available ✅")
    else:
        logger.warning("Google AI Studio API key not found. AI features disabled.")

except Exception as e:
    logger.warning(f"Google AI Studio setup failed: {e}. AI features disabled.")

# ---------------------------
# Load NAMASTE datasets (from SQLite files)
# ---------------------------
DATASETS = ["UNANI.sqlite", "AYURVEDA.sqlite", "SIDDHA.sqlite"]
df_namc = pd.DataFrame()

try:
    frames = []
    for file in DATASETS:
        if os.path.exists(file):
            try:
                conn = sqlite3.connect(file)
                tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)

                if not tables.empty:
                    # Get the actual table name (it has hyphens, which is problematic)
                    table_name = tables.iloc[0, 0]
                    logger.info(f"Found table: {table_name} in {file}")
                    
                    # Read the data
                    df = pd.read_sql(f'SELECT * FROM "{table_name}"', conn)
                    
                    # Rename columns to match expected format
                    column_mapping = {}
                    if 'Column_1' in df.columns: column_mapping['Column_1'] = 'Sr_No'
                    if 'Column_2' in df.columns: column_mapping['Column_2'] = 'NAMC_ID'
                    if 'Column_3' in df.columns: column_mapping['Column_3'] = 'NAMC_CODE'
                    if 'Column_4' in df.columns: column_mapping['Column_4'] = 'NAMC_TERM'
                    if 'Column_5' in df.columns: column_mapping['Column_5'] = 'NAMC_term_diacritical'
                    if 'Column_6' in df.columns: column_mapping['Column_6'] = 'Short_definition'
                    if 'Column_7' in df.columns: column_mapping['Column_7'] = 'Long_definition'
                    if 'Column_8' in df.columns: column_mapping['Column_8'] = 'Reference'
                    
                    df = df.rename(columns=column_mapping)
                    # Add source information to identify which database the record came from
                    df['Source_Database'] = file.replace('.sqlite', '')
                    frames.append(df)
                    logger.info(f"Loaded dataset {file}, table: {table_name}, shape: {df.shape}")
                conn.close()
            except sqlite3.Error as e:
                logger.error(f"SQLite error with {file}: {e}")
        else:
            logger.warning(f"Dataset not found: {file}")

    if frames:
        df_namc = pd.concat(frames, ignore_index=True)
        logger.info(f"Combined dataset shape: {df_namc.shape}")
        logger.info(f"Available columns: {list(df_namc.columns)}")
    else:
        logger.warning("No SQL datasets loaded!")

except Exception as e:
    logger.error(f"Failed to load datasets: {e}")

# ---------------------------
# FastAPI app
# ---------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # adjust for prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Models
# ---------------------------
class ChatRequest(BaseModel):
    query: str
    conversation_history: Optional[List[Dict]] = None

class SearchRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    response: str
    source: str = "ai"

class SearchResponse(BaseModel):
    query: str
    namaste_matches: List[Dict[str, Any]]
    icd11_matches: str

# ---------------------------
# Helper: Search NAMASTE dataset - Returns complete entries
# ---------------------------
def search_namc_complete(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    if df_namc.empty:
        return []

    try:
        # Create search mask based on available columns
        mask = pd.Series([False] * len(df_namc))
        
        # Search in different columns if they exist
        search_columns = []
        if 'NAMC_TERM' in df_namc.columns: 
            mask = mask | df_namc["NAMC_TERM"].astype(str).str.contains(query, case=False, na=False)
            search_columns.append('NAMC_TERM')
        if 'NAMC_term_diacritical' in df_namc.columns:
            mask = mask | df_namc["NAMC_term_diacritical"].astype(str).str.contains(query, case=False, na=False)
            search_columns.append('NAMC_term_diacritical')
        if 'Short_definition' in df_namc.columns:
            mask = mask | df_namc["Short_definition"].astype(str).str.contains(query, case=False, na=False)
            search_columns.append('Short_definition')
        if 'Long_definition' in df_namc.columns:
            mask = mask | df_namc["Long_definition"].astype(str).str.contains(query, case=False, na=False)
            search_columns.append('Long_definition')
        if 'NAMC_CODE' in df_namc.columns:
            mask = mask | df_namc["NAMC_CODE"].astype(str).str.contains(query, case=False, na=False)
            search_columns.append('NAMC_CODE')
        
        results = df_namc[mask].head(top_k)

        if results.empty:
            return []

        # Convert the matching rows to a list of dictionaries with complete data
        complete_results = []
        for _, row in results.iterrows():
            # Create a dictionary with all available fields
            entry = {}
            for col in results.columns:
                if pd.notna(row[col]) and str(row[col]).strip() != '':
                    entry[col] = row[col]
            
            # Add which columns matched this query
            matched_columns = []
            for col in search_columns:
                if col in row and pd.notna(row[col]) and query.lower() in str(row[col]).lower():
                    matched_columns.append(col)
            
            entry['matched_columns'] = matched_columns
            complete_results.append(entry)
        
        return complete_results
        
    except Exception as e:
        logger.error(f"Dataset search error: {e}")
        return []

# ---------------------------
# Helper: Search ICD-11 API
# ---------------------------
ICD_API_URL = "https://icd11restapi-developer-test.azurewebsites.net/icd/release/11/"

def search_icd11(query: str, top_k: int = 5) -> str:
    try:
        url = f"{ICD_API_URL}search?q={query}&flatResults=true&highlighting=false"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if "destinationEntities" not in data:
            return "No ICD-11 matches found"

        results = data["destinationEntities"][:top_k]
        if not results:
            return "No ICD-11 matches found"

        context = "\n".join(
            f"- {item.get('title', 'N/A')} → Code: {item.get('theCode', 'N/A')}"
            for item in results
        )
        return context

    except Exception as e:
        logger.error(f"ICD-11 search error: {e}")
        return "Error searching ICD-11"

# ---------------------------
# Medical System Prompt
# ---------------------------
MEDICAL_SYSTEM_PROMPT = """
You are Dr. MedBot, a specialized medical AI assistant.
You provide accurate, safe, evidence-based medical information.
Always connect NAMASTE codes with WHO ICD-11 where relevant.
Never provide a definitive diagnosis—only educational information.
Always recommend consulting a healthcare professional. Keep answers concise.
"""

# ---------------------------
# Google Gemini Chatbot Logic
# ---------------------------
def call_gemini_medical(query: str, conversation_history: List[Dict] = None, context: str = "") -> Optional[str]:
    if not GEMINI_AVAILABLE or not GEMINI_API_KEY:
        return None

    try:
        headers = {"Content-Type": "application/json"}

        contents = [{"role": "user", "parts": [{"text": MEDICAL_SYSTEM_PROMPT}]}]

        if conversation_history:
            for msg in conversation_history:
                role = "user" if msg.get("role") == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})

        final_query = f"""
        User asked: {query}
        Relevant NAMASTE dataset context:
        {context if context else "No NAMASTE match"}
        Please also map/search ICD-11 if relevant.
        """
        contents.append({"role": "user", "parts": [{"text": final_query}]})

        payload = {
            "contents": contents,
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 600},
        }

        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers=headers,
            json=payload,
            timeout=20,
        )
        response.raise_for_status()

        result = response.json()
        candidates = result.get("candidates", [])
        if candidates and "content" in candidates[0]:
            parts = candidates[0]["content"].get("parts", [])
            if parts and "text" in parts[0]:
                return parts[0]["text"].strip()

        return None

    except Exception as e:
        logger.error(f"Google AI Studio error: {e}")
        return None

# ---------------------------
# Routes
# ---------------------------
@app.get("/")
def read_root():
    return {"message": "Medical AI Search + Chatbot running ✅"}

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    query = request.query
    logger.info(f"Searching for: {query}")
    
    namc_results = search_namc_complete(query)
    icd_results = search_icd11(query)

    return SearchResponse(
        query=query,
        namaste_matches=namc_results,
        icd11_matches=icd_results,
    )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    query = request.query.strip()
    conversation_history = request.conversation_history or []

    # For chat, we still want the formatted context
    namc_results = search_namc_complete(query)
    formatted_namc = "\n".join(
        [f"• {json.dumps(result, ensure_ascii=False, indent=2)}" 
         for result in namc_results[:3]]  # Limit to 3 for chat context
    ) if namc_results else "No NAMASTE matches found"
    
    icd_context = search_icd11(query)
    combined_context = f"NAMASTE:\n{formatted_namc}\n\nICD-11:\n{icd_context}"

    if GEMINI_AVAILABLE:
        ai_response = call_gemini_medical(query, conversation_history, context=combined_context)
        if ai_response:
            return ChatResponse(response=ai_response, source="ai")

    return ChatResponse(
        response="⚠️ AI unavailable, but raw search is working.",
        source="system",
    )

@app.get("/status")
def get_status():
    return {
        "ai_available": GEMINI_AVAILABLE,
        "dataset_loaded": not df_namc.empty,
        "dataset_size": df_namc.shape[0] if not df_namc.empty else 0,
        "dataset_columns": list(df_namc.columns) if not df_namc.empty else [],
        "timestamp": time.time(),
    }

# Test route to check database connection
@app.get("/test-db")
def test_db():
    db_status = {}
    for file in DATASETS:
        if os.path.exists(file):
            try:
                conn = sqlite3.connect(file)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                db_status[file] = {
                    "status": "Connected",
                    "tables": [table[0] for table in tables]
                }
                conn.close()
            except sqlite3.Error as e:
                db_status[file] = {
                    "status": f"Error: {str(e)}",
                    "tables": []
                }
        else:
            db_status[file] = {
                "status": "File not found",
                "tables": []
            }
    
    return db_status