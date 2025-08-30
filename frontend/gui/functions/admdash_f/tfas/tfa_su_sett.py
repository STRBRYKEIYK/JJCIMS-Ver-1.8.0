# Combined Multi-Step 2FA Wizard for Settings
# Steps are based on tfa_su_step1.py to tfa_su_step5.py
# All assets and UI logic are preserved, navigation is handled in a single window.


from pathlib import Path
from tkinter import Tk, Canvas, Entry, Button, PhotoImage, Frame, Toplevel
import sys
import pyodbc
import os
from cryptography.fernet import Fernet
from backend.database import get_db_path
# from utils.window_icon import set_window_icon  # unused

# Helper for asset paths (relative to workspace root)
WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
ASSETS_ROOT = WORKSPACE_ROOT / "assets" / "adm_sett_2fa_setup_assets"


def step_assets(step):  # replaces lambda (E731)
    return ASSETS_ROOT / f"step_{step}"


def relative_to_assets(step, path):
    return step_assets(step) / Path(path)


# Fernet key loader (from setup_2fa_utils)
def load_fernet_key(fernet_key_path):
    # Support both Python file with FERNET_KEY variable and raw key file
    if os.path.exists(fernet_key_path):
        if fernet_key_path.endswith(".py"):
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "fernet_key_module", fernet_key_path
            )
            fernet_key_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(fernet_key_module)
            key = getattr(fernet_key_module, "FERNET_KEY", None)
            if not key:
                raise ValueError("FERNET_KEY variable not found in fernet_key.py")
        else:
            with open(fernet_key_path, "rb") as f:
                key = f.read()
    else:
        key = Fernet.generate_key()
        # Default to writing as raw key file
        with open(fernet_key_path, "wb") as f:
            f.write(key)
    return key


# Employee list loader (from setup_2fa_utils)
def get_employee_list(db_path):
    employees = []
    try:
        conn = pyodbc.connect(
            r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + db_path
        )
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM [emp_list]")
        employees = [row[0] for row in cursor.fetchall()]
        conn.close()
    except Exception as e:
        print(f"Error loading employee list: {e}")
    return employees


