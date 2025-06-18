import pandas as pd

def read_csv(file_path: str) -> pd.DataFrame:
    """
    Reading csv file from file path
    """
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise FileNotFoundError(f"Could not find file {file_path}. Exit with error {e}")
    return df

