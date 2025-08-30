from pathlib import Path
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from database import queries
# Legacy Excel logging imports removed (logs now stored in adm_logs table)
import re
from utils.window_icon import set_window_icon

OUTPUT_PATH = Path(__file__).parent

class ToastNotification:
    def __init__(self, parent, message, type="info", duration=3000):
        self.parent = parent
        self.message = message
        self.type = type
        self.duration = duration
        self._after_ids = set()

        # Window
        self.toast = tk.Toplevel(parent)
        self.toast.withdraw()
        self.toast.overrideredirect(True)
        self.toast.attributes('-topmost', True)
        self.toast.attributes('-alpha', 0.9)

        colors = {
            "info": {"bg": "#2196F3", "fg": "#FFFFFF"},
            "success": {"bg": "#4CAF50", "fg": "#FFFFFF"},
            "warning": {"bg": "#FF9800", "fg": "#FFFFFF"},
            "error": {"bg": "#F44336", "fg": "#FFFFFF"}
        }
        color_scheme = colors.get(type, colors["info"])

        main_frame = tk.Frame(self.toast, bg=color_scheme["bg"], relief="solid", bd=1)
        main_frame.pack(fill="both", expand=True, padx=2, pady=2)

        icons = {"info": "ℹ", "success": "✓", "warning": "⚠", "error": "✗"}
        icon = icons.get(type, "ℹ")

        content_frame = tk.Frame(main_frame, bg=color_scheme["bg"])
        content_frame.pack(fill="both", expand=True, padx=10, pady=8)
        tk.Label(content_frame, text=f"{icon} {message}", bg=color_scheme["bg"], fg=color_scheme["fg"], font=("Inter", 10), wraplength=300).pack()

        self.position_toast()
        self.show_toast()
        self._safe_after(duration, self.hide_toast)
        main_frame.bind("<Button-1>", lambda e: self.hide_toast())

    def _safe_after(self, delay_ms, callback):
        if self.toast and self.toast.winfo_exists():
            after_id = self.toast.after(delay_ms, callback)
            self._after_ids.add(after_id)
            return after_id
        return None

    def position_toast(self):
        self.toast.update_idletasks()
        x = self.parent.winfo_x() + self.parent.winfo_width() - self.toast.winfo_reqwidth() - 20
        y = self.parent.winfo_y() + 80
        self.toast.geometry(f"{self.toast.winfo_reqwidth()}x{self.toast.winfo_reqheight()}+{x}+{y}")

    def show_toast(self):
        self.toast.deiconify()
        self.animate_in(0.0)

    def animate_in(self, alpha):
        if alpha < 0.9 and self.toast.winfo_exists():
            self.toast.attributes('-alpha', alpha)
            self._safe_after(20, lambda: self.animate_in(alpha + 0.1))
        else:
            if self.toast.winfo_exists():
                self.toast.attributes('-alpha', 0.9)

    def hide_toast(self):
        if self.toast.winfo_exists():
            self.animate_out(0.9)

    def animate_out(self, alpha):
        if alpha > 0 and self.toast.winfo_exists():
            self.toast.attributes('-alpha', alpha)
            self._safe_after(20, lambda: self.animate_out(alpha - 0.1))
        else:
            for after_id in list(self._after_ids):
                try:
                    self.toast.after_cancel(after_id)
                except Exception:
                    pass
            self._after_ids.clear()
            if self.toast.winfo_exists():
                self.toast.destroy()

def show_toast(parent, message, type="info", duration=3000):
    """Show a toast notification"""
    return ToastNotification(parent, message, type, duration)

def show_custom_dialog(parent, title, message, type="info", buttons=None):  # Deprecated duplicate kept for backward compat
    # Redirect to unified implementation below
    if buttons is None:
        buttons = ["OK"]
    return CustomDialog(parent, title, message, type, buttons).result

class CustomDialog:
    def __init__(self, parent, title, message, type="info", buttons=["OK"]):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x200")
        self.dialog.configure(bg="#000000")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)

        self.dialog.update_idletasks()
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        size = tuple(int(_) for _ in self.dialog.geometry().split('+')[0].split('x'))
        x = screen_width/2 - size[0]/2
        y = screen_height/2 - size[1]/2
        self.dialog.geometry("+%d+%d" % (x, y))

        self.dialog.grid_columnconfigure(0, weight=1)
        self.dialog.grid_rowconfigure(1, weight=1)

        header_frame = tk.Frame(self.dialog, bg="#800000", height=40)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_propagate(False)
        header_frame.grid_columnconfigure(0, weight=1)

        icon_text = "ℹ" if type == "success" else "Saved Successfully" if type == "info" else "Information:" if type == "warning" else "Warning:"
        icon_color = "#1E90FF" if type == "info" else "#FFD700" if type == "warning" else "#FF4040"
        tk.Label(header_frame, text=icon_text, font=("Arial", 20), bg="#800000", fg=icon_color).grid(row=0, column=0, padx=10)

        message_frame = tk.Frame(self.dialog, bg="#000000")
        message_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        message_frame.grid_columnconfigure(0, weight=1)
        message_frame.grid_rowconfigure(0, weight=1)
        tk.Label(message_frame, text=message, font=("Inter", 12), bg="#000000", fg="#FFFFFF", wraplength=350, justify="center").grid(row=0, column=0, pady=10)

        button_frame = tk.Frame(self.dialog, bg="#800000")
        button_frame.grid(row=2, column=0, sticky="ew", ipady=5)
        button_frame.grid_columnconfigure(0, weight=1)

        self.result = None
        
        for i, button_text in enumerate(buttons):
            btn = tk.Button(
                button_frame,
                text=button_text,
                font=("Inter", 10),
                bg="#000000",
                fg="#FFFFFF",
                activebackground="#333333",
                activeforeground="#FFFFFF",
                borderwidth=0,
                width=10,
                command=lambda b=button_text: self.on_button(b)
            )
            btn.grid(row=0, column=i, padx=5, pady=5)

        # Bind escape key to cancel
        self.dialog.bind("<Escape>", lambda e: self.on_button("Cancel" if "Cancel" in buttons else buttons[-1]))
        
        # Bind enter key to OK
        self.dialog.bind("<Return>", lambda e: self.on_button("OK" if "OK" in buttons else buttons[0]))

        # Make dialog modal
        self.dialog.wait_window()

    def on_button(self, button_text):
        self.result = button_text
        self.dialog.destroy()
        self.result = button_text
        self.dialog.destroy()

