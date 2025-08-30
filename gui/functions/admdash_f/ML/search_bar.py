import tkinter as tk
import os
import sys
from database import get_connector

# Define headers and search configurations for each view
VIEW_CONFIGS = {
    "ITEMS_LIST": {
        "headers": [
            "NAME", "BRAND", "TYPE", "LOCATION", "UNIT OF MEASURE", "STATUS", "IN", "OUT", "BALANCE", "MIN STOCK", "DEFICIT", "PRICE PER UNIT", "COST", "LAST PO", "SUPPLIER"
        ],
        "table_name": "ITEMSDB",
        "search_fields": ["NAME", "BRAND", "TYPE", "LOCATION", "UNIT OF MEASURE", "STATUS", "SUPPLIER"],
        "suggestion_field": "NAME"
    },
    "Restock List": {
        "headers": [
            "NAME", "BRAND", "TYPE", "LOCATION", "UNIT OF MEASURE", "STATUS", "IN", "OUT", "BALANCE", "MIN STOCK", "DEFICIT", "PRICE PER UNIT", "COST", "LAST PO", "SUPPLIER"
        ],
        "table_name": "ITEMSDB",  # Changed from 'statssum' to 'ITEMSDB' - same table as Items List
        "search_fields": ["NAME", "BRAND", "TYPE", "LOCATION", "UNIT OF MEASURE", "STATUS", "SUPPLIER"],
        "suggestion_field": "NAME"
    }
}

def _resolve_db_path():
    """Return the first existing canonical ACCDB path (prioritize root /database)."""
    try:
        try:
            from main import get_app_dir
        except ImportError:
            def get_app_dir():
                if getattr(sys, 'frozen', False):
                    return os.path.dirname(sys.executable)
                return os.path.dirname(os.path.abspath(sys.modules['__main__'].__file__)) if '__main__' in sys.modules else os.getcwd()
        app_dir = get_app_dir()
        candidates = [
            os.path.join(app_dir, 'database', 'JJCIMS.accdb'),  # Primary
            os.path.normpath(os.path.join(app_dir, '..', 'database', 'JJCIMS.accdb')),  # Parent (dev setups)
            os.path.normpath(os.path.join(app_dir, 'utils', 'database', 'JJCIMS.accdb')),  # utils mirror (legacy)
        ]
        for p in candidates:
            if os.path.exists(p):
                return p
        # Fallback to first even if missing (will raise later making issue visible)
        return candidates[0]
    except Exception as e:
        print(f"[DEBUG] _resolve_db_path error: {e}")
        return None