class MultiStep2FAWizardforsett:
    def __init__(
        self,
        parent=None,
        username=None,
        db_path=None,
        fernet_key_path=None,
        popup=False,
        colors=None,
    ):
        # Store params
        self.parent = parent
        self.username = username
        self.db_path = db_path
        self.fernet_key_path = fernet_key_path
        self.popup = popup
        self.colors = colors or {"bg": "#000000", "header": "#800000"}

        # Load Fernet key and employee list - with error handling
        try:
            self.fernet_key = (
                load_fernet_key(fernet_key_path) if fernet_key_path else None
            )
        except Exception as e:
            print(f"Warning: Could not load Fernet key: {e}")
            self.fernet_key = None

        try:
            self.employee_list = get_employee_list(db_path) if db_path else []
        except Exception as e:
            print(f"Warning: Could not load employee list: {e}")
            self.employee_list = []

        # Setup as embedded frame only (no popup mode)
        self.root = Frame(parent, bg=self.colors["bg"])
        self.root.pack(fill="both", expand=True)

        self.current_step = 1
        self.breadcrumb_progression = [1]  # Track the step progression for breadcrumbs
        self.canvas = Canvas(
            self.root,
            bg=self.colors["bg"],
            height=841,
            width=1400,
            bd=0,
            highlightthickness=0,
            relief="ridge",
        )
        self.canvas.pack(fill="both", expand=True)
        self.steps = {}
        self.init_steps()
        self.show_step(1)

    def clear_canvas(self):
        self.canvas.delete("all")
        # Remove all widgets except canvas (for both modal and frame)
        for widget in self.root.winfo_children():
            if isinstance(widget, (Button, Entry)):
                widget.destroy()

    def init_steps(self):
        self.steps = {
            1: self.step1,
            2: self.step2,
            3: self.step3,
            4: self.step4,
            5: self.step5,
        }

    def show_step(self, step):
        self.clear_canvas()
        # Breadcrumb logic
        if step == 1:
            self.breadcrumb_progression = [1]
        elif step == 5:
            # If jumping to step 5, show 1 -> 5
            self.breadcrumb_progression = [1, 5]
        elif (
            step == 4
            and self.breadcrumb_progression
            and self.breadcrumb_progression[-1] == 5
        ):
            # If coming from step 5 to 4, show 1 -> 5 -> 4
            if self.breadcrumb_progression != [1, 5, 4]:
                self.breadcrumb_progression.append(4)
        else:
            # Normal progression
            if (
                not self.breadcrumb_progression
                or self.breadcrumb_progression[-1] != step
            ):
                self.breadcrumb_progression.append(step)
        self.current_step = step
        self.draw_breadcrumbs()
        self.steps[step]()

    def draw_breadcrumbs(self):
        # Draw breadcrumbs at the top (no header, positioned for 1400x841)
        step_names = {
            1: "Generate",
            2: "Scan code",
            3: "Verify",
            4: "Success",
            5: "Setup Key",
        }
        x_start = 50
        y = 20
        spacing = 200
        self._breadcrumb_tags = []
        for idx, step in enumerate(self.breadcrumb_progression):
            name = step_names.get(step, f"Step {step}")
            fill = "#FFD700" if step == self.current_step else "#FFFFFF"
            tag = f"breadcrumb_{idx}"
            _text_id = self.canvas.create_text(
                x_start + idx * spacing,
                y,
                anchor="nw",
                text=name,
                fill=fill,
                font=(
                    "Segoe UI",
                    16,
                    "bold" if step == self.current_step else "normal",
                ),
                tags=(tag,),
            )
            self._breadcrumb_tags.append((tag, step, idx))
            # Only allow going back, not forward
            if step != self.current_step and idx < self.breadcrumb_progression.index(
                self.current_step
            ):

                def make_callback(target_step, target_idx):
                    def cb(event):
                        # Trim breadcrumb progression to the clicked step
                        self.breadcrumb_progression = self.breadcrumb_progression[
                            : target_idx + 1
                        ]
                        self.show_step(target_step)

                    return cb

                self.canvas.tag_bind(tag, "<Button-1>", make_callback(step, idx))
                self.canvas.tag_bind(
                    tag, "<Enter>", lambda e: self.canvas.config(cursor="hand2")
                )
                self.canvas.tag_bind(
                    tag, "<Leave>", lambda e: self.canvas.config(cursor="")
                )
            # Draw arrow if not last
            if idx < len(self.breadcrumb_progression) - 1:
                self.canvas.create_text(
                    x_start + (idx + 1) * spacing - 50,
                    y,
                    anchor="nw",
                    text="→",
                    fill="#FFFFFF",
                    font=("Segoe UI", 16),
                )

    def safe_load_image(self, step, image_name, fallback_color="#800000"):
        """Safely load an image with fallback"""
        try:
            return PhotoImage(file=relative_to_assets(step, image_name))
        except Exception as e:
            print(f"Warning: Could not load {image_name} for step {step}: {e}")
            # Create a minimal 1x1 transparent image as fallback
            return PhotoImage(width=1, height=1)

    def step1(self):
        import tkinter.messagebox  # threading removed (unused)

        step = 1

        # Bottom footer (replaces header)
        self.canvas.create_rectangle(
            0.0, 748.0, 1400.0, 841.0, fill="#800000", outline=""
        )

        # Main content image
        image_1 = self.safe_load_image(step, "image_1.png")
        self.canvas.create_image(700.0, 213.0, image=image_1)

        # Username label
        self.canvas.create_text(
            254.0,
            331.0,
            anchor="nw",
            text="Username:",
            fill="#FFFFFF",
            font=("Inter Light", 36),
        )

        # Entry field
        entry_image_1 = self.safe_load_image(step, "entry_1.png")
        _entry_bg_1 = self.canvas.create_image(
            699.5, 468.5, image=entry_image_1
        )  # unused ID
        entry_1 = Entry(
            self.root,
            bd=0,
            bg="#000000",
            fg="#FFFFFF",
            font=("Inter Light", 30),
            insertbackground="#FFFFFF",
            highlightthickness=0,
        )
        entry_1.place(x=311.5, y=418.5, width=776.0, height=100.0)
        if self.username:
            entry_1.insert(0, self.username)

        # Generate button (button_1)
        button_image_1 = self.safe_load_image(step, "button_1.png")
        button_generate = Button(
            self.root,
            image=button_image_1,
            borderwidth=0,
            highlightthickness=0,
            bg="#000000",
            activebackground="#000000",
            command=None,
            relief="flat",
            state="disabled",
        )
        button_generate.place(
            x=277.0, y=617.0, width=220.17446899414062, height=65.53191375732422
        )

        # Key Setup button (button_2)
        button_image_2 = self.safe_load_image(step, "button_2.png")
        key_setup = Button(
            self.root,
            image=button_image_2,
            borderwidth=0,
            highlightthickness=0,
            bg="#000000",
            activebackground="#000000",
            command=None,
            relief="flat",
        )
        key_setup.place(
            x=900.0, y=617.0, width=222.48085021972656, height=65.6907958984375
        )

        # Footer button (button_3)
        button_image_3 = self.safe_load_image(step, "button_3.png")
        footer_button = Button(
            self.root,
            image=button_image_3,
            borderwidth=0,
            highlightthickness=0,
            bg="#800000",
            activebackground="#800000",
            command=lambda: self.show_step(5),
            relief="flat",
        )
        footer_button.place(x=471.0, y=774.0, width=457.0, height=41.0)

        # If the image didn't load properly, create a text-based button as fallback
        if (
            not button_image_3 or button_image_3.width() == 1
        ):  # Check if it's our fallback 1x1 image
            print(
                "Warning: Could not load button_3.png for step 1, using text fallback"
            )
            footer_button.destroy()  # Remove the image button
            footer_button = Button(
                self.root,
                text="Setup 2FA",
                font=("Segoe UI", 12, "bold"),
                bg="#800000",
                fg="#FFFFFF",
                activebackground="#A00000",
                borderwidth=0,
                highlightthickness=0,
                command=lambda: self.show_step(5),
                relief="flat",
            )
            footer_button.place(x=471.0, y=774.0, width=457.0, height=41.0)

        # Toast notification helper
        def toast(msg, color="#222", fg="#fff", duration=2000):
            toast_win = Toplevel(self.root)
            toast_win.overrideredirect(True)
            toast_win.configure(bg=color)
            toast_win.attributes("-topmost", True)
            x = self.root.winfo_rootx() + 200
            y = self.root.winfo_rooty() + 100
            toast_win.geometry(f"300x40+{x}+{y}")
            label = tkinter.Label(
                toast_win, text=msg, bg=color, fg=fg, font=("Segoe UI", 12, "bold")
            )
            label.pack(fill="both", expand=True)
            toast_win.after(duration, toast_win.destroy)

        # Go to step 5 function
        def go_to_step5():
            username = entry_1.get().strip()
            if not username:
                toast("Enter a username first!", color="#800000")
                return
            self.username = username
            self.show_step(5)

        key_setup.config(command=go_to_step5)

        # Debounce logic for username check
        self._username_check_after_id = None

        def check_username():
            username = entry_1.get().strip()
            if not username:
                button_generate.config(state="disabled")
                return
            # Check if username exists in DB
            exists = False
            try:
                # Ensure we have a valid path to the database
                if not self.db_path or not os.path.exists(self.db_path):
                    print(f"Database path invalid or not found: {self.db_path}")
                    toast(
                        "Database not found. Please check configuration.",
                        color="#800000",
                    )
                    button_generate.config(state="disabled")
                    return

                # Connect with explicit driver specification and error handling
                conn_str = (
                    r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ="
                    + self.db_path
                )
                conn = pyodbc.connect(conn_str)
                cursor = conn.cursor()

                # Try to get the table names to verify connection works
                try:
                    table_names = [
                        table.table_name for table in cursor.tables(tableType="TABLE")
                    ]
                    if "Emp_list" not in table_names:
                        print(f"Available tables: {table_names}")
                        toast("Emp_list table not found in database", color="#800000")
                        button_generate.config(state="disabled")
                        conn.close()
                        return
                except Exception as table_err:
                    print(f"Error checking tables: {table_err}")

                # Execute the query with parameterized statement for security
                query = "SELECT username FROM [Emp_list] WHERE username=?"
                print(f"Executing query: {query} with parameter: {username}")
                cursor.execute(query, (username,))
                row = cursor.fetchone()
                exists = row is not None
                conn.close()
            except pyodbc.Error as db_err:
                print(f"Database Error: {db_err}")
                error_msg = str(db_err)
                if "IM002" in error_msg:
                    toast(
                        "MS Access driver not found. Check database configuration.",
                        color="#800000",
                    )
                else:
                    toast(f"DB Error: {error_msg}", color="#800000")
                button_generate.config(state="disabled")
                return
            except Exception as e:
                print(f"Unexpected error in check_username: {e}")
                toast(f"Error: {e}", color="#800000")
                button_generate.config(state="disabled")
                return

            if exists:
                toast("Username found!", color="#228B22")
                button_generate.config(state="normal")
            else:
                toast("Username not found!", color="#800000")
                button_generate.config(state="disabled")

        def on_entry_change(event=None):
            if self._username_check_after_id:
                self.root.after_cancel(self._username_check_after_id)
            self._username_check_after_id = self.root.after(500, check_username)

        entry_1.bind("<KeyRelease>", on_entry_change)

        # Generate button logic: check access level before proceeding
        def on_generate():
            username = entry_1.get().strip()
            if not username:
                toast("Enter a username first!", color="#800000")
                return
            try:
                # Validate database path
                if not self.db_path or not os.path.exists(self.db_path):
                    print(f"Database path invalid or not found: {self.db_path}")
                    toast(
                        "Database not found. Please check configuration.",
                        color="#800000",
                    )
                    return

                # Connect with explicit driver specification
                conn_str = (
                    r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ="
                    + self.db_path
                )
                conn = pyodbc.connect(conn_str)
                cursor = conn.cursor()

                # Execute query with proper parameterization
                query = "SELECT [Access Level], [2FA Secret] FROM [Emp_list] WHERE username=?"
                print(f"Executing query: {query} with parameter: {username}")
                cursor.execute(query, (username,))
                row = cursor.fetchone()
                conn.close()

                if row:
                    access_level = row[0] if row[0] else "None"
                    print(f"User {username} found with access level: {access_level}")

                    if access_level in ("Level 2", "Level 3"):
                        # Check if 2FA Secret already exists (not null/empty)
                        secret = row[1] if len(row) > 1 else None
                        if secret and str(secret).strip():
                            toast("User already has a 2FA Secret!", color="#800000")
                            return
                        toast("Access granted!", color="#228B22")
                        self.username = username
                        self.show_step(2)
                    else:
                        print(f"Invalid access level for 2FA setup: {access_level}")
                        toast(
                            f"Access Level must be Level 2 or 3! Current level: {access_level}",
                            color="#800000",
                        )
                else:
                    toast("Username not found!", color="#800000")
            except pyodbc.Error as db_err:
                print(f"Database Error in on_generate: {db_err}")
                error_msg = str(db_err)
                if "IM002" in error_msg:
                    toast(
                        "MS Access driver not found. Check database configuration.",
                        color="#800000",
                    )
                else:
                    toast(f"DB Error: {error_msg}", color="#800000")
            except Exception as e:
                print(f"Unexpected error in on_generate: {type(e).__name__} - {e}")
                toast(f"Error: {e}", color="#800000")

        button_generate.config(command=on_generate)

        # Keep references
        self._refs = [
            image_1,
            entry_image_1,
            button_image_1,
            button_image_2,
            entry_1,
            button_generate,
            key_setup,
            footer_button,
        ]
        # Always store button_image_3 reference, even if it's a fallback image
        # This ensures it won't be garbage collected
        self._refs.append(button_image_3)

    def step2(self):
        import pyotp
        import qrcode
        from PIL import ImageTk  # Only ImageTk needed

        step = 2

        # Bottom footer
        self.canvas.create_rectangle(
            0.0, 748.0, 1400.0, 841.0, fill="#800000", outline=""
        )

        # Main content image
        image_1 = self.safe_load_image(step, "image_1.png")
        self.canvas.create_image(699.0, 175.0, image=image_1)

        # QR code display area
        image_2 = self.safe_load_image(step, "image_2.png")
        self.canvas.create_image(703.3471069335938, 449.0, image=image_2)

        # Generate a new 2FA secret for this session (not saved or encrypted yet)
        self._2fa_secret = pyotp.random_base32()
        # Generate QR code for Google Authenticator
        username = self.username or "user"
        issuer = "JJCIMS"
        totp = pyotp.TOTP(self._2fa_secret)
        uri = totp.provisioning_uri(name=username, issuer_name=issuer)
        qr = qrcode.QRCode(box_size=6, border=2)
        qr.add_data(uri)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        # Resize to fit the QR area
        qr_img = qr_img.resize((250, 250))
        qr_photo = ImageTk.PhotoImage(qr_img)
        self.canvas.create_image(703, 449, image=qr_photo)  # Overlay on the QR area

        # Show manual entry key, clickable to copy
        manual_key_y = 610  # Positioned lower to have more space below the QR code

        # Create the manual key text with proper positioning and styling - make it clickable
        key_text_id = self.canvas.create_text(
            700,
            manual_key_y,
            text=f"Manual Key: {self._2fa_secret}",
            fill="#FFFFFF",
            font=("Inter Light", 20),
            anchor="center",
            tags="manual_key",
        )

        # Create instruction text separately - not clickable
        _instruction_text_id = self.canvas.create_text(
            700,
            manual_key_y + 30,
            text="(Click to copy)",
            fill="#ffffff",
            font=("Inter Light", 14),
            anchor="center",
        )

        # Bind click event to copy the key
        def copy_manual_key(event=None):
            self.root.clipboard_clear()
            self.root.clipboard_append(self._2fa_secret)
            import tkinter

            toast_win = tkinter.Toplevel(self.root)
            toast_win.overrideredirect(True)
            toast_win.configure(bg="#222")
            toast_win.attributes("-topmost", True)
            x = self.root.winfo_rootx() + 700
            y = self.root.winfo_rooty() + manual_key_y + 40
            toast_win.geometry(f"120x30+{x}+{y}")
            label = tkinter.Label(
                toast_win,
                text="Copied!",
                bg="#222",
                fg="#fff",
                font=("Segoe UI", 10, "bold"),
            )
            label.pack(fill="both", expand=True)
            toast_win.after(1000, toast_win.destroy)

        # Add simple hover effects for better user experience
        def on_enter(event):
            self.canvas.config(cursor="hand2")
            self.canvas.itemconfig(
                key_text_id, fill="#5dade2"
            )  # Highlight the key text instead

        def on_leave(event):
            self.canvas.config(cursor="")
            self.canvas.itemconfig(
                key_text_id, fill="#FFFFFF"
            )  # Reset to original color

        # Bind events to the key text only
        self.canvas.tag_bind("manual_key", "<Button-1>", copy_manual_key)
        self.canvas.tag_bind("manual_key", "<Enter>", on_enter)
        self.canvas.tag_bind("manual_key", "<Leave>", on_leave)

        # Continue button
        button_image_1 = self.safe_load_image(step, "button_1.png")
        continue_button = Button(
            self.root,
            image=button_image_1,
            borderwidth=0,
            bg="#000000",
            activebackground="#000000",
            highlightthickness=0,
            command=lambda: self.show_step(3),
            relief="flat",
        )
        continue_button.place(
            x=592.6397705078125,
            y=671.54931640625,
            width=232.5906982421875,
            height=63.383365631103516,
        )

        # Footer button
        button_image_2 = self.safe_load_image(step, "button_2.png")
        footer_button = Button(
            self.root,
            image=button_image_2,
            borderwidth=0,
            bg="#800000",
            activebackground="#800000",
            highlightthickness=0,
            command=lambda: self.show_step(5),
            relief="flat",
        )
        footer_button.place(x=471.0, y=774.0, width=457.0, height=41.0)

        self._refs = [image_1, image_2, qr_photo, button_image_1, button_image_2]

    def step3(self):
        import pyotp
        import tkinter

        step = 3

        # Bottom footer
        self.canvas.create_rectangle(
            0.0, 748.0, 1400.0, 841.0, fill="#800000", outline=""
        )

        # Main content image
        image_1 = self.safe_load_image(step, "image_1.png")
        self.canvas.create_image(700.0, 204.0, image=image_1)

        # Label for 6-digit code
        self.canvas.create_text(
            356.0,
            359.0,
            anchor="nw",
            text="Enter 6 digit code:",
            fill="#FFFFFF",
            font=("Inter Light", 36),
        )

        # Entry fields (6) - using the new layout
        entry_images = [
            self.safe_load_image(step, f"entry_{i + 1}.png") for i in range(6)
        ]
        entry_positions = [
            (409.5, 489.5, 374.0, 455.0, 70.0, 70.0),  # entry_1
            (525.5, 489.5, 490.0, 455.0, 70.0, 70.0),  # entry_2
            (642.0, 489.5, 607.0, 455.0, 70.0, 70.0),  # entry_3
            (758.0, 489.5, 723.0, 455.0, 70.0, 70.0),  # entry_4
            (874.5, 489.5, 840.0, 455.0, 70.0, 70.0),  # entry_5
            (990.5, 489.5, 955.0, 455.0, 70.0, 70.0),  # entry_6
        ]

        entry_bgs = []
        entry_fields = []

        for i, (img_x, img_y, entry_x, entry_y, width, height) in enumerate(
            entry_positions
        ):
            # Create image background
            entry_bg = self.canvas.create_image(img_x, img_y, image=entry_images[i])
            entry_bgs.append(entry_bg)

            # Create entry field
            entry = Entry(
                self.root,
                bd=0,
                bg="#000000",
                fg="#FFFFFF",
                font=("Inter Light", 30),
                justify="center",
                insertbackground="#FFFFFF",
                highlightthickness=0,
            )
            entry.place(x=entry_x, y=entry_y, width=width, height=height)
            entry_fields.append(entry)

        # Entry validation and navigation (from step_3.py)
        def validate_and_move(event, current_entry, next_entry=None):
            """Validate input and move to next entry"""
            char = event.char

            # Allow only digits 0-9
            if char.isdigit() and len(current_entry.get()) == 0:
                current_entry.delete(0, "end")
                current_entry.insert(0, char)

                # Move to next entry if available
                if next_entry:
                    next_entry.focus_set()
                elif current_entry == entry_fields[5]:
                    # If this is the last entry, trigger verify button
                    verify_button.invoke()

                return "break"  # Prevent default behavior

            # Block any other characters
            return "break"

        def handle_backspace(event, current_entry, prev_entry=None):
            """Handle backspace key - delete from rightmost to leftmost"""
            # Find the rightmost filled entry
            for entry in reversed(entry_fields):
                if entry.get():
                    entry.delete(0, "end")
                    entry.focus_set()
                    break

            return "break"  # Prevent default behavior

        # Bind events for sequential typing and validation
        entry_fields[0].bind(
            "<KeyPress>",
            lambda event: validate_and_move(event, entry_fields[0], entry_fields[1]),
        )
        entry_fields[1].bind(
            "<KeyPress>",
            lambda event: validate_and_move(event, entry_fields[1], entry_fields[2]),
        )
        entry_fields[2].bind(
            "<KeyPress>",
            lambda event: validate_and_move(event, entry_fields[2], entry_fields[3]),
        )
        entry_fields[3].bind(
            "<KeyPress>",
            lambda event: validate_and_move(event, entry_fields[3], entry_fields[4]),
        )
        entry_fields[4].bind(
            "<KeyPress>",
            lambda event: validate_and_move(event, entry_fields[4], entry_fields[5]),
        )
        entry_fields[5].bind(
            "<KeyPress>", lambda event: validate_and_move(event, entry_fields[5])
        )

        # Bind backspace for all entries
        for entry in entry_fields:
            entry.bind("<BackSpace>", lambda event: handle_backspace(event, entry))

        # Set focus to first entry
        entry_fields[0].focus_set()

        def toast(msg, color="#222", fg="#fff", duration=2000):
            print(f"[TOAST][step3] {msg}", file=sys.stderr)
            toast_win = Toplevel(self.root)
            toast_win.overrideredirect(True)
            toast_win.configure(bg=color)
            toast_win.attributes("-topmost", True)
            x = self.root.winfo_rootx() + 200
            y = self.root.winfo_rooty() + 100
            toast_win.geometry(f"300x40+{x}+{y}")
            label = tkinter.Label(
                toast_win, text=msg, bg=color, fg=fg, font=("Segoe UI", 12, "bold")
            )
            label.pack(fill="both", expand=True)
            toast_win.after(duration, toast_win.destroy)

        def on_verify():
            code = "".join([e.get() for e in entry_fields])
            if not code or len(code) != 6 or not code.isdigit():
                toast("Enter a valid 6-digit code!", color="#800000")
                return
            # Validate code using the secret generated in step2
            secret = getattr(self, "_2fa_secret", None)
            if not secret:
                toast("No 2FA secret found!", color="#800000")
                return
            totp = pyotp.TOTP(secret)
            if totp.verify(code):
                # Save/encrypt secret to DB
                try:
                    fernet = Fernet(self.fernet_key)
                    encrypted_secret = fernet.encrypt(secret.encode()).decode("utf-8")
                    conn = pyodbc.connect(
                        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ="
                        + self.db_path
                    )
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE [Emp_list] SET [2FA Secret]=? WHERE username=?",
                        (encrypted_secret, self.username),
                    )
                    conn.commit()
                    conn.close()
                    toast("2FA setup complete!", color="#228B22")
                    self.show_step(4)
                except Exception as e:
                    print(
                        f"[DEBUG][step3] Exception during DB update: {e}",
                        file=sys.stderr,
                    )
                    toast(f"DB Error: {e}", color="#800000")
            else:
                toast("Invalid code!", color="#800000")

        # Verify button
        button_image_1 = self.safe_load_image(step, "button_1.png")
        verify_button = Button(
            self.root,
            image=button_image_1,
            borderwidth=0,
            highlightthickness=0,
            bg="#000000",
            activebackground="#000000",
            command=on_verify,
            relief="flat",
        )
        verify_button.place(
            x=585.0, y=628.0, width=230.94189453125, height=62.934051513671875
        )

        # Footer button
        button_image_2 = self.safe_load_image(step, "button_2.png")
        footer_button = Button(
            self.root,
            image=button_image_2,
            borderwidth=0,
            highlightthickness=0,
            bg="#800000",
            activebackground="#800000",
            command=lambda: self.show_step(5),
            relief="flat",
        )
        footer_button.place(x=471.0, y=774.0, width=457.0, height=41.0)

        self._refs = [
            image_1,
            *entry_images,
            button_image_1,
            button_image_2,
            *entry_fields,
        ]

    def step4(self):
        step = 4

        # Bottom footer
        self.canvas.create_rectangle(
            0.0, 748.0, 1400.0, 841.0, fill="#800000", outline=""
        )

        # Main content image
        image_1 = self.safe_load_image(step, "image_1.png")
        self.canvas.create_image(700.0, 316.0, image=image_1)

        # Countdown text
        self._countdown = 5
        self._countdown_text_id = self.canvas.create_text(
            548.0,
            523.0,
            anchor="nw",
            text="Going Back in ...",
            fill="#FFFFFF",
            font=("Inter Light", 36),
        )

        def update_countdown():
            self._countdown -= 1
            if self._countdown > 0:
                self.canvas.itemconfig(
                    self._countdown_text_id, text=f"Going Back in ... {self._countdown}"
                )
                self.root.after(1000, update_countdown)
            else:
                self.show_step(1)

        self.root.after(1000, update_countdown)

        # Footer button
        button_image_1 = self.safe_load_image(step, "button_1.png")
        footer_button = Button(
            self.root,
            image=button_image_1,
            borderwidth=0,
            highlightthickness=0,
            bg="#800000",
            activebackground="#800000",
            command=lambda: self.show_step(1),
            relief="flat",
        )
        footer_button.place(x=471.0, y=774.0, width=457.0, height=41.0)

        self._refs = [image_1, button_image_1]

    def step5(self):
        import tkinter

        step = 5

        # Bottom footer
        self.canvas.create_rectangle(
            0.0, 748.0, 1400.0, 841.0, fill="#800000", outline=""
        )

        # Main content image
        image_1 = self.safe_load_image(step, "image_1.png")
        self.canvas.create_image(700.0, 238.0, image=image_1)

        # Label
        self.canvas.create_text(
            325.0,
            354.0,
            anchor="nw",
            text="Your 2FA key:",
            fill="#FFFFFF",
            font=("Inter Light", 36),
        )

        # Entry field
        entry_image_1 = self.safe_load_image(step, "entry_1.png")
        _entry_bg_1 = self.canvas.create_image(700.0, 473.0, image=entry_image_1)
        entry_1 = Entry(
            self.root,
            bd=0,
            bg="#000000",
            fg="#FFFFFF",
            insertbackground="#FFFFFF",
            font=("Inter Light", 30),
            highlightthickness=0,
            disabledbackground="#000000",
            disabledforeground="#FFFFFF",
        )
        entry_1.place(x=365.0, y=435.0, width=670.0, height=70.0)

        def toast(msg, color="#222", fg="#fff", duration=2000):
            toast_win = tkinter.Toplevel(self.root)
            toast_win.overrideredirect(True)
            toast_win.configure(bg=color)
            toast_win.attributes("-topmost", True)
            x = self.root.winfo_rootx() + 200
            y = self.root.winfo_rooty() + 100
            toast_win.geometry(f"300x40+{x}+{y}")
            label = tkinter.Label(
                toast_win, text=msg, bg=color, fg=fg, font=("Segoe UI", 12, "bold")
            )
            label.pack(fill="both", expand=True)
            toast_win.after(duration, toast_win.destroy)

        # Check if username is provided
        if not self.username or not str(self.username).strip():
            toast(
                "No username provided. Please enter your username first.",
                color="#800000",
            )
            entry_1.delete(0, "end")
            entry_1.insert(0, "Username required.")
            entry_1.config(state="disabled")
            # Disable submit button
            button_image_1 = self.safe_load_image(step, "button_1.png")
            submit_button = Button(
                self.root,
                image=button_image_1,
                borderwidth=0,
                highlightthickness=0,
                bg="#000000",
                activebackground="#000000",
                command=None,
                relief="flat",
                state="disabled",
            )
            submit_button.place(x=602.0, y=583.0, width=195.4391326904297, height=73.0)
            self.root.after(1800, lambda: self.show_step(1))
            # Keep references to prevent garbage collection
            self._refs = [image_1, entry_image_1, button_image_1]
            return

        # Check if user already has a 2FA secret
        already_has_2fa = False
        try:
            conn = pyodbc.connect(
                r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + self.db_path
            )
            cursor = conn.cursor()
            cursor.execute(
                "SELECT [2FA Secret] FROM [Emp_list] WHERE username=?", (self.username,)
            )
            row = cursor.fetchone()
            conn.close()
            if row and row[0] and str(row[0]).strip():
                already_has_2fa = True
        except Exception as e:
            toast(f"DB Error: {e}", color="#800000")

        # Submit button
        button_image_1 = self.safe_load_image(step, "button_1.png")
        submit_button = Button(
            self.root,
            image=button_image_1,
            borderwidth=0,
            highlightthickness=0,
            bg="#000000",
            activebackground="#000000",
            command=None,
            relief="flat",
        )
        submit_button.place(x=602.0, y=583.0, width=195.4391326904297, height=73.0)

        if already_has_2fa:
            toast("You already have a 2FA key!", color="#800000")
            entry_1.delete(0, "end")
            entry_1.insert(0, "No need to enter a 2FA key.")
            entry_1.config(state="disabled")
            submit_button.config(state="disabled")
        else:

            def on_submit():
                key = entry_1.get().strip()
                if not key:
                    toast("Please enter a 2FA key!", color="#800000")
                    return
                # Optionally, validate key format (base32, length, etc.)
                try:
                    from pyotp import TOTP

                    TOTP(key)  # Will raise if invalid
                except Exception:
                    toast("Invalid 2FA key format!", color="#800000")
                    return
                try:
                    fernet = Fernet(self.fernet_key)
                    encrypted_secret = fernet.encrypt(key.encode()).decode("utf-8")
                    conn = pyodbc.connect(
                        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ="
                        + self.db_path
                    )
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE [Emp_list] SET [2FA Secret]=? WHERE username=?",
                        (encrypted_secret, self.username),
                    )
                    conn.commit()
                    conn.close()
                    toast("2FA key imported!", color="#228B22")
                    self.show_step(4)
                except Exception as e:
                    toast(f"DB Error: {e}", color="#800000")

            submit_button.config(command=on_submit, state="normal")

        # Footer button
        button_image_2 = self.safe_load_image(step, "button_2.png")
        footer_button = Button(
            self.root,
            image=button_image_2,
            borderwidth=0,
            highlightthickness=0,
            bg="#800000",
            activebackground="#800000",
            command=lambda: self.show_step(1),
            relief="flat",
        )
        footer_button.place(x=471.0, y=774.0, width=457.0, height=41.0)

        self._refs = [image_1, entry_image_1, button_image_1, button_image_2]


