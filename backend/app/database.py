import os
from contextlib import contextmanager
from typing import Generator

import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"


class ConnectionPool:
    def __init__(self, minconn: int = 1, maxconn: int = 10):
        self.minconn = minconn
        self.maxconn = maxconn
        self._pool = []
        self._in_use = []

    def getconn(self) -> psycopg.Connection:
        if self._pool:
            conn = self._pool.pop()
        else:
            conn = psycopg.connect(DATABASE_URL)
        self._in_use.append(conn)
        return conn

    def putconn(self, conn: psycopg.Connection):
        self._in_use.remove(conn)
        if conn.closed:
            return
        self._pool.append(conn)

    def closeall(self):
        for conn in self._pool + self._in_use:
            conn.close()
        self._pool.clear()
        self._in_use.clear()


connection_pool = ConnectionPool(1, 10)


def get_db() -> Generator[psycopg.Connection, None, None]:
    conn = connection_pool.getconn()
    try:
        yield conn
    finally:
        connection_pool.putconn(conn)


@contextmanager
def get_cursor(conn: psycopg.Connection):
    cursor = conn.cursor(row_factory=psycopg.rows.dict_row)
    try:
        yield cursor
    finally:
        cursor.close()