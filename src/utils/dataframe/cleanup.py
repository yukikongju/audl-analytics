import pandas as pd

def standardize_column_names(df: pd.DataFrame, case: str = "snake") -> pd.DataFrame:

    def to_snake(name: str, to_replace: str = ".", replace_with: str = "_"):
        return name.strip().lower().replace(to_replace, replace_with)

    if case == "snake":
        df.columns = [to_snake(col) for col in df.columns]
    elif case == "lower":
        df.columns = [col.lower() for col in df.columns]
    elif case == "upper":
        df.columns = [col.upper() for col in df.columns]
    else:
        raise ValueError(f"{case} not supported. Please select either 'snake', 'lower', or 'upper'")

    return df

def drop_duplicated_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[:, ~df.columns.duplicated(keep='first')]

def standardize_dataframe(df: pd.DataFrame, case: str = 'snake') -> pd.DataFrame:
    df = standardize_column_names(df=df, case=case)
    df = drop_duplicated_columns(df=df)
    return df

