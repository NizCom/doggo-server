from psycopg2 import pool
from src.utils.config import load_database_config

# Initialize the connection pool variable
db_pool = None


def init_db_pool():
    global db_pool
    if db_pool is None:
        db_config = load_database_config()
        db_pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            **db_config
        )


def get_db_connection():
    if db_pool is None:
        raise Exception("Database pool not initialized.")
    return db_pool.getconn()


def release_db_connection(conn):
    if db_pool and conn:
        db_pool.putconn(conn)


def close_db_pool():
    if db_pool:
        db_pool.closeall()