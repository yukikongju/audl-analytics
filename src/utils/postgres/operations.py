import logging
from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection


class TableAlreadyExistError(Exception):
    pass


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


