import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from database import queries
# Removed openpyxl usage; logging now goes to adm_logs table
# Sound imports removed

def delete_item(table, db, update_stats, username="Admin"):
    """Delete the selected material(s) from the JJCIMS database."""
    # Try to get checked items first (for CheckboxTreeview)
    if hasattr(table, 'get_checked'):
        selected_items = table.get_checked()
    else:
        try:
            selected_items = table.selection()
        except tk.TclError:
            selected_items = []  # Widget was destroyed or invalid

    # Ensure selected items are in the current view
    valid_items = set(table.get_children())
    selected_items = [item_id for item_id in selected_items if item_id in valid_items]

    if not selected_items:
        messagebox.showwarning("Warning", "Please select at least one item to delete.")
        return

    confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete the selected material(s)?")
    if not confirm:
        return

    try:
        connection = db.connect()
        cursor = connection.cursor()

        for item_id in selected_items:
            row = table.item(item_id, "values")
            material_to_delete = row[0]  # NAME column
            supplier = row[1] if len(row) > 1 else ""  # SUPPLIER column
            # Use centralized helper
            try:
                queries.delete_item_by_name(db, material_to_delete)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete {material_to_delete}: {e}")
                continue
            table.delete(item_id)
            queries.insert_admin_log(db, username, f"Deleted material: {material_to_delete} from supplier: {supplier}")

        connection.commit()
        messagebox.showinfo("Success", "Selected material(s) deleted successfully!")
        update_stats()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to delete material(s): {e}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()

def _log_admin_action(connection, username, details):
    # Keep a thin shim that uses centralized helper for backward compatibility
    try:
        queries.insert_admin_log(connection, username, details)
    except Exception as e:
        print(f"[LOGGING] Failed to write admin log: {e}")