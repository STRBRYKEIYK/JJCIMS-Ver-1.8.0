import os
import sys
import time
from PIL import Image, ImageTk

# Explicit imports instead of star to satisfy linters; trimmed unused symbols
from gui.functions.admdash_f.admdash_imp import (
    tk, ttk, messagebox, Path,
    configure_window, center_window,
    add_item, delete_item,
    search_items, select_suggestion,
    add_stats_panel, update_stats,
    view_items_treeview, DEFAULT_COLUMNS, DEFAULT_COLUMN_WIDTHS, NUMERIC_COLUMNS, CENTERED_COLUMNS,
    clear_admin_logs, clear_employee_logs,
    IntegratedAdminSettings, hide_main_buttons, show_main_buttons, show_export_buttons,
    show_error, export_to_xlsx, export_to_csv,
    create_tab_buttons, reset_table_columns, clear_table, load_data,
    add_tooltips, load_restock_list, configure_custom_scrollbar, set_window_icon, Admin2FA, UpdateItemsWindow
)
from database import get_connector, get_db_path

# Central resolved DB path (ensures import side-effect uses get_db_path)
DB_PATH = get_db_path()

class ToastNotification:
    def __init__(self, parent, message, type="info", duration=3000):
        self.parent = parent
        self.message = message
        self.type = type
        self.duration = duration
        
        # Create toast window
        self.toast = tk.Toplevel(parent)
        self.toast.withdraw()  # Hide initially
        self.toast.overrideredirect(True)  # Remove window decorations
        self.toast.attributes('-topmost', True)  # Keep on top
        self.toast.attributes('-alpha', 0.9)  # Slight transparency
        
        # Configure colors based on type
        colors = {
            "info": {"bg": "#2196F3", "fg": "#FFFFFF"},
            "success": {"bg": "#4CAF50", "fg": "#FFFFFF"},
            "warning": {"bg": "#FF9800", "fg": "#FFFFFF"},
            "error": {"bg": "#F44336", "fg": "#FFFFFF"}
        }
        
        color_scheme = colors.get(type, colors["info"])
        
        # Create main frame
        main_frame = tk.Frame(
            self.toast,
            bg=color_scheme["bg"],
            relief="solid",
            bd=1
        )
        main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Add icon based on type
        icons = {
            "info": "ℹ",
            "success": "✓",
            "warning": "⚠",
            "error": "✗"
        }
        
        icon = icons.get(type, "ℹ")
        
        # Create content frame
        content_frame = tk.Frame(main_frame, bg=color_scheme["bg"])
        content_frame.pack(fill="both", expand=True, padx=10, pady=8)
        
        # Add icon and message
        tk.Label(
            content_frame,
            text=f"{icon} {message}",
            bg=color_scheme["bg"],
            fg=color_scheme["fg"],
            font=("Inter", 10),
            wraplength=300
        ).pack()
        
        # Position toast at top-right of parent window
        self.position_toast()
        
        # Show toast with animation
        self.show_toast()
        
        # Auto-hide after duration
        self.toast.after(duration, self.hide_toast)
        
        # Click to dismiss
        main_frame.bind("<Button-1>", lambda e: self.hide_toast())
        
    def position_toast(self):
        # Update to get actual size
        self.toast.update_idletasks()
        
        # Get parent window position and size
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        
        # Get toast size
        toast_width = self.toast.winfo_reqwidth()
        toast_height = self.toast.winfo_reqheight()
        
        # Position at top-right of parent
        x = parent_x + parent_width - toast_width - 20
        y = parent_y + 80  # Below header
        
        self.toast.geometry(f"{toast_width}x{toast_height}+{x}+{y}")
        
    def show_toast(self):
        self.toast.deiconify()  # Show window
        # Animate opacity from 0 to 0.9
        self.animate_in(0.0)
        
    def animate_in(self, alpha):
        if alpha < 0.9:
            self.toast.attributes('-alpha', alpha)
            self.toast.after(20, lambda: self.animate_in(alpha + 0.1))
        else:
            self.toast.attributes('-alpha', 0.9)
            
    def hide_toast(self):
        # Animate opacity from 0.9 to 0
        self.animate_out(0.9)
        
    def animate_out(self, alpha):
        if alpha > 0:
            self.toast.attributes('-alpha', alpha)
            self.toast.after(20, lambda: self.animate_out(alpha - 0.1))
        else:
            self.toast.destroy()

def show_toast(parent, message, type="info", duration=3000):
    """Show a toast notification"""
    return ToastNotification(parent, message, type, duration)


# Add the `src` directory to the Python module search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),  '..')))

# DB and Fernet key paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Updated to use main JJCIMS database for employee list
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, 'database', 'JJCIMS.accdb'))
FERNET_KEY_PATH = os.path.abspath(os.path.join(BASE_DIR, 'config', 'fernet_key.py'))

