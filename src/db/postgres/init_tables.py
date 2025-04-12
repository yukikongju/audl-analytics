import os

from src.utils.postgres.operations import create_table_from_sql
from src.utils.postgres.connections import get_postgres_connection


def main():
    SCHEDULE_TABLE_NAME = "schedule"

    # --- reading create table queries
    ROOT_DIR = os.path.abspath(os.curdir)
    SCHEDULE_SQL_PATH = os.path.join(ROOT_DIR, "src/db/postgres/schema/schedule.sql")

    with open(SCHEDULE_SQL_PATH, 'r') as f:
        create_schedule_sql = ''.join(f.readlines())

    #  print(create_schedule_sql)

    # --- run create table queries
    conn = get_postgres_connection()
    create_table_from_sql(conn, SCHEDULE_TABLE_NAME, create_sql=create_schedule_sql, 
                          drop_if_exist=True)
    print(f"Successfully created table {SCHEDULE_TABLE_NAME}")


if __name__ == "__main__":
    main()
