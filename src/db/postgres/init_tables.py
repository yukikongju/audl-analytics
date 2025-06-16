import os
from argparse import ArgumentParser, Namespace

from src.utils.postgres.operations import create_table_from_sql
from src.utils.postgres.connections import get_postgres_connection


def main(args: Namespace):
    table_name = args.table_name
    sql_path = args.sql_path

    # --- reading create table queries
    ROOT_DIR = os.path.abspath(os.curdir)
    sql_path = os.path.join(ROOT_DIR, sql_path)
    print(sql_path)

    with open(sql_path, 'r') as f:
        ddl = ''.join(f.readlines())

    # --- run create table queries
    conn = get_postgres_connection()

    # - creating schedule table
    create_table_from_sql(conn, table_name=table_name, create_sql=ddl, 
                          drop_if_exist=False)
    print(f"Successfully created table {table_name}")




if __name__ == "__main__":
    parser = ArgumentParser(description="Creating Table from sql file")
    parser.add_argument("--sql_path", required=True, type=str, help="Path to sql file")
    parser.add_argument("--table_name", required=True, type=str, help="Table Name")
    args = parser.parse_args()
    main(args)
