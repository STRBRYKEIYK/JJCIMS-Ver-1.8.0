import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkfont
from gui.functions.admdash_f.checkbox_treeview import CheckboxTreeview

# Updated column widths for better readability
EXTENDED_COLUMN_WIDTHS = {
    "NAME": 250, "BRAND": 150, "TYPE": 150, "LOCATION": 150, "UNIT OF MEASURE": 120, "STATUS": 120,
    "IN": 100, "OUT": 100, "BALANCE": 100, "MIN STOCK": 120, "DEFICIT": 100, "PRICE PER UNIT": 150, "COST": 150, "LAST PO": 150, "SUPPLIER": 200
}

# Utility: Reset columns and headings with alignment
def reset_table_columns(table, columns, column_widths):
    center_cols = {"IN", "OUT", "BALANCE", "MIN STOCK", "DEFICIT", "STATUS", "PRICE PER UNIT", "COST", "LAST PO"}
    center_header_only = {"NAME", "BRAND", "TYPE", "LOCATION", "UNIT OF MEASURE", "SUPPLIER"}
    table["columns"] = columns
    for col in columns:
        display_col = col.replace("_", " ")
        if col in center_cols:
            anchor = "center"
            heading_anchor = "center"
        elif col in center_header_only:
            anchor = "w"
            heading_anchor = "center"
        else:
            anchor = "w"
            heading_anchor = "w"
        table.heading(col, text=display_col, anchor=heading_anchor)
        table.column(col, width=column_widths.get(col, 100), anchor=anchor)

# Utility: Auto-adjust column widths
def auto_adjust_column_widths(table):
    font = tkfont.nametofont("TkDefaultFont")
    for col in table["columns"]:
        max_width = font.measure(col)
        for row_id in table.get_children():
            value = str(table.set(row_id, col))
            max_width = max(max_width, font.measure(value))
        table.column(col, width=max_width + 20)

# Utility: Clear all rows
def clear_table(table):
    for row in table.get_children():
        table.delete(row)

# Utility: Load data from ML table
# format_row and update_stats are callbacks for row formatting and stats update
# db must have .connect() method
# default_columns/widths are lists/dicts
# This is a general loader for admin tables

def load_data(table, db, default_columns, default_column_widths, format_row, update_stats):
    try:
        # Set new columns for the table
        extended_columns = [
            "NAME", "BRAND", "TYPE", "LOCATION", "UNIT OF MEASURE", "STATUS", "IN", "OUT", "BALANCE", "MIN STOCK", "DEFICIT", "PRICE PER UNIT", "COST", "LAST PO", "SUPPLIER"
        ]
        reset_table_columns(table, extended_columns, EXTENDED_COLUMN_WIDTHS)
        clear_table(table)
        connection = db.connect()
        cursor = connection.cursor()
        query = (
            "SELECT [NAME], [BRAND], [TYPE], [LOCATION], [UNIT OF MEASURE], [STATUS], [IN], [OUT], [BALANCE], [MIN STOCK], [DEFICIT], [PRICE PER UNIT], [COST], [LAST PO], [SUPPLIER] "
            "FROM ITEMSDB"
        )
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            formatted_row = format_row(row, extended_columns)
            table.insert("", "end", values=formatted_row)
        # Auto-sort by NAME column (A-Z)
        name_col_index = extended_columns.index("NAME")
        items = [(table.set(row_id, "NAME"), row_id) for row_id in table.get_children("")]
        items.sort(key=lambda x: x[0].lower())
        for index, (_, row_id) in enumerate(items):
            table.move(row_id, '', index)
        # Add sorting functionality to column headers
        sort_states = {col: False for col in extended_columns}
        def sort_column(col):
            sort_states[col] = not sort_states[col]
            reverse = sort_states[col]
            items = [(table.set(row_id, col), row_id) for row_id in table.get_children("")]
            items.sort(key=lambda x: x[0].lower() if isinstance(x[0], str) else x[0], reverse=reverse)
            for index, (_, row_id) in enumerate(items):
                table.move(row_id, '', index)
            # Update headings to show sort state
            arrow = " ▼" if reverse else " ▲"
            for c in extended_columns:
                text = c + (arrow if c == col else "")
                table.heading(c, text=text)
        for col in extended_columns:
            def make_sort_command(col_name):
                return lambda: sort_column(col_name)
            table.heading(col, text=col, command=make_sort_command(col))
        auto_adjust_column_widths(table)
        update_stats()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load data: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

def format_row(row, columns):
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
            except Exception as e:
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

