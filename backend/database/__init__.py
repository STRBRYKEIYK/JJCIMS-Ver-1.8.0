from .access_connector import AccessConnector
from .path_utils import get_db_path as _internal_get_db_path


def get_connector(db_path=None):
  """Return a connector instance.
  Behavior: always return AccessConnector which connects to the local Access DB file.
  """
  return AccessConnector(db_path)


def get_db_path():
  """Return resolved JJCIMS.accdb path without opening a connection."""
  return _internal_get_db_path()
