import os
import warnings
import sys
import gc
import psutil
import google.generativeai as genai
from dotenv import load_dotenv

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['USE_TF'] = 'False'
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
warnings.filterwarnings('ignore')

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Load environment variables
load_dotenv()

# Configure Gemini API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

# Set up Gemini chat model
chat_model = genai.GenerativeModel('gemini-2.5-flash-lite')

# Define system prompt for medical/Ayurveda focus
SYSTEM_PROMPT = """You are an expert in Ayurvedic medicine and modern medical terminology. Your role is to:
1. Only answer questions related to medical terms, health conditions, Ayurvedic concepts, and traditional medicine
2. Provide accurate information about Ayurvedic treatments, herbs, and medical concepts
3. Explain connections between modern medical terms and Ayurvedic concepts when relevant
4. For non-medical or non-Ayurvedic questions, politely explain that you can only assist with medical and Ayurvedic topics

DO NOT:
- Answer questions unrelated to medicine, health, or Ayurveda
- Provide personal medical advice or diagnoses
- Discuss non-medical topics
- Give an answer of more than 100 words

If a question is not related to medicine or Ayurveda, respond with: "I can only assist with questions related to medical terms, health conditions, and Ayurvedic concepts. Please ask a relevant question."
"""

# Import both search engines
from namaste_search.src.search import AyurvedicSearch
from icd11_search.src.search import ICD11Search
from model_manager import ModelManager
# Added import: use the standalone ICD search function
from icd11_namaste_mapping.src.query import map_icd

ayurvedic_engine = None
icd_engine = None
server_start_time = None

def check_memory():
    memory = psutil.virtual_memory()
    available_gb = memory.available / (1024**3)
    print(f"💾 Available Memory: {available_gb:.1f} GB")
    print(f"💾 Memory Usage: {memory.percent}%")
    if available_gb < 2.0:
        print("⚠️  Warning: Less than 2GB available memory")
        print("🔧 Consider closing other applications")
        return False
    return True

def optimize_memory():
    print("🧹 Optimizing memory...")
    gc.collect()
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['MKL_NUM_THREADS'] = '1'
    print("✅ Memory optimization complete")

def initialize_search_engines():
    global ayurvedic_engine, icd_engine, server_start_time
    print("🌿 Initializing Ayurvedic & ICD-11 Search Engines")
    print("=" * 60)
    server_start_time = datetime.now()
    
    if not check_memory():
        print("❌ Insufficient memory.")
        return False
        
    optimize_memory()
    
    try:
        # Load shared model first
        print("🚀 Loading shared LaBSE model...")
        ModelManager.get_model()  # Initialize shared model
        
        print("🚀 Creating Ayurvedic search engine instance...")
        ayurvedic_engine = AyurvedicSearch()
        if not ayurvedic_engine.load_components():
            print("❌ Failed to load Ayurvedic search engine components")
            return False
            
        print("🚀 Creating ICD-11 search engine instance...")
        icd_engine = ICD11Search()
        if not icd_engine.load_components():
            print("❌ Failed to load ICD-11 search engine components")
            return False
            
        print("✅ Both search engines ready!")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing engines: {str(e)}")
        return False

@app.route('/')
def home():
    memory = psutil.virtual_memory()
    return {
        "message": "🌿 Namaste Search API (Ayurvedic + ICD-11)",
        "status": {
            "ayurvedic": "ready" if ayurvedic_engine and getattr(ayurvedic_engine, "is_ready", True) else "initializing",
            "icd11": "ready" if icd_engine and getattr(icd_engine, "model", None) else "initializing"
        },
        "models": {
            "ayurvedic": "sentence-transformers/LaBSE",
            "icd11": "sentence-transformers/LaBSE"
        },
        "memory_usage": f"{memory.percent}%",
        "available_memory": f"{memory.available / (1024**3):.1f} GB",
        "endpoints": {
            "search_ayurvedic": "/search_ayurvedic?q=query&k=5",
            "search_icd": "/search_icd?q=query&k=5",
            "map": "/map (POST: {'query': 'your text'})",
            "health": "/health",
            "memory": "/memory"
        }
    }

@app.route('/health')
def health():
    memory = psutil.virtual_memory()
    uptime = (datetime.now() - server_start_time).total_seconds() if server_start_time else 0
    return jsonify({
        "status": {
            "ayurvedic": "healthy" if ayurvedic_engine and getattr(ayurvedic_engine, "is_ready", True) else "unhealthy",
            "icd11": "healthy" if icd_engine and getattr(icd_engine, "model", None) else "unhealthy"
        },
        "uptime_seconds": uptime,
        "memory_percent": memory.percent,
        "available_gb": round(memory.available / (1024**3), 1),
        "ayurvedic_vectors": ayurvedic_engine.index.ntotal if ayurvedic_engine and hasattr(ayurvedic_engine, "index") else 0,
        "icd11_vectors": icd_engine.index.ntotal if icd_engine and hasattr(icd_engine, "index") else 0
    })