def search_items(dashboard, event=None):
    """Content-aware search that adapts to the current view/tab."""
    try:
        keyword = dashboard.search_entry.get().strip()
        
        # Get current view from dashboard
        current_view = getattr(dashboard, 'current_view', 'ITEMS_LIST')
        print(f"[DEBUG] Search initiated - Current view: {current_view}, Keyword: '{keyword}'")
        
        # Check if current view supports search
        if current_view not in VIEW_CONFIGS:
            print(f"[DEBUG] View '{current_view}' not found in VIEW_CONFIGS")
            if hasattr(dashboard, 'suggestions_popup'):
                dashboard.suggestions_popup.withdraw()
            return
        
        config = VIEW_CONFIGS[current_view]
        headers = config["headers"]
        table_name = config["table_name"]
        search_fields = config["search_fields"]
        suggestion_field = config["suggestion_field"]
        
        print(f"[DEBUG] Using table: {table_name}, Search fields: {search_fields}")
        
        if not keyword:
            if hasattr(dashboard, 'suggestions_popup'):
                dashboard.suggestions_popup.withdraw()
            # Reload appropriate data based on current view
            try:
                if current_view == "ITEMS_LIST":
                    dashboard.load_data()
                elif current_view == "Restock List":
                    # For restock list, we need to reload using the VRL function
                    print("[DEBUG] Reloading restock list data...")
                    from gui.functions.admdash_f.vrl import load_restock_list
                    db_path = _resolve_db_path()
                    if db_path and os.path.exists(db_path):
                        print(f"[DEBUG] Restock reload db: {db_path}")
                        load_restock_list(db_path, dashboard.table)
                    else:
                        print("[ERROR] Restock reload: database path unresolved")
            except Exception as e:
                print(f"Error reloading data: {e}")
                import traceback
                traceback.print_exc()
            return
        
        try:
            # Always create a new connection for search to avoid closed connection issues
            db_path = _resolve_db_path()
            if not db_path:
                print("[ERROR] Could not resolve database path")
                return
            if not os.path.exists(db_path):
                print(f"[ERROR] Database path does not exist: {db_path}")
                return
            print(f"[DEBUG] Search using database: {db_path}")
            
            # Always create fresh connection for search
            db = get_connector(str(db_path))
            connection = db.connect()
            cursor = connection.cursor()
            
            # Fetch suggestions from the database
            try:
                # Print actual columns for Restock List debug
                if current_view == "Restock List":
                    cursor.execute(f"SELECT TOP 1 * FROM [{table_name}]")
                    col_names = [desc[0] for desc in cursor.description]
                    print(f"[DEBUG] Restock columns: {col_names}")
                # Validate suggestion_query
                suggestion_query = f"SELECT DISTINCT [{suggestion_field}] FROM [{table_name}] WHERE LCASE([{suggestion_field}]) LIKE ?"
                cursor.execute(suggestion_query, (f"%{keyword.lower()}%",))
                suggestions = cursor.fetchall()
            except Exception as e:
                print(f"Database error in suggestion query: {e}")
                suggestions = []

            if hasattr(dashboard, 'suggestions_listbox'):
                dashboard.suggestions_listbox.delete(0, tk.END)
                for suggestion in suggestions:
                    if suggestion and suggestion[0]:
                        dashboard.suggestions_listbox.insert(tk.END, suggestion[0])

            if suggestions and hasattr(dashboard, 'suggestions_popup'):
                try:
                    x = dashboard.search_entry.winfo_rootx()
                    y = dashboard.search_entry.winfo_rooty() + dashboard.search_entry.winfo_height()
                    dashboard.suggestions_popup.geometry(f"{dashboard.search_entry.winfo_width()}x150+{x}+{y}")
                    dashboard.suggestions_popup.deiconify()
                except Exception as e:
                    print(f"Error showing suggestions popup: {e}")
            elif hasattr(dashboard, 'suggestions_popup'):
                dashboard.suggestions_popup.withdraw()

            try:
                # Validate filter_query
                column_list = ", ".join([f"[{col}]" for col in headers])
                
                # Build case-insensitive search conditions
                conditions = []
                params = []
                
                # Split search terms and search each field
                search_terms = keyword.lower().split()
                print(f"[DEBUG] Search terms: {search_terms}")
                for field in search_fields:
                    for term in search_terms:
                        conditions.append(f"LCASE([{field}]) LIKE ?")
                        params.append(f"%{term}%")
                
                # Combine conditions with OR
                where_conditions = " OR ".join(conditions)
                filter_query = f"SELECT {column_list} FROM [{table_name}] WHERE {where_conditions}"
                print(f"[DEBUG] Filter query: {filter_query}")
                print(f"[DEBUG] Query params count: {len(params)}")
                
                try:
                    cursor.execute(filter_query, params)
                    rows = cursor.fetchall()
                    
                    # For Restock List, we need to filter the results to only show items needing restocking
                    if current_view == "Restock List":
                        # Filter in Python to only include items that need restocking
                        status_index = headers.index("STATUS") if "STATUS" in headers else -1
                        balance_index = headers.index("BALANCE") if "BALANCE" in headers else -1
                        min_stock_index = headers.index("MIN STOCK") if "MIN STOCK" in headers else -1
                        
                        filtered_rows = []
                        for row in rows:
                            if len(row) > status_index and status_index >= 0:
                                status = str(row[status_index]).lower() if row[status_index] else ""
                                if status and ("out of stock" in status or "low in stock" in status):
                                    filtered_rows.append(row)
                                    continue
                                    
                            if balance_index >= 0 and min_stock_index >= 0 and len(row) > max(balance_index, min_stock_index):
                                balance = row[balance_index] if row[balance_index] not in (None, "") else 0
                                min_stock = row[min_stock_index] if row[min_stock_index] not in (None, "") else 0
                                try:
                                    balance = float(balance) if balance else 0
                                    min_stock = float(min_stock) if min_stock else 0
                                    if balance <= min_stock:
                                        filtered_rows.append(row)
                                except (ValueError, TypeError):
                                    # Skip if we can't convert to numbers
                                    pass
                        
                        rows = filtered_rows
                    
                    print(f"[DEBUG] Initial search found {len(rows)} rows")
                except Exception as ex:
                    print(f"Database error in filter query: {ex}")
                    import traceback
                    traceback.print_exc()
                    rows = []
                
                # If no results, try more flexible matching
                if not rows:
                    print("[DEBUG] No initial results, trying flexible search...")
                    # Try each word separately with more flexible wildcards
                    conditions = []
                    params = []
                    search_terms = keyword.lower().split()
                    
                    for field in search_fields:
                        for term in search_terms:
                            # Add start-with, contains, and end-with patterns
                            conditions.append(f"LCASE([{field}]) LIKE ?")
                            params.append(f"{term}%")  # Starts with
                            conditions.append(f"LCASE([{field}]) LIKE ?")
                            params.append(f"%{term}")  # Ends with
                            conditions.append(f"LCASE([{field}]) LIKE ?")
                            params.append(f"%{term}%")  # Contains
                    
                    where_conditions = " OR ".join(conditions)
                    filter_query = f"SELECT {column_list} FROM [{table_name}] WHERE {where_conditions}"
                    print(f"[DEBUG] Flexible query: {filter_query}")
                    
                    try:
                        cursor.execute(filter_query, params)
                        rows = cursor.fetchall()
                        
                        # Apply same filtering for Restock List view
                        if current_view == "Restock List" and rows:
                            status_index = headers.index("STATUS") if "STATUS" in headers else -1
                            balance_index = headers.index("BALANCE") if "BALANCE" in headers else -1
                            min_stock_index = headers.index("MIN STOCK") if "MIN STOCK" in headers else -1
                            
                            filtered_rows = []
                            for row in rows:
                                if len(row) > status_index and status_index >= 0:
                                    status = str(row[status_index]).lower() if row[status_index] else ""
                                    if status and ("out of stock" in status or "low in stock" in status):
                                        filtered_rows.append(row)
                                        continue
                                        
                                if balance_index >= 0 and min_stock_index >= 0 and len(row) > max(balance_index, min_stock_index):
                                    balance = row[balance_index] if row[balance_index] not in (None, "") else 0
                                    min_stock = row[min_stock_index] if row[min_stock_index] not in (None, "") else 0
                                    try:
                                        balance = float(balance) if balance else 0
                                        min_stock = float(min_stock) if min_stock else 0
                                        if balance <= min_stock:
                                            filtered_rows.append(row)
                                    except (ValueError, TypeError):
                                        # Skip if we can't convert to numbers
                                        pass
                            
                            rows = filtered_rows
                        
                        print(f"[DEBUG] Flexible search found {len(rows)} rows")
                    except Exception as ex:
                        print(f"Database error in flexible filter query: {ex}")
                        import traceback
                        traceback.print_exc()
                        rows = []
            except Exception as e:
                print(f"Database error in filter query: {e}")
                rows = []

            if dashboard.table:
                # Clear existing data
                dashboard.table.delete(*dashboard.table.get_children())
                print(f"[DEBUG] Cleared table, populating with {len(rows)} rows")

                # Reset columns to match headers for current view
                dashboard.table["columns"] = headers
                # Always use "tree headings" to maintain checkbox functionality
                dashboard.table["show"] = "tree headings"
                
                # Configure headers and columns
                for col in headers:
                    dashboard.table.heading(col, text=col)
                    # Apply appropriate column styling based on view
                    if current_view in ["ITEMS_LIST"]:
                        if col in ["Stock", "Stock out", "Balance", "Min Stock", "Deficit", "Status"]:
                            dashboard.table.column(col, anchor="center", width=100)
                        else:
                            dashboard.table.column(col, anchor="w", width=150)
                        # For Materials List, also set up sorting
                        if hasattr(dashboard, 'sort_by_column'):
                            dashboard.table.heading(col, command=lambda _col=col: dashboard.sort_by_column(_col, False))
                    elif current_view == "Restock List":
                        if col in ["Stock out", "Balance", "Min Stock", "Deficit"]:
                            dashboard.table.column(col, anchor="center", width=100)
                        elif col == "Status":
                            dashboard.table.column(col, anchor="center", width=100)
                        else:
                            dashboard.table.column(col, anchor="w", width=150)
                
                # Insert filtered rows and preserve checkbox states
                for i, row in enumerate(rows):
                    # Format the row appropriately based on current view
                    if current_view == "Restock List":
                        # Use the formatting function from vrl.py for consistent formatting
                        try:
                            from gui.functions.admdash_f.vrl import format_row
                            sanitized_row = tuple(format_row(row, headers))
                            print(f"[DEBUG] Row {i}: Formatted - {sanitized_row}")
                        except ImportError as ie:
                            print(f"[DEBUG] Import error for format_row: {ie}")
                            # Fallback to basic sanitization if vrl.py not available
                            sanitized_row = tuple(value if value is not None else "" for value in row)
                            print(f"[DEBUG] Row {i}: Basic format - {sanitized_row}")
                        except Exception as fe:
                            print(f"[DEBUG] Format error for row {i}: {fe}")
                            sanitized_row = tuple(value if value is not None else "" for value in row)
                    else:
                        # For other views, use basic sanitization
                        sanitized_row = tuple(value if value is not None else "" for value in row)
                    
                    # For CheckboxTreeview
                    if hasattr(dashboard.table, '_checked_items'):
                        # Create a unique identifier for the row (using first column/NAME)
                        row_id = dashboard.table.insert("", tk.END, values=sanitized_row)
                        # Check if this item was previously checked
                        if sanitized_row[0] in [dashboard.table.item(item)['values'][0] 
                                              for item in dashboard.table._checked_items]:
                            dashboard.table.change_state(row_id, "checked")
                    else:
                        dashboard.table.insert("", tk.END, values=sanitized_row)
                
                print(f"[DEBUG] Search complete: populated table with {len(rows)} filtered results")
                # If in ITEMS_LIST and no rows found for a single-term search, force a quick refresh then retry once (handles race after add)
                if current_view == "ITEMS_LIST" and len(rows) == 0 and len(keyword.split()) == 1:
                    try:
                        dashboard.load_data()
                        # Retry simple exact match
                        cursor.close()
                        try:
                            connection.close()
                        except Exception:
                            pass
                        db_path_retry = _resolve_db_path()
                        if db_path_retry and os.path.exists(db_path_retry):
                            db_retry = get_connector(str(db_path_retry))
                            connection_retry = db_retry.connect()
                            cur2 = connection_retry.cursor()
                            cur2.execute(f"SELECT {', '.join([f'[{c}]' for c in headers])} FROM [{table_name}] WHERE LCASE([{suggestion_field}]) = ?", (keyword.lower(),))
                            retry_rows = cur2.fetchall()
                            if retry_rows:
                                print(f"[DEBUG] Retry found {len(retry_rows)} rows; updating table")
                                for item in dashboard.table.get_children():
                                    dashboard.table.delete(item)
                                for r in retry_rows:
                                    sanitized = tuple(v if v is not None else '' for v in r)
                                    dashboard.table.insert('', tk.END, values=sanitized)
                            cur2.close()
                            try:
                                connection_retry.close()
                            except Exception:
                                pass
                    except Exception as re:
                        print(f"[DEBUG] Retry after add failed: {re}")
                    
        except Exception as e:
            print(f"Database error in search: {e}")
            import traceback
            traceback.print_exc()
            if hasattr(dashboard, 'status_label'):
                dashboard.status_label.config(text=f"Error: Failed to search items: {e}", fg="#D72631")
        finally:
            try:
                if 'cursor' in locals():
                    cursor.close()
                if 'connection' in locals():
                    try:
                        connection.close()
                    except Exception:
                        pass
            except Exception:
                pass
                
    except Exception as e:
        print(f"Search error: {e}")
        import traceback
        traceback.print_exc()

