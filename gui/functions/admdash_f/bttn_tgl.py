def hide_main_buttons(add_button, update_item_button, delete_button):
    """Hide the main buttons (Add, Update, Delete)."""
    add_button.pack_forget()
    update_item_button.pack_forget()
    delete_button.pack_forget()

def show_main_buttons(add_button, update_item_button, delete_button):
    """Show the main buttons (Add, Update, Delete)."""
    add_button.pack(pady=3)
    update_item_button.pack(pady=3)
    delete_button.pack(pady=3)


def show_export_buttons(export_button, export_csv_button, current_view):
    """Show the export buttons (Excel, CSV) ONLY for Admin Logs, Employee Logs, and Restock List views. Hide everywhere else."""
    print(f"[DEBUG] show_export_buttons called with current_view={current_view}")
    # Always hide first
    if export_button:
        export_button.pack_forget()
    if export_csv_button:
        export_csv_button.pack_forget()
    # Only show in allowed views
    if current_view in ("Admin Logs", "Employee Logs", "Restock List"):
        if export_button:
            print(f"[DEBUG] Showing export_button: {export_button} in view {current_view}")
            export_button.pack(side="bottom", pady=(3, 0), padx=10, anchor="s")
        if export_csv_button:
            print(f"[DEBUG] Showing export_csv_button: {export_csv_button} in view {current_view}")
            export_csv_button.pack(side="bottom", pady=(0, 10), padx=10, anchor="s")

def manage_export_buttons_by_view(export_button, export_csv_button, current_view):
    """Show or hide export buttons based on the current view."""
    if current_view in ("Admin Logs", "Employee Logs"):
        show_export_buttons(export_button, export_csv_button, current_view)
    # Do not hide here; only show in allowed views

def show_delete_log_button(delete_log_button, current_view):
    """Show the delete log button only for Admin Logs and Employee Logs views."""
    if current_view in ("Admin Logs", "Employee Logs"):
        delete_log_button.pack(pady=3)
    else:
        delete_log_button.pack_forget()

def hide_delete_log_button(delete_log_button):
    """Hide the delete log button."""
    delete_log_button.pack_forget()