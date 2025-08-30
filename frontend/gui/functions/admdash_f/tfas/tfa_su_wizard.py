# Combined Multi-Step 2FA Wizard
# Steps are based on tfa_su_step1.py to tfa_su_step5.py
# All assets and UI logic are preserved, navigation is handled in a single window.


from pathlib import Path
from tkinter import Tk, Canvas, Entry, Button, PhotoImage, Frame, Toplevel
import sys
import os
from backend.database import get_connector, get_db_path
from cryptography.fernet import Fernet
from backend.utils.window_icon import set_window_icon

# Helper for asset paths (relative to workspace root)
WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
ASSETS_ROOT = WORKSPACE_ROOT / "assets" / "tfa_su_assets"


def step_assets(step):
    return ASSETS_ROOT / f"step_{step}"


def relative_to_assets(step, path):
    # Return a string path that Tkinter PhotoImage accepts
    return str(step_assets(step) / Path(path))


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
def get_employee_list(db_path=None):
    employees = []
    try:
        connector = get_connector(db_path or get_db_path())
        conn = connector.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM [emp_list]")
        employees = [row[0] for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error loading employee list: {e}")
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
    return employees


class MultiStep2FAWizard:
    def __init__(
        self,
        parent=None,
        username=None,
        db_path=None,
        fernet_key_path=None,
        popup=True,
        colors=None,
    ):
        # Store params
        self.parent = parent
        self.username = username
        self.db_path = db_path
        self.fernet_key_path = fernet_key_path
        self.popup = popup
        self.colors = colors or {"bg": "#000000", "header": "#800000"}

        # Load Fernet key and employee list
        self.fernet_key = load_fernet_key(fernet_key_path) if fernet_key_path else None
        self.employee_list = get_employee_list(db_path) if db_path else []

        # Setup window/frame
        if popup:
            self.root = Toplevel(parent) if parent else Tk()
            self.root.title("2FA Setup Wizard")

            # Set consistent window icon
            set_window_icon(self.root)

            self.root.geometry("700x700")
            self.root.configure(bg=self.colors["bg"])
            self.root.resizable(False, False)
            self._modal_parent = None
        else:
            self.root = Frame(parent, bg=self.colors["bg"], width=700, height=700)
            self.root.pack_propagate(False)
            self.root.pack()
            # Save the parent Toplevel for modal close
            self._modal_parent = parent if isinstance(parent, Toplevel) else None

        self.current_step = 1
        self.breadcrumb_progression = [1]  # Track the step progression for breadcrumbs
        self.canvas = Canvas(
            self.root,
            bg=self.colors["bg"],
            height=700,
            width=700,
            bd=0,
            highlightthickness=0,
            relief="ridge",
        )
        self.canvas.place(x=0, y=0)
        self.steps = {}
        self.init_steps()
        self.show_step(1)
        if popup and (not parent):
            self.root.mainloop()

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
        # Draw breadcrumbs just below the top rectangle (y=70)
        step_names = {
            1: "Generate",
            2: "Scan code",
            3: "Verify",
            4: "Success",
            5: "Setup Key",
        }
        x_start = 20
        y = 75
        spacing = 110
        self._breadcrumb_tags = []
        for idx, step in enumerate(self.breadcrumb_progression):
            name = step_names.get(step, f"Step {step}")
            fill = "#FFD700" if step == self.current_step else "#FFFFFF"
            tag = f"breadcrumb_{idx}"
            self.canvas.create_text(
                x_start + idx * spacing,
                y,
                anchor="nw",
                text=name,
                fill=fill,
                font=(
                    "Segoe UI",
                    14,
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
                    x_start + (idx + 1) * spacing - 30,
                    y,
                    anchor="nw",
                    text="→",
                    fill="#FFFFFF",
                    font=("Segoe UI", 14),
                )

    def step1(self):
        import tkinter.messagebox

        step = 1
        # Backgrounds
        self.canvas.create_rectangle(
            0, 0, 700, 70, fill=self.colors["header"], outline=""
        )
        self.canvas.create_rectangle(
            0, 630, 700, 700, fill=self.colors["header"], outline=""
        )
        # Images
        image_2 = PhotoImage(file=relative_to_assets(step, "image_2.png"))
        self.canvas.create_image(350, 35, image=image_2)
        image_3 = PhotoImage(file=relative_to_assets(step, "image_3.png"))
        self.canvas.create_image(349, 223, image=image_3)
        # Entry
        entry_image_1 = PhotoImage(file=relative_to_assets(step, "entry_1.png"))
        self.canvas.create_image(349.5, 422.0, image=entry_image_1)
        entry_1 = Entry(
            self.root,
            bd=0,
            bg="#000000",
            fg="#FFFFFF",
            highlightthickness=0,
            font=("Segoe UI", 20),
            insertbackground="#FFFFFF",
        )
        entry_1.place(x=155.0, y=397.0, width=389.0, height=50.0)
        if self.username:
            entry_1.insert(0, self.username)
        self.canvas.create_text(
            141,
            328,
            anchor="nw",
            text="Username:",
            fill="#FFFFFF",
            font=("Inter Light", -20),
        )

        # Main action buttons
        button_image_generate = PhotoImage(
            file=relative_to_assets(step, "button_4.png")
        )
        button_generate = Button(
            self.root,
            image=button_image_generate,
            borderwidth=0,
            highlightthickness=0,
            bg="#000000",
            activebackground="#000000",
            command=None,
            relief="flat",
            state="disabled",
        )
        button_generate.place(x=174.0, y=496.0, width=134.3922119140625, height=40.0)
        button_image_cancel = PhotoImage(file=relative_to_assets(step, "button_5.png"))

        # Cancel button closes modal or destroys frame
        def cancel_action():
            if self.popup:
                self.root.destroy()
            else:
                # In modal mode, destroy the parent Toplevel if available
                if hasattr(self, "_modal_parent") and self._modal_parent:
                    self._modal_parent.destroy()
                else:
                    self.root.pack_forget()

        button_cancel = Button(
            self.root,
            image=button_image_cancel,
            borderwidth=0,
            bg="#000000",
            activebackground="#000000",
            highlightthickness=0,
            command=cancel_action,
            relief="flat",
        )
        button_cancel.place(x=391.0, y=496.0, width=135.8, height=40.1)
        button_image_key_setup = PhotoImage(
            file=relative_to_assets(step, "button_6.png")
        )

        def go_to_step5():
            username = entry_1.get().strip()
            if not username:
                toast("Enter a username first!", color="#800000")
                return
            self.username = username
            self.show_step(5)

        key_setup = Button(
            self.root,
            image=button_image_key_setup,
            borderwidth=0,
            bg="#800000",
            activebackground="#800000",
            highlightthickness=0,
            command=go_to_step5,
            relief="flat",
        )
        key_setup.place(x=235.0, y=644.0, width=229.0, height=41.0)

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

        # Debounce logic for username check
        self._username_check_after_id = None
        self._username_last_value = ""

        def check_username():
            username = entry_1.get().strip()
            if not username:
                button_generate.config(state="disabled")
                return
            # Check if username exists in DB
            exists = False
            try:
                connector = get_connector(self.db_path)
                conn = connector.connect()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT username FROM [emp_list] WHERE username=?", (username,)
                )
                row = cursor.fetchone()
                exists = row is not None
                cursor.close()
                conn.close()
            except Exception as e:
                toast(f"DB Error: {e}", color="#800000")
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
                connector = get_connector(self.db_path)
                conn = connector.connect()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT [Access Level], [2FA Secret] FROM [emp_list] WHERE username=?",
                    (username,),
                )
                row = cursor.fetchone()
                cursor.close()
                conn.close()
                if row and row[0] in ("Level 2", "Level 3"):
                    # Check if 2FA Secret already exists (not null/empty)
                    secret = row[1] if len(row) > 1 else None
                    if secret and str(secret).strip():
                        toast("User already has a 2FA Secret!", color="#800000")
                        return
                    toast("Access granted!", color="#228B22")
                    self.username = username
                    self.show_step(2)
                else:
                    toast("Access Level must be Level 2 or 3!", color="#800000")
            except Exception as e:
                toast(f"DB Error: {e}", color="#800000")

        button_generate.config(command=on_generate)

        # Patch: Also set username before going to step 2 or 3 from breadcrumbs or other navigation
        def go_to_step2():
            username = entry_1.get().strip()
            if not username:
                toast("Enter a username first!", color="#800000")
                return
            self.username = username
            self.show_step(2)

        def go_to_step3():
            username = entry_1.get().strip()
            if not username:
                toast("Enter a username first!", color="#800000")
                return
            self.username = username
            self.show_step(3)

        # If you have navigation buttons or logic to go to step 2 or 3 directly from step 1, use go_to_step2/go_to_step3 as the command.

        # Keep references
        self._refs = [
            image_2,
            image_3,
            entry_image_1,
            button_image_generate,
            button_image_cancel,
            button_image_key_setup,
            entry_1,
            button_generate,
            key_setup,
        ]

    def step2(self):
        import pyotp
        import qrcode
        from PIL import ImageTk

        step = 2
        # Background and header/footer
        self.canvas.create_rectangle(
            0, 0, 700, 70, fill=self.colors["header"], outline=""
        )
        self.canvas.create_rectangle(
            0, 630, 700, 700, fill=self.colors["header"], outline=""
        )

        # Images
        image_2 = PhotoImage(file=relative_to_assets(step, "image_2.png"))
        self.canvas.create_image(350, 35, image=image_2)
        image_3 = PhotoImage(file=relative_to_assets(step, "image_3.png"))
        self.canvas.create_image(349, 143, image=image_3)

        # Generate a new 2FA secret for this session (not yet saved)
        self._2fa_secret = pyotp.random_base32()

        # Build TOTP provisioning URI and QR image
        username = self.username or "user"
        issuer = "JJCIMS"
        totp = pyotp.TOTP(self._2fa_secret)
        uri = totp.provisioning_uri(name=username, issuer_name=issuer)
        qr = qrcode.QRCode(box_size=6, border=2)
        qr.add_data(uri)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img = qr_img.resize((200, 200))
        qr_photo = ImageTk.PhotoImage(qr_img)
        self.canvas.create_image(350, 350, image=qr_photo)

        # Manual key text (clickable to copy)
        manual_key_text = f"Manual key: {self._2fa_secret}"
        font_tuple = ("Inter ExtraLight", -14, "underline")
        manual_key_y = 460
        self.canvas.create_text(
            350,
            manual_key_y,
            anchor="n",
            text=manual_key_text,
            fill="#00BFFF",
            font=font_tuple,
            tags=("manual_key",),
        )

        def copy_manual_key(event=None):
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(self._2fa_secret)
                import tkinter

                toast_win = tkinter.Toplevel(self.root)
                toast_win.overrideredirect(True)
                toast_win.configure(bg="#222")
                toast_win.attributes("-topmost", True)
                x = self.root.winfo_rootx() + 350
                y = self.root.winfo_rooty() + manual_key_y + 30
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
            except Exception:
                pass

        self.canvas.tag_bind("manual_key", "<Button-1>", copy_manual_key)
        self.canvas.tag_bind(
            "manual_key", "<Enter>", lambda e: self.canvas.config(cursor="hand2")
        )
        self.canvas.tag_bind(
            "manual_key", "<Leave>", lambda e: self.canvas.config(cursor="")
        )

        # Navigation buttons
        button_image_continue = PhotoImage(
            file=relative_to_assets(step, "button_5.png")
        )
        continue_button = Button(
            self.root,
            image=button_image_continue,
            borderwidth=0,
            bg="#000000",
            activebackground="#000000",
            highlightthickness=0,
            command=lambda: self.show_step(3),
            relief="flat",
        )
        continue_button.place(x=278.0, y=565.0, width=143.69, height=39.16)

        button_image_key_setup = PhotoImage(
            file=relative_to_assets(step, "button_1.png")
        )
        key_setup = Button(
            self.root,
            image=button_image_key_setup,
            borderwidth=0,
            bg="#800000",
            activebackground="#800000",
            highlightthickness=0,
            command=lambda: self.show_step(5),
            relief="flat",
        )
        key_setup.place(x=237.0, y=644.0, width=224.0, height=41.0)

        # Keep references to images/widgets
        self._refs = [
            image_2,
            image_3,
            qr_photo,
            button_image_continue,
            button_image_key_setup,
        ]

    def step3(self):
        import pyotp
        import tkinter

        step = 3
        self.canvas.create_rectangle(
            0, 0, 700, 70, fill=self.colors["header"], outline=""
        )
        self.canvas.create_rectangle(
            0, 630, 700, 700, fill=self.colors["header"], outline=""
        )
        image_2 = PhotoImage(file=relative_to_assets(step, "image_2.png"))
        self.canvas.create_image(350, 35, image=image_2)
        image_3 = PhotoImage(file=relative_to_assets(step, "image_3.png"))
        self.canvas.create_image(350, 218, image=image_3)
        self.canvas.create_text(
            131,
            338,
            anchor="nw",
            text="Enter 6 digit code:",
            fill="#FFFFFF",
            font=("Inter Light", -20),
        )
        # Entry fields (6)
        entry_images = [
            PhotoImage(file=relative_to_assets(step, f"entry_{i + 1}.png"))
            for i in range(6)
        ]
        for x, img in zip([160, 236, 312, 388, 464, 540], entry_images):
            self.canvas.create_image(x, 413.0, image=img)
        entry_fields = []
        entry_xs = [142, 218, 294, 370, 446, 522]
        for i in range(6):
            entry = Entry(
                self.root,
                bd=0,
                bg="#000000",
                fg="#FFFFFF",
                highlightthickness=0,
                insertbackground="#FFFFFF",
                font=("Segoe UI", 24),
                justify="center",
                show="\u2022",
            )
            entry.place(x=entry_xs[i], y=385.0, width=36.0, height=48.0)
            entry_fields.append(entry)

        def limit_to_one_digit(event):
            widget = event.widget
            value = widget.get()
            idx = entry_fields.index(widget)
            if len(value) > 1:
                widget.delete(1, "end")
                value = widget.get()
            elif value and not value[-1].isdigit():
                widget.delete(len(value) - 1, "end")
                value = widget.get()
            if event.keysym == "BackSpace" and value == "":
                if idx > 0:
                    entry_fields[idx - 1].focus_set()
                return
            if len(value) == 1:
                if idx < 5:
                    entry_fields[idx + 1].focus_set()
                else:
                    verify_button.invoke()

        for entry in entry_fields:
            entry.bind("<KeyRelease>", limit_to_one_digit)

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
                    connector = get_connector(self.db_path)
                    connector.execute_query(
                        "UPDATE [emp_list] SET [2FA Secret]=? WHERE username=?",
                        params=(encrypted_secret, self.username),
                    )
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

        button_image_verify = PhotoImage(file=relative_to_assets(step, "button_5.png"))
        verify_button = Button(
            self.root,
            image=button_image_verify,
            borderwidth=0,
            highlightthickness=0,
            bg="#000000",
            activebackground="#000000",
            command=on_verify,
            relief="flat",
        )
        verify_button.place(x=278.0, y=498.0, width=143.69, height=39.16)
        button_image_key_setup = PhotoImage(
            file=relative_to_assets(step, "button_1.png")
        )
        key_setup = Button(
            self.root,
            image=button_image_key_setup,
            borderwidth=0,
            highlightthickness=0,
            bg="#800000",
            activebackground="#800000",
            command=lambda: self.show_step(5),
            relief="flat",
        )
        key_setup.place(x=237.0, y=644.0, width=226.0, height=41.0)
        self._refs = [
            image_2,
            image_3,
            *entry_images,
            button_image_verify,
            button_image_key_setup,
        ]

    def step4(self):
        step = 4
        self.canvas.create_rectangle(
            0, 0, 700, 70, fill=self.colors["header"], outline=""
        )
        self.canvas.create_rectangle(
            0, 630, 700, 700, fill=self.colors["header"], outline=""
        )
        image_2 = PhotoImage(file=relative_to_assets(step, "image_2.png"))
        self.canvas.create_image(350, 35, image=image_2)
        image_3 = PhotoImage(file=relative_to_assets(step, "image_3.png"))
        self.canvas.create_image(349, 266, image=image_3)
        # Countdown logic
        self._countdown = 5
        self._countdown_text_id = self.canvas.create_text(
            180,
            362,
            anchor="nw",
            text=f"Going back to Generate page in ... {self._countdown}",
            fill="#FFFFFF",
            font=("Inter Light", -20),
        )

        def update_countdown():
            self._countdown -= 1
            if self._countdown > 0:
                self.canvas.itemconfig(
                    self._countdown_text_id,
                    text=f"Going back to Generate page in ... {self._countdown}",
                )
                self.root.after(1000, update_countdown)
            else:
                self.show_step(1)

        self.root.after(1000, update_countdown)
        button_image_return = PhotoImage(file=relative_to_assets(step, "button_4.png"))

        def close_window():
            if self.popup:
                self.root.destroy()
            else:
                if hasattr(self, "_modal_parent") and self._modal_parent:
                    self._modal_parent.destroy()
                else:
                    self.root.pack_forget()

        return_button = Button(
            self.root,
            image=button_image_return,
            borderwidth=0,
            highlightthickness=0,
            bg="#000000",
            activebackground="#000000",
            command=close_window,
            relief="flat",
        )
        return_button.place(x=263.0, y=500.0, width=174.76, height=42.03)
        self._refs = [image_2, image_3, button_image_return]

    def step5(self):
        import tkinter

        step = 5
        self.canvas.create_rectangle(
            0, 0, 700, 70, fill=self.colors["header"], outline=""
        )
        self.canvas.create_rectangle(
            0, 630, 700, 700, fill=self.colors["header"], outline=""
        )
        image_2 = PhotoImage(file=relative_to_assets(step, "image_2.png"))
        self.canvas.create_image(350, 35, image=image_2)
        image_3 = PhotoImage(file=relative_to_assets(step, "image_3.png"))
        self.canvas.create_image(349, 207, image=image_3)
        entry_image_1 = PhotoImage(file=relative_to_assets(step, "entry_1.png"))
        self.canvas.create_image(349.5, 379.0, image=entry_image_1)
        entry_1 = Entry(
            self.root,
            bd=0,
            bg="#000000",
            fg="#ffffff",
            highlightthickness=0,
            font=("Segoe UI", 20),
            disabledbackground="#000000",
            disabledforeground="#ffffff",
            insertbackground="#ffffff",
        )
        entry_1.place(x=104.0, y=350.0, width=491.0, height=58.0)
        self.canvas.create_text(
            87,
            291,
            anchor="nw",
            text="Enter your 2FA key to import:",
            fill="#FFFFFF",
            font=("Inter Light", -24),
        )

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
            button_image_submit = PhotoImage(
                file=relative_to_assets(step, "button_5.png")
            )
            submit_button = Button(
                self.root,
                image=button_image_submit,
                borderwidth=0,
                highlightthickness=0,
                bg="#000000",
                activebackground="#000000",
                command=None,
                relief="flat",
                state="disabled",
            )
            submit_button.place(x=281.0, y=459.0, width=138.6, height=51.77)
            self.root.after(1800, lambda: self.show_step(1))
            # Keep references to prevent garbage collection
            self._refs = [image_2, image_3, entry_image_1, button_image_submit]
            return

        # Check if user already has a 2FA secret
        already_has_2fa = False
        try:
            connector = get_connector(self.db_path)
            conn = connector.connect()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT [2FA Secret] FROM [emp_list] WHERE username=?", (self.username,)
            )
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            if row and row[0] and str(row[0]).strip():
                already_has_2fa = True
        except Exception as e:
            toast(f"DB Error: {e}", color="#800000")

        button_image_submit = PhotoImage(file=relative_to_assets(step, "button_5.png"))
        submit_button = Button(
            self.root,
            image=button_image_submit,
            borderwidth=0,
            highlightthickness=0,
            bg="#000000",
            activebackground="#000000",
            command=None,
            relief="flat",
        )
        submit_button.place(x=281.0, y=459.0, width=138.6, height=51.77)

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
                    connector = get_connector(self.db_path)
                    connector.execute_query(
                        "UPDATE [emp_list] SET [2FA Secret]=? WHERE username=?",
                        params=(encrypted_secret, self.username),
                    )
                    toast("2FA key imported!", color="#228B22")
                    self.show_step(4)
                except Exception as e:
                    toast(f"DB Error: {e}", color="#800000")

            submit_button.config(command=on_submit, state="normal")

    # Minimal helper to launch the wizard programmatically with an optional dark overlay


