import os

import psycopg


def connect() -> psycopg.Connection:
    """Application-role connection in autocommit mode.

    Use cases own their transactions.
    """
    return psycopg.connect(os.environ["DATABASE_URL"], autocommit=True)
