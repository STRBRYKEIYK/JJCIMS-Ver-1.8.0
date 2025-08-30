import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import time
from database import get_connector, get_db_path

class StatsPanel:
    def __init__(self, parent, table, username=None):
        """Initialize an enhanced statistics panel with auto-sliding info and tips."""
        self.parent = parent
        self.timer = None
        self.next_tip_timer = None
        self.current_tip_index = 0
        self.username = username or "Admin"
        self._is_destroyed = False
        
        # Bind to destroy event to clean up timers
        self.parent.bind("<Destroy>", self._on_destroy)
        
        # Shorter, more focused tips
        self.system_tips = [
            "📋 Use checkboxes for batch actions",
            "🔍 Quick search: Type item name",
            "⚠️ Check Restock List daily",
            "📊 Export data for reports",
            "📉 Monitor low stock items",
            "📱 Keep costs up to date",
            "⏰ Regular inventory checks",
            "💾 Backup data weekly",
            "❗ Check critical items"
        ]
        
        # Create the main stats container with improved styling
        ttk.Separator(parent, orient="horizontal").pack(fill="x", padx=10, pady=5)
        self.stats_frame = tk.Frame(parent, bg="#181c1f")
        self.stats_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # Add user info and datetime header
        header_frame = tk.Frame(self.stats_frame, bg="#181c1f")
        header_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        # User info with icon
        user_frame = tk.Frame(header_frame, bg="#181c1f")
        user_frame.pack(side=tk.LEFT)
        tk.Label(user_frame, text="👤 ", font=("Arial", 10), bg="#181c1f", fg="#4CAF50").pack(side=tk.LEFT)
        tk.Label(user_frame, text=self.username, font=("Arial", 10), bg="#181c1f", fg="#E0E0E0").pack(side=tk.LEFT)
        
        # Date and time with auto-update
        self.datetime_label = tk.Label(header_frame, text="", font=("Arial", 10), bg="#181c1f", fg="#666666")
        self.datetime_label.pack(side=tk.RIGHT)
        self._update_datetime()

        # Create labels with modern styling and icons
        self.total_items_label = self._create_stat_label("📦 Total Items: 0")
        self.out_of_stock_label = self._create_stat_label("❌ Out of Stock: 0")
        self.low_stock_label = self._create_stat_label("⚠️ Low in Stock: 0")
        self.total_balance_label = self._create_stat_label("💰 Total Cost: ₱0")
        
        # Create compact sliding info panel
        self.info_frame = tk.Frame(self.stats_frame, bg="#1e2329", height=25)
        self.info_frame.pack(fill=tk.X, padx=10, pady=(5, 2))
        
        self.tip_label = tk.Label(
            self.info_frame,
            text=self.system_tips[0],
            font=("Arial", 10),
            bg="#1e2329",
            fg="#4CAF50",
            anchor="w",
            padx=5
        )
        self.tip_label.pack(fill=tk.X, expand=True)
        
        # Add last refresh indicator with icon
        self.refresh_label = tk.Label(
            self.stats_frame,
            text="🔄 Last Refresh: Just now",
            font=("Arial", 9),
            bg="#181c1f",
            fg="#666666"
        )
        self.refresh_label.pack(anchor="e", padx=10, pady=(2, 5))

        ttk.Separator(parent, orient="horizontal").pack(fill="x", padx=10, pady=5)

        # Start auto-updates
        self._start_auto_slide()
    
    def _update_datetime(self):
        """Update the date and time display."""
        try:
            # Check if widget still exists
            if self._is_destroyed or not hasattr(self, 'parent') or not self.parent.winfo_exists() or not hasattr(self, 'datetime_label') or not self.datetime_label.winfo_exists():
                return
                
            current_time = time.strftime("%I:%M:%S %p")
            current_date = time.strftime("%B %d, %Y")
            self.datetime_label.config(text=f"🗓️ {current_date} ⌚ {current_time}")
            self.parent.after(1000, self._update_datetime)
        except Exception as e:
            print(f"Error updating datetime: {e}")  # Log the specific error
    
    def _create_stat_label(self, text):
        """Create a styled statistic label with hover effect and tooltip."""
        try:
            if self._is_destroyed or not hasattr(self, 'stats_frame') or not self.stats_frame.winfo_exists():
                return None
                
            frame = tk.Frame(self.stats_frame, bg="#181c1f")
            frame.pack(fill=tk.X, padx=10, pady=2)
            
            label = tk.Label(
                frame,
                text=text,
                font=("Arial", 11, "bold"),
                bg="#181c1f",
                fg="white",
                anchor="w"
            )
            label.pack(side=tk.LEFT)
            
            # Bind hover effects and tooltips
            label.bind("<Enter>", lambda e: self._on_hover(label, True))
            label.bind("<Leave>", lambda e: self._on_hover(label, False))
            
            # Add tooltips based on label type
            if "Total Items" in text:
                self._add_tooltip(label, "Total number of items in inventory")
            elif "Out of Stock" in text:
                self._add_tooltip(label, "Items that need immediate reordering")
            elif "Low in Stock" in text:
                self._add_tooltip(label, "Items below minimum stock level")
            elif "Total Cost" in text:
                self._add_tooltip(label, "Total value of current inventory")
            
            return label
        except Exception as e:
            print(f"Error creating stat label: {e}")  # Log the specific error
            return None
    
    def _add_tooltip(self, widget, text):
        """Add a tooltip to a widget."""
        def show_tooltip(event):
            try:
                # Check if widget still exists
                if self._is_destroyed or not widget.winfo_exists():
                    return
                    
                tooltip = tk.Toplevel()
                tooltip.wm_overrideredirect(True)
                tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
                
                label = tk.Label(tooltip, text=text, justify=tk.LEFT,
                               background="#2C3E50", fg="white",
                               relief="solid", borderwidth=1,
                               font=("Arial", 9), padx=5, pady=2)
                label.pack()
                
                def hide_tooltip():
                    try:
                        if tooltip.winfo_exists():
                            tooltip.destroy()
                    except Exception:
                        pass
                
                widget.tooltip = tooltip
                widget.bind("<Leave>", lambda e: hide_tooltip())
                tooltip.bind("<Leave>", lambda e: hide_tooltip())
            except Exception as e:
                print(f"Error showing tooltip: {e}")  # Log the specific error
        
        widget.bind("<Enter>", show_tooltip)

    def _on_hover(self, label, entering):
        """Handle hover effects for labels."""
        try:
            # Check if widget still exists
            if self._is_destroyed or not label.winfo_exists():
                return
                
            if entering:
                label.config(fg="#4CAF50")  # Green highlight on hover
            else:
                label.config(fg="white")
        except Exception as e:
            print(f"Error in _on_hover: {e}")  # Log the specific error
    
    def _start_auto_slide(self):
        """Start the auto-sliding tips timer."""
        try:
            if self._is_destroyed or not hasattr(self, 'parent') or not self.parent.winfo_exists():
                return
                
            self._slide_tip()
        except Exception as e:
            print(f"Error starting auto slide: {e}")  # Log the specific error
    
    def _slide_tip(self):
        """Slide to the next system tip."""
        try:
            # First check if widget is destroyed
            if self._is_destroyed or not hasattr(self, 'parent') or not self.parent.winfo_exists():
                return
                
            if not hasattr(self, 'tip_label') or not self.tip_label.winfo_exists():
                return
            
            self.current_tip_index = (self.current_tip_index + 1) % len(self.system_tips)
            
            # Create sliding animation
            next_tip = self.system_tips[self.current_tip_index]
            
            def slide_out(pos=100):
                try:
                    # Check for destroyed state before proceeding
                    if self._is_destroyed:
                        return
                    
                    # Make sure self.parent and self.tip_label still exist
                    if not hasattr(self, 'parent') or not hasattr(self, 'tip_label'):
                        return
                    
                    if not self.parent.winfo_exists() or not self.tip_label.winfo_exists():
                        return
                        
                    if pos <= -100:
                        self.tip_label.config(text=next_tip)
                        slide_in()
                    else:
                        self.tip_label.place(relx=pos/100, rely=0, relwidth=1)
                        # Cancel any existing timer
                        if hasattr(self, 'timer') and self.timer:
                            try:
                                self.parent.after_cancel(self.timer)
                            except Exception:
                                pass
                                
                        # Create a named callback that can be canceled if needed
                        # schedule next frame
                        self.timer = self.parent.after(5, lambda: slide_out(pos-10))
                        # Timer ID is just stored as is - no need to set attributes on it
                except Exception as e:
                    print(f"Error in slide_out: {e}")  # Log the specific error
            
            def slide_in(pos=-100):
                try:
                    # Check for destroyed state before proceeding
                    if self._is_destroyed:
                        return
                    
                    # Make sure self.parent and self.tip_label still exist
                    if not hasattr(self, 'parent') or not hasattr(self, 'tip_label'):
                        return
                        
                    if not self.parent.winfo_exists() or not self.tip_label.winfo_exists():
                        return
                        
                    if pos >= 0:
                        self.tip_label.place(relx=0, rely=0, relwidth=1)
                    else:
                        self.tip_label.place(relx=pos/100, rely=0, relwidth=1)
                        # Cancel any existing timer
                        if hasattr(self, 'timer') and self.timer:
                            try:
                                self.parent.after_cancel(self.timer)
                            except Exception:
                                pass
                                
                        # Create a named callback that can be canceled if needed
                        # schedule next frame
                        self.timer = self.parent.after(5, lambda: slide_in(pos+10))
                        # Timer ID is just stored as is - no need to set attributes on it
                except Exception as e:
                    print(f"Error in slide_in: {e}")  # Log the specific error
            
            slide_out()
            
            # Schedule next tip change - cancel any existing timer first
            if hasattr(self, 'next_tip_timer') and self.next_tip_timer:
                try:
                    self.parent.after_cancel(self.next_tip_timer)
                except Exception:
                    pass
            
            self.next_tip_timer = self.parent.after(30000, self._slide_tip)
        except Exception as e:
            print(f"Error in _slide_tip: {e}")  # Log the specific error
    
    def update_stats(self, stats):
        """Update the statistics display with animation."""
        try:
            # Check if widget is destroyed
            if self._is_destroyed or not hasattr(self, 'parent') or not self.parent.winfo_exists():
                return
                
            if not stats:
                return
                
            self._animate_update(self.total_items_label, f"Total Items: {stats['total_items']}")
            self._animate_update(self.out_of_stock_label, f"Out of Stock: {stats['out_of_stock']}")
            self._animate_update(self.low_stock_label, f"Low in Stock: {stats['low_stock']}")
            
            if 'total_cost' in stats:
                self._animate_update(self.total_balance_label, f"Total Cost: ₱{stats['total_cost']:,.2f}")
            
            # Update refresh time
            if hasattr(self, 'refresh_label') and self.refresh_label.winfo_exists():
                self.refresh_label.config(text=f"Last Refresh: {time.strftime('%I:%M:%S %p')}")
        except Exception as e:
            print(f"Error in update_stats: {e}")  # Log the specific error
    
    def _animate_update(self, label, new_text):
        """Animate the update of a statistic."""
        try:
            # Check if widgets still exist
            if self._is_destroyed or not hasattr(self, 'parent') or not self.parent.winfo_exists():
                return
                
            if not label or not label.winfo_exists():
                return
                
            current = label.cget("text")
            if current != new_text:
                label.config(fg="#4CAF50")  # Highlight change in green
                label.config(text=new_text)
                
                # Define a callback function that checks if widget exists
                def reset_color():
                    try:
                        if not self._is_destroyed and label.winfo_exists():
                            label.config(fg="white")
                    except Exception:
                        pass
                
                self.parent.after(1000, reset_color)
        except Exception as e:
            print(f"Error in _animate_update: {e}")  # Log the specific error

    def _on_destroy(self, event=None):
        """Handle widget destruction event."""
        if event and event.widget == self.parent:
            self._is_destroyed = True
            self.cleanup()
    
    def cleanup(self):
        """Cleanup timers when the panel is destroyed."""
        try:
            if hasattr(self, 'timer') and self.timer:
                try:
                    self.parent.after_cancel(self.timer)
                except Exception:
                    pass
                self.timer = None
                
            if hasattr(self, 'next_tip_timer') and self.next_tip_timer:
                try:
                    self.parent.after_cancel(self.next_tip_timer)
                except Exception:
                    pass
                self.next_tip_timer = None
                
        except Exception as e:
            print(f"Error during cleanup: {e}")  # Log the specific error

