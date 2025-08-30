from pathlib import Path
import tkinter as tk
from tkinter import Canvas, Entry, Button, PhotoImage, Toplevel


class UpdateItemsWindow:
    def __init__(self, root=None, items_data=None, db_connection=None, refresh_callback=None):
        self.window = Toplevel(root)
        
        # Configure window style with withdraw/deiconify trick
        self.window.withdraw()  # Hide window temporarily
        self.window.overrideredirect(True)
        self.window.after(10, self.window.deiconify)  # Show window again
        
        # Window properties
        self.window.geometry("720x720")
        self.window.configure(bg="#000000")
        self.window.title("UPDATE ITEMS")
        self.window.attributes('-alpha', 1.0)
        
        # Store window states
        self.window.minimized = False
        self.window._normal_geometry = None
        
        # Store selected items and database connection
        self.selected_items = items_data or []
        self.db = db_connection
        self.refresh_callback = refresh_callback
        self.current_item_index = 0
        
        # Store images to prevent garbage collection
        self.images = {}
        
        # Assets path - points to parent/assets/upi_assets
        self.assets_path = Path(__file__).resolve().parent.parent.parent.parent.parent / "assets" / "upi_assets"
        
        # Store entry widgets
        self.entries = {}
        
        # Field mappings from database columns to entry widgets
        # Column number to entry mapping:
        # entry_11 = Column 1  (NAME)
        # entry_10 = Column 2  (BRAND)
        # entry_9 = Column 3   (TYPE)
        # entry_8 = Column 4   (LOCATION)
        # entry_7 = Column 5   (UNIT OF MEASURE)
        # entry_6 = Column 7   (IN)
        # entry_5 = Column 8   (OUT)
        # entry_4 = Column 10  (PRICE PER UNIT)
        # entry_3 = Column 12  (MINIMUM STOCK)
        # entry_2 = Column 14  (LAST PO DATE)
        # entry_1 = Column 15  (SUPPLIER)
        
        self.field_mappings = {
            '[Column 1]': 'entry_11',   # NAME
            '[Column 2]': 'entry_10',   # BRAND
            '[Column 3]': 'entry_9',    # TYPE
            '[Column 4]': 'entry_8',    # LOCATION
            '[Column 5]': 'entry_7',    # UNIT OF MEASURE
            '[Column 7]': 'entry_6',    # IN
            '[Column 8]': 'entry_5',    # OUT
            '[Column 10]': 'entry_4',   # PRICE PER UNIT
            '[Column 12]': 'entry_3',   # MINIMUM STOCK
            '[Column 14]': 'entry_2',   # LAST PO DATE
            '[Column 15]': 'entry_1'    # SUPPLIER
        }
        
        # Setup UI and window behavior
        self.setup_window_behavior()
        self.setup_ui()
        self.center_window()
        
        # Initialize fields with selected item data
        if self.selected_items:
            self.initialize_fields(self.selected_items[0])
            
        self.window.grab_set()
        
    def initialize_fields(self, item_data):
        """Initialize entry fields with the selected item's data
        
        Args:
            item_data: Dictionary containing item data from database
        """
        # Clear all entries first
        for entry_name, entry in self.entries.items():
            entry.configure(state='normal')  # Temporarily enable if readonly
            entry.delete(0, tk.END)
            if entry_name == 'entry_12':  # Reset to readonly for Now Editing entry
                entry.configure(state='readonly')
            
        # Populate entries with item data
        for db_field, entry_name in self.field_mappings.items():
            if db_field in item_data:
                value = item_data[db_field]
                if value is not None:
                    self.entries[entry_name].insert(0, str(value))
        
        # Update Now Editing entry with current item name
        self.entries["entry_12"].configure(state='normal')
        name = item_data.get('NAME', '')
        total_items = len(self.selected_items)
        if total_items > 1:
            self.entries["entry_12"].insert(0, f"{name} ({self.current_item_index + 1}/{total_items})")
        else:
            self.entries["entry_12"].insert(0, name)
        self.entries["entry_12"].configure(state='readonly')
                    
    def load_next_item(self):
        """Load the next item's data if multiple items were selected"""
        if self.current_item_index < len(self.selected_items) - 1:
            self.current_item_index += 1
            self.initialize_fields(self.selected_items[self.current_item_index])
            
    def load_previous_item(self):
        """Load the previous item's data if multiple items were selected"""
        if self.current_item_index > 0:
            self.current_item_index -= 1
            self.initialize_fields(self.selected_items[self.current_item_index])
        
    def setup_window_behavior(self):
        """Setup window behavior including dragging and transparency"""
        def start_move(event):
            if not self.window.minimized:
                self.window.x = event.x_root - self.window.winfo_x()
                self.window.y = event.y_root - self.window.winfo_y()

        def do_move(event):
            if not self.window.minimized and hasattr(self.window, 'x'):
                x = event.x_root - self.window.x
                y = event.y_root - self.window.y
                self.window.geometry(f"+{x}+{y}")
        
        def stop_move(event):
            self.window.x = None
            self.window.y = None
            
        def minimize_window():
            if not self.window.minimized:
                self.window._normal_geometry = self.window.geometry()
                self.window.withdraw()
                self.window.minimized = True
            else:
                self.window.deiconify()
                if self.window._normal_geometry:
                    self.window.geometry(self.window._normal_geometry)
                self.window.minimized = False
                self.window.focus_force()
        
        # Create maroon header frame for dragging
        self.header_frame = tk.Frame(self.window, bg="#800000", height=30, cursor="hand2")
        self.header_frame.place(x=0, y=0, width=720)
        
        # Bind dragging events
        self.header_frame.bind('<Button-1>', start_move)
        self.header_frame.bind('<B1-Motion>', do_move)
        self.header_frame.bind('<ButtonRelease-1>', stop_move)
        
        # Window state handlers
        def on_map(event=None):
            self.window.attributes('-alpha', 1.0)
            self.window.attributes('-topmost', True)
            self.window.after(100, lambda: self.window.attributes('-topmost', False))
            
        def on_unmap(event=None):
            self.window.attributes('-alpha', 0.95)
            
        self.window.bind('<Map>', on_map)
        self.window.bind('<Unmap>', on_unmap)
        self.window.bind('<FocusIn>', lambda e: self.window.attributes('-alpha', 1.0))
        self.window.bind('<FocusOut>', lambda e: self.window.attributes('-alpha', 0.95))
        
        # Store minimize function for button command
        self.minimize_window = minimize_window
    
    def center_window(self):
        """Center the window on the screen"""
        window_width = 720
        window_height = 720
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def setup_ui(self):
        """Set up the UI elements of the window"""
        # Create main canvas
        self.canvas = Canvas(
            self.window,
            bg="#000000",
            height=720,
            width=720,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.canvas.place(x=0, y=0)

        # Create header
        self.canvas.create_rectangle(
            0.0,
            0.0,
            720.0,
            35.0,
            fill="#800000",
            outline=""
        )
        
        # Create window control buttons
        window_controls = [
            (9.0, 24.0, "button_1", self.window.destroy),  # Close
            (35.0, 24.0, "button_2", self.minimize_window),  # Minimize
            (61.0, 24.0, "button_3", lambda: None)  # Placeholder for maximize/restore
        ]
        
        # Create control button background
        self.canvas.create_rectangle(
            0.0,
            19.0,
            87.0,
            47.0,
            fill="#834343",
            outline=""
        )
        
        for x, y, btn_name, command in window_controls:
            self.images[btn_name] = PhotoImage(file=self.assets_path / f"{btn_name}.png")
            button = Button(
                self.window,
                image=self.images[btn_name],
                borderwidth=0,
                bg="#800000",
                highlightthickness=0,
                command=command,
                relief="flat",
                activebackground="#800000"
            )
            button.place(x=x, y=y, width=15.0, height=15.0)
            
            # Add hover effects
            button.normal_color = "#800000"
            button.hover_color = "#993333"
            button.bind('<Enter>', lambda e: e.widget.configure(bg=e.widget.hover_color))
            button.bind('<Leave>', lambda e: e.widget.configure(bg=e.widget.normal_color))
        
        # Header text
        self.canvas.create_text(
            25.0,
            7.0,
            anchor="nw",
            text="UPDATE ITEMS",
            fill="#FFFFFF",
            font=("Inter Bold", 16 * -1)
        )
        
        # Create maroon footer
        self.canvas.create_rectangle(
            0.0,
            648.0,
            720.0,
            720.0,
            fill="#800000",
            outline=""
        )

        # Create Now Editing label and entry
        self.canvas.create_text(
            133.0,
            115.0,
            anchor="nw",
            text="Now Editing:",
            fill="#EDE7DD",
            font=("Inter", 14 * -1)
        )

        # Create entry_12 for displaying current item
        self.images["entry_12"] = PhotoImage(file=self.assets_path / "entry_12.png")
        entry_bg_12 = self.canvas.create_image(
            412.5,
            124.0,
            image=self.images["entry_12"]
        )
        entry_12 = Entry(
            self.window,
            bd=0,
            bg="#000000",
            fg="#FFFFFF",
            highlightthickness=0,
            state='readonly'
        )
        entry_12.place(
            x=250.0,
            y=101.0,
            width=325.0,
            height=44.0
        )
        self.entries["entry_12"] = entry_12
        
        # Create entry fields
        entry_positions = [
            ("entry_1", 198.0, 573.0, 400.0, 40.0, "SUPPLIER"),
            ("entry_2", 198.0, 521.0, 400.0, 40.0, "LAST PO DATE"),
            ("entry_3", 198.0, 469.0, 400.0, 40.0, "MINIMUM STOCK"),
            ("entry_4", 198.0, 417.0, 400.0, 40.0, "PRICE PER UNIT"),
            ("entry_5", 198.0, 365.0, 400.0, 40.0, "OUT"),
            ("entry_6", 198.0, 313.0, 400.0, 40.0, "IN"),
            ("entry_7", 198.0, 261.0, 400.0, 40.0, "UNIT OF MEASURE"),
            ("entry_8", 198.0, 209.0, 400.0, 40.0, "LOCATION"),
            ("entry_9", 198.0, 157.0, 400.0, 40.0, "TYPE"),
            ("entry_10", 198.0, 105.0, 400.0, 40.0, "BRAND"),
            ("entry_11", 198.0, 53.0, 400.0, 40.0, "NAME"),
        ]

        # Create entries
        for entry_name, x, y, width, height, label_text in entry_positions:
            # Create background image for entry
            self.images[entry_name] = PhotoImage(file=self.assets_path / f"{entry_name}.png")
            entry_bg = self.canvas.create_image(x, y, image=self.images[entry_name])
            
            # Create the entry widget
            entry = Entry(
                self.window,
                bd=0,
                bg="#000000",
                fg="#FFFFFF",
                highlightthickness=0
            )
            entry.place(
                x=x - 190.0,
                y=y - 20.0,
                width=width - 10.0,
                height=height - 10.0
            )
            self.entries[entry_name] = entry
            
            # Add label for the entry
            self.canvas.create_text(
                x - 190.0,
                y - 15.0,
                anchor="nw",
                text=label_text + ":",
                fill="#FFFFFF",
                font=("Inter Bold", 12 * -1)
            )
        
        # Create Save button
        self.images["button_4"] = PhotoImage(file=self.assets_path / "button_1.png")
        save_button = Button(
            self.window,
            image=self.images["button_4"],
            borderwidth=0,
            highlightthickness=0,
            command=self.handle_save,
            relief="flat",
            cursor="hand2"
        )
        save_button.place(
            x=603.0,
            y=663.0,
            width=30.0,
            height=30.0
        )

        # Create Cancel button
        self.images["button_5"] = PhotoImage(file=self.assets_path / "button_2.png")
        cancel_button = Button(
            self.window,
            image=self.images["button_5"],
            borderwidth=0,
            highlightthickness=0,
            command=self.handle_cancel,
            relief="flat",
            cursor="hand2"
        )
        cancel_button.place(
            x=555.0,
            y=663.0,
            width=30.0,
            height=30.0
        )

        # Button labels
        self.canvas.create_text(
            548.0,
            696.0,
            anchor="nw",
            text="CANCEL",
            fill="#EDE7DD",
            font=("Inter", 10 * -1)
        )

        self.canvas.create_text(
            602.0,
            696.0,
            anchor="nw",
            text="SAVE",
            fill="#EDE7DD",
            font=("Inter", 10 * -1)
        )

        # Window settings
        self.window.resizable(False, False)
        
        # Setup navigation for multiple items
        self.setup_navigation_buttons()

    def handle_save(self):
        """Save the current item's changes to the database"""
        if not self.db or not self.selected_items:
            return
            
        try:
            # Get current item's ID
            current_item = self.selected_items[self.current_item_index]
            item_id = current_item.get('ID')  # Assuming 'ID' is the primary key
            
            if not item_id:
                return
                
            # Collect updated values
            updates = {}
            for db_field, entry_name in self.field_mappings.items():
                value = self.entries[entry_name].get().strip()
                if value:  # Only update non-empty fields
                    updates[db_field] = value
            
            success = False
            error_message = ""
            
            # First attempt - Using parameterized query
            try:
                connection = self.db.connect()
                cursor = connection.cursor()
                
                # Build update query using exact column names
                set_clause = ", ".join([f"{field} = ?" for field in updates.keys()])
                query = f"UPDATE ITEMSDB SET {set_clause} WHERE ID = ?"
                
                # Execute update with proper column values
                cursor.execute(query, list(updates.values()) + [item_id])
                connection.commit()
                success = True
                
            except Exception as e:
                error_message = f"First method failed: {str(e)}\n"
                # Continue to second method if first fails
                
                try:
                    # Second attempt - Using direct value substitution
                    set_clause = ", ".join([f"{field} = '{value}'" for field, value in updates.items()])
                    query = f"UPDATE ITEMSDB SET {set_clause} WHERE ID = {item_id}"
                    
                    cursor.execute(query)
                    connection.commit()
                    success = True
                    
                except Exception as e2:
                    error_message += f"Second method failed: {str(e2)}"
                
            finally:
                if 'connection' in locals():
                    connection.close()
            
            if success:
                # Show success message
                import tkinter.messagebox as messagebox
                messagebox.showinfo("Success", "Item updated successfully!")
                
                # Call refresh callback if provided
                if self.refresh_callback:
                    self.refresh_callback()
                
                # Load next item if available
                if self.current_item_index < len(self.selected_items) - 1:
                    self.load_next_item()
                else:
                    self.window.destroy()
            else:
                import tkinter.messagebox as messagebox
                messagebox.showerror("Error", f"Failed to update item: {error_message}")
                
        except Exception as e:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Error", f"Failed to update item: {str(e)}")
    
    def handle_cancel(self):
        """Close the window"""
        self.window.destroy()
        
    def setup_navigation_buttons(self):
        """Setup navigation buttons for multiple items"""
        if len(self.selected_items) > 1:
            # Create Previous button if it's not the first item
            if self.current_item_index > 0:
                self.images["button_6"] = PhotoImage(file=self.assets_path / "btutton_11.png")
                prev_button = Button(
                    self.window,
                    image=self.images["button_6"],
                    borderwidth=0,
                    highlightthickness=0,
                    command=self.load_previous_item,
                    relief="flat",
                    cursor="hand2"
                )
                prev_button.place(
                    x=510.0,
                    y=663.0,
                    width=30.0,
                    height=30.0
                )
                
            # Create Next button if it's not the last item
            if self.current_item_index < len(self.selected_items) - 1:
                self.images["button_7"] = PhotoImage(file=self.assets_path / "button_12.png")
                next_button = Button(
                    self.window,
                    image=self.images["button_7"],
                    borderwidth=0,
                    highlightthickness=0,
                    command=self.load_next_item,
                    relief="flat",
                    cursor="hand2"
                )
                next_button.place(
                    x=465.0,
                    y=663.0,
                    width=30.0,
                    height=30.0
                )
