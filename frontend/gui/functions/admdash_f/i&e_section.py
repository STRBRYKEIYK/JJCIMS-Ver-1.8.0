from pathlib import Path
from tkinter import (
    Tk,
    Canvas,
    Entry,
    Button,
    PhotoImage,
    IntVar,
    BooleanVar,
    Frame,
    messagebox,
    filedialog,
)
import tkinter as tk
import os
import shutil
from backend.database import get_db_path

# Optional dependencies
try:
    import openpyxl  # type: ignore

    HAS_OPENPYXL = True
except Exception:
    openpyxl = None  # type: ignore[assignment]
    HAS_OPENPYXL = False
try:
    import pyodbc  # type: ignore

    HAS_PYODBC = True
except Exception:
    pyodbc = None  # type: ignore[assignment]
    HAS_PYODBC = False
import csv


class ImportExport(Frame):
    def __init__(self, parent, **kwargs):
        Frame.__init__(self, parent, **kwargs)
        self.parent = parent
        self.configure(bg="#000000")

        self.current_frame = None
        self.frames = {}

        # Create frames
        self.frames["import"] = ImportFrame(self, self)
        self.frames["export"] = ExportFrame(self, self)

        # Show initial frame (import page)
        self.show_frame("import")

    def show_frame(self, frame_name):
        if self.current_frame:
            self.current_frame.pack_forget()

        self.current_frame = self.frames[frame_name]
        self.current_frame.pack(fill="both", expand=True)


