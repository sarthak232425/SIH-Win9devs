import numpy as np
import json
import os
import re
import pandas as pd
from namaste_search.src.indexer import load_faiss_index
from namaste_search.src.data_loader import load_and_preprocess_data, get_row_data_by_indices

from model_manager import ModelManager

class AyurvedicSearch:
    """
    A search engine for Ayurvedic NAMASTE codes using LaBSE embeddings and FAISS indexing.
    """
    
    def __init__(self):
        """Initialize the search engine by loading all required components."""
        self.model = None
        self.index = None
        self.dataframe = None
        self.is_ready = False
        
        # Define paths
        self.index_path = os.path.join(os.path.dirname(__file__), '..', 'index', 'faiss_index.bin')
        
    def load_components(self):
        """
        Load all required components: model, FAISS index, and original data.
        
        Returns:
            bool: True if all components loaded successfully, False otherwise
        """
        print("Loading search engine components...")
        
        try:
            # Use shared model instead of loading new one
            print("📎 Getting shared LaBSE model instance...")
            self.model = ModelManager.get_model()
            
            # Rest of loading code remains same
            print("Loading FAISS index...")
            self.index = load_faiss_index(self.index_path)
            if self.index is None:
                print("Failed to load FAISS index")
                return False
                
            print("Loading original dataset...")
            self.dataframe = load_and_preprocess_data()
            if self.dataframe is None:
                print("Failed to load original dataset")
                return False
                
            self.is_ready = True
            print("🚀 Search engine ready!")
            return True
            
        except Exception as e:
            print(f"Error loading components: {str(e)}")
            return False
    
    def detect_query_type(self, query_text):
        """
        Automatically detect if the query is a code, term, or description.
        
        Args:
            query_text (str): The search query
            
        Returns:
            str: 'code', 'term', 'description', or 'multi'
        """
        query = query_text.strip()
        
        # Pattern 1: NAMASTE Code detection (e.g., "SR11 (AAA-1)", "VC-11", "EE-2.4")
        code_patterns = [
            r'^[A-Z]{1,3}[-\d]+\s*\([A-Z]+-\d+\)$',  # SR11 (AAA-1)
            r'^[A-Z]{1,3}-\d+(\.\d+)?$',              # VC-11, EE-2.4
            r'^[A-Z]{1,3}\d+$',                       # SR11
            r'^[A-Z]+-\d+$'                           # K-3
        ]
        
        for pattern in code_patterns:
            if re.match(pattern, query, re.IGNORECASE):
                return "code"
        
        # Pattern 2: Sanskrit/Medical term detection (contains tildes, specific characters)
        term_patterns = [
            r'.*[~āīūṛḷēōṁṃḥ].*',  # Contains Sanskrit diacritics
            r'.*[ḥḷṛ].*',          # Specific Sanskrit characters
            r'^[a-zA-Z]+[-~][a-zA-Z]+',  # Terms with hyphens/tildes
        ]
        
        for pattern in term_patterns:
            if re.match(pattern, query, re.IGNORECASE):
                return "term"
        
        # Pattern 3: Description/symptom detection (multiple words, common medical terms)
        if len(query.split()) >= 2:
            medical_keywords = [
                'characterized by', 'symptoms', 'treatment', 'disorder', 'disease',
                'pain', 'fever', 'inflammation', 'swelling', 'bleeding', 'weakness',
                'abdomen', 'abdominal', 'digestive', 'respiratory', 'cardiac',
                'caused by', 'associated with', 'manifested by'
            ]
            
            query_lower = query.lower()
            if any(keyword in query_lower for keyword in medical_keywords):
                return "description"
        
        # Pattern 4: Single medical terms (but not Sanskrit)
        if len(query.split()) == 1 and not re.match(r'.*[~āīūṛḷēōṁṃḥḥḷṛ].*', query):
            return "term"
        
        return "description"  # Default to description for semantic search

    def search_by_code(self, query_text, k=5):
        """Search specifically in NAMC_CODE field."""
        print("🔍 Searching by NAMASTE code...")
        
        # Check if column exists
        if 'NAMC_CODE' not in self.dataframe.columns:
            print("❌ NAMC_CODE column not found")
            return None
        
        # Try exact and partial matches in code field
        code_matches = self.dataframe[
            self.dataframe['NAMC_CODE'].str.contains(query_text, case=False, na=False, regex=False)
        ]
        
        if not code_matches.empty:
            results = []
            for idx, (_, row) in enumerate(code_matches.iterrows()):
                if idx >= k:
                    break
                results.append({
                    "rank": idx + 1,
                    "data": row.to_dict(),
                    "similarity_score": 1.0,  # Exact match
                    "match_type": "code_match"
                })
            
            return {
                "success": True,
                "query": query_text,
                "total_results": len(results),
                "search_method": "code_search",
                "results": results
            }
        
        return None  # No matches found

    def search_by_term(self, query_text, k=5):
        """Search specifically in NAMC_term field."""
        print("🔍 Searching by NAMASTE term...")
        
        # Check if column exists
        if 'NAMC_term' not in self.dataframe.columns:
            print("❌ NAMC_term column not found")
            return None
        
        # Try exact and partial matches in term field
        term_matches = self.dataframe[
            self.dataframe['NAMC_term'].str.contains(query_text, case=False, na=False, regex=False)
        ]
        
        if not term_matches.empty:
            results = []
            for idx, (_, row) in enumerate(term_matches.iterrows()):
                if idx >= k:
                    break
                results.append({
                    "rank": idx + 1,
                    "data": row.to_dict(),
                    "similarity_score": 0.95,  # High relevance for term match
                    "match_type": "term_match"
                })
            
            return {
                "success": True,
                "query": query_text,
                "total_results": len(results),
                "search_method": "term_search",
                "results": results
            }
        
        return None  # No matches found

    def embed_query(self, query_text):
        """
        Convert a text query into an embedding vector.
        
        Args:
            query_text (str): The search query text
            
        Returns:
            numpy.ndarray: The query embedding, or None if failed
        """
        if not self.model:
            print("Model not loaded. Call load_components() first.")
            return None
        
        try:
            # Generate embedding for the query (same process as training data)
            query_embedding = self.model.encode(
                [query_text],
                convert_to_numpy=True,
                normalize_embeddings=True  # Same normalization as training
            )
            return query_embedding
            
        except Exception as e:
            print(f"Error embedding query: {str(e)}")
            return None
    
    def search_by_description(self, query_text, k=5, return_scores=True):
        """Search using semantic similarity in definitions (your current embeddings)."""
        print("🔍 Performing semantic search in definitions...")
        return self.search(query_text, k, return_scores)

    def search(self, query_text, k=5, return_scores=True):
        """
        Original semantic search method (using your current embeddings).
        """
        if not self.is_ready:
            return {
                "success": False,
                "error": "Search engine not initialized. Call load_components() first.",
                "results": []
            }
        
        if not query_text or not query_text.strip():
            return {
                "success": False,
                "error": "Empty query provided",
                "results": []
            }
        
        try:
            # Embed the query
            query_embedding = self.embed_query(query_text.strip())
            if query_embedding is None:
                return {
                    "success": False,
                    "error": "Failed to generate query embedding",
                    "results": []
                }
            
            # Perform FAISS search
            scores, indices = self.index.search(query_embedding.astype(np.float32), k)
            
            # Get the complete row data for found indices
            found_indices = indices[0].tolist()  # FAISS returns 2D array, we want the first row
            similarity_scores = scores[0].tolist()
            
            # Retrieve complete data for the found indices
            complete_data = get_row_data_by_indices(self.dataframe, found_indices)
            
            # Combine with similarity scores if requested
            results = []
            for i, (data_row, score) in enumerate(zip(complete_data, similarity_scores)):
                result_item = {
                    "rank": i + 1,
                    "data": data_row,
                    "match_type": "semantic_match"
                }
                
                if return_scores:
                    result_item["similarity_score"] = float(score)
                
                results.append(result_item)
            
            return {
                "success": True,
                "query": query_text,
                "total_results": len(results),
                "search_method": "semantic_search",
                "results": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Search failed: {str(e)}",
                "results": []
            }

    def intelligent_search(self, query_text, k=5, return_scores=True):
        """
        Intelligent search that automatically detects query type and searches appropriate fields.
        """
        if not self.is_ready:
            return {
                "success": False,
                "error": "Search engine not initialized. Call load_components() first.",
                "results": []
            }
        
        query_text = query_text.strip()
        query_type = self.detect_query_type(query_text)
        
        print(f"🤖 Detected query type: {query_type}")
        
        # Try field-specific search first
        if query_type == "code":
            result = self.search_by_code(query_text, k)
            if result:
                return result
        elif query_type == "term":
            result = self.search_by_term(query_text, k)
            if result:
                return result
        
        # Fall back to semantic search (your current embeddings)
        print("⚡ Falling back to semantic search...")
        return self.search_by_description(query_text, k, return_scores)

    def batch_search(self, queries, k=5):
        """
        Perform search for multiple queries at once.
        """
        if not self.is_ready:
            return {
                "success": False,
                "error": "Search engine not initialized",
                "results": {}
            }
        
        batch_results = {}
        
        for i, query in enumerate(queries):
            result = self.intelligent_search(query, k=k, return_scores=True)
            batch_results[f"query_{i}"] = {
                "query_text": query,
                "result": result
            }
        
        return {
            "success": True,
            "total_queries": len(queries),
            "results": batch_results
        }

