import contextlib
from typing import Iterator

import psycopg
from psycopg.rows import dict_row

from .config import settings


def get_conn() -> psycopg.Connection:
    return psycopg.connect(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
        autocommit=False,
        row_factory=dict_row,
    )


@contextlib.contextmanager
def transaction() -> Iterator[psycopg.Connection]:
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                yield cur
    finally:
        conn.close()