class ImportFrame(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller

        self.OUTPUT_PATH = Path(__file__).parent.parent.parent.parent
        self.ASSETS_PATH = self.OUTPUT_PATH / Path(r"assets\ine_assets\Import_assets")

        self.configure(bg="#000000")

        # Initialize variables for import functionality
        self.import_queue = []
        self.drag_drop_visible = True
        self.file_path_entry = None
        self.dragdrop_image_id = None

        # File paths for system files
        # Use canonical single database file for both items and employee lists
        self.system_paths = {
            "JJCIMS.accdb": Path(get_db_path()),
            "Employee List.accdb": Path(get_db_path()),  # mapped to canonical DB
        }

        # Strict accepted file names (case-insensitive). Maps lowercase name -> system_paths key
        self.accepted_map = {
            "jjcims.accdb": "JJCIMS.accdb",
            "employee list.accdb": "Employee List.accdb",
        }
        self.accepted_files = set(self.accepted_map.keys())

        # Setup UI
        self.setup_ui()

    def relative_to_assets(self, path: str) -> Path:
        asset_path = self.ASSETS_PATH / Path(path)
        if not asset_path.exists():
            print(f"Warning: Asset not found: {asset_path}")
            # Create a fallback or handle missing asset gracefully
        return asset_path

    def canonicalize(self, file_name: str):
        """Return the canonical system_paths key for an accepted file name, or None."""
        return self.accepted_map.get(file_name.lower())

    def validate_file(self, file_path):
        """Validate if the file is what it claims to be"""
        try:
            file_name = os.path.basename(file_path)
            canonical_key = self.canonicalize(file_name)
            if not canonical_key:
                return False, f"File {file_name} is not an accepted file type."

            # Validate based on type
            if canonical_key.endswith(".accdb"):
                return self.validate_access_db(file_path, canonical_key)

            return False, "Unknown file type."

        except Exception as e:
            return False, f"Error validating file: {str(e)}"

    def validate_access_db(self, file_path, file_name):
        """Validate Access database files"""
        try:
            if not HAS_PYODBC or pyodbc is None:  # type: ignore[truthy-bool]
                return False, "Access DB validation requires 'pyodbc' to be installed."
            conn_str = (
                f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={file_path};"
            )
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()

            if file_name == "JJCIMS.accdb":
                # Check for required tables in JJCIMS database
                required_tables = ["ITEMSDB"]  # Add more tables as needed
                tables = [row.table_name for row in cursor.tables(tableType="TABLE")]
                for table in required_tables:
                    if table not in tables:
                        conn.close()
                        return (
                            False,
                            f"Required table '{table}' not found in JJCIMS database.",
                        )

            elif file_name == "Employee List.accdb":
                # Check for required tables in Employee List database (Emp_list)
                required_tables = ["Emp_list"]  # Matches project schema
                tables = [row.table_name for row in cursor.tables(tableType="TABLE")]
                for table in required_tables:
                    if table not in tables:
                        conn.close()
                        return (
                            False,
                            f"Required table '{table}' not found in Employee List database.",
                        )

            conn.close()
            return True, "Valid Access database."

        except Exception as e:
            return False, f"Invalid Access database: {str(e)}"

    def browse_file(self):
        """Open file dialog to browse and queue multiple import files"""
        self._select_files_and_queue()

    def _select_files_and_queue(self):
        """Pick multiple files and add only allowed ones to the queue."""
        filetypes = [
            ("Access Database", "*.accdb"),
            ("All Files", "*.*"),
        ]

        try:
            file_paths = filedialog.askopenfilenames(
                title="Select files to import",
                filetypes=filetypes,
                initialdir=os.path.expanduser("~"),
            )
        except Exception:
            # Fallback pattern for some Tk variants
            file_paths = filedialog.askopenfilenames(
                title="Select files to import",
                filetypes=[("Access Database", "*.accdb")],
                initialdir=os.path.expanduser("~"),
            )

        if file_paths:
            added_count = 0
            error_messages = []

            for file_path in file_paths:
                success, message = self.add_to_import_queue(file_path)
                if success:
                    added_count += 1
                else:
                    error_messages.append(f"• {os.path.basename(file_path)}: {message}")

            # Update entry field for UX (show first file or count)
            if getattr(self, "file_path_entry", None) is not None:
                self.file_path_entry.delete(0, tk.END)
                if len(file_paths) == 1:
                    self.file_path_entry.insert(0, file_paths[0])
                else:
                    self.file_path_entry.insert(0, f"{len(file_paths)} files selected")

            # Show results
            if added_count > 0:
                result_msg = f"Added {added_count} file(s) to import queue."
                if error_messages:
                    result_msg += "\n\nErrors:\n" + "\n".join(error_messages)
                    messagebox.showwarning("Files Added with Errors", result_msg)
                else:
                    messagebox.showinfo("Files Added", result_msg)
            else:
                if error_messages:
                    error_msg = "No files were added due to errors:\n" + "\n".join(
                        error_messages
                    )
                    messagebox.showerror("Import Errors", error_msg)

    def add_to_import_queue(self, file_path):
        """Add file to import queue after validation"""
        is_valid, message = self.validate_file(file_path)

        if is_valid:
            file_name = os.path.basename(file_path)
            canon = self.canonicalize(file_name)
            # Check if file already in queue (by canonical name)
            if not any(item.get("canon") == canon for item in self.import_queue):
                self.import_queue.append(
                    {
                        "name": file_name,
                        "canon": canon,
                        "path": file_path,
                        "status": "Pending",
                    }
                )
                self.update_import_queue_display()
                return True, f"Added {file_name} to import queue."
            else:
                return False, f"{file_name} is already in the import queue."
        else:
            return False, message

    def update_import_queue_display(self):
        """Always show the import queue (drag/drop removed)."""
        self.show_import_queue()

    def hide_drag_drop_area(self):
        """Hide the drag and drop area"""
        try:
            if hasattr(self, "image_image_3") and hasattr(self, "canvas"):
                # Hide the drag and drop image
                items = self.canvas.find_all()
                for item in items:
                    if self.canvas.type(item) == "image":
                        # Check if this is the drag and drop image
                        coords = self.canvas.coords(item)
                        if len(coords) >= 2 and abs(coords[0] - 696.2652282714844) < 1:
                            self.canvas.itemconfig(item, state="hidden")
            self.drag_drop_visible = False
        except Exception as e:
            print(f"Error hiding drag drop area: {e}")

    def show_import_queue(self):
        """Show the import queue list"""
        # Create a frame for the import queue
        if not hasattr(self, "queue_frame"):
            self.queue_frame = Frame(self, bg="#191919", relief="solid", bd=1)
            self.queue_frame.place(x=400, y=380, width=600, height=250)

            # Queue title
            queue_title = tk.Label(
                self.queue_frame,
                text="Import Queue",
                bg="#191919",
                fg="#FFFFFF",
                font=("Inter", 16, "bold"),
            )
            queue_title.pack(pady=10)

            # Queue listbox
            self.queue_listbox = tk.Listbox(
                self.queue_frame,
                bg="#333333",
                fg="#FFFFFF",
                selectbackground="#800000",
                font=("Inter", 10),
                height=8,
            )
            self.queue_listbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))

            # Control buttons frame
            buttons_frame = Frame(self.queue_frame, bg="#191919")
            buttons_frame.pack(fill="x", padx=10, pady=(0, 10))

            # Remove selected button
            self.remove_btn = Button(
                buttons_frame,
                text="Remove Selected",
                command=self.remove_from_queue,
                bg="#800000",
                fg="white",
                font=("Inter", 10),
                relief="flat",
            )
            self.remove_btn.pack(side="left", padx=(0, 5))

            # Clear all button
            self.clear_btn = Button(
                buttons_frame,
                text="Clear All",
                command=self.clear_queue,
                bg="#600000",
                fg="white",
                font=("Inter", 10),
                relief="flat",
            )
            self.clear_btn.pack(side="left")

        # Update queue display
        self.refresh_queue_display()
        self.queue_frame.tkraise()

    def refresh_queue_display(self):
        """Refresh the import queue display"""
        if hasattr(self, "queue_listbox"):
            self.queue_listbox.delete(0, tk.END)
            for item in self.import_queue:
                status_text = f"{item['name']} - {item['status']}"
                self.queue_listbox.insert(tk.END, status_text)

    def remove_from_queue(self):
        """Remove selected item from import queue"""
        if hasattr(self, "queue_listbox"):
            selection = self.queue_listbox.curselection()
            if selection:
                index = selection[0]
                if 0 <= index < len(self.import_queue):
                    self.import_queue.pop(index)
                    self.refresh_queue_display()
                    self.update_import_queue_display()

    def clear_queue(self):
        """Clear all items from import queue"""
        self.import_queue.clear()
        self.refresh_queue_display()
        self.update_import_queue_display()

    def show_drag_drop_area(self):
        """Deprecated: Drag-and-drop area removed. Always show queue."""
        self.show_import_queue()

    def import_single_file(self):
        """Import single file from entry path"""
        if getattr(self, "file_path_entry", None) is None:
            messagebox.showwarning("No File", "Please select a file to import.")
            return
        file_path = self.file_path_entry.get().strip()
        if not file_path:
            messagebox.showwarning("No File", "Please select a file to import.")
            return
        if not os.path.exists(file_path):
            messagebox.showerror("File Not Found", "The selected file does not exist.")
            return
        success, message = self.add_to_import_queue(file_path)
        if success:
            messagebox.showinfo("File Added", message)
        else:
            messagebox.showerror("Validation Error", message)

    def process_imports(self):
        """Process all files in the import queue"""
        if not self.import_queue:
            messagebox.showwarning("No Files", "No files in import queue.")
            return

        success_count = 0
        error_count = 0

        for item in self.import_queue:
            try:
                item["status"] = "Processing..."
                self.refresh_queue_display()
                self.update()  # Force UI update

                success = self.import_file(item["path"], item["name"])

                if success:
                    item["status"] = "Success"
                    success_count += 1
                else:
                    item["status"] = "Failed"
                    error_count += 1

                self.refresh_queue_display()
                self.update()  # Force UI update

            except Exception as e:
                item["status"] = f"Error: {str(e)[:50]}"
                error_count += 1
                self.refresh_queue_display()

        # Show completion message
        message = f"Import completed!\nSuccess: {success_count}\nErrors: {error_count}"
        if error_count > 0:
            messagebox.showwarning("Import Completed with Errors", message)
        else:
            messagebox.showinfo("Import Completed", message)

    def import_file(self, source_path, file_name):
        """Import a single file to its destination"""
        try:
            canonical_key = self.canonicalize(file_name)
            if not canonical_key or canonical_key not in self.system_paths:
                return False

            destination_path = self.system_paths[canonical_key]

            # Create backup of existing file
            if destination_path.exists():
                backup_path = destination_path.with_suffix(
                    f".backup{destination_path.suffix}"
                )
                shutil.copy2(str(destination_path), str(backup_path))

            # Create destination directory if it doesn't exist
            destination_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy file to destination
            shutil.copy2(source_path, str(destination_path))

            return True

        except Exception as e:
            print(f"Error importing {file_name}: {str(e)}")
            return False

    def setup_ui(self):
        """Setup the user interface elements"""
        self.canvas = Canvas(
            self,
            bg="#000000",
            height=841,
            width=1400,
            bd=0,
            highlightthickness=0,
            relief="ridge",
        )

        self.canvas.pack(fill="both", expand=True)

        # Import Page UI Elements
        try:
            image_image_1 = PhotoImage(file=self.relative_to_assets("image_1.png"))
            self.canvas.create_image(699.0, 450.0, image=image_image_1)
            self.image_image_1 = image_image_1  # Keep reference
        except Exception as e:
            print(f"Error loading image_1.png: {e}")

        try:
            button_image_1 = PhotoImage(file=self.relative_to_assets("button_1.png"))
            button_1 = Button(
                self,
                image=button_image_1,
                borderwidth=0,
                highlightthickness=0,
                background="#000000",
                activebackground="#000000",
                cursor="hand2",
                command=lambda: self.controller.show_frame("export"),
                relief="flat",
            )
            button_1.place(
                x=374.6312561035156,
                y=77.25743103027344,
                width=198.3143768310547,
                height=59.241085052490234,
            )
            self.button_image_1 = button_image_1  # Keep reference
        except Exception as e:
            print(f"Error loading button_1.png: {e}")
            # Create fallback button
            button_1 = Button(
                self,
                text="Export",
                borderwidth=0,
                highlightthickness=0,
                background="#800000",
                activebackground="#600000",
                fg="white",
                cursor="hand2",
                command=lambda: self.controller.show_frame("export"),
                relief="flat",
            )
            button_1.place(
                x=374.6312561035156,
                y=77.25743103027344,
                width=198.3143768310547,
                height=59.241085052490234,
            )

        try:
            image_image_2 = PhotoImage(file=self.relative_to_assets("image_2.png"))
            self.canvas.create_image(274.31687927246094, 104.0, image=image_image_2)
            self.image_image_2 = image_image_2  # Keep reference
        except Exception as e:
            print(f"Error loading image_2.png: {e}")

        # image_3 removed: drag-and-drop area replaced by import queue

        try:
            button_image_2 = PhotoImage(file=self.relative_to_assets("button_2.png"))
            button_2 = Button(
                self,
                image=button_image_2,
                borderwidth=0,
                highlightthickness=0,
                bg="#191919",
                activebackground="#191919",
                cursor="hand2",
                activeforeground="#191919",
                command=self.handle_import,
                relief="flat",
            )
            button_2.place(
                x=230.38648986816406,
                y=665.73583984375,
                width=936.7872314453125,
                height=55.32703399658203,
            )
            self.button_image_2 = button_image_2  # Keep reference
        except Exception as e:
            print(f"Error loading button_2.png: {e}")
            # Create fallback button
            button_2 = Button(
                self,
                text="IMPORT",
                borderwidth=0,
                highlightthickness=0,
                bg="#800000",
                activebackground="#600000",
                fg="white",
                font=("Inter", 16, "bold"),
                cursor="hand2",
                command=self.handle_import,
                relief="flat",
            )
            button_2.place(
                x=230.38648986816406,
                y=665.73583984375,
                width=936.7872314453125,
                height=55.32703399658203,
            )

        try:
            entry_image_1 = PhotoImage(file=self.relative_to_assets("entry_1.png"))
            self.canvas.create_image(663.0, 306.0, image=entry_image_1)
            self.entry_image_1 = entry_image_1  # Keep reference
        except Exception as e:
            print(f"Error loading entry_1.png: {e}")

        entry_1 = Entry(
            self,
            bd=0,
            bg="#191919",
            fg="#ffffff",
            cursor="xterm",
            font=("Roboto", 23),
            insertbackground="#ffffff",
            highlightthickness=0,
        )
        entry_1.place(x=248.0, y=275.0, width=830.0, height=60.0)

        # Store reference to entry for file path display
        self.file_path_entry = entry_1

        try:
            button_image_3 = PhotoImage(file=self.relative_to_assets("button_3.png"))
            button_3 = Button(
                self,
                image=button_image_3,
                borderwidth=0,
                highlightthickness=0,
                bg="#191919",
                activebackground="#191919",
                cursor="hand2",
                activeforeground="#191919",
                command=self.browse_file,
                relief="flat",
            )
            button_3.place(x=1096.0, y=275.0, width=60.0, height=60.0)
            self.button_image_3 = button_image_3  # Keep reference
        except Exception as e:
            print(f"Error loading button_3.png: {e}")
            # Create fallback button
            button_3 = Button(
                self,
                text="...",
                borderwidth=0,
                highlightthickness=0,
                bg="#800000",
                activebackground="#600000",
                fg="white",
                font=("Inter", 12, "bold"),
                cursor="hand2",
                command=self.browse_file,
                relief="flat",
            )
            button_3.place(x=1096.0, y=275.0, width=60.0, height=60.0)

        self.canvas.create_text(
            244.0,
            219.0,
            anchor="nw",
            text="File path:",
            fill="#FFFFFF",
            font=("Inter", 24 * -1),
        )
        self.canvas.create_text(
            523.0,
            158.0,
            anchor="nw",
            text="IMPORT FILES",
            fill="#800000",
            font=("Inter BlackItalic", 40 * -1),
        )

        # Replace drag-and-drop area with the queue shown by default
        self.show_import_queue()

    def handle_import(self):
        """Handle import button click"""
        if self.import_queue:
            # Process queue if there are items
            result = messagebox.askyesno(
                "Process Import Queue",
                f"Process {len(self.import_queue)} file(s) in the import queue?",
            )
            if result:
                self.process_imports()
        else:
            # Import single file from entry
            self.import_single_file()

    def on_drag_drop_click(self, event):
        """Open file picker to add multiple files to the queue."""
        self._select_files_and_queue()

    # Native DnD handler (when tkinterdnd2 is available)
    def on_native_drop(self, event):
        # Drag-and-drop removed; ignore
        return

    def _parse_dnd_files(self, data: str):
        # Drag-and-drop removed; keep function for compatibility if referenced
        return []

    def setup_drag_drop(self):
        """Drag-and-drop disabled permanently. Use click-to-select."""
        pass


