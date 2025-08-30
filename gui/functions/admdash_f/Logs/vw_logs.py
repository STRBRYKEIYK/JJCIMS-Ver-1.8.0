from tkinter import messagebox
from datetime import datetime, date, time
from database import get_connector, get_db_path


def _table_exists(db_path, table_name):
    """Return True if table exists in the Access DB, False otherwise."""
    connector = None
    cursor = None
    try:
        connector = get_connector(db_path)
        conn = connector.connect()
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
        cursor.fetchone()
        return True
    except Exception:
        return False
    finally:
        try:
            if cursor:
                cursor.close()
        except Exception:
            pass
        try:
            if connector:
                connector.close()
        except Exception:
            pass


def _get_table_columns(db_path, table_name):
    """Return a list of column names for the given table (uppercased)."""
    connector = None
    cursor = None
    try:
        connector = get_connector(db_path)
        conn = connector.connect()
        cursor = conn.cursor()
        cols = []
        for c in cursor.columns(table=table_name):
            # pyodbc row object may expose different attribute names
            name = None
            for attr in ("column_name", "COLUMN_NAME"):
                if hasattr(c, attr):
                    val = getattr(c, attr)
                    if val:
                        name = str(val).upper()
                        break
            if name:
                cols.append(name)
        return cols
    except Exception:
        return []
    finally:
        try:
            if cursor:
                cursor.close()
        except Exception:
            pass
        try:
            if connector:
                connector.close()
        except Exception:
            pass


def view_logs(dashboard, logs_path, current_view_callback):
    """Load and display the contents of the Employee Logs sheet in the Treeview with consistent style."""
    from gui.functions.admdash_f.table_utils import create_logs_table
    db_path = get_db_path()
    if not _table_exists(db_path, 'emp_logs'):
        messagebox.showerror("Error", "Employee logs table 'emp_logs' not found in database.")
        return
    connector = None
    cursor = None
    try:
        connector = get_connector(db_path)
        conn = connector.connect()
        cursor = conn.cursor()
        # Determine available columns and select accordingly
        tbl_cols = _get_table_columns(db_path, 'emp_logs')
        if 'DATE' in tbl_cols:
            cursor.execute("SELECT [DATE], [TIME], [NAME], [DETAILS] FROM [emp_logs] ORDER BY [DATE] DESC, [TIME] DESC")
        else:
            cursor.execute("SELECT [TIME], [NAME], [DETAILS] FROM [emp_logs] ORDER BY [TIME] DESC")
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description] if cursor.description else None
        if not columns:
            columns = ['DATE', 'TIME', 'NAME', 'DETAILS'] if 'DATE' in tbl_cols else ['TIME', 'NAME', 'DETAILS']
        create_logs_table(dashboard, columns=columns)
        dashboard.table.delete(*dashboard.table.get_children())
        # Format DATE and TIME columns for display
        def _format_value(col_name, val):
            if val is None:
                return ""
            upper = col_name.upper()
            try:
                if upper == 'DATE':
                    if isinstance(val, datetime):
                        return val.strftime('%Y-%m-%d')
                    if isinstance(val, date):
                        return val.strftime('%Y-%m-%d')
                    # fallback: string, split by space
                    s = str(val)
                    return s.split(' ')[0]
                if upper == 'TIME':
                    if isinstance(val, datetime):
                        return val.strftime('%H:%M:%S')
                    if isinstance(val, time):
                        return val.strftime('%H:%M:%S')
                    # fallback: string, take last part if contains space
                    s = str(val)
                    return s.split(' ')[-1]
            except Exception:
                return str(val)
            return str(val)

        for row in rows:
            formatted_row = []
            for i, col in enumerate(columns):
                col_name = col.upper()
                val = row[i] if i < len(row) else None
                formatted_row.append(_format_value(col_name, val))
            dashboard.table.insert("", "end", values=formatted_row)
        if cursor:
            cursor.close()
        if connector:
            connector.close()

        # Hide stats panel for logs view
        from gui.functions.admdash_f.ML.stats_pnl import set_stats_mode
        set_stats_mode("hidden", dashboard.table, dashboard.total_items_label, dashboard.out_of_stock_label, dashboard.low_stock_label, dashboard.total_cost_label)
        current_view_callback("employees")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load Employee Logs: {e}")