def create_rounded_search_bar(parent, search_callback, width=300, height=35):
    """Create a rounded search bar with search icon"""
    from PIL import Image, ImageDraw, ImageTk
    
    # Create search container frame
    search_container = tk.Frame(parent, bg="#000000")
    search_container.pack(side=tk.LEFT, padx=10, pady=10)
    
    # Create rounded entry background
    def create_rounded_entry_bg(width, height, radius=15):
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw rounded rectangle background (dark grey)
        draw.rounded_rectangle(
            [(0, 0), (width-1, height-1)],
            radius=radius,
            fill=(48, 48, 48, 255),  # Dark grey background
            outline=(255, 255, 255, 255),  # White outline
            width=2
        )
        return ImageTk.PhotoImage(img)
    
    # Create search icon
    def create_search_icon(size=24):
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw search icon (magnifying glass)
        # Circle
        circle_center = (size//2 - 2, size//2 - 2)
        circle_radius = size//3
        draw.ellipse(
            [circle_center[0] - circle_radius, circle_center[1] - circle_radius,
             circle_center[0] + circle_radius, circle_center[1] + circle_radius],
            outline=(255, 111, 0, 255),
            width=2
        )
        
        # Handle
        handle_start = (circle_center[0] + circle_radius - 2, circle_center[1] + circle_radius - 2)
        handle_end = (size - 3, size - 3)
        draw.line([handle_start, handle_end], fill=(255, 111, 0, 255), width=2)
        
        return ImageTk.PhotoImage(img)
    
    # Create background label
    bg_img = create_rounded_entry_bg(width, height)
    bg_label = tk.Label(search_container, image=bg_img, bg="#000000")
    bg_label.image = bg_img  # Keep reference
    bg_label.pack()
    
    # Create entry widget positioned over the background
    entry = tk.Entry(
        bg_label,
        font=("Segoe UI", 12),
        bg="#303030",  # Match the rounded background
        fg="#ffffff",
        insertbackground="#ff6f00",  # Orange cursor
        border=0,
        relief=tk.FLAT,
        width=int(width/10)  # Approximate character width
    )
    entry.place(x=10, y=(height-20)//2, width=width-50, height=20)
    
    # Create search button with icon
    search_icon = create_search_icon(height-10)
    search_btn = tk.Button(
        bg_label,
        image=search_icon,
        bg="#303030",
        activebackground="#404040",
        border=0,
        relief=tk.FLAT,
        command=search_callback,
        cursor="hand2"
    )
    search_btn.image = search_icon  # Keep reference
    search_btn.place(x=width-35, y=5, width=25, height=25)
    
    return search_container, entry, search_btn

class AdminDashboard:
    def refresh_items_view(self):
        """Rebuild the styled ITEMS_LIST Treeview and reload data (used after add/update)."""
        try:
            if not hasattr(self, 'table_frame') or not self.table_frame.winfo_exists():
                return
            # Always recreate full styled tree
            self.create_items_table()
            self.load_data()
        except Exception as e:
            print(f"[DEBUG] refresh_items_view error: {e}")
    def show_skeleton_screen(self, rows=8, cols=None):
        """Display a skeleton screen in the table area while loading data."""
        import tkinter as tk
        from tkinter import ttk
        # Remove any existing table and scrollbar
        if hasattr(self, 'table') and self.table:
            self.table.destroy()
        if hasattr(self, 'scroll_y') and self.scroll_y:
            self.scroll_y.destroy()
        self.scroll_y = ttk.Scrollbar(self.table_frame, orient=tk.VERTICAL, style="Custom.Vertical.TScrollbar")
        self.table = ttk.Treeview(
            self.table_frame,
            columns=self.default_columns if cols is None else cols,
            show="headings",
            yscrollcommand=self.scroll_y.set
        )
        self.scroll_y.config(command=self.table.yview)
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.table.pack(fill=tk.BOTH, expand=True)
        # Set up columns
        columns = self.default_columns if cols is None else cols
        for col in columns:
            self.table.heading(col, text=col)
            self.table.column(col, anchor="center")
        # Insert skeleton rows (gray rectangles)
        for _ in range(rows):
            self.table.insert("", "end", values=["" for _ in columns])
        # Overlay rectangles using tags and style
        style = ttk.Style()
        style.configure("Skeleton.Treeview", background="#e0e0e0", foreground="#e0e0e0")
        self.table.tag_configure("skeleton", background="#e0e0e0", foreground="#e0e0e0")
        for item in self.table.get_children():
            self.table.item(item, tags=("skeleton",))
    def __init__(self, username=None):
        # Track all after callback IDs for robust cancellation
        self._after_ids = set()
        self.username = username
        self.update_datetime_id = None
        self.logs_path = Path(__file__).resolve().parent.parent / "database" / "logs.xlsx"
        # Prefer TkinterDnD root when available to enable native drag-and-drop
        try:
            from tkinterdnd2 import TkinterDnD  # type: ignore
            self.root = TkinterDnD.Tk()
            self._dnd_enabled = True
        except Exception:
            self.root = tk.Tk()
            self._dnd_enabled = False
        self.root.attributes("-fullscreen", True)
        
        # Add sort state tracking
        self.sort_states = {}  # Track sort states for columns
        self.numeric_columns = {"IN", "OUT", "BALANCE", "MIN STOCK", "DEFICIT", "PRICE PER UNIT", "COST"}
        
        # Set window icon
        set_window_icon(self.root)
        
        # Set up window close protocol
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Track the current view (default to ITEMS_LIST)
        self.current_view = "ITEMS_LIST"  # Default to ITEMS_LIST for initial view

        # Store default ITEMS_LIST columns and their widths (removed 'NO')
        self.default_columns = DEFAULT_COLUMNS
        self.default_column_widths = DEFAULT_COLUMN_WIDTHS
        self.numeric_columns = NUMERIC_COLUMNS
        self.centered_columns = CENTERED_COLUMNS
      

        # Use the global configuration for the main window
        configure_window(self.root, title="JJCIMS - Admin Dashboard", width=1024, height=768, resizable=True)
        center_window(self.root)

        self.root.configure(bg="#000000")  # Pure black background

        # Header
        self.header = tk.Frame(self.root, bg="#000000", height=100)  # Pure black background
        self.header.pack(side=tk.TOP, fill=tk.X)
        
        # Left section with logo
        header_left = tk.Frame(self.header, bg="#000000")
        header_left.pack(side=tk.LEFT, fill=tk.Y)

        # Try to load and display the logo
        try:
            logo_path = Path(__file__).resolve().parent.parent / "assets" / "adm_dash.png"
            original_img = Image.open(str(logo_path))
            
            # Resize to a smaller size (e.g., 300px width while maintaining aspect ratio)
            aspect_ratio = original_img.height / original_img.width
            new_width = 300
            new_height = int(new_width * aspect_ratio)
            resized_img = original_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Use image without scanline effects
            self.logo_image = ImageTk.PhotoImage(resized_img)
            
            self.logo_label = tk.Label(
                header_left,
                image=self.logo_image,
                bg="#000000", 
                cursor="hand2"
            )
            self.logo_label.pack(side=tk.LEFT, padx=10, pady=5)
            self.logo_label.bind("<Button-1>", lambda event: self.go_back_to_admin_login())
        except Exception as e:
            print(f"Error loading logo image: {e}")

        # Database connection for main inventory
        # Use centralized path resolution (supports relocation & PyInstaller)
        try:
            self.db = get_connector()  # auto-resolves JJCIMS.accdb
        except Exception:
            # Fallback still uses get_connector with explicit path
            fallback_path = Path(__file__).resolve().parent.parent / "database" / "JJCIMS.accdb"
            self.db = get_connector(str(fallback_path))
        try:
            self.db.connect()
        except Exception as e:
            print(f"Error connecting to database: {e}")
            self.show_toast("error", "Database Error", "Failed to connect to the database. Please check the configuration.")

        # Note: Employee list is now using the main JJCIMS.accdb database with emp_list table

        # Sidebar
        self.sidebar = tk.Frame(self.root, bg="#000000", width=400)  # Pure black background
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        # Place stats panel at the top of the sidebar, above the sidebar buttons
        # Correctly assign stats labels to self for later use
        stats = add_stats_panel(self.sidebar, self.table if hasattr(self, 'table') else None, username=self.username)
        if stats is not None:
            self.total_items_label, self.out_of_stock_label, self.low_stock_label, self.total_cost_label = stats

        # --- macOS Button Style ---
        style = ttk.Style()
        macos_button_bg = '#F5F5F7'
        macos_button_fg = '#1C1C1E'
        macos_button_border = '#D1D1D6'
        macos_button_active_bg = '#E5E5EA'
        macos_button_font = ("Segoe UI", 12, "bold")
        style.configure(
            "MacOS.TButton",
            font=macos_button_font,
            background=macos_button_bg,
            foreground=macos_button_fg,
            borderwidth=1,
            focusthickness=2,
            focuscolor=macos_button_border,
            relief="flat",
            padding=(16, 8),
        )
        style.map(
            "MacOS.TButton",
            background=[('active', macos_button_active_bg), ('pressed', macos_button_active_bg)],
            foreground=[('active', macos_button_fg), ('pressed', macos_button_fg)],
            bordercolor=[('focus', macos_button_border), ('!focus', macos_button_border)]
        )
        # Build sidebar buttons and settings
        self.build_sidebar_buttons()

        # Configure the custom scrollbar style
        configure_custom_scrollbar()        

        # Table Frame
        self.table_frame = tk.Frame(self.root, bg="#000000")
        self.table_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        create_tab_buttons(self, parent=self.table_frame)
        self.table = None
        self.scroll_y = None
        from gui.functions.admdash_f.ML.view_items_treeview import view_items_treeview
        view_items_treeview(self)

        # --- Restore A-Z sorting by binding Treeview column headers to sort_by_column ---
        if self.table:
            for col in self.default_columns:
                self.table.heading(col, text=col, command=lambda c=col: self.sort_by_column(c, False))

        # Load initial data
        self.load_data()
        
        # Set initial view and button visibility (hide export buttons by default)
        self.set_current_view("ITEMS_LIST")

        # Ensure the default view is consistent
        self.current_view = "ITEMS_LIST"

        # --- SEARCH BAR (rounded with search icon) positioned beside tabs ---
        # Wait for tabs_and_search_frame to be created, then add search bar
        if self.root and self.root.winfo_exists():
            self.root.after(100, self._delayed_search_bar_creation)

    def build_sidebar_buttons(self):
        """Create sidebar buttons, export buttons, log controls, and settings button with 2FA guard."""
        # Basic button group (macOS style already configured in __init__)
        self.add_button = tk.Button(
            self.sidebar,
            text="Add New Item",
            command=lambda: self.open_add_item(),
            bg="#ff6f00", fg="#fffde7",
            activebackground="#0d1331", activeforeground="#ffd600",
            font=("Segoe UI", 12, "bold"),
            width=18, anchor="w", padx=10, pady=5
        )
        self.add_button.pack(pady=3)

        self.update_item_button = tk.Button(
            self.sidebar,
            text="Update Item",
            command=self.open_update_window,
            bg="#283593", fg="#fffde7",
            activebackground="#0d1331", activeforeground="#ffd600",
            font=("Segoe UI", 12, "bold"),
            width=18, anchor="w", padx=10, pady=5
        )
        self.update_item_button.pack(pady=3)

        self.delete_button = tk.Button(
            self.sidebar,
            text="Delete Item",
            command=lambda: delete_item(self.table, self.db, self.update_stats, self.username),
            bg="#b71c1c", fg="#fffde7",
            activebackground="#0d1331", activeforeground="#ffd600",
            font=("Segoe UI", 12, "bold"),
            width=18, anchor="w", padx=10, pady=5
        )
        self.delete_button.pack(pady=3)

        # Export buttons (not packed until needed by view)
        self.export_button = tk.Button(
            self.sidebar,
            text="Export (Excel)",
            command=self.export_excel,
            bg="#cfd8dc", fg="#000000",
            activebackground="#0d1331", activeforeground="#ff6f00",
            font=("Segoe UI", 12, "bold"),
            width=18, anchor="w", padx=10, pady=5
        )
        self.export_csv_button = tk.Button(
            self.sidebar,
            text="Export (CSV)",
            command=self.export_csv,
            bg="#cfd8dc", fg="#000000",
            activebackground="#0d1331", activeforeground="#ff6f00",
            font=("Segoe UI", 12, "bold"),
            width=18, anchor="w", padx=10, pady=5
        )

        self.clear_admin_logs_button = tk.Button(
            self.sidebar,
            text="Clear Admin Logs",
            command=lambda: clear_admin_logs(
                self.logs_path, self, self.reset_table_columns, self.clear_table, self.set_current_view
            ),
            bg="#b71c1c", fg="#fffde7",
            font=("Segoe UI", 12, "bold"),
            width=18, anchor="w", padx=10, pady=5
        )

        self.delete_log_button = tk.Button(
            self.sidebar,
            text="Delete Log Entry",
            command=self.delete_log_entry,
            bg="#b71c1c", fg="#fffde7",
            font=("Segoe UI", 12, "bold"),
            width=18, anchor="w", padx=10, pady=5
        )

        self.clear_employee_logs_button = tk.Button(
            self.sidebar,
            text="Clear Employee Logs",
            command=lambda: clear_employee_logs(
                self.logs_path, self, self.reset_table_columns, self.clear_table, self.set_current_view
            ),
            bg="#b71c1c", fg="#fffde7",
            font=("Segoe UI", 12, "bold"),
            width=18, anchor="w", padx=10, pady=5
        )

        # Settings button with 2FA
        settings_img_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'settings.png'))
        self.settings_2fa_verified = False
        self.admin_settings = IntegratedAdminSettings(self)

        def settings_with_2fa():
            if not self.root or not self.root.winfo_exists():
                return
            if hasattr(self, 'username') and self.username and self.username.lower() == 'bypass':
                self.admin_settings.show_settings()
                return
            if self.settings_2fa_verified:
                self.admin_settings.show_settings()
                return
            def on_2fa_success():
                self.settings_2fa_verified = True
                if self.root and self.root.winfo_exists():
                    self.admin_settings.show_settings()
            try:
                secret_enc = self.db.get_2fa_secret(self.username)
                if not secret_enc:
                    if hasattr(self, 'username') and self.username and self.username.lower() == 'bypass':
                        self.admin_settings.show_settings()
                        return
                    self.show_toast("error", "2FA Error", "2FA secret not found for this user.")
                    return
                from cryptography.fernet import Fernet
                from gui.config.fernet_key import FERNET_KEY
                fernet = Fernet(FERNET_KEY)
                secret = fernet.decrypt(secret_enc.encode()).decode()
                if self.root and self.root.winfo_exists():
                    Admin2FA(self.root, secret=secret, on_success=on_2fa_success)
            except Exception as e:
                if hasattr(self, 'username') and self.username and self.username.lower() == 'bypass':
                    self.admin_settings.show_settings()
                    return
                self.show_toast("error", "2FA Error", f"Failed to decrypt 2FA secret: {e}")
                return

        try:
            settings_img = Image.open(settings_img_path)
            settings_img = settings_img.resize((36, 36), Image.LANCZOS)
            self.settings_icon = ImageTk.PhotoImage(settings_img)
            self.settings_btn = tk.Button(
                self.sidebar,
                image=self.settings_icon,
                bg="#000000",
                relief="flat",
                bd=0,
                activebackground="#000000",
                command=settings_with_2fa,
                cursor="hand2"
            )
            self.settings_btn.pack(side=tk.BOTTOM, pady=24, padx=10, anchor="s")
        except Exception as e:
            print(f"Failed to load settings icon, using text button: {e}")
            self.settings_btn = tk.Button(
                self.sidebar,
                text="⚙️ Settings",
                bg="#ff6f00",
                fg="#fffde7",
                activebackground="#c65000",
                activeforeground="#fffde7",
                font=("Segoe UI", 12, "bold"),
                relief="flat",
                command=settings_with_2fa,
                cursor="hand2",
                width=18,
                anchor="w",
                padx=10,
                pady=5
            )
            self.settings_btn.pack(side=tk.BOTTOM, pady=24, padx=10, anchor="s")

        add_tooltips({
            self.add_button: "Add a new item to the inventory",
            self.update_item_button: "Update selected item(s)",
            self.delete_button: "Delete selected item(s)",
            self.export_button: "Export data to an Excel file",
            self.export_csv_button: "Export data to a CSV file",
            self.clear_admin_logs_button: "Clear all admin logs",
            self.clear_employee_logs_button: "Clear all employee logs",
            getattr(self, 'delete_log_button', None): "Delete the selected log entry" if hasattr(self, 'delete_log_button') else None,
            getattr(self, 'settings_btn', None): "Open settings (2FA required)" if hasattr(self, 'settings_btn') else None
        })

    def show_toast(self, type, title, message, duration=3000):
        """Show a toast notification using the module-level show_toast function."""
        if self.root and self.root.winfo_exists():
            return show_toast(self.root, f"{title}: {message}", type, duration)

    def safe_create_search_bar_beside_tabs(self):
        if not self.root or not self.root.winfo_exists():
            return
        self.create_search_bar_beside_tabs()

    def _delayed_search_bar_creation(self):
        """Wrapper method to safely schedule search bar creation"""
        if self.root and self.root.winfo_exists():
            self.safe_create_search_bar_beside_tabs()

    def _delayed_update_datetime(self):
        """Wrapper method to safely schedule datetime updates"""
        if self.root and self.root.winfo_exists():
            self.update_datetime()

    def create_search_bar_beside_tabs(self):
        """Create the search bar positioned beside the tab buttons"""
        try:
            if not (self.root and self.root.winfo_exists()):
                return
            if hasattr(self, 'tabs_and_search_frame'):
                self.search_container, self.search_entry, self.search_button = create_rounded_search_bar(
                    self.tabs_and_search_frame, 
                    lambda: search_items(self) if self.root and self.root.winfo_exists() else None, 
                    width=500,  # Increased width for longer search bar
                    height=35
                )
                self.search_entry.bind("<KeyRelease>", lambda event: search_items(self, event) if self.root and self.root.winfo_exists() else None)
                # Position search bar on the right side with some spacing
                self.search_container.pack(side=tk.RIGHT, padx=(30, 10), pady=5)  # Increased left padding for longer search bar
                # Initialize suggestions popup after search entry is created
                self.init_suggestions_popup()
            else:
                # Retry after a short delay if tabs_and_search_frame isn't ready yet
                if self.root and self.root.winfo_exists():
                    self.root.after(50, self._delayed_search_bar_creation)
        except Exception as e:
            print(f"Error creating search bar: {e}")

    def init_suggestions_popup(self):
        """Initialize the suggestions popup after search entry is created"""
        try:
            # Suggestions popup (autocomplete)
            self.suggestions_popup = tk.Toplevel(self.root)
            self.suggestions_popup.withdraw()
            self.suggestions_popup.overrideredirect(True)
            self.suggestions_popup.configure(bg="#C0C0C0")
            self.suggestions_listbox = tk.Listbox(
                self.suggestions_popup,
                font=("Arial", 12),
                bg="#C0C0C0",
                fg="#000000",
                selectbackground="#ff6f00",
                selectforeground="#000000",
                activestyle="none"
            )
            self.suggestions_listbox.pack(fill=tk.BOTH, expand=True)
            self.suggestions_listbox.bind("<<ListboxSelect>>", lambda event: select_suggestion(self, event))
            self.suggestions_listbox.bind("<Return>", lambda event: select_suggestion(self, event))
            self.suggestions_listbox.bind("<Escape>", lambda e: self.suggestions_popup.withdraw())
            self.search_entry.bind("<FocusOut>", lambda e: self.suggestions_popup.withdraw())
        except Exception as e:
            print(f"Error initializing suggestions popup: {e}")

    def update_datetime(self):
        """Update the date/time display in the header, robustly handling after callbacks."""
        try:
            if not hasattr(self, 'datetime_label') or not self.root or not self.root.winfo_exists():
                return
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            self.datetime_label.config(text=current_time)
            # Cancel previous after if exists
            if self.update_datetime_id:
                try:
                    if self.root and self.root.winfo_exists():
                        self.root.after_cancel(self.update_datetime_id)
                        self._after_ids.discard(self.update_datetime_id)
                except Exception:
                    pass
            # Only schedule next after if window still exists
            if self.root and self.root.winfo_exists():
                self.update_datetime_id = self.root.after(1000, self._delayed_update_datetime)
                self._after_ids.add(self.update_datetime_id)
        except Exception as e:
            print(f"Error updating datetime: {e}")
        else:
            self.update_datetime_id = None

    def on_close(self):
        """Properly cleanup and close the admin dashboard, robustly cancelling all after callbacks."""
        try:
            # Cancel all scheduled after callbacks
            if hasattr(self, '_after_ids'):
                for after_id in list(self._after_ids):
                    try:
                        if self.root and self.root.winfo_exists():
                            self.root.after_cancel(after_id)
                    except Exception:
                        pass
                self._after_ids.clear()
            # Cancel the scheduled update_datetime callback if it exists
            if self.update_datetime_id:
                try:
                    if self.root and self.root.winfo_exists():
                        self.root.after_cancel(self.update_datetime_id)
                    self.update_datetime_id = None
                except Exception:
                    pass
            # Cancel skeleton timer if pending
            if hasattr(self, '_skeleton_timer_id') and self._skeleton_timer_id:
                try:
                    if self.root and self.root.winfo_exists():
                        self.root.after_cancel(self._skeleton_timer_id)
                except Exception:
                    pass
                self._skeleton_timer_id = None
            # Close any open dialogs or popups
            if hasattr(self, 'suggestions_popup'):
                try:
                    if self.suggestions_popup and self.suggestions_popup.winfo_exists():
                        self.suggestions_popup.destroy()
                except Exception:
                    pass
            # Close database connections
            if hasattr(self, 'db') and self.db:
                try:
                    self.db.close()
                except Exception:
                    pass
            # Employee list now uses main database, no separate connection to close
            # Finally destroy the main window
            try:
                if self.root and self.root.winfo_exists():
                    self.root.destroy()
            except Exception:
                pass
            # Extra safety: set self.root to None after destroying
            self.root = None
        except Exception as e:
            print(f"Error during cleanup: {e}")
            # Force destroy if cleanup fails
            try:
                if self.root and self.root.winfo_exists():
                    self.root.destroy()
            except Exception:
                pass
            self.root = None


    def create_items_table(self):
        """Create items table with sorting functionality."""
        view_items_treeview(self)
        
        # Reset sort states for new table
        self.sort_states = {col: False for col in self.default_columns}
        
        # Bind sorting to all column headers
        for col in self.table["columns"]:
            self.table.heading(col, 
                             text=col,
                             command=lambda c=col: self.sort_by_column(c, False))

    def create_logs_table(self):
        """Create logs table with sorting functionality."""
    # Placeholder: implement logs table creation if required
    pass

    def show_error(self, error_message, retry_callback=None):
        show_error(self, error_message, retry_callback)

    def sort_by_column(self, col, reverse=None):
        """Enhanced column sorting with indicators and proper numeric handling."""
        # Initialize sort state for column if not exists
        if col not in self.sort_states:
            self.sort_states[col] = False

        # Toggle sort state if reverse not specified
        if reverse is None:
            self.sort_states[col] = not self.sort_states[col]
            reverse = self.sort_states[col]
        else:
            self.sort_states[col] = reverse

        # Get all items
        items = [(self.table.set(k, col), k) for k in self.table.get_children("")]
        
        # Convert values for sorting
        def convert_value(value):
            if not value:
                return 0 if col in self.numeric_columns else ""
                
            if col in self.numeric_columns:
                # Remove currency symbols and commas for numeric columns
                cleaned = value.replace('₱', '').replace(',', '').strip()
                try:
                    return float(cleaned)
                except ValueError:
                    return 0
            return value.lower()  # Case-insensitive string sorting
            
        # Sort items
        items.sort(key=lambda x: convert_value(x[0]), reverse=reverse)
        
        # Rearrange items in sorted positions
        for index, (_, k) in enumerate(items):
            self.table.move(k, '', index)
            
        # Update all column headers to show sort indicators
        for header in self.table["columns"]:
            if header == col:
                indicator = " ▼" if reverse else " ▲"
                self.table.heading(header, 
                                 text=f"{header}{indicator}",
                                 command=lambda h=header: self.sort_by_column(h))
            else:
                # Remove indicators from other columns
                header_text = header.split(" ▼")[0].split(" ▲")[0]
                self.table.heading(header, 
                                 text=header_text,
                                 command=lambda h=header: self.sort_by_column(h))

    def handle_error(self, error_message, retry_callback=None):
        """Display an enhanced error message with retry options."""
        import traceback
        print("[ERROR]", error_message)
        traceback.print_exc()
        error_window = tk.Toplevel(self.root)
        error_window.title("Error")
        error_window.geometry("400x200")
        error_window.resizable(False, False)
        center_window(error_window)
        error_window.configure(bg="#000000")

        tk.Label(
            error_window, text="⚠️ Error", font=("Arial", 16, "bold"), bg="#000000", fg="#ff6f00"
        ).pack(pady=10)
        tk.Label(
            error_window, text=error_message, font=("Arial", 12), bg="#000000", fg="#fffde7"
        ).pack(pady=10)

        if retry_callback:
            tk.Button(
                error_window, text="Retry", command=lambda: [retry_callback(), error_window.destroy()],
                font=("Arial", 12, "bold"), bg="#4CAF50", fg="white"
            ).pack(pady=10)

        tk.Button(
            error_window, text="Close", command=error_window.destroy,
            font=("Arial", 12, "bold"), bg="#F44336", fg="white"
        ).pack(pady=10)

    def reset_table_columns(self, columns, column_widths):
        """Reset the Treeview columns and headings."""
        reset_table_columns(self.table, columns, column_widths)

    def format_row(self, row, columns):
        """Format row values, especially for currency columns and dates."""
        formatted_row = []
        for idx, value in enumerate(row):
            if value is None:
                formatted_row.append("")
            elif columns[idx] == "LAST PO" and value:
                try:
                    from datetime import datetime
                    # Handle different types of date inputs
                    if isinstance(value, str):
                        # Split on space or 'T' to remove time component if present
                        date_part = value.split(' ')[0].split('T')[0]
                        # Remove any time component that might be remaining
                        date_part = date_part.split('.')[0]
                        
                        # Try different possible date formats
                        for fmt in ['%Y-%m-%d', '%Y/%m/%d']:
                            try:
                                dt = datetime.strptime(date_part, fmt)
                                formatted_row.append(dt.strftime('%Y/%m/%d'))
                                break
                            except ValueError:
                                continue
                        else:
                            # If no format matched, just use the date part
                            formatted_row.append(date_part)
                    else:
                        # Handle datetime objects
                        formatted_row.append(value.strftime('%Y/%m/%d'))
                except Exception:
                    # If parsing fails, just take the first 10 characters if it's a string
                    if isinstance(value, str):
                        formatted_row.append(value[:10].replace('-', '/'))
                    else:
                        formatted_row.append(str(value))
            elif columns[idx] in {"PRICE PER UNIT", "COST"}:
                try:
                    formatted_row.append(f"₱{float(value):,.2f}")
                except ValueError:
                    formatted_row.append("₱0.00")
            else:
                formatted_row.append(value)
        return tuple(formatted_row)

    def refresh_current_view(self):
        """Refresh the currently active view (items list or restock list)."""
        if self.current_view == "Restock List":
            print("[DEBUG] Refreshing restock list view...")
            # For restock list, use the enhanced refresh function with database operations
            import os
            from pathlib import Path
            try:
                from main import get_app_dir
            except ImportError:
                def get_app_dir():
                    return Path(__file__).resolve().parent.parent
            app_dir = get_app_dir()
            db_path = os.path.join(app_dir, 'database', 'JJCIMS.accdb')
            
            # Use the enhanced refresh function from vrl.py
            from gui.functions.admdash_f.vrl import refresh_restock_list_after_update
            refresh_restock_list_after_update(db_path, self.table, delay_ms=150)
        else:
            print("[DEBUG] Refreshing items list view...")
            self.load_data()

    def load_data(self, preserve_checked_ids=None):
        """Load data into the table and auto-adjust column widths. Optionally preserve checked state by item ID. Robustly manage after callbacks."""
        # Set up a flag and timer for skeleton screen
        self._skeleton_timer_id = None
        self._skeleton_shown = False
        
        def show_skeleton_if_needed():
            if not self.root or not self.root.winfo_exists():
                return
            self._skeleton_shown = True
            self.show_skeleton_screen()
        
        def _delayed_skeleton():
            if self.root and self.root.winfo_exists():
                show_skeleton_if_needed()
        
        if self.root and self.root.winfo_exists():
            self._skeleton_timer_id = self.root.after(400, _delayed_skeleton)
            if hasattr(self, '_after_ids'):
                self._after_ids.add(self._skeleton_timer_id)

        # Execute Update Status and statssum queries first
        try:
            connection = self.db.connect()
            cursor = connection.cursor()
            cursor.execute("EXEC [Update Status]")
            connection.commit()
            cursor.execute("EXEC statssum")
            connection.commit()
        except Exception as e:
            print(f"Error executing database queries: {e}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()

        # Now load the real data
        def finish_loading():
            if not self.root or not self.root.winfo_exists():
                return
            # Cancel skeleton timer if still pending
            if self._skeleton_timer_id is not None:
                try:
                    self.root.after_cancel(self._skeleton_timer_id)
                    if hasattr(self, '_after_ids'):
                        self._after_ids.discard(self._skeleton_timer_id)
                except Exception:
                    pass
                self._skeleton_timer_id = None
            # If skeleton was shown, remove it by destroying the table and scrollbar
            if getattr(self, '_skeleton_shown', False):
                if hasattr(self, 'table') and self.table:
                    self.table.destroy()
                if hasattr(self, 'scroll_y') and self.scroll_y:
                    self.scroll_y.destroy()
                self._skeleton_shown = False
            # Safely call external load_data only if table still exists
            try:
                if hasattr(self, 'table') and self.table and self.table.winfo_exists():
                    load_data(
                        table=self.table,
                        db=self.db,
                        default_columns=self.default_columns,
                        default_column_widths=self.default_column_widths,
                        format_row=self.format_row,
                        update_stats=self.update_stats
                    )
                else:
                    print('[DEBUG] Skipping load_data: table no longer exists')
            except Exception as e:
                # Catch Tkinter widget errors (invalid command name) and log
                print(f"[DEBUG] load_data aborted due to widget state: {e}")
            # After loading data, always clear selection unless preserving checked state
            # Check if table still exists and is valid before accessing it
            if not hasattr(self, 'table') or not self.table or not self.table.winfo_exists():
                return
                
            if preserve_checked_ids and hasattr(self.table, 'toggle_checkbox') and hasattr(self.table, 'is_checked'):
                for row_id in self.table.get_children(''):
                    values = self.table.item(row_id, 'values')
                    if values and str(values[0]) in preserve_checked_ids and not self.table.is_checked(row_id):
                        self.table.toggle_checkbox(row_id)
            else:
                try:
                    if hasattr(self.table, 'clear_checked'):
                        self.table.clear_checked()
                    else:
                        # Only try to clear selection if table still exists
                        current_selection = self.table.selection()
                        if current_selection:
                            self.table.selection_remove(current_selection)
                except tk.TclError:
                    # Widget was destroyed, ignore the error
                    pass
                except Exception:
                    print("[DEBUG] Error clearing table selection")
        
        def _delayed_finish_loading():
            if self.root and self.root.winfo_exists():
                finish_loading()
        
        # Run finish_loading as soon as possible after DB work
        if self.root and self.root.winfo_exists():
            finish_id = self.root.after(0, _delayed_finish_loading)
            if hasattr(self, '_after_ids'):
                self._after_ids.add(finish_id)

    def clear_table(self):
        """Clear all rows from the Treeview."""
        clear_table(self.table)

    def view_logs(self):
        """Load and display the contents of the Employee Logs sheet in the Treeview."""
        # ...existing code...
        from gui.functions.admdash_f.Logs.vw_logs import view_logs
        self.set_current_view("Employee Logs")
        view_logs(
            self,
            self.logs_path,
            lambda _: None
        )
        from gui.functions.admdash_f.ML.search_bar import update_search_bar_visibility
        update_search_bar_visibility(self)
        from gui.functions.admdash_f.ML.stats_pnl import set_stats_mode
        set_stats_mode("hidden", self.table, self.total_items_label, self.out_of_stock_label, self.low_stock_label, self.total_cost_label)

    def view_admin_logs(self):
        """Load and display the contents of the Admin Logs sheet in the Treeview."""
        # ...existing code...
        from gui.functions.admdash_f.Logs.vw_logs import view_admin_logs
        self.set_current_view("Admin Logs")
        view_admin_logs(
            self,
            self.logs_path,
            lambda _: None
        )
        from gui.functions.admdash_f.ML.search_bar import update_search_bar_visibility
        update_search_bar_visibility(self)
        from gui.functions.admdash_f.ML.stats_pnl import set_stats_mode
        set_stats_mode("hidden", self.table, self.total_items_label, self.out_of_stock_label, self.low_stock_label, self.total_cost_label)


    def set_current_view(self, view_name):
        # Store the current view name
        self.current_view = view_name
        print(f"[DEBUG] Setting current view to: {view_name}")

        # First, hide all special buttons
        if hasattr(self, 'clear_admin_logs_button'):
            self.clear_admin_logs_button.pack_forget()
        if hasattr(self, 'clear_employee_logs_button'):
            self.clear_employee_logs_button.pack_forget()
        if hasattr(self, 'delete_log_button'):
            self.delete_log_button.pack_forget()

        # Handle logs views specifically
        if view_name in ("Admin Logs", "Employee Logs"):
            # For logs views, hide main buttons (add, update, delete)
            if hasattr(self, 'add_button') and hasattr(self, 'update_item_button') and hasattr(self, 'delete_button'):
                hide_main_buttons(self.add_button, self.update_item_button, self.delete_button)
            
            # Show the delete log button for both log views
            if hasattr(self, 'delete_log_button'):
                self.delete_log_button.pack(pady=3)
            
            # Show correct clear button for the specific log view
            if view_name == "Admin Logs" and hasattr(self, 'clear_admin_logs_button'):
                self.clear_admin_logs_button.pack(pady=3)
            elif view_name == "Employee Logs" and hasattr(self, 'clear_employee_logs_button'):
                self.clear_employee_logs_button.pack(pady=3)
        else:
            # For non-logs views, show standard buttons
            if hasattr(self, 'add_button') and hasattr(self, 'update_item_button') and hasattr(self, 'delete_button'):
                show_main_buttons(self.add_button, self.update_item_button, self.delete_button)

        # Always manage export buttons visibility based on current view
        if hasattr(self, 'export_button') and hasattr(self, 'export_csv_button'):
            show_export_buttons(self.export_button, self.export_csv_button, view_name)
            
        print(f"[DEBUG] Button visibility set for view: {view_name}")

    def open_update_window(self): 
        # Use checked items if available (CheckboxTreeview), else fallback to selection()
        if hasattr(self.table, 'get_checked'):
            selected_items = self.table.get_checked()
        else:
            selected_items = self.table.selection()  # Get selected items
        # Filter selected_items to only those present in the current Treeview
        valid_items = set(self.table.get_children())
        selected_items = [item_id for item_id in selected_items if item_id in valid_items]
        if not selected_items:
            self.show_toast("warning", "No Selection", "Please select at least one item to update.")
            return

        # Gather all selected item data into a list, skip missing IDs
        items_data = []
        missing_ids = []
        for item_id in selected_items:
            try:
                item_data = self.table.item(item_id, 'values')
                # Defensive: skip if item_data is empty or None
                if not item_data or all(v == '' for v in item_data):
                    missing_ids.append(item_id)
                    continue
                # Defensive: if LAST_PO is None or empty, set to current date
                item_data = list(item_data)
                if len(item_data) > 14 and (item_data[14] is None or str(item_data[14]).strip().lower() == "none" or str(item_data[14]).strip() == ""):
                    from datetime import datetime
                    item_data[14] = datetime.now().strftime("%Y-%m-%d")
                items_data.append(tuple(item_data))
            except Exception:
                missing_ids.append(item_id)
                continue

        if missing_ids:
            self.show_toast("warning", "Missing Items", "Some selected items could not be found and will be skipped.")

        if items_data:
            def after_update():
                # Clear checked state before reloading data
                if hasattr(self.table, 'clear_checked'):
                    self.table.clear_checked()
                else:
                    try:
                        if self.table and self.table.winfo_exists():
                            current_selection = self.table.selection()
                            if current_selection:
                                self.table.selection_remove(current_selection)
                    except tk.TclError:
                        pass  # Widget destroyed, ignore
                
                # Immediate refresh after save - no delays or complex callbacks
                if self.current_view == "Restock List":
                    print("[DEBUG] Immediate restock list refresh after update save...")
                    self.view_restock_list()  # Direct call for immediate refresh
                else:
                    print("[DEBUG] Refreshing items list after update...")
                    self.load_data()  # Reload the regular items list
                    self.load_data()  # Reload the regular items list
                    
            def clear_selection():
                # Check if the main window still exists before accessing its widgets
                if not self.root or not self.root.winfo_exists():
                    print("[DEBUG] Main window no longer exists, skipping post-update cleanup")
                    return

                # Also clear checked state if user closes update window without saving
                try:
                    if hasattr(self, 'table') and self.table:
                        if hasattr(self.table, 'clear_checked') and callable(self.table.clear_checked):
                            if self.table.winfo_exists():
                                self.table.clear_checked()
                        else:
                            if self.table.winfo_exists():
                                current_selection = self.table.selection()
                                if current_selection:
                                    self.table.selection_remove(current_selection)
                except (tk.TclError, AttributeError, Exception) as e:
                    print(f"[DEBUG] Error during selection cleanup: {str(e)}")
                    pass  # Widget destroyed or other error, ignore
                
                # Refresh the current view properly but safely
                try:
                    if not self.root or not self.root.winfo_exists():
                        print("[DEBUG] Cannot refresh view, root window no longer exists")
                        return
                        
                    if hasattr(self, 'current_view') and self.current_view == "Restock List":
                        print("[DEBUG] Safely refreshing restock list after closing update window...")
                        # Use direct call instead of after to avoid callback issues
                        self.view_restock_list()
                    else:
                        print("[DEBUG] Safely refreshing items list after closing update window...")
                        # Direct call instead of after to avoid callback issues
                        self.load_data()
                except (tk.TclError, AttributeError, Exception) as e:
                    print(f"[DEBUG] Error during view refresh: {str(e)}")
                    pass  # Ignore errors during cleanup
            # Wrap after_update to rebuild style first when returning to ITEMS_LIST
            def styled_after_update():
                try:
                    if self.current_view == "Restock List":
                        after_update()
                    else:
                        # Rebuild styled table then run after_update logic (which refreshes view)
                        self.refresh_items_view()
                except Exception as e:
                    print(f"[DEBUG] styled_after_update error: {e}")
            UpdateItemsWindow(
                self.root, items_data, self.db.connect(),
                refresh_callback=styled_after_update,
                on_close=clear_selection
            )
            
    def open_add_item(self):
        def reload_and_clear():
            if hasattr(self.table, 'clear_checked'):
                self.table.clear_checked()
            else:
                try:
                    if self.table and self.table.winfo_exists():
                        current_selection = self.table.selection()
                        if current_selection:
                            self.table.selection_remove(current_selection)
                except tk.TclError:
                    pass  # Widget destroyed, ignore
            
            # Refresh the current view properly
            if self.current_view == "Restock List":
                print("[DEBUG] Refreshing restock list after adding item...")
                self.view_restock_list()  # Reload the restock list
            else:
                print("[DEBUG] Refreshing items list after adding item...")
                # Use unified refresh to ensure style retained
                self.refresh_items_view()
            # Clear search box so new items become discoverable without stale filter
            try:
                if hasattr(self, 'search_entry') and self.search_entry.winfo_exists():
                    self.search_entry.delete(0, tk.END)
            except Exception:
                pass
            # Schedule a second refresh shortly after to catch any delayed status updates
            try:
                self.root.after(150, lambda: (self.current_view != "Restock List" and self.refresh_items_view()) or None)
            except Exception:
                pass
        # Invoke the imported add_item form helper
        add_item(self.root, self.db, reload_and_clear, self.current_view, self.username)
        # Pass the reload_and_clear method as a callback to refresh and clear the table after adding an item, and current_view for context-sensitive form

    def delete_item(self):
        """Delete the selected item(s) from the database."""
        # Store the current view before deletion
        current_view = self.current_view
        
        # Create a custom update_stats function that also refreshes the view
        def update_stats_and_refresh():
            self.update_stats()  # Update the stats first
            # Then refresh the appropriate view
            if current_view == "Restock List":
                print("[DEBUG] Refreshing restock list after item deletion...")
                # Use after() to ensure the deletion is complete before refreshing
                self.root.after(100, self.view_restock_list)
            else:
                print("[DEBUG] Refreshing items list after item deletion...")
                self.root.after(100, self.load_data)
        
        # Use checked items if available (CheckboxTreeview), else fallback to selection()
        if hasattr(self.table, 'get_checked'):
            checked_items = self.table.get_checked()
            # Patch: temporarily override selection() to return checked items for delete_items
            orig_selection = self.table.selection
            self.table.selection = lambda: [item_id for item_id in checked_items if item_id in self.table.get_children()]
            try:
                delete_item(self.table, self.db, update_stats_and_refresh, self.username)
            finally:
                self.table.selection = orig_selection
        else:
            # Only pass valid item_ids to delete_item
            valid_items = set(self.table.get_children())
            selected_items = [item_id for item_id in self.table.selection() if item_id in valid_items]
            # Temporarily patch selection to only return valid items
            orig_selection = self.table.selection
            self.table.selection = lambda: selected_items
            try:
                delete_item(self.table, self.db, update_stats_and_refresh, self.username)
            finally:
                self.table.selection = orig_selection

    def save_changes(self):
        """Save changes made in the current session back to the database."""
        connection = None
        try:
            # Assuming changes are already reflected in the database connection
            connection = self.db.connect()
            connection.commit()
            self.show_toast("success", "Success", "Changes saved successfully!")
        except Exception as e:
            self.show_toast("error", "Save Error", f"Failed to save changes: {e}")
        finally:
            if connection:
                connection.close()
    # Replace the existing export_file method in AdminDashboard
    def export_excel(self):
        """Export the currently visible data in the Treeview to an Excel file."""
        export_to_xlsx(self.table, self.current_view)

    # Replace the existing export_to_csv method in AdminDashboard
    def export_csv(self):
        """Export the currently visible data in the Treeview to a CSV file."""
        export_to_csv(self.table, self.current_view)

    def view_total_cost(self):
        """Calculate and display the total cost of all items."""
        # FPI/Parts logic fully removed
        try:
            total_cost = 0
            for row_id in self.table.get_children():
                row = self.table.item(row_id, "values")
                # Extract the COST column (index 13) and remove the ₱ sign and commas
                cost_value = row[13].replace("₱", "").replace(",", "")
                total_cost += float(cost_value)

            self.show_toast("info", "Total Cost", f"The total cost is: ₱{total_cost:,.2f}")
        except Exception as e:
            self.show_toast("error", "Calculation Error", f"Failed to calculate total cost: {e}")

    def go_back_to_admin_login(self):
        """Navigate back to the AdminLogin window."""
        # Sound removed
        from gui.admin_login import AdminLogin  # Defer the import to avoid circular dependency
        self.on_close()  # Use on_close to ensure after_cancel is called
        admin_login = AdminLogin()  # Create a new instance of AdminLogin
        admin_login.run()  # Run the AdminLogin window

    def update_stats(self):
        # Guard against destroyed table widget causing invalid command errors
        try:
            if not hasattr(self, 'table') or not self.table or not self.table.winfo_exists():
                return
            db_path = Path(__file__).resolve().parent.parent / "database" / "JJCIMS.accdb"
            update_stats(self.table, self.total_items_label, self.out_of_stock_label, self.low_stock_label, self.total_cost_label, db_path)
        except Exception as e:
            # Silently ignore Tkinter invalid command errors
            print(f"[DEBUG] update_stats skipped: {e}")

    def run(self):
        self.root.mainloop()

    def view_items(self):
        try:
            # Safely reset table before rebuilding to avoid invalid command name errors
            self._safe_reset_table()
            # Always reload the default Treeview with checkboxes and style
            self.create_items_table()  # This ensures CheckboxTreeview and style
            self.set_current_view("ITEMS_LIST")
            self.load_data()
            # Hide clear log buttons
            if hasattr(self, 'clear_admin_logs_button'):
                self.clear_admin_logs_button.pack_forget()
            if hasattr(self, 'clear_employee_logs_button'):
                self.clear_employee_logs_button.pack_forget()
            # Switch stats panel to default mode
            from gui.functions.admdash_f.ML.stats_pnl import set_stats_mode
            set_stats_mode("default", self.table, self.total_items_label, self.out_of_stock_label, self.low_stock_label, self.total_cost_label)
            # Update search bar visibility
            from gui.functions.admdash_f.ML.search_bar import update_search_bar_visibility
            update_search_bar_visibility(self)
            # Force stats update to ensure proper display
            self.update_stats()
        except Exception as e:
            print(f"[DEBUG] view_items error: {e}")

    def view_restock_list(self):
        print("[DEBUG] Loading restock list view...")
        try:
            self._safe_reset_table()
            self.create_items_table()
            db_path = Path(__file__).resolve().parent.parent / "database" / "JJCIMS.accdb"
            load_restock_list(str(db_path), self.table)
            self.set_current_view("Restock List")
            # Hide clear log buttons
            if hasattr(self, 'clear_admin_logs_button'):
                self.clear_admin_logs_button.pack_forget()
            if hasattr(self, 'clear_employee_logs_button'):
                self.clear_employee_logs_button.pack_forget()
            # Hide all other buttons
            hide_main_buttons(self.add_button, self.update_item_button, self.delete_button)
            # Show only the relevant buttons
            self.update_item_button.pack(pady=3)
            self.export_button.pack(pady=3)
            self.export_csv_button.pack(pady=3)
            # Update stats panel for restock list
            from gui.functions.admdash_f.ML.stats_pnl import set_stats_mode
            set_stats_mode("vrl", self.table, self.total_items_label, self.out_of_stock_label, self.low_stock_label, self.total_cost_label, str(Path(__file__).resolve().parent.parent / "database" / "JJCIMS.accdb"))
            print("[DEBUG] Restock list view loaded successfully")
        except Exception as e:
            print(f"[DEBUG] view_restock_list error: {e}")

    def _safe_reset_table(self):
        """Destroy existing table & scrollbar and cancel callbacks safely to prevent 'invalid command name' errors."""
        try:
            # Cancel any pending after callbacks that might reference the old table
            if hasattr(self, '_after_ids') and self.root and self.root.winfo_exists():
                for aid in list(self._after_ids):
                    try:
                        self.root.after_cancel(aid)
                    except Exception:
                        pass
                    finally:
                        self._after_ids.discard(aid)
            # Destroy table and scrollbar if they still exist
            if hasattr(self, 'table') and self.table and self.table.winfo_exists():
                self.table.destroy()
            if hasattr(self, 'scroll_y') and self.scroll_y and self.scroll_y.winfo_exists():
                self.scroll_y.destroy()
            self.table = None
            self.scroll_y = None
        except Exception as e:
            print(f"[DEBUG] _safe_reset_table issue: {e}")

    def hide_main_buttons(self):
        hide_main_buttons(self.add_button, self.update_item_button, self.delete_button)

    def show_main_buttons(self):
        show_main_buttons(self.add_button, self.update_item_button, self.delete_button)

    def show_export_buttons(self):
        show_export_buttons(self.export_button, self.export_csv_button, self.current_view)

    def show_feature_message(self, message):
        """Show a message in the Treeview area indicating a feature is under development."""
        # Destroy and recreate the table to clear any previous content
        if self.table:
            self.table.destroy()
        if self.scroll_y:
            self.scroll_y.destroy()
        self.scroll_y = ttk.Scrollbar(self.table_frame, orient=tk.VERTICAL, style="Custom.Vertical.TScrollbar")
        self.table = ttk.Treeview(
            self.table_frame,
            columns=("MESSAGE",),
            show="headings",
            yscrollcommand=self.scroll_y.set
        )
        self.scroll_y.config(command=self.table.yview)
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.table.pack(fill=tk.BOTH, expand=True)
        self.table.heading("MESSAGE", text="MESSAGE")
        self.table.column("MESSAGE", anchor="center")
        self.table.insert("", "end", values=(message,))

        # --- Treeview header sorting (A-Z) ---
        # After creating the table, bind column headers for sorting
        def bind_treeview_sorting():
            if self.table and hasattr(self.table, 'columns'):
                for col in self.table['columns']:
                    try:
                        self.table.heading(col, text=col, command=lambda c=col: self.sort_by_column(c, False))
                    except Exception:
                        pass
        
        def _delayed_bind_sorting():
            if self.root and self.root.winfo_exists():
                bind_treeview_sorting()
        
        if self.root and self.root.winfo_exists():
            self.root.after(500, _delayed_bind_sorting)  # Delay to ensure table is created

    def delete_log_entry(self):
        """Delete the selected log entry from the current log sheet and refresh the Treeview."""
        import pandas as pd
        selected = self.table.selection()
        if not selected:
            # Sound removed
            self.show_toast("warning", "No Selection", "Please select a log entry to delete.")
            return
        row_values = self.table.item(selected[0], 'values')
        if not row_values:
            # Sound removed
            self.show_toast("warning", "No Selection", "Please select a log entry to delete.")
            return
        # Determine which sheet to edit
        if self.current_view == "Admin Logs":
            sheet_name = "admin"
        elif self.current_view == "Employee Logs":
            sheet_name = "employees"
        else:
            # Sound removed
            self.show_toast("warning", "Invalid View", "Log deletion is only available in Admin Logs or Employee Logs view.")
            return
        
        # Sound removed before confirmation
        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this log entry?"):
            return
            
        logs_path = str(self.logs_path)
        try:
            df = pd.read_excel(logs_path, sheet_name=sheet_name)
            # Find the row to delete by matching all values (string comparison)
            mask = (df.astype(str) == pd.Series(row_values, index=df.columns).astype(str)).all(axis=1)
            if not mask.any():
                # Sound removed
                self.show_toast("warning", "Not Found", "Could not find the selected log entry in the file.")
                return
            df = df[~mask]
            with pd.ExcelWriter(logs_path, mode="a", if_sheet_exists="replace", engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            # Sound removed
            self.show_toast("success", "Success", "Log entry deleted.")
            # Remove from Treeview
            self.table.delete(selected[0])
            # Refresh the view
            if self.current_view == "Admin Logs":
                self.view_admin_logs()
            else:
                self.view_logs()
        except Exception as e:
            # Sound removed
            self.show_toast("error", "Delete Error", f"Failed to delete log entry: {e}")

    def get_table_data(self):
        """Returns the current table data as a list of dictionaries"""
        items = []
        for child in self.table.get_children():
            item = self.table.item(child)['values']
            items.append(item)
        return items