import tkinter as tk
from gui.functions.admdash_f.checkbox_treeview import CheckboxTreeview
from tkinter import ttk
from gui.functions.admdash_f.table_utils import load_data
from backend.database import get_db_path

# Updated headers for ITEMSDB Treeview
DEFAULT_COLUMNS = [
    "NAME",
    "BRAND",
    "TYPE",
    "LOCATION",
    "UNIT OF MEASURE",
    "STATUS",
    "IN",
    "OUT",
    "BALANCE",
    "MIN STOCK",
    "DEFICIT",
    "PRICE PER UNIT",
    "COST",
    "LAST PO",
    "SUPPLIER",
]
DEFAULT_COLUMN_WIDTHS = {
    "NAME": 150,
    "BRAND": 100,
    "TYPE": 100,
    "LOCATION": 100,
    "UNIT OF MEASURE": 100,
    "STATUS": 80,
    "IN": 60,
    "OUT": 60,
    "BALANCE": 70,
    "MIN STOCK": 80,
    "DEFICIT": 70,
    "PRICE PER UNIT": 100,
    "COST": 100,
    "LAST PO": 100,
    "SUPPLIER": 120,
}
NUMERIC_COLUMNS = {
    "IN",
    "OUT",
    "BALANCE",
    "MIN STOCK",
    "DEFICIT",
    "PRICE PER UNIT",
    "COST",
}
CENTERED_COLUMNS = {
    "IN",
    "OUT",
    "BALANCE",
    "MIN STOCK",
    "DEFICIT",
    "STATUS",
    "PRICE PER UNIT",
    "COST",
    "LAST PO",
}