def view_admin_logs(dashboard, logs_path, current_view_callback):
    """Load and display the contents of the Admin Logs sheet in the Treeview with consistent style."""
    from gui.functions.admdash_f.table_utils import create_logs_table
    db_path = get_db_path()
    if not _table_exists(db_path, 'adm_logs'):
        messagebox.showerror("Error", "Admin logs table 'adm_logs' not found in database.")
        return
    connector = None
    cursor = None
    try:
        connector = get_connector(db_path)
        conn = connector.connect()
        cursor = conn.cursor()
        # Determine available columns and select accordingly
        tbl_cols = _get_table_columns(db_path, 'adm_logs')
        if 'DATE' in tbl_cols:
            cursor.execute("SELECT [DATE], [TIME], [USER], [DETAILS] FROM [adm_logs] ORDER BY [DATE] DESC, [TIME] DESC")
        else:
            cursor.execute("SELECT [TIME], [USER], [DETAILS] FROM [adm_logs] ORDER BY [TIME] DESC")
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description] if cursor.description else None
        if not columns:
            columns = ['DATE', 'TIME', 'USER', 'DETAILS'] if 'DATE' in tbl_cols else ['TIME', 'USER', 'DETAILS']
        create_logs_table(dashboard, columns=columns)
        dashboard.table.delete(*dashboard.table.get_children())
        # Format DATE and TIME columns for display
        def _format_value(col_name, val):
            if val is None:
                return ""
            upper = col_name.upper()
            try:
                if upper == 'DATE':
                    if isinstance(val, datetime):
                        return val.strftime('%Y-%m-%d')
                    if isinstance(val, date):
                        return val.strftime('%Y-%m-%d')
                    s = str(val)
                    return s.split(' ')[0]
                if upper == 'TIME':
                    if isinstance(val, datetime):
                        return val.strftime('%H:%M:%S')
                    if isinstance(val, time):
                        return val.strftime('%H:%M:%S')
                    s = str(val)
                    return s.split(' ')[-1]
            except Exception:
                return str(val)
            return str(val)

        for row in rows:
            formatted_row = []
            for i, col in enumerate(columns):
                col_name = col.upper()
                val = row[i] if i < len(row) else None
                formatted_row.append(_format_value(col_name, val))
            dashboard.table.insert("", "end", values=formatted_row)
        if cursor:
            cursor.close()
        if connector:
            connector.close()

        # Hide stats panel for logs view
        from gui.functions.admdash_f.ML.stats_pnl import set_stats_mode
        set_stats_mode("hidden", dashboard.table, dashboard.total_items_label, dashboard.out_of_stock_label, dashboard.low_stock_label, dashboard.total_cost_label)
        current_view_callback("admin")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load Admin Logs: {e}")


def clear_admin_logs(logs_path, dashboard, reset_table_columns, clear_table, set_current_view):
    # Warning before confirmation
    
    # Ask for confirmation
    if not messagebox.askyesno("Confirm Clear", "Are you sure you want to clear all Admin Logs? This action cannot be undone."):
        return
    
    db_path = get_db_path()
    try:
        connector = get_connector(db_path)
        connector.execute_query("DELETE FROM [adm_logs]")
        messagebox.showinfo("Success", "Admin Logs cleared.")
        view_admin_logs(dashboard, db_path, set_current_view)
        if hasattr(dashboard, 'set_current_view'):
            dashboard.set_current_view("Admin Logs")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to clear Admin Logs: {e}")


def clear_employee_logs(logs_path, dashboard, reset_table_columns, clear_table, set_current_view):
    # Warning before confirmation
    
    # Ask for confirmation
    if not messagebox.askyesno("Confirm Clear", "Are you sure you want to clear all Employee Logs? This action cannot be undone."):
        return
    
    db_path = get_db_path()
    try:
        connector = get_connector(db_path)
        connector.execute_query("DELETE FROM [emp_logs]")
        messagebox.showinfo("Success", "Employee Logs cleared.")
        view_logs(dashboard, db_path, set_current_view)
        if hasattr(dashboard, 'set_current_view'):
            dashboard.set_current_view("Employee Logs")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to clear Employee Logs: {e}")