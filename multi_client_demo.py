import tkinter as tk
from tkinter import ttk, messagebox
import os
import threading
import time
from dotenv import load_dotenv
from backend.database import get_connector
from backend.database import queries

# Load environment variables
load_dotenv()

# Dynamically set database type using environment variable
os.environ["JJCIMS_DB_TYPE"] = "mysql"  # Use "access" for local file-based or "mysql" for API



class MultiClientDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("JJCIMS Multi-Client Demo")
        self.geometry("800x600")
        
        # Create a connector to the database
        self.connector = get_connector()
        
        # Create UI elements
        self.create_ui()
        
        # Load initial data
        self.load_data()
        
        # Setup auto-refresh for real-time updates
        self.auto_refresh()
    
    def create_ui(self):
        # Main frame
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Connection info
        db_type = os.environ.get("JJCIMS_DB_TYPE", "access")
        api_url = os.environ.get("JJCIMS_API_URL", "Not configured")
        
        if db_type == "mysql":
            connection_text = f"Connected to: MySQL via API at {api_url}"
        else:
            connection_text = "Connected to: Local Access Database"
        
        connection_label = ttk.Label(main_frame, text=connection_text)
        connection_label.pack(anchor=tk.W, pady=5)
        
        # Tabs
        tab_control = ttk.Notebook(main_frame)
        
        # Items tab
        items_tab = ttk.Frame(tab_control)
        tab_control.add(items_tab, text="Items")
        
        # Create table for items
        columns = ("ID", "Name", "Supplier", "PO#")
        self.items_table = ttk.Treeview(items_tab, columns=columns, show='headings')
        
        # Set column headings
        for col in columns:
            self.items_table.heading(col, text=col)
            self.items_table.column(col, width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(items_tab, orient=tk.VERTICAL, command=self.items_table.yview)
        self.items_table.configure(yscroll=scrollbar.set)
        
        # Pack table and scrollbar
        self.items_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Employee logs tab
        logs_tab = ttk.Frame(tab_control)
        tab_control.add(logs_tab, text="Employee Logs")
        
        # Create table for logs
        log_columns = ("Date", "Time", "Name", "Details")
        self.logs_table = ttk.Treeview(logs_tab, columns=log_columns, show='headings')
        
        # Set column headings for logs
        for col in log_columns:
            self.logs_table.heading(col, text=col)
            self.logs_table.column(col, width=100)
        
        # Add scrollbar for logs
        log_scrollbar = ttk.Scrollbar(logs_tab, orient=tk.VERTICAL, command=self.logs_table.yview)
        self.logs_table.configure(yscroll=log_scrollbar.set)
        
        # Pack logs table and scrollbar
        self.logs_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Pack tab control
        tab_control.pack(expand=1, fill=tk.BOTH)
        
        # Add bottom frame for controls
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=10)
        
        # Add a button to refresh data
        refresh_btn = ttk.Button(bottom_frame, text="Refresh Data", command=self.load_data)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # Add a button to add test log entry
        add_log_btn = ttk.Button(bottom_frame, text="Add Test Log", command=self.add_test_log)
        add_log_btn.pack(side=tk.LEFT, padx=5)
        
        # Add status label
        self.status_label = ttk.Label(bottom_frame, text="Ready")
        self.status_label.pack(side=tk.RIGHT, padx=5)
    
    def load_data(self):
        """Load data from the database"""
        try:
            self.status_label.config(text="Loading data...")
            
            # Clear existing data
            for row in self.items_table.get_children():
                self.items_table.delete(row)
            
            for row in self.logs_table.get_children():
                self.logs_table.delete(row)
            
            # Load items
            items = queries.fetch_items_for_employee_dashboard(self.connector)
            for item in items:
                # Convert None values to empty strings
                sanitized_item = tuple(str(x) if x is not None else "" for x in item)
                self.items_table.insert("", tk.END, values=sanitized_item)
            
            # Load logs
            logs = queries.fetch_emp_logs(self.connector)
            for log in logs:
                # Convert None values to empty strings
                sanitized_log = tuple(str(x) if x is not None else "" for x in log)
                self.logs_table.insert("", tk.END, values=sanitized_log)
            
            self.status_label.config(text=f"Data loaded at {time.strftime('%H:%M:%S')}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {e}")
            self.status_label.config(text="Error loading data")
    
    def add_test_log(self):
        """Add a test log entry to demonstrate real-time updates"""
        try:
            queries.insert_emp_log(self.connector, "Test User", "Added from multi-client demo")
            self.load_data()
            messagebox.showinfo("Success", "Test log added successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add log: {e}")
    
    def auto_refresh(self):
        """Set up automatic refresh of data every 30 seconds"""
        def refresh_loop():
            while True:
                time.sleep(30)
                self.after(0, self.load_data)
        
        # Start auto-refresh in a background thread
        refresh_thread = threading.Thread(target=refresh_loop, daemon=True)
        refresh_thread.start()

if __name__ == "__main__":
    app = MultiClientDashboard()
    app.mainloop()