def search_interactive():
    """
    Interactive search function for testing the search engine.
    """
    print("🔍 Ayurvedic NAMASTE Code Search Engine")
    print("=" * 50)
    
    # Initialize search engine
    search_engine = AyurvedicSearch()
    
    print("Initializing search engine...")
    if not search_engine.load_components():
        print("Failed to initialize search engine. Exiting.")
        return
    
    # Debug: Show available columns
    print(f"\n📋 Available data columns: {list(search_engine.dataframe.columns)}")
    
    print("\nSearch engine ready! Type your queries below.")
    print("Commands:")
    print("  - Type any text to search (auto-detects codes, terms, or descriptions)")
    print("  - Type 'quit' or 'exit' to exit")
    print("  - Type 'help' for more options")
    print("  - Type 'columns' to see available data fields")
    print("-" * 50)
    
    while True:
        try:
            query = input("\n🔍 Enter your search query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye! 👋")
                break
            
            if query.lower() == 'help':
                print("\nHelp:")
                print("  🔢 Code search: 'SR11 (AAA-1)', 'VC-11', 'EE-2.4'")
                print("  🏥 Term search: 'vAtasa~jcayaH', Sanskrit medical terms")
                print("  📝 Description search: 'fever treatment', 'abdominal pain'")
                print("  - The system automatically detects what type of search to perform")
                continue
            
            if query.lower() == 'columns':
                print(f"\n📋 Available columns in dataset:")
                for i, col in enumerate(search_engine.dataframe.columns, 1):
                    print(f"  {i}. {col}")
                continue
            
            if not query:
                print("Please enter a search query.")
                continue
            
            # Perform intelligent search
            print(f"\nSearching for: '{query}'...")
            results = search_engine.intelligent_search(query, k=5, return_scores=True)
            
            if results["success"]:
                print(f"\n✅ Found {results['total_results']} results using {results.get('search_method', 'intelligent search')}:")
                print("-" * 60)
                
                for result in results["results"]:
                    data = result["data"]
                    score = result.get("similarity_score", 0)
                    match_type = result.get("match_type", "unknown")
                    
                    print(f"\n🏥 Rank {result['rank']} (Score: {score:.4f}, Type: {match_type})")
                    print("-" * 50)
                    
                    # Display key information in order of importance
                    important_fields = ['NAMC_CODE', 'NAMC_term', 'Long_definition']
                    
                    for field in important_fields:
                        if field in data and pd.notna(data[field]) and str(data[field]).strip() and str(data[field]) not in ['nan', 'None', '', 'NaN']:
                            value = str(data[field]).strip()
                            
                            # Format field names nicely
                            display_names = {
                                'NAMC_CODE': 'Code',
                                'NAMC_term': 'Term', 
                                'Long_definition': 'Definition'
                            }
                            
                            display_name = display_names.get(field, field)
                            
                            # Truncate long text appropriately
                            if field == 'Long_definition' and len(value) > 200:
                                value = value[:200] + "..."
                            elif len(value) > 100:
                                value = value[:100] + "..."
                                
                            print(f"   {display_name}: {value}")
                    
                    # Show any other available fields
                    other_fields = [k for k in data.keys() if k not in important_fields]
                    for field in other_fields[:2]:  # Show max 2 additional fields
                        if field in data and pd.notna(data[field]) and str(data[field]).strip() and str(data[field]) not in ['nan', 'None', '', 'NaN']:
                            value = str(data[field]).strip()
                            if len(value) > 80:
                                value = value[:80] + "..."
                            print(f"   {field}: {value}")
                    
                    print("-" * 40)
                    
            else:
                print(f"❌ Search failed: {results['error']}")
                
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"An error occurred: {str(e)}")

