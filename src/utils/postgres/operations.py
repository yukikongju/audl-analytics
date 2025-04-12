import logging
import pandas as pd

from sqlalchemy import inspect, text, Table, MetaData
from sqlalchemy.engine import Connection
from sqlalchemy.dialects.postgresql import insert

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

    conn.execute(text(create_sql))
    logging.log(0, f"Succesfully created table {table_name}")


def upsert_dataframe(conn: Connection, table_name: str, df: pd.DataFrame) -> None:
    """

    """
    # --- get table indexes
    indexes = get_table_indexes(conn, table_name)
    if not indexes:
        raise ValueError(f"No indexes found for table {table_name}. Cannot upsert")
    conflict_columns = indexes[0]['column_names']


    # --- build upsert query
    metadata = MetaData()
    table = Table(table_name, metadata, autoload_with=conn)
    records = df.to_dict(orient='records')
    stmt = insert(table).values(records)
    upsert_stmt = stmt.on_conflict_do_update(
        index_elements=conflict_columns,
        set_={col: getattr(stmt.excluded, col) for col in df.columns if col != 'gameID'}
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


