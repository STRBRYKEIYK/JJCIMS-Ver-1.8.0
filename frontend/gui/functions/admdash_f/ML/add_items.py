import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageTk
from gui.functions.admdash_f.draft_manager import DraftManager
from backend.utils.window_icon import set_window_icon
from backend.database import get_connector, get_db_path  # centralized DB access
from backend.database import queries


def relative_to_assets(path: str) -> Path:
    ASSETS_PATH = (
        Path(__file__).parent.parent.parent.parent.parent / "assets" / "ani_assets"
    )
    return ASSETS_PATH / Path(path)


def add_item(root, db, load_data_callback, current_view=None, username="Admin"):
    """Open a form to add a new material to the JJCIMS database.

    Args:
        root: The parent window
        db: Database connection
        load_data_callback: Callback to refresh parent window data
        current_view: Current view state in parent window
        username: Current user's username
    """
    # Store references to prevent garbage collection
    add_item.windows = getattr(add_item, "windows", set())
    """Open a form to add a new material to the JJCIMS database."""
    # Check if window already exists
    for window in root.winfo_children():
        if isinstance(window, tk.Toplevel) and hasattr(window, "is_add_items_window"):
            window.lift()  # Bring to front
            window.focus_force()  # Give it focus
            return

    def add_material_to_jjcims(root, db, load_data_callback):
        """Open a form to add a new material to the JJCIMS database."""
        add_window = tk.Toplevel(root)
        add_window.is_add_items_window = True

        # Set consistent window icon
        set_window_icon(add_window)

        # Configure window style with withdraw/deiconify trick
        add_window.withdraw()  # Hide window temporarily
        add_window.overrideredirect(True)
        add_window.after(
            10, add_window.deiconify
        )  # Show window again to register with system

        add_window.attributes("-alpha", 1.0)
        add_window.wm_title("Add Items")

        # Initial window setup
        add_window.geometry("720x721")
        add_window.configure(bg="#000000")
        add_window.resizable(False, False)

        # Store window states
        add_window.minimized = False
        add_window._normal_geometry = None
        add_window.fullscreen = False

        # Ensure passed db is a centralized connector; if a raw path or None was passed (legacy callers), upgrade it
        if db is None or not hasattr(db, "connect"):
            try:
                db = get_connector(get_db_path())
            except Exception:
                # Fallback: attempt default get_connector without explicit path
                try:
                    db = get_connector()
                except Exception:
                    messagebox.showerror(
                        "Database Error", "Unable to initialize database connector."
                    )
                    add_window.destroy()
                    return

        # Helper for logging admin actions (reuse connection passed, create table if needed best-effort)
        def _log_admin_action(connection, username, details):
            try:
                cursor = connection.cursor()
                now = datetime.now()
                log_date = now.strftime("%Y-%m-%d")
                log_time = now.strftime("%H:%M:%S")
                try:
                    cursor.execute(
                        "INSERT INTO [adm_logs] ([DATE],[TIME],[USER],[DETAILS]) VALUES (?,?,?,?)",
                        (log_date, log_time, username, details),
                    )
                    connection.commit()
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
                            connection.commit()
                            cursor.execute(
                                "INSERT INTO [adm_logs] ([DATE],[TIME],[USER],[DETAILS]) VALUES (?,?,?,?)",
                                (log_date, log_time, username, details),
                            )
                            connection.commit()
                        except Exception as create_err:
                            print(
                                f"[LOGGING] Failed creating adm_logs table: {create_err}"
                            )
                    else:
                        print(f"[LOGGING] Insert failed: {insert_err}")
            except Exception as e:
                print(f"[LOGGING] Unexpected error: {e}")

        def minimize_window():
            if not add_window.minimized:
                # Store current state and minimize
                add_window._normal_geometry = add_window.geometry()
                add_window.withdraw()
                add_window.minimized = True
            else:
                # Restore window
                add_window.deiconify()
                if add_window._normal_geometry:
                    add_window.geometry(add_window._normal_geometry)
                add_window.minimized = False
                add_window.focus_force()

        # Function removed - replaced by easter egg in handle_button_click

        # Window state handlers
        def on_map(event=None):
            add_window.attributes("-alpha", 1.0)
            add_window.attributes("-topmost", True)
            add_window.after(100, lambda: add_window.attributes("-topmost", False))

        def on_unmap(event=None):
            add_window.attributes("-alpha", 0.95)

        add_window.bind("<Map>", on_map)
        add_window.bind("<Unmap>", on_unmap)
        add_window.bind("<FocusIn>", lambda e: add_window.attributes("-alpha", 1.0))
        add_window.bind("<FocusOut>", lambda e: add_window.attributes("-alpha", 0.95))

        # Make window draggable
        def start_move(event):
            if not add_window.minimized:
                add_window.x = event.x_root - add_window.winfo_x()
                add_window.y = event.y_root - add_window.winfo_y()

        def do_move(event):
            if not add_window.minimized and hasattr(add_window, "x"):
                x = event.x_root - add_window.x
                y = event.y_root - add_window.y
                add_window.geometry(f"+{x}+{y}")

        def stop_move(event):
            add_window.x = None
            add_window.y = None

        # Create maroon header frame for dragging
        header_frame = tk.Frame(add_window, bg="#800000", height=30, cursor="hand2")
        header_frame.place(x=0, y=0, width=720)

        # Bind dragging events to the maroon header
        header_frame.bind("<Button-1>", start_move)
        header_frame.bind("<B1-Motion>", do_move)
        header_frame.bind("<ButtonRelease-1>", stop_move)

        # Center the window
        window_width = 720
        window_height = 721
        screen_width = add_window.winfo_screenwidth()
        screen_height = add_window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        add_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Store all PhotoImage references
        add_window.image_references = {}

        canvas = tk.Canvas(
            add_window,
            bg="#000000",
            height=721,
            width=720,
            bd=0,
            highlightthickness=0,
            relief="ridge",
        )
        canvas.place(x=0, y=0)

        # Create rectangles
        canvas.create_rectangle(0.0, 1.0, 721.0, 73.0, fill="#800000", outline="")
        canvas.create_rectangle(2.0, 649.0, 723.0, 721.0, fill="#800000", outline="")
        canvas.create_rectangle(0.0, 19.0, 87.0, 47.0, fill="#834343", outline="")

        # Load header image first
        try:
            header_image = ImageTk.PhotoImage(
                Image.open(relative_to_assets("image_1.png"))
            )
            add_window.image_references["header"] = header_image
            canvas.create_image(360.0, 37.0, image=header_image)
        except Exception as e:
            print(f"Error loading header image: {e}")

        # Create buttons and store their images
        for i in range(1, 13):
            try:
                img = ImageTk.PhotoImage(
                    Image.open(relative_to_assets(f"button_{i}.png"))
                )
                add_window.image_references[f"button_{i}"] = img
            except Exception as e:
                print(f"Error loading button_{i}.png: {e}")
                continue

        def on_enter(e):
            e.widget["bg"] = e.widget.hover_color

        def on_leave(e):
            e.widget["bg"] = e.widget.normal_color

        # handle_button_click defined later with additional actions (close/minimize/fullscreen)
        # Custom window state handler
        def handle_window_state(event=None):
            state = add_window.state()
            if state == "iconic":  # Window is minimized
                add_window.minimized = True
            elif state == "normal":  # Window is restored
                add_window.minimized = False
                # Temporarily set topmost to ensure visibility
                add_window.attributes("-topmost", True)
                add_window.after(10, lambda: add_window.attributes("-topmost", False))

        # Bind window state events
        add_window.bind("<Map>", handle_window_state)  # Window shown/restored
        add_window.bind("<Unmap>", handle_window_state)  # Window hidden/minimized

        # Create bottom control buttons (4-6)
        bottom_buttons = [
            (539.0, 666.0, 27.0, "Cancel"),
            (583.0, 666.0, 26.0, "Draft"),
            (622.0, 666.0, 27.0, "Save"),
        ]
        for i, (x, y, w, text) in enumerate(bottom_buttons, 4):
            if f"button_{i}" in add_window.image_references:
                btn = tk.Button(
                    add_window,
                    image=add_window.image_references[f"button_{i}"],
                    borderwidth=0,
                    highlightthickness=0,
                    command=lambda x=i: handle_button_click(x),
                    relief="flat",
                    activebackground="#000000",
                )
                btn.place(x=x, y=y, width=w, height=26.0)
                canvas.create_text(
                    x + w / 2 - 10,
                    y + 26,
                    anchor="nw",
                    text=text,
                    fill="#FFFFFF",
                    font=("Inter Light", 10 * -1),
                )

        # Create LOAD DRAFT button
        if "button_7" in add_window.image_references:
            load_draft_btn = tk.Button(
                add_window,
                image=add_window.image_references["button_7"],
                borderwidth=0,
                bg="#800000",
                highlightthickness=0,
                command=lambda: handle_button_click(7),
                relief="flat",
                activebackground="#800000",
            )
            load_draft_btn.place(x=73.0, y=672.0, width=125.0, height=26.0)

        # Create entries with backgrounds
        entries = {}
        combo_vars = {}
        for i in range(1, 10):
            try:
                entry_img = ImageTk.PhotoImage(
                    Image.open(relative_to_assets(f"entry_{i}.png"))
                )
                add_window.image_references[f"entry_{i}"] = entry_img
            except Exception as e:
                print(f"Error loading entry_{i}.png: {e}")
                continue

            # Define entry positions and sizes
            entry_positions = {
                1: (83.0, 197.0, 555.0, 48.0),  # Item Name
                2: (83.0, 287.0, 159.0, 48.0),  # Brand
                3: (281.0, 287.0, 159.0, 48.0),  # Type
                4: (479.0, 287.0, 159.0, 48.0),  # Location
                5: (479.0, 376.0, 159.0, 48.0),  # Minimum Stock
                6: (281.0, 376.0, 159.0, 48.0),  # In
                7: (83.0, 376.0, 159.0, 48.0),  # Unit of Measure
                8: (83.0, 465.0, 159.0, 48.0),  # Price Per Unit
                9: (281.0, 465.0, 357.0, 48.0),  # Supplier
            }

            x, y, w, h = entry_positions[i]
            canvas.create_image(
                x + w / 2, y + h / 2, image=add_window.image_references[f"entry_{i}"]
            )

            # Create either Entry or Combobox based on field type
            if i in [2, 3, 4, 7, 9]:  # Brand, Type, Location, Unit of Measure, Supplier
                var = tk.StringVar()
                combo_vars[f"entry_{i}"] = var
                entry = ttk.Combobox(
                    add_window,
                    textvariable=var,
                    font=("Inter", 12),
                    style="Custom.TCombobox",
                    state="readonly",  # Make readonly by default
                )
                # Configure combo box style
                configure_combo_style()
                # Map entry numbers to database fields
                field_map = {
                    2: "BRAND",
                    3: "TYPE",
                    4: "LOCATION",
                    7: "UNIT OF MEASURE",
                    9: "SUPPLIER",
                }
                # Load combo box data
                entry["values"] = load_combo_data(db, field_map[i])
                # Bind the combo box selection
                entry.bind(
                    "<<ComboboxSelected>>",
                    lambda e, combo=entry, field=field_map[i]: handle_combo_selection(
                        e, combo, field, db, add_window
                    ),
                )
                # Make caret/cursor visible for Combobox (when editable)
                try:
                    entry.configure(insertbackground="#FFFFFF")
                except Exception:
                    pass
            else:
                entry = tk.Entry(
                    add_window,
                    bd=0,
                    bg="#000000",
                    fg="#FFFFFF",
                    highlightthickness=0,
                    font=("Inter", 12),
                    insertbackground="#FFFFFF",  # Cursor color
                )

            entry.place(x=x, y=y, width=w, height=h)
            entries[f"entry_{i}"] = entry

            # Add dynamic warning label (hidden by default)
            warning_label = tk.Label(add_window, text="", fg="red", bg="#000000")
            warning_label.place(x=x, y=y + h + 2)  # Place just below the entry
            entries[f"warning_{i}"] = warning_label

        # Create helper buttons (8-12)
        helper_positions = {
            8: (227.0, 299.0),  # Brand helper
            9: (425.0, 299.0),  # Type helper
            10: (623.0, 299.0),  # Location helper
            11: (227.0, 388.0),  # Unit helper
            12: (623.0, 477.0),  # Supplier helper
        }

        for i, (x, y) in helper_positions.items():
            if f"button_{i}" in add_window.image_references:
                btn = tk.Button(
                    add_window,
                    image=add_window.image_references[f"button_{i}"],
                    borderwidth=0,
                    highlightthickness=0,
                    command=lambda x=i: handle_button_click(x),
                    relief="flat",
                    activebackground="#000000",
                )
                btn.place(x=x, y=y, width=25.0, height=25.0)

        # Create labels with adjusted positions and proper font size
        labels_text = {
            "Item Name:": (70.0, 166.0),
            "Brand:": (70.0, 258.0),
            "Type:": (271.0, 258.0),
            "Location:": (469.0, 258.0),
            "Unit of Measure:": (73.0, 345.0),
            "In:": (271.0, 345.0),
            "Minimum Stock:": (469.0, 345.0),  # Adjusted y-coordinate
            "Price Per Unit:": (70.0, 433.0),
            "Supplier:": (271.0, 433.0),
        }

        for text, (x, y) in labels_text.items():
            label = tk.Label(
                add_window,
                text=text,
                fg="#FFFFFF",
                bg="#000000",
                font=("Inter Medium", 14),  # Proper font size
                anchor="w",
            )
            label.place(x=x, y=y)

        # Create draft manager instance
        draft_manager = DraftManager(add_window, db, entries, username)

        # Load and place the LOAD LAST DRAFT button
        button_7_image = ImageTk.PhotoImage(
            Image.open(relative_to_assets("button_7.png"))
        )
        button_7 = tk.Button(
            add_window,
            image=button_7_image,
            borderwidth=0,
            bg="#800000",
            highlightthickness=0,
            command=lambda: handle_button_click(7),
            relief="flat",
            activebackground="#800000",
        )
        button_7.image = button_7_image
        button_7.place(x=73.0, y=672.0, width=125.0, height=26.0)

        def handle_button_click(button_num):
            if button_num == 1:  # Red - Close
                add_window.withdraw()  # Hide window
                add_window.destroy()  # Then destroy it
            elif button_num == 2:  # Yellow - Minimize
                minimize_window()
            elif button_num == 3:  # Green - Toggle fullscreen

                def color_wave():
                    colors = [
                        "#800000",
                        "#A00000",
                        "#C00000",
                        "#E00000",
                        "#FF0000",
                        "#E00000",
                        "#C00000",
                        "#A00000",
                    ]

                    def wave_step(color_index=0):
                        if header_frame.winfo_exists():
                            header_frame.configure(bg=colors[color_index])
                            if color_index < len(colors) - 1:
                                add_window.after(90, wave_step, color_index + 1)
                            else:
                                add_window.after(
                                    400, lambda: header_frame.configure(bg="#800000")
                                )

                    wave_step()

                # Run the header color animation
                color_wave()
                # Toggle a pseudo-fullscreen (maximize / restore) since overrideredirect is enabled
                if not getattr(add_window, "fullscreen", False):
                    add_window._normal_geometry = add_window.geometry()
                    sw = add_window.winfo_screenwidth()
                    sh = add_window.winfo_screenheight()
                    add_window.geometry(f"{sw}x{sh}+0+0")
                    add_window.fullscreen = True
                else:
                    if (
                        hasattr(add_window, "_normal_geometry")
                        and add_window._normal_geometry
                    ):
                        add_window.geometry(add_window._normal_geometry)
                    add_window.fullscreen = False
            elif button_num == 4:  # Cancel
                add_window.withdraw()
                add_window.destroy()
            elif button_num == 5:  # Draft
                draft_manager.save_draft()
            elif button_num == 6:  # Save
                save_item()
            elif button_num == 7:  # Load Last Draft
                draft_manager.load_draft()
            elif button_num in [8, 9, 10, 11, 12]:  # Helper buttons
                handle_helper_button(button_num, entries, db, add_window)

        def save_item():
            # Get values from entries
            values = {
                "NAME": entries["entry_1"].get().strip(),
                "BRAND": entries["entry_2"].get().strip(),
                "TYPE": entries["entry_3"].get().strip(),
                "LOCATION": entries["entry_4"].get().strip(),
                "MIN STOCK": entries["entry_5"].get().strip(),
                "IN": entries["entry_6"].get().strip(),
                "UNIT OF MEASURE": entries["entry_7"].get().strip(),
                "PRICE PER UNIT": entries["entry_8"].get().strip(),
                "SUPPLIER": entries["entry_9"].get().strip(),
            }

            # Validate fields
            if not all(values.values()):
                # Create custom error dialog
                error_dialog = tk.Toplevel(add_window)
                error_dialog.overrideredirect(True)
                error_dialog.withdraw()
                error_dialog.after(10, error_dialog.deiconify)
                error_dialog.attributes("-alpha", 1.0)
                error_dialog.configure(bg="#000000")
                error_dialog.resizable(False, False)

                # Create custom title bar
                title_bar = tk.Frame(error_dialog, bg="#800000", height=30)
                title_bar.pack(fill=tk.X)

                title_label = tk.Label(
                    title_bar,
                    text="Error",
                    bg="#800000",
                    fg="white",
                    font=("Inter", 10),
                )
                title_label.pack(side=tk.LEFT, padx=10, pady=5)

                # Add window dragging
                def start_move(event):
                    error_dialog.x = event.x_root - error_dialog.winfo_x()
                    error_dialog.y = event.y_root - error_dialog.winfo_y()

                def do_move(event):
                    if hasattr(error_dialog, "x"):
                        x = event.x_root - error_dialog.x
                        y = event.y_root - error_dialog.y
                        error_dialog.geometry(f"+{x}+{y}")

                title_bar.bind("<Button-1>", start_move)
                title_bar.bind("<B1-Motion>", do_move)
                title_bar.configure(cursor="hand2")

                # Message
                msg_label = tk.Label(
                    error_dialog,
                    text="All fields are required",
                    bg="#000000",
                    fg="white",
                    font=("Inter", 10),
                    wraplength=300,
                )
                msg_label.pack(padx=20, pady=20)

                # Button frame
                button_frame = tk.Frame(error_dialog, bg="#000000")
                button_frame.pack(pady=10)

                # OK button
                ok_btn = tk.Button(
                    button_frame,
                    text="OK",
                    command=error_dialog.destroy,
                    bg="#800000",
                    fg="white",
                    font=("Inter", 10),
                    width=8,
                )
                ok_btn.pack(padx=5)

                # Center dialog on parent window
                error_dialog.transient(add_window)
                error_dialog.grab_set()
                error_dialog.update_idletasks()
                x = (
                    add_window.winfo_x()
                    + (add_window.winfo_width() - error_dialog.winfo_width()) // 2
                )
                y = (
                    add_window.winfo_y()
                    + (add_window.winfo_height() - error_dialog.winfo_height()) // 2
                )
                error_dialog.geometry(f"+{x}+{y}")

                # Window state handlers
                def on_focus_in(event):
                    error_dialog.attributes("-alpha", 1.0)
                    error_dialog.attributes("-topmost", True)

                def on_focus_out(event):
                    error_dialog.attributes("-alpha", 0.95)
                    error_dialog.attributes("-topmost", False)

                error_dialog.bind("<FocusIn>", on_focus_in)
                error_dialog.bind("<FocusOut>", on_focus_out)
                error_dialog.bind("<Escape>", lambda e: error_dialog.destroy())

                error_dialog.focus_force()
                return

            try:
                # Validate numeric fields
                int(values["IN"])
                int(values["MIN STOCK"])
                float(values["PRICE PER UNIT"])

                # Insert into database
                connection = db.connect()
                cursor = connection.cursor()

                # Check for duplicates
                cursor.execute(
                    "SELECT NAME FROM ITEMSDB WHERE NAME = ?", (values["NAME"],)
                )
                if cursor.fetchone():
                    # Create custom error dialog for duplicate item
                    error_dialog = tk.Toplevel(add_window)
                    error_dialog.overrideredirect(True)
                    error_dialog.withdraw()
                    error_dialog.after(10, error_dialog.deiconify)
                    error_dialog.attributes("-alpha", 1.0)
                    error_dialog.configure(bg="#000000")
                    error_dialog.resizable(False, False)

                    # Create custom title bar
                    title_bar = tk.Frame(error_dialog, bg="#800000", height=30)
                    title_bar.pack(fill=tk.X)

                    title_label = tk.Label(
                        title_bar,
                        text="Error",
                        bg="#800000",
                        fg="white",
                        font=("Inter", 10),
                    )
                    title_label.pack(side=tk.LEFT, padx=10, pady=5)

                    # Add window dragging
                    def start_move(event):
                        error_dialog.x = event.x_root - error_dialog.winfo_x()
                        error_dialog.y = event.y_root - error_dialog.winfo_y()

                    def do_move(event):
                        if hasattr(error_dialog, "x"):
                            x = event.x_root - error_dialog.x
                            y = event.y_root - error_dialog.y
                            error_dialog.geometry(f"+{x}+{y}")

                    title_bar.bind("<Button-1>", start_move)
                    title_bar.bind("<B1-Motion>", do_move)
                    title_bar.configure(cursor="hand2")

                    # Message
                    msg_label = tk.Label(
                        error_dialog,
                        text=f"Item '{values['NAME']}' already exists!",
                        bg="#000000",
                        fg="white",
                        font=("Inter", 10),
                        wraplength=300,
                    )
                    msg_label.pack(padx=20, pady=20)

                    # Button frame
                    button_frame = tk.Frame(error_dialog, bg="#000000")
                    button_frame.pack(pady=10)

                    # OK button
                    ok_btn = tk.Button(
                        button_frame,
                        text="OK",
                        command=error_dialog.destroy,
                        bg="#800000",
                        fg="white",
                        font=("Inter", 10),
                        width=8,
                    )
                    ok_btn.pack(padx=5)

                    # Center dialog on parent window
                    error_dialog.transient(add_window)
                    error_dialog.grab_set()
                    error_dialog.update_idletasks()
                    x = (
                        add_window.winfo_x()
                        + (add_window.winfo_width() - error_dialog.winfo_width()) // 2
                    )
                    y = (
                        add_window.winfo_y()
                        + (add_window.winfo_height() - error_dialog.winfo_height()) // 2
                    )
                    error_dialog.geometry(f"+{x}+{y}")

                    # Window state handlers
                    def on_focus_in(event):
                        error_dialog.attributes("-alpha", 1.0)
                        error_dialog.attributes("-topmost", True)

                    def on_focus_out(event):
                        error_dialog.attributes("-alpha", 0.95)
                        error_dialog.attributes("-topmost", False)

                    error_dialog.bind("<FocusIn>", on_focus_in)
                    error_dialog.bind("<FocusOut>", on_focus_out)
                    error_dialog.bind("<Escape>", lambda e: error_dialog.destroy())

                    error_dialog.focus_force()
                    return

                # Insert new item with explicit column names
                cursor.execute(
                    """
                    INSERT INTO ITEMSDB (
                        [NAME], [BRAND], [TYPE], [LOCATION], [UNIT OF MEASURE], 
                        [IN], [MIN STOCK], [PRICE PER UNIT], [SUPPLIER]
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        values["NAME"],
                        values["BRAND"],
                        values["TYPE"],
                        values["LOCATION"],
                        values["UNIT OF MEASURE"],
                        int(values["IN"]),
                        int(values["MIN STOCK"]),
                        float(values["PRICE PER UNIT"]),
                        values["SUPPLIER"],
                    ),
                )
                connection.commit()

                # Execute the Access database queries after adding item
                try:
                    print(
                        "[DEBUG] Executing 'Update Status' query from Access database..."
                    )
                    cursor.execute("EXEC [Update Status]")
                    connection.commit()
                    print("[DEBUG] 'Update Status' query executed successfully")

                    print("[DEBUG] Executing 'statssum' query from Access database...")
                    cursor.execute("EXEC statssum")
                    connection.commit()
                    print("[DEBUG] 'statssum' query executed successfully")
                except Exception as query_error:
                    print(
                        f"[WARNING] Access queries failed, using fallback: {query_error}"
                    )
                    # Fallback to direct SQL if Access queries fail
                    try:
                        fallback_sql = """
                        UPDATE ITEMSDB
                        SET STATUS = IIf(BALANCE > 0 AND BALANCE <= [MIN STOCK], 'Low in Stock', IIf(BALANCE = 0, 'Out of Stock', 'In Stock'))
                        WHERE BALANCE IS NOT NULL AND [MIN STOCK] IS NOT NULL;
                        """
                        cursor.execute(fallback_sql)
                        connection.commit()
                        print("[DEBUG] Fallback SQL executed successfully")
                    except Exception as fallback_error:
                        print(
                            f"[ERROR] Both Access queries and fallback SQL failed: {fallback_error}"
                        )

                # Log the action using centralized helper
                try:
                    details = f"Added {values['IN']}x of {values['NAME']} from {values['SUPPLIER']}"
                    queries.insert_admin_log(db, username, details)
                except Exception as e:
                    print(f"[LOGGING] Unexpected logging error: {e}")

                # Show success dialog
                success_dialog = tk.Toplevel(add_window)
                success_dialog.overrideredirect(True)
                success_dialog.withdraw()
                success_dialog.after(10, success_dialog.deiconify)
                success_dialog.attributes("-alpha", 1.0)
                success_dialog.configure(bg="#000000")
                success_dialog.resizable(False, False)

                # Create custom title bar
                title_bar = tk.Frame(success_dialog, bg="#800000", height=30)
                title_bar.pack(fill=tk.X)

                title_label = tk.Label(
                    title_bar,
                    text="Success",
                    bg="#800000",
                    fg="white",
                    font=("Inter", 10),
                )
                title_label.pack(side=tk.LEFT, padx=10, pady=5)

                # Add window dragging
                def start_move(event):
                    success_dialog.x = event.x_root - success_dialog.winfo_x()
                    success_dialog.y = event.y_root - success_dialog.winfo_y()

                def do_move(event):
                    if hasattr(success_dialog, "x"):
                        x = event.x_root - success_dialog.x
                        y = event.y_root - success_dialog.y
                        success_dialog.geometry(f"+{x}+{y}")

                title_bar.bind("<Button-1>", start_move)
                title_bar.bind("<B1-Motion>", do_move)
                title_bar.configure(cursor="hand2")

                # Message
                msg_label = tk.Label(
                    success_dialog,
                    text="Item added successfully!",
                    bg="#000000",
                    fg="white",
                    font=("Inter", 10),
                    wraplength=300,
                )
                msg_label.pack(padx=20, pady=20)

                # Button frame
                button_frame = tk.Frame(success_dialog, bg="#000000")
                button_frame.pack(pady=10)

                # OK button
                ok_btn = tk.Button(
                    button_frame,
                    text="OK",
                    command=success_dialog.destroy,
                    bg="#800000",
                    fg="white",
                    font=("Inter", 10),
                    width=8,
                )
                ok_btn.pack(padx=5)

                # Center dialog on parent window
                success_dialog.transient(add_window)
                success_dialog.grab_set()
                success_dialog.update_idletasks()
                x = (
                    add_window.winfo_x()
                    + (add_window.winfo_width() - success_dialog.winfo_width()) // 2
                )
                y = (
                    add_window.winfo_y()
                    + (add_window.winfo_height() - success_dialog.winfo_height()) // 2
                )
                success_dialog.geometry(f"+{x}+{y}")

                # Window state handlers
                def on_focus_in(event):
                    success_dialog.attributes("-alpha", 1.0)
                    success_dialog.attributes("-topmost", True)

                def on_focus_out(event):
                    success_dialog.attributes("-alpha", 0.95)
                    success_dialog.attributes("-topmost", False)

                success_dialog.bind("<FocusIn>", on_focus_in)
                success_dialog.bind("<FocusOut>", on_focus_out)
                success_dialog.bind("<Escape>", lambda e: success_dialog.destroy())

                success_dialog.focus_force()
                add_window.wait_window(success_dialog)

                # Ensure the database connection is refreshed before reloading data
                connection.close()
                connection = db.connect()

                # Delete any drafts for this item from ANI_DRAFTS table
                try:
                    cursor = connection.cursor()
                    cursor.execute(
                        "DELETE FROM ANI_DRAFTS WHERE [Item Name] = ?",
                        (values["NAME"],),
                    )
                    connection.commit()
                except Exception as e:
                    # Only log serious errors, ignore table not found
                    if not str(e).startswith(
                        "('42S02'"
                    ):  # Not a "table not found" error
                        print(f"Error handling drafts: {e}")
                finally:
                    cursor.close()

                # Call load_data_callback to refresh the table and trigger stats update
                load_data_callback()

                # Force an update of the stats panel through the admin dashboard
                if hasattr(root, "update_stats"):
                    root.update_stats()

                # Custom dialog to keep add_window in front
                dialog = tk.Toplevel(add_window)
                dialog.overrideredirect(True)
                dialog.withdraw()
                dialog.after(10, dialog.deiconify)
                dialog.attributes("-alpha", 1.0)
                dialog.configure(bg="#000000")
                dialog.resizable(False, False)

                # Create custom title bar
                title_bar = tk.Frame(dialog, bg="#800000", height=30)
                title_bar.pack(fill=tk.X)

                title_label = tk.Label(
                    title_bar,
                    text="Add Another Item",
                    bg="#800000",
                    fg="white",
                    font=("Inter", 10),
                )
                title_label.pack(side=tk.LEFT, padx=10, pady=5)

                # Add window dragging
                def start_move(event):
                    dialog.x = event.x_root - dialog.winfo_x()
                    dialog.y = event.y_root - dialog.winfo_y()

                def do_move(event):
                    if hasattr(dialog, "x"):
                        x = event.x_root - dialog.x
                        y = event.y_root - dialog.y
                        dialog.geometry(f"+{x}+{y}")

                title_bar.bind("<Button-1>", start_move)
                title_bar.bind("<B1-Motion>", do_move)
                title_bar.configure(cursor="hand2")

                # Message
                msg_label = tk.Label(
                    dialog,
                    text="Would you like to add another item?",
                    bg="#000000",
                    fg="white",
                    font=("Inter", 11),
                    wraplength=250,
                )
                msg_label.pack(padx=20, pady=20)

                # Buttons frame
                btn_frame = tk.Frame(dialog, bg="#000000")
                btn_frame.pack(pady=10)

                def on_yes():
                    dialog.destroy()
                    for entry in entries.values():
                        if isinstance(entry, ttk.Combobox):
                            entry.set("")
                        else:
                            entry.delete(0, tk.END)

                def on_no():
                    dialog.destroy()
                    add_window.destroy()

                yes_btn = tk.Button(
                    btn_frame,
                    text="Yes",
                    command=on_yes,
                    bg="#800000",
                    fg="white",
                    font=("Inter", 10),
                    width=10,
                )
                no_btn = tk.Button(
                    btn_frame,
                    text="No",
                    command=on_no,
                    bg="#800000",
                    fg="white",
                    font=("Inter", 10),
                    width=10,
                )
                yes_btn.pack(side=tk.LEFT, padx=5)
                no_btn.pack(side=tk.LEFT, padx=5)

                # Center dialog on parent window
                dialog.transient(add_window)
                dialog.grab_set()
                dialog.update_idletasks()
                dialog_width = 300
                dialog_height = 150
                x = (
                    add_window.winfo_x()
                    + (add_window.winfo_width() - dialog_width) // 2
                )
                y = (
                    add_window.winfo_y()
                    + (add_window.winfo_height() - dialog_height) // 2
                )
                dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

                # Window state handlers
                def on_focus_in(event):
                    dialog.attributes("-alpha", 1.0)
                    dialog.attributes("-topmost", True)

                def on_focus_out(event):
                    dialog.attributes("-alpha", 0.95)
                    dialog.attributes("-topmost", False)

                dialog.bind("<FocusIn>", on_focus_in)
                dialog.bind("<FocusOut>", on_focus_out)
                dialog.bind("<Escape>", lambda e: on_no())

                dialog.focus_force()
                add_window.wait_window(dialog)

            except ValueError:
                # Create custom error dialog for invalid numbers
                error_dialog = tk.Toplevel(add_window)
                error_dialog.overrideredirect(True)
                error_dialog.withdraw()
                error_dialog.after(10, error_dialog.deiconify)
                error_dialog.attributes("-alpha", 1.0)
                error_dialog.configure(bg="#000000")
                error_dialog.resizable(False, False)

                # Create custom title bar
                title_bar = tk.Frame(error_dialog, bg="#800000", height=30)
                title_bar.pack(fill=tk.X)

                title_label = tk.Label(
                    title_bar,
                    text="Error",
                    bg="#800000",
                    fg="white",
                    font=("Inter", 10),
                )
                title_label.pack(side=tk.LEFT, padx=10, pady=5)

                # Add window dragging
                def start_move(event):
                    error_dialog.x = event.x_root - error_dialog.winfo_x()
                    error_dialog.y = event.y_root - error_dialog.winfo_y()

                def do_move(event):
                    if hasattr(error_dialog, "x"):
                        x = event.x_root - error_dialog.x
                        y = event.y_root - error_dialog.y
                        error_dialog.geometry(f"+{x}+{y}")

                title_bar.bind("<Button-1>", start_move)
                title_bar.bind("<B1-Motion>", do_move)
                title_bar.configure(cursor="hand2")

                # Message
                msg_label = tk.Label(
                    error_dialog,
                    text="Please enter valid numbers for quantity and price fields",
                    bg="#000000",
                    fg="white",
                    font=("Inter", 10),
                    wraplength=300,
                )
                msg_label.pack(padx=20, pady=20)

                # Button frame
                button_frame = tk.Frame(error_dialog, bg="#000000")
                button_frame.pack(pady=10)

                # OK button
                ok_btn = tk.Button(
                    button_frame,
                    text="OK",
                    command=error_dialog.destroy,
                    bg="#800000",
                    fg="white",
                    font=("Inter", 10),
                    width=8,
                )
                ok_btn.pack(padx=5)

                # Center dialog on parent window
                error_dialog.transient(add_window)
                error_dialog.grab_set()
                error_dialog.update_idletasks()
                x = (
                    add_window.winfo_x()
                    + (add_window.winfo_width() - error_dialog.winfo_width()) // 2
                )
                y = (
                    add_window.winfo_y()
                    + (add_window.winfo_height() - error_dialog.winfo_height()) // 2
                )
                error_dialog.geometry(f"+{x}+{y}")

                # Window state handlers
                def on_focus_in(event):
                    error_dialog.attributes("-alpha", 1.0)
                    error_dialog.attributes("-topmost", True)

                def on_focus_out(event):
                    error_dialog.attributes("-alpha", 0.95)
                    error_dialog.attributes("-topmost", False)

                error_dialog.bind("<FocusIn>", on_focus_in)
                error_dialog.bind("<FocusOut>", on_focus_out)
                error_dialog.bind("<Escape>", lambda e: error_dialog.destroy())

                error_dialog.focus_force()

            except Exception as e:
                # Create custom error dialog for general errors
                error_dialog = tk.Toplevel(add_window)
                error_dialog.overrideredirect(True)
                error_dialog.withdraw()
                error_dialog.after(10, error_dialog.deiconify)
                error_dialog.attributes("-alpha", 1.0)
                error_dialog.configure(bg="#000000")
                error_dialog.resizable(False, False)

                # Create custom title bar
                title_bar = tk.Frame(error_dialog, bg="#800000", height=30)
                title_bar.pack(fill=tk.X)

                title_label = tk.Label(
                    title_bar,
                    text="Error",
                    bg="#800000",
                    fg="white",
                    font=("Inter", 10),
                )
                title_label.pack(side=tk.LEFT, padx=10, pady=5)

                # Add window dragging
                def start_move(event):
                    error_dialog.x = event.x_root - error_dialog.winfo_x()
                    error_dialog.y = event.y_root - error_dialog.winfo_y()

                def do_move(event):
                    if hasattr(error_dialog, "x"):
                        x = event.x_root - error_dialog.x
                        y = event.y_root - error_dialog.y
                        error_dialog.geometry(f"+{x}+{y}")

                title_bar.bind("<Button-1>", start_move)
                title_bar.bind("<B1-Motion>", do_move)
                title_bar.configure(cursor="hand2")

                # Message
                msg_label = tk.Label(
                    error_dialog,
                    text=f"An error occurred: {str(e)}",
                    bg="#000000",
                    fg="white",
                    font=("Inter", 10),
                    wraplength=300,
                )
                msg_label.pack(padx=20, pady=20)

                # Button frame
                button_frame = tk.Frame(error_dialog, bg="#000000")
                button_frame.pack(pady=10)

                # OK button
                ok_btn = tk.Button(
                    button_frame,
                    text="OK",
                    command=error_dialog.destroy,
                    bg="#800000",
                    fg="white",
                    font=("Inter", 10),
                    width=8,
                )
                ok_btn.pack(padx=5)

                # Center dialog on parent window
                error_dialog.transient(add_window)
                error_dialog.grab_set()
                error_dialog.update_idletasks()
                x = (
                    add_window.winfo_x()
                    + (add_window.winfo_width() - error_dialog.winfo_width()) // 2
                )
                y = (
                    add_window.winfo_y()
                    + (add_window.winfo_height() - error_dialog.winfo_height()) // 2
                )
                error_dialog.geometry(f"+{x}+{y}")

                # Window state handlers
                def on_focus_in(event):
                    error_dialog.attributes("-alpha", 1.0)
                    error_dialog.attributes("-topmost", True)

                def on_focus_out(event):
                    error_dialog.attributes("-alpha", 0.95)
                    error_dialog.attributes("-topmost", False)

                error_dialog.bind("<FocusIn>", on_focus_in)
                error_dialog.bind("<FocusOut>", on_focus_out)
                error_dialog.bind("<Escape>", lambda e: error_dialog.destroy())

                error_dialog.focus_force()
            finally:
                if "connection" in locals():
                    connection.close()

        # Key bindings
        add_window.bind("<Return>", lambda e: save_item())
        add_window.bind("<Escape>", lambda e: add_window.destroy())

    add_material_to_jjcims(root, db, load_data_callback)


def load_combo_data(db, field):
    """Load unique values from database for combo boxes"""
    try:
        connection = db.connect()
        cursor = connection.cursor()
        cursor.execute(
            f"SELECT DISTINCT [{field}] FROM ITEMSDB WHERE [{field}] IS NOT NULL ORDER BY [{field}]"
        )
        values = [row[0] for row in cursor.fetchall()]
        values.append("Add +")  # Add the "Add +" option
        return values
    except Exception as e:
        print(f"Error loading {field} data: {e}")
        return ["Add +"]
    finally:
        if "connection" in locals():
            connection.close()


def add_new_value(db, field, combo, add_window):
    """Make combo box editable to add new values directly"""
    combo.configure(state="normal")  # Make editable
    combo.delete(0, tk.END)  # Clear current value
    combo.focus_set()  # Set focus for immediate typing

    def handle_input(event=None):
        """Handle the input when Enter is pressed or focus is lost"""
        new_value = combo.get().strip()
        if new_value and new_value != "Add +":
            # Check if this value exists in the database
            try:
                connection = db.connect()
                cursor = connection.cursor()
                cursor.execute(
                    f"SELECT COUNT(*) FROM ITEMSDB WHERE [{field}] = ?", (new_value,)
                )
                count = cursor.fetchone()[0]

                if count == 0:
                    # Value doesn't exist, update combo values
                    current_values = list(combo["values"])
                    if "Add +" in current_values:
                        current_values.insert(-1, new_value)  # Insert before "Add +"
                    else:
                        current_values.append(new_value)
                        current_values.append("Add +")
                    combo["values"] = current_values
            except Exception as e:
                print(f"Error checking value existence: {e}")
            finally:
                if "connection" in locals():
                    connection.close()

        combo.configure(state="readonly")  # Make readonly again

    # Bind Enter key and focus-out events
    combo.bind("<Return>", handle_input)
    combo.bind("<FocusOut>", handle_input)


def configure_combo_style():
    """Configure the ttk style for combo boxes"""
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
        relief="flat",
    )
    style.layout(
        "Custom.TCombobox",
        [
            (
                "Combobox.field",
                {
                    "sticky": "nswe",
                    "children": [
                        (
                            "Combobox.padding",
                            {
                                "expand": "1",
                                "sticky": "nswe",
                                "children": [("Combobox.textarea", {"sticky": "nswe"})],
                            },
                        )
                    ],
                },
            )
        ],
    )
    style.map(
        "Custom.TCombobox",
        fieldbackground=[("readonly", "#000000")],
        selectbackground=[("readonly", "#800000")],
        selectforeground=[("readonly", "#FFFFFF")],
        relief=[("readonly", "flat")],
    )


def handle_combo_selection(event, combo, field, db, add_window):
    """Handle combo box selection, including the Add + option"""
    if combo.get() == "Add +":
        add_new_value(db, field, combo, add_window)
    else:
        # When a value is selected, check if it's still used in the database
        try:
            connection = db.connect()
            cursor = connection.cursor()
            # Count occurrences of this value
            cursor.execute(
                f"SELECT COUNT(*) FROM ITEMSDB WHERE [{field}] = ?", (combo.get(),)
            )
            count = cursor.fetchone()[0]

            if count == 0:
                # If value is not used anymore, remove it from combo box
                current_values = list(combo["values"])
                if combo.get() in current_values:
                    current_values.remove(combo.get())
                    combo["values"] = current_values
                    combo.set("")  # Clear the selection
        except Exception as e:
            print(f"Error checking value usage: {e}")
        finally:
            if "connection" in locals():
                connection.close()


def handle_helper_button(button_num, entries, db, add_window):
    """Handle helper button clicks to open respective combo boxes"""
    # Map button numbers to entry indices and field names
    button_map = {
        8: (2, "BRAND"),
        9: (3, "TYPE"),
        10: (4, "LOCATION"),
        11: (7, "UNIT OF MEASURE"),
        12: (9, "SUPPLIER"),
    }

    if button_num in button_map:
        entry_num, field = button_map[button_num]
        combo = entries[f"entry_{entry_num}"]
        combo.focus_set()
        combo.event_generate("<Down>")

        def validate_entry(entry_num, value):
            """Validate entry values and show warnings"""
            warning_label = entries[f"warning_{entry_num}"]

            if not value.strip():
                warning_label.config(text="This field is required")
                return False

            if entry_num == 5:  # Minimum Stock
                try:
                    val = int(value)
                    if val < 0:
                        warning_label.config(text="Must be a positive number")
                        return False
                    warning_label.config(text="")
                    return True
                except ValueError:
                    warning_label.config(text="Must be a valid number")
                    return False

            if entry_num == 6:  # In Stock
                try:
                    val = int(value)
                    if val < 0:
                        warning_label.config(text="Must be a positive number")
                        return False
                    warning_label.config(text="")
                    return True
                except ValueError:
                    warning_label.config(text="Must be a valid number")
                    return False

            if entry_num == 8:  # Price
                try:
                    val = float(value)
                    if val < 0:
                        warning_label.config(text="Must be a positive number")
                        return False
                    warning_label.config(text="")
                    return True
                except ValueError:
                    warning_label.config(text="Must be a valid price")
                    return False

            warning_label.config(text="")
            return True

        # Bind validation to entries
        for i in [1, 5, 6, 8]:  # Only bind to non-combo entries
            entry = entries[f"entry_{i}"]
            entry.bind(
                "<KeyRelease>", lambda e, num=i: validate_entry(num, e.widget.get())
            )
            entry.bind(
                "<FocusOut>", lambda e, num=i: validate_entry(num, e.widget.get())
            )

        def show_loading_indicator(message="Processing..."):
            """Show a loading indicator during long operations"""
            loading = tk.Toplevel(add_window)
            loading.overrideredirect(True)
            loading.configure(bg="#000000")
            loading.transient(add_window)

            # Center on parent window
            x = add_window.winfo_x() + (add_window.winfo_width() - 200) // 2
            y = add_window.winfo_y() + (add_window.winfo_height() - 50) // 2
            loading.geometry(f"200x50+{x}+{y}")

            label = tk.Label(loading, text=message, bg="#000000", fg="#FFFFFF")
            label.pack(expand=True)

            loading.update()
            return loading

        def handle_database_operation(operation_func, success_message, error_message):
            """Handle database operations with loading indicator"""
            loading = show_loading_indicator()
            try:
                result = operation_func()
                loading.destroy()
                if result:  # If operation was successful
                    messagebox.showinfo("Success", success_message)
                return result
            except Exception as e:
                loading.destroy()
                messagebox.showerror("Error", f"{error_message}: {str(e)}")
                return False
            finally:
                if loading.winfo_exists():
                    loading.destroy()

        # Modified save_item function to use loading indicator
        def save_item_with_loading():
            def save_operation():
                # Existing save_item logic here
                return True

            return handle_database_operation(
                save_operation, "Item added successfully!", "Failed to save item"
            )