def view_items_treeview(dashboard):
    """Always destroy and recreate the ITEMSDB Treeview with checkboxes and style."""
    columns = dashboard.default_columns
    if hasattr(dashboard, "table") and dashboard.table:
        dashboard.table.destroy()
    if hasattr(dashboard, "scroll_y") and dashboard.scroll_y:
        dashboard.scroll_y.destroy()
    if hasattr(dashboard, "scroll_x") and dashboard.scroll_x:
        dashboard.scroll_x.destroy()

    # Create both vertical and horizontal scrollbars
    dashboard.scroll_y = ttk.Scrollbar(
        dashboard.table_frame, orient=tk.VERTICAL, style="Custom.Vertical.TScrollbar"
    )
    dashboard.scroll_x = ttk.Scrollbar(
        dashboard.table_frame,
        orient=tk.HORIZONTAL,
        style="Custom.Horizontal.TScrollbar",
    )

    # Store sort state
    dashboard.sort_states = {
        col: False for col in columns
    }  # False = ascending, True = descending

    style = ttk.Style()
    style.configure(
        "Admin.Treeview",
        font=("Segoe UI", 11, "bold"),  # Reduced font size
        rowheight=28,  # Reduced row height
        background="#181c1f",
        fieldbackground="#181c1f",
        foreground="#FFFFFF",
        bordercolor="#404040",  # Darker grey for cell borders
        borderwidth=1,
        relief="solid",
    )
    # Configure the cell borders and grid
    style.layout(
        "Admin.Treeview",
        [
            ("Admin.Treeview.treearea", {"sticky": "nswe", "border": 1}),
        ],
    )
    # Add grid lines
    dashboard.table_frame.grid_rowconfigure(0, weight=1)
    dashboard.table_frame.grid_columnconfigure(0, weight=1)
    style.map(
        "Admin.Treeview",
        background=[("selected", "#FFFFFF")],
        foreground=[("selected", "#181c1f")],
    )
    style.configure(
        "Admin.Treeview.Heading",
        font=("Segoe UI", 11, "bold"),  # Reduced font size
        background="#181c1f",
        foreground="#FFFFFF",
        padding=(2, 2),  # Reduced padding
        bordercolor="#404040",  # Darker grey for header borders
        borderwidth=1,
        relief="raised",
    )

    def sort_column(col):
        """Sort treeview column with A-Z indicator."""
        # Check if we're in restock list view and refresh data first
        if (
            hasattr(dashboard, "current_view")
            and dashboard.current_view == "Restock List"
        ):
            print("[DEBUG] Refreshing restock data before sorting...")
            from gui.functions.admdash_f.vrl import load_restock_list

            load_restock_list(get_db_path(), dashboard.table)

        dashboard.sort_states[col] = not dashboard.sort_states[col]  # Toggle sort state
        reverse = dashboard.sort_states[col]
        # Get all items
        rows_list = [
            (dashboard.table.set(k, col), k) for k in dashboard.table.get_children("")
        ]

        # Convert numbers to float for proper numeric sorting
        if col in NUMERIC_COLUMNS:
            rows_list = [
                (float("".join(filter(str.isdigit, i[0]))) if i[0].strip() else 0, i[1])
                for i in rows_list
            ]
        # Special handling for LAST PO column
        elif col == "LAST PO":
            from datetime import datetime

            def parse_date(date_str):
                try:
                    # Remove any time component
                    date_part = date_str.split(" ")[0].split("T")[0]
                    return datetime.strptime(date_part, "%Y/%m/%d")
                except Exception:
                    try:
                        return datetime.strptime(date_str, "%Y-%m-%d")
                    except Exception:
                        return datetime.min  # Return minimum date if parsing fails

            rows_list = [
                (parse_date(i[0]) if i[0].strip() else datetime.min, i[1])
                for i in rows_list
            ]

        # Sort the list
        rows_list.sort(reverse=reverse)

        # Rearrange items in sorted positions
        for index, (val, k) in enumerate(rows_list):
            dashboard.table.move(k, "", index)

        # Update headings to show sort state
        arrow = " ▼" if reverse else " ▲"
        for c in columns:
            text = c + (arrow if c == col else "")
            dashboard.table.heading(c, text=text)

    # Update column names and widths to match JJCIMS schema
    dashboard.table = CheckboxTreeview(
        dashboard.table_frame,
        columns=columns,
        show="headings",
        style="Admin.Treeview",
        yscrollcommand=dashboard.scroll_y.set,
        xscrollcommand=dashboard.scroll_x.set,
        selectmode="browse",
    )
    dashboard.scroll_y.config(command=dashboard.table.yview)
    dashboard.scroll_x.config(command=dashboard.table.xview)

    dashboard.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
    dashboard.scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
    dashboard.table.pack(fill=tk.BOTH, expand=True)

    col_settings = [
        ("NAME", 150, "w"),
        ("BRAND", 100, "w"),
        ("TYPE", 100, "w"),
        ("LOCATION", 100, "w"),
        ("UNIT OF MEASURE", 100, "w"),
        ("STATUS", 80, "w"),
        ("IN", 60, "center"),
        ("OUT", 60, "center"),
        ("BALANCE", 70, "center"),
        ("MIN STOCK", 80, "center"),
        ("DEFICIT", 70, "center"),
        ("PRICE PER UNIT", 100, "e"),
        ("COST", 100, "e"),
        ("LAST PO", 100, "w"),
        ("SUPPLIER", 120, "w"),
    ]

    for col, width, anchor in col_settings:

        def make_sort_command(col_name=col):
            return lambda: sort_column(col_name)

        dashboard.table.heading(
            col, text=col, anchor=anchor, command=make_sort_command()
        )
        dashboard.table.column(
            col, width=width, anchor=anchor, minwidth=60, stretch=False
        )

    # Add right-click auto-resize functionality
    def auto_resize_on_right_click(event):
        """Auto-resize column to fit content when right-clicking on header."""
        try:
            # Check if we're in restock list view and refresh data first
            if (
                hasattr(dashboard, "current_view")
                and dashboard.current_view == "Restock List"
            ):
                print("[DEBUG] Refreshing restock data before auto-resize...")
                dashboard.view_restock_list()
                return  # Exit early since view_restock_list will reload everything

            region = dashboard.table.identify_region(event.x, event.y)
            if region == "heading":
                column = dashboard.table.identify_column(event.x, event.y)
                if column:
                    col_index = int(column.replace("#", "")) - 1
                    if col_index >= 0 and col_index < len(dashboard.table["columns"]):
                        col_name = dashboard.table["columns"][col_index]
                        auto_resize_column_main(dashboard.table, col_name)
        except Exception as e:
            print(f"[ERROR] Failed to auto-resize column: {e}")

    def auto_resize_column_main(table, col_name):
        """Auto-resize a specific column to fit its content."""
        try:
            import tkinter.font as tkfont

            # Get the font used in the treeview
            try:
                font = tkfont.nametofont(table.cget("font"))
            except Exception:
                font = tkfont.Font(family="Segoe UI", size=11, weight="bold")

            # Calculate header width
            header_width = font.measure(col_name) + 40

            # Find maximum content width in this column
            max_width = header_width
            for item in table.get_children():
                value = str(table.set(item, col_name))
                content_width = font.measure(value) + 20
                max_width = max(max_width, content_width)

            # Set reasonable bounds
            min_width = 60
            max_reasonable_width = 400
            final_width = max(min_width, min(max_width, max_reasonable_width))

            # Apply the new width
            table.column(col_name, width=final_width)
            print(f"[DEBUG] Auto-resized column '{col_name}' to width {final_width}")

        except Exception as e:
            print(f"[ERROR] Failed to auto-resize column {col_name}: {e}")

    # Bind right-click event
    dashboard.table.bind("<Button-3>", auto_resize_on_right_click)

    dashboard.table.heading("#0", text="", anchor="center")
    dashboard.table.column("#0", width=50, anchor="center", stretch=False)
    dashboard.table.update_idletasks()
    # Hide the Mark as Produced button if present (not FPI view)
    if hasattr(dashboard, "hide_mark_produced_button"):
        dashboard.hide_mark_produced_button()

    # Format PRICE PER UNIT, COST, and LAST PO columns
    for item in dashboard.table.get_children():
        values = dashboard.table.item(item, "values")
        formatted_values = []
        for idx, value in enumerate(values):
            col_name = DEFAULT_COLUMNS[idx]
            if col_name in {"PRICE PER UNIT", "COST"}:
                try:
                    formatted_values.append(f"₱{float(value):,.2f}")
                except ValueError:
                    formatted_values.append("₱0.00")
            elif col_name == "LAST PO" and value:
                try:
                    # Remove any time component
                    date_part = str(value).split(" ")[0].split("T")[0].split(".")[0]
                    formatted_values.append(date_part.replace("-", "/"))
                except Exception:
                    formatted_values.append(value)
            else:
                formatted_values.append(value)
        dashboard.table.item(item, values=formatted_values)

    # Load data into the Treeview
    load_data(
        table=dashboard.table,
        db=dashboard.db,
        default_columns=DEFAULT_COLUMNS,
        default_column_widths=DEFAULT_COLUMN_WIDTHS,
        format_row=dashboard.format_row,
        update_stats=dashboard.update_stats,
    )
    # Auto-sort rows A-Z by NAME after loading
    items = [
        (dashboard.table.set(row_id, "NAME"), row_id)
        for row_id in dashboard.table.get_children("")
    ]
    items.sort(key=lambda x: x[0].lower())
    for index, (_, row_id) in enumerate(items):
        dashboard.table.move(row_id, "", index)
