import pandas as pd
import os


def load_and_preprocess_data():
    """
    Loads the icd11_clean.csv file, preprocesses the text data,
    and returns a pandas DataFrame.

    Returns:
        pandas.DataFrame: The preprocessed data with 'code' and 'title' columns.
        Returns None if the file is not found or there are issues with the data.
    """
    # Define the path to the CSV file
    csv_file_path = os.path.join(os.path.dirname(__file__), 'icd11_clean.csv')
    
    try:
        # Load the dataset
        print(f"Loading data from: {csv_file_path}")
        df = pd.read_csv(csv_file_path)
        
        # Display basic information about the dataset
        print(f"Dataset loaded successfully. Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        
        # Check if required columns exist
        required_columns = ['code', 'title']
        for col in required_columns:
            if col not in df.columns:
                print(f"Error: '{col}' column not found in the dataset")
                print("Available columns:", list(df.columns))
                return None
        
        # Preprocessing steps
        print("Starting data preprocessing...")
        
        # 1. Remove rows where title is null or empty
        initial_rows = len(df)
        df = df.dropna(subset=['title'])
        df = df[df['title'].str.strip() != '']
        final_rows = len(df)
        
        if final_rows < initial_rows:
            print(f"Removed {initial_rows - final_rows} rows with missing or empty title")
        
        # 2. Convert title to string and clean basic formatting
        df['title'] = df['title'].astype(str).str.strip()
        df['code'] = df['code'].astype(str).str.strip()
        
        # 3. Reset index after filtering
        df = df.reset_index(drop=True)
        
        print(f"Data preprocessing completed. Final shape: {df.shape}")
        return df
        
    except FileNotFoundError:
        print(f"Error: File not found at {csv_file_path}")
        print("Please ensure the icd11_clean.csv file exists in the same directory")
        return None
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return None


def get_text_data(df):
    """
    Extracts the text data for embedding from the DataFrame.
    For ICD-11 data, we'll combine code and title for better semantic search.
    Keep the (TM2) classification as it's important medical information.
    
    Args:
        df (pandas.DataFrame): The preprocessed DataFrame
        
    Returns:
        list: List of text strings to be embedded
    """
    if df is None or 'title' not in df.columns:
        return []
    
    # Combine code and title for richer semantic representation
    # Keep the (TM2) as it's important classification information
    text_data = []
    for _, row in df.iterrows():
        code = row['code']
        title = row['title']
        
        # Only clean excessive dashes but keep (TM2) classification
        cleaned_title = title.replace('- - - - -', '').replace('- - - -', '').strip()
        
        # Combine code and title (keeping TM2)
        combined_text = f"{code}: {cleaned_title}"
        text_data.append(combined_text)
    
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
            print(f"First text entry: {text_data[0]}")
            print(f"Second text entry: {text_data[1]}")
        
        # Test row data retrieval
        sample_indices = [0, 1, 2]
        sample_data = get_row_data_by_indices(data, sample_indices)
        print(f"\n--- Sample Row Data (JSON format) ---")
        print(f"Number of rows retrieved: {len(sample_data)}")
        if sample_data:
            print(f"Keys in first row: {list(sample_data[0].keys())}")
