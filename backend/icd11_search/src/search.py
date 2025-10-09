import numpy as np
import faiss
import json
from icd11_search.src.data_loader import load_and_preprocess_data, get_row_data_by_indices
from icd11_search.src.embedder import load_embedding_model
from icd11_search.src.indexer import load_faiss_index

from model_manager import ModelManager

class ICD11Search:
    """
    ICD-11 Semantic Search Engine using LaBSE embeddings and FAISS indexing.
    """
    
    def __init__(self):
        self.model = None
        self.index = None
        self.data = None
        
    def load_components(self):
        """
        Load all required components for search.
        
        Returns:
            bool: True if all components loaded successfully
        """
        try:
            # Use shared model instead of loading new one
            print("📎 Getting shared LaBSE model instance...")
            self.model = ModelManager.get_model()
            
            # Load the FAISS index
            print("Loading FAISS index...")
            index_path = "icd11_search/index/icd11_faiss_index.bin"
            self.index = load_faiss_index(index_path)
            if self.index is None:
                print("Failed to load FAISS index")
                return False
                
            # Load the original data
            print("Loading original data...")
            self.data = load_and_preprocess_data()
            if self.data is None:
                print("Failed to load original data")
                return False
                
            print("All components loaded successfully!")
            return True
            
        except Exception as e:
            print(f"Error loading components: {str(e)}")
            return False
    
    def search(self, query, k=5, return_scores=False):
        """
        Perform semantic search for the given query.
        
        Args:
            query (str): The search query
            k (int): Number of results to return
            return_scores (bool): Whether to include similarity scores
            
        Returns:
            dict: Search results with success status and results list
        """
        if not all([self.model, self.index, self.data is not None]):
            return {
                "success": False,
                "error": "Search components not properly loaded",
                "results": []
            }
        
        try:
            # Generate embedding for the query
            query_embedding = self.model.encode(
                [query],
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            
            # Perform search using FAISS
            scores, indices = self.index.search(query_embedding.astype(np.float32), k)
            
            # Prepare results
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx != -1:  # Valid result
                    # Get the original data for this index
                    row_data = get_row_data_by_indices(self.data, [idx])[0]
                    
                    result = {
                        "rank": i + 1,
                        "index": int(idx),
                        "data": row_data
                    }
                    
                    if return_scores:
                        result["similarity_score"] = float(score)
                    
                    results.append(result)
            
            return {
                "success": True,
                "query": query,
                "total_results": len(results),
                "results": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Search error: {str(e)}",
                "results": []
            }
    
    def batch_search(self, queries, k=5):
        """
        Perform batch search for multiple queries.
        
        Args:
            queries (list): List of search queries
            k (int): Number of results per query
            
        Returns:
            dict: Batch search results
        """
        batch_results = {}
        
        for query in queries:
            batch_results[query] = self.search(query, k=k, return_scores=True)
        
        return batch_results


def search_interactive():
    """
    Interactive search mode for testing.
    """
    print("\n🔍 ICD-11 Interactive Search Mode")
    print("=" * 50)
    print("Type your medical queries to search ICD-11 codes")
    print("Type 'quit' or 'exit' to stop")
    print("-" * 50)
    
    # Initialize search engine
    search_engine = ICD11Search()
    if not search_engine.load_components():
        print("❌ Failed to initialize search engine")
        return False
    
    print("✅ Search engine ready!")
    print("\nEnter your search queries:\n")
    
    try:
        while True:
            query = input("🔍 Search: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not query:
                continue
            
            print(f"\nSearching for: '{query}'...")
            results = search_engine.search(query, k=5, return_scores=True)
            
            if results["success"]:
                print(f"✅ Found {results['total_results']} results:\n")
                
                for result in results["results"]:
                    data = result["data"]
                    score = result.get("similarity_score", 0)
                    
                    print(f"🏥 Rank {result['rank']} (Similarity: {score:.4f})")
                    print(f"   Code: {data['code']}")
                    print(f"   Title: {data['title']}")
                    print()
            else:
                print(f"❌ Search failed: {results['error']}")
            
            print("-" * 50)
    
    except KeyboardInterrupt:
        print("\n👋 Search interrupted. Goodbye!")
    
    return True


def search_api(query, k=5):
    """
    API-style search function that returns JSON.
    
    Args:
        query (str): Search query
        k (int): Number of results
        
    Returns:
        str: JSON string with results
    """
    search_engine = ICD11Search()
    if not search_engine.load_components():
        return json.dumps({
            "success": False,
            "error": "Failed to initialize search engine",
            "results": []
        })
    
    results = search_engine.search(query, k=k, return_scores=True)
    return json.dumps(results, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    # Test the search functionality
    print("Testing ICD-11 Search Engine...")
    
    # Test search
    search_engine = ICD11Search()
    
    if search_engine.load_components():
        print("\n=== Testing Search ===")
        
        # Test queries
        test_queries = [
            "digestive system",
            "sweat pattern",
            "elevated digestive power",
            "sputum",
            "convalescence"
        ]
        
        for query in test_queries:
            print(f"\nTesting query: '{query}'")
            results = search_engine.search(query, k=3, return_scores=True)
            
            if results["success"]:
                print(f"✅ Found {results['total_results']} results")
                for result in results["results"][:2]:  # Show first 2 results
                    data = result["data"]
                    score = result.get("similarity_score", 0)
                    print(f"   {result['rank']}. {data['code']}: {data['title'][:60]}... (Score: {score:.4f})")
            else:
                print(f"❌ Search failed: {results['error']}")
        
        print("\n✅ Search testing completed!")
        
        # Start interactive mode
        print("\nStarting interactive search mode...")
        search_interactive()
    else:
        print("❌ Failed to load search components")
