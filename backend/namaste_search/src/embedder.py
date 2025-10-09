import numpy as np
import os
from sentence_transformers import SentenceTransformer
from namaste_search.src.data_loader import load_and_preprocess_data, get_text_data


def load_embedding_model():
    """
    Loads the LaBSE sentence transformer model for generating embeddings.
    
    Returns:
        SentenceTransformer: The loaded model
    """
    model_name = 'sentence-transformers/LaBSE'
    print(f"Loading embedding model: {model_name}")
    
    try:
        model = SentenceTransformer(model_name)
        print("Model loaded successfully!")
        return model
    except Exception as e:
        print(f"Error loading model: {str(e)}")
        return None

def generate_embeddings(texts, model, batch_size=32):
    """
    Generate embeddings for a list of texts using the provided model.
    
    Args:
        texts (list): List of text strings to embed
        model (SentenceTransformer): The loaded sentence transformer model
        batch_size (int): Batch size for processing (default: 32)
        
    Returns:
        numpy.ndarray: Array of embeddings with shape (n_texts, embedding_dim)
    """
    if not texts:
        print("No texts provided for embedding generation")
        return None
    
    print(f"Generating embeddings for {len(texts)} texts...")
    print(f"Using batch size: {batch_size}")
    
    try:
        # Generate embeddings in batches to manage memory usage
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True  # Normalize for better similarity search
        )
        
        print(f"Embeddings generated successfully!")
        print(f"Embedding shape: {embeddings.shape}")
        print(f"Embedding dimension: {embeddings.shape[1]}")
        
        return embeddings
        
    except Exception as e:
        print(f"Error generating embeddings: {str(e)}")
        return None

def save_embeddings(embeddings, save_path):
    """
    Save embeddings to a NumPy file.
    
    Args:
        embeddings (numpy.ndarray): The embeddings array
        save_path (str): Path where to save the embeddings
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Save embeddings
        np.save(save_path, embeddings)
        print(f"Embeddings saved successfully to: {save_path}")
        print(f"File size: {os.path.getsize(save_path) / (1024*1024):.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"Error saving embeddings: {str(e)}")
        return False

def load_embeddings(load_path):
    """
    Load embeddings from a NumPy file.
    
    Args:
        load_path (str): Path to the saved embeddings file
        
    Returns:
        numpy.ndarray: The loaded embeddings array, or None if failed
    """
    try:
        if not os.path.exists(load_path):
            print(f"Embeddings file not found at: {load_path}")
            return None
        
        embeddings = np.load(load_path)
        print(f"Embeddings loaded successfully from: {load_path}")
        print(f"Embedding shape: {embeddings.shape}")
        
        return embeddings
        
    except Exception as e:
        print(f"Error loading embeddings: {str(e)}")
        return None

def generate_and_save_embeddings():
    """
    Main function to generate embeddings from the dataset and save them.
    This function orchestrates the entire embedding generation process.
    
    Returns:
        bool: True if the process completed successfully, False otherwise
    """
    # Define paths
    embeddings_dir = os.path.join(os.path.dirname(__file__), '..', 'embeddings')
    embeddings_path = os.path.join(embeddings_dir, 'text_embeddings.npy')
    
    # Check if embeddings already exist
    if os.path.exists(embeddings_path):
        print(f"Embeddings already exist at: {embeddings_path}")
        response = input("Do you want to regenerate them? (y/n): ")
        if response.lower() != 'y':
            print("Using existing embeddings.")
            return True
    
    # Load and preprocess data
    print("\n=== Loading Data ===")
    df = load_and_preprocess_data()
    if df is None:
        print("Failed to load data. Aborting embedding generation.")
        return False
    
    # Extract text data
    texts = get_text_data(df)
    if not texts:
        print("No text data found. Aborting embedding generation.")
        return False
    
    # Load embedding model
    print("\n=== Loading Model ===")
    model = load_embedding_model()
    if model is None:
        print("Failed to load embedding model. Aborting.")
        return False
    
    # Generate embeddings
    print("\n=== Generating Embeddings ===")
    embeddings = generate_embeddings(texts, model)
    if embeddings is None:
        print("Failed to generate embeddings. Aborting.")
        return False
    
    # Save embeddings
    print("\n=== Saving Embeddings ===")
    success = save_embeddings(embeddings, embeddings_path)
    if not success:
        print("Failed to save embeddings.")
        return False
    
    print("\n=== Embedding Generation Complete ===")
    print(f"Successfully generated and saved {embeddings.shape[0]} embeddings")
    print(f"Embedding dimension: {embeddings.shape[1]}")
    
    return True

if __name__ == '__main__':
    # Run the embedding generation process
    print("Starting embedding generation process...")
    success = generate_and_save_embeddings()
    
    if success:
        print("\n✅ Embedding generation completed successfully!")
    else:
        print("\n❌ Embedding generation failed!")
    
    # Test loading the saved embeddings
    embeddings_path = os.path.join(os.path.dirname(__file__), '..', 'embeddings', 'text_embeddings.npy')
    if os.path.exists(embeddings_path):
        print("\n=== Testing Embedding Loading ===")
        loaded_embeddings = load_embeddings(embeddings_path)
        if loaded_embeddings is not None:
            print("✅ Embeddings can be loaded successfully!")