def search_api(query_text, k=5):
    """API-style search function that returns JSON results."""
    search_engine = AyurvedicSearch()
    
    if not search_engine.load_components():
        return json.dumps({
            "success": False,
            "error": "Failed to initialize search engine",
            "results": []
        })
    
    results = search_engine.intelligent_search(query_text, k=k, return_scores=True)
    return json.dumps(results, indent=2, ensure_ascii=False)

def single_query_search(query, k=5, format_output='pretty'):
    """Perform a single search query."""
    if format_output == 'json':
        result = search_api(query, k=k)
        print(result)
        return True
    
    # Pretty formatted output using intelligent search
    search_engine = AyurvedicSearch()
    if not search_engine.load_components():
        print("❌ Failed to initialize search engine")
        return False
    
    results = search_engine.intelligent_search(query, k=k, return_scores=True)
    
    if results["success"]:
        print(f"\n🔍 Query: '{query}' (detected as {search_engine.detect_query_type(query)})")
        print(f"✅ Found {results['total_results']} results using {results.get('search_method', 'intelligent search')}:\n")
        
        for result in results["results"]:
            data = result["data"]
            score = result.get("similarity_score", 0)
            match_type = result.get("match_type", "unknown")
            
            print(f"🏥 Rank {result['rank']} (Score: {score:.4f}, Type: {match_type})")
            print("-" * 50)
            
            # Display key information
            important_fields = ['NAMC_CODE', 'NAMC_term', 'Long_definition']
            
            for field in important_fields:
                if field in data and pd.notna(data[field]) and str(data[field]).strip() and str(data[field]) not in ['nan', 'None', '', 'NaN']:
                    value = str(data[field]).strip()
                    
                    display_names = {
                        'NAMC_CODE': 'Code',
                        'NAMC_term': 'Term', 
                        'Long_definition': 'Definition'
                    }
                    
                    display_name = display_names.get(field, field)
                    
                    if field == 'Long_definition' and len(value) > 200:
                        value = value[:200] + "..."
                    elif len(value) > 100:
                        value = value[:100] + "..."
                        
                    print(f"{display_name}: {value}")
            
            # Show additional fields if any
            other_fields = [k for k in data.keys() if k not in important_fields]
            for field in other_fields[:2]:
                if field in data and pd.notna(data[field]) and str(data[field]).strip() and str(data[field]) not in ['nan', 'None', '', 'NaN']:
                    value = str(data[field]).strip()
                    if len(value) > 80:
                        value = value[:80] + "..."
                    print(f"{field}: {value}")
            
            print("\n")
        
        return True
    else:
        print(f"❌ Search failed: {results['error']}")
        return False

if __name__ == '__main__':
    # Run interactive search
    search_interactive()
