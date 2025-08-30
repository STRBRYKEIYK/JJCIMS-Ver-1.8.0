import pyodbc
import time
from .path_utils import resolve_db_path


class AccessConnector:
    """Wrapper around pyodbc Access connections.

    If db_path is None, the connector will try (in order):
      - environment variable JJCIMS_DB
      - utils.helpers.get_app_dir() + /database/JJCIMS.accdb (if helpers available)
      - fallback to database/JJCIMS.accdb next to this module
    """
    def __init__(self, db_path=None):
        # Centralized robust resolution (env var, PyInstaller, helpers, local, upward search)
        self.db_path = resolve_db_path(db_path)
        self.connection = None

    def connect(self):
        self.connection = pyodbc.connect(
            f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={self.db_path};"
        )
        return self.connection

    def execute_query(self, query, params=None, retries=3, delay=2):
        """Execute a query with optional params and simple retry-on-locking logic.

        This method opens a fresh connection for each attempt to avoid using
        closed/half-closed connections after failures.
        """
        last_exc = None
        for attempt in range(retries):
            connection = self.connect()
            cursor = connection.cursor()
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                connection.commit()
                return
            except pyodbc.Error as e:
                last_exc = e
                if "locked" in str(e).lower():
                    if attempt < retries - 1:
                        time.sleep(delay)
                        continue
                    else:
                        raise
                else:
                    raise
            finally:
                try:
                    cursor.close()
                except Exception:
                    pass
                try:
                    connection.close()
                except Exception:
                    pass
        # If we exhausted retries, re-raise last exception
        if last_exc:
            raise last_exc

    def get_2fa_secret(self, username):
        """Fetch the 2FA Secret for the given username from the emp_list table."""
        query = "SELECT [2FA Secret] FROM [emp_list] WHERE [Username]=?"
        connection = self.connect()
        cursor = connection.cursor()
        try:
            cursor.execute(query, (username,))
            row = cursor.fetchone()
            if row:
                return row[0]
            return None
        finally:
            try:
                cursor.close()
            except Exception:
                pass
            try:
                connection.close()
            except Exception:
                pass

    def fetchall(self, query, params=None, retries=3, delay=2):
        """Execute a SELECT query and return all rows.

        Uses the same retry-on-lock logic as execute_query and ensures
        connections/cursors are closed.
        """
        last_exc = None
        for attempt in range(retries):
            connection = self.connect()
            cursor = connection.cursor()
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                rows = cursor.fetchall()
                return rows
            except pyodbc.Error as e:
                last_exc = e
                if "locked" in str(e).lower():
                    if attempt < retries - 1:
                        time.sleep(delay)
                        continue
                    else:
                        raise
                else:
                    raise
            finally:
                try:
                    cursor.close()
                except Exception:
                    pass
                try:
                    connection.close()
                except Exception:
                    pass
        if last_exc:
            raise last_exc

    def fetchone(self, query, params=None, retries=3, delay=2):
        """Execute a SELECT query and return a single row (or None)."""
        last_exc = None
        for attempt in range(retries):
            connection = self.connect()
            cursor = connection.cursor()
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                row = cursor.fetchone()
                return row
            except pyodbc.Error as e:
                last_exc = e
                if "locked" in str(e).lower():
                    if attempt < retries - 1:
                        time.sleep(delay)
                        continue
                    else:
                        raise
                else:
                    raise
            finally:
                try:
                    cursor.close()
                except Exception:
                    pass
                try:
                    connection.close()
                except Exception:
                    pass
        if last_exc:
            raise last_exc

    def close(self):
        """Close any existing database connection."""
        if hasattr(self, 'connection') and self.connection:
            try:
                self.connection.close()
                self.connection = None
            except Exception:
                pass