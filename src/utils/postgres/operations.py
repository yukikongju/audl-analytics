import logging
import pandas as pd

from sqlalchemy import inspect, text, Table, MetaData
from sqlalchemy.engine import Connection
from sqlalchemy.dialects.postgresql import insert
from typing import List

from src.utils.errors import TableAlreadyExistError, TableNotFoundError


def create_table_from_sql(conn: Connection, table_name: str, create_sql: str, drop_if_exist: bool = False) -> None:
    """

    """
    if drop_if_exist:
        conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))

    inspector = inspect(conn)
    table_exists = inspector.has_table(table_name)

    if table_exists:
        raise TableAlreadyExistError(f"Table '{table_name}' already exists. Please change the flag 'drop_if_exist' or delete the table and retry.")

    try:
        conn.execute(text(create_sql))
    except Exception as e:
        raise Exception(f"The following error has occured when creating table {table_name}: {e}")

    logging.log(0, f"Succesfully created table {table_name}")


def upsert_dataframe(conn: Connection, table_name: str, df: pd.DataFrame) -> None:
    """

    """
    # --- get table indexes
    conflict_keys = get_table_primary_key(conn, table_name)
    if not conflict_keys:
        raise ValueError(f"No indexes found for table {table_name}. Cannot upsert")
    print(conflict_keys)

    metadata = MetaData()
    table = Table(table_name, metadata, autoload_with=conn)
    table_cols = [col.name for col in table.columns]

    # --- drop columns not in schema
    try:
        dff = df[table_cols]
    except:
        raise ValueError("Column not in schema")

    # --- check if dataframe width is the same as DDL
    if len(dff.columns) != len(table_cols):
        raise ValueError(f"The number of column in dataframe doesn't match table schema. Dataframe has {len(dff.columns)} whilst DDL has {len(table_cols)}. Please check!")

    # --- check if df matches DDL
    if set(dff.columns) != set(table_cols):
        raise ValueError("The dataframe columns doesn't match the defined DDL. Please check!")

    # --- convert dataframe column into matching data type
    dff = convert_df_types_to_table_schema(conn=conn, df=dff, table_name=table_name)

    # --- build upsert query
    records = dff.to_dict(orient='records')

    # FIXME: add case when table has index + pk
    stmt = insert(table).values(records)
    update_dict = {
        col: getattr(stmt.excluded, col)
        for col in df.columns if col not in conflict_keys
    }
    upsert_stmt = stmt.on_conflict_do_update(
        index_elements=conflict_keys,
        set_=update_dict
    )

    # --- push the data into the table
    conn.execute(upsert_stmt)
    logging.log(0, f"Succesfully upserted dataframe into table {table_name}")


def get_table_indexes(conn: Connection, table_name: str):
    """

    """
    inspector = inspect(conn)
    table_exists = inspector.has_table(table_name)
    if not table_exists:
        raise TableNotFoundError(f"Could not get the indexes of the table {table_name} because the table doesn't exist. Please check!")

    return inspector.get_indexes(table_name)

def get_table_primary_key(conn: Connection, table_name: str) -> List[str]:
    inspector = inspect(conn)

    table_exists = inspector.has_table(table_name)
    if not table_exists:
        raise TableNotFoundError(f"Could not get the indexes of the table {table_name} because the table doesn't exist. Please check!")

    pk = inspector.get_pk_constraint(table_name)
    return pk['constrained_columns']


def convert_df_types_to_table_schema(conn: Connection, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    """
    Aligns the DataFrame's column dtypes to match the PostgreSQL table schema.

    Parameters:
        df (pd.DataFrame): Input DataFrame to align.
        conn (Connection): SQLAlchemy connection to PostgreSQL.
        table_name (str): Name of the table to match schema with.

    Returns:
        pd.DataFrame: A new DataFrame with converted dtypes.
    """
    inspector = inspect(conn)
    columns_info = inspector.get_columns(table_name)

    df_aligned = df.copy()
    for col in columns_info:
        col_name = col['name']
        col_type = col['type']

        if col_name not in df_aligned.columns:
            continue  # skip missing columns

        try:
            if "CHAR" in str(col_type).upper() or "TEXT" in str(col_type).upper():
                df_aligned[col_name] = df_aligned[col_name].astype(str)
            elif "INT" in str(col_type).upper():
                df_aligned[col_name] = pd.to_numeric(df_aligned[col_name], downcast='integer', errors='coerce')
            elif "FLOAT" in str(col_type).upper() or "NUMERIC" in str(col_type).upper() or "DECIMAL" in str(col_type).upper():
                df_aligned[col_name] = pd.to_numeric(df_aligned[col_name], errors='coerce')
            elif "BOOL" in str(col_type).upper():
                df_aligned[col_name] = df_aligned[col_name].astype(bool)
            elif "TIMESTAMP" in str(col_type).upper() or "DATE" in str(col_type).upper():
                df_aligned[col_name] = pd.to_datetime(df_aligned[col_name], errors='coerce')
            else:
                logging.warning(f"Unmapped SQL type '{col_type}' for column '{col_name}', leaving as-is.")
        except Exception as e:
            #  logging.warning(f"Could not convert column '{col_name}' to type '{col_type}': {e}")
            raise Exception(f"Could not convert column '{col_name}' to type '{col_type}': {e}")

    return df_aligned