class ExportFrame(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self.controller = controller

        OUTPUT_PATH = Path(__file__).parent.parent.parent.parent
        ASSETS_PATH = OUTPUT_PATH / Path(r"assets\ine_assets\Export_assets")

        def relative_to_assets(path: str) -> Path:
            asset_path = ASSETS_PATH / Path(path)
            if not asset_path.exists():
                print(f"Warning: Asset not found: {asset_path}")
                # Create a fallback or handle missing asset gracefully
            return asset_path

        self.configure(bg="#000000")
        self.export_dir = None  # target folder for exports

        # Variables for radio buttons and checkboxes
        self.export_format = IntVar(value=1)  # 1=Access, 2=Excel, 3=CSV
        self.items_db_var = BooleanVar(value=False)
        self.logs_var = BooleanVar(value=False)
        self.employee_var = BooleanVar(value=False)

        # Images for selected/unselected states
        self.checkbox_images = {}
        self.radio_images = {}

        def load_images():
            # Load checkbox images
            for i in range(5, 8):
                try:
                    self.checkbox_images[i] = {
                        "unchecked": PhotoImage(
                            file=relative_to_assets(f"image_{i}.png")
                        ),
                        "checked": PhotoImage(
                            file=relative_to_assets(f"image_{i}_selected.png")
                        ),
                    }
                except Exception as e:
                    print(f"Error loading checkbox images for {i}: {e}")
                    # Create fallback checkbox images (simple rectangles)
                    self.checkbox_images[i] = {"unchecked": None, "checked": None}
            # Load radio button images
            for i in range(2, 5):
                try:
                    self.radio_images[i] = {
                        "unselected": PhotoImage(
                            file=relative_to_assets(f"image_{i}.png")
                        ),
                        "selected": PhotoImage(
                            file=relative_to_assets(f"image_{i}_selected.png")
                        ),
                    }
                except Exception as e:
                    print(f"Error loading radio button images for {i}: {e}")
                    # Create fallback radio button images
                    self.radio_images[i] = {"unselected": None, "selected": None}

        self.canvas = Canvas(
            self,
            bg="#000000",
            height=841,
            width=1400,
            bd=0,
            highlightthickness=0,
            relief="ridge",
        )

        self.canvas.pack(fill="both", expand=True)

        def update_checkbox_image(image_id, checkbox_num, var):
            state = "checked" if var.get() else "unchecked"
            if self.checkbox_images[checkbox_num][state]:
                self.canvas.itemconfig(
                    image_id, image=self.checkbox_images[checkbox_num][state]
                )

        # Load images
        load_images()

        # Create the rest of the Export UI
        self.canvas.create_rectangle(
            165.0, 136.0, 1234.0, 765.0, fill="#1A1A1A", outline=""
        )

        # Add image_1
        try:
            image_image_1 = PhotoImage(file=relative_to_assets("image_1.png"))
            self.canvas.create_image(475.5423583984375, 104.0, image=image_image_1)
            self.image_image_1 = image_image_1  # Keep reference
        except Exception as e:
            print(f"Error loading image_1.png: {e}")

        # Add image_8 (positioned similar to image_1 in import page)
        try:
            image_image_8 = PhotoImage(file=relative_to_assets("image_8.png"))
            self.canvas.create_image(699.0, 450.0, image=image_image_8)
            self.image_image_8 = image_image_8  # Keep reference
        except Exception as e:
            print(f"Error loading image_8.png: {e}")

        try:
            button_image_1 = PhotoImage(file=relative_to_assets("button_1.png"))
            button_1 = Button(
                self,
                image=button_image_1,
                borderwidth=0,
                highlightthickness=0,
                background="#000000",
                activebackground="#000000",
                cursor="hand2",
                command=lambda: controller.show_frame("import"),
                relief="flat",
            )
            button_1.place(
                x=176.31881713867188,
                y=77.2576904296875,
                width=198.34820556640625,
                height=59.25119400024414,
            )
            self.button_image_1 = button_image_1
        except Exception as e:
            print(f"Error loading button_1.png: {e}")
            # Create fallback button
            button_1 = Button(
                self,
                text="Import",
                borderwidth=0,
                highlightthickness=0,
                background="#800000",
                activebackground="#600000",
                fg="white",
                cursor="hand2",
                command=lambda: controller.show_frame("import"),
                relief="flat",
            )
            button_1.place(
                x=176.31881713867188,
                y=77.2576904296875,
                width=198.34820556640625,
                height=59.25119400024414,
            )

        # Entry for file path
        try:
            entry_image_1 = PhotoImage(file=relative_to_assets("entry_1.png"))
            self.canvas.create_image(663.0, 469.5, image=entry_image_1)
            self.entry_image_1 = entry_image_1
        except Exception as e:
            print(f"Error loading entry_1.png: {e}")

        # Target folder entry (for export destination)
        entry_1 = Entry(
            self,
            bd=0,
            bg="#191919",
            fg="#ffffff",
            cursor="xterm",
            insertbackground="#ffffff",
            font=("Inter", 24),
            highlightthickness=0,
        )
        entry_1.place(x=248.0, y=438.0, width=830.0, height=61.0)
        self.target_entry = entry_1

        # Browse button
        try:
            button_image_3 = PhotoImage(file=relative_to_assets("button_3.png"))
            button_3 = Button(
                self,
                image=button_image_3,
                borderwidth=0,
                highlightthickness=0,
                background="#191919",
                activebackground="#191919",
                cursor="hand2",
                command=self._choose_export_folder,
                relief="flat",
            )
            button_3.place(x=1096.0, y=438.0, width=60.0, height=61.0)
            # Keep a reference to the PhotoImage so it doesn't get garbage-collected
            self.button_image_3 = button_image_3
            # Also attach to the widget as a backup reference
            button_3.image = button_image_3
        except Exception as e:
            print(f"Error loading button_3.png: {e}")
            # Create fallback button
            button_3 = Button(
                self,
                text="...",
                borderwidth=0,
                highlightthickness=0,
                background="#800000",
                activebackground="#600000",
                fg="white",
                font=("Inter", 12, "bold"),
                cursor="hand2",
                command=self._choose_export_folder,
                relief="flat",
            )
            button_3.place(x=1096.0, y=438.0, width=60.0, height=61.0)

        # Export button
        try:
            button_image_2 = PhotoImage(file=relative_to_assets("button_2.png"))
            button_2 = Button(
                self,
                image=button_image_2,
                borderwidth=0,
                highlightthickness=0,
                background="#191919",
                activebackground="#191919",
                cursor="hand2",
                command=self._do_export,
                relief="flat",
            )
            button_2.place(
                x=230.39764404296875,
                y=665.83642578125,
                width=936.9470825195312,
                height=55.33647155761719,
            )
            self.button_image_2 = button_image_2
        except Exception as e:
            print(f"Error loading button_2.png: {e}")
            # Create fallback button
            button_2 = Button(
                self,
                text="EXPORT",
                borderwidth=0,
                highlightthickness=0,
                background="#800000",
                activebackground="#600000",
                fg="white",
                font=("Inter", 16, "bold"),
                cursor="hand2",
                command=self._do_export,
                relief="flat",
            )
            button_2.place(
                x=230.39764404296875,
                y=665.83642578125,
                width=936.9470825195312,
                height=55.33647155761719,
            )

        # Labels
        self.canvas.create_text(
            242.0,
            383.0,
            anchor="nw",
            text="File path:",
            fill="#FFFFFF",
            font=("Inter", 24 * -1),
        )

        self.canvas.create_text(
            242.0,
            241.0,
            anchor="nw",
            text="Files to export:",
            fill="#FFFFFF",
            font=("Inter", 24 * -1),
        )

        self.canvas.create_text(
            242.0,
            522.0,
            anchor="nw",
            text="Export Format:",
            fill="#FFFFFF",
            font=("Inter", 24 * -1),
        )

        self.canvas.create_text(
            520.0,
            158.0,
            anchor="nw",
            text="EXPORT FILES",
            fill="#800000",
            font=("Inter BlackItalic", 40 * -1),
        )

        # Radio button labels
        self.canvas.create_text(
            341.0,
            578.0,
            anchor="nw",
            text="Access file",
            fill="#FFFFFF",
            font=("Inter Medium", 20 * -1),
        )

        self.canvas.create_text(
            671.0,
            578.0,
            anchor="nw",
            text="Excel File",
            fill="#FFFFFF",
            font=("Inter Medium", 20 * -1),
        )

        self.canvas.create_text(
            981.0,
            578.0,
            anchor="nw",
            text="CSV file",
            fill="#FFFFFF",
            font=("Inter Medium", 20 * -1),
        )

        # Checkbox labels
        self.canvas.create_text(
            278.0,
            290.0,
            anchor="nw",
            text="Items database",
            fill="#FFFFFF",
            font=("Inter Medium", 20 * -1),
        )

        self.canvas.create_text(
            664.0,
            290.0,
            anchor="nw",
            text="Logs files",
            fill="#FFFFFF",
            font=("Inter Medium", 20 * -1),
        )

        self.canvas.create_text(
            967.0,
            290.0,
            anchor="nw",
            text="Employee list",
            fill="#FFFFFF",
            font=("Inter Medium", 20 * -1),
        )

        def toggle_checkbox(var, image_id, checkbox_num):
            var.set(not var.get())
            update_checkbox_image(image_id, checkbox_num, var)

        # Create radio buttons (with fallbacks for missing images)
        if self.radio_images[2]["selected"]:
            self.image_2 = self.canvas.create_image(
                323.0,
                594.0,
                image=self.radio_images[2]["selected"],  # Start with Access selected
            )
        else:
            # Fallback: create a simple circle
            self.image_2 = self.canvas.create_oval(
                318, 589, 328, 599, fill="#800000", outline="#FFFFFF"
            )

        if self.radio_images[3]["unselected"]:
            self.image_3 = self.canvas.create_image(
                653.0, 594.0, image=self.radio_images[3]["unselected"]
            )
        else:
            # Fallback: create a simple circle
            self.image_3 = self.canvas.create_oval(
                648, 589, 658, 599, fill="#191919", outline="#FFFFFF"
            )

        if self.radio_images[4]["unselected"]:
            self.image_4 = self.canvas.create_image(
                964.0, 594.0, image=self.radio_images[4]["unselected"]
            )
        else:
            # Fallback: create a simple circle
            self.image_4 = self.canvas.create_oval(
                959, 589, 969, 599, fill="#191919", outline="#FFFFFF"
            )

        def update_radio_images():
            selected = self.export_format.get()
            for i, img_id in [(2, self.image_2), (3, self.image_3), (4, self.image_4)]:
                if (
                    self.radio_images[i]["selected"]
                    and self.radio_images[i]["unselected"]
                ):
                    state = "selected" if selected == (i - 1) else "unselected"
                    self.canvas.itemconfig(img_id, image=self.radio_images[i][state])

        self.canvas.tag_bind(
            self.image_2,
            "<Button-1>",
            lambda e: (self.export_format.set(1), update_radio_images()),
        )

        self.canvas.tag_bind(
            self.image_3,
            "<Button-1>",
            lambda e: (self.export_format.set(2), update_radio_images()),
        )

        self.canvas.tag_bind(
            self.image_4,
            "<Button-1>",
            lambda e: (self.export_format.set(3), update_radio_images()),
        )

        # Create checkboxes (with fallbacks for missing images)
        if self.checkbox_images[5]["unchecked"]:
            self.image_5 = self.canvas.create_image(
                255.0, 308.0, image=self.checkbox_images[5]["unchecked"]
            )
        else:
            # Fallback: create a simple rectangle
            self.image_5 = self.canvas.create_rectangle(
                250, 303, 260, 313, fill="#191919", outline="#FFFFFF"
            )

        self.canvas.tag_bind(
            self.image_5,
            "<Button-1>",
            lambda e: toggle_checkbox(self.items_db_var, self.image_5, 5),
        )

        if self.checkbox_images[6]["unchecked"]:
            self.image_6 = self.canvas.create_image(
                640.0, 308.0, image=self.checkbox_images[6]["unchecked"]
            )
        else:
            # Fallback: create a simple rectangle
            self.image_6 = self.canvas.create_rectangle(
                635, 303, 645, 313, fill="#191919", outline="#FFFFFF"
            )

        self.canvas.tag_bind(
            self.image_6,
            "<Button-1>",
            lambda e: toggle_checkbox(self.logs_var, self.image_6, 6),
        )

        if self.checkbox_images[7]["unchecked"]:
            self.image_7 = self.canvas.create_image(
                944.0, 308.0, image=self.checkbox_images[7]["unchecked"]
            )
        else:
            # Fallback: create a simple rectangle
            self.image_7 = self.canvas.create_rectangle(
                939, 303, 949, 313, fill="#191919", outline="#FFFFFF"
            )

        self.canvas.tag_bind(
            self.image_7,
            "<Button-1>",
            lambda e: toggle_checkbox(self.employee_var, self.image_7, 7),
        )

    # ---------------- Export logic wiring ----------------
    def _choose_export_folder(self):
        folder = filedialog.askdirectory(
            title="Select export destination folder", initialdir=os.path.expanduser("~")
        )
        if folder:
            self.export_dir = folder
            self.target_entry.delete(0, tk.END)
            self.target_entry.insert(0, folder)

    def _do_export(self):
        # Validate destination
        dest = self.target_entry.get().strip() or self.export_dir
        if not dest:
            messagebox.showwarning("No Destination", "Please choose an export folder.")
            return
        if not os.path.isdir(dest):
            try:
                os.makedirs(dest, exist_ok=True)
            except Exception as e:
                messagebox.showerror(
                    "Destination Error", f"Cannot create destination folder:\n{e}"
                )
                return

        targets = {
            "items_db": self.items_db_var.get(),
            "logs": self.logs_var.get(),
            "employee": self.employee_var.get(),
        }
        if not any(targets.values()):
            messagebox.showwarning(
                "No Selection", "Select at least one file to export."
            )
            return

        fmt = self.export_format.get()  # 1=Access,2=Excel,3=CSV
        src_db = Path(get_db_path())
        # Employee list is stored in the canonical DB
        src_emp = src_db

        exported = []
        errors = []

        def safe_copy(src: Path, dst_name: str):
            try:
                shutil.copy2(str(src), os.path.join(dest, dst_name))
                exported.append(dst_name)
            except Exception as e:
                errors.append(f"{dst_name}: {e}")

        try:
            if fmt == 1:  # Access
                if targets["items_db"]:
                    if src_db.exists():
                        safe_copy(src_db, "JJCIMS.accdb")
                    else:
                        errors.append("JJCIMS.accdb not found")
                if targets["employee"]:
                    if src_emp.exists():
                        # Exporting the employee list as a copy of the canonical DB
                        safe_copy(src_emp, "Employee List.accdb")
                    else:
                        errors.append("Employee List.accdb (canonical DB) not found")
                if targets["logs"]:
                    errors.append(
                        "Exporting logs to Access format is not supported. Use Excel or CSV format."
                    )

            elif fmt == 2:  # Excel
                if targets["items_db"]:
                    try:
                        self._export_table_to_excel(
                            src_db, "ITEMSDB", os.path.join(dest, "ITEMSDB.xlsx")
                        )
                        exported.append("ITEMSDB.xlsx")
                    except Exception as e:
                        errors.append(f"ITEMSDB.xlsx: {e}")
                if targets["employee"]:
                    try:
                        self._export_table_to_excel(
                            src_emp,
                            "Emp_list",
                            os.path.join(dest, "Employee_List.xlsx"),
                        )
                        exported.append("Employee_List.xlsx")
                    except Exception as e:
                        errors.append(f"Employee_List.xlsx: {e}")
                if targets["logs"]:
                    try:
                        # Export admin logs from database
                        self._export_table_to_excel(
                            src_db, "adm_logs", os.path.join(dest, "admin_logs.xlsx")
                        )
                        exported.append("admin_logs.xlsx")
                        # Export employee logs from database
                        self._export_table_to_excel(
                            src_db, "emp_logs", os.path.join(dest, "employee_logs.xlsx")
                        )
                        exported.append("employee_logs.xlsx")
                    except Exception as e:
                        errors.append(f"logs export: {e}")

            elif fmt == 3:  # CSV
                if targets["items_db"]:
                    try:
                        self._export_table_to_csv(
                            src_db, "ITEMSDB", os.path.join(dest, "ITEMSDB.csv")
                        )
                        exported.append("ITEMSDB.csv")
                    except Exception as e:
                        errors.append(f"ITEMSDB.csv: {e}")
                if targets["employee"]:
                    try:
                        self._export_table_to_csv(
                            src_emp, "Emp_list", os.path.join(dest, "Employee_List.csv")
                        )
                        exported.append("Employee_List.csv")
                    except Exception as e:
                        errors.append(f"Employee_List.csv: {e}")
                if targets["logs"]:
                    try:
                        # Export admin logs from database
                        self._export_table_to_csv(
                            src_db, "adm_logs", os.path.join(dest, "admin_logs.csv")
                        )
                        exported.append("admin_logs.csv")
                        # Export employee logs from database
                        self._export_table_to_csv(
                            src_db, "emp_logs", os.path.join(dest, "employee_logs.csv")
                        )
                        exported.append("employee_logs.csv")
                    except Exception as e:
                        errors.append(f"logs->CSV: {e}")

        except Exception as e:
            errors.append(str(e))

        # Summary
        if exported and not errors:
            messagebox.showinfo("Export Completed", "Exported: " + ", ".join(exported))
        elif exported and errors:
            messagebox.showwarning(
                "Export Completed with Errors",
                f"Exported: {', '.join(exported)}\nErrors:\n- " + "\n- ".join(errors),
            )
        else:
            messagebox.showerror(
                "Export Failed", "\n".join(errors) if errors else "Nothing exported."
            )

    def _export_table_to_csv(self, accdb_path: Path, table: str, csv_path: str):
        if not HAS_PYODBC or pyodbc is None:  # type: ignore[truthy-bool]
            raise RuntimeError(
                "CSV export from Access requires 'pyodbc' to be installed."
            )
        conn_str = (
            f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={accdb_path};"
        )
        conn = pyodbc.connect(conn_str)
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM [{table}]")
        columns = [c[0] for c in cur.description]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            for row in cur.fetchall():
                writer.writerow(list(row))
        cur.close()
        conn.close()

    def _export_table_to_excel(self, accdb_path: Path, table: str, xlsx_path: str):
        if not HAS_PYODBC or pyodbc is None:  # type: ignore[truthy-bool]
            raise RuntimeError(
                "Excel export from Access requires 'pyodbc' to be installed."
            )
        if not HAS_OPENPYXL or openpyxl is None:  # type: ignore[truthy-bool]
            raise RuntimeError("Excel export requires 'openpyxl' to be installed.")
        conn_str = (
            f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={accdb_path};"
        )
        conn = pyodbc.connect(conn_str)
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM [{table}]")
        columns = [c[0] for c in cur.description]
        rows = cur.fetchall()
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = table
        ws.append(columns)
        for r in rows:
            ws.append(list(r))
        wb.save(xlsx_path)
        cur.close()
        conn.close()


def create_import_export_frame(parent):
    """Factory function to create ImportExport frame for Admin Settings"""
    return ImportExport(parent)


if __name__ == "__main__":
    root = Tk()
    root.geometry("1400x841")
    root.configure(bg="#000000")
    root.resizable(False, False)
    app = ImportExport(root)
    app.pack(fill="both", expand=True)
    root.mainloop()
