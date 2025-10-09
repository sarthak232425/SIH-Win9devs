#!/usr/bin/env python3
"""
ICD-11 Medical Code Search API Server
=====================================

Flask API server for the ICD-11 semantic search engine using
LaBSE embeddings and FAISS indexing.

Usage:
    python flask_api.py

Endpoints:
    GET  /                     - API status and documentation
    GET  /health               - Health check
    GET  /search?q=query&k=5   - Search ICD-11 codes
    POST /batch_search         - Batch search multiple queries
    GET  /stats                - Search engine statistics
"""

import os
import warnings
import sys

# Environment setup BEFORE any ML imports
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['USE_TF'] = 'False'
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
os.environ['TRANSFORMERS_NO_ADVISORY_WARNINGS'] = '1'
warnings.filterwarnings('ignore')

# Suppress specific TensorFlow warnings
warnings.filterwarnings('ignore', category=UserWarning, module='google.protobuf')
warnings.filterwarnings('ignore', category=FutureWarning, module='transformers')

try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    import json
    from datetime import datetime
    
    print("✅ Flask imported successfully")
    
    # Try to import search engine with error handling
    try:
        from icd11_search.src.search import ICD11Search
        print("✅ ICD-11 Search engine imported successfully")
    except Exception as e:
        print(f"❌ Failed to import search engine: {e}")
        print("🔧 Make sure search.py exists and dependencies are installed")
        sys.exit(1)
    
except ImportError as e:
    print(f"❌ Failed to import Flask dependencies: {e}")
    print("🔧 Run: pip install flask flask-cors")
    sys.exit(1)

app = Flask(__name__)
CORS(app)

# Global variables
search_engine = None
server_start_time = None


def initialize_search_engine():
    """Initialize the search engine with error handling."""
    global search_engine, server_start_time
    
    print("🚀 Initializing ICD-11 Search Engine...")
    server_start_time = datetime.now()
    
    try:
        search_engine = ICD11Search()
        if search_engine.load_components():
            print("✅ Search engine ready for API requests!")
            return True
        else:
            print("❌ Search engine failed to load components")
            return False
    except Exception as e:
        print(f"❌ Error initializing search engine: {str(e)}")
        return False


@app.route('/')
def home():
    """API documentation and status page."""
    return jsonify({
        "message": "🏥 ICD-11 Medical Code Search API is running!",
        "status": "healthy" if search_engine else "initializing",
        "version": "1.0.0",
        "endpoints": {
            "search": {
                "url": "/search",
                "method": "GET",
                "parameters": {
                    "q": "Search query (required)",
                    "k": "Number of results (optional, default: 5, max: 50)"
                }
            },
            "batch_search": {
                "url": "/batch_search",
                "method": "POST",
                "body": {
                    "queries": ["query1", "query2", "..."],
                    "k": "Number of results per query (optional)"
                }
            },
            "health": {
                "url": "/health",
                "method": "GET",
                "description": "Health check endpoint"
            },
            "stats": {
                "url": "/stats",
                "method": "GET",
                "description": "Search engine statistics"
            }
        },
        "examples": {
            "digestive_search": "/search?q=digestive power&k=5",
            "sweat_pattern": "/search?q=sweat pattern",
            "code_search": "/search?q=SR8C",
            "sputum_search": "/search?q=sputum excess&k=10"
        }
    })


@app.route('/health')
def health():
    """Health check endpoint."""
    global search_engine, server_start_time
    
    if search_engine and hasattr(search_engine, 'model') and search_engine.model:
        uptime = (datetime.now() - server_start_time).total_seconds() if server_start_time else 0
        return jsonify({
            "status": "healthy",
            "search_engine": "ready",
            "total_vectors": search_engine.index.ntotal if search_engine.index else 0,
            "embedding_dimension": search_engine.index.d if search_engine.index else 0,
            "uptime_seconds": round(uptime, 2),
            "timestamp": datetime.now().isoformat()
        })
    else:
        return jsonify({
            "status": "unhealthy",
            "search_engine": "not ready",
            "timestamp": datetime.now().isoformat()
        }), 503