# Factory: Create admin items table (with checkboxes and custom style)
def create_items_table(dashboard):
    if dashboard.table:
        dashboard.table.destroy()
    if dashboard.scroll_y:
        dashboard.scroll_y.destroy()
    dashboard.scroll_y = ttk.Scrollbar(dashboard.table_frame, orient=tk.VERTICAL, style="Custom.Vertical.TScrollbar")
    
    # Configure the style properly
    style = ttk.Style()
    # Don't reset theme - just configure the styles directly
    style.configure(
        "Admin.Treeview",
        font=("Segoe UI", 14, "bold"),
        rowheight=36,
        background="#181c1f",
        fieldbackground="#181c1f",
        foreground="#FFD700",
        bordercolor="#181c1f",
        borderwidth=0,
    )
    style.map(
        "Admin.Treeview",
        background=[('selected', '#FFD700')],
        foreground=[('selected', '#181c1f')],
    )
    style.configure(
        "Admin.Treeview.Heading",
        font=("Segoe UI", 14, "bold"),
        background="#181c1f",
        foreground="#FFD700",
        bordercolor="#FFD700",
        borderwidth=2,
    )
    style.map(
        "Admin.Treeview.Heading",
        background=[('active', '#FFD700')],
        foreground=[('active', '#181c1f')],
    )
    dashboard.table = CheckboxTreeview(
        dashboard.table_frame,
        columns=dashboard.default_columns,
        show="tree headings",
        style="Admin.Treeview",
        yscrollcommand=dashboard.scroll_y.set
    )
    dashboard.scroll_y.config(command=dashboard.table.yview)
    dashboard.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
    dashboard.table.pack(fill=tk.BOTH, expand=True)
    col_settings = [
        ("NAME", 180, "w"),
        ("BRAND", 120, "w"),
        ("TYPE", 120, "w"),
        ("LOCATION", 120, "w"),
        ("UNIT OF MEASURE", 120, "w"),
        ("STATUS", 100, "center"),
        ("IN", 80, "center"),
        ("OUT", 80, "center"),
        ("BALANCE", 80, "center"),
        ("MIN STOCK", 90, "center"),
        ("DEFICIT", 80, "center"),
        ("PRICE PER UNIT", 120, "center"),
        ("COST", 120, "center"),
        ("LAST PO", 120, "center"),
        ("SUPPLIER", 150, "w"),
    ]
    for idx, (col, width, anchor) in enumerate(col_settings):
        dashboard.table.heading(col, text=col, anchor=anchor)
        dashboard.table.column(col, width=width, anchor=anchor, minwidth=width, stretch=True)
    dashboard.table.heading("#0", text="", anchor="center")
    dashboard.table.column("#0", width=50, anchor="center", stretch=False)
    dashboard.table.update_idletasks()
    # Auto-adjust columns for content
    auto_adjust_column_widths(dashboard.table)

# Factory: Create logs table (simple headings, no checkboxes)
def create_logs_table(dashboard, columns=None):
    if dashboard.table:
        dashboard.table.destroy()
    if dashboard.scroll_y:
        dashboard.scroll_y.destroy()
    dashboard.scroll_y = ttk.Scrollbar(dashboard.table_frame, orient=tk.VERTICAL, style="Custom.Vertical.TScrollbar")
    style = ttk.Style()
    # Don't reset theme - just configure the styles directly
    style.configure(
        "Admin.Treeview",
        font=("Segoe UI", 14, "bold"),
        rowheight=36,
        background="#181c1f",
        fieldbackground="#181c1f",
        foreground="#FFD700",
        bordercolor="#181c1f",
        borderwidth=0,
    )
    style.map(
        "Admin.Treeview",
        background=[('selected', '#FFD700')],
        foreground=[('selected', '#181c1f')],
    )
    style.configure(
        "Admin.Treeview.Heading",
        font=("Segoe UI", 14, "bold"),
        background="#181c1f",
        foreground="#FFD700",
        bordercolor="#FFD700",
        borderwidth=2,
    )
    style.map(
        "Admin.Treeview.Heading",
        background=[('active', '#FFD700')],
        foreground=[('active', '#181c1f')],
    )
    # Always set columns and headings
    if not columns:
        columns = ["DATE", "TIME", "NAME", "DETAILS"]
    dashboard.table = ttk.Treeview(
        dashboard.table_frame,
        columns=columns,
        show="headings",
        style="Admin.Treeview",
        yscrollcommand=dashboard.scroll_y.set
    )
    dashboard.scroll_y.config(command=dashboard.table.yview)
    dashboard.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
    dashboard.table.pack(fill=tk.BOTH, expand=True)
    for col in columns:
        dashboard.table.heading(col, text=col)
        dashboard.table.column(col, width=120, anchor="center")