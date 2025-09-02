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
    "AYURVEDA": "AYURVEDA.sqlite",
    "UNANI": "UNANI.sqlite", 
    "SIDDHA": "SIDDHA.sqlite"
}

# Load ICD-11 database
ICD11_DATABASE = "ICD11.sqlite"

# Store individual dataframes for each system
df_databases = {}
df_icd11 = pd.DataFrame()

try:
    # Load NAMASTE databases
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

    # Load ICD-11 database
    if os.path.exists(ICD11_DATABASE):
        try:
            conn = sqlite3.connect(ICD11_DATABASE)
            tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
            
            if not tables.empty:
                table_name = tables.iloc[0, 0]
                logger.info(f"Found ICD-11 table: {table_name}")
                
                df_icd11 = pd.read_sql(f'SELECT * FROM "{table_name}"', conn)
                logger.info(f"Loaded ICD-11 dataset, shape: {df_icd11.shape}")
                
                # Clean column names (remove extra spaces, special characters)
                df_icd11.columns = df_icd11.columns.str.strip()
                logger.info(f"ICD-11 columns: {list(df_icd11.columns)}")
                
            conn.close()
        except sqlite3.Error as e:
            logger.error(f"SQLite error with ICD-11 database: {e}")
    else:
        logger.warning(f"ICD-11 database not found: {ICD11_DATABASE}")

    # Create combined dataframe for NAMASTE
    if df_databases:
        df_combined = pd.concat(list(df_databases.values()), ignore_index=True)
        logger.info(f"Combined NAMASTE dataset shape: {df_combined.shape}")
    else:
        logger.warning("No NAMASTE datasets loaded!")
        df_combined = pd.DataFrame()

except Exception as e:
    logger.error(f"Failed to load datasets: {e}")
    df_combined = pd.DataFrame()
    df_icd11 = pd.DataFrame()

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
    systems: List[str] = ["ALL"]

class MappingRequest(BaseModel):
    namaste_code: str

class ChatResponse(BaseModel):
    response: str
    source: str = "ai"

class SearchResponse(BaseModel):
    query: str
    systems: List[str]
    namaste_matches: List[Dict[str, Any]]
    icd11_matches: List[Dict[str, Any]]

class MappingResponse(BaseModel):
    namaste_code: str
    namaste_info: Dict[str, Any]
    icd11_matches: List[Dict[str, Any]]

# ---------------------------
# Helper: Search ICD-11 database - UPDATED FOR YOUR STRUCTURE
# ---------------------------
# REPLACE your search_icd11_database function with this:

