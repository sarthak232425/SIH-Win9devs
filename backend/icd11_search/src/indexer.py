import numpy as np
import faiss
import os
from icd11_search.src.embedder import load_embeddings


def create_faiss_index(embeddings, index_type='IndexFlatIP'):
    """
    Create a FAISS index from embeddings.
    
    Args:
        embeddings (numpy.ndarray): The embeddings array with shape (n_samples, embedding_dim)
        index_type (str): Type of FAISS index to create
                         - 'IndexFlatIP': Exact search using inner product (good for normalized embeddings)
                         - 'IndexFlatL2': Exact search using L2 distance
                         - 'IndexIVFFlat': Approximate search (faster for large datasets)
        
    Returns:
        faiss.Index: The created FAISS index, or None if failed
    """
    if embeddings is None or len(embeddings) == 0:
        print("No embeddings provided for index creation")
        return None
    
    try:
        embedding_dim = embeddings.shape[1]
        n_samples = embeddings.shape[0]
        
        print(f"Creating FAISS index...")
        print(f"Number of samples: {n_samples}")
        print(f"Embedding dimension: {embedding_dim}")
        print(f"Index type: {index_type}")
        
        # Create the appropriate index type
        if index_type == 'IndexFlatIP':
            # Inner Product (good for normalized embeddings)
            index = faiss.IndexFlatIP(embedding_dim)
        elif index_type == 'IndexFlatL2':
            # L2 distance (Euclidean distance)
            index = faiss.IndexFlatL2(embedding_dim)
        elif index_type == 'IndexIVFFlat':
            # Approximate search - faster for large datasets
            nlist = min(100, n_samples // 10)  # Number of clusters
            quantizer = faiss.IndexFlatIP(embedding_dim)
            index = faiss.IndexIVFFlat(quantizer, embedding_dim, nlist)
            
            # Train the index (required for IVF indexes)
            print(f"Training IVF index with {nlist} clusters...")
            index.train(embeddings.astype(np.float32))
        else:
            print(f"Unsupported index type: {index_type}")
            return None
        
        # Add embeddings to the index
        print("Adding embeddings to index...")
        index.add(embeddings.astype(np.float32))
        
        print(f"FAISS index created successfully!")
        print(f"Index contains {index.ntotal} vectors")
        
        return index
        
    except Exception as e:
        print(f"Error creating FAISS index: {str(e)}")
        return None


def save_faiss_index(index, save_path):
    """
    Save a FAISS index to disk.
    
    Args:
        index (faiss.Index): The FAISS index to save
        save_path (str): Path where to save the index
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Save the index
        faiss.write_index(index, save_path)
        
        print(f"FAISS index saved successfully to: {save_path}")
        print(f"File size: {os.path.getsize(save_path) / (1024*1024):.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"Error saving FAISS index: {str(e)}")
        return False


def load_faiss_index(load_path):
    """
    Load a FAISS index from disk.
    
    Args:
        load_path (str): Path to the saved FAISS index
        
    Returns:
        faiss.Index: The loaded FAISS index, or None if failed
    """
    try:
        if not os.path.exists(load_path):
            print(f"FAISS index file not found at: {load_path}")
            return None
        
        # Load the index
        index = faiss.read_index(load_path)
        
        print(f"FAISS index loaded successfully from: {load_path}")
        print(f"Index contains {index.ntotal} vectors")
        print(f"Index dimension: {index.d}")
        
        return index
        
    except Exception as e:
        print(f"Error loading FAISS index: {str(e)}")
        return None


def build_and_save_index(index_type='IndexFlatIP', force_rebuild=False):
    """
    Main function to build and save the FAISS index from embeddings.
    
    Args:
        index_type (str): Type of FAISS index to create
        force_rebuild (bool): Whether to force rebuild even if index exists
        
    Returns:
        bool: True if the process completed successfully, False otherwise
    """
    # Define paths
    embeddings_path = os.path.join(os.path.dirname(__file__), 'embeddings', 'icd11_embeddings.npy')
    index_dir = os.path.join(os.path.dirname(__file__), 'index')
    index_path = os.path.join(index_dir, 'icd11_faiss_index.bin')
    
    # Check if index already exists
    if os.path.exists(index_path) and not force_rebuild:
        print(f"FAISS index already exists at: {index_path}")
        response = input("Do you want to rebuild it? (y/n): ")
        if response.lower() != 'y':
            print("Using existing index.")
            return True
    
    # Load embeddings
    print("\n=== Loading Embeddings ===")
    embeddings = load_embeddings(embeddings_path)
    if embeddings is None:
        print("Failed to load embeddings. Please run embedder.py first.")
        return False
    
    # Create FAISS index
    print("\n=== Creating FAISS Index ===")
    index = create_faiss_index(embeddings, index_type)
    if index is None:
        print("Failed to create FAISS index.")
        return False
    
    # Save FAISS index
    print("\n=== Saving FAISS Index ===")
    success = save_faiss_index(index, index_path)
    if not success:
        print("Failed to save FAISS index.")
        return False
    
    print("\n=== Index Creation Complete ===")
    print(f"Successfully created and saved FAISS index with {index.ntotal} vectors")
    
    return True


def get_index_info(index_path=None):
    """
    Get information about a saved FAISS index.
    
    Args:
        index_path (str): Path to the FAISS index file. If None, uses default path.
        
    Returns:
        dict: Dictionary containing index information, or None if failed
    """
    if index_path is None:
        index_path = os.path.join(os.path.dirname(__file__), 'index', 'icd11_faiss_index.bin')
    
    index = load_faiss_index(index_path)
    if index is None:
        return None
    
    info = {
        'total_vectors': index.ntotal,
        'dimension': index.d,
        'index_type': type(index).__name__,
        'file_size_mb': os.path.getsize(index_path) / (1024*1024),
        'is_trained': index.is_trained if hasattr(index, 'is_trained') else True
    }
    
    return info


if __name__ == '__main__':
    print("Starting ICD-11 FAISS index creation process...")
    
    # You can change the index type here based on your needs
    # Options: 'IndexFlatIP', 'IndexFlatL2', 'IndexIVFFlat'
    index_type = 'IndexFlatIP'  # Good for normalized embeddings from LaBSE
    
    success = build_and_save_index(index_type=index_type)
    
    if success:
        print(f"\n✅ FAISS index creation completed successfully!")
        
        # Display index information
        print("\n=== Index Information ===")
        info = get_index_info()
        if info:
            for key, value in info.items():
                print(f"{key}: {value}")
        
        # Test loading the saved index
        print("\n=== Testing Index Loading ===")
        index_path = os.path.join(os.path.dirname(__file__), 'index', 'icd11_faiss_index.bin')
        test_index = load_faiss_index(index_path)
        if test_index is not None:
            print("✅ Index can be loaded successfully!")
    else:
        print("\n❌ FAISS index creation failed!")