def launch_2fa_wizard(
    parent=None, username=None, db_path=None, fernet_key_path=None, colors=None
):
    overlay = None
    try:
        if parent:
            # Create a semi-transparent dark overlay to simulate blur/darken effect
            overlay = Toplevel(parent)
            overlay.overrideredirect(True)
            overlay.attributes("-alpha", 0.5)
            overlay.configure(bg="#000000")
            overlay.geometry(
                f"{parent.winfo_screenwidth()}x{parent.winfo_screenheight()}+0+0"
            )
            overlay.lift()
            overlay.grab_set()
        # Create modal window for wizard
        win = Toplevel(parent)
        win.overrideredirect(True)
        win.grab_set()  # Modal
        win.configure(bg=colors["bg"] if colors and "bg" in colors else "#000000")
        win.geometry(
            f"700x700+{win.winfo_screenwidth() // 2 - 350}+{win.winfo_screenheight() // 2 - 350}"
        )
        if overlay:
            win.lift(overlay)
        MultiStep2FAWizard(
            parent=win,
            username=username,
            db_path=db_path,
            fernet_key_path=fernet_key_path,
            popup=False,  # Use the provided window
            colors=colors or {"bg": "#000000", "header": "#800000"},
        )
        win.focus_set()
        win.wait_window()
    finally:
        if overlay:
            try:
                overlay.destroy()
            except Exception:
                pass


# Backwards-compatible wrapper expected by other modules
def open_2fa_wizard_modal(
    parent=None, username=None, db_path=None, fernet_key_path=None, colors=None
):
    """Compatibility wrapper for older imports that used open_2fa_wizard_modal.
    Delegates to launch_2fa_wizard.
    """
    return launch_2fa_wizard(
        parent=parent,
        username=username,
        db_path=db_path,
        fernet_key_path=fernet_key_path,
        colors=colors,
    )