def search_icd11_database(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    if df_icd11.empty:
        logger.warning("ICD-11 database is empty")
        return []

    try:
        query = query.strip().lower()
        results = []
        
        logger.info(f"Searching ICD-11 for: '{query}'")
        
        # Your actual column structure
        columns_to_search = ['Title', 'ChapterTitle', 'Code', 'Version', 'ChapterNr']
        reason_columns = ['Reason 1', 'Reason 2', 'Reason 3', 'Reason 4', 'Reason 5']
        
        # Search through all rows
        for _, row in df_icd11.iterrows():
            match_found = False
            matched_columns = []
            
            # Check main columns first
            for col in columns_to_search:
                if col in df_icd11.columns and pd.notna(row[col]):
                    cell_value = str(row[col]).lower()
                    if query in cell_value:
                        match_found = True
                        matched_columns.append(col)
                        break
            
            # If no match in main columns, check reason columns
            if not match_found:
                for col in reason_columns:
                    if col in df_icd11.columns and pd.notna(row[col]):
                        cell_value = str(row[col]).lower()
                        if query in cell_value:
                            match_found = True
                            matched_columns.append(col)
                            break
            
            if match_found:
                # Combine reason fields into a full description
                reason_fields = []
                for reason_col in reason_columns:
                    if reason_col in df_icd11.columns and pd.notna(row[reason_col]) and str(row[reason_col]).strip():
                        reason_fields.append(str(row[reason_col]).strip())
                
                full_description = " → ".join(reason_fields) if reason_fields else ""
                
                entry = {
                    'Version': row.get('Version', ''),
                    'Code': row.get('Code', ''),
                    'Title': row.get('Title', ''),
                    'ChapterNr': row.get('ChapterNr', ''),
                    'ChapterTitle': row.get('ChapterTitle', ''),
                    'FullDescription': full_description,
                    'matched_columns': matched_columns
                }
                
                # Clean up any encoding issues
                for key, value in entry.items():
                    if isinstance(value, str):
                        # Remove any non-printable characters
                        entry[key] = ''.join(char for char in value if char.isprintable())
                
                results.append(entry)
                
                if len(results) >= top_k:
                    break
        
        logger.info(f"Found {len(results)} ICD-11 matches for query: {query}")
        return results
        
    except Exception as e:
        logger.error(f"ICD-11 search error: {e}")
        return []

# ---------------------------
# Helper: Format ICD-11 results for display
# ---------------------------
def format_icd11_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not results:
        return []
    
    formatted_results = []
    for result in results:
        formatted_result = {}
        
        # Add all available fields
        for key, value in result.items():
            if pd.notna(value) and str(value).strip() != '':
                formatted_result[key] = value
        
        formatted_results.append(formatted_result)
    
    return formatted_results
# ---------------------------
# Helper: Search NAMASTE dataset - SIMPLIFIED
# ---------------------------
def search_namc_complete(query: str, systems: List[str] = ["ALL"], top_k: int = 10) -> List[Dict[str, Any]]:
    if not df_databases:
        return []

    try:
        query = query.strip()
        logger.info(f"Searching NAMASTE for: '{query}' in systems: {systems}")
        
        # Determine which dataframes to search
        if "ALL" in systems:
            search_dfs = list(df_databases.values())
        else:
            search_dfs = [df_databases[s] for s in systems if s in df_databases]
        
        if not search_dfs:
            return []
        
        all_results = []
        
        for df in search_dfs:
            # First try exact code matching
            if 'NAMC_CODE' in df.columns:
                code_mask = df['NAMC_CODE'].astype(str).str.upper().str.strip() == query.upper().strip()
                code_results = df[code_mask]
                
                for _, row in code_results.iterrows():
                    entry = {col: row[col] for col in df.columns if pd.notna(row[col]) and str(row[col]).strip() != ''}
                    entry['matched_columns'] = ['NAMC_CODE']
                    entry['match_type'] = 'exact_code'
                    all_results.append(entry)
            
            # Then try text search in other fields
            text_columns = ['NAMC_TERM', 'NAMC_term_diacritical', 'Short_definition', 'Long_definition']
            text_mask = pd.Series([False] * len(df))
            
            for col in text_columns:
                if col in df.columns:
                    col_mask = df[col].astype(str).str.lower().str.contains(query.lower(), na=False)
                    text_mask = text_mask | col_mask
            
            text_results = df[text_mask]
            for _, row in text_results.iterrows():
                entry = {col: row[col] for col in df.columns if pd.notna(row[col]) and str(row[col]).strip() != ''}
                
                # Find which columns matched
                matched_cols = []
                for col in text_columns:
                    if col in df.columns and pd.notna(row[col]) and query.lower() in str(row[col]).lower():
                        matched_cols.append(col)
                
                entry['matched_columns'] = matched_cols
                entry['match_type'] = 'text_search'
                all_results.append(entry)
        
        # Remove duplicates
        unique_results = []
        seen_codes = set()
        
        for result in all_results:
            code = result.get('NAMC_CODE', '') or result.get('NAMC_ID', '')
            if code and code not in seen_codes:
                seen_codes.add(code)
                unique_results.append(result)
            elif not code:
                unique_results.append(result)
            
            if len(unique_results) >= top_k:
                break
        
        logger.info(f"Found {len(unique_results)} NAMASTE matches")
        return unique_results
        
    except Exception as e:
        logger.error(f"NAMASTE search error: {e}")
        return []
def map_namaste_to_icd11(namaste_code: str) -> Dict[str, Any]:
    if not df_databases or df_icd11.empty:
        return {"namaste_info": {}, "icd11_matches": []}

    try:
        # Clean the code
        namaste_code = namaste_code.strip().upper()
        logger.info(f"Mapping NAMASTE code: {namaste_code}")
        
        # Find the NAMASTE entry
        namaste_info = {}
        source_system = ""
        
        # Search through all databases for the code
        for system_name, df in df_databases.items():
            if 'NAMC_CODE' in df.columns:
                # Case-insensitive code search
                code_mask = df['NAMC_CODE'].astype(str).str.upper().str.strip() == namaste_code
                matches = df[code_mask]
                
                if not matches.empty:
                    namaste_info = matches.iloc[0].to_dict()
                    source_system = system_name
                    logger.info(f"Found NAMASTE code in {system_name}: {namaste_info.get('NAMC_TERM', 'Unknown')}")
                    break
        
        if not namaste_info:
            logger.warning(f"NAMASTE code {namaste_code} not found in any database")
            return {"namaste_info": {}, "icd11_matches": []}
        
        # Add source system information
        namaste_info['Source_Database'] = source_system
        
        # Get the term to search for in ICD-11 - prioritize English terms
        search_terms = []
        
        # First priority: English term from NAMC_TERM (before parentheses)
        if 'NAMC_TERM' in namaste_info and pd.notna(namaste_info['NAMC_TERM']):
            term = str(namaste_info['NAMC_TERM']).split('(')[0].strip()
            if term and len(term) > 2:  # Only add meaningful terms
                search_terms.append(term)
        
        # Second priority: Short definition
        if 'Short_definition' in namaste_info and pd.notna(namaste_info['Short_definition']):
            definition = str(namaste_info['Short_definition']).split('.')[0].strip()
            if definition and len(definition) > 3:
                search_terms.append(definition)
        
        # Third priority: Extract keywords from both
        all_text = ""
        if 'NAMC_TERM' in namaste_info and pd.notna(namaste_info['NAMC_TERM']):
            all_text += " " + str(namaste_info['NAMC_TERM'])
        if 'Short_definition' in namaste_info and pd.notna(namaste_info['Short_definition']):
            all_text += " " + str(namaste_info['Short_definition'])
        
        # Extract meaningful English words (4+ letters)
        english_words = re.findall(r'\b[a-zA-Z]{4,}\b', all_text)
        search_terms.extend(english_words[:3])  # Add top 3 words
        
        # Remove duplicates and empty terms
        search_terms = [term for term in set(search_terms) if term.strip()]
        
        logger.info(f"Search terms for ICD-11: {search_terms}")
        
        if not search_terms:
            logger.warning(f"No search terms found for NAMASTE code {namaste_code}")
            return {"namaste_info": namaste_info, "icd11_matches": []}
        
        # Search ICD-11 with these terms
        icd11_matches = []
        
        for term in search_terms:
            if term.strip():
                term_matches = search_icd11_database(term, top_k=3)
                for match in term_matches:
                    match['match_reason'] = f'Matched: {term}'
                icd11_matches.extend(term_matches)
                
                if len(icd11_matches) >= 8:  # Reasonable limit
                    break
        
        # Remove duplicates by ICD-11 code
        unique_matches = []
        seen_codes = set()
        
        for match in icd11_matches:
            code = match.get('Code', '')
            if code and code not in seen_codes:
                seen_codes.add(code)
                unique_matches.append(match)
            elif not code:  # If no code, include anyway
                unique_matches.append(match)
        
        # Format the results
        formatted_matches = format_icd11_results(unique_matches)
        
        logger.info(f"Found {len(formatted_matches)} ICD-11 matches for {namaste_code}")
        
        return {
            "namaste_info": {k: v for k, v in namaste_info.items() if pd.notna(v) and str(v).strip() != ''},
            "icd11_matches": formatted_matches[:5]  # Limit to 5 best matches
        }
        
    except Exception as e:
        logger.error(f"Mapping error for code {namaste_code}: {e}")
        return {"namaste_info": {}, "icd11_matches": []}
# ---------------------------
# Medical System Prompt
# ---------------------------
MEDICAL_SYSTEM_PROMPT = """
You are an Ayurvedic medical assistant. Provide brief, precise answers about Ayurvedic terminology, herbs, and treatments.  
Use only Ayurvedic concepts and Sanskrit terms. Keep responses to few sentences.  
No Western medical references. Speak as one Vaidya to another.
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
        Relevant context:
        {context if context else "No additional context"}
        Please provide accurate medical information and recommend consulting healthcare professionals.
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
    icd_results = search_icd11_database(query)
    formatted_icd_results = format_icd11_results(icd_results)
    
    return SearchResponse(
        query=query,
        systems=systems,
        namaste_matches=namc_results,
        icd11_matches=formatted_icd_results,
    )

@app.post("/map", response_model=MappingResponse)
async def map_codes(request: MappingRequest):
    namaste_code = request.namaste_code
    logger.info(f"Mapping NAMASTE code: {namaste_code}")
    
    mapping_result = map_namaste_to_icd11(namaste_code)
    
    return MappingResponse(
        namaste_code=namaste_code,
        namaste_info=mapping_result["namaste_info"],
        icd11_matches=mapping_result["icd11_matches"]
    )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    query = request.query.strip()
    conversation_history = request.conversation_history or []

    # For chat, search all systems by default
    namc_results = search_namc_complete(query, ["ALL"])
    formatted_namc = "\n".join(
        [f"• {json.dumps(result, ensure_ascii=False, indent=2)}" 
         for result in namc_results[:2]]
    ) if namc_results else "No NAMASTE matches found"
    
    icd_context = search_icd11_database(query)
    formatted_icd = "\n".join(
        [f"• {json.dumps(result, ensure_ascii=False, indent=2)}" 
         for result in icd_context[:2]]
    ) if icd_context else "No ICD-11 matches found"
    
    combined_context = f"NAMASTE:\n{formatted_namc}\n\nICD-11:\n{formatted_icd}"

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
        "namaste_databases_loaded": list(df_databases.keys()),
        "icd11_database_loaded": not df_icd11.empty,
        "total_namaste_records": sum(len(df) for df in df_databases.values()) if df_databases else 0,
        "total_icd11_records": len(df_icd11) if not df_icd11.empty else 0,
        "timestamp": time.time(),
    }

# ADD this debug endpoint to see NAMASTE codes:

@app.get("/debug-namaste-codes")
def debug_namaste_codes():
    """Debug endpoint to see available NAMASTE codes"""
    codes_info = {}
    
    for system_name, df in df_databases.items():
        # Check what code columns exist
        code_columns = []
        for col in df.columns:
            if 'code' in col.lower() or 'cod' in col.lower():
                code_columns.append(col)
        
        # Get sample codes
        sample_codes = []
        if code_columns:
            code_col = code_columns[0]  # Use first code column found
            sample_codes = df[code_col].dropna().unique().tolist()[:10]
        
        codes_info[system_name] = {
            "code_columns": code_columns,
            "sample_codes": sample_codes,
            "total_records": len(df)
        }
    
    return codes_info

# Test route to check database connection
@app.get("/test-db")
def test_db():
    db_status = {}
    
    # Check NAMASTE databases
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
    
    # Check ICD-11 database
    if os.path.exists(ICD11_DATABASE):
        try:
            conn = sqlite3.connect(ICD11_DATABASE)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            db_status["ICD11"] = {
                "status": "Connected",
                "tables": [table[0] for table in tables],
                "records": len(df_icd11) if not df_icd11.empty else 0
            }
            conn.close()
        except sqlite3.Error as e:
            db_status["ICD11"] = {
                "status": f"Error: {str(e)}",
                "tables": []
            }
    else:
        db_status["ICD11"] = {
            "status": "File not found",
            "tables": []
        }
    
    return db_status