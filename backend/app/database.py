import os

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from psycopg2 import pool

load_dotenv()

DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

# connection pool — min 1, max 10
connection_pool = pool.SimpleConnectionPool(1, 10, DATABASE_URL)


def get_db():
    conn = connection_pool.getconn()
    try:
        yield conn
    finally:
        connection_pool.putconn(conn)  # always return to pool


def get_cursor(conn):
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)  # returns dict
