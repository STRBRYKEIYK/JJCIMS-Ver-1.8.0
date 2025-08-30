import tkinter as tk
from tkinter import ttk
from tkinter.ttk import Separator
from pathlib import Path
from .globals import global_state
from backend.config.gui_config import configure_window, center_window
from backend.database import get_connector, get_db_path
from .functions.emplydash_f.emplydash_utils import (
    focus_next_widget,
    update_clock,
    filter_items as util_filter_items,
)
from .functions.emplydash_f.checkbox_treeview import CheckboxTreeview
from .functions.style.admscrl import configure_custom_scrollbar
from PIL import Image, ImageTk
from backend.utils.window_icon import set_window_icon
from backend.utils.notification_manager import NotificationManager
# Removed unused imports: numpy, create_window_icon
# Sound imports removed

# Define colors - Dark muted pastel palette
BG_COLOR = "#40495A"  # Dark charcoal background
HEADER_COLOR = "#40495A"  # Muted dark blue-gray for header
SIDEBAR_COLOR = "#40495A"  # Muted gray for sidebar
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


class MainBrowser:
    def refresh_type_buttons(self):
        # Remove existing type buttons (except Out of Stock and Back to Login)
        if hasattr(self, "type_buttons"):
            for btn in self.type_buttons:
                btn.destroy()
        self.type_buttons = []
        # Fetch unique types from the database
        try:
            from backend.database import get_connector

            db = get_connector()
            db.connect()
            cursor = db.connection.cursor()
            cursor.execute(
                "SELECT DISTINCT [TYPE] FROM [ITEMSDB] WHERE [TYPE] IS NOT NULL AND [TYPE] <> ''"
            )
            type_rows = cursor.fetchall()
            db.connection.close()
            unique_types = sorted(set(row[0].strip() for row in type_rows if row[0]))
        except Exception as e:
            print(f"Error fetching types: {e}")
            unique_types = []

        # Always add 'All' at the top
        def add_type_button(item_type):
            btn = tk.Button(
                self.sidebar,
                text=item_type,
                bg=BUTTON_SECONDARY,
                fg=TEXT_PRIMARY,
                font=("Arial", 10, "bold"),
                command=lambda t=item_type: self.filter_by_type(t),
            )
            btn.pack(fill=tk.X, pady=5, padx=5)
            self.type_buttons.append(btn)

        add_type_button("All")
        for item_type in unique_types:
            add_type_button(item_type)

    def show_skeleton_screen(self, rows=8):
        """Display a skeleton screen in the table area while loading data."""
        import tkinter as tk
        from tkinter import ttk

        # Remove any existing table and scrollbar
        if hasattr(self, "table") and self.table:
            self.table.destroy()
        if hasattr(self, "scroll_y") and self.scroll_y:
            self.scroll_y.destroy()
        self.scroll_y = ttk.Scrollbar(
            self.treeview_container,
            orient=tk.VERTICAL,
            style="Custom.Vertical.TScrollbar",
        )
        self.table = ttk.Treeview(
            self.treeview_container,
            columns=(
                "NAME",
                "BRAND",
                "TYPE",
                "LOCATION",
                "UNIT OF MEASURE",
                "STATUS",
                "BALANCE",
            ),
            show="headings",
            yscrollcommand=self.scroll_y.set,
            style="Custom.Treeview",
        )
        self.scroll_y.config(command=self.table.yview)
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # Set up columns
        columns = (
            "NAME",
            "BRAND",
            "TYPE",
            "LOCATION",
            "UNIT OF MEASURE",
            "STATUS",
            "BALANCE",
        )
        for col in columns:
            self.table.heading(col, text=col)
            self.table.column(col, anchor="w")
        # Insert skeleton rows (gray rectangles)
        for _ in range(rows):
            self.table.insert("", "end", values=["" for _ in columns])
        # Overlay rectangles using tags and style
        style = ttk.Style()
        style.configure("Skeleton.Treeview", background="#e0e0e0", foreground="#e0e0e0")
        self.table.tag_configure("skeleton", background="#e0e0e0", foreground="#e0e0e0")
        for item in self.table.get_children():
            self.table.item(item, tags=("skeleton",))

    def __init__(self):
        print(f"Current user in MainBrowser: {global_state.current_user}")  # Debugging
        self.root = tk.Tk()
        self.root.protocol(
            "WM_DELETE_WINDOW", self.on_close
        )  # Handle window close event
        self.root.attributes("-fullscreen", True)
        configure_window(
            self.root,
            title="JJCFPIS - Dashboard",
            width=1024,
            height=768,
            resizable=True,
        )
        center_window(self.root)
        self.root.configure(bg=BG_COLOR)  # Dark blue-gray

        # Set window icon
        set_window_icon(self.root)

        # Initialize notification manager
        self.notification_manager = NotificationManager(self.root)

        # Database connection via centralized helpers
        try:
            self.db = get_connector(get_db_path())
            self.db.connect()
        except Exception as e:
            print(f"Error connecting to database: {e}")
            self.notification_manager.show_notification(
                "Database Error",
                "Failed to connect to the database. Please check the configuration.",
                duration=5000,
                type_="error",
            )

        # Header
        self.header = tk.Frame(self.root, bg=HEADER_COLOR, height=80)  # Header color
        self.header.pack(side=tk.TOP, fill=tk.X)

        # Replace title label with a clickable image
        try:
            logo_path = (
                Path(__file__).resolve().parent.parent / "assets" / "emp_dash.png"
            )
            original_img = Image.open(str(logo_path))

            # Resize to a smaller size (e.g., 300px width while maintaining aspect ratio)
            aspect_ratio = original_img.height / original_img.width
            new_width = 300
            new_height = int(new_width * aspect_ratio)
            resized_img = original_img.resize(
                (new_width, new_height), Image.Resampling.LANCZOS
            )

            # Use image without scanline effects
            self.logo_image = ImageTk.PhotoImage(resized_img)

            self.logo_label = tk.Label(
                self.header,
                image=self.logo_image,
                bg=HEADER_COLOR,  # Header color
                cursor="hand2",
            )
            self.logo_label.pack(side=tk.LEFT, padx=10, pady=5)
            self.logo_label.bind("<Button-1>", lambda event: self.go_back_to_welcome())
        except Exception as e:
            print(f"Error loading logo image: {e}")

        self.search_entry = tk.Entry(self.header, font=("Arial", 12), width=40)
        self.search_entry.pack(side=tk.LEFT, padx=10, pady=5)  # Adjusted padding
        self.search_entry.bind("<KeyRelease>", self.search_items)

        # Restore original tk.Buttons and remove MacOS.TButton style
        self.search_button = tk.Button(
            self.header,
            text="Search",
            command=self.search_items,
            bg=BUTTON_PRIMARY,
            fg=TEXT_PRIMARY,
        )
        self.search_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Create a Toplevel widget for autocomplete suggestions
        self.suggestions_popup = tk.Toplevel(self.root)
        self.suggestions_popup.withdraw()  # Hide initially
        self.suggestions_popup.overrideredirect(True)  # Remove window decorations
        self.suggestions_popup.configure(bg=SIDEBAR_COLOR)  # Light gray

        # Add a Listbox to the popup for displaying suggestions
        self.suggestions_listbox = tk.Listbox(
            self.suggestions_popup,
            font=("Arial", 12),
            bg=SIDEBAR_COLOR,  # Light gray
            fg=TEXT_PRIMARY,  # Dark text
            selectbackground=SELECTION_COLOR,  # Light blue selection
            selectforeground=TEXT_PRIMARY,  # Dark text on selection
            activestyle="none",
        )
        self.suggestions_listbox.pack(fill=tk.BOTH, expand=True)

        # Bind events for selecting suggestions
        self.suggestions_listbox.bind("<<ListboxSelect>>", self.select_suggestion)
        self.suggestions_listbox.bind("<Return>", self.select_suggestion)
        self.suggestions_listbox.bind(
            "<Escape>", lambda e: self.suggestions_popup.withdraw()
        )

        # Bind focus-out event to hide the popup
        self.search_entry.bind(
            "<FocusOut>", lambda e: self.suggestions_popup.withdraw()
        )

        # Sidebar
        self.sidebar = tk.Frame(
            self.root, bg=SIDEBAR_COLOR, width=600
        )  # Light gray sidebar
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        Separator(self.sidebar, orient="horizontal").pack(fill=tk.X, padx=10, pady=5)
        Separator(self.sidebar, orient="horizontal").pack(fill=tk.X, padx=10, pady=5)
        # Display the current user at the top of the sidebar, above the buttons
        self.user_label = tk.Label(
            self.sidebar,
            text=f"Employee: {global_state.current_user}",
            font=("Arial", 14, "bold"),
            bg=SIDEBAR_COLOR,  # Light gray
            fg=TEXT_PRIMARY,  # Dark text
            anchor="w",
        )
        self.user_label.pack(
            side=tk.TOP, anchor="w", padx=10, pady=10
        )  # Adjust padding for alignment
        Separator(self.sidebar, orient="horizontal").pack(fill=tk.X, padx=10, pady=5)
        Separator(self.sidebar, orient="horizontal").pack(fill=tk.X, padx=10, pady=5)

        # Add dynamic type filter buttons
        self.type_buttons = []
        self.refresh_type_buttons()

        # Add "Back to Login" button immediately after the 'Out of Stock' button
        self.back_to_login_button = tk.Button(
            self.sidebar,
            text="🔙 Back to Login",
            command=self.go_back,
            bg=ERROR_COLOR,
            fg="white",
            font=("Arial", 12, "bold"),
        )
        self.back_to_login_button.pack(fill=tk.X, pady=5, padx=5)

        Separator(self.sidebar, orient="horizontal").pack(fill=tk.X, padx=10, pady=5)

        # Add "TYPES" label above the type filter buttons
        self.type_filter_label = tk.Label(
            self.sidebar,
            text="TYPES",
            font=("Arial", 12, "bold"),
            bg=SIDEBAR_COLOR,  # Light gray
            fg=ACCENT_COLOR,  # Soft blue accent
            anchor="center",
        )
        self.type_filter_label.pack(side=tk.TOP)  # Center-align the label

        Separator(self.sidebar, orient="horizontal").pack(fill=tk.X, padx=10, pady=5)

        # Add 'Out of Stock' filter button after type filter buttons
        self.out_of_stock_btn = tk.Button(
            self.sidebar,
            text="Out of Stock",
            bg=BUTTON_SECONDARY,
            fg=TEXT_PRIMARY,
            font=("Arial", 10, "bold"),
            command=lambda: self.filter_by_type("Out of Stock"),
        )
        self.out_of_stock_btn.pack(fill=tk.X, pady=5, padx=5)

        Separator(self.sidebar, orient="horizontal").pack(fill=tk.X, padx=10, pady=5)

        # Add a spacer frame at the bottom for layout consistency
        spacer = tk.Frame(self.sidebar, bg=SIDEBAR_COLOR, height=30)  # Light gray
        spacer.pack(side=tk.BOTTOM, fill=tk.X)

        # Table Frame
        self.table_frame = tk.Frame(
            self.root, bg=BG_COLOR, width=1400
        )  # Dark background
        self.table_frame.pack(
            side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10
        )

        # Configure custom scrollbar style
        configure_custom_scrollbar()

        # Create a container frame for the treeview and scrollbar
        self.treeview_container = tk.Frame(self.table_frame, bg=BG_COLOR)
        self.treeview_container.pack(fill=tk.BOTH, expand=True)

        # Create and apply a custom Treeview style for the metal fabrication theme
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Custom.Treeview",
            font=("Arial", 12, "normal"),  # Smaller, normal font for better readability
            rowheight=32,  # Slightly smaller row height
            background=TABLE_BG,  # Dark blue-gray background for readability
            fieldbackground=TABLE_BG,  # Dark blue-gray field background
            foreground=TEXT_PRIMARY,  # Light text for contrast
            bordercolor="#5D6D7E",  # Muted border
            borderwidth=1,
        )
        style.map(
            "Custom.Treeview",
            background=[("selected", SELECTION_COLOR)],  # Light blue when selected
            foreground=[("selected", TEXT_PRIMARY)],  # Dark text when selected
        )
        style.configure(
            "Custom.Treeview.Heading",
            font=("Arial", 12, "bold"),
            background=TABLE_HEADER,  # Muted gray for headers
            foreground=TEXT_PRIMARY,  # Light text for headers
            bordercolor="#5D6D7E",  # Muted header border
            borderwidth=1,
        )
        style.map(
            "Custom.Treeview.Heading",
            background=[("active", "#6C7B7F")],  # Muted hover effect
            foreground=[("active", TEXT_PRIMARY)],
        )

        # Create scrollbar for the table in the container
        self.scroll_y = ttk.Scrollbar(
            self.treeview_container,
            orient=tk.VERTICAL,
            style="Custom.Vertical.TScrollbar",
        )

        # Create the table widget with the custom style in the container
        self.table = CheckboxTreeview(
            self.treeview_container,
            columns=(
                "NAME",
                "BRAND",
                "TYPE",
                "LOCATION",
                "UNIT OF MEASURE",
                "STATUS",
                "BALANCE",
            ),
            show="headings",
            style="Custom.Treeview",
            yscrollcommand=self.scroll_y.set,
        )

        self.table.heading("NAME", text="NAME")
        self.table.heading("BRAND", text="BRAND")
        self.table.heading("TYPE", text="TYPE")
        self.table.heading("LOCATION", text="LOCATION")
        self.table.heading("UNIT OF MEASURE", text="UNIT OF MEASURE")
        self.table.heading("STATUS", text="STATUS")
        self.table.heading("BALANCE", text="BALANCE")

        # Configure column widths
        self.table.column("NAME", width=200, anchor="w")
        self.table.column("BRAND", width=150, anchor="w")
        self.table.column("TYPE", width=150, anchor="w")
        self.table.column("LOCATION", width=150, anchor="w")
        self.table.column("UNIT OF MEASURE", width=120, anchor="w")
        self.table.column("STATUS", width=120, anchor="w")
        self.table.column("BALANCE", width=100, anchor="w")

        # Configure and pack scrollbar and table in the container
        self.scroll_y.config(command=self.table.yview)
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Enable multiple selection in the table
        self.table["selectmode"] = "extended"

        # Bind single-click to check/uncheck
        self.table.bind("<Button-1>", self.on_table_single_click)

        # Bottom Panel (directly under the Treeview)
        self.bottom_panel = tk.Frame(self.table_frame, bg=BG_COLOR)  # Dark background
        self.bottom_panel.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        # Status label (centered both vertically and horizontally in the bottom panel)
        self.status_label = tk.Label(
            self.bottom_panel,
            text="",
            font=("Arial", 16, "bold"),
            fg=TEXT_PRIMARY,  # Light text
            bg=BG_COLOR,  # Dark background
            anchor="center",  # Center text
            justify="center",
        )
        self.status_label.pack(
            side=tk.TOP, pady=5, padx=0, fill=tk.X, expand=True
        )  # Center horizontally and vertically

        # Add a real-time clock to the header
        self.clock_label = tk.Label(
            self.header,
            text="",
            font=("Arial", 12, "bold"),
            bg=HEADER_COLOR,  # Header color
            fg=TEXT_PRIMARY,  # Light text
            anchor="e",
        )
        self.clock_label.pack(side=tk.RIGHT, padx=10, pady=5)  # Adjusted padding
        self.update_clock_id = self.root.after(1000, self.update_clock)

        # Automatically focus the search box on window load
        self.root.after(100, lambda: self.safe_focus_search_entry())

        # Add tooltips to buttons
        self.add_tooltip(self.search_button, "Click to search items")

        # Improve keyboard navigation
        self.root.bind("<Tab>", focus_next_widget)
        self.root.bind("<Return>", lambda e: self.search_items())

        # Load initial data after UI is ready for faster perceived load
        self.root.after(100, self.load_items)

        # Bind focus events to pause and resume updates
        self.root.bind("<FocusIn>", self.resume_updates)
        self.root.bind("<FocusOut>", self.pause_updates)

        # Initialize a flag to track whether updates are paused
        self.updates_paused = False

        # Add keyboard shortcuts for common actions
        self.root.bind("<Control-f>", lambda e: self.search_entry.focus())
        self.root.bind("<Escape>", lambda e: self.go_back())

        # Add a session timer with auto-logout
        self.session_duration = 30 * 60  # 30 minutes
        self.time_remaining = self.session_duration
        self.update_timer_id = self.root.after(
            1000, self.update_session_timer
        )  # Start the timer

        self.is_closing = False

        # Add copyright label at the bottom center of the bottom panel
        self.copyright_label = tk.Label(
            self.bottom_panel,
            text="© 2025 JJC Fabrication Process Information System made by KWF",
            font=("Arial", 10, "italic"),
            bg=BG_COLOR,  # Dark background
            fg=TEXT_SECONDARY,  # Muted secondary text
        )
        self.copyright_label.place(relx=0.5, rely=1.0, anchor="s", y=1)

        # Create cart button frame
        self.cart_frame = tk.Frame(self.bottom_panel, bg=BG_COLOR)
        self.cart_frame.pack(side=tk.RIGHT, padx=20, pady=5)

        # Load cart button image
        try:
            cart_image_path = (
                Path(__file__).resolve().parent.parent / "assets" / "cart_button.png"
            )
            cart_img = Image.open(str(cart_image_path))
            # Resize to appropriate size
            cart_img = cart_img.resize((40, 40), Image.Resampling.LANCZOS)
            self.cart_image = ImageTk.PhotoImage(cart_img)
        except Exception as e:
            print(f"Error loading cart image: {e}")
            self.cart_image = None

        # Create cart button container
        self.cart_button_container = tk.Frame(self.cart_frame, bg=BG_COLOR)
        self.cart_button_container.pack()

        # Cart button with image
        if self.cart_image:
            self.cart_button = tk.Button(
                self.cart_button_container,
                image=self.cart_image,
                command=self.go_to_checkout,
                bg=BG_COLOR,
                fg=TEXT_PRIMARY,
                borderwidth=0,
                relief="flat",
                state=tk.DISABLED,
                cursor="hand2",
            )
        else:
            # Fallback text button if image fails to load
            self.cart_button = tk.Button(
                self.cart_button_container,
                text="🛒",
                command=self.go_to_checkout,
                bg=SUCCESS_COLOR,
                fg="white",
                font=("Arial", 20),
                borderwidth=0,
                relief="flat",
                state=tk.DISABLED,
                cursor="hand2",
            )

        self.cart_button.pack()

        # Cart counter (shows number of selected items)
        self.cart_counter = tk.Label(
            self.cart_button_container,
            text="0",
            bg=ERROR_COLOR,
            fg="white",
            font=("Arial", 10, "bold"),
            width=2,
            height=1,
            relief="flat",
        )
        self.cart_counter.place(x=25, y=-5)  # Position in top-right of button
        self.cart_counter.configure(state="disabled")  # Initially hidden

        # "Go to Cart" label
        self.cart_label = tk.Label(
            self.cart_frame,
            text="Go to Cart",
            bg=BG_COLOR,
            fg=TEXT_PRIMARY,
            font=("Arial", 10),
        )
        self.cart_label.pack(pady=(5, 0))

        # Enable sorting by clicking on column headers
        for col in (
            "NAME",
            "BRAND",
            "TYPE",
            "LOCATION",
            "UNIT OF MEASURE",
            "STATUS",
            "BALANCE",
        ):
            self.table.heading(
                col, text=col, command=lambda _col=col: self.sort_by_column(_col, False)
            )

        # Bind checkbox toggling to update the cart button state
        self.table.bind("<<CheckboxToggled>>", self.update_cart_button_state)
        self.update_cart_button_state()  # Ensure correct state on startup

        # (macOS-style window controls removed, revert to original)

    def update_clock(self):
        if getattr(self, "is_closing", False):
            return
        try:
            if not self.root.winfo_exists():
                return
            update_clock(self.clock_label, self.root, [self.update_clock_id])
        except tk.TclError:
            # Widget has been destroyed
            return
        except Exception as e:
            print(f"Error in update_clock: {e}")
            return

    def add_tooltip(self, widget, text):
        pass  # Now imported from utils

    def focus_next_widget(self, event):
        pass  # Now imported from utils

    def get_checked_items(self):
        """Get a set of currently checked item names."""
        checked_items = set()
        try:
            checked_items = self.table.get_checked()
            existing_items = set(self.table.get_children())
            for item in checked_items:
                try:
                    # Check if the item still exists in the table
                    if item in existing_items:
                        values = self.table.item(item)["values"]
                        if values and len(values) > 0:
                            item_name = values[0]  # Items is the first column
                            checked_items.add(item_name)
                except (IndexError, KeyError, tk.TclError) as e:
                    print(f"Warning: Could not get material name for item {item}: {e}")
                    continue
        except Exception as e:
            print(f"Error getting checked items: {e}")
        return checked_items

    def restore_checked_items(self, previously_checked):
        """Restore checkbox state for items that were previously checked."""
        try:
            for item in self.table.get_children():
                try:
                    values = self.table.item(item)["values"]
                    if values and len(values) > 0:
                        item_name = values[0]  # Items is the first column
                        if item_name in previously_checked:
                            self.table.set_checked(item, True)
                except (IndexError, KeyError, tk.TclError) as e:
                    print(f"Warning: Could not restore checkbox for item {item}: {e}")
                    continue
            # Update the cart button state after restoring checkboxes
            self.update_cart_button_state()
        except Exception as e:
            print(f"Error restoring checked items: {e}")

    def load_items(self):
        # Refresh type filter buttons before loading items
        self.refresh_type_buttons()
        # Only load items if table and root still exist
        if (
            not hasattr(self, "table")
            or not self.root.winfo_exists()
            or not self.table.winfo_exists()
        ):
            return

        # Set up a flag and timer for skeleton screen
        self._skeleton_timer_id = None
        self._skeleton_shown = False

        def show_skeleton_if_needed():
            if not self.root or not self.root.winfo_exists():
                return
            self._skeleton_shown = True
            self.show_skeleton_screen()

        self._skeleton_timer_id = self.root.after(400, show_skeleton_if_needed)

        # Store currently checked items
        previously_checked = self.get_checked_items()

        def finish_loading():
            if not self.root or not self.root.winfo_exists():
                return
            # Cancel skeleton timer if still pending
            if self._skeleton_timer_id is not None:
                try:
                    self.root.after_cancel(self._skeleton_timer_id)
                except Exception:
                    pass
                self._skeleton_timer_id = None
            # If skeleton was shown, remove it by destroying the table and scrollbar
            if getattr(self, "_skeleton_shown", False):
                if hasattr(self, "table") and self.table:
                    self.table.destroy()
                if hasattr(self, "scroll_y") and self.scroll_y:
                    self.scroll_y.destroy()
                self._skeleton_shown = False
            try:
                from backend.database import get_connector

                db = get_connector()
                db.connect()
                cursor = db.connection.cursor()
                # Only show items that are not out of stock
                query = "SELECT [NAME], [BRAND], [TYPE], [LOCATION], [UNIT OF MEASURE], [STATUS], [BALANCE] FROM [ITEMSDB] WHERE [STATUS] <> 'Out of Stock' OR [STATUS] IS NULL OR [STATUS] = ''"
                cursor.execute(query)
                rows = cursor.fetchall()

                self.table.delete(*self.table.get_children())
                # Clear any stale checkbox references
                self.table.clear_checked_items()

                for row in rows:
                    # Convert None values to empty strings for display
                    display_row = tuple(
                        value if value is not None else "" for value in row
                    )
                    item_id = self.table.insert("", tk.END, values=display_row)

                    # Check if item is out of stock and style it differently
                    status = (
                        display_row[5]
                        if len(display_row) > 5 and display_row[5]
                        else ""
                    )
                    if status.strip().lower() == "out of stock":
                        # Apply styling to indicate out-of-stock status
                        self.table.set(item_id, "STATUS", "🚫 Out of Stock")
                        # Configure tag for out-of-stock items
                        self.table.tag_configure(
                            "outofstock", background="#555555", foreground="#999999"
                        )
                        self.table.item(item_id, tags=("outofstock",))
                # Auto-sort rows A-Z by NAME after inserting
                items = [
                    (self.table.set(row_id, "NAME"), row_id)
                    for row_id in self.table.get_children("")
                ]
                items.sort(key=lambda x: x[0].lower())
                for index, (_, row_id) in enumerate(items):
                    self.table.move(row_id, "", index)

                # Restore checkbox state for previously checked items
                self.restore_checked_items(previously_checked)

                self.status_label.config(
                    text=f"Loaded {len(rows)} item(s)", fg=SUCCESS_COLOR
                )
                # Show success notification for data loading
                if len(rows) > 0:
                    self.notification_manager.show_notification(
                        "Data Loaded",
                        f"Successfully loaded {len(rows)} item(s) from database.",
                        duration=2000,
                        type_="success",
                    )
                # Debug: print the number of rows fetched
                print(
                    f"[DEBUG] load_items: {len(rows)} rows fetched from ITEMSDB table."
                )
            except Exception as e:
                self.status_label.config(text=f"Error: {e}", fg=ERROR_COLOR)
            finally:
                try:
                    cursor.close()
                    db.connection.close()
                except Exception:
                    pass

        # Run finish_loading as soon as possible after DB work
        self.root.after(0, finish_loading)

    def filter_items(self, category):
        util_filter_items(self.db, self.table, category, self.root)

    def search_items(self, event=None):
        """Search items by keyword across multiple fields and update the table."""
        keyword = self.search_entry.get().strip()
        if not keyword:
            self.suggestions_popup.withdraw()  # Hide the popup if the search box is empty
            self.load_items()  # Load all items
            return

        # Store currently checked items
        previously_checked = self.get_checked_items()

        try:
            from backend.database import get_connector

            db = get_connector()
            db.connect()
            cursor = db.connection.cursor()
            # Fetch suggestions from the database - exclude out of stock items
            suggestion_query = "SELECT DISTINCT [NAME] FROM [ITEMSDB] WHERE LCASE([NAME]) LIKE ? AND ([STATUS] <> 'Out of Stock' OR [STATUS] IS NULL OR [STATUS] = '')"
            cursor.execute(suggestion_query, (f"%{keyword.lower()}%",))
            suggestions = cursor.fetchall()
            self.suggestions_listbox.delete(0, tk.END)
            for suggestion in suggestions:
                self.suggestions_listbox.insert(tk.END, suggestion[0])
            if suggestions:
                x = self.search_entry.winfo_rootx()
                y = self.search_entry.winfo_rooty() + self.search_entry.winfo_height()
                self.suggestions_popup.geometry(
                    f"{self.search_entry.winfo_width()}x150+{x}+{y}"
                )
                self.suggestions_popup.deiconify()
            else:
                self.suggestions_popup.withdraw()
            # Fetch filtered items for the table - exclude out of stock items
            filter_query = """SELECT [NAME], [BRAND], [TYPE], [LOCATION], [UNIT OF MEASURE], [STATUS], [BALANCE] 
                             FROM [ITEMSDB] 
                             WHERE (LCASE([NAME]) LIKE ? OR LCASE([BRAND]) LIKE ? OR LCASE([TYPE]) LIKE ? OR LCASE([LOCATION]) LIKE ? OR LCASE([STATUS]) LIKE ?)
                             AND ([STATUS] <> 'Out of Stock' OR [STATUS] IS NULL OR [STATUS] = '')"""
            cursor.execute(
                filter_query,
                (
                    f"%{keyword.lower()}%",
                    f"%{keyword.lower()}%",
                    f"%{keyword.lower()}%",
                    f"%{keyword.lower()}%",
                    f"%{keyword.lower()}%",
                ),
            )
            rows = cursor.fetchall()

            for row in self.table.get_children():
                self.table.delete(row)
            # Clear any stale checkbox references
            self.table.clear_checked_items()

            for row in rows:
                # Convert None values to empty strings for display
                display_row = tuple(value if value is not None else "" for value in row)
                item_id = self.table.insert("", tk.END, values=display_row)

                # Check if item is out of stock and style it differently
                status = (
                    display_row[5] if len(display_row) > 5 and display_row[5] else ""
                )
                if status.strip().lower() == "out of stock":
                    # Apply styling to indicate out-of-stock status
                    self.table.set(item_id, "STATUS", "🚫 Out of Stock")
                    # Configure tag for out-of-stock items
                    self.table.tag_configure(
                        "outofstock", background="#555555", foreground="#999999"
                    )
                    self.table.item(item_id, tags=("outofstock",))

            # Restore checkbox state for previously checked items
            self.restore_checked_items(previously_checked)

            self.status_label.config(
                text=f"Found {len(rows)} item(s) matching '{keyword}'", fg=SUCCESS_COLOR
            )

            # Show search result notification
            if len(rows) > 0:
                self.notification_manager.show_notification(
                    "Search Results",
                    f"Found {len(rows)} item(s) matching '{keyword}'",
                    duration=2000,
                    type_="info",
                )
            else:
                self.notification_manager.show_notification(
                    "No Results",
                    f"No items found matching '{keyword}'",
                    duration=3000,
                    type_="warning",
                )
        except Exception as e:
            self.status_label.config(
                text=f"Error: Failed to search items: {e}", fg=ERROR_COLOR
            )
            self.notification_manager.show_notification(
                "Search Error",
                f"Failed to search items: {str(e)}",
                duration=4000,
                type_="error",
            )
        finally:
            try:
                cursor.close()
                db.connection.close()
            except Exception:
                pass

    def select_suggestion(self, event=None):
        """Handle the selection of a suggestion."""
        try:
            selected = self.suggestions_listbox.get(
                self.suggestions_listbox.curselection()
            )
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, selected)
            self.suggestions_popup.withdraw()  # Hide the popup
            self.search_items()  # Trigger the search with the selected suggestion
        except tk.TclError:
            pass  # Ignore if no selection is made

    def on_table_single_click(self, event):
        # Toggle checkbox when clicking anywhere on the row (not just the checkbox image)
        row_id = self.table.identify_row(event.y)
        if row_id:
            # Check if the item is out of stock before allowing toggle
            values = self.table.item(row_id)["values"]
            if values and len(values) > 5:  # STATUS is at index 5
                status = values[5] if values[5] else ""
                if status.strip().lower() == "out of stock":
                    # Show warning and don't allow toggle
                    self.notification_manager.show_notification(
                        "Item Unavailable",
                        f"'{values[0]}' is out of stock and cannot be added to cart.",
                        duration=3000,
                        type_="warning",
                    )
                    return
            self.table.toggle_checkbox(row_id)

    def go_back_to_welcome(self):
        """Navigate back to the WelcomeWindow."""
        # Sound removed
        self.is_closing = True

        # Clean up notifications
        if hasattr(self, "notification_manager"):
            try:
                if hasattr(self.notification_manager, "active_notifications"):
                    for notification in self.notification_manager.active_notifications[
                        :
                    ]:
                        try:
                            if notification.winfo_exists():
                                notification.destroy()
                        except Exception:
                            pass
                    self.notification_manager.active_notifications.clear()
            except Exception:
                pass

        # Cancel any pending `after` callbacks
        if hasattr(self, "update_clock_id") and self.update_clock_id:
            try:
                self.root.after_cancel(self.update_clock_id)
            except Exception:
                pass
            self.update_clock_id = None
        if hasattr(self, "update_timer_id") and self.update_timer_id:
            try:
                self.root.after_cancel(self.update_timer_id)
            except Exception:
                pass
            self.update_timer_id = None
        if hasattr(self, "update_task") and self.update_task:
            try:
                self.root.after_cancel(self.update_task)
            except Exception:
                pass
            self.update_task = None
        if self.root.winfo_exists():
            self.root.destroy()  # Close the current MainBrowser window
        from gui.employee_login import (
            WelcomeWindow,
        )  # Defer the import to avoid circular dependency

        welcome_window = WelcomeWindow()  # Create a new instance of WelcomeWindow
        welcome_window.run()  # Run the WelcomeWindow

    def go_back(self):
        """Go back to the Employee Login."""
        # Sound removed

        self.is_closing = True

        # Clean up notifications
        if hasattr(self, "notification_manager"):
            try:
                if hasattr(self.notification_manager, "active_notifications"):
                    for notification in self.notification_manager.active_notifications[
                        :
                    ]:
                        try:
                            if notification.winfo_exists():
                                notification.destroy()
                        except Exception:
                            pass
                    self.notification_manager.active_notifications.clear()
            except Exception:
                pass

        # Cancel any pending `after` callbacks
        if hasattr(self, "update_clock_id") and self.update_clock_id:
            try:
                self.root.after_cancel(self.update_clock_id)
            except Exception:
                pass
            self.update_clock_id = None
        if hasattr(self, "update_timer_id") and self.update_timer_id:
            try:
                self.root.after_cancel(self.update_timer_id)
            except Exception:
                pass
            self.update_timer_id = None
        if hasattr(self, "update_task") and self.update_task:
            try:
                self.root.after_cancel(self.update_task)
            except Exception:
                pass
            self.update_task = None
        if self.root.winfo_exists():
            self.root.destroy()  # Destroy the current dashboard window
        from gui.employee_login import WelcomeWindow

        login_window = WelcomeWindow()  # Reinitialize the login window
        login_window.run()  # Run the login window

    def on_close(self):
        """Clean up resources before closing the window."""
        self.is_closing = True

        # Clean up notifications
        if hasattr(self, "notification_manager"):
            try:
                # Clear any active notifications
                if hasattr(self.notification_manager, "active_notifications"):
                    for notification in self.notification_manager.active_notifications[
                        :
                    ]:
                        try:
                            if notification.winfo_exists():
                                notification.destroy()
                        except Exception:
                            pass
                    self.notification_manager.active_notifications.clear()
            except Exception:
                pass

        # Cancel any pending `after` callbacks
        if hasattr(self, "update_clock_id") and self.update_clock_id:
            try:
                self.root.after_cancel(self.update_clock_id)
            except Exception:
                pass
            self.update_clock_id = None
        if hasattr(self, "update_timer_id") and self.update_timer_id:
            try:
                self.root.after_cancel(self.update_timer_id)
            except Exception:
                pass
            self.update_timer_id = None
        if hasattr(self, "update_task") and self.update_task:
            try:
                self.root.after_cancel(self.update_task)
            except Exception:
                pass
            self.update_task = None
        # Destroy the window
        if self.root.winfo_exists():
            self.root.destroy()

    def run(self):
        """Run the main loop."""
        if getattr(self, "is_closing", False) or not self.root.winfo_exists():
            return
        self.update_task = self.root.after(
            1000, self.update_data
        )  # Example of a recurring task
        self.root.mainloop()

    def update_data(self):
        """Example of a recurring task."""
        # Do not run or reschedule if closing or window is gone
        if getattr(self, "is_closing", False):
            return
        try:
            if (
                not self.root.winfo_exists()
                or not hasattr(self, "table")
                or not self.table.winfo_exists()
            ):
                return
        except Exception:
            return
        if not self.updates_paused:
            # Only schedule next callback if not closing and window still exists
            if not getattr(self, "is_closing", False):
                try:
                    if (
                        self.root.winfo_exists()
                        and hasattr(self, "table")
                        and self.table.winfo_exists()
                    ):
                        self.update_task = self.root.after(1000, self.update_data)
                except Exception:
                    return

    # Session timer update logic
    # Replace the inline update_timer function with a method for better control
    def update_session_timer(self):
        if getattr(self, "is_closing", False) or not self.root.winfo_exists():
            return
        try:
            self.time_remaining -= 1
            if self.time_remaining <= 0:
                self.notification_manager.show_notification(
                    "Session Expired",
                    "Your session has expired. Returning to login screen.",
                    duration=3000,
                    type_="warning",
                )
                # Add a small delay before going back to allow notification to show
                self.root.after(3000, self.go_back)
            else:
                mins, secs = divmod(self.time_remaining, 60)
                self.clock_label.config(text=f"Session: {mins:02d}:{secs:02d}")
                if not getattr(self, "is_closing", False) and self.root.winfo_exists():
                    self.update_timer_id = self.root.after(
                        1000, self.update_session_timer
                    )
        except Exception as e:
            print(f"Error in update_session_timer: {e}")

    def pause_updates(self, event=None):
        """Pause periodic UI/data updates when window loses focus."""
        self.updates_paused = True

    def resume_updates(self, event=None):
        """Resume periodic UI/data updates when window regains focus."""
        self.updates_paused = False

    def filter_by_type(self, item_type):
        # Refresh type filter buttons before filtering
        self.refresh_type_buttons()
        """Filter the Items by type."""

        # Store currently checked items (but only for non-"Out of Stock" filters)
        previously_checked = set()
        if item_type != "Out of Stock":
            previously_checked = self.get_checked_items()

        try:
            from backend.database import get_connector

            db = get_connector()
            db.connect()
            cursor = db.connection.cursor()
            # Filter based on the type selection (case-insensitive)
            if item_type == "All":
                query = "SELECT [NAME], [BRAND], [TYPE], [LOCATION], [UNIT OF MEASURE], [STATUS], [BALANCE] FROM [ITEMSDB] WHERE [STATUS] <> 'Out of Stock' OR [STATUS] IS NULL OR [STATUS] = ''"
                cursor.execute(query)
            elif item_type == "Out of Stock":
                query = "SELECT [NAME], [BRAND], [TYPE], [LOCATION], [UNIT OF MEASURE], [STATUS], [BALANCE] FROM [ITEMSDB] WHERE [STATUS] = 'Out of Stock'"
                cursor.execute(query)
            else:
                # Case-insensitive filter for type
                query = (
                    "SELECT [NAME], [BRAND], [TYPE], [LOCATION], [UNIT OF MEASURE], [STATUS], [BALANCE] FROM [ITEMSDB] "
                    "WHERE LCASE([TYPE]) = ? AND ([STATUS] <> 'Out of Stock' OR [STATUS] IS NULL OR [STATUS] = '')"
                )
                cursor.execute(query, (item_type.lower(),))
            rows = cursor.fetchall()

            for row in self.table.get_children():
                self.table.delete(row)
            # Clear any stale checkbox references
            self.table.clear_checked_items()

            # Remove checkbox column for Out of Stock
            if item_type == "Out of Stock":
                self.table.configure(show="headings")  # Hide the #0 column (checkbox)
                for row in rows:
                    display_row = tuple(
                        value if value is not None else "" for value in row
                    )
                    self.table.insert("", tk.END, values=display_row)
                self.table.tag_configure(
                    "outofstock", background="#A9A9A9", foreground="#666666"
                )
                self.status_label.config(
                    text="Out of Stock Items cannot be selected.", fg=TEXT_SECONDARY
                )
                self.cart_button.config(state=tk.DISABLED)
            else:
                self.table.configure(
                    show="tree headings"
                )  # Restore the checkbox column
                for row in rows:
                    display_row = tuple(
                        value if value is not None else "" for value in row
                    )
                    item_id = self.table.insert("", tk.END, values=display_row)

                    # Check if item is out of stock and style it differently
                    status = (
                        display_row[5]
                        if len(display_row) > 5 and display_row[5]
                        else ""
                    )
                    if status.strip().lower() == "out of stock":
                        # Apply styling to indicate out-of-stock status
                        self.table.set(item_id, "STATUS", "🚫 Out of Stock")
                        # Configure tag for out-of-stock items
                        self.table.tag_configure(
                            "outofstock", background="#555555", foreground="#999999"
                        )
                        self.table.item(item_id, tags=("outofstock",))

                # Restore checkbox state for previously checked items
                self.restore_checked_items(previously_checked)

                self.status_label.config(
                    text=f"Showing {len(rows)} item(s) for {item_type}",
                    fg=SUCCESS_COLOR,
                )
                self.update_cart_button_state()
            cursor.close()
            db.connection.close()
        except Exception as e:
            self.status_label.config(text=f"Error: {e}", fg=ERROR_COLOR)
            self.notification_manager.show_notification(
                "Filter Error",
                f"Failed to filter items: {str(e)}",
                duration=4000,
                type_="error",
            )
        finally:
            try:
                cursor.close()
                db.connection.close()
            except Exception:
                pass

    def go_to_checkout(self):
        # Get all checked items
        checked = self.table.get_checked()
        # Only keep checked items that still exist in the Treeview
        valid_items = set(self.table.get_children())
        checked = [item for item in checked if item in valid_items]

        if not checked:
            self.notification_manager.show_notification(
                "No Selection",
                "Please check at least one item to proceed.",
                duration=3000,
                type_="warning",
            )
            return

        # Filter out out-of-stock items and collect them for notification
        selected_items = []
        removed_items = []

        for item in checked:
            values = self.table.item(item)["values"]
            # Check if item is out of stock
            status = values[5] if len(values) > 5 and values[5] else ""

            if status.strip().lower() == "out of stock":
                # Add to removed items list for notification
                removed_items.append(values[0])  # Item name
                # Uncheck the out-of-stock item
                self.table.set_checked(item, False)
            else:
                # CheckoutWindow expects: (name, brand, type, location, balance, quantity)
                # Table columns: ("NAME", "BRAND", "TYPE", "LOCATION", "UNIT OF MEASURE", "STATUS", "BALANCE")
                # Indices:       (   0,      1,      2,        3,               4,          5,        6)
                item_data = (
                    values[0],
                    values[1],
                    values[2],
                    values[3],
                    values[6],
                    1,
                )  # (NAME, BRAND, TYPE, LOCATION, BALANCE, default quantity=1)
                selected_items.append(item_data)

        # Notify user if any out-of-stock items were removed
        if removed_items:
            # removed_names variable was unused; removed to satisfy lint
            if selected_items:
                # Some valid items remain - show notification and proceed
                self.notification_manager.show_notification(
                    "Items Removed",
                    f"Removed {len(removed_items)} out-of-stock item(s). Proceeding with {len(selected_items)} valid item(s).",
                    duration=4000,
                    type_="warning",
                )
            else:
                # All items were out of stock
                self.notification_manager.show_notification(
                    "All Items Out of Stock",
                    f"All {len(removed_items)} selected item(s) are out of stock. Please select different items.",
                    duration=5000,
                    type_="error",
                )
                # Update cart button state to reflect changes
                self.update_cart_button_state()
                return

        # Check if any valid items remain after filtering
        if not selected_items:
            self.notification_manager.show_notification(
                "No Valid Items",
                "No valid items selected for checkout.",
                duration=3000,
                type_="warning",
            )
            return

        # Proceed to checkout with valid items
        self.notification_manager.show_notification(
            "Proceeding to Checkout",
            f"Moving to checkout with {len(selected_items)} item(s).",
            duration=2000,
            type_="success",
        )

        self.is_closing = True
        if hasattr(self, "update_clock_id") and self.update_clock_id:
            try:
                self.root.after_cancel(self.update_clock_id)
            except Exception:
                pass
            self.update_clock_id = None
        if hasattr(self, "update_timer_id") and self.update_timer_id:
            try:
                self.root.after_cancel(self.update_timer_id)
            except Exception:
                pass
            self.update_timer_id = None
        if hasattr(self, "update_task") and self.update_task:
            try:
                self.root.after_cancel(self.update_task)
            except Exception:
                pass
            self.update_task = None
        if self.root.winfo_exists():
            self.root.destroy()
        from gui.functions.emplydash_f.checkout_win import CheckoutWindow

        checkout_window = CheckoutWindow(selected_items)
        checkout_window.run()

    def sort_by_column(self, col, reverse):
        # Get all items and their values for the given column
        items = [(self.table.set(k, col), k) for k in self.table.get_children("")]
        # Sort items (A-Z or Z-A)
        items.sort(reverse=reverse)
        # Rearrange items in sorted order
        for index, (val, k) in enumerate(items):
            self.table.move(k, "", index)
        # Reverse sort next time
        self.table.heading(col, command=lambda: self.sort_by_column(col, not reverse))

    def update_cart_button_state(self, event=None):
        # Update cart button state and counter
        if hasattr(self, "status_label") and "Out of Stock" in self.status_label.cget(
            "text"
        ):
            self.cart_button.config(state=tk.DISABLED)
            self.cart_counter.configure(text="0")
            self.cart_counter.place_forget()  # Hide counter
            return

        checked = self.table.get_checked() if hasattr(self, "table") else []

        # Filter out any out-of-stock items from checked items
        valid_checked = []
        for item in checked:
            try:
                values = self.table.item(item)["values"]
                if values and len(values) > 5:  # STATUS is at index 5
                    status = values[5] if values[5] else ""
                    if status.strip().lower() != "out of stock":
                        valid_checked.append(item)
                    else:
                        # Uncheck out-of-stock items automatically
                        self.table.set_checked(item, False)
                else:
                    valid_checked.append(item)  # Include items without status info
            except (IndexError, KeyError, tk.TclError):
                continue

        item_count = len(valid_checked)

        if item_count > 0:
            self.cart_button.config(state=tk.NORMAL)
            self.cart_counter.configure(text=str(item_count))
            self.cart_counter.place(x=25, y=-5)  # Show counter
        else:
            self.cart_button.config(state=tk.DISABLED)
            self.cart_counter.configure(text="0")
            self.cart_counter.place_forget()  # Hide counter

    def safe_focus_search_entry(self):
        try:
            if self.root.winfo_exists() and self.search_entry.winfo_exists():
                self.search_entry.focus()
        except Exception:
            pass
