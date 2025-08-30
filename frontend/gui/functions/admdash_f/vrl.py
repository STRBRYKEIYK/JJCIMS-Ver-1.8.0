"""
Vendor Restock List Module (vrl.py)

This module handles the display and management of items that need restocking.
The restock list is based on the STATUS field in the ITEMSDB table,
specifically items with status 'Out of Stock' or 'Low in Stock'.
Results are ordered to show 'Out of Stock' items first, then 'Low in Stock' items.

Functions:
- load_restock_list: Load items needing restocking into a treeview
- format_row: Format data for display in the treeview
- sort_restock_column: Sort the treeview by column
- auto_resize_column_on_right_click: Auto-resize column on right-click
- auto_resize_column: Resize a column to fit content
- preserve_column_widths: Preserve column widths between view changes
- refresh_restock_list_after_update: Refresh the restock list after changes

Modified: August 6, 2025
"""

import pyodbc
import decimal
import os
from datetime import datetime

from backend.database import get_connector, get_db_path


def load_restock_list(access_db_path: str | None = None, treeview=None):
    """Populate the restock Treeview with items whose STATUS is Low/Out of Stock.

    Centralized DB path resolution via get_db_path / get_connector.
    """
    if treeview is None:
        print("[WARNING] load_restock_list called without a treeview")
        return
    if access_db_path is None:
        access_db_path = get_db_path()
    if not os.path.exists(access_db_path):
        print(f"[ERROR] Restock list DB file not found: {access_db_path}")
        return
    conn = None
    cursor = None
    try:
        connector = get_connector(access_db_path)
        conn = connector.connect()
        cursor = conn.cursor()
        columns = [
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
        # Attempt prioritized query with Access-specific IIf ordering
        rows = []
        try:
            cursor.execute(
                """
                SELECT NAME, BRAND, TYPE, LOCATION, [UNIT OF MEASURE], STATUS,
                       [IN], OUT, BALANCE, [MIN STOCK], DEFICIT, [PRICE PER UNIT], COST, [LAST PO], SUPPLIER,
                       IIf(STATUS='Out of Stock',1,IIf(STATUS='Low in Stock',2,3)) AS SortOrder
                FROM ITEMSDB
                WHERE STATUS IN ('Out of Stock','Low in Stock')
                ORDER BY SortOrder, NAME
                """
            )
            raw = cursor.fetchall()
            if raw:
                rows = [r[:-1] for r in raw]  # strip SortOrder
                print(f"[DEBUG] Restock (IIf) rows: {len(rows)}")
        except Exception as primary_err:
            print(f"[WARNING] IIf ordering failed: {primary_err}; falling back")
            try:
                cursor.execute(
                    """
                    SELECT NAME, BRAND, TYPE, LOCATION, [UNIT OF MEASURE], STATUS,
                           [IN], OUT, BALANCE, [MIN STOCK], DEFICIT, [PRICE PER UNIT], COST, [LAST PO], SUPPLIER
                    FROM ITEMSDB
                    WHERE STATUS IN ('Out of Stock','Low in Stock')
                    """
                )
                raw = cursor.fetchall()

                def status_key(r):
                    status = r[5]
                    if status == "Out of Stock":
                        return (0, r[0])
                    if status == "Low in Stock":
                        return (1, r[0])
                    return (2, r[0])

                rows = sorted(raw, key=status_key)
                print(f"[DEBUG] Restock (fallback) rows: {len(rows)}")
            except Exception as fallback_err:
                print(f"[ERROR] Restock queries failed entirely: {fallback_err}")
                rows = []

        # Clear existing content
        for rid in treeview.get_children():
            treeview.delete(rid)

        treeview["columns"] = columns
        widths = {
            "NAME": 180,
            "BRAND": 120,
            "TYPE": 120,
            "LOCATION": 120,
            "UNIT OF MEASURE": 120,
            "STATUS": 100,
            "IN": 80,
            "OUT": 80,
            "BALANCE": 80,
            "MIN STOCK": 90,
            "DEFICIT": 80,
            "PRICE PER UNIT": 120,
            "COST": 120,
            "LAST PO": 120,
            "SUPPLIER": 150,
        }
        for col in columns:
            treeview.heading(
                col,
                text=col,
                anchor="center",
                command=lambda c=col: sort_restock_column(treeview, c),
            )
            anchor = (
                "center"
                if col in {"IN", "OUT", "BALANCE", "MIN STOCK", "DEFICIT", "STATUS"}
                else ("e" if col in {"PRICE PER UNIT", "COST"} else "w")
            )
            treeview.column(
                col,
                width=widths.get(col, 100),
                anchor=anchor,
                minwidth=60,
                stretch=False,
            )

        treeview.bind(
            "<Button-3>", lambda e: auto_resize_column_on_right_click(e, treeview)
        )

        for row in rows:
            treeview.insert("", "end", values=format_row(row, columns))
        print(f"[DEBUG] Restock list loaded successfully: {len(rows)} rows")
    except pyodbc.Error as db_err:
        print(f"[ERROR] Database error loading restock list: {db_err}")
    except Exception as e:
        print(f"[ERROR] Unexpected restock load error: {e}")
    finally:
        try:
            if cursor:
                cursor.close()
        except Exception:
            pass
        try:
            if conn:
                conn.close()
        except Exception:
            pass


def format_row(row, columns):
    """
    Format a row of data for display in the Treeview.

    Args:
        row (tuple): A row of data from the database.
        columns (list): List of column names to determine formatting.

    Returns:
        list: A formatted row.
    """
    formatted = []

    # Find indices of special columns
    price_col_idx = None
    cost_col_idx = None
    date_col_idx = None

    for i, col_name in enumerate(columns):
        if col_name == "PRICE PER UNIT":
            price_col_idx = i
        elif col_name == "COST":
            cost_col_idx = i
        elif col_name == "LAST PO":
            date_col_idx = i

    for i, value in enumerate(row):
        if value is None:
            formatted.append("")
        elif isinstance(value, decimal.Decimal):
            # Format numeric values - add currency symbol for price and cost columns
            if i == price_col_idx or i == cost_col_idx:
                formatted.append(f"₱{float(value):,.2f}")
            else:
                # For other decimal values, check if they're whole numbers
                float_val = float(value)
                if float_val.is_integer():
                    formatted.append(f"{int(float_val):,}")  # Show as whole number
                else:
                    formatted.append(f"{float_val:,.2f}")
        elif isinstance(value, (int, float)):
            # Format numeric values - add currency symbol for price and cost columns
            if i == price_col_idx or i == cost_col_idx:
                formatted.append(f"₱{value:,.2f}")
            else:
                # For other numeric values, check if they're whole numbers
                if isinstance(value, int) or (
                    isinstance(value, float) and value.is_integer()
                ):
                    formatted.append(f"{int(value):,}")  # Show as whole number
                else:
                    formatted.append(f"{value:,.2f}")
        elif i == date_col_idx:  # LAST PO (date) column
            # Format date to show only date, no time
            if isinstance(value, str):
                try:
                    # Try to parse the date from string and format it
                    if "/" in value:
                        # Already formatted as date
                        formatted.append(
                            value.split()[0]
                        )  # Take only date part if there's time
                    else:
                        # Try to parse different date formats
                        try:
                            date = datetime.strptime(value.split()[0], "%Y-%m-%d")
                            formatted.append(date.strftime("%Y/%m/%d"))
                        except ValueError:
                            try:
                                date = datetime.strptime(value.split()[0], "%m/%d/%Y")
                                formatted.append(date.strftime("%Y/%m/%d"))
                            except ValueError:
                                formatted.append(
                                    value.split()[0]
                                )  # Just remove time if present
                except (ValueError, IndexError):
                    formatted.append(str(value))
            else:
                # For datetime objects
                try:
                    formatted.append(value.strftime("%Y/%m/%d"))
                except (AttributeError, ValueError):
                    formatted.append(str(value))
        else:
            # Strip unnecessary quotes or characters from strings
            formatted.append(str(value).strip("'\""))
    return formatted


def sort_restock_column(treeview, col):
    """Sort restock list by column with proper data type handling."""
    try:
        # Check if we need to refresh the data from the database
        # We can avoid refreshing when sorting to improve performance
        print("[DEBUG] Sorting restock data by column", col)

        # Check if treeview has sort state tracking
        if not hasattr(treeview, "_sort_states"):
            treeview._sort_states = {}

        # Initialize sort state for column if not exists
        if col not in treeview._sort_states:
            treeview._sort_states[col] = False

        # Toggle sort state
        treeview._sort_states[col] = not treeview._sort_states[col]
        reverse = treeview._sort_states[col]

        # Get all items
        items = [(treeview.set(k, col), k) for k in treeview.get_children("")]

        # Define numeric columns
        numeric_columns = [
            "IN",
            "OUT",
            "BALANCE",
            "MIN STOCK",
            "DEFICIT",
            "PRICE PER UNIT",
            "COST",
        ]

        # Convert values for sorting
        def convert_value(value):
            if not value:
                return 0 if col in numeric_columns else ""

            if col in numeric_columns:
                # Remove currency symbols and commas for numeric columns
                cleaned = str(value).replace("₱", "").replace(",", "").strip()
                try:
                    return float(cleaned)
                except ValueError:
                    return 0
            return str(value).lower()  # Case-insensitive string sorting

        # Sort items
        items.sort(key=lambda x: convert_value(x[0]), reverse=reverse)

        # Rearrange items in sorted positions
        for index, (_, k) in enumerate(items):
            treeview.move(k, "", index)

        # Update column header to show sort indicator
        indicator = " ▼" if reverse else " ▲"
        header_text = col.split(" ▼")[0].split(" ▲")[0]  # Remove existing indicators
        treeview.heading(col, text=f"{header_text}{indicator}")

        # Remove indicators from other columns
        for other_col in treeview["columns"]:
            if other_col != col:
                other_header_text = other_col.split(" ▼")[0].split(" ▲")[0]
                treeview.heading(
                    other_col,
                    text=other_header_text,
                    command=lambda c=other_col: sort_restock_column(treeview, c),
                )

        # Reset the current column command to maintain sorting functionality
        current_header_text = col.split(" ▼")[0].split(" ▲")[0]
        treeview.heading(
            col,
            text=f"{current_header_text}{indicator}",
            command=lambda c=col: sort_restock_column(treeview, c),
        )

        print(
            f"[DEBUG] Sorted restock list by {col} ({'descending' if reverse else 'ascending'})"
        )

    except Exception as e:
        print(f"[ERROR] Failed to sort by column {col}: {e}")


def auto_resize_column_on_right_click(event, treeview):
    """Auto-resize column to fit content when right-clicking on header."""
    try:
        # We no longer need to refresh data before resizing columns
        # This avoids unnecessary database queries and improves performance

        # Determine which column was clicked
        region = treeview.identify_region(event.x, event.y)
        if region == "heading":
            column = treeview.identify_column(event.x, event.y)
            if column:
                # Convert column identifier to column name
                col_index = int(column.replace("#", "")) - 1
                if col_index >= 0 and col_index < len(treeview["columns"]):
                    col_name = treeview["columns"][col_index]
                    auto_resize_column(treeview, col_name)
    except Exception as e:
        print(f"[ERROR] Failed to auto-resize column: {e}")


def auto_resize_column(treeview, col_name):
    """Auto-resize a specific column to fit its content."""
    try:
        import tkinter.font as tkfont

        # Get the font used in the treeview
        try:
            font = tkfont.nametofont(treeview.cget("font"))
        except Exception:
            font = tkfont.Font()

        # Calculate header width
        header_width = font.measure(col_name) + 40  # Extra padding for header

        # Find maximum content width in this column
        max_width = header_width
        for item in treeview.get_children():
            value = str(treeview.set(item, col_name))
            content_width = font.measure(value) + 20  # Extra padding for content
            max_width = max(max_width, content_width)

        # Set minimum and maximum reasonable widths
        min_width = 60
        max_reasonable_width = 400  # Prevent extremely wide columns
        final_width = max(min_width, min(max_width, max_reasonable_width))

        # Apply the new width
        treeview.column(col_name, width=final_width)
        print(f"[DEBUG] Auto-resized column '{col_name}' to width {final_width}")

    except Exception as e:
        print(f"[ERROR] Failed to auto-resize column {col_name}: {e}")


def preserve_column_widths(treeview):
    """
    Preserve column widths before switching views.
    This function is called by tab_buttons.py to maintain column widths
    when switching to the restock list view.

    Args:
        treeview (ttk.Treeview): The Treeview widget whose column widths to preserve.
    """
    try:
        # Simplified - just ensure columns can be resized properly
        if (
            not treeview
            or not hasattr(treeview, "winfo_exists")
            or not treeview.winfo_exists()
        ):
            print("[DEBUG] Treeview not available for column width preservation")
            return

        # Don't store widths as it interferes with column resizing
        print("[DEBUG] Column width preservation - allowing normal column behavior")

    except Exception as e:
        print(f"[WARNING] Failed to preserve column widths: {e}")


def refresh_restock_list_after_update(access_db_path, treeview, delay_ms=100):
    """Lightweight deferred refresh that simply re-invokes load_restock_list after delay."""

    def delayed_refresh():
        try:
            print("[DEBUG] Deferred restock refresh executing...")
            load_restock_list(access_db_path, treeview)
        except Exception as e:
            print(f"[ERROR] Deferred restock refresh failed: {e}")

    if hasattr(treeview, "after"):
        treeview.after(delay_ms, delayed_refresh)
    else:
        delayed_refresh()