@app.route('/search', methods=['GET'])
def search():
    """Main search endpoint for ICD-11 codes."""
    global search_engine
    
    if not search_engine or not hasattr(search_engine, 'model') or not search_engine.model:
        return jsonify({
            "success": False,
            "error": "Search engine not ready. Please wait for initialization to complete."
        }), 503
    
    query = request.args.get('q', '').strip()
    k = request.args.get('k', '5')
    
    if not query:
        return jsonify({
            "success": False,
            "error": "Query parameter 'q' is required",
            "example": "/search?q=digestive power&k=5"
        }), 400
    
    try:
        k = int(k)
        if k < 1 or k > 50:
            return jsonify({
                "success": False,
                "error": "Parameter 'k' must be between 1 and 50"
            }), 400
    except ValueError:
        return jsonify({
            "success": False,
            "error": "Parameter 'k' must be a valid integer"
        }), 400
    
    try:
        # Perform the search
        results = search_engine.search(query, k=k, return_scores=True)
        
        # Add query metadata
        results["query_metadata"] = {
            "original_query": query,
            "query_length": len(query),
            "word_count": len(query.split()),
            "requested_results": k,
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify(results)
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Search failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500


@app.route('/batch_search', methods=['POST'])
def batch_search():
    """Batch search endpoint for multiple queries."""
    global search_engine
    
    if not search_engine or not hasattr(search_engine, 'model') or not search_engine.model:
        return jsonify({
            "success": False,
            "error": "Search engine not ready"
        }), 503
    
    try:
        data = request.get_json()
        
        if not data or 'queries' not in data:
            return jsonify({
                "success": False,
                "error": "Request body must contain 'queries' array",
                "example": {"queries": ["digestive power", "sweat pattern"], "k": 5}
            }), 400
        
        queries = data.get('queries', [])
        k = data.get('k', 5)
        
        if not isinstance(queries, list) or len(queries) == 0:
            return jsonify({
                "success": False,
                "error": "Queries must be a non-empty array"
            }), 400
        
        if len(queries) > 20:
            return jsonify({
                "success": False,
                "error": "Maximum 20 queries allowed per batch request"
            }), 400
        
        try:
            k = int(k)
            if k < 1 or k > 50:
                return jsonify({
                    "success": False,
                    "error": "Parameter 'k' must be between 1 and 50"
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                "error": "Parameter 'k' must be a valid integer"
            }), 400
        
        # Perform batch search
        batch_results = search_engine.batch_search(queries, k=k)
        
        return jsonify({
            "success": True,
            "batch_metadata": {
                "total_queries": len(queries),
                "results_per_query": k,
                "timestamp": datetime.now().isoformat()
            },
            "results": batch_results
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Batch search failed: {str(e)}"
        }), 500


@app.route('/stats')
def stats():
    """Get search engine statistics."""
    global search_engine
    
    if not search_engine or not hasattr(search_engine, 'model') or not search_engine.model:
        return jsonify({
            "error": "Search engine not ready"
        }), 503
    
    try:
        # Get dataset statistics
        dataset_stats = {}
        if hasattr(search_engine, 'data') and search_engine.data is not None:
            dataset_stats = {
                "total_codes": len(search_engine.data),
                "columns": list(search_engine.data.columns),
                "sample_codes": search_engine.data['code'].head(5).tolist() if 'code' in search_engine.data.columns else []
            }
        
        # Get index statistics
        index_stats = {}
        if hasattr(search_engine, 'index') and search_engine.index:
            index_stats = {
                "total_vectors": search_engine.index.ntotal,
                "embedding_dimension": search_engine.index.d,
                "index_type": type(search_engine.index).__name__
            }
        
        return jsonify({
            "dataset_info": dataset_stats,
            "index_info": index_stats,
            "model_info": {
                "model_name": "sentence-transformers/LaBSE",
                "embedding_type": "multilingual"
            },
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            "error": f"Failed to get stats: {str(e)}"
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": ["/", "/health", "/search", "/batch_search", "/stats"]
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        "error": "Internal server error",
        "message": "Please check the server logs for details"
    }), 500


def print_startup_info():
    """Print startup information and examples."""
    print("\n" + "=" * 60)
    print("🏥 ICD-11 Medical Code Search API Server")
    print("=" * 60)
    print("\n📡 API Endpoints:")
    print("   • GET  /                     - API documentation")
    print("   • GET  /health               - Health check")
    print("   • GET  /search?q=query&k=5   - Search ICD-11 codes")
    print("   • POST /batch_search         - Batch search")
    print("   • GET  /stats                - Statistics")
    
    print("\n💡 Example Usage:")
    print("   • http://localhost:5000/search?q=digestive power")
    print("   • http://localhost:5000/search?q=sweat pattern&k=10")
    print("   • http://localhost:5000/search?q=SR8C")
    
    print("\n📝 Batch Search Example:")
    print("   POST /batch_search")
    print("   {\"queries\": [\"digestive power\", \"sweat pattern\"], \"k\": 5}")
    
    print("\n🌐 API available at: http://localhost:5000")
    print("💡 Press Ctrl+C to stop")
    print("=" * 60)


if __name__ == '__main__':
    print("🏥 ICD-11 Medical Code Search API Server")
    print("=" * 60)
    
    if initialize_search_engine():
        print_startup_info()
        
        try:
            app.run(
                host='0.0.0.0', 
                port=5000, 
                debug=False,
                threaded=True,
                use_reloader=False
            )
        except KeyboardInterrupt:
            print("\n\n👋 Server stopped by user")
            print("Thank you for using ICD-11 Search API!")
        except Exception as e:
            print(f"\n❌ Server error: {str(e)}")
    else:
        print("❌ Failed to start server - search engine initialization failed")
        print("🔧 Please ensure:")
        print("   1. icd11_clean.csv exists in the current directory")
        print("   2. Run 'python main.py --setup' first")
        print("   3. All dependencies are installed")
        sys.exit(1)
