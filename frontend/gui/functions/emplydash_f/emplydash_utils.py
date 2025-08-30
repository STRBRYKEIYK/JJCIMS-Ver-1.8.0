import threading
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from backend.database import get_connector
from backend.database import queries


def add_tooltip(widget, text):
    tooltip = tk.Toplevel(widget)
    tooltip.withdraw()
    tooltip.overrideredirect(True)
    tooltip_label = tk.Label(
        tooltip,
        text=text,
        font=("Arial", 10),
        bg="yellow",
        relief="solid",
        borderwidth=1,
    )
    tooltip_label.pack()

    def show_tooltip(event):
        x, y, _, _ = widget.bbox("insert")
        x += widget.winfo_rootx() + 25
        y += widget.winfo_rooty() + 25
        tooltip.geometry(f"+{x}+{y}")
        tooltip.deiconify()

    def hide_tooltip(event):
        tooltip.withdraw()

    widget.bind("<Enter>", show_tooltip)
    widget.bind("<Leave>", hide_tooltip)


def focus_next_widget(event):
    event.widget.tk_focusNext().focus()
    return "break"


def update_clock(clock_label, root, update_clock_id_holder):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clock_label.config(text=now)
    update_clock_id_holder[0] = root.after(
        1000, lambda: update_clock(clock_label, root, update_clock_id_holder)
    )


def load_items(db, table, root):
    def load_data():
        try:
            # Use centralized query helper
            # db may be a connector instance or a function; ensure we have connector
            connector = db if hasattr(db, "fetchall") else get_connector()
            rows = queries.fetch_items_for_employee_dashboard(connector)
            # Schedule UI update on main thread
            root.after(0, lambda: update_table(rows))
        except Exception as e:
            print(f"Error: {e}")
            root.after(
                0, lambda: messagebox.showerror("Error", f"Failed to load items: {e}")
            )

    def update_table(rows):
        # Clear and repopulate the table
        for row in table.get_children():
            table.delete(row)
        for row in rows:
            sanitized_row = tuple(
                value if value is not None else "N/A" for value in row
            )
            table.insert("", "end", values=sanitized_row)

    threading.Thread(target=load_data, daemon=True).start()


def filter_items(db, table, category, root):
    cursor = None
    db_connection = None
    try:
        for row in table.get_children():
            table.delete(row)
        if category == "ALL":
            load_items(db, table, root)
        else:
            connector = db if hasattr(db, "fetchall") else get_connector()
            rows = queries.fetch_items_by_type(connector, category)
            for row in rows:
                sanitized_row = tuple(
                    value if value is not None else "N/A" for value in row
                )
                table.insert("", tk.END, values=sanitized_row)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to filter items: {e}")
    finally:
        if cursor:
            cursor.close()
        if db_connection:
            db_connection.close()
