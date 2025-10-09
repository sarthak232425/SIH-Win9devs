#!/usr/bin/env python3
"""
Ayurvedic NAMASTE Code Search Engine - Main Application
=====================================================

This is the main entry point for the Ayurvedic search engine that uses
LaBSE embeddings and FAISS indexing for semantic search.

Usage:
    python main.py --help                    # Show help
    python main.py --setup                   # Setup the entire pipeline
    python main.py --search                  # Interactive search
    python main.py --api                     # API mode for web integration
    python main.py --query "search term"     # Single query search
"""


# Suppress TensorFlow warnings and force PyTorch backend
import os
import warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TF warnings
os.environ['USE_TF'] = 'False'  # Force PyTorch backend
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
warnings.filterwarnings('ignore')

# Rest of your imports...
import argparse
import json
import sys
from datetime import datetime

# Import all our modules
from data_loader import load_and_preprocess_data
from embedder import generate_and_save_embeddings, load_embeddings
from indexer import build_and_save_index, get_index_info
from search import AyurvedicSearch, search_interactive, search_api

def print_banner():
    """Print the application banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║              🌿 Ayurvedic NAMASTE Search Engine 🌿           ║
    ║                                                              ║
    ║        Semantic Search for Ayurvedic Medical Codes           ║
    ║           Using LaBSE Embeddings + FAISS Index              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_system_status():
    """
    Check the status of all system components.
    
    Returns:
        dict: Status of each component
    """
    base_dir = os.path.dirname(__file__)
    
    status = {
        'data_file': False,
        'embeddings': False,
        'index': False,
        'ready_for_search': False
    }
    
    # Check data file
    data_path = os.path.join(base_dir, '..', 'data', 'NAMASTE_CODE.csv')
    status['data_file'] = os.path.exists(data_path)
    
    # Check embeddings
    embeddings_path = os.path.join(base_dir, '..', 'embeddings', 'text_embeddings.npy')
    status['embeddings'] = os.path.exists(embeddings_path)
    
    # Check FAISS index
    index_path = os.path.join(base_dir, '..', 'index', 'faiss_index.bin')
    status['index'] = os.path.exists(index_path)
    
    # Overall readiness
    status['ready_for_search'] = all([status['data_file'], status['embeddings'], status['index']])
    
    return status

def print_status():
    """Print the current system status."""
    print("\n📊 System Status:")
    print("=" * 50)
    
    status = check_system_status()
    
    components = [
        ('Data File (NAMASTE_CODE.csv)', status['data_file']),
        ('Embeddings (text_embeddings.npy)', status['embeddings']),
        ('FAISS Index (faiss_index.bin)', status['index']),
    ]
    
    for component, exists in components:
        status_icon = "✅" if exists else "❌"
        print(f"{status_icon} {component}")
    
    print("-" * 50)
    overall_status = "✅ Ready for Search" if status['ready_for_search'] else "❌ Setup Required"
    print(f"Overall Status: {overall_status}")
    
    if status['ready_for_search']:
        # Show additional info if everything is ready
        try:
            index_info = get_index_info()
            if index_info:
                print(f"\n📈 Index Statistics:")
                print(f"   • Total vectors: {index_info['total_vectors']:,}")
                print(f"   • Embedding dimension: {index_info['dimension']}")
                print(f"   • Index size: {index_info['file_size_mb']:.2f} MB")
        except:
            pass
    
    return status

def setup_pipeline(force_rebuild=False):
    """
    Set up the entire search pipeline.
    
    Args:
        force_rebuild (bool): Whether to force rebuild existing components
        
    Returns:
        bool: True if setup completed successfully
    """
    print("\n🚀 Setting up Ayurvedic Search Engine Pipeline")
    print("=" * 55)
    
    try:
        # Step 1: Check data
        print("\n📁 Step 1: Checking data availability...")
        df = load_and_preprocess_data()
        if df is None:
            print("❌ Data loading failed. Please ensure NAMASTE_CODE.csv exists in the data folder.")
            return False
        print(f"✅ Data loaded successfully: {len(df)} records")
        
        # Step 2: Generate embeddings
        print("\n🧠 Step 2: Generating embeddings...")
        if not generate_and_save_embeddings():
            print("❌ Embedding generation failed.")
            return False
        print("✅ Embeddings generated successfully")
        
        # Step 3: Build FAISS index
        print("\n🔍 Step 3: Building search index...")
        if not build_and_save_index(force_rebuild=force_rebuild):
            print("❌ Index creation failed.")
            return False
        print("✅ Search index built successfully")
        
        # Step 4: Verify setup
        print("\n✅ Step 4: Verifying setup...")
        search_engine = AyurvedicSearch()
        if search_engine.load_components():
            print("✅ All components verified successfully")
            print("\n🎉 Setup Complete! The search engine is ready to use.")
            return True
        else:
            print("❌ Setup verification failed")
            return False
            
    except Exception as e:
        print(f"❌ Setup failed with error: {str(e)}")
        return False

def single_query_search(query, k=5, format_output='pretty'):
    """
    Perform a single search query.
    
    Args:
        query (str): The search query
        k (int): Number of results to return
        format_output (str): Output format ('pretty', 'json')
        
    Returns:
        bool: True if search was successful
    """
    if format_output == 'json':
        # API-style JSON output
        result = search_api(query, k=k)
        print(result)
        return True
    
    # Pretty formatted output
    print(f"\n🔍 Searching for: '{query}'")
    print("=" * 60)
    
    search_engine = AyurvedicSearch()
    if not search_engine.load_components():
        print("❌ Failed to initialize search engine")
        return False
    
    results = search_engine.search(query, k=k, return_scores=True)
    
    if results["success"]:
        print(f"✅ Found {results['total_results']} results:\n")
        
        for result in results["results"]:
            data = result["data"]
            score = result.get("similarity_score", 0)
            
            print(f"🏥 Rank {result['rank']} (Similarity: {score:.4f})")
            print("-" * 50)
            
            # Display key fields
            if 'NAMASTE_code' in data:
                print(f"Code: {data['NAMASTE_code']}")
            
            if 'Long_definition' in data:
                definition = data['Long_definition']
                if len(definition) > 200:
                    definition = definition[:200] + "..."
                print(f"Definition: {definition}")
            
            # Show other available fields (first few)
            other_fields = [k for k in data.keys() if k not in ['NAMASTE_code', 'Long_definition']][:3]
            for field in other_fields:
                value = str(data[field])
                if len(value) > 100:
                    value = value[:100] + "..."
                print(f"{field}: {value}")
            
            print("\n")
        
        return True
    else:
        print(f"❌ Search failed: {results['error']}")
        return False

def api_mode():
    """
    Run the application in API mode for web integration.
    This provides a simple command-line API interface.
    """
    print("\n🌐 API Mode - Ready for web integration")
    print("=" * 50)
    print("Usage: Send queries via stdin, get JSON responses via stdout")
    print("Type 'quit' to exit")
    print("-" * 50)
    
    search_engine = AyurvedicSearch()
    if not search_engine.load_components():
        error_response = {
            "success": False,
            "error": "Failed to initialize search engine",
            "results": []
        }
        print(json.dumps(error_response))
        return False
    
    try:
        while True:
            line = input().strip()
            if line.lower() in ['quit', 'exit']:
                break
            
            if line:
                results = search_engine.search(line, k=5, return_scores=True)
                print(json.dumps(results, ensure_ascii=False))
    except (EOFError, KeyboardInterrupt):
        pass
    
    return True

def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description="Ayurvedic NAMASTE Code Search Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --setup                    # Set up the search engine
  python main.py --search                   # Interactive search mode
  python main.py --query "fever treatment"  # Single query search
  python main.py --status                   # Check system status
  python main.py --api                      # API mode for web integration
        """
    )
    
    parser.add_argument('--setup', action='store_true', 
                       help='Set up the entire search pipeline')
    parser.add_argument('--search', action='store_true', 
                       help='Start interactive search mode')
    parser.add_argument('--query', type=str, 
                       help='Perform a single search query')
    parser.add_argument('--status', action='store_true', 
                       help='Check system status')
    parser.add_argument('--api', action='store_true', 
                       help='Run in API mode for web integration')
    parser.add_argument('--force-rebuild', action='store_true', 
                       help='Force rebuild of embeddings and index')
    parser.add_argument('--json', action='store_true', 
                       help='Output results in JSON format')
    parser.add_argument('-k', '--top-k', type=int, default=5, 
                       help='Number of results to return (default: 5)')
    
    args = parser.parse_args()
    
    # Show banner
    print_banner()
    
    # If no arguments provided, show status and help
    if not any(vars(args).values()):
        print_status()
        print("\n💡 Tip: Use --help to see all available options")
        print("💡 Tip: Use --setup to initialize the search engine")
        return
    
    # Handle different modes
    if args.status:
        status = print_status()
        if not status['ready_for_search']:
            print("\n💡 Run 'python main.py --setup' to initialize the system")
    
    elif args.setup:
        success = setup_pipeline(force_rebuild=args.force_rebuild)
        if success:
            print("\n💡 Now you can use 'python main.py --search' for interactive search")
        sys.exit(0 if success else 1)
    
    elif args.search:
        status = check_system_status()
        if not status['ready_for_search']:
            print("❌ System not ready. Please run --setup first.")
            sys.exit(1)
        search_interactive()
    
    elif args.query:
        status = check_system_status()
        if not status['ready_for_search']:
            print("❌ System not ready. Please run --setup first.")
            sys.exit(1)
        
        output_format = 'json' if args.json else 'pretty'
        success = single_query_search(args.query, k=args.top_k, format_output=output_format)
        sys.exit(0 if success else 1)
    
    elif args.api:
        status = check_system_status()
        if not status['ready_for_search']:
            error_response = {
                "success": False,
                "error": "System not ready. Please run setup first.",
                "results": []
            }
            print(json.dumps(error_response))
            sys.exit(1)
        api_mode()

if __name__ == '__main__':
    main()
