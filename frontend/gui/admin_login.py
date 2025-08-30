import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
from backend.database import get_connector, get_db_path
from cryptography.fernet import Fernet
from .employee_login import WelcomeWindow
from backend.utils.window_icon import set_window_icon
from .admin_dashboard import AdminDashboard
from .functions.admdash_f.tfas.tfa_su_wizard import open_2fa_wizard_modal
from .functions.admdash_f.tfas.admin_2fa import Admin2FA
# Sound imports removed

# --- CONFIG ---
BG_COLOR = "#800000"
RIGHT_BG = "#000000"
FG_COLOR = "#E8C999"
ACCENT_COLOR = "#BF5F5F"  # soft red
ENTRY_BG = "#23272b"
BUTTON_BG = "#8E1616"
BUTTON_FG = "#E8C999"

# DB and Fernet key paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = get_db_path()
FERNET_KEY_PATH = os.path.abspath(os.path.join(BASE_DIR, "config", "fernet_key.py"))


def load_fernet_key():
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location("fernet_key", FERNET_KEY_PATH)
        fernet_key_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fernet_key_mod)
        if fernet_key_mod.FERNET_KEY and fernet_key_mod.FERNET_KEY != b"":
            return fernet_key_mod.FERNET_KEY
    except Exception as e:
        print(f"Error loading Fernet key: {e}")  # Log error for debugging
    key = Fernet.generate_key()
    with open(FERNET_KEY_PATH, "w") as f:
        f.write("# Fernet key for 2FA\nfrom cryptography.fernet import Fernet\n")
        f.write(f"FERNET_KEY = {repr(key)}\n")
    return key


FERNET_KEY = load_fernet_key()
fernet = Fernet(FERNET_KEY)


def create_text_image(text, font_size, is_bold=False):
    """Create simple text image without effects"""
    padding = 20  # Increased padding

    # Load font
    try:
        font_path = "C:\\Windows\\Fonts\\segoeui.ttf"  # Regular Segoe UI
        if is_bold:
            font_path = "C:\\Windows\\Fonts\\segoeuib.ttf"  # Bold Segoe UI
        font = ImageFont.truetype(font_path, font_size)
    except Exception:
        # Fallback to default
        font = ImageFont.load_default()

    # Create temporary image to calculate text size
    temp_img = Image.new("RGBA", (1000, 200), (0, 0, 0, 0))  # Larger temporary image
    temp_draw = ImageDraw.Draw(temp_img)
    text_bbox = temp_draw.textbbox((padding, padding), text, font=font)
    text_width = text_bbox[2] - text_bbox[0] + padding * 2  # Add padding to width
    text_height = text_bbox[3] - text_bbox[1] + padding * 2  # Add padding to height

    # Create actual image with correct size and some extra space
    img = Image.new(
        "RGBA", (text_width + 40, text_height + 20), (0, 0, 0, 0)
    )  # Added extra space
    draw = ImageDraw.Draw(img)

    # Draw text in white with proper centering
    draw_x = (img.width - text_width + padding * 2) // 2  # Center horizontally
    draw_y = (img.height - text_height + padding * 2) // 2  # Center vertically
    draw.text((draw_x, draw_y), text, font=font, fill=(255, 255, 255, 255))

    return ImageTk.PhotoImage(img)