@app.route('/memory')
def memory_status():
    memory = psutil.virtual_memory()
    return jsonify({
        "total_gb": round(memory.total / (1024**3), 1),
        "available_gb": round(memory.available / (1024**3), 1),
        "used_gb": round(memory.used / (1024**3), 1),
        "percent_used": memory.percent,
        "ayurvedic_loaded": ayurvedic_engine is not None and getattr(ayurvedic_engine, "is_ready", True),
        "icd11_loaded": icd_engine is not None and getattr(icd_engine, "model", None)
    })

@app.route('/search_ayurvedic')
def search_ayurvedic():
    global ayurvedic_engine
    if not ayurvedic_engine or not getattr(ayurvedic_engine, "is_ready", True):
        return jsonify({"success": False, "error": "Ayurvedic search engine not ready"}), 503
    query = request.args.get('q', '').strip()
    k = min(int(request.args.get('k', 5)), 50)
    if not query:
        return jsonify({"success": False, "error": "Query parameter 'q' is required"}), 400
    try:
        memory_before = psutil.virtual_memory().percent
        results = ayurvedic_engine.intelligent_search(query, k=k, return_scores=True)
        memory_after = psutil.virtual_memory().percent
        results["memory_info"] = {
            "memory_before": memory_before,
            "memory_after": memory_after,
            "memory_delta": memory_after - memory_before
        }
        return jsonify(results)
    except Exception as e:
        return jsonify({"success": False, "error": f"Search failed: {str(e)}"}), 500

@app.route('/search_icd')
def search_icd():
    global icd_engine
    if not icd_engine or not getattr(icd_engine, "model", None):
        return jsonify({"success": False, "error": "ICD-11 search engine not ready"}), 503
    query = request.args.get('q', '').strip()
    k = min(int(request.args.get('k', 5)), 50)
    if not query:
        return jsonify({"success": False, "error": "Query parameter 'q' is required"}), 400
    try:
        memory_before = psutil.virtual_memory().percent
        results = icd_engine.search(query, k=k, return_scores=True)
        memory_after = psutil.virtual_memory().percent
        results["memory_info"] = {
            "memory_before": memory_before,
            "memory_after": memory_after,
            "memory_delta": memory_after - memory_before
        }
        return jsonify(results)
    except Exception as e:
        return jsonify({"success": False, "error": f"Search failed: {str(e)}"}), 500

