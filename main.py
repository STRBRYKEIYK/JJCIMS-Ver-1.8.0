import os
import sys
import shutil
from pathlib import Path

# Add the 'src' directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent))
sys.path.append(str(Path(__file__).resolve().parent / "backend"))
sys.path.append(str(Path(__file__).resolve().parent / "frontend"))

from frontend.gui.employee_login import WelcomeWindow
from backend.utils.helpers import get_app_dir
from backend.database import get_db_path


def extract_resource(resource_name, target_path):
    """Extract a resource file to the target path if it doesn't already exist."""
    if not os.path.exists(target_path):
        # Get the resource path (for PyInstaller)
        if getattr(sys, "frozen", False):  # Running as an executable
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        resource_path = os.path.join(base_path, resource_name)
        shutil.copy(resource_path, target_path)


# logs.xlsx is no longer used; logs are stored inside the Access DB (JJCIMS.accdb)


def preload_windows():
    """Preload heavy window classes in the background for faster user experience."""
    try:
        from frontend.gui.admin_dashboard import AdminDashboard
        from frontend.gui.employee_dashboard import MainBrowser
        from frontend.gui.admin_login import AdminLogin
        from frontend.gui.employee_login import WelcomeWindow
        from frontend.gui.functions.admdash_f.tfas import admin_2fa
        from frontend.gui.functions.admdash_f.tfas import setup_2fa_utils
        from frontend.gui.functions.admdash_f.ML import add_items
        from frontend.gui.functions.admdash_f.ML import update_items
        from frontend.gui.functions.emplydash_f import checkout_win
        from frontend.gui.functions.admdash_f.integrated_adm_sett import (
            IntegratedAdminSettings,
        )
        from frontend.gui.functions.admdash_f.tfas.tfa_su_wizard import (
            MultiStep2FAWizard,
        )

        # Instantiate but do not show windows (do not call .mainloop() or .run())
        _ = AdminDashboard
        _ = MainBrowser
        _ = AdminLogin
        _ = WelcomeWindow
        _ = admin_2fa
        _ = setup_2fa_utils
        _ = add_items
        _ = update_items
        _ = checkout_win
        _ = IntegratedAdminSettings
        _ = MultiStep2FAWizard
    except Exception as e:
        print(f"[Preload] Error preloading windows: {e}")


# Define paths for the database and log file
app_dir = get_app_dir()
db_file_path = get_db_path()
# Additional important paths
employee_list_db_path = get_db_path()
gui_fernet_key_path = os.path.join(
    app_dir, "frontend", "gui", "config", "fernet_key.py"
)
config_fernet_key_path = os.path.join(app_dir, "backend", "config", "fernet_key.py")

# Ensure the database and log file are in the application directory
os.makedirs(os.path.join(app_dir, "backend", "database"), exist_ok=True)
extract_resource("backend/database/JJCIMS.accdb", db_file_path)

# Ensure the JJCIMS(2).ico file is available in the application directory
main_icon_path = os.path.join(app_dir, "JJCIMS(2).ico")
extract_resource("JJCIMS(2).ico", main_icon_path)
# logs.xlsx no longer required; logs are now kept in the Access DB

if __name__ == "__main__":
    # Initialize and start the main application directly
    try:
        print("Starting JJCIMS application...")
        print(f"Python version: {sys.version}")
        print(f"Current directory: {os.getcwd()}")
        print(f"Database path: {get_db_path()}")
        
        app = WelcomeWindow()
        app.run()
    except Exception as e:
        import traceback
        print(f"Error starting main application: {e}")
        print("Detailed traceback:")
        traceback.print_exc()