if __name__ == "__main__":
    # Example usage: embedded frame mode
    root = Tk()
    root.geometry("1400x841")
    root.configure(bg="#000000")

    MultiStep2FAWizardforsett(
        parent=root,
        username=None,
        db_path=get_db_path(),
        fernet_key_path=str(WORKSPACE_ROOT / "gui" / "config" / "fernet_key.py"),
        popup=False,
    )

    root.mainloop()


def create_2fa_setup_frame(
    parent, username, db_path=None, fernet_key_path=None, colors=None
):
    """
    Create the 2FA setup wizard as an embedded frame for admin settings.
    - parent: Tkinter parent widget
    - username: Username for whom to set up 2FA
    - db_path: Path to the Access database (defaults to database/JJCIMS.accdb)
    - fernet_key_path: Path to the Fernet key file (defaults to gui/config/fernet_key.py)
    - colors: Dict of color settings (optional)
    Returns the MultiStep2FAWizardforsett instance.
    """
    # Set default paths if not provided
    if db_path is None:
        db_path = get_db_path()
    if fernet_key_path is None:
        fernet_key_path = str(WORKSPACE_ROOT / "gui" / "config" / "fernet_key.py")

    return MultiStep2FAWizardforsett(
        parent=parent,
        username=username,
        db_path=db_path,
        fernet_key_path=fernet_key_path,
        popup=False,
        colors=colors or {"bg": "#000000", "header": "#800000"},
    )