def add_stats_panel(parent, table, username=None):
    """Create and return a new StatsPanel instance."""
    panel = StatsPanel(parent, table, username=username)
    return panel.total_items_label, panel.out_of_stock_label, panel.low_stock_label, panel.total_balance_label

def safe_int(val):
    try:
        return int(val)
    except Exception:
        return 0

def get_db_stats(db_path=None, mode="ITEMS_LIST"):
    """Get statistics directly from ITEMSDB table.

    If db_path is None, resolve centrally using database.get_db_path().
    """
    try:
        if db_path is None:
            db_path = get_db_path()
        db = get_connector(db_path)
        connection = db.connect()
        cursor = connection.cursor()

        stats = {}
        normalized_mode = "ITEMS_LIST" if mode in ("default", "ITEMS_LIST") else mode

        if normalized_mode == "ITEMS_LIST":
            cursor.execute("SELECT COUNT(*) FROM ITEMSDB")
            stats['total_items'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM ITEMSDB WHERE Status='Out of Stock'")
            stats['out_of_stock'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM ITEMSDB WHERE Status='Low in Stock'")
            stats['low_stock'] = cursor.fetchone()[0]

            cursor.execute("SELECT SUM(Cost) FROM ITEMSDB")
            total_cost = cursor.fetchone()[0]
            stats['total_cost'] = total_cost if total_cost else 0

        elif normalized_mode == "Restock List":
            cursor.execute("SELECT COUNT(*) FROM ITEMSDB WHERE Status IN ('Low in Stock', 'Out of Stock')")
            stats['total_restock'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM ITEMSDB WHERE Status='Low in Stock'")
            stats['low_stock'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM ITEMSDB WHERE Status='Out of Stock'")
            stats['out_of_stock'] = cursor.fetchone()[0]

            cursor.execute("SELECT SUM(Cost) FROM ITEMSDB")
            total_cost = cursor.fetchone()[0]
            stats['total_cost'] = total_cost if total_cost else 0

        return stats
    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to get statistics: {e}")
        return None
    finally:
        try:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()
        except Exception:
            pass

def update_stats(table, total_items_label, out_of_stock_label, low_stock_label, total_balance_label, db_path=None):
    """Update the statistics panel with current ITEMSDB table data."""
    try:
        stats = get_db_stats(db_path)
        if isinstance(total_items_label, tk.Label):  # Old style update
            if stats:
                total_items_label.config(text=f"Total Items: {stats['total_items']}")
                out_of_stock_label.config(text=f"Out of Stock: {stats['out_of_stock']}")
                low_stock_label.config(text=f"Low in Stock: {stats['low_stock']}")
                total_balance_label.config(text=f"Total Cost: ₱{stats['total_cost']:,.2f}")
        else:  # New style update (StatsPanel)
            total_items_label.update_stats(stats)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to update stats: {e}")

def set_stats_mode(mode, table, total_items_label, out_of_stock_label, low_stock_label, total_balance_label, db_path=None):
    """Set the statistics panel mode with animations."""
    try:
        # Treat 'default' same as ITEMS_LIST
        if mode in ("ITEMS_LIST", "default") and db_path:
            stats = get_db_stats(db_path, "ITEMS_LIST")
            if stats:
                if isinstance(total_items_label, tk.Label):  # Old style update
                    total_items_label.config(text=f"Total Items: {stats['total_items']}")
                    out_of_stock_label.config(text=f"Out of Stock: {stats['out_of_stock']}")
                    low_stock_label.config(text=f"Low Stock: {stats['low_stock']}")
                    total_balance_label.config(text=f"Total Cost: ₱{stats['total_cost']:,.2f}")
                else:  # New style update (StatsPanel)
                    total_items_label.update_stats(stats)

        elif mode in ["Restock List", "vrl"] and db_path:
            stats = get_db_stats(db_path, "Restock List")
            if stats:
                if isinstance(total_items_label, tk.Label):  # Old style update
                    total_items_label.config(text=f"Low Stock: {stats['low_stock']}")
                    low_stock_label.config(text=f"Out of Stock: {stats['out_of_stock']}")
                    out_of_stock_label.config(text=f"To Restock: {stats['total_restock']}")
                    # Show total cost for visibility even in restock view
                    if 'total_cost' in stats:
                        total_balance_label.config(text=f"Total Cost: ₱{stats['total_cost']:,.2f}")
                    else:
                        total_balance_label.config(text="")
                else:  # New style update (StatsPanel)
                    modified_stats = {
                        'total_items': stats['low_stock'],
                        'out_of_stock': stats['total_restock'],
                        'low_stock': stats['out_of_stock'],
                        'total_cost': stats.get('total_cost', 0)
                    }
                    total_items_label.update_stats(modified_stats)

        elif mode in ["Employee Logs", "Admin Logs"]:
            total_logs = len(table.get_children())
            current_date = time.strftime("%Y-%m-%d %H:%M:%S")
            if isinstance(total_items_label, tk.Label):  # Old style update
                total_items_label.config(text=f"Total Logs: {total_logs}")
                low_stock_label.config(text=f"Last Updated: {current_date}")
                out_of_stock_label.config(text=f"Current Date: {current_date}")
                total_balance_label.config(text="")
            else:  # New style update (StatsPanel)
                log_stats = {
                    'total_items': total_logs,
                    'out_of_stock': 0,
                    'low_stock': 0
                }
                total_items_label.update_stats(log_stats)

        elif mode == "hidden":
            if isinstance(total_items_label, tk.Label):  # Old style update
                total_items_label.config(text="")
                low_stock_label.config(text="")
                out_of_stock_label.config(text="")
                total_balance_label.config(text="")
            else:  # New style update (StatsPanel)
                empty_stats = {
                    'total_items': 0,
                    'out_of_stock': 0,
                    'low_stock': 0
                }
                total_items_label.update_stats(empty_stats)

    except Exception as e:
        messagebox.showerror("Error", f"Failed to update stats: {e}")