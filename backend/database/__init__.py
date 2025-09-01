from .access_connector import AccessConnector
from .path_utils import get_db_path as _internal_get_db_path
import os

# Try to import the MySQL connector, but don't fail if it's not available
try:
    from .mysql_connector import MySQLConnector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

# Determine which database connector to use based on environment variable
DB_TYPE = os.environ.get("JJCIMS_DB_TYPE", "access").lower()

def get_connector(db_path=None):
    """Return a connector instance.
    Behavior based on JJCIMS_DB_TYPE environment variable:
    - "access": return AccessConnector which connects to the local Access DB file
    - "mysql": return MySQLConnector which connects to the MySQL database via FastAPI
    """
    if DB_TYPE == "mysql" and MYSQL_AVAILABLE:
        return MySQLConnector()
    else:
        return AccessConnector(db_path)

def get_db_path():
    """Return resolved JJCIMS.accdb path without opening a connection."""
    return _internal_get_db_path()
