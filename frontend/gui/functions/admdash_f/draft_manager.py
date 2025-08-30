import tkinter as tk
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import traceback

class DraftManager:
    def __init__(self, parent_window, db, entries, username):
        self.parent_window = parent_window
        self.db = db
        self.entries = entries
        self.username = username
        self.draft_window = None
        self._is_draft_window_open = False
        
        # Clean up when parent window is destroyed
        self.parent_window.bind('<Destroy>', self._cleanup)

    def _cleanup(self, event=None):
        """Clean up resources when parent window is destroyed"""
        if self.draft_window and self.draft_window.winfo_exists():
            self.draft_window.destroy()
            self._is_draft_window_open = False

    def _show_dialog(self, dialog_type, title, message, parent_window=None):
        """Show a custom modal dialog that keeps parent window visible and focused"""
        dialog = tk.Toplevel(parent_window or self.draft_window)
        
        # Set up the window style for proper system integration
        dialog.overrideredirect(True)
        dialog.withdraw()  # Hide window temporarily
        dialog.after(10, dialog.deiconify)  # Show window again to register with system
        
        dialog.attributes('-alpha', 1.0)
        dialog.wm_title(title)
        
        # Configure dialog appearance
        dialog.configure(bg="#000000")
        dialog.resizable(False, False)
        
        # Create custom title bar
        title_bar = tk.Frame(dialog, bg="#800000", height=30)
        title_bar.pack(fill=tk.X)
        
        title_label = tk.Label(title_bar, text=title, bg="#800000", fg="white", font=("Inter", 10))
        title_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Add window dragging
        def start_move(event):
            dialog.x = event.x_root - dialog.winfo_x()
            dialog.y = event.y_root - dialog.winfo_y()

        def do_move(event):
            if hasattr(dialog, 'x'):
                x = event.x_root - dialog.x
                y = event.y_root - dialog.y
                dialog.geometry(f"+{x}+{y}")

        title_bar.bind("<Button-1>", start_move)
        title_bar.bind("<B1-Motion>", do_move)
        title_bar.configure(cursor="hand2")  # Show move cursor
        
        # Message
        msg_label = tk.Label(dialog, text=message, bg="#000000", fg="white", 
                           font=("Inter", 10), wraplength=300)
        msg_label.pack(padx=20, pady=20)
        
        # Buttons frame
        button_frame = tk.Frame(dialog, bg="#000000")
        button_frame.pack(pady=10)
        
        result = tk.BooleanVar()
        
        def on_yes():
            result.set(True)
            dialog.destroy()
            
        def on_no():
            result.set(False)
            dialog.destroy()
        
        # Create buttons based on dialog type
        if dialog_type == "yesno":
            yes_btn = tk.Button(button_frame, text="Yes", command=on_yes,
                              bg="#800000", fg="white", font=("Inter", 10), width=8)
            yes_btn.pack(side=tk.LEFT, padx=5)
            
            no_btn = tk.Button(button_frame, text="No", command=on_no,
                             bg="#800000", fg="white", font=("Inter", 10), width=8)
            no_btn.pack(side=tk.LEFT, padx=5)
        else:
            ok_btn = tk.Button(button_frame, text="OK", command=on_yes,
                             bg="#800000", fg="white", font=("Inter", 10), width=8)
            ok_btn.pack(padx=5)
        
        # Make dialog modal but keep parent visible
        dialog.transient(parent_window or self.draft_window)
        dialog.grab_set()
        
        # Center dialog on parent and adjust focus
        dialog.update_idletasks()
        parent = parent_window or self.draft_window
        x = parent.winfo_x() + (parent.winfo_width() - dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Window state handlers
        def on_focus_in(event):
            dialog.attributes('-alpha', 1.0)
            dialog.attributes('-topmost', True)
            
        def on_focus_out(event):
            dialog.attributes('-alpha', 0.95)
            dialog.attributes('-topmost', False)
            
        dialog.bind("<FocusIn>", on_focus_in)
        dialog.bind("<FocusOut>", on_focus_out)
        dialog.bind("<Escape>", lambda e: dialog.destroy())
        
        dialog.focus_force()  # Force focus
        dialog.wait_variable(result)
        return result.get()

    def save_draft(self):
        """Save current form values as a draft"""
        # Validate fields
        if not self.entries["entry_1"].get().strip():
            self._show_dialog("info", "Warning", "Please enter an item name before saving draft.", self.parent_window)
            self.entries["entry_1"].focus_set()
            return
            
        # Get current values from all entries
        draft_values = {
            "NAME": self.entries["entry_1"].get().strip(),
            "BRAND": self.entries["entry_2"].get().strip(),
            "TYPE": self.entries["entry_3"].get().strip(),
            "LOCATION": self.entries["entry_4"].get().strip(),
            "MIN_STOCK": self.entries["entry_5"].get().strip(),
            "IN": self.entries["entry_6"].get().strip(),
            "UNIT_OF_MEASURE": self.entries["entry_7"].get().strip(),
            "PRICE_PER_UNIT": self.entries["entry_8"].get().strip(),
            "SUPPLIER": self.entries["entry_9"].get().strip(),
            "DATE": datetime.now().strftime("%d/%m/%Y")
        }

        if all(not value for value in draft_values.values() if value != draft_values["DATE"]):
            self._show_dialog("info", "Warning", "Please fill at least one field before saving draft.", self.parent_window)
            return

        try:
            connection = self.db.connect()
            cursor = connection.cursor()

            cursor.execute("""
                INSERT INTO ANI_DRAFTS (
                    [Date], [Item Name], [Brand], [Type], [Location], 
                    [Unit of Measure], [In], [Minimum Stock], [Price per Unit], [Supplier]
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                draft_values["DATE"], draft_values["NAME"], draft_values["BRAND"], 
                draft_values["TYPE"], draft_values["LOCATION"], draft_values["UNIT_OF_MEASURE"],
                draft_values["IN"], draft_values["MIN_STOCK"], draft_values["PRICE_PER_UNIT"],
                draft_values["SUPPLIER"]
            ))
            connection.commit()
            self._show_dialog("info", "Success", "Draft saved successfully!", self.parent_window)

        except Exception as e:
            self._show_dialog("error", "Error", f"Failed to save draft: {str(e)}", self.parent_window)
            traceback.print_exc()
        finally:
            if 'connection' in locals():
                connection.close()

    def create_draft_window(self):
        """Create the draft selection window"""
        if self.draft_window is not None and self.draft_window.winfo_exists():
            if self.draft_window.state() == 'withdrawn':
                self.draft_window.deiconify()
            self.draft_window.lift()
            self.draft_window.focus_force()
            return

        self.draft_window = tk.Toplevel(self.parent_window)
        
        # Configure window style with withdraw/deiconify trick
        self.draft_window.withdraw()  # Hide window temporarily
        self.draft_window.overrideredirect(True)
        self.draft_window.after(10, self.draft_window.deiconify)  # Show window again to register with system
        
        self.draft_window.attributes('-alpha', 1.0)
        self.draft_window.wm_title("Select Draft")
        
        # Configure window appearance
        self.draft_window.configure(bg="#000000")
        self.draft_window.resizable(False, False)
        
        # Create custom title bar
        title_bar = tk.Frame(self.draft_window, bg="#800000", height=30)
        title_bar.pack(fill=tk.X)
        
        title_label = tk.Label(title_bar, text="Select Draft", bg="#800000", 
                             fg="white", font=("Inter", 10))
        title_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Add window controls
        controls_frame = tk.Frame(title_bar, bg="#800000")
        controls_frame.pack(side=tk.RIGHT, padx=5)
        
        # Close button
        close_btn = tk.Button(controls_frame, text="×", 
                            command=self.draft_window.destroy,
                            bg="#800000", fg="white", font=("Inter", 12), bd=0,
                            activebackground="#A00000", width=2)
        close_btn.pack(side=tk.RIGHT, padx=2)
        
        # Minimize button
        min_btn = tk.Button(controls_frame, text="-", 
                          command=lambda: self.draft_window.withdraw(),
                          bg="#800000", fg="white", font=("Inter", 12), bd=0,
                          activebackground="#A00000", width=2)
        min_btn.pack(side=tk.RIGHT, padx=2)
        
        # Make window draggable
        def start_move(event):
            self.draft_window.x = event.x_root - self.draft_window.winfo_x()
            self.draft_window.y = event.y_root - self.draft_window.winfo_y()

        def do_move(event):
            if hasattr(self.draft_window, 'x'):
                x = event.x_root - self.draft_window.x
                y = event.y_root - self.draft_window.y
                self.draft_window.geometry(f"+{x}+{y}")
                
        title_bar.bind("<Button-1>", start_move)
        title_bar.bind("<B1-Motion>", do_move)
        title_bar.configure(cursor="hand2")
        
        # Window state handlers
        def on_map(event=None):
            self.draft_window.attributes('-alpha', 1.0)
            self.draft_window.attributes('-topmost', True)
            self.draft_window.after(100, lambda: self.draft_window.attributes('-topmost', False))
        
        def on_unmap(event=None):
            self.draft_window.attributes('-alpha', 0.95)
        
        self.draft_window.bind('<Map>', on_map)
        self.draft_window.bind('<Unmap>', on_unmap)
        self.draft_window.bind('<FocusIn>', lambda e: self.draft_window.attributes('-alpha', 1.0))
        self.draft_window.bind('<FocusOut>', lambda e: self.draft_window.attributes('-alpha', 0.95))
        self.draft_window.bind('<Escape>', lambda e: self.draft_window.iconify())
        
        # Create window content
        content_frame = tk.Frame(self.draft_window, bg="#000000")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create Treeview and load data
        self.draft_list = self._create_draft_list(content_frame)
        
        if self._load_drafts():
            self._add_control_buttons()
            
            # Set window size and position
            self.draft_window.geometry("400x400")
            x = self.parent_window.winfo_x() + (self.parent_window.winfo_width() - 400) // 2
            y = self.parent_window.winfo_y() + (self.parent_window.winfo_height() - 400) // 2
            self.draft_window.geometry(f"+{x}+{y}")
            
            # Set window behavior
            self.draft_window.transient(self.parent_window)
            self.draft_window.focus_force()
            
            # Allow window to go behind others after initial show
            self.draft_window.after(100, lambda: self.draft_window.attributes('-topmost', False))
        else:
            self.draft_window.destroy()
            self.draft_window = None

    def _setup_window_drag(self, header_frame):
        """Set up window dragging functionality"""
        def start_move(event):
            self.draft_window.x = event.x
            self.draft_window.y = event.y

        def stop_move(event):
            self.draft_window.x = None
            self.draft_window.y = None

        def do_move(event):
            deltax = event.x - self.draft_window.x
            deltay = event.y - self.draft_window.y
            x = self.draft_window.winfo_x() + deltax
            y = self.draft_window.winfo_y() + deltay
            self.draft_window.geometry(f"+{x}+{y}")
        
        header_frame.bind('<Button-1>', start_move)
        header_frame.bind('<ButtonRelease-1>', stop_move)
        header_frame.bind('<B1-Motion>', do_move)

    def _create_draft_list(self, parent_frame):
        """Create and configure the draft list Treeview"""
        # Create frame for treeview and scrollbar
        treeview_frame = tk.Frame(parent_frame, bg="#000000")
        treeview_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("Date", "Item Name")
        draft_list = ttk.Treeview(treeview_frame, columns=columns, show="headings", height=12)
        
        # Configure columns
        draft_list.heading("Date", text="Date", anchor="center")
        draft_list.heading("Item Name", text="Item Name", anchor="center")
        
        # Set column widths and alignment
        draft_list.column("Date", width=120, anchor="center")
        draft_list.column("Item Name", width=255, anchor="w")

        # Style the Treeview
        style = ttk.Style()
        style.configure("Treeview",
            background="#000000",
            foreground="#FFFFFF",
            fieldbackground="#000000",
            rowheight=25
        )
        style.configure("Treeview.Heading",
            background="#800000",
            foreground="#FFFFFF",
            font=("Inter", 10, "bold")
        )
        
        style.map("Treeview",
            background=[("selected", "#800000")],
            foreground=[("selected", "#FFFFFF")]
        )

        # Add scrollbar
        scrollbar = ttk.Scrollbar(treeview_frame, orient=tk.VERTICAL, command=draft_list.yview)
        draft_list.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        draft_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind double-click to select
        draft_list.bind("<Double-1>", lambda e: self._select_draft())

        return draft_list

    def _load_drafts(self):
        """Load drafts from database into the Treeview"""
        try:
            connection = self.db.connect()
            cursor = connection.cursor()
            cursor.execute("SELECT [Date], [Item Name] FROM ANI_DRAFTS ORDER BY [Date] DESC")
            drafts = cursor.fetchall()
            
            if not drafts:
                self._show_dialog("info", "No Drafts", "No drafts available.", self.parent_window)
                if self.draft_window:
                    self.draft_window.destroy()
                return False
                
            for draft in drafts:
                if isinstance(draft[0], str):
                    try:
                        date_obj = datetime.strptime(draft[0], "%d/%m/%Y")
                    except ValueError:
                        try:
                            date_obj = datetime.strptime(draft[0], "%Y-%m-%d")
                        except ValueError:
                            continue
                else:
                    date_obj = draft[0]
                formatted_date = date_obj.strftime("%d/%m/%Y")
                self.draft_list.insert("", "end", values=(formatted_date, draft[1]))
            return True
                
        except Exception as e:
            self._show_dialog("error", "Error", f"Failed to load drafts: {str(e)}", self.parent_window)
            traceback.print_exc()
            if self.draft_window:
                self.draft_window.destroy()
            return False
        finally:
            if 'connection' in locals():
                connection.close()

    def _select_draft(self):
        """Handle draft selection and loading"""
        selected = self.draft_list.selection()
        if not selected:
            return
        
        try:
            connection = self.db.connect()
            cursor = connection.cursor()
            item_name = self.draft_list.item(selected[0])['values'][1]
            date = self.draft_list.item(selected[0])['values'][0]
            
            cursor.execute("""
                SELECT [Item Name], [Brand], [Type], [Location], [Unit of Measure],
                       [In], [Minimum Stock], [Price per Unit], [Supplier]
                FROM ANI_DRAFTS
                WHERE [Item Name] = ? AND [Date] = ?
            """, (item_name, date))
            
            draft = cursor.fetchone()
            if draft:
                # Map draft values to entries
                self.entries["entry_1"].delete(0, tk.END)
                self.entries["entry_1"].insert(0, draft[0] or "")  # NAME
                self.entries["entry_2"].set(draft[1] or "")        # BRAND
                self.entries["entry_3"].set(draft[2] or "")        # TYPE
                self.entries["entry_4"].set(draft[3] or "")        # LOCATION
                self.entries["entry_7"].set(draft[4] or "")        # UNIT OF MEASURE
                self.entries["entry_6"].delete(0, tk.END)
                self.entries["entry_6"].insert(0, draft[5] or "")  # IN
                self.entries["entry_5"].delete(0, tk.END)
                self.entries["entry_5"].insert(0, draft[6] or "")  # MIN STOCK
                self.entries["entry_8"].delete(0, tk.END)
                self.entries["entry_8"].insert(0, draft[7] or "")  # PRICE PER UNIT
                self.entries["entry_9"].set(draft[8] or "")        # SUPPLIER
                
            self.draft_window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load draft: {str(e)}")
            traceback.print_exc()
        finally:
            if 'connection' in locals():
                connection.close()

    def _delete_draft(self):
        """Delete the selected draft"""
        selected = self.draft_list.selection()
        if not selected:
            self._show_dialog("info", "No Selection", "Please select a draft to delete")
            return
        
        try:
            item_name = self.draft_list.item(selected[0])['values'][1]
            date = self.draft_list.item(selected[0])['values'][0]
            
            # Ask for confirmation
            if not self._show_dialog("yesno", "Confirm Delete", 
                                   f"Are you sure you want to delete the draft for '{item_name}'?"):
                return
                
            connection = self.db.connect()
            cursor = connection.cursor()
            
            cursor.execute("""
                DELETE FROM ANI_DRAFTS
                WHERE [Item Name] = ? AND [Date] = ?
            """, (item_name, date))
            connection.commit()
            
            # Remove from treeview
            self.draft_list.delete(selected[0])
            
            # Check if there are any drafts left
            if not self.draft_list.get_children():
                self._show_dialog("info", "No Drafts", "No drafts available.")
                self.draft_window.destroy()
                return
                
        except Exception as e:
            self._show_dialog("error", "Error", f"Failed to delete draft: {str(e)}")
            traceback.print_exc()
        finally:
            if 'connection' in locals():
                connection.close()

    def _add_control_buttons(self):
        """Add Load, Delete and Cancel buttons to the draft window"""
        button_frame = tk.Frame(self.draft_window, bg="#000000")
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        # Create buttons container for equal spacing
        buttons_container = tk.Frame(button_frame, bg="#000000")
        buttons_container.pack(expand=True)

        # Create buttons
        load_btn = tk.Button(buttons_container, text="Load", command=self._select_draft,
                           bg="#800000", fg="#FFFFFF", width=8,
                           font=("Inter", 10))
        load_btn.pack(side=tk.LEFT, padx=5)

        delete_btn = tk.Button(buttons_container, text="Delete", command=self._delete_draft,
                             bg="#800000", fg="#FFFFFF", width=8,
                             font=("Inter", 10))
        delete_btn.pack(side=tk.LEFT, padx=5)

        cancel_btn = tk.Button(buttons_container, text="Cancel", command=self.draft_window.destroy,
                             bg="#800000", fg="#FFFFFF", width=8,
                             font=("Inter", 10))
        cancel_btn.pack(side=tk.LEFT, padx=5)

    def load_draft(self):
        """Public method to initiate draft loading"""
        self.create_draft_window()
