from tkinter import messagebox, filedialog
from openpyxl import Workbook
import csv
from datetime import datetime

def export_to_xlsx(table, current_view):
    """Export the currently visible data in the Treeview to an Excel file."""
    try:
        # Get the data currently displayed in the Treeview
        columns = table["columns"]
        rows = [table.item(row_id, "values") for row_id in table.get_children()]

        if not rows:
            messagebox.showwarning("Warning", "No data to export.")
            return

        # Get the current date for the filename
        current_date = datetime.now().strftime("%m-%d-%Y")

        # Determine the default filename based on the current view
        if current_view == "Restock List":
            default_filename = f"JJCIMS RESTOCK LIST - {current_date}.xlsx"
        elif current_view == "Admin Logs":
            default_filename = f"JJCIMS ADMIN LOGS - {current_date}.xlsx"
        elif current_view == "Employee Logs":
            default_filename = f"JJCIMS EMPLOYEE LOGS - {current_date}.xlsx"
        else:
            default_filename = f"Exported Data - {current_date}.xlsx"

        # Ask the user where to save the file
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            title="Export Data",
            initialfile=default_filename
        )

        if not file_path:
            return  # User canceled the save dialog

        # Write the data to an Excel file using openpyxl
        wb = Workbook()
        ws = wb.active
        ws.title = "Exported Data"

        # Write the column headers
        ws.append(columns)

        # Write the rows
        for row in rows:
            ws.append(row)

        # Save the workbook
        wb.save(file_path)
        messagebox.showinfo("Success", f"Data exported successfully to {file_path}!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to export data: {e}")


def export_to_csv(table, current_view):
    """Export the currently visible data in the Treeview to a CSV file."""
    try:
        columns = table["columns"]
        rows = [table.item(row_id, "values") for row_id in table.get_children()]

        if not rows:
            messagebox.showwarning("Warning", "No data to export.")
            return

        # Get the current date for the filename
        current_date = datetime.now().strftime("%m-%d-%Y")

        # Determine the default filename based on the current view
        if current_view == "ITEMSDB":
            default_filename = f"JJCFPIS ITEMSDB - {current_date}.csv"
        elif current_view == "Logs":
            default_filename = f"JJCFPIS LOGS - {current_date}.csv"
        else:
            default_filename = f"Exported Data - {current_date}.csv"

        # Ask the user where to save the file
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Export Data",
            initialfile=default_filename
        )

        if not file_path:
            return  # User canceled the save dialog

        with open(file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(columns)
            writer.writerows(rows)

        messagebox.showinfo("Success", f"Data exported successfully to {file_path}!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to export data: {e}")