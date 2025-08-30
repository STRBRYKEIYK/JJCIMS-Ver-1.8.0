import os
import sys
from pathlib import Path


def resolve_db_path(explicit: str | None = None, filename: str = 'JJCIMS.accdb') -> str:
    """Resolve the canonical path to the Access database file.

    Search Order (first existing path wins):
      1. explicit argument (if provided and exists)
      2. env var JJCIMS_DB (must exist)
      3. PyInstaller runtime extraction dir (sys._MEIPASS)/database/<filename>
      4. Directory of the executable (PyInstaller) /database/<filename>
      5. Directory of the executable (PyInstaller) /<filename>
      6. utils.helpers.get_app_dir()/database/<filename> (if callable & exists)
      7. Module's parent directory (this file)/<filename>
      8. Module's parent directory /database/<filename>
      9. Upward directory search from CWD for a 'database/<filename>' or '<filename>'

    If none of the candidates exist, the final fallback returned is the module
    local database/<filename> (it may not yet exist).
    """
    candidates: list[Path] = []

    def _add(path_like):
        try:
            if path_like:
                candidates.append(Path(path_like))
        except Exception:
            pass

    # 1 explicit
    _add(explicit)
    # 2 env var
    _add(os.environ.get('JJCIMS_DB'))

    # 3-5 PyInstaller contexts
    meipass = getattr(sys, '_MEIPASS', None)  # type: ignore[attr-defined]
    if meipass:
        _add(Path(meipass) / 'database' / filename)
    exe_dir = None
    if getattr(sys, 'frozen', False):  # bundled
        try:
            exe_dir = Path(sys.executable).parent
            _add(exe_dir / 'database' / filename)
            _add(exe_dir / filename)
        except Exception:
            pass

    # 6 helpers.get_app_dir
    try:
        from utils.helpers import get_app_dir  # type: ignore
        app_dir = get_app_dir()
        _add(Path(app_dir) / 'database' / filename)
    except Exception:
        pass

    # 7 / 8 local module directory
    here = Path(__file__).parent
    _add(here / filename)
    _add(here / 'database' / filename)

    # 9 upward search from cwd (limit depth to avoid long scans)
    try:
        cwd = Path.cwd()
        for parent in [cwd, *cwd.parents][:8]:  # up to 8 levels
            _add(parent / 'database' / filename)
            _add(parent / filename)
    except Exception:
        pass

    # Return first existing
    for p in candidates:
        try:
            if p and p.exists() and p.is_file():
                return str(p)
        except Exception:
            continue

    # Fallback (do not guarantee existence)
    return str(here / 'database' / filename)


def get_db_path() -> str:
    """Public helper for other modules to obtain the resolved DB path."""
    return resolve_db_path()