def select_suggestion(dashboard, event=None):
    """Handle the selection of a suggestion."""
    try:
        if hasattr(dashboard, 'suggestions_listbox') and dashboard.suggestions_listbox.curselection():
            selected = dashboard.suggestions_listbox.get(dashboard.suggestions_listbox.curselection())
            dashboard.search_entry.delete(0, tk.END)
            dashboard.search_entry.insert(0, selected)
            if hasattr(dashboard, 'suggestions_popup'):
                dashboard.suggestions_popup.withdraw()
            search_items(dashboard)
    except Exception as e:
        print(f"Error selecting suggestion: {e}")
        if hasattr(dashboard, 'suggestions_popup'):
            dashboard.suggestions_popup.withdraw()

def show_search_bar(dashboard):
    """Show the search bar if the current view supports search."""
    current_view = getattr(dashboard, 'current_view', 'ITEMS_LIST')
    if current_view in VIEW_CONFIGS:
        if hasattr(dashboard, 'search_container'):
            dashboard.search_container.pack(side=tk.RIGHT, padx=(30, 10), pady=5)  # Increased left padding for longer search bar

def hide_search_bar(dashboard):
    """Hide the search bar for views that don't support search."""
    if hasattr(dashboard, 'search_container'):
        dashboard.search_container.pack_forget()
    if hasattr(dashboard, 'suggestions_popup'):
        dashboard.suggestions_popup.withdraw()

def update_search_bar_visibility(dashboard):
    """Update search bar visibility based on current view."""
    current_view = getattr(dashboard, 'current_view', 'ITEMS_LIST')
    if current_view in VIEW_CONFIGS:
        show_search_bar(dashboard)
    else:
        hide_search_bar(dashboard)

def clear_search(dashboard):
    """Clear the search entry and reload original data."""
    if hasattr(dashboard, 'search_entry'):
        dashboard.search_entry.delete(0, tk.END)
    if hasattr(dashboard, 'suggestions_popup'):
        dashboard.suggestions_popup.withdraw()
    search_items(dashboard)  # This will trigger reload since keyword is empty
