import os
import warnings
import sys
import gc
import psutil

# Memory optimization environment variables
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['USE_TF'] = 'False'
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
warnings.filterwarnings('ignore')

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from datetime import datetime
import requests

app = Flask(__name__)
CORS(app)

# Global variables
search_engine = None
server_start_time = None

def check_memory():
    """Check available memory before loading model."""
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
    """Optimize memory before loading large model."""
    print("🧹 Optimizing memory...")
    
    # Force garbage collection
    gc.collect()
    
    # Set environment for memory efficiency
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['MKL_NUM_THREADS'] = '1'
    
    print("✅ Memory optimization complete")

def initialize_search_engine():
    """Initialize search engine with LaBSE model and memory management."""
    global search_engine, server_start_time
    
    print("🌿 Initializing Ayurvedic Search Engine with LaBSE")
    print("=" * 60)
    
    server_start_time = datetime.now()
    
    # Check available memory
    if not check_memory():
        print("❌ Insufficient memory. Please:")
        print("   1. Close other applications")
        print("   2. Increase virtual memory (paging file)")
        print("   3. Restart your computer")
        return False
    
    # Optimize memory
    optimize_memory()
    
    try:
        # Import search engine
        print("📦 Importing search engine module...")
        from search import AyurvedicSearch
        
        # Initialize search engine
        print("🚀 Creating search engine instance...")
        search_engine = AyurvedicSearch()
        
        # Load components with progress tracking
        print("📚 Loading search engine components...")
        print("   This may take 2-5 minutes for LaBSE model...")
        
        if search_engine.load_components():
            print("✅ LaBSE search engine ready!")
            
            # Memory status after loading
            memory = psutil.virtual_memory()
            print(f"💾 Memory after loading: {memory.percent}% used")
            
            return True
        else:
            print("❌ Failed to load search engine components")
            return False
            
    except MemoryError as e:
        print(f"❌ Memory Error: {str(e)}")
        print("🔧 Solutions:")
        print("   1. Increase virtual memory to 16GB")
        print("   2. Restart computer after changing virtual memory")
        print("   3. Close other memory-intensive applications")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

@app.route('/')
def home():
    """API documentation and status."""
    memory = psutil.virtual_memory()
    
    return {
        "message": "🌿 Ayurvedic Search API with LaBSE",
        "status": "ready" if search_engine and search_engine.is_ready else "initializing",
        "model": "sentence-transformers/LaBSE",
        "memory_usage": f"{memory.percent}%",
        "available_memory": f"{memory.available / (1024**3):.1f} GB",
        "endpoints": {
            "search": "/search?q=query&k=5",
            "health": "/health",
            "memory": "/memory"
        },
        "examples": {
            "code": "/search?q=SR11 (AAA-1)",
            "term": "/search?q=vAtasa~jcayaH",
            "description": "/search?q=fever treatment"
        }
    }

@app.route('/health')
def health():
    """Health check with memory status."""
    if search_engine and search_engine.is_ready:
        memory = psutil.virtual_memory()
        uptime = (datetime.now() - server_start_time).total_seconds() if server_start_time else 0
        
        return jsonify({
            "status": "healthy",
            "model": "LaBSE",
            "uptime_seconds": uptime,
            "memory_percent": memory.percent,
            "available_gb": round(memory.available / (1024**3), 1),
            "total_vectors": search_engine.index.ntotal if search_engine.index else 0
        })
    else:
        return jsonify({
            "status": "unhealthy",
            "error": "Search engine not ready"
        }), 503

@app.route('/memory')
def memory_status():
    """Detailed memory information."""
    memory = psutil.virtual_memory()
    return jsonify({
        "total_gb": round(memory.total / (1024**3), 1),
        "available_gb": round(memory.available / (1024**3), 1),
        "used_gb": round(memory.used / (1024**3), 1),
        "percent_used": memory.percent,
        "search_engine_loaded": search_engine is not None and search_engine.is_ready
    })

@app.route('/search')
def search():
    """Main search endpoint with memory monitoring."""
    global search_engine
    
    if not search_engine or not search_engine.is_ready:
        return jsonify({
            "success": False,
            "error": "Search engine not ready"
        }), 503
    
    query = request.args.get('q', '').strip()
    k = min(int(request.args.get('k', 5)), 50)
    
    if not query:
        return jsonify({
            "success": False,
            "error": "Query parameter 'q' is required"
        }), 400
    
    try:
        # Perform search with memory monitoring
        memory_before = psutil.virtual_memory().percent
        
        results = search_engine.intelligent_search(query, k=k, return_scores=True)
        
        memory_after = psutil.virtual_memory().percent
        
        # Add memory info to response
        results["memory_info"] = {
            "memory_before": memory_before,
            "memory_after": memory_after,
            "memory_delta": memory_after - memory_before
        }
        
        return jsonify(results)
        
    except MemoryError:
        return jsonify({
            "success": False,
            "error": "Insufficient memory for search operation"
        }), 507
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Search failed: {str(e)}"
        }), 500


ICD_SERVER_URL = "http://localhost:5001/search_icd"

@app.route("/map", methods=["POST"])
def map_query():
    data = request.get_json()
    query = data.get("query", "")

    if not query:
        return jsonify({"success": False, "error": "Query text required"}), 400

    # Forward to ICD server
    try:
        response = requests.post(ICD_SERVER_URL, json={"query": query})
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    

# from icd11_namaste_mapping.src.query import search_icd

# @app.route('/query_icd')
# def query_icd():
#     """
#     ICD11 hybrid search endpoint using search_icd from query.py.
#     Example: /query_icd?q=fever&k=5
#     """
#     query = request.args.get('q', '').strip()
#     k = min(int(request.args.get('k', 5)), 50)

#     if not query:
#         return jsonify({
#             "success": False,
#             "error": "Query parameter 'q' is required"
#         }), 400

#     try:
#         results = search_icd(query, ann_top_k=50, final_top_k=k)
#         return jsonify({
#             "success": True,
#             "results": results
#         })
#     except Exception as e:
#         return jsonify({
#             "success": False,
#             "error": f"Search failed: {str(e)}"
#         }), 500
    

if __name__ == '__main__':
    print("🌿 Ayurvedic Search API Server with LaBSE")
    print("=" * 50)
    
    # Check if psutil is available
    try:
        import psutil
    except ImportError:
        print("Installing psutil for memory monitoring...")
        os.system("pip install psutil")
        import psutil
    
    # Initialize search engine
    if initialize_search_engine():
        print("\n🌐 Starting Flask server...")
        print("📡 API available at: http://localhost:5000")
        print("💾 Memory monitoring enabled")
        print("🔍 LaBSE model loaded successfully")
        print("\n💡 Press Ctrl+C to stop")
        print("=" * 50)
        
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
        print("   4. Try running: python flask_server_labse.py")
