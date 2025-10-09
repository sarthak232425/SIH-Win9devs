import pandas as pd
import os

def load_and_preprocess_data():
    """
    Loads the NAMASTE_CODE.csv file, preprocesses the text data,
    and returns a pandas DataFrame.

    Returns:
        pandas.DataFrame: The preprocessed data with a 'Long_definition' column.
        Returns None if the file is not found or there are issues with the data.
    """
    # Define the path to the CSV file
    csv_file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'NAMASTE_CODE.csv')
    
    try:
        # Load the dataset
        print(f"Loading data from: {csv_file_path}")
        df = pd.read_csv(csv_file_path)
        
        # Display basic information about the dataset
        print(f"Dataset loaded successfully. Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        
        # Check if Long_definition column exists
        if 'Long_definition' not in df.columns:
            print("Error: 'Long_definition' column not found in the dataset")
            print("Available columns:", list(df.columns))
            return None
        
        # Preprocessing steps
        print("Starting data preprocessing...")
        
        # 1. Remove rows where Long_definition is null or empty
        initial_rows = len(df)
        df = df.dropna(subset=['Long_definition'])
        df = df[df['Long_definition'].str.strip() != '']
        final_rows = len(df)
        
        if final_rows < initial_rows:
            print(f"Removed {initial_rows - final_rows} rows with missing or empty Long_definition")
        
        # 2. Convert Long_definition to string and clean basic formatting
        df['Long_definition'] = df['Long_definition'].astype(str).str.strip()
        
        # 3. Reset index after filtering
        df = df.reset_index(drop=True)
        
        print(f"Data preprocessing completed. Final shape: {df.shape}")
        return df
        
    except FileNotFoundError:
        print(f"Error: File not found at {csv_file_path}")
        print("Please ensure the NAMASTE_CODE.csv file exists in the data folder")
        return None
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return None

def get_text_data(df):
    """
    Extracts the text data for embedding from the DataFrame.
    
    Args:
        df (pandas.DataFrame): The preprocessed DataFrame
        
    Returns:
        list: List of text strings to be embedded
    """
    if df is None or 'Long_definition' not in df.columns:
        return []
    
    text_data = df['Long_definition'].tolist()
    print(f"Extracted {len(text_data)} text entries for embedding")
    return text_data

def get_row_data_by_indices(df, indices):
    """
    Returns complete row data for given indices in JSON-serializable format.
    
    Args:
        df (pandas.DataFrame): The original DataFrame
        indices (list): List of row indices
        
    Returns:
        list: List of dictionaries containing complete row data
    """
    if df is None:
        return []
    
    # Get rows by indices
    selected_rows = df.iloc[indices]
    
    # Convert to list of dictionaries (JSON-serializable)
    result = selected_rows.to_dict('records')
    
    return result

if __name__ == '__main__':
    # Test the data loader
    print("Testing data_loader.py...")
    
    # Load and preprocess data
    data = load_and_preprocess_data()
    
    if data is not None:
        print("\n--- Dataset Information ---")
        print(f"Shape: {data.shape}")
        print(f"Columns: {list(data.columns)}")
        
        print("\n--- First 3 rows ---")
        print(data.head(3))
        
        # Test text extraction
        text_data = get_text_data(data)
        if text_data:
            print(f"\n--- Sample Text Data ---")
            print(f"First text entry: {text_data[0][:100]}...")
        
        # Test row data retrieval
        sample_indices = [0, 1, 2]
        sample_data = get_row_data_by_indices(data, sample_indices)
        print(f"\n--- Sample Row Data (JSON format) ---")
        print(f"Number of rows retrieved: {len(sample_data)}")
        if sample_data:
            print(f"Keys in first row: {list(sample_data[0].keys())}")