# Unified show_custom_dialog already defined above
ASSETS_PATH = Path(__file__).parent.parent.parent.parent.parent / "assets" / "upi_assets"

def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)

class UpdateItemsWindow:
    def __init__(self, root, items_data, db_connection, refresh_callback=None, on_close=None):
        # Track all after callback IDs before creating any widgets
        self._after_ids = set()
        
        self.root = tk.Toplevel(root)
        
        # Set consistent window icon
        set_window_icon(self.root)
        
        # Configure window style with withdraw/deiconify trick for borderless window
        self.root.withdraw()  # Hide window temporarily
        self.root.overrideredirect(True)
        # Use after but track the ID
        after_id = self.root.after(10, self.root.deiconify)
        self._after_ids.add(after_id)  # Track this after ID
        
        self.root.attributes('-alpha', 1.0)
        self.root.wm_title("JJCIMS - Update Item")
        self.root.geometry("720x720")
        self.root.configure(bg="#000000")
        self.root.resizable(False, False)
        
        # Store window states
        self.root.minimized = False
        self.root._normal_geometry = None
        
        # Center the window
        window_width = 720
        window_height = 720
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Window state handlers
        def on_map(event=None):
            self.root.attributes('-alpha', 1.0)
            self.root.attributes('-topmost', True)
            self.root.after(100, lambda: self.root.attributes('-topmost', False))
            
        def on_unmap(event=None):
            self.root.attributes('-alpha', 0.95)
            
        self.root.bind('<Map>', on_map)
        self.root.bind('<Unmap>', on_unmap)
        self.root.bind('<FocusIn>', lambda e: self.root.attributes('-alpha', 1.0))
        self.root.bind('<FocusOut>', lambda e: self.root.attributes('-alpha', 0.95))

        # Make window draggable
        def start_move(event):
            if not self.root.minimized:
                self.root.x = event.x_root - self.root.winfo_x()
                self.root.y = event.y_root - self.root.winfo_y()

        def do_move(event):
            if not self.root.minimized and hasattr(self.root, 'x'):
                x = event.x_root - self.root.x
                y = event.y_root - self.root.y
                self.root.geometry(f"+{x}+{y}")
        
        def stop_move(event):
            self.root.x = None
            self.root.y = None
        
        # Create maroon header frame for dragging
        header_frame = tk.Frame(self.root, bg="#800000", height=72, cursor="hand2")
        header_frame.place(x=0, y=0, width=720)
        
        # Bind dragging events to the maroon header
        header_frame.bind('<Button-1>', start_move)
        header_frame.bind('<B1-Motion>', do_move)
        header_frame.bind('<ButtonRelease-1>', stop_move)
        
        if not isinstance(items_data, list) or isinstance(items_data, str):
            items_data = [items_data]
        self.items_data = items_data
        self.db_connection = db_connection
        self.refresh_callback = refresh_callback
        self.on_close = on_close
        self.current_index = 0
        
        # Bind keyboard shortcuts
        self.root.bind("<Return>", lambda e: self.save_changes())
        self.root.bind("<Escape>", lambda e: self._close_window())
        
        # Override window close button - handled by custom buttons since borderless
        self.root.protocol("WM_DELETE_WINDOW", self._close_window)


        # Initialize the canvas
        # Store references to UI elements
        self.entries = {}
        self.entry_fields = [
            ("Now Editing:", "[NAME]", "display"),
            ("Item Name:", "[NAME]", "text"),
            ("Brand:", "[BRAND]", "combobox"),
            ("Type:", "[TYPE]", "combobox"),
            ("Location:", "[LOCATION]", "combobox"),
            ("Unit of Measure:", "[UNIT OF MEASURE]", "combobox"),
            ("In:", "[IN]", "number"),
            ("Out:", "[OUT]", "number"),
            ("Minimum Stock:", "[MIN STOCK]", "number"),
            ("Price Per Unit:", "[PRICE PER UNIT]", "currency"),
            ("Last P.O:", "[LAST PO]", "date"),
            ("Supplier:", "[SUPPLIER]", "combobox")
        ]
        
        # Get unique values from database for comboboxes
        self.combobox_values = {}
        cursor = self.db_connection.cursor()
        
        combobox_fields = {
            "[BRAND]": "BRAND",
            "[TYPE]": "TYPE", 
            "[LOCATION]": "LOCATION",
            "[UNIT OF MEASURE]": "[UNIT OF MEASURE]",
            "[SUPPLIER]": "SUPPLIER"
        }
        
        for field_key, db_column in combobox_fields.items():
            try:
                # Get unique values for each field, excluding None/empty values
                cursor.execute(f"SELECT DISTINCT {db_column} FROM ITEMSDB WHERE {db_column} IS NOT NULL AND {db_column} <> '' ORDER BY {db_column}")
                values = [row[0] for row in cursor.fetchall()]
                self.combobox_values[field_key] = values if values else [""]  # Fallback to empty string if no values found
            except Exception as e:
                print(f"Error fetching values for {db_column}: {str(e)}")
                self.combobox_values[field_key] = [""]  # Fallback to empty string on error

        # Create UI Elements
        self._create_ui()
        
        # Load initial data
        if self.items_data:
            self.load_item(0)
            
    def _create_ui(self):
        # Create custom style for comboboxes
        style = ttk.Style()
        style.configure(
            "Custom.TCombobox",
            fieldbackground="#000000",
            background="#000000",
            foreground="#FFFFFF",
            arrowcolor="#FFFFFF",
            selectbackground="#800000",
            selectforeground="#FFFFFF",
            borderwidth=0,
            highlightthickness=0,
            relief="flat"
        )
        style.layout('Custom.TCombobox', [
            ('Combobox.field', {
                'sticky': 'nswe',
                'children': [
                    ('Combobox.padding', {
                        'expand': '1',
                        'sticky': 'nswe',
                        'children': [
                            ('Combobox.textarea', {'sticky': 'nswe'})
                        ]
                    })
                ]
            })
        ])
        style.map(
            "Custom.TCombobox",
            fieldbackground=[('readonly', '#000000')],
            selectbackground=[('readonly', '#800000')],
            selectforeground=[('readonly', '#FFFFFF')],
            relief=[('readonly', 'flat')]
        )
        
        # Create canvas
        self.canvas = tk.Canvas(
            self.root,
            bg="#000000",
            height=720,
            width=720,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.canvas.place(x=0, y=0)

        # Create all visual elements
        self._create_header()
        self._create_footer()
        self._create_entry_fields()
        self._setup_editing_field()
        self._create_navigation_buttons()

    def _create_header(self):
        # Create header rectangle
        self.canvas.create_rectangle(
            0.0, 0.0, 720.0, 72.0,
            fill="#800000", outline=""
        )
        
        # Load and display center header image
        self.image_3 = tk.PhotoImage(file=relative_to_assets("image_3.png"))
        self.canvas.create_image(361.0, 36.0, image=self.image_3)

    def _create_footer(self):
        # Create footer rectangle
        self.canvas.create_rectangle(
            0.0, 648.0, 720.0, 720.0,
            fill="#800000", outline=""
        )

        # Create save/cancel buttons
        button_commands = {
            "button_1.png": (603.0, 663.0, "SAVE", self.save_changes),
            "button_2.png": (555.0, 663.0, "CLOSE", self._close_window)
        }

        for img_name, (x, y, text, command) in button_commands.items():
            btn_img = tk.PhotoImage(file=relative_to_assets(img_name))
            setattr(self, f"button_img_{img_name.split('.')[0]}", btn_img)
            btn = tk.Button(
                self.root,
                image=btn_img,
                borderwidth=0,
                highlightthickness=0,
                command=command,
                relief="flat"
            )
            btn.place(x=x, y=y, width=30.0, height=30.0)
            
            # Create button labels
            self.canvas.create_text(
                x-5, y+33,
                anchor="nw",
                text=text,
                fill="#EDE7DD",
                font=("Inter", 10 * -1)
            )

    def _create_entry_fields(self):
        # Base y-positions for each row (label, entry)
        row_positions = [
            (115, 101),   # Now Editing
            (184, 208),   # Item Name
            (268, 291),   # Brand
            (268, 291),   # Type
            (268, 291),   # Location
            (352, 375),   # Unit of Measure
            (352, 375),   # In
            (352, 375),   # Out
            (439, 460),   # Minimum Stock
            (439, 460),   # Price Per Unit
            (439, 460),   # Last P.O
            (524, 540),   # Supplier
        ]
        
        # Define y-offset for each group
        brand_row_y = (268, 291)
        measure_row_y = (352, 375)
        stock_row_y = (439, 460)

        # Store entry widgets for later access
        self.entry_widgets = {}
        
        for i, ((label, field, entry_type), (label_y, entry_y)) in enumerate(zip(self.entry_fields, row_positions), start=1):
            # Calculate x positions and y positions based on field type
            if i == 1:  # Now Editing
                x_label = 133.0
                x_entry = 250.0
                width = 325.0
                label_y, entry_y = row_positions[0]
            elif i == 2:  # Item Name
                x_label = 95.0
                x_entry = 113.0
                width = 495.0
                label_y, entry_y = row_positions[1]
            elif i in [3, 4, 5]:  # Brand, Type, Location row
                if i == 3:  # Brand (first column)
                    x_label = 95.0
                    x_entry = 113.0
                elif i == 4:  # Type (second column)
                    x_label = 282.0
                    x_entry = 300.0
                else:  # Location (third column)
                    x_label = 468.0
                    x_entry = 486.0
                width = 122.0
                label_y, entry_y = brand_row_y
            elif i in [6, 7, 8]:  # Unit of Measure, In, Out row
                if i == 6:  # Unit of Measure (first column)
                    x_label = 95.0
                    x_entry = 113.0
                elif i == 7:  # In (second column)
                    x_label = 282.0
                    x_entry = 300.0
                else:  # Out (third column)
                    x_label = 468.0
                    x_entry = 486.0
                width = 122.0
                label_y, entry_y = measure_row_y
            elif i in [9, 10, 11]:  # Minimum Stock, Price Per Unit, Last P.O row
                if i == 9:  # Minimum Stock (first column)
                    x_label = 95.0
                    x_entry = 113.0
                elif i == 10:  # Price Per Unit (second column)
                    x_label = 282.0
                    x_entry = 300.0
                else:  # Last P.O (third column)
                    x_label = 468.0
                    x_entry = 486.0
                width = 122.0
                label_y, entry_y = stock_row_y
            else:  # Supplier
                x_label = 95.0
                x_entry = 113.0
                width = 495.0
                label_y, entry_y = row_positions[11]

            # Create label
            self.canvas.create_text(
                x_label,
                label_y,
                anchor="nw",
                text=label,
                fill="#EDE7DD",
                font=("Inter", 16 * -1)
            )
            
            # Create entry background
            img = tk.PhotoImage(file=relative_to_assets(f"entry_{13-i}.png"))  # Reverse order for images
            setattr(self, f"entry_img_{13-i}", img)
            
            self.canvas.create_image(
                x_entry + width/2,
                entry_y + 22,
                image=img
            )
            
            # Create appropriate widget based on type
            if entry_type == "display":
                entry = tk.Entry(
                    self.root,
                    bd=0,
                    bg="#000000",
                    fg="white",
                    highlightthickness=0,
                    font=("Inter", 12),
                    insertbackground="#FFFFFF"  # Ensure caret is visible
                )
                entry.configure(state="readonly")
            elif entry_type == "combobox":
                values = list(self.combobox_values.get(field, []))
                if values and "Add +" not in values:
                    values.append("Add +")
                # Add empty string option for clearing
                if "" not in values:
                    values.insert(0, "")
                entry = ttk.Combobox(
                    self.root,
                    values=values,
                    font=("Inter", 12),
                    state="readonly",
                    style='Custom.TCombobox'
                )
                self.root.option_add('*TCombobox*Listbox.font', ("Inter", 12))
                entry.bind('<<ComboboxSelected>>', lambda e, cb=entry, f=field: self._handle_combobox_selection(e, cb, f))
                
                # Add key binding to allow clearing with Delete/Backspace
                def clear_combobox(event, combo=entry):
                    if event.keysym in ('Delete', 'BackSpace'):
                        combo.set("")
                        return "break"
                entry.bind('<Key>', clear_combobox)
            elif entry_type in ["number", "currency"]:
                entry = tk.Entry(
                    self.root,
                    bd=0,
                    bg="#000000",
                    fg="white",
                    highlightthickness=0,
                    insertbackground="#FFFFFF",  # Ensure caret is visible
                    font=("Inter", 12),
                    justify='right'
                )
                # Apply number validation to both number and currency fields
                entry.bind('<KeyPress>', lambda e: self._validate_number(e))
                if entry_type == "currency":
                    entry.bind('<FocusOut>', lambda e: self._format_currency(e.widget))
            elif entry_type == "date":
                entry = tk.Entry(
                    self.root,
                    bd=0,
                    bg="#000000",
                    fg="white",
                    highlightthickness=0,
                    insertbackground="#FFFFFF",  # Ensure caret is visible
                    font=("Inter", 12)
                )
                def date_key_handler(event):
                    # Allow Ctrl+A to select all
                    if event.state & 0x4 and event.keysym.lower() == 'a':
                        event.widget.selection_range(0, tk.END)
                        return 'break'
                    
                    # Allow clearing the entire field with Ctrl+Delete or when all text is selected
                    if event.keysym in ('BackSpace', 'Delete'):
                        try:
                            # Check if all text is selected
                            if event.widget.selection_present():
                                event.widget.delete(0, tk.END)
                                return 'break'
                        except tk.TclError:
                            pass  # No selection
                    
                    # Rest of the existing date handling logic
                    content = event.widget.get()
                    cursor_pos = event.widget.index(tk.INSERT)
                    if (not content or content == "YYYY/MM/DD") and event.char.isdigit():
                        event.widget.delete(0, tk.END)
                        event.widget.insert(0, "    /  /  ")
                        event.widget.icursor(0)
                    if event.keysym in ('Left', 'Right', 'Tab'):
                        return
                    if event.keysym in ('BackSpace', 'Delete'):
                        if not content or content.strip() == "YYYY/MM/DD":
                            event.widget.delete(0, tk.END)
                            event.widget.insert(0, datetime.now().strftime("%Y/%m/%d"))
                            return 'break'
                        if cursor_pos in [5, 8] or (event.keysym == 'Delete' and cursor_pos in [4, 7]):
                            return 'break'
                        if event.keysym == 'BackSpace' and cursor_pos > 0:
                            if cursor_pos <= 4:
                                event.widget.delete(cursor_pos-1, cursor_pos)
                                event.widget.insert(cursor_pos-1, " ")
                            elif 6 <= cursor_pos <= 7:
                                event.widget.delete(cursor_pos-1, cursor_pos)
                                event.widget.insert(cursor_pos-1, " ")
                            elif 9 <= cursor_pos <= 10:
                                event.widget.delete(cursor_pos-1, cursor_pos)
                                event.widget.insert(cursor_pos-1, " ")
                            event.widget.icursor(cursor_pos-1)
                        elif event.keysym == 'Delete' and cursor_pos < len(content):
                            if cursor_pos < 4:
                                event.widget.delete(cursor_pos, cursor_pos+1)
                                event.widget.insert(cursor_pos, " ")
                            elif 5 <= cursor_pos <= 6:
                                event.widget.delete(cursor_pos, cursor_pos+1)
                                event.widget.insert(cursor_pos, " ")
                            elif 8 <= cursor_pos <= 9:
                                event.widget.delete(cursor_pos, cursor_pos+1)
                                event.widget.insert(cursor_pos, " ")
                            event.widget.icursor(cursor_pos)
                        return 'break'
                    if not event.char.isdigit():
                        return 'break'
                    if cursor_pos < 4:
                        if cursor_pos < 4:
                            event.widget.delete(cursor_pos, cursor_pos + 1)
                            event.widget.insert(cursor_pos, event.char)
                            new_pos = cursor_pos + 1
                            if new_pos == 4:
                                new_pos = 5
                            event.widget.icursor(new_pos)
                    elif 5 <= cursor_pos <= 6:
                        # removed unused variable 'current'
                        if cursor_pos == 5:
                            if int(event.char + "0") <= 12:
                                event.widget.delete(5, 6)
                                event.widget.insert(5, event.char)
                                event.widget.icursor(6)
                        else:
                            month = int(event.widget.get()[5] + event.char)
                            if month <= 12:
                                event.widget.delete(6, 7)
                                event.widget.insert(6, event.char)
                                event.widget.icursor(8)
                    elif 8 <= cursor_pos <= 9:
                        # removed unused variable 'current'
                        if cursor_pos == 8:
                            if int(event.char + "0") <= 31:
                                event.widget.delete(8, 9)
                                event.widget.insert(8, event.char)
                                event.widget.icursor(9)
                        else:
                            day = int(event.widget.get()[8] + event.char)
                            if day <= 31:
                                event.widget.delete(9, 10)
                                event.widget.insert(9, event.char)
                                event.widget.icursor(10)
                    return 'break'
                def on_focus_in(event):
                    content = event.widget.get().strip()
                    if not content:
                        event.widget.insert(0, "YYYY/MM/DD")
                        event.widget.selection_range(0, 4)
                def on_focus_out(event):
                    content = event.widget.get()
                    if content == "YYYY/MM/DD":
                        event.widget.delete(0, tk.END)
                    else:
                        self._validate_date(event.widget)
                entry.bind('<Key>', date_key_handler)
                entry.bind('<FocusIn>', on_focus_in)
                entry.bind('<FocusOut>', on_focus_out)
            else:
                entry = tk.Entry(
                    self.root,
                    bd=0,
                    bg="#000000",
                    fg="white",
                    highlightthickness=0,
                    insertbackground="#FFFFFF",  # Ensure caret is visible
                    font=("Inter", 12)
                )
            
            # Place the widget
            entry.place(
                x=x_entry,
                y=entry_y,
                width=width,
                height=44.0
            )
            
            # Store entry widget reference
            self.entries[field] = entry

    def _setup_editing_field(self):
        # Create "Now Editing" label with black background for better visibility
        now_editing_frame = tk.Frame(
            self.root,
            bg="#000000",
            width=100,
            height=30
        )
        now_editing_frame.place(x=133.0, y=115.0)
        
        tk.Label(
            now_editing_frame,
            text="Now Editing:",
            fg="#EDE7DD",
            bg="#000000",
            font=("Inter", 16 * -1)
        ).pack()

        # Create the background image
        self.image_1 = tk.PhotoImage(file=relative_to_assets("image_1.png"))
        self.canvas.create_image(361.0, 124.0, image=self.image_1)

        self.entry_img_12 = tk.PhotoImage(file=relative_to_assets("entry_12.png"))
        self.canvas.create_image(412.5, 124.0, image=self.entry_img_12)
        
        self.editing_entry = tk.Entry(
            self.root,
            bd=0,
            bg="#000000",
            fg="white",
            highlightthickness=0,
            font=("Inter", 12),
            readonlybackground="#000000"  # Set readonly background color
        )
        self.editing_entry.place(x=250.0, y=101.0, width=325.0, height=44.0)
        self.editing_entry.configure(state="readonly")

    def _create_navigation_buttons(self):
        if len(self.items_data) > 1:
            # Create navigation button images
            self.button_img_11 = tk.PhotoImage(file=relative_to_assets("button_11.png"))
            self.button_img_12 = tk.PhotoImage(file=relative_to_assets("button_12.png"))
            
            # Create previous button
            self.prev_btn = tk.Button(
                self.root,
                image=self.button_img_11,
                borderwidth=0,
                highlightthickness=0,
                command=self.goto_prev_item,
                relief="flat"
            )
            self.prev_btn.place(x=91.0, y=112.0, width=23.0, height=27.0)
            
            # Create next button
            self.next_btn = tk.Button(
                self.root,
                image=self.button_img_12,
                borderwidth=0,
                highlightthickness=0,
                command=self.goto_next_item,
                relief="flat"
            )
            self.next_btn.place(x=609.0, y=112.0, width=22.0, height=27.0)

    def _handle_window_control(self, button_index):
        if button_index == 0:    # Minimize
            self.minimize_window()
        elif button_index == 2:   # Close
            self._close_window()
    
    def minimize_window(self):
        """Minimize the borderless window"""
        if not self.root.minimized:
            # Store current state and minimize
            self.root._normal_geometry = self.root.geometry()
            self.root.withdraw()
            self.root.minimized = True
        else:
            # Restore window
            self.root.deiconify()
            if self.root._normal_geometry:
                self.root.geometry(self.root._normal_geometry)
            self.root.minimized = False
            self.root.focus_force()
            
    def _has_changes(self):
        """Check if there are any unsaved changes"""
        for field, entry in self.entries.items():
            if field == "[NAME]" and entry == self.editing_entry:
                continue  # Skip the "Now Editing" field
            current_value = entry.get().strip()
            original_idx = self.get_field_index(field)
            if original_idx < 0 or original_idx >= len(self.items_data[self.current_index]):
                continue
            original_value = str(self.items_data[self.current_index][original_idx])
            # Handle numeric values properly
            if field in ["[IN]", "[OUT]", "[MIN STOCK]", "[PRICE PER UNIT]"]:
                try:
                    current_num = float(current_value.replace(",", "") if current_value else 0)
                    original_num = float(original_value.replace(",", "") if original_value else 0)
                    if abs(current_num - original_num) > 0.001:  # Using small epsilon for float comparison
                        return True
                except ValueError:
                    if current_value != original_value:
                        return True
            else:
                if current_value != original_value:
                    return True
        return False

    def goto_next_item(self):
        if self._has_changes():
            closed = self.save_changes(prompt=True)
            if closed:
                return
        if self.items_data:
            self.current_index = (self.current_index + 1) % len(self.items_data)
            self.load_item(self.current_index)

    def goto_prev_item(self):
        if self._has_changes():
            closed = self.save_changes(prompt=True)
            if closed:
                return
        if self.items_data:
            self.current_index = (self.current_index - 1) % len(self.items_data)
            self.load_item(self.current_index)

    def load_item(self, idx):
        if not self.items_data:
            return
            
        self.current_index = idx
        item_data = self.items_data[idx]
        
        # Debug print
        print("Item Data:", item_data)
        print("Item Data Length:", len(item_data))
        
        # Get the name from the correct index for Now Editing
        name_value = item_data[0]  # NAME is at index 0
        
        # Update the "Now Editing" field
        self.editing_entry.configure(state="normal")
        self.editing_entry.delete(0, tk.END)
        self.editing_entry.insert(0, f"  {name_value}")  
        self.editing_entry.configure(state="readonly")
        
        # Map data to entry fields
        field_mapping = {
                "[NAME]": 0,            # Column 0 - Item Name
                "[BRAND]": 1,           # Column 1 - Brand
                "[TYPE]": 2,            # Column 2 - Type
                "[LOCATION]": 3,        # Column 3 - Location
                "[UNIT OF MEASURE]": 4,  # Column 4 - Unit of Measure
                "[IN]": 6,             # Column 6 - In (after STATUS)
                "[OUT]": 7,            # Column 7 - Out
                "[MIN STOCK]": 9,      # Column 9 - Min Stock (after BALANCE)
                "[PRICE PER UNIT]": 11, # Column 11 - Price Per Unit (after DEFICIT)
                "[LAST PO]": 13,        # Column 13 - Last P.O (after COST)
                "[SUPPLIER]": 14        # Column 14 - Supplier
            }
        
        for field, entry in self.entries.items():
            try:
                value = item_data[field_mapping[field]]
            except (IndexError, KeyError) as e:
                print(f"Error loading field {field}: {str(e)}")
                value = ""
            if field == "[LAST PO]":
                if value is None or str(value).strip().lower() == "none" or not str(value).strip():
                    value = datetime.now().strftime("%Y/%m/%d")  # Auto-fill with current date
            
            if isinstance(entry, ttk.Combobox):
                # For comboboxes, ensure value exists in the list
                current_values = list(entry['values'])
                str_value = str(value) if value is not None else ""
                if str_value and str_value not in current_values:
                    if "Add +" in current_values:
                        current_values.remove("Add +")
                    current_values.append(str_value)
                    current_values.sort()
                    current_values.append("Add +")
                    entry['values'] = current_values
                entry.set(str_value)
            else:
                # For regular entries
                entry.delete(0, tk.END)
                entry.insert(0, str(value) if value is not None else "")

    def save_changes(self, prompt=True):
        def clean_numeric(value):
            value = re.sub(r"[^\d.]", "", str(value))
            if value == "":
                return 0
            try:
                return float(value) if '.' in value else int(value)
            except ValueError:
                raise ValueError(f"Invalid numeric value: {value}")

        def clean_date(value):
            if not value or not str(value).strip():
                return None
            try:
                # Convert to YYYY/MM/DD format, accepting both / and - as separators
                date = datetime.strptime(value.replace('-', '/'), "%Y/%m/%d")
                return date.strftime("%Y/%m/%d")
            except ValueError:
                raise ValueError(f"Invalid date format for Last P.O: {value}. Expected format: YYYY/MM/DD")

        try:
            # Before saving, check if there are unsaved changes when switching items
            if prompt and len(self.items_data) > 1:
                result = show_custom_dialog(
                    self.root,
                    "Unsaved Changes",
                    "You have unsaved changes. What would you like to do?",
                    type="warning",
                    buttons=["Save", "Don't Save", "Cancel"]
                )
                if result == "Cancel":
                    return True
                if result == "Don't Save":
                    return False

            # Get updated data from entry fields
            updated_data = {}
            for field, entry in self.entries.items():
                value = entry.get().strip()
                
                if field in ["[IN]", "[OUT]", "[MIN STOCK]", "[PRICE PER UNIT]"]:
                    value = clean_numeric(value)
                elif field == "[LAST PO]":
                    value = clean_date(value)
                    
                updated_data[field] = value

            # Validate required fields
            required_fields = ["[NAME]", "[BRAND]", "[TYPE]", "[LOCATION]", "[UNIT OF MEASURE]"]
            for field in required_fields:
                if not updated_data.get(field):
                    if prompt:
                        field_name = field.strip('[]').replace('_', ' ').title()
                        show_toast(
                            self.root,
                            f"{field_name} is required",
                            type="error"
                        )
                    return False

            # Check for actual changes
            changes = []
            for field, value in updated_data.items():
                original_value = str(self.items_data[self.current_index][self.get_field_index(field)])
                new_value = str(value)
                if original_value != new_value:
                    changes.append(f"{field}: {original_value} → {new_value}")

            if not changes:
                if prompt:
                    show_toast(
                        self.root,
                        "No changes to save",
                        type="info"
                    )
                return False

            # Update database
            try:
                # Build fields dict for update_item_by_id using ID where possible
                original_name = self.items_data[self.current_index][0]
                # Map updated_data keys (e.g. "[NAME]") to column names used by DB
                column_map = {
                    "[NAME]": "NAME",
                    "[BRAND]": "BRAND",
                    "[TYPE]": "TYPE",
                    "[LOCATION]": "LOCATION",
                    "[UNIT OF MEASURE]": "UNIT OF MEASURE",
                    "[IN]": "IN",
                    "[OUT]": "OUT",
                    "[MIN STOCK]": "MIN STOCK",
                    "[PRICE PER UNIT]": "PRICE PER UNIT",
                    "[LAST PO]": "LAST PO",
                    "[SUPPLIER]": "SUPPLIER",
                }

                # Prefer to update by ID if ID is available in items_data rows (first element may be NAME)
                item_id = None
                try:
                    # If the row contains an ID column, attempt to use it. Many queries return NAME first; fall back to NAME update.
                    if len(self.items_data[self.current_index]) > 0 and isinstance(self.items_data[self.current_index][0], int):
                        item_id = self.items_data[self.current_index][0]
                except Exception:
                    item_id = None

                fields_to_update = {}
                for field, value in updated_data.items():
                    col = column_map.get(field)
                    if col is None:
                        continue
                    # Access connector expects column names without brackets in helpers
                    fields_to_update[col] = value

                if item_id is not None:
                    # Update by ID
                    queries.update_item_by_id(self.db_connection, item_id, fields_to_update)
                else:
                    # No ID available; perform an UPDATE by NAME using a helper call that builds SQL
                    # Use update_item_by_id with a WHERE on NAME by executing a custom query via connector
                    set_clause = ", ".join([f"[{k}] = ?" for k in fields_to_update.keys()])
                    params = tuple(fields_to_update.values()) + (original_name,)
                    query = f"UPDATE ITEMSDB SET {set_clause} WHERE NAME = ?"
                    self.db_connection.execute_query(query, params)

                # Attempt to run Access stored queries; if connector doesn't support EXEC syntax, ignore failures
                try:
                    self.db_connection.execute_query("EXEC [Update Status]")
                    self.db_connection.execute_query("EXEC statssum")
                except Exception:
                    # Fallback: recalc STATUS with local SQL
                    fallback_sql = (
                        "UPDATE ITEMSDB "
                        "SET STATUS = IIf(BALANCE > 0 AND BALANCE <= [MIN STOCK], 'Low in Stock', "
                        "IIf(BALANCE = 0, 'Out of Stock', 'In Stock')) "
                        "WHERE BALANCE IS NOT NULL AND [MIN STOCK] IS NOT NULL;"
                    )
                    try:
                        self.db_connection.execute_query(fallback_sql)
                    except Exception:
                        # If fallback also fails, continue without raising so UI can handle gracefully
                        pass

                # Create a concise but detailed log message
                change_descriptions = []
                for field, value in updated_data.items():
                    original_value = self.items_data[self.current_index][self.get_field_index(field)]
                    if str(value) != str(original_value):
                        field_name = field.strip('[]').replace('_', ' ').lower()
                        if field == "[UNIT OF MEASURE]":
                            change_descriptions.append(f"unit changed to {value}")
                        elif field in ["[IN]", "[OUT]"]:
                            action = "increased" if float(str(value)) > float(str(original_value or 0)) else "decreased"
                            change_descriptions.append(f"stock {action} to {value}")
                        elif field == "[MIN STOCK]":
                            change_descriptions.append(f"minimum stock set to {value}")
                        elif field == "[PRICE PER UNIT]":
                            change_descriptions.append(f"price updated to {value}")
                        elif field == "[LAST PO]":
                            change_descriptions.append(f"last PO set to {value}")
                        elif field in ["[BRAND]", "[TYPE]", "[LOCATION]", "[SUPPLIER]"]:
                            change_descriptions.append(f"{field_name} changed to {value}")

                log_message = f"Updated '{updated_data['[NAME]']}' — {', '.join(change_descriptions)}"
                
                # Use the username if available, else fallback to 'Admin' and insert admin log via queries helper
                username = getattr(self, 'username', None)
                if not username:
                    try:
                        username = self.root.master.username
                    except Exception:
                        username = "Admin"
                queries.insert_admin_log(self.db_connection, username, log_message)

                if prompt:
                    show_toast(
                        self.root,
                        "Item updated successfully!",
                        type="success"
                    )

                # Update local data
                item_list = list(self.items_data[self.current_index])
                for field, value in updated_data.items():
                    idx = self.get_field_index(field)
                    item_list[idx] = value
                self.items_data[self.current_index] = tuple(item_list)

                # Refresh the parent window if callback exists
                if self.refresh_callback:
                    self.refresh_callback()

                # Do NOT close the update window after saving; user must close manually
                return False  # Window not closed

            except Exception as e:
                if prompt:
                    show_toast(
                        self.root,
                        f"Failed to update database: {str(e)}",
                        type="error"
                    )
                return False

        except ValueError as ve:
            if prompt:
                show_toast(
                    self.root,
                    str(ve),
                    type="error"
                )
            return False

    def get_field_index(self, field):
        mapping = {
            "NAME": 0,           # Column 0
            "BRAND": 1,          # Column 1
            "TYPE": 2,          # Column 2
            "LOCATION": 3,       # Column 3
            "UNIT_OF_MEASURE": 4, # Column 4
            "IN": 6,            # Column 6 (after STATUS)
            "OUT": 7,           # Column 7
            "MIN_STOCK": 9,     # Column 9 (after BALANCE)
            "PRICE_PER_UNIT": 11, # Column 11 (after DEFICIT)
            "LAST_PO": 13,       # Column 13 (after COST)
            "SUPPLIER": 14       # Column 14
        }
        return mapping.get(field.strip('[]'), -1)

    def _log_to_admin_sheet(self, log_entry):
        """Insert log entry into adm_logs table (DATE, TIME, USER, DETAILS).

        Replaces legacy Excel logging. Accepts a list [DATE, TIME, USER, DETAILS].
        Attempts to create adm_logs table if missing (best-effort, silent on failure).
        """
        if not hasattr(self, 'db_connection') or self.db_connection is None:
            try:
                self.db_connection = self.db
            except Exception:
                return
        try:
            cursor = self.db_connection.cursor()
            try:
                cursor.execute(
                    "INSERT INTO [adm_logs] ([DATE],[TIME],[USER],[DETAILS]) VALUES (?,?,?,?)",
                    tuple(log_entry[:4])
                )
                self.db_connection.commit()
            except Exception as insert_err:
                if "adm_logs" in str(insert_err).lower():
                    try:
                        cursor.execute(
                            """
                            CREATE TABLE adm_logs (
                                ID AUTOINCREMENT PRIMARY KEY,
                                [DATE] DATETIME,
                                [TIME] TEXT(8),
                                [USER] TEXT(255),
                                [DETAILS] TEXT(255)
                            )
                            """
                        )
                        self.db_connection.commit()
                        cursor.execute(
                            "INSERT INTO [adm_logs] ([DATE],[TIME],[USER],[DETAILS]) VALUES (?,?,?,?)",
                            tuple(log_entry[:4])
                        )
                        self.db_connection.commit()
                    except Exception as create_err:
                        print(f"[LOGGING] Failed to create adm_logs: {create_err}")
                else:
                    print(f"[LOGGING] Insert failed: {insert_err}")
        except Exception as outer_err:
            print(f"[LOGGING] Unexpected logging error: {outer_err}")

    def _validate_number(self, event):
        """Validates that only numbers are entered while allowing essential keys"""
        # Allow control keys (backspace, delete, tab, arrow keys, etc.)
        if event.keysym in ('BackSpace', 'Delete', 'Tab', 'Left', 'Right', 'Up', 'Down', 
                           'Home', 'End', 'Prior', 'Next', 'Return', 'KP_Enter'):
            return
        
        # Allow Ctrl+A (select all), Ctrl+C (copy), Ctrl+V (paste), Ctrl+X (cut)
        if event.state & 0x4:  # Ctrl key is pressed
            if event.keysym.lower() in ('a', 'c', 'v', 'x'):
                return
        
        # Only allow digits and decimal point
        if event.char and not (event.char.isdigit() or event.char == '.'):
            return "break"
        
        # Prevent multiple decimal points
        if event.char == '.' and '.' in event.widget.get():
            return "break"
            
    def _validate_date(self, widget):
        """Validates and formats date input"""
        date_str = widget.get().strip()
        
        # Allow empty dates
        if not date_str or date_str == "YYYY/MM/DD":
            widget.delete(0, tk.END)
            return
            
        try:
            # If it's a partial date, don't validate yet
            if any(x in date_str for x in ['Y', 'M', 'D']):
                return
                
            # Parse and validate the date
            date = datetime.strptime(date_str.replace('-', '/'), "%Y/%m/%d")
            
            # Validate year is not too far in the future
            current_year = datetime.now().year
            if date.year > current_year + 10:  # Allow dates up to 10 years in the future
                date = date.replace(year=current_year)
            
            # Format back to the standard format
            widget.delete(0, tk.END)
            widget.insert(0, date.strftime("%Y/%m/%d"))
            
        except ValueError:
            # Don't show error dialog during normal editing
            if not any(x in date_str for x in ['Y', 'M', 'D']):
                show_toast(
                    self.root,
                    "Please enter a valid date in YYYY/MM/DD format",
                    type="error"
                )
                widget.delete(0, tk.END)
                widget.insert(0, "YYYY/MM/DD")
                widget.selection_range(0, 4)
            
    def _format_currency(self, widget):
        """Formats number as currency"""
        try:
            value = widget.get().replace(",", "").strip()
            # Allow empty values
            if not value:
                return
            value = float(value)
            widget.delete(0, tk.END)
            widget.insert(0, f"{value:,.2f}")
        except ValueError:
            # Only show error for non-empty invalid values
            current_value = widget.get().strip()
            if current_value:  # Only show error if there's actually a value
                show_toast(
                    self.root,
                    "Invalid currency value",
                    type="error"
                )
                widget.delete(0, tk.END)
                widget.insert(0, "0.00")

    def _handle_combobox_selection(self, event, combobox, field):
        """Handle combobox selection, including the Add + option"""
        if combobox.get() == "Add +":
            self._add_new_value(field, combobox)
    
    def _add_new_value(self, field, combobox):
        """Make combo box editable to add new values directly"""
        # Store current values
        current_values = list(combobox['values'])
        if "Add +" in current_values:
            current_values.remove("Add +")
        
        # Create a new entry for adding value
        add_window = tk.Toplevel(self.root)
        add_window.title(f"Add New {field.strip('[]').replace('_', ' ').title()}")
        add_window.geometry("300x120")
        add_window.configure(bg="#000000")
        add_window.transient(self.root)
        add_window.grab_set()
        
        # Create and pack widgets
        tk.Label(
            add_window,
            text=f"Enter new {field.strip('[]').replace('_', ' ').title()}:",
            bg="#000000",
            fg="#FFFFFF",
            font=("Inter", 10)
        ).pack(pady=10)
        
        entry = tk.Entry(
            add_window,
            bg="#000000",
            fg="#FFFFFF",
            font=("Inter", 10),
            insertbackground="#FFFFFF"
        )
        entry.pack(pady=5)
        entry.focus_set()
        
        def save_value():
            new_value = entry.get().strip()
            if new_value and new_value != "Add +":
                # Update combobox values
                new_values = list(current_values)
                if new_value not in new_values:
                    new_values.append(new_value)
                new_values.sort()
                new_values.append("Add +")
                
                combobox['values'] = new_values
                combobox.set(new_value)
                
                # Update stored values
                self.combobox_values[field] = [v for v in new_values if v != "Add +"]
                
            add_window.destroy()
        
        # Create a frame for buttons with maroon background
        button_frame = tk.Frame(add_window, bg="#800000")
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Add Save and Close buttons
        tk.Button(
            button_frame,
            text="Save",
            command=save_value,
            bg="#000000",
            fg="#FFFFFF",
            font=("Inter", 10)
        ).pack(side=tk.RIGHT, padx=5, pady=5)
        
        tk.Button(
            button_frame,
            text="Cancel",
            command=add_window.destroy,
            bg="#000000",
            fg="#FFFFFF",
            font=("Inter", 10)
        ).pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Bind Enter and Escape keys
        entry.bind('<Return>', lambda e: save_value())
        add_window.bind('<Escape>', lambda e: add_window.destroy())
        
        # Center the window on parent
        add_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - add_window.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - add_window.winfo_height()) // 2
        add_window.geometry(f"+{x}+{y}")
    


    def _close_window(self):
        # Check for unsaved changes before closing
        if self._has_changes():
            result = show_custom_dialog(
                self.root,
                "Unsaved Changes",
                "You have unsaved changes. What would you like to do?",
                type="warning",
                buttons=["Save", "Don't Save", "Cancel"]
            )
            if result == "Save":
                # If save is successful and doesn't return True (indicating cancellation)
                if not self.save_changes(prompt=True):
                    self._cleanup_and_close()
            elif result == "Don't Save":
                self._cleanup_and_close()
            # If result is "Cancel", do nothing and keep window open
        else:
            self._cleanup_and_close()
    
    def _cleanup_and_close(self):
        """Helper method to handle the actual window cleanup and closing"""
        # Cancel any pending after callbacks
        if hasattr(self, '_after_ids'):
            for after_id in list(self._after_ids):
                try:
                    if self.root and self.root.winfo_exists():
                        self.root.after_cancel(after_id)
                except Exception:
                    pass  # Ignore errors during cleanup
            self._after_ids.clear()
            
        # Call on_close callback if provided
        if self.on_close and callable(self.on_close):
            try:
                self.on_close()
            except Exception as e:
                print(f"Error in on_close callback: {str(e)}")
                
        # Destroy the window
        if self.root and self.root.winfo_exists():
            try:
                self.root.destroy()
            except Exception as e:
                print(f"Error destroying window: {str(e)}")

