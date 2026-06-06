"""
Wrapper resiliente SQL centralizado.
No usa pyodbc/pymssql directo.
"""

import time
from core.sql_first.db import get_sql_connection

def get_resilient_sql_connection(retries: int = 3, delay: float = 1.0):
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            return get_sql_connection()
        except Exception as e:
            last_error = e
            if attempt < retries:
                time.sleep(delay)

    raise last_error

def execute_with_retry(callback, retries: int = 3, delay: float = 1.0):
    last_error = None

    for attempt in range(1, retries + 1):
        conn = None
        try:
            conn = get_sql_connection()
            result = callback(conn)
            return result
        except Exception as e:
            last_error = e
            if attempt < retries:
                time.sleep(delay)
        finally:
            try:
                if conn:
                    conn.close()
            except Exception:
                pass

    raise last_error
