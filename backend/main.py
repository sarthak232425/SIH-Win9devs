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
import re

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
DATASETS = {
    "UNANI": "UNANI.sqlite",
    "AYURVEDA": "AYURVEDA.sqlite", 
    "SIDDHA": "SIDDHA.sqlite"
}

# Store individual dataframes for each system
df_databases = {}

try:
    for system_name, file_path in DATASETS.items():
        if os.path.exists(file_path):
            try:
                conn = sqlite3.connect(file_path)
                tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)

                if not tables.empty:
                    table_name = tables.iloc[0, 0]
                    logger.info(f"Found table: {table_name} in {file_path}")
                    
                    df = pd.read_sql(f'SELECT * FROM "{table_name}"', conn)
                    
                    # Rename columns
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
                    df['Source_Database'] = system_name
                    df_databases[system_name] = df
                    logger.info(f"Loaded {system_name} dataset, shape: {df.shape}")
                conn.close()
            except sqlite3.Error as e:
                logger.error(f"SQLite error with {file_path}: {e}")
        else:
            logger.warning(f"Dataset not found: {file_path}")

    # Create combined dataframe
    if df_databases:
        df_combined = pd.concat(list(df_databases.values()), ignore_index=True)
        logger.info(f"Combined dataset shape: {df_combined.shape}")
    else:
        logger.warning("No SQL datasets loaded!")
        df_combined = pd.DataFrame()

except Exception as e:
    logger.error(f"Failed to load datasets: {e}")
    df_combined = pd.DataFrame()

# ---------------------------
# FastAPI app
# ---------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    systems: List[str] = ["ALL"]  # Default to search all systems

class ChatResponse(BaseModel):
    response: str
    source: str = "ai"

class SearchResponse(BaseModel):
    query: str
    systems: List[str]
    namaste_matches: List[Dict[str, Any]]
    icd11_matches: str

# ---------------------------
# Helper: Improved Search with system selection
# ---------------------------
def search_namc_complete(query: str, systems: List[str] = ["ALL"], top_k: int = 10) -> List[Dict[str, Any]]:
    if not df_databases:
        return []

    try:
        # Clean the query
        query = query.strip().lower()
        
        # Determine which dataframes to search
        if "ALL" in systems:
            search_dfs = list(df_databases.values())
        else:
            search_dfs = [df_databases[s] for s in systems if s in df_databases]
        
        if not search_dfs:
            return []
        
        all_results = []
        
        for df in search_dfs:
            # Determine search type based on query pattern
            is_code_search = re.match(r'^[a-zA-Z]*-?\d+', query)
            is_numeric_search = re.match(r'^\d+$', query)
            
            # Create search mask
            combined_mask = pd.Series([False] * len(df))
            
            # For code searches, prioritize exact matches in code fields
            if is_code_search and 'NAMC_CODE' in df.columns:
                code_mask = df["NAMC_CODE"].astype(str).str.lower() == query
                combined_mask = combined_mask | code_mask
            
            # For numeric searches, look for exact matches in numeric fields
            if is_numeric_search:
                if 'NAMC_ID' in df.columns:
                    id_mask = df["NAMC_ID"].astype(str) == query
                    combined_mask = combined_mask | id_mask
                if 'Sr_No' in df.columns:
                    sr_mask = df["Sr_No"].astype(str) == query
                    combined_mask = combined_mask | sr_mask
            
            # If no exact matches found, use intelligent search
            if not combined_mask.any():
                search_columns = ['NAMC_TERM', 'NAMC_CODE', 'NAMC_term_diacritical', 
                                'Short_definition', 'Long_definition', 'Reference']
                
                for col in search_columns:
                    if col in df.columns:
                        if col in ['NAMC_TERM', 'NAMC_CODE']:
                            # Exact match for key fields
                            col_mask = df[col].astype(str).str.lower() == query
                        else:
                            # Word boundary match for other fields
                            col_mask = df[col].astype(str).str.contains(
                                r'\b' + re.escape(query) + r'\b', case=False, na=False, regex=True
                            )
                        combined_mask = combined_mask | col_mask
            
            # Get results from this dataframe
            results = df[combined_mask].head(top_k)
            
            # Convert to list of dictionaries
            for _, row in results.iterrows():
                entry = {}
                for col in results.columns:
                    if pd.notna(row[col]) and str(row[col]).strip() != '':
                        entry[col] = row[col]
                
                # Add which columns matched this query
                matched_columns = []
                for col in ['NAMC_TERM', 'NAMC_term_diacritical', 'Short_definition', 
                           'Long_definition', 'NAMC_CODE', 'NAMC_ID', 'Sr_No']:
                    if col in row and pd.notna(row[col]) and query in str(row[col]).lower():
                        matched_columns.append(col)
                
                entry['matched_columns'] = matched_columns
                all_results.append(entry)
        
        return all_results[:top_k]  # Limit total results
        
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
    systems = request.systems
    logger.info(f"Searching for: '{query}' in systems: {systems}")
    
    namc_results = search_namc_complete(query, systems)
    icd_results = search_icd11(query)

    return SearchResponse(
        query=query,
        systems=systems,
        namaste_matches=namc_results,
        icd11_matches=icd_results,
    )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    query = request.query.strip()
    conversation_history = request.conversation_history or []

    # For chat, search all systems by default
    namc_results = search_namc_complete(query, ["ALL"])
    formatted_namc = "\n".join(
        [f"• {json.dumps(result, ensure_ascii=False, indent=2)}" 
         for result in namc_results[:3]]
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
        "databases_loaded": list(df_databases.keys()),
        "total_records": sum(len(df) for df in df_databases.values()) if df_databases else 0,
        "timestamp": time.time(),
    }

# Test route to check database connection
@app.get("/test-db")
def test_db():
    db_status = {}
    for system_name, file_path in DATASETS.items():
        if os.path.exists(file_path):
            try:
                conn = sqlite3.connect(file_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                db_status[system_name] = {
                    "status": "Connected",
                    "tables": [table[0] for table in tables],
                    "records": len(df_databases[system_name]) if system_name in df_databases else 0
                }
                conn.close()
            except sqlite3.Error as e:
                db_status[system_name] = {
                    "status": f"Error: {str(e)}",
                    "tables": []
                }
        else:
            db_status[system_name] = {
                "status": "File not found",
                "tables": []
            }
    
    return db_status