@app.route("/map", methods=["GET"])
def map_query():
    global ayurvedic_engine
    query = request.args.get("query", "").strip()
    k = min(int(request.args.get("k", 5)), 50)
    ann_k = min(int(request.args.get("ann_k", 50)), 200)

    if not query:
        return jsonify({"success": False, "error": "Query text required"}), 400

    try:
        # ICD-11 results using imported function (runs FAISS + re-ranking from icd11_namaste_mapping)
        try:
            ayurvedic_results = ayurvedic_engine.intelligent_search(query, k=k, return_scores=True)

            # Extract Long_definition from the first result, fallback to original query if not found
            long_definition = None
            if (
                ayurvedic_results.get("results") and
                isinstance(ayurvedic_results["results"], list) and
                len(ayurvedic_results["results"]) > 0 and
                "data" in ayurvedic_results["results"][0] and
                "Long_definition" in ayurvedic_results["results"][0]["data"]
            ):
                long_definition = ayurvedic_results["results"][0]["data"]["Long_definition"]
            else:
                long_definition = query

            icd_results = map_icd(long_definition, ann_top_k=ann_k, final_top_k=k)
        except Exception as e:
            icd_results = {"success": False, "error": f"ICD search failed: {str(e)}"}

        return jsonify({
            "success": True,
            "namaste_code": query,
            "ayurvedic_results": long_definition,
            "k": k,
            "ann_k": ann_k,
            "icd11_results": icd_results
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/chatbot", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                "success": False,
                "error": "Query is required in the request body"
            }), 400

        print(data['query'])
        print(data['history'])
        user_message = data['query']

        # Get conversation history if provided (may contain role/content dicts from frontend)
        chat_history = data.get('history', [])

        # Normalize history into plain text to avoid SDK schema mismatch
        def _normalize_history(history_list):
            turns = []
            for item in history_list:
                # item might be a simple string
                if isinstance(item, str):
                    turns.append(item)
                    continue

                # item might be a dict with role/content
                if isinstance(item, dict):
                    role = item.get('role', 'user')
                    content = item.get('content', '')

                    # content may itself be a dict or list depending on frontend shape
                    text = ''
                    if isinstance(content, str):
                        text = content
                    elif isinstance(content, dict):
                        # try common shapes: {'text': '...'} or {'parts': ['...']}
                        if 'text' in content:
                            text = content.get('text', '')
                        elif 'parts' in content and isinstance(content['parts'], list):
                            parts = []
                            for p in content['parts']:
                                if isinstance(p, str):
                                    parts.append(p)
                                elif isinstance(p, dict):
                                    parts.append(p.get('text', ''))
                            text = ' '.join(parts)
                        else:
                            # fallback to stringifying
                            text = str(content)
                    elif isinstance(content, list):
                        parts = []
                        for c in content:
                            if isinstance(c, str):
                                parts.append(c)
                            elif isinstance(c, dict):
                                parts.append(c.get('text', '') or str(c))
                        text = ' '.join(parts)
                    else:
                        text = str(content)

                    label = 'User' if str(role).lower().startswith('user') else 'Assistant' if str(role).lower().startswith('assistant') else str(role)
                    turns.append(f"{label}: {text}")
                else:
                    # unknown shape, stringify
                    turns.append(str(item))

            return '\n'.join([t for t in turns if t.strip()])

        history_text = _normalize_history(chat_history)

        # Start a new chat WITHOUT passing raw history to the SDK to avoid schema errors
        chat = chat_model.start_chat()

        # Build a plain-text prompt that includes the system prompt and (optionally) prior conversation
        if history_text:
            combined_message = f"{SYSTEM_PROMPT}\n\nConversation so far:\n{history_text}\n\nUser: {user_message}\nAssistant:"
        else:
            combined_message = f"{SYSTEM_PROMPT}\n\nUser question: {user_message}\nResponse:"

        # Generate response
        response = chat.send_message(combined_message)
        # Extract the response text
        response_text = response.text
        
        # If this is a non-medical query, the model should have detected it based on the system prompt
        # and responded with the standard message. No need for additional filtering.
        
        # Update conversation history and serialize SDK objects into JSON-safe dicts
        def _serialize_sdk_history(sdk_history):
            serialized = []
            for item in sdk_history:
                try:
                    # role may be 'role' or 'author' on different SDK versions
                    role = getattr(item, 'role', None) or getattr(item, 'author', None) or 'assistant'
                    content = getattr(item, 'content', None)

                    text = ''
                    if content is None:
                        text = str(item)
                    else:
                        # content may be a simple string
                        if isinstance(content, str):
                            text = content
                        # content may have a .text attribute
                        elif hasattr(content, 'text'):
                            text = getattr(content, 'text') or ''
                        # content may have .parts (list)
                        elif hasattr(content, 'parts') and getattr(content, 'parts'):
                            parts = []
                            for p in getattr(content, 'parts'):
                                if isinstance(p, str):
                                    parts.append(p)
                                elif hasattr(p, 'text'):
                                    parts.append(getattr(p, 'text') or '')
                                elif isinstance(p, dict):
                                    parts.append(p.get('text', ''))
                                else:
                                    parts.append(str(p))
                            text = ' '.join([t for t in parts if t])
                        # content may be a dict-like
                        elif isinstance(content, dict):
                            if 'text' in content:
                                text = content.get('text', '')
                            elif 'parts' in content and isinstance(content['parts'], list):
                                parts = []
                                for p in content['parts']:
                                    if isinstance(p, str):
                                        parts.append(p)
                                    elif isinstance(p, dict):
                                        parts.append(p.get('text', ''))
                                text = ' '.join([t for t in parts if t])
                            else:
                                text = str(content)
                        else:
                            text = str(content)
                except Exception:
                    role = 'assistant'
                    text = str(item)

                serialized.append({
                    'role': role,
                    'text': text
                })
            return serialized

        serialized_history = _serialize_sdk_history(chat.history)

        return jsonify({
            "success": True,
            "response": response_text,
            "history": serialized_history
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Chat failed: {str(e)}"
        }), 500

if __name__ == '__main__':
    print("🌿 Namaste Search API Server (Ayurvedic + ICD-11)")
    print("=" * 60)
    try:
        import psutil
    except ImportError:
        print("Installing psutil for memory monitoring...")
        os.system("pip install psutil")
        import psutil
    if initialize_search_engines():
        print("\n🌐 Starting Flask server...")
        print("📡 API available at: http://localhost:5000")
        print("💾 Memory monitoring enabled")
        print("🔍 Both models loaded successfully")
        print("\n💡 Press Ctrl+C to stop")
        print("=" * 60)
        try:
            app.run(host='127.0.0.1', port=5000, debug=False)
        except KeyboardInterrupt:
            print("\n👋 Server stopped")
    else:
        print("\n❌ Failed to start server")
        print("\n🔧 To fix memory issues:")
        print("   1. Increase Windows virtual memory to 16GB")
        print("   2. Restart your computer")
        print("   3. Close other applications")