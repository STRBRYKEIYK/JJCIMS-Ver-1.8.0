import os
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFont
from .globals import global_state
from backend.config.gui_config import configure_window, center_window
from backend.database import get_connector
from backend.utils.window_icon import set_window_icon
# Sound imports removed

# Define colors - Dark muted pastel palette (consistent with dashboard)
BG_COLOR = "#2F3640"  # Dark charcoal background
HEADER_COLOR = "#40495A"  # Muted dark blue-gray for header
SIDEBAR_COLOR = "#535C68"  # Muted gray for sidebar
TEXT_PRIMARY = "#F5F6FA"  # Off-white text on dark backgrounds
TEXT_SECONDARY = "#A4B0BE"  # Muted light gray for secondary text
ACCENT_COLOR = "#70A1D7"  # Muted pastel blue for accents
BUTTON_PRIMARY = "#5F7C8A"  # Muted teal-gray for primary buttons
BUTTON_SECONDARY = "#6C7B7F"  # Muted slate gray for secondary buttons
SUCCESS_COLOR = "#7FB069"  # Muted pastel green for success
ERROR_COLOR = "#D63447"  # Muted red for errors
WARNING_COLOR = "#F8B500"  # Muted amber for warnings
TABLE_BG = "#40495A"  # Dark blue-gray table background
TABLE_HEADER = "#535C68"  # Muted gray table headers
SELECTION_COLOR = "#6C5CE7"  # Muted pastel purple for selections

# macOS-style control button colors
MACOS_RED = "#ff5f56"  # macOS close button red
MACOS_RED_HOVER = "#e0443e"  # macOS close button red hover
MACOS_YELLOW = "#ffbd2e"  # macOS minimize button yellow
MACOS_YELLOW_HOVER = "#dea123"  # macOS minimize button yellow hover

# Glow text colors - using palette colors instead of orange
GLOW_COLOR = (112, 161, 215)  # Accent color RGB for glow text (ACCENT_COLOR converted)
GLOW_COLOR_ALPHA = (112, 161, 215, 100)  # Accent color with alpha for glow effect
GLOW_COLOR_SOLID = (112, 161, 215, 255)  # Solid accent color for main text

# Legacy color variables for backward compatibility
RIGHT_BG = SIDEBAR_COLOR
FG_COLOR = TEXT_PRIMARY
ENTRY_BG = HEADER_COLOR
BUTTON_BG = BUTTON_PRIMARY
BUTTON_FG = TEXT_PRIMARY


def create_text_with_glow(text, font_size, is_bold=False):
    """Create text with glow effect (scanlines removed)"""
    # Create a temporary image with black background
    padding = 20
    img = Image.new("RGBA", (1000, font_size + padding * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Load font
    try:
        font_path = "C:\\Windows\\Fonts\\segoeui.ttf"  # Regular Segoe UI
        if is_bold:
            font_path = "C:\\Windows\\Fonts\\segoeuib.ttf"  # Bold Segoe UI
        font = ImageFont.truetype(font_path, font_size)
    except Exception:
        # Fallback to default
        font = ImageFont.load_default()

    # Get text size and position it
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # Create new image with exact text size
    img = Image.new(
        "RGBA", (text_width + padding * 2, text_height + padding * 2), (0, 0, 0, 0)
    )
    draw = ImageDraw.Draw(img)

    # Draw text with glow using accent color
    glow_color = GLOW_COLOR_ALPHA  # Accent color with alpha
    for offset in range(3):  # Glow effect
        draw.text((padding + offset, padding), text, font=font, fill=glow_color)
        draw.text((padding - offset, padding), text, font=font, fill=glow_color)
        draw.text((padding, padding + offset), text, font=font, fill=glow_color)
        draw.text((padding, padding - offset), text, font=font, fill=glow_color)

    # Main text
    draw.text(
        (padding, padding), text, font=font, fill=GLOW_COLOR_SOLID
    )  # Solid accent color

    # Return without scanline effect
    return ImageTk.PhotoImage(img)


class WelcomeWindow:
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
            color = SUCCESS_COLOR
            icon = "✔"
            if duration is None:
                duration = 6000
        elif type == "info":
            color = WARNING_COLOR
            icon = "ℹ"
            if duration is None:
                duration = 5000
        else:
            color = ERROR_COLOR
            icon = "✖"
            if duration is None:
                duration = 4000
        frame = tk.Frame(self._toast, bg=color)
        frame.pack(fill="both", expand=True)
        label = tk.Label(
            frame,
            text=f"{icon}  {message}",
            font=("Arial", 14, "bold"),
            bg=color,
            fg=TEXT_PRIMARY,
            padx=20,
            pady=10,
        )
        label.pack()
        self._toast.update_idletasks()
        # Animation: slide in from right (top right corner)
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

    def __init__(self):
        # Initialize the main window
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        configure_window(
            self.root,
            title="JJCFPIS - Dashboard",
            width=1024,
            height=768,
            resizable=True,
        )
        center_window(self.root)
        self.root.configure(bg=BG_COLOR)

        # Set window icon
        set_window_icon(self.root)

        # Left panel
        self._setup_left_panel()

        # Right panel
        self._setup_right_panel()

        # Add copyright label with glow effect
        copyright_label = tk.Label(
            self.left_panel,
            text="© 2025 JJC Inventory Management System made by Keith W. F.",
            font=("Arial", 10, "italic"),
            bg=BG_COLOR,
            fg=ACCENT_COLOR,
        )
        copyright_label.place(relx=0.5, rely=1.0, anchor="s", y=-5)

        self.load_employee_names()

    def load_employee_names(self):
        """Load all valid employee names and usernames from the Access database."""
        self.valid_name_parts = set()
        self.valid_full_names = set()  # Store valid full name combinations
        self.suggestion_list = []  # List of dicts: { 'first': ..., 'last': ..., 'middle': ..., 'username': ... }
        try:
            connector = get_connector()
            rows = connector.fetchall(
                "SELECT [First Name], [Last Name], [Middle Name], [Username] FROM [emp_list]"
            )
            for row in rows:
                first_name = str(row[0]).strip() if row[0] else ""
                last_name = str(row[1]).strip() if row[1] else ""
                middle_name = str(row[2]).strip() if row[2] else ""
                username = str(row[3]).strip() if row[3] else ""

                # Add individual parts to valid_name_parts for quick lookup
                if first_name:
                    for part in first_name.split():
                        self.valid_name_parts.add(part.lower())
                    self.valid_name_parts.add(first_name.lower())
                if last_name:
                    self.valid_name_parts.add(last_name.lower())
                if middle_name:
                    self.valid_name_parts.add(middle_name.lower())
                if username:
                    self.valid_name_parts.add(username.lower())

                # Add full name combinations to valid_full_names for employees without usernames
                if first_name and last_name:
                    # Add "First Last" combination
                    full_name = f"{first_name} {last_name}".lower()
                    self.valid_full_names.add(full_name)

                    # Add "First Middle Last" if middle name exists
                    if middle_name:
                        full_name_with_middle = (
                            f"{first_name} {middle_name} {last_name}".lower()
                        )
                        self.valid_full_names.add(full_name_with_middle)

                # Add to suggestion_list for display
                self.suggestion_list.append(
                    {
                        "first": first_name,
                        "last": last_name,
                        "middle": middle_name,
                        "username": username,
                    }
                )
        except Exception as e:
            print(f"Error loading employee names/usernames from Access DB: {e}")
            self.valid_name_parts = set()
            self.suggestion_list = []

    def _setup_left_panel(self):
        """Set up the left panel with logo and control buttons."""
        self.left_panel = tk.Frame(self.root, bg=BG_COLOR, width=800)
        self.left_panel.pack(side="left", fill="y")

        # Center contents vertically in the left panel
        self.left_panel_inner = tk.Frame(self.left_panel, bg=BG_COLOR)
        self.left_panel_inner.place(relx=0.5, rely=0.5, anchor="center")

        # Add logo with scanline effect
        self._add_logo()

        # Add control buttons (red, yellow)
        self._add_control_buttons()

    def _add_logo(self):
        """Add the logo without scanline effect to the left panel."""
        logo_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "assets", "emp_1.png")
        )
        original_img = Image.open(logo_path).resize(
            (750, 750), Image.Resampling.LANCZOS
        )
        self.logo_image = ImageTk.PhotoImage(original_img)

        logo_label = tk.Button(
            self.left_panel_inner,
            image=self.logo_image,
            bg=BG_COLOR,
            activebackground=BG_COLOR,  # Prevent white flash when clicking
            relief="flat",
            bd=0,
            cursor="hand2",
            highlightthickness=0,  # Remove focus highlight
            command=self.open_admin_login,  # Link to admin login
        )
        logo_label.image = (
            self.logo_image
        )  # Keep a reference to avoid garbage collection
        logo_label.pack(pady=10)

        # Add a thin outline
        logo_label.config(highlightbackground=TEXT_SECONDARY, highlightthickness=2)

    def _add_control_buttons(self):
        """Add macOS-style window control buttons (close, minimize) to the left panel."""
        self.control_buttons_frame = tk.Frame(
            self.left_panel, bg=BG_COLOR
        )  # Pure Black
        self.control_buttons_frame.place(relx=0.02, rely=0.02, anchor="nw")

        # macOS-style close (red) button
        close_btn = tk.Canvas(
            self.control_buttons_frame,
            width=22,
            height=22,
            bg=BG_COLOR,
            highlightthickness=0,
            bd=0,
        )
        close_btn.grid(row=0, column=0, padx=2)
        close_oval = close_btn.create_oval(
            3, 3, 19, 19, fill=MACOS_RED, outline=MACOS_RED_HOVER, width=2
        )
        close_btn.bind("<Button-1>", lambda event: self.close_program())

        def on_close_hover(e):
            close_btn.itemconfig(close_oval, fill=MACOS_RED_HOVER)

        def on_close_leave(e):
            close_btn.itemconfig(close_oval, fill=MACOS_RED)

        close_btn.bind("<Enter>", on_close_hover)
        close_btn.bind("<Leave>", on_close_leave)

        # macOS-style minimize (yellow) button
        min_btn = tk.Canvas(
            self.control_buttons_frame,
            width=22,
            height=22,
            bg=BG_COLOR,
            highlightthickness=0,
            bd=0,
        )
        min_btn.grid(row=0, column=1, padx=2)
        min_oval = min_btn.create_oval(
            3, 3, 19, 19, fill=MACOS_YELLOW, outline=MACOS_YELLOW_HOVER, width=2
        )
        min_btn.bind("<Button-1>", lambda event: self.hide_window())

        def on_min_hover(e):
            min_btn.itemconfig(min_oval, fill=MACOS_YELLOW_HOVER)

        def on_min_leave(e):
            min_btn.itemconfig(min_oval, fill=MACOS_YELLOW)

        min_btn.bind("<Enter>", on_min_hover)
        min_btn.bind("<Leave>", on_min_leave)

    def _setup_right_panel(self):
        """Set up the right panel with input fields and buttons."""
        self.right_panel = tk.Frame(self.root, bg=SIDEBAR_COLOR)  # Muted gray
        self.right_panel.pack(side="right", fill="both", expand=True)

        # Center contents vertically in the right panel
        self.right_panel_inner = tk.Frame(
            self.right_panel, bg=SIDEBAR_COLOR
        )  # Muted gray
        self.right_panel_inner.place(relx=0.5, rely=0.5, anchor="center")

        # Add input label, entry, error label, and continue button
        self._debounce_after_id = None
        self._add_input_fields()

    def _add_input_fields(self):
        """Add input fields and buttons to the right panel. Only create widgets if they don't already exist."""
        if hasattr(self, "entry") and self.entry.winfo_exists():
            return  # Prevent duplicate widgets
        name_img = create_text_with_glow(
            "Enter Your Name, Username, or Any Part", 36, is_bold=True
        )
        self.label = tk.Label(self.right_panel_inner, image=name_img, bg=SIDEBAR_COLOR)
        self.label.image = name_img
        self.label.pack(pady=20)

        self.entry = tk.Entry(
            self.right_panel_inner,
            font=("Arial", 18),
            width=30,
            relief="solid",
            bd=1,
            bg=HEADER_COLOR,
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
        )
        self.entry.pack(pady=10)

        # Suggestion box as a floating Toplevel (combobox style)
        self.suggestion_popup = None

        self.error_label = tk.Label(
            self.right_panel_inner,
            text="",
            font=("Arial", 16),
            fg=ERROR_COLOR,
            bg=SIDEBAR_COLOR,
        )
        self.error_label.pack(pady=10)

        self.entry.bind("<KeyRelease>", self._on_entry_keyrelease)
        self.entry.bind("<Return>", lambda event: self.continue_to_main())

        self.button = tk.Button(
            self.right_panel_inner,
            text="Continue",
            command=self.continue_to_main,
            bg=BUTTON_PRIMARY,
            fg=TEXT_PRIMARY,
            font=("Arial", 20, "bold"),
            width=20,
            relief="flat",
        )
        self.button.pack(pady=20)

    def _on_entry_keyrelease(self, event=None):
        typed = self.entry.get().strip().lower()
        if self._debounce_after_id:
            self.root.after_cancel(self._debounce_after_id)
        self._debounce_after_id = self.root.after(500, self.update_error_label)
        # Suggestion logic
        if typed:
            # Match against any part of name or username
            matches = [
                s
                for s in self.suggestion_list
                if typed in s["first"].lower()
                or typed in s["last"].lower()
                or typed in s["middle"].lower()
                or typed in s["username"].lower()
            ]
            if matches:
                self._show_suggestion_popup(matches)
            else:
                self._hide_suggestion_popup()
        else:
            self._hide_suggestion_popup()

    def _show_suggestion_popup(self, matches):
        # Destroy previous popup if exists
        self._hide_suggestion_popup()
        if not matches:
            return
        self.suggestion_popup = tk.Toplevel(self.root)
        self.suggestion_popup.wm_overrideredirect(True)
        self.suggestion_popup.attributes("-topmost", True)
        self.suggestion_popup.configure(bg=SIDEBAR_COLOR)
        # Position below entry
        self.suggestion_popup.update_idletasks()
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height()
        width = self.entry.winfo_width()
        self.suggestion_popup.geometry(f"{width}x{3 * 32}+{x}+{y}")
        # Listbox and scrollbar
        frame = tk.Frame(self.suggestion_popup, bg=SIDEBAR_COLOR)
        frame.pack(fill="both", expand=True)
        listbox = tk.Listbox(
            frame,
            font=("Arial", 16),
            width=30,
            height=3,
            bg=HEADER_COLOR,
            fg=TEXT_PRIMARY,
            selectbackground=ACCENT_COLOR,
            selectforeground=TEXT_PRIMARY,
            relief="solid",
            bd=1,
            activestyle="none",
        )
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=listbox.yview)
        listbox.config(yscrollcommand=scrollbar.set)
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        # Show suggestions as 'FirstName LastName (Username)' or just 'FirstName LastName' if no username
        for match in matches:
            if match["username"]:
                display = (
                    f"{match['first']} {match['last']} ({match['username']})".strip()
                )
            else:
                display = f"{match['first']} {match['last']}".strip()
            listbox.insert(tk.END, display)

        # Bind selection
        def on_select(event=None):
            selection = listbox.curselection()
            if selection:
                selected = matches[selection[0]]
                self.entry.delete(0, tk.END)
                # Fill entry with username if available, else full name
                if selected["username"]:
                    self.entry.insert(0, selected["username"])
                else:
                    self.entry.insert(0, f"{selected['first']} {selected['last']}")
                self._hide_suggestion_popup()

        listbox.bind("<<ListboxSelect>>", on_select)
        # Also allow click
        listbox.bind("<ButtonRelease-1>", on_select)

        # Hide popup if entry loses focus, but delay to allow selection event to process
        def delayed_hide_popup(event=None):
            self.root.after(100, self._hide_suggestion_popup)

        self.entry.bind("<FocusOut>", delayed_hide_popup)
        # Store reference for later hide
        self._suggestion_listbox_widget = listbox

    def _hide_suggestion_popup(self):
        if hasattr(self, "suggestion_popup") and self.suggestion_popup:
            self.suggestion_popup.destroy()
            self.suggestion_popup = None
        self._suggestion_listbox_widget = None

    # _on_suggestion_select removed; selection is handled in the popup combobox

    def _debounced_update_error_label(self, event=None):
        if self._debounce_after_id:
            self.root.after_cancel(self._debounce_after_id)
        self._debounce_after_id = self.root.after(500, self.update_error_label)

    def update_error_label(self, event=None):
        name = self.entry.get().strip().lower()
        display_name = self.entry.get().strip()
        if not name:
            self.show_toast("Please enter your name.", type="error")
        elif not name.replace(" ", "").isalpha():
            self.show_toast("Names can only have letters and spaces.", type="error")
        elif len(name.replace(" ", "")) < 2:
            self.show_toast("Name must be at least 2 characters.", type="error")
        elif (
            name != "username"
            and name not in self.valid_name_parts
            and name not in self.valid_full_names
        ):
            self.show_toast(
                "Sorry, only registered employees can access this system.", type="error"
            )
        else:
            # Show recognized user feedback as a success toast
            self.show_toast(f"Hi {display_name}, you're good to go!", type="success")

    def show_custom_prompt(self, title, message):
        """Show a custom OK/Cancel prompt styled with the app's color palette, borderless and centered, with a border outline and perfectly fitted text/buttons."""
        prompt = tk.Toplevel(self.root)
        prompt.title(title)
        prompt.configure(
            bg=SIDEBAR_COLOR, highlightbackground=TEXT_SECONDARY, highlightthickness=2
        )  # Add border
        prompt.geometry("600x320")
        prompt.overrideredirect(True)
        prompt.grab_set()
        prompt.resizable(False, False)
        prompt.update_idletasks()
        x = (prompt.winfo_screenwidth() // 2) - (600 // 2)
        y = (prompt.winfo_screenheight() // 2) - (320 // 2)
        prompt.geometry(f"600x320+{x}+{y}")
        # Message
        label = tk.Label(
            prompt,
            text=message,
            font=("Arial", 18, "bold"),
            bg=SIDEBAR_COLOR,
            fg=ACCENT_COLOR,
            wraplength=560,
            justify="center",
        )
        label.pack(pady=(36, 24), padx=20, fill="x")
        # Button frame
        btn_frame = tk.Frame(prompt, bg=SIDEBAR_COLOR)
        btn_frame.pack(pady=0)
        result = {"answer": None}

        def on_yes():
            result["answer"] = True
            prompt.destroy()

        def on_no():
            result["answer"] = False
            prompt.destroy()

        yes_btn = tk.Button(
            btn_frame,
            text="Yes",
            font=("Arial", 15, "bold"),
            bg=BUTTON_PRIMARY,
            fg=TEXT_PRIMARY,
            width=16,
            height=2,
            relief="flat",
            command=on_yes,
            activebackground=BUTTON_PRIMARY,
            activeforeground=TEXT_PRIMARY,
        )
        yes_btn.pack(side="left", padx=30, ipadx=10, ipady=2, expand=True, fill="x")
        no_btn = tk.Button(
            btn_frame,
            text="No",
            font=("Arial", 15, "bold"),
            bg=ERROR_COLOR,
            fg=TEXT_PRIMARY,
            width=16,
            height=2,
            relief="flat",
            command=on_no,
            activebackground=ERROR_COLOR,
            activeforeground=TEXT_PRIMARY,
        )
        no_btn.pack(side="right", padx=30, ipadx=10, ipady=2, expand=True, fill="x")
        # Add space below the buttons
        tk.Frame(prompt, height=36, bg=SIDEBAR_COLOR).pack()
        prompt.wait_window()
        return result["answer"]

    def get_username_for_name(self, name):
        """Get the username for the given name from the Access database."""
        try:
            connector = get_connector()
            rows = connector.fetchall(
                "SELECT [Username], [First Name], [Last Name], [Middle Name] FROM [emp_list]"
            )

            input_lower = name.lower().strip()

            for row in rows:
                username = str(row[0]).strip() if row[0] else ""
                first_name = str(row[1]).strip() if row[1] else ""
                last_name = str(row[2]).strip() if row[2] else ""
                middle_name = str(row[3]).strip() if row[3] else ""

                # Check for exact matches
                if (
                    input_lower == first_name.lower()
                    or input_lower == last_name.lower()
                    or input_lower == username.lower()
                    or input_lower == f"{first_name} {last_name}".lower()
                    or (
                        middle_name
                        and input_lower
                        == f"{first_name} {middle_name} {last_name}".lower()
                    )
                    or (first_name and input_lower in first_name.lower().split())
                ):
                    return username if username else None
            return None
        except Exception as e:
            print(f"Error fetching username: {e}")
            return None

    def get_access_level(self, name):
        """Get the access level for the given name or username from the Access database."""
        try:
            connector = get_connector()
            rows = connector.fetchall(
                "SELECT [Access Level], [First Name], [Last Name], [Middle Name], [Username] FROM [emp_list]"
            )

            input_lower = name.lower().strip()

            for row in rows:
                access_level = row[0]
                first_name = str(row[1]).strip() if row[1] else ""
                last_name = str(row[2]).strip() if row[2] else ""
                middle_name = str(row[3]).strip() if row[3] else ""
                username = str(row[4]).strip() if row[4] else ""

                # Check for exact matches
                if (
                    input_lower == first_name.lower()
                    or input_lower == last_name.lower()
                    or input_lower == username.lower()
                    or input_lower == f"{first_name} {last_name}".lower()
                    or (
                        middle_name
                        and input_lower
                        == f"{first_name} {middle_name} {last_name}".lower()
                    )
                    or (first_name and input_lower in first_name.lower().split())
                ):
                    return access_level
            return None
        except Exception as e:
            print(f"Error fetching access level: {e}")
            return None

    def continue_to_main(self):
        """Validate input and proceed to the main browser or admin login based on access level."""
        name = self.entry.get().strip()
        name_lower = name.lower()
        if not name_lower:
            self.show_toast("Please enter your name.", type="error")
            return
        if not name_lower.replace(" ", "").isalpha():
            self.show_toast("Names can only have letters and spaces.", type="error")
            return
        if len(name_lower.replace(" ", "")) < 2:
            self.show_toast("Name must be at least 2 characters.", type="error")
            return
        # Allow either a valid employee name, full name, or the literal 'username'
        if (
            name_lower != "username"
            and name_lower not in self.valid_name_parts
            and name_lower not in self.valid_full_names
        ):
            self.show_toast(
                "Sorry, only registered employees or 'username' can access this system.",
                type="error",
            )
            return
        # Check access level
        access_level = self.get_access_level(name)
        if name_lower == "username":
            access_level = "Level 3"  # Always treat Username as Level 3
        if access_level in ("Level 2", "Level 3"):
            self.show_toast(f"Hi {name}, you're good to go!", type="success")
            msg = f"You have Access [{access_level}].\n\nDo you want to continue to the Employee Dashboard or go to Admin Login?"
            choice = self.show_dashboard_or_admin_prompt(msg)
            if choice == "admin":
                self.root.destroy()
                from gui.admin_login import AdminLogin

                # Get the actual username for admin login prefill
                if name_lower == "username":
                    admin_login = AdminLogin(prefill_username="username")
                else:
                    username = self.get_username_for_name(name)
                    if username:
                        admin_login = AdminLogin(prefill_username=username)
                    else:
                        admin_login = AdminLogin(prefill_username=name)
                admin_login.run()
                return
            self.login(name)
        elif access_level == "Level 1":
            self.show_toast(f"Hi {name}, you're good to go!", type="success")
            self.login(name)
        else:
            self.show_toast("Access level not found or not permitted.", type="error")
            return

    def show_dashboard_or_admin_prompt(self, message):
        """Prompt user to choose between Employee Dashboard and Admin Login."""
        prompt = tk.Toplevel(self.root)
        prompt.title("Access Level Choice")
        prompt.configure(
            bg=SIDEBAR_COLOR, highlightbackground=TEXT_SECONDARY, highlightthickness=2
        )
        prompt.geometry("600x320")
        prompt.overrideredirect(True)
        prompt.grab_set()
        prompt.resizable(False, False)
        prompt.update_idletasks()
        x = (prompt.winfo_screenwidth() // 2) - (600 // 2)
        y = (prompt.winfo_screenheight() // 2) - (320 // 2)
        prompt.geometry(f"600x320+{x}+{y}")
        label = tk.Label(
            prompt,
            text=message,
            font=("Arial", 18, "bold"),
            bg=SIDEBAR_COLOR,
            fg=ACCENT_COLOR,
            wraplength=560,
            justify="center",
        )
        label.pack(pady=(36, 24), padx=20, fill="x")
        btn_frame = tk.Frame(prompt, bg=SIDEBAR_COLOR)
        btn_frame.pack(pady=0)
        result = {"choice": None}

        def to_dashboard():
            result["choice"] = "dashboard"
            prompt.destroy()

        def to_admin():
            result["choice"] = "admin"
            prompt.destroy()

        dash_btn = tk.Button(
            btn_frame,
            text="Employee Dashboard",
            font=("Arial", 15, "bold"),
            bg=BUTTON_PRIMARY,
            fg=TEXT_PRIMARY,
            width=18,
            height=2,
            relief="flat",
            command=to_dashboard,
            activebackground=BUTTON_PRIMARY,
            activeforeground=TEXT_PRIMARY,
        )
        dash_btn.pack(side="left", padx=30, ipadx=10, ipady=2, expand=True, fill="x")
        admin_btn = tk.Button(
            btn_frame,
            text="Admin Login",
            font=("Arial", 15, "bold"),
            bg=ERROR_COLOR,
            fg=TEXT_PRIMARY,
            width=18,
            height=2,
            relief="flat",
            command=to_admin,
            activebackground=ERROR_COLOR,
            activeforeground=TEXT_PRIMARY,
        )
        admin_btn.pack(side="right", padx=30, ipadx=10, ipady=2, expand=True, fill="x")
        tk.Frame(prompt, height=36, bg=SIDEBAR_COLOR).pack()
        prompt.wait_window()
        return result["choice"]

    def open_admin_login(self):
        """Prompt the user before proceeding to the admin login with custom style."""
        # Sound removed

        msg = (
            "This section is for Admins and C.T.Os only.\n\n"
            + "If you're not one of these, please go back.\n\n"
            + "Do you want to continue?"
        )
        answer = self.show_custom_prompt("Admin Login", msg)

        # Sound removed

        if answer:
            self.root.destroy()
            from gui.admin_login import AdminLogin

            admin_login = AdminLogin()
            admin_login.run()

    def get_display_name_for_dashboard(self, input_name):
        """Get the appropriate display name for the dashboard - username if available, else full name."""
        try:
            connector = get_connector()
            rows = connector.fetchall(
                "SELECT [First Name], [Last Name], [Middle Name], [Username] FROM [emp_list]"
            )

            input_lower = input_name.lower().strip()

            for row in rows:
                first_name = str(row[0]).strip() if row[0] else ""
                last_name = str(row[1]).strip() if row[1] else ""
                middle_name = str(row[2]).strip() if row[2] else ""
                username = str(row[3]).strip() if row[3] else ""

                # Check for exact matches
                if (
                    input_lower == first_name.lower()
                    or input_lower == last_name.lower()
                    or input_lower == username.lower()
                    or input_lower == f"{first_name} {last_name}".lower()
                    or (
                        middle_name
                        and input_lower
                        == f"{first_name} {middle_name} {last_name}".lower()
                    )
                    or (first_name and input_lower in first_name.lower().split())
                ):
                    # Return username if available, else full name
                    if username:
                        return username
                    else:
                        return f"{first_name} {last_name}".strip()
            return input_name  # Fallback to original input
        except Exception as e:
            print(f"Error getting display name: {e}")
            return input_name

    def login(self, username):
        """Handle user login with a 2-second delay before opening the dashboard."""
        # Get the appropriate display name for the dashboard
        display_name = self.get_display_name_for_dashboard(username)
        global_state.current_user = display_name
        print(f"Logged in as: {global_state.current_user}")

        # Sound removed
        def proceed():
            self.root.destroy()  # Destroy the current window
            from gui.employee_dashboard import MainBrowser

            main_browser = MainBrowser()  # Reinitialize the dashboard
            main_browser.run()  # Run the employee dashboard

        self.root.after(1000, proceed)

    def close_program(self):
        """Close the program."""
        self.root.destroy()

    def hide_window(self):
        """Minimize the window."""
        self.root.iconify()

    def run(self):
        """Run the main loop."""
        self.root.mainloop()