class AdminLogin:
    def show_toast(self, message, duration=None, type="error"):
        """
        Show a toast notification with improved feedback:
        - type: 'success', 'error', 'info'
        - duration: ms (default 4000 for error/info, 6000 for success)
        - color: green for success, red for error, gold for info
        """
        # Remove any existing toast
        if hasattr(self, "_toast") and self._toast:
            self._toast.destroy()
        self._toast = tk.Toplevel(self.root)
        self._toast.overrideredirect(True)
        self._toast.attributes("-topmost", True)
        # Color and icon by type
        if type == "success":
            color = "#388e3c"
            icon = "✔"
            if duration is None:
                duration = 6000
        elif type == "info":
            color = "#FFD600"
            icon = "ℹ"
            if duration is None:
                duration = 5000
        else:
            color = "#b71c1c"
            icon = "✖"
            if duration is None:
                duration = 4000
        frame = tk.Frame(self._toast, bg=color)
        frame.pack(fill="both", expand=True)
        label = tk.Label(
            frame,
            text=f"{icon}  {message}",
            font=("Segoe UI", 14, "bold"),
            bg=color,
            fg="#fffde7",
            padx=20,
            pady=10,
        )
        label.pack()
        self._toast.update_idletasks()
        # Animation: slide in from right
        screen_width = self.root.winfo_screenwidth()
        toast_width = self._toast.winfo_width()
        margin = 30
        final_x = screen_width - toast_width - margin
        y = margin
        start_x = screen_width
        self._toast.geometry(f"+{start_x}+{y}")

        def animate(step=0):
            steps = 20
            delta = (final_x - start_x) // steps
            new_x = start_x + delta * step
            if new_x < final_x:
                new_x = final_x
            self._toast.geometry(f"+{new_x}+{y}")
            if step < steps:
                self._toast.after(10, lambda: animate(step + 1))

        animate()
        self._toast.after(duration, self._toast.destroy)

    def __init__(self, prefill_username=None):
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg=BG_COLOR)

        # Set window icon
        set_window_icon(self.root)

        self.attempts_remaining = 5
        self.open_dialogs = {}
        self.username = ""  # Store the username here
        self.prefill_username = prefill_username  # Store prefill_username if provided
        self.setup_ui()

    def setup_ui(self):
        left_panel = tk.Frame(self.root, bg=BG_COLOR, width=800)
        left_panel.pack(side="left", fill="y")
        left_panel_inner = tk.Frame(left_panel, bg=BG_COLOR)
        left_panel_inner.place(relx=0.5, rely=0.5, anchor="center")

        # Load and display the logo without scanline effect
        logo_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "assets", "adm_1.png")
        )
        original_img = Image.open(logo_path).resize(
            (750, 750), Image.Resampling.LANCZOS
        )
        self.logo_image = ImageTk.PhotoImage(original_img)

        logo_label = tk.Button(
            left_panel_inner,
            image=self.logo_image,
            bg=BG_COLOR,
            activebackground=BG_COLOR,  # Prevent white flash when clicking
            relief="flat",
            command=self.go_back_to_welcome,  # Add command to go back
            bd=0,
            highlightthickness=0,  # Remove focus highlight
            cursor="hand2",  # Add hand cursor to indicate it's clickable
        )
        logo_label.image = (
            self.logo_image
        )  # Keep a reference to avoid garbage collection
        logo_label.pack(pady=10)

        # Add a thin gold outline
        logo_label.config(highlightbackground="#ffd600", highlightthickness=2)

        # Add copyright label at the bottom center of the left panel
        copyright_label = tk.Label(
            left_panel,
            text="© 2025 JJC Inventory Management System made by Keith W. F.",
            font=("Arial", 10, "italic"),
            bg=BG_COLOR,
            fg=ACCENT_COLOR,
        )
        copyright_label.place(relx=0.5, rely=1.0, anchor="s", y=-5)

        # --- macOS-style window controls (top-left) ---
        control_frame = tk.Frame(left_panel, bg=BG_COLOR)
        control_frame.place(relx=0.012, rely=0.018, anchor="nw")

        # Helper for hover effect
        def on_enter(canvas, oval, color):
            canvas.itemconfig(oval, fill=color)

        def on_leave(canvas, oval, color):
            canvas.itemconfig(oval, fill=color)

        # Red (close)
        red_btn = tk.Canvas(
            control_frame, width=22, height=22, bg=BG_COLOR, highlightthickness=0, bd=0
        )
        red_btn.grid(row=0, column=0, padx=(0, 4))
        red_oval = red_btn.create_oval(
            3, 3, 19, 19, fill="#ff5f57", outline="#e33e41", width=1
        )
        red_btn.bind("<Button-1>", lambda e: self.root.destroy())
        red_btn.bind("<Enter>", lambda e: on_enter(red_btn, red_oval, "#e0483e"))
        red_btn.bind("<Leave>", lambda e: on_leave(red_btn, red_oval, "#ff5f57"))
        # Orange (minimize)
        yellow_btn = tk.Canvas(
            control_frame, width=22, height=22, bg=BG_COLOR, highlightthickness=0, bd=0
        )
        yellow_btn.grid(row=0, column=1, padx=(0, 4))
        yellow_oval = yellow_btn.create_oval(
            3, 3, 19, 19, fill="#FFBD2E", outline="#BF8E1E", width=1
        )
        yellow_btn.bind("<Button-1>", lambda e: self.root.iconify())
        yellow_btn.bind(
            "<Enter>", lambda e: on_enter(yellow_btn, yellow_oval, "#BF8E1E")
        )
        yellow_btn.bind(
            "<Leave>", lambda e: on_leave(yellow_btn, yellow_oval, "#FFBD2E")
        )

        # (Optional) Add tooltips for accessibility
        def add_tooltip(widget, text):
            tip = tk.Toplevel(widget)
            tip.withdraw()
            tip.overrideredirect(True)
            label = tk.Label(
                tip,
                text=text,
                bg="#000000",
                fg="#fffde7",
                font=("Arial", 9),
                padx=4,
                pady=2,
            )
            label.pack()

            def show(event):
                x = event.x_root + 10
                y = event.y_root + 5
                tip.geometry(f"+{x}+{y}")
                tip.deiconify()

            def hide(event):
                tip.withdraw()

            widget.bind("<Enter>", show)
            widget.bind("<Leave>", hide)

        add_tooltip(red_btn, "Close")
        add_tooltip(yellow_btn, "Minimize")
        right_panel = tk.Frame(self.root, bg=RIGHT_BG)
        right_panel.pack(side="right", fill="both", expand=True)
        right_inner = tk.Frame(right_panel, bg=RIGHT_BG)
        right_inner.place(relx=0.5, rely=0.5, anchor="center")

        # Create WELCOME TO JJCIMS text
        welcome_img = create_text_image("WELCOME TO JJCIMS", 40, is_bold=True)
        welcome_label = tk.Label(right_inner, image=welcome_img, bg=RIGHT_BG)
        welcome_label.image = welcome_img  # Keep reference
        welcome_label.pack(pady=20)

        # Create Username label
        username_img = create_text_image("Username:", 24, is_bold=True)
        username_label = tk.Label(right_inner, image=username_img, bg=RIGHT_BG)
        username_label.image = username_img  # Keep reference
        username_label.pack(pady=(10, 5))
        self.username_entry = tk.Entry(
            right_inner,
            font=("Segoe UI", 18),
            width=30,
            relief="solid",
            bd=1,
            bg=ENTRY_BG,
            fg=FG_COLOR,
            insertbackground=FG_COLOR,
        )
        self.username_entry.pack(pady=(0, 5))
        if self.prefill_username:
            self.username_entry.insert(0, self.prefill_username)
            self.username = self.prefill_username
        self.username_error_label = tk.Label(
            right_inner, text="", font=("Segoe UI", 12), fg="#b71c1c", bg=RIGHT_BG
        )
        self.username_error_label.pack(pady=(0, 10))

        # Create Password label
        password_img = create_text_image("Password:", 24, is_bold=True)
        password_label = tk.Label(right_inner, image=password_img, bg=RIGHT_BG)
        password_label.image = password_img  # Keep reference
        password_label.pack(pady=(10, 5))
        self.password_entry = tk.Entry(
            right_inner,
            font=("Segoe UI", 18),
            width=30,
            relief="solid",
            bd=1,
            show="*",
            bg=ENTRY_BG,
            fg=FG_COLOR,
            insertbackground=FG_COLOR,
        )
        self.password_entry.pack(pady=(0, 5))
        self.password_error_label = tk.Label(
            right_inner, text="", font=("Segoe UI", 12), fg="#b71c1c", bg=RIGHT_BG
        )
        self.password_error_label.pack(pady=(0, 10))
        self.login_button = tk.Button(
            right_inner,
            text="Login",
            command=self.login,
            bg=BUTTON_BG,
            fg=BUTTON_FG,
            font=("Segoe UI", 20, "bold"),
            width=20,
            relief="flat",
            activebackground=ENTRY_BG,
            activeforeground=ACCENT_COLOR,
        )
        self.login_button.pack(pady=(10, 10))
        from gui.functions.admdash_f.Login.pw_rst import PasswordResetWizard

        forgot_btn = tk.Button(
            right_inner,
            text="Forgot Password?",
            font=("Segoe UI", 12, "underline"),
            bg=RIGHT_BG,
            fg=ACCENT_COLOR,
            relief="flat",
            bd=0,
            cursor="hand2",
            command=lambda: PasswordResetWizard(
                parent=self.root,
                DB_PATH=DB_PATH,
                fernet=fernet,
                decrypt_2fa=self.decrypt_2fa,
            ),
            activebackground=RIGHT_BG,
            activeforeground=ACCENT_COLOR,
        )
        forgot_btn.pack(pady=(0, 8))
        setup_2fa_btn = tk.Button(
            right_inner,
            text="Setup 2FA",
            font=("Segoe UI", 12, "underline"),
            bg=RIGHT_BG,
            fg=ACCENT_COLOR,
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.setup_2fa,
            activebackground=RIGHT_BG,
            activeforeground=ACCENT_COLOR,
        )
        setup_2fa_btn.pack(pady=(0, 10))
        self.login_status_label = tk.Label(
            right_inner,
            text="",
            font=("Segoe UI", 14, "bold"),
            fg="#b71c1c",
            bg=RIGHT_BG,
        )
        self.login_status_label.pack(pady=(0, 10))
        self._username_validate_after_id = None
        self._password_validate_after_id = None
        self.username_entry.bind("<KeyRelease>", self._debounced_validate_username)
        self.password_entry.bind("<KeyRelease>", self._debounced_validate_password)

    def _debounced_validate_username(self, event=None):
        if self._username_validate_after_id:
            self.root.after_cancel(self._username_validate_after_id)
        self._username_validate_after_id = self.root.after(500, self.validate_username)

    def _debounced_validate_password(self, event=None):
        if self._password_validate_after_id:
            self.root.after_cancel(self._password_validate_after_id)
        self._password_validate_after_id = self.root.after(500, self.validate_password)
        self.password_entry.bind("<Return>", lambda event: self.login())

    def validate_username(self, event=None):
        username = self.username_entry.get()
        if not username.strip():
            self.show_toast("Please enter your username.", type="error")
        elif not all(c.isalpha() or c.isspace() for c in username):
            self.show_toast("Usernames can only have letters and spaces.", type="error")
        elif len(username.replace(" ", "")) < 2:
            self.show_toast("Username must be at least 2 letters.", type="error")

    def validate_password(self, event=None):
        password = self.password_entry.get()
        if not password.strip():
            self.show_toast("Please enter your password.", type="error")

    def decrypt_2fa(self, enc_secret):
        return fernet.decrypt(enc_secret.encode("utf-8")).decode("utf-8")

    def encrypt_2fa(self, secret):
        return fernet.encrypt(secret.encode("utf-8")).decode("utf-8")

    def forgot_password(self):
        from gui.functions.pw_rst import forgot_password, reset_password

        # Pass all required arguments for modularity
        forgot_password(
            parent=self.root,
            open_dialogs=self.open_dialogs,
            DB_PATH=DB_PATH,
            fernet=fernet,
            decrypt_2fa=self.decrypt_2fa,
            reset_password_func=reset_password,
        )

    def setup_2fa(self):
        # Use the new direct modal wizard for 2FA setup
        username = (
            self.username_entry.get().strip()
            if hasattr(self, "username_entry")
            else self.username
        )
        db_path = get_db_path()
        fernet_key_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "config", "fernet_key.py")
        )
        open_2fa_wizard_modal(
            parent=self.root,
            username=username,
            db_path=db_path,
            fernet_key_path=fernet_key_path,
            colors={
                "bg": "#000000",
                "header": "#800000",
                "fg": "#fffde7",
                "entry_bg": "#23272b",
                "button_bg": "#ff6f00",
                "button_fg": "#fffde7",
                "accent": "#ff6f00",
            },
        )

    def prompt_2fa(self, secret):
        Admin2FA(self.root, secret, on_success=self._open_dashboard).show()

    def _open_dashboard(self):
        # Add a 2-second delay before closing and opening dashboard
        def proceed():
            self.root.destroy()
            admin_dashboard = AdminDashboard(username=self.username)
            admin_dashboard.run()

        self.root.after(1000, proceed)

    def prompt_2fa_setup(self):
        if self.open_dialogs.get("2fa_prompt"):
            return

        def on_close():
            self.open_dialogs.pop("2fa_prompt", None)
            top.destroy()

        top = tk.Toplevel(self.root)
        self.open_dialogs["2fa_prompt"] = top
        top.title("2FA Setup Recommended")
        top.configure(bg=RIGHT_BG)
        top.geometry("400x220")
        top.resizable(False, False)
        top.grab_set()
        # Center the window
        x = self.root.winfo_screenwidth() // 2 - 200
        y = self.root.winfo_screenheight() // 2 - 110
        top.geometry(f"+{x}+{y}")
        tk.Label(
            top,
            text="Looks like you don't have 2FA yet.",
            font=("Segoe UI", 16, "bold"),
            bg=RIGHT_BG,
            fg=ACCENT_COLOR,
        ).pack(pady=(30, 10))
        tk.Label(
            top,
            text="Would you like to set it up now?",
            font=("Segoe UI", 12),
            bg=RIGHT_BG,
            fg=FG_COLOR,
        ).pack(pady=(0, 20))
        btn_frame = tk.Frame(top, bg=RIGHT_BG)
        btn_frame.pack(pady=10)

        def setup_2fa_action():
            top.destroy()
            self.open_dialogs.pop("2fa_prompt", None)
            self.setup_2fa()  # Directly call setup_2fa

        def maybe_later_action():
            top.destroy()
            self.open_dialogs.pop("2fa_prompt", None)
            self._open_dashboard()

        # Apple macOS style buttons
        setup_btn = tk.Button(
            btn_frame,
            text="Set up 2FA",
            font=("Segoe UI", 13, "bold"),
            bg="#f5f5f7",
            fg="#0071e3",
            activebackground="#e5e5ea",
            activeforeground="#0071e3",
            relief="flat",
            bd=0,
            padx=18,
            pady=6,
            cursor="hand2",
            command=setup_2fa_action,
        )
        setup_btn.grid(row=0, column=0, padx=10)
        later_btn = tk.Button(
            btn_frame,
            text="Maybe, Later?",
            font=("Segoe UI", 13),
            bg="#f5f5f7",
            fg="#1d1d1f",
            activebackground="#e5e5ea",
            activeforeground="#1d1d1f",
            relief="flat",
            bd=0,
            padx=18,
            pady=6,
            cursor="hand2",
            command=maybe_later_action,
        )
        later_btn.grid(row=0, column=1, padx=10)
        top.protocol("WM_DELETE_WINDOW", on_close)

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        self.username = username  # Store for dashboard and logging
        # Bypass check
        if username == "bypass" and password == "042402":
            self.show_toast("Bypass login successful. Welcome, Dev!", type="success")

            def proceed():
                self.root.destroy()
                admin_dashboard = AdminDashboard(username="bypass")
                admin_dashboard.run()

            self.root.after(1000, proceed)
            return
        # Remove error labels (now using toast)
        if not username:
            self.show_toast("Please enter your username.", type="error")
            return
        elif not all(c.isalpha() or c.isspace() for c in username):
            self.show_toast("Usernames can only have letters and spaces.", type="error")
            return
        elif len(username.replace(" ", "")) < 2:
            self.show_toast("Username must be at least 2 letters.", type="error")
            return
        if not password:
            self.show_toast("Please enter your password.", type="error")
            return
        self.login_button.config(state=tk.DISABLED)  # Disable button while processing
        try:
            # Use centralized connector to query the emp_list table
            connector = get_connector(get_db_path())
            conn = None
            cursor = None
            try:
                conn = connector.connect()
                cursor = conn.cursor()
                query = (
                    "SELECT [Access Level], [Password], [2FA Secret] FROM [emp_list] "
                    "WHERE LCase([Username])=? AND ([Access Level]='Level 2' OR [Access Level]='Level 3')"
                )
                try:
                    cursor.execute(query, (username.lower(),))
                    result = cursor.fetchone()
                except Exception as db_query_err:
                    print(f"Database query error: {db_query_err}")
                    self.show_toast(
                        "Unable to connect to the database. Please try again later.",
                        type="error",
                    )
                    return
            except Exception as db_conn_err:
                print(f"Database connection error: {db_conn_err}")
                self.show_toast(
                    "Unable to connect to the database. Please try again later.",
                    type="error",
                )
                return
            finally:
                try:
                    if cursor:
                        cursor.close()
                except Exception:
                    pass
                try:
                    connector.close()
                except Exception:
                    try:
                        if conn:
                            conn.close()
                    except Exception:
                        pass
            if result:
                access_level, db_pw, enc_2fa = result
                try:
                    decrypted_pw = fernet.decrypt(db_pw.encode()).decode()
                except Exception as e:
                    print(f"Password decryption error: {e}")
                    self.show_toast(
                        "There was a problem verifying your password. Please contact support.",
                        type="error",
                    )
                    return
                if decrypted_pw == password:
                    self.show_toast(
                        f"Welcome back, {username}! Login successful.", type="success"
                    )
                    if enc_2fa:
                        try:
                            secret = self.decrypt_2fa(enc_2fa)
                        except Exception as e:
                            print(f"2FA secret error: {e}")
                            self.show_toast(
                                "There was a problem with your 2FA setup. Please contact support.",
                                type="error",
                            )
                            return
                        self.prompt_2fa(secret)
                    else:
                        self.prompt_2fa_setup()
                        self.show_toast(
                            "Login successful! Please set up 2FA for extra security.",
                            type="success",
                        )
                else:
                    self.password_entry.delete(0, tk.END)
                    self.show_toast(
                        "Incorrect username or password. Please try again.",
                        type="error",
                    )
            else:
                self.password_entry.delete(0, tk.END)
                self.show_toast(
                    "Incorrect username or password. Please try again.", type="error"
                )
        except Exception:
            self.show_toast(
                "A database error occurred. Please try again later.", type="error"
            )
        finally:
            try:
                self.login_button.config(state=tk.NORMAL)
            except tk.TclError:
                pass  # Button was destroyed, ignore

    def go_back_to_welcome(self):
        self.root.destroy()
        welcome_window = WelcomeWindow()
        welcome_window.run()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = AdminLogin()
    app.run()
