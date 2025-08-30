import os
import importlib.util
import pyodbc
import pyotp
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from cryptography.fernet import Fernet
from backend.database import get_db_path

# Import all the functional components from the original admin settings
from .backup_restore_section import BackupRestoreSection
from .user_roles_manager import UserRolesManager
from .about_section import create_about_section
from backend.utils.window_icon import set_window_icon
from .account_settings_wizard import AccountSettingsWizard


class IntegratedAdminSettings:
    """
    Integrated Admin Settings that uses the adm_sett_ui design
    with complete functional implementation

    UI Layout: Based on adm_sett_ui.py
    Assets: Uses assets/sett_assets directory
    Functionality: Complete admin settings functionality
    """

    OUTPUT_PATH = Path(__file__).parent
    ASSETS_PATH = OUTPUT_PATH.parents[2] / "assets" / "sett_assets"

    @staticmethod
    def relative_to_assets(path: str) -> Path:
        return IntegratedAdminSettings.ASSETS_PATH / Path(path)

    def __init__(self, parent):
        self.parent = parent
        self.assets_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../assets/sett_assets")
        )
        self.secret_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), "../../../config/admin_otp_secret.txt"
            )
        )

        # Bypass 2FA/secret check if username is 'bypass'
        if (
            hasattr(parent, "username")
            and getattr(parent, "username", "").lower() == "bypass"
        ):
            self.otp_secret = None
        else:
            self.otp_secret = self.get_or_create_otp_secret()

        self.settings_win = None
        self.active_section = None
        self.section_frames = {}
        self.user_roles_manager = None
        self.tfa_wizard = None  # Initialize 2FA wizard attribute

        # UI Components
        self.canvas = None
        self.content_frame = None

        # Button images
        self.button_images = {}

    def get_or_create_otp_secret(self):
        """Get or create OTP secret for 2FA"""
        config_dir = os.path.dirname(self.secret_path)
        os.makedirs(config_dir, exist_ok=True)
        if os.path.exists(self.secret_path):
            with open(self.secret_path, "r") as f:
                return f.read().strip()
        else:
            secret = pyotp.random_base32()
            with open(self.secret_path, "w") as f:
                f.write(secret)
            return secret

    def show_settings(self):
        """Main method to show the settings window with adm_sett_ui design and functionality"""
        if self.settings_win and self.settings_win.winfo_exists():
            # Bring to front and focus if already open
            try:
                self.settings_win.deiconify()
                self.settings_win.lift()
                self.settings_win.focus_force()
                # Topmost trick to ensure focus on Windows, then revert
                self.settings_win.attributes("-topmost", True)
                self.settings_win.after(
                    200,
                    lambda: self.settings_win.attributes("-topmost", False)
                    if self.settings_win and self.settings_win.winfo_exists()
                    else None,
                )
            except Exception:
                pass
            return

        self.settings_win = tk.Toplevel(self.parent.root)
        self.settings_win.title("Admin Settings - JJCIMS VER 1.6.0")
        self.settings_win.geometry("1400x1000")
        self.settings_win.configure(bg="#FFFFFF")

        # Set consistent window icon
        set_window_icon(self.settings_win)

        # Create the main canvas
        self.canvas = tk.Canvas(
            self.settings_win,
            bg="#FFFFFF",
            height=1000,
            width=1400,
            bd=0,
            highlightthickness=0,
            relief="ridge",
        )
        self.canvas.place(x=0, y=0)

        # Create the main panels (matching adm_sett_ui layout)
        self.nav_panel = self.canvas.create_rectangle(
            0.0, 0.0, 1400.0, 159.0, fill="#800000", outline=""
        )

        self.content_panel = self.canvas.create_rectangle(
            0.0, 159.0, 1400.0, 1000.0, fill="#000000", outline=""
        )

        # Create content frame for sections
        self.content_frame = tk.Frame(self.settings_win, bg="#000000")
        self.content_frame.place(x=0, y=159, width=1400, height=841)

        # Add user info and logo
        self.add_user_info()

        # Load button images and create navigation buttons
        self.create_navigation_buttons()

        # Initialize all content sections
        self.initialize_content_sections()

        # Show default section (Account Settings)
        self.show_account_settings()

        self.settings_win.resizable(False, False)

        # Auto-focus the settings window when it opens
        try:
            self.settings_win.transient(self.parent.root)
        except Exception:
            pass
        try:
            self.settings_win.deiconify()
            self.settings_win.lift()
            self.settings_win.focus_force()
            # Use a short delay to reinforce focus after layout settles
            self.settings_win.after(
                100,
                lambda: self.settings_win.focus_force()
                if self.settings_win and self.settings_win.winfo_exists()
                else None,
            )
            # Briefly set topmost to guarantee focus, then revert
            self.settings_win.attributes("-topmost", True)
            self.settings_win.after(
                250,
                lambda: self.settings_win.attributes("-topmost", False)
                if self.settings_win and self.settings_win.winfo_exists()
                else None,
            )
        except Exception:
            pass

    def create_navigation_buttons(self):
        """Create the navigation buttons with adm_sett_ui layout and functionality"""
        try:
            # Button configurations matching adm_sett_ui.py layout
            button_configs = [
                {
                    "image": "button_1.png",
                    "x": 1276.0,
                    "y": 104.0,
                    "width": 94.0,
                    "height": 30.0,
                    "command": self.show_about,
                },  # About
                {
                    "image": "button_2.png",
                    "x": 1080.0,
                    "y": 104.0,
                    "width": 180.0,
                    "height": 30.0,
                    "command": self.show_backup_restore_section,
                },  # Backup/Restore
                {
                    "image": "button_3.png",
                    "x": 902.0,
                    "y": 104.0,
                    "width": 162.0,
                    "height": 30.0,
                    "command": self.show_import_export,
                },  # Import/Export
                {
                    "image": "button_4.png",
                    "x": 301.0,
                    "y": 106.0,
                    "width": 130.0,
                    "height": 30.0,
                    "command": self.show_user_roles,
                },  # User Roles
                {
                    "image": "button_5.png",
                    "x": 159.0,
                    "y": 106.0,
                    "width": 126.0,
                    "height": 30.0,
                    "command": self.show_2fa_section,
                },  # Setup 2FA
                {
                    "image": "button_6.png",
                    "x": 30.0,
                    "y": 106.0,
                    "width": 113.0,
                    "height": 30.0,
                    "command": self.show_account_settings,
                },  # Account Settings
            ]

            self.button_positions = {
                1: (1276.0, 104.0, 94.0, 30.0),  # About
                2: (1080.0, 104.0, 180.0, 30.0),  # Backup/Restore
                3: (902.0, 104.0, 162.0, 30.0),  # Import/Export
                4: (301.0, 106.0, 130.0, 30.0),  # User Roles
                5: (159.0, 106.0, 126.0, 30.0),  # Setup 2FA
                6: (30.0, 106.0, 113.0, 30.0),  # Account Settings
            }

            self.selected_button = None
            self.underline_id = None

            for i, config in enumerate(button_configs):
                try:
                    image_path = self.relative_to_assets(config["image"])
                    if os.path.exists(image_path):
                        button_image = tk.PhotoImage(file=image_path)
                        self.button_images[f"button_{i + 1}"] = button_image

                        button_num = i + 1
                        button = tk.Button(
                            self.settings_win,
                            image=button_image,
                            borderwidth=0,
                            highlightthickness=0,
                            bg="#800000",
                            activebackground="#800000",
                            command=lambda cmd=config["command"], btn=button_num: [
                                cmd(),
                                self.select_button(btn),
                            ],
                            relief="flat",
                        )

                        button.place(
                            x=config["x"],
                            y=config["y"],
                            width=config["width"],
                            height=config["height"],
                        )

                except Exception as e:
                    print(f"Failed to load button image {config['image']}: {e}")
                    # Create text button as fallback
                    button_names = [
                        "About",
                        "Backup/Restore",
                        "Import/Export",
                        "User Roles",
                        "Setup 2FA",
                        "Account Settings",
                    ]
                    button_text = button_names[i]
                    button = tk.Button(
                        self.settings_win,
                        text=button_text,
                        borderwidth=0,
                        highlightthickness=0,
                        bg="#800000",
                        fg="#FFFFFF",
                        activebackground="#A44E4E",
                        command=config["command"],
                        relief="flat",
                        font=("Segoe UI", 10, "bold"),
                    )
                    button.place(
                        x=config["x"],
                        y=config["y"],
                        width=config["width"],
                        height=config["height"],
                    )

            # Select Account Settings button (button_6) by default
            self.select_button(6)

        except Exception as e:
            print(f"Error creating navigation buttons: {e}")

    def select_button(self, btn_num):
        """Select a button and show underline indicator"""
        self.selected_button = btn_num
        # Remove previous underline
        if hasattr(self, "underline_id") and self.underline_id is not None:
            self.canvas.delete(self.underline_id)
        # Draw new underline
        if hasattr(self, "button_positions") and btn_num in self.button_positions:
            x, y, w, h = self.button_positions[btn_num]
            self.underline_id = self.canvas.create_rectangle(
                x, y + h + 20, x + w, y + h + 23, fill="#FFFFFF", outline=""
            )

    # Removed create_window_controls and related window control buttons

    def add_user_info(self):
        """Add user information and logo to the header (adm_sett_ui layout)"""
        try:
            # Add logo images first (same order as adm_sett_ui.py)
            logo1_path = self.relative_to_assets("image_1.png")
            if os.path.exists(logo1_path):
                self.image_image_1 = tk.PhotoImage(file=logo1_path)
                self.canvas.create_image(75.0, 58.0, image=self.image_image_1)

            # User greeting - positioned like in adm_sett_ui with placeholder format
            # Create AFTER image_1 to ensure it appears on top
            username = getattr(self.parent, "username", "USERNAME")
            self.canvas.create_text(
                12.0,
                43.0,
                anchor="nw",
                text=f"Hi, {username}",
                fill="#FFFFFF",
                font=("Inter SemiBoldItalic", 16, "italic", "bold"),
            )

            # Add second logo image
            logo2_path = self.relative_to_assets("image_2.png")
            if os.path.exists(logo2_path):
                self.image_image_2 = tk.PhotoImage(file=logo2_path)
                self.canvas.create_image(666.0, 90.0, image=self.image_image_2)

        except Exception as e:
            print(f"Error adding user info: {e}")

    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        try:
            current_state = self.settings_win.attributes("-fullscreen")
            if current_state:
                self.settings_win.attributes("-fullscreen", False)
                self.settings_win.geometry("1400x1000")
            else:
                self.settings_win.attributes("-fullscreen", True)
        except Exception as e:
            print(f"Error toggling fullscreen: {e}")

    def initialize_content_sections(self):
        """Initialize all content section frames"""
        self.section_frames = {
            "Account Settings": self.create_account_settings(self.content_frame),
            "Import / Export": self.create_import_export(self.content_frame),
            "Setup 2FA": self.create_2fa_section(self.content_frame),
            "User Roles": self.create_user_roles(self.content_frame),
            "Backup / Restore": self.create_backup_restore_section(self.content_frame),
            "About": self.create_about(self.content_frame),
        }

    def switch_to_section(self, section_name):
        """Switch to a specific section"""
        # Hide all frames
        for frame in self.section_frames.values():
            frame.pack_forget()

        # Show selected frame
        if section_name in self.section_frames:
            frame = self.section_frames[section_name]
            frame.pack(fill="both", expand=True)

    # ==================== FUNCTIONAL METHODS FROM ORIGINAL ADM_SETT.PY ====================

    def create_account_settings(self, parent):
        """Create upgraded multi-step Account Settings wizard section."""
        frame = tk.Frame(parent, bg="#000000")
        self.account_wizard = AccountSettingsWizard(frame, self)
        self.account_wizard.show()
        return frame

    def show_account_settings(self):
        """Show multi-step wizard account settings section."""
        self.switch_to_section("Account Settings")
        if hasattr(self, "account_wizard"):
            # Ensure data loaded
            if not self.account_wizard._loaded:
                self.account_wizard.load_user_data()
            self.account_wizard.show_step(0)

    def toggle_password(self):
        """Toggle password visibility"""
        if self.show_password:
            self.password_entry.config(show="\u2022")
            self.show_btn.config(text="Show")
            self.show_password = False
        else:
            self.password_entry.config(show="")
            self.show_btn.config(text="Hide")
            self.show_password = True

    def enable_edit(self):
        """Enable editing of account settings"""
        for entry in [
            self.first_name_entry,
            self.last_name_entry,
            self.username_entry,
            self.password_entry,
        ]:
            entry.config(state="normal")
        self.show_btn.config(state="normal")
        self.save_btn.config(state="normal")
        self.cancel_btn.config(state="normal")
        self.edit_btn.config(state="disabled")
        self.password_entry.config(show="*")
        self.show_password = False

    def cancel_edit(self):
        """Cancel editing and reload original data"""
        self.show_account_settings()
        for entry in [
            self.first_name_entry,
            self.last_name_entry,
            self.username_entry,
            self.password_entry,
        ]:
            entry.config(state="readonly")
        self.show_btn.config(state="normal")
        self.save_btn.config(state="disabled")
        self.cancel_btn.config(state="disabled")
        self.edit_btn.config(state="normal")

    def save_account_settings(self):
        """Save account settings changes"""
        try:
            # Get values from entries
            first_name = self.first_name_entry.get().strip()
            last_name = self.last_name_entry.get().strip()
            username = self.username_entry.get().strip()
            password = self.password_var.get().strip()

            # Validate inputs
            if not all([first_name, last_name, username, password]):
                messagebox.showerror("Error", "All fields are required.")
                return

            # Database connection
            db_path = get_db_path()
            key_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../../config/fernet_key.py")
            )

            conn_str = (
                r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
                f"DBQ={db_path};"
            )

            # Encrypt password
            spec = importlib.util.spec_from_file_location("fernet_key", key_path)
            fernet_key_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(fernet_key_mod)
            key = fernet_key_mod.FERNET_KEY
            fernet = Fernet(key)
            encrypted_password = fernet.encrypt(password.encode()).decode()

            # Update database
            original_username = getattr(self.parent, "username", username)
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE [Emp_list] 
                SET [First Name]=?, [Last Name]=?, [Username]=?, [Password]=? 
                WHERE [Username]=?
            """,
                (
                    first_name,
                    last_name,
                    username,
                    encrypted_password,
                    original_username,
                ),
            )

            conn.commit()
            cursor.close()
            conn.close()

            # Update parent username if changed
            if hasattr(self.parent, "username"):
                self.parent.username = username

            messagebox.showinfo("Success", "Account settings saved successfully!")
            self.show_account_settings()  # Reload data

        except Exception as e:
            print(f"Error saving account settings: {e}")
            messagebox.showerror("Error", f"Failed to save account settings: {e}")

    def create_import_export(self, parent):
        """Create Import/Export section using the enhanced ImportExport UI (i&e_section.py)."""
        container = tk.Frame(parent, bg="#000000")
        # Try to dynamically load the module despite the special character in filename.
        try:
            import importlib.util
            import traceback

            module_path = Path(__file__).parent / "i&e_section.py"
            if module_path.exists():
                spec = importlib.util.spec_from_file_location(
                    "admin_import_export_section", module_path
                )
                mod = importlib.util.module_from_spec(spec)  # type: ignore
                try:
                    spec.loader.exec_module(mod)  # type: ignore
                    # Prefer factory if provided
                    if hasattr(mod, "create_import_export_frame"):
                        self.import_export_view = mod.create_import_export_frame(
                            container
                        )
                    elif hasattr(mod, "ImportExport"):
                        self.import_export_view = mod.ImportExport(container)
                    else:
                        raise AttributeError(
                            "No ImportExport class or factory found in i&e_section.py"
                        )
                    self.import_export_view.pack(fill="both", expand=True)
                except Exception as inner_e:
                    traceback.print_exc()
                    self._build_import_export_fallback(
                        container,
                        f"Failed loading enhanced Import/Export UI: {inner_e}",
                    )
            else:
                self._build_import_export_fallback(
                    container, "Enhanced Import/Export file not found."
                )
        except Exception as e:
            self._build_import_export_fallback(
                container, f"Error initializing enhanced Import/Export UI: {e}"
            )
        return container

    def _build_import_export_fallback(self, frame, error_msg=None):
        """Fallback simple button-based Import/Export UI (previous implementation)."""
        tk.Label(
            frame,
            text="Import / Export",
            font=("Segoe UI", 15, "bold"),
            bg="#000000",
            fg="#fffde7",
        ).pack(anchor="w", pady=(18, 8), padx=18)
        if error_msg:
            tk.Label(
                frame,
                text=error_msg,
                font=("Segoe UI", 10),
                bg="#000000",
                fg="#ff6f00",
                wraplength=800,
                justify="left",
            ).pack(anchor="w", padx=18, pady=(0, 10))
        btn_frame = tk.Frame(frame, bg="#000000")
        btn_frame.pack(pady=18)
        tk.Button(
            btn_frame,
            text="Import Database",
            command=self.import_database,
            font=("Segoe UI", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            relief="flat",
            width=16,
        ).pack(side=tk.LEFT, padx=10)
        tk.Button(
            btn_frame,
            text="Export Database",
            command=self.export_database,
            font=("Segoe UI", 12, "bold"),
            bg="#FF9800",
            fg="white",
            relief="flat",
            width=16,
        ).pack(side=tk.LEFT, padx=10)
        tk.Button(
            btn_frame,
            text="Import Logs",
            command=self.import_logs,
            font=("Segoe UI", 12, "bold"),
            bg="#9C27B0",
            fg="white",
            relief="flat",
            width=16,
        ).pack(side=tk.LEFT, padx=10)
        tk.Button(
            btn_frame,
            text="Export Logs",
            command=self.export_logs,
            font=("Segoe UI", 12, "bold"),
            bg="#2196F3",
            fg="white",
            relief="flat",
            width=16,
        ).pack(side=tk.LEFT, padx=10)

    def show_import_export(self):
        """Show Import/Export section"""
        self.switch_to_section("Import / Export")

    def import_database(self):
        """Import database from file"""
        try:
            from tkinter import filedialog
            import shutil

            source_file = filedialog.askopenfilename(
                title="Select Database File to Import",
                filetypes=[("Access Database", "*.accdb"), ("All files", "*.*")],
            )

            if source_file:
                if messagebox.askyesno(
                    "Confirm Import",
                    "This will replace the current database.\n"
                    "Are you sure you want to continue?",
                ):
                    target_db = get_db_path()
                    backup_db = target_db + ".backup"

                    # Backup current database
                    shutil.copy2(target_db, backup_db)

                    # Import new database
                    shutil.copy2(source_file, target_db)

                    messagebox.showinfo("Success", "Database imported successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to import database: {e}")

    def export_database(self):
        """Export database to file"""
        try:
            from tkinter import filedialog
            import shutil
            from datetime import datetime

            target_file = filedialog.asksaveasfilename(
                title="Export Database As",
                defaultextension=".accdb",
                filetypes=[("Access Database", "*.accdb"), ("All files", "*.*")],
                initialname=f"JJCIMS_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.accdb",
            )

            if target_file:
                source_db = get_db_path()
                shutil.copy2(source_db, target_file)
                messagebox.showinfo(
                    "Success", f"Database exported successfully!\n{target_file}"
                )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export database: {e}")

    def import_logs(self):
        """Import logs from Excel file into database tables"""
        try:
            from tkinter import filedialog
            from backend.database import get_connector
            import pandas as pd

            source_file = filedialog.askopenfilename(
                title="Select Logs File to Import",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            )

            if source_file:
                if messagebox.askyesno(
                    "Confirm Import",
                    "This will replace the current logs in the database.\n"
                    "Are you sure you want to continue?",
                ):
                    try:
                        # Read Excel file
                        df = pd.read_excel(source_file, sheet_name=None)

                        # Get database connection
                        conn = get_connector()
                        cursor = conn.cursor()

                        # Clear existing logs
                        cursor.execute("DELETE FROM adm_logs")
                        cursor.execute("DELETE FROM emp_logs")

                        # Import admin logs
                        if "admin" in df:
                            admin_logs = df["admin"]
                            for _, row in admin_logs.iterrows():
                                cursor.execute(
                                    """
                                    INSERT INTO adm_logs (timestamp, action, details, ip_address)
                                    VALUES (?, ?, ?, ?)
                                """,
                                    (
                                        str(row.get("timestamp", "")),
                                        str(row.get("action", "")),
                                        str(row.get("details", "")),
                                        str(row.get("ip_address", "")),
                                    ),
                                )

                        # Import employee logs
                        if "employees" in df:
                            emp_logs = df["employees"]
                            for _, row in emp_logs.iterrows():
                                cursor.execute(
                                    """
                                    INSERT INTO emp_logs (timestamp, action, details, ip_address, employee_id)
                                    VALUES (?, ?, ?, ?, ?)
                                """,
                                    (
                                        str(row.get("timestamp", "")),
                                        str(row.get("action", "")),
                                        str(row.get("details", "")),
                                        str(row.get("ip_address", "")),
                                        str(row.get("employee_id", "")),
                                    ),
                                )

                        conn.commit()
                        messagebox.showinfo("Success", "Logs imported successfully!")

                    except Exception as e:
                        conn.rollback()
                        raise e
                    finally:
                        conn.close()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to import logs: {e}")

    def export_logs(self):
        """Export logs from database tables to Excel file"""
        try:
            from tkinter import filedialog
            from backend.database import get_connector
            from datetime import datetime
            import pandas as pd

            target_file = filedialog.asksaveasfilename(
                title="Export Logs As",
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialname=f"JJCIMS_Logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            )

            if target_file:
                try:
                    # Get database connection
                    conn = get_connector()
                    cursor = conn.cursor()

                    # Export admin logs
                    cursor.execute("SELECT * FROM adm_logs")
                    admin_columns = [desc[0] for desc in cursor.description]
                    admin_data = cursor.fetchall()

                    # Export employee logs
                    cursor.execute("SELECT * FROM emp_logs")
                    emp_columns = [desc[0] for desc in cursor.description]
                    emp_data = cursor.fetchall()

                    # Create Excel file with multiple sheets
                    with pd.ExcelWriter(target_file, engine="openpyxl") as writer:
                        if admin_data:
                            admin_df = pd.DataFrame(admin_data, columns=admin_columns)
                            admin_df.to_excel(writer, sheet_name="admin", index=False)

                        if emp_data:
                            emp_df = pd.DataFrame(emp_data, columns=emp_columns)
                            emp_df.to_excel(writer, sheet_name="employees", index=False)

                    messagebox.showinfo(
                        "Success", f"Logs exported successfully!\n{target_file}"
                    )

                except Exception as e:
                    raise e
                finally:
                    conn.close()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export logs: {e}")

    def create_2fa_section(self, parent):
        """Create 2FA Setup section with embedded wizard"""
        frame = tk.Frame(parent, bg="#000000")

        try:
            # Import the 2FA wizard
            from .tfas.tfa_su_sett import create_2fa_setup_frame

            # Get current username
            username = getattr(self.parent, "username", None)

            # Database and key paths
            db_path = get_db_path()
            fernet_key_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../../config/fernet_key.py")
            )

            # Color settings to match admin settings theme
            colors = {"bg": "#000000", "header": "#800000"}

            # Create the embedded 2FA wizard
            self.tfa_wizard = create_2fa_setup_frame(
                parent=frame,
                username=username,
                db_path=db_path,
                fernet_key_path=fernet_key_path,
                colors=colors,
            )

        except Exception as e:
            print(f"Error creating 2FA wizard: {e}")
            # Fallback UI if wizard fails to load
            container = tk.Frame(frame, bg="#000000")
            container.pack(fill="both", expand=True)

            title_frame = tk.Frame(container, bg="#000000")
            title_frame.pack(fill="x", pady=(50, 20))
            tk.Label(
                title_frame,
                text="Setup 2FA",
                font=("Segoe UI", 15, "bold"),
                bg="#000000",
                fg="#fffde7",
            ).pack()

            error_frame = tk.Frame(container, bg="#000000")
            error_frame.pack(fill="x", pady=20)
            tk.Label(
                error_frame,
                text=f"Error loading 2FA wizard: {str(e)}",
                font=("Segoe UI", 12),
                bg="#000000",
                fg="#ff6f00",
            ).pack()

        return frame

    def show_2fa_section(self):
        """Show 2FA Setup section with embedded wizard"""
        self.switch_to_section("Setup 2FA")

        try:
            # Ensure the wizard is properly initialized
            if hasattr(self, "tfa_wizard") and self.tfa_wizard:
                # Reset to first step if needed
                if hasattr(self.tfa_wizard, "show_step"):
                    self.tfa_wizard.show_step(1)
                elif hasattr(self.tfa_wizard, "navigate_to_step"):
                    self.tfa_wizard.navigate_to_step(1)
            else:
                # If the wizard doesn't exist, create it
                from .tfas.tfa_su_sett import create_2fa_setup_frame

                # Get current username
                username = getattr(self.parent, "username", None)

                # Get the content section frame
                content_frame = self.section_frames.get("Setup 2FA")
                if content_frame:
                    # Database and key paths - using the correct path to Employee List.accdb
                    db_path = get_db_path()
                    fernet_key_path = os.path.abspath(
                        os.path.join(
                            os.path.dirname(__file__), "../../../config/fernet_key.py"
                        )
                    )

                    # Color settings to match admin settings theme
                    colors = {"bg": "#000000", "header": "#800000"}

                    # Create the embedded 2FA wizard
                    self.tfa_wizard = create_2fa_setup_frame(
                        parent=content_frame,
                        username=username,
                        db_path=db_path,
                        fernet_key_path=fernet_key_path,
                        colors=colors,
                    )
        except Exception as e:
            print(f"Error showing 2FA section: {e}")

    def create_user_roles(self, parent):
        """Create User Roles section"""
        self.user_roles_manager = UserRolesManager(self, self.settings_win)
        return self.user_roles_manager.create_user_roles_frame(parent)

    def show_user_roles(self):
        """Show User Roles section"""
        self.switch_to_section("User Roles")
        if self.user_roles_manager:
            self.user_roles_manager.load_user_data()  # Use correct method name

    def create_backup_restore_section(self, parent):
        """Create Backup/Restore section"""
        frame = tk.Frame(parent, bg="#000000")

        try:
            assets_backup = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__), "../../../assets/bnr_assets/bu_assets"
                )
            )
            assets_restore = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__), "../../../assets/bnr_assets/r_assets"
                )
            )

            # Create the BackupRestoreSection and pack it to fill the frame
            backup_restore_section = BackupRestoreSection(
                frame, assets_backup, assets_restore
            )
            backup_restore_section.pack(fill="both", expand=True)

        except Exception as e:
            print(f"Error creating BackupRestoreSection: {e}")
            # Fallback UI if BackupRestoreSection fails
            container = tk.Frame(frame, bg="#000000")
            container.pack(fill="both", expand=True)

            title_label = tk.Label(
                container,
                text="Backup / Restore",
                font=("Segoe UI", 15, "bold"),
                bg="#000000",
                fg="#fffde7",
            )
            title_label.pack(pady=(20, 10))

            error_label = tk.Label(
                container,
                text=f"Error loading backup/restore interface:\n{str(e)}",
                font=("Segoe UI", 11),
                bg="#000000",
                fg="#ff6f00",
            )
            error_label.pack(pady=10)

            # Create simple backup/restore buttons as fallback
            btn_frame = tk.Frame(container, bg="#000000")
            btn_frame.pack(pady=20)

            backup_btn = tk.Button(
                btn_frame,
                text="Create Backup",
                font=("Segoe UI", 12, "bold"),
                bg="#4CAF50",
                fg="white",
                relief="flat",
                width=16,
                command=self.create_backup_fallback,
            )
            backup_btn.pack(side=tk.LEFT, padx=10)

            restore_btn = tk.Button(
                btn_frame,
                text="Restore Backup",
                font=("Segoe UI", 12, "bold"),
                bg="#FF9800",
                fg="white",
                relief="flat",
                width=16,
                command=self.restore_backup_fallback,
            )
            restore_btn.pack(side=tk.LEFT, padx=10)

        return frame

    def show_backup_restore_section(self):
        """Show Backup/Restore section"""
        self.switch_to_section("Backup / Restore")

    def create_backup_fallback(self):
        """Create a backup of the database (fallback method)"""
        try:
            from tkinter import filedialog
            import shutil
            from datetime import datetime

            # Get backup location
            backup_file = filedialog.asksaveasfilename(
                title="Save Backup As",
                defaultextension=".accdb",
                filetypes=[("Access Database", "*.accdb"), ("All files", "*.*")],
                initialname=f"JJCIMS_Backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.accdb",
            )

            if backup_file:
                # Source database path
                source_db = get_db_path()

                # Copy database
                shutil.copy2(source_db, backup_file)
                messagebox.showinfo(
                    "Success", f"Backup created successfully!\n{backup_file}"
                )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create backup: {e}")

    def restore_backup_fallback(self):
        """Restore database from backup (fallback method)"""
        try:
            from tkinter import filedialog
            import shutil

            # Get backup file
            backup_file = filedialog.askopenfilename(
                title="Select Backup File",
                filetypes=[("Access Database", "*.accdb"), ("All files", "*.*")],
            )

            if backup_file:
                # Confirm restore
                if messagebox.askyesno(
                    "Confirm Restore",
                    "This will replace the current database with the backup.\n"
                    "Are you sure you want to continue?",
                ):
                    # Target database path
                    target_db = get_db_path()

                    # Create backup of current database first
                    current_backup = target_db + ".backup"
                    shutil.copy2(target_db, current_backup)

                    # Restore from backup
                    shutil.copy2(backup_file, target_db)

                    messagebox.showinfo(
                        "Success",
                        "Database restored successfully!\n"
                        f"Previous database backed up as: {current_backup}",
                    )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to restore backup: {e}")

    def create_about(self, parent):
        """Create About section"""
        root_window = None
        try:
            root_window = self.settings_win
        except Exception:
            root_window = getattr(self.parent, "root", None)

        return create_about_section(parent, root_window)

    def show_about(self):
        """Show About section"""
        self.switch_to_section("About")


# For backward compatibility, you can also create an alias
AdminSettings = IntegratedAdminSettings
