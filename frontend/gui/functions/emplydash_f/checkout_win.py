import sys
import os
import tkinter as tk
from tkinter import messagebox
from backend.database import get_connector, get_db_path
from backend.database import queries
from pathlib import Path

# openpyxl removed - logging now uses Access DB via AccessConnector
from ...globals import global_state

from backend.config.gui_config import configure_window, center_window
from backend.utils.window_icon import set_window_icon

# Define colors - Dark muted pastel palette (consistent with dashboard)
BG_COLOR = "#2F3640"  # Dark charcoal background
HEADER_COLOR = "#40495A"  # Muted dark blue-gray for header
SIDEBAR_COLOR = "#535C68"  # Muted gray for sidebar
TEXT_PRIMARY = "#F5F6FA"  # Off-white text on dark backgrounds
TEXT_SECONDARY = "#A4B0BE"  # Muted light gray for secondary text
ACCENT_COLOR = "#70A1D7"  # Muted pastel blue for accents
BUTTON_PRIMARY = "#5F7C8A"  # Muted teal-gray for primary buttons
BUTTON_SECONDARY = "#6C7B7F"  # Muted slate gray for secondary buttons
SUCCESS_COLOR = "#7FB069"  # Muted pastel green for success
ERROR_COLOR = "#D63447"  # Muted red for errors
WARNING_COLOR = "#F8B500"  # Muted amber for warnings
TABLE_BG = "#40495A"  # Dark blue-gray table background
TABLE_HEADER = "#535C68"  # Muted gray table headers
SELECTION_COLOR = "#6C5CE7"  # Muted pastel purple for selections


# Define the resource_path function
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # for PyInstaller
    except AttributeError:
        base_path = os.path.abspath(".")  # for dev mode
    return os.path.join(base_path, relative_path)


class CheckoutWindow:
    def __init__(self, selected_items):
        # Merge duplicate items by summing their quantities
        unique_items = {}
        for item in selected_items:
            item_name = item[0]  # Use name as unique identifier
            if item_name in unique_items:
                unique_items[item_name]["quantity"] += 1
            else:
                # Ensure the item tuple has exactly 5 elements before adding quantity
                unique_items[item_name] = {"item": item[:5], "quantity": 1}

        self.selected_items = [
            unique_items[item_name]["item"] + (unique_items[item_name]["quantity"],)
            for item_name in unique_items
        ]

        # Initialize the rest of the UI
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        configure_window(
            self.root, title="JJCIMS - Checkout", width=1024, height=768, resizable=True
        )
        center_window(self.root)
        self.root.configure(bg=BG_COLOR)  # Dark background

        # Set consistent window icon
        set_window_icon(self.root)

        # Header
        self.header = tk.Frame(self.root, bg=HEADER_COLOR, height=50)
        self.header.pack(side=tk.TOP, fill=tk.X)

        # Create a container frame for the logo and user label
        self.header_content = tk.Frame(self.header, bg=HEADER_COLOR)
        self.header_content.pack(side=tk.TOP, pady=5)

        # Add the logo to the center of the header
        logo_path = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "assets"
            / "checkout.png"
        )
        try:
            logo_image = tk.PhotoImage(file=str(logo_path))
            self.logo_label = tk.Label(
                self.header_content, image=logo_image, bg=HEADER_COLOR
            )
            self.logo_label.image = (
                logo_image  # Keep a reference to avoid garbage collection
            )
            self.logo_label.pack(side=tk.LEFT, padx=10)
        except Exception as e:
            print(f"Error loading checkout logo: {e}")
            # Fallback text label if image fails
            self.logo_label = tk.Label(
                self.header_content,
                text="JJCFPIS - Checkout",
                font=("Arial", 16, "bold"),
                bg=HEADER_COLOR,
                fg=TEXT_PRIMARY,
            )
            self.logo_label.pack(side=tk.LEFT, padx=10)

        # Display the current user aligned with the logo
        current_user = (
            global_state.current_user if global_state.current_user else "Unknown User"
        )
        self.title_label = tk.Label(
            self.header_content,
            text=f"Employee: {current_user}",
            font=("Arial", 16, "bold"),
            bg=HEADER_COLOR,
            fg=TEXT_PRIMARY,
        )
        self.title_label.pack(side=tk.LEFT, padx=10)

        if not self.selected_items:
            tk.messagebox.showinfo("No Items", "No items in the cart to display.")
            return

        # Centralized database connection
        try:
            self.db = get_connector(get_db_path())
            self.db.connect()
        except Exception as e:
            print(f"Error connecting to database: {e}")
            tk.messagebox.showerror(
                "Database Error", f"Failed to connect to the database: {e}"
            )
            return

        # Table Frame
        self.table_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Table Headers
        headers = [
            "NAME",
            "BRAND",
            "TYPE",
            "LOCATION",
            "BALANCE",
            "   ",
            "QUANTITY",
            "   ",
            "   ",
        ]
        for col, header in enumerate(headers):
            label = tk.Label(
                self.table_frame,
                text=header,
                font=("Arial", 12, "bold"),
                bg=TABLE_HEADER,
                fg=TEXT_PRIMARY,
                borderwidth=1,
                relief="solid",
            )
            label.grid(row=0, column=col, sticky="nsew", padx=1, pady=1)

        # Populate Table Rows
        self.quantity_inputs = {}
        self.row_widgets = {}  # Track widgets per row for removal

        for row, item in enumerate(self.selected_items, start=1):
            name, brand, item_type, location, balance, quantity = item

            # Trash can button
            def remove_item(item_name=name):
                # Remove from selected_items using name as identifier
                self.selected_items = [
                    i for i in self.selected_items if i[0] != item_name
                ]
                self.root.destroy()
                if not self.selected_items:
                    from gui.employee_dashboard import MainBrowser

                    main_browser = MainBrowser()
                    main_browser.run()
                else:
                    # Otherwise, refresh the checkout window
                    CheckoutWindow(self.selected_items).run()

            # Load the trash can icon image
            trash_icon_path = (
                Path(__file__).resolve().parent.parent.parent.parent
                / "assets"
                / "x.png"
            )
            trash_icon = tk.PhotoImage(file=str(trash_icon_path))

            # Replace the trash can button with an image button
            trash_btn = tk.Button(
                self.table_frame,
                image=trash_icon,
                command=remove_item,
                bg=BG_COLOR,
                borderwidth=0,  # Remove border for a cleaner look
            )
            trash_btn.image = trash_icon  # Keep a reference to avoid garbage collection
            trash_btn.grid(row=row, column=8, sticky="nsew", padx=1, pady=1)

            tk.Label(
                self.table_frame,
                text=name,
                font=("Arial", 10),
                bg=TABLE_BG,
                fg=TEXT_PRIMARY,
                borderwidth=1,
                relief="solid",
            ).grid(row=row, column=0, sticky="nsew", padx=1, pady=1)
            tk.Label(
                self.table_frame,
                text=brand,
                font=("Arial", 10),
                bg=TABLE_BG,
                fg=TEXT_PRIMARY,
                borderwidth=1,
                relief="solid",
            ).grid(row=row, column=1, sticky="nsew", padx=1, pady=1)
            tk.Label(
                self.table_frame,
                text=item_type,
                font=("Arial", 10),
                bg=TABLE_BG,
                fg=TEXT_PRIMARY,
                borderwidth=1,
                relief="solid",
            ).grid(row=row, column=2, sticky="nsew", padx=1, pady=1)
            tk.Label(
                self.table_frame,
                text=location,
                font=("Arial", 10),
                bg=TABLE_BG,
                fg=TEXT_PRIMARY,
                borderwidth=1,
                relief="solid",
            ).grid(row=row, column=3, sticky="nsew", padx=1, pady=1)
            tk.Label(
                self.table_frame,
                text=balance,
                font=("Arial", 10),
                bg=TABLE_BG,
                fg=TEXT_PRIMARY,
                borderwidth=1,
                relief="solid",
            ).grid(row=row, column=4, sticky="nsew", padx=1, pady=1)

            quantity_var = tk.IntVar(value=quantity)
            self.quantity_inputs[name] = (
                quantity_var  # Use name as key instead of item_id
            )

            # Load the - button image
            minus_image_path = (
                Path(__file__).resolve().parent.parent.parent.parent
                / "assets"
                / "-.png"
            )
            minus_image = tk.PhotoImage(file=str(minus_image_path))

            # Replace the - button with an image button
            decrement_button = tk.Button(
                self.table_frame,
                image=minus_image,
                command=lambda qv=quantity_var: decrement_quantity(qv),
                bg=TABLE_BG,
                borderwidth=0,  # Remove border for a cleaner look
            )
            decrement_button.image = (
                minus_image  # Keep a reference to avoid garbage collection
            )
            decrement_button.grid(row=row, column=5, sticky="nsew", padx=1, pady=1)

            # Load the + button image
            plus_image_path = (
                Path(__file__).resolve().parent.parent.parent.parent
                / "assets"
                / "+.png"
            )
            plus_image = tk.PhotoImage(file=str(plus_image_path))

            # Replace the + button with an image button
            increment_button = tk.Button(
                self.table_frame,
                image=plus_image,
                command=lambda qv=quantity_var, bal=balance: increment_quantity(
                    qv, bal
                ),
                bg=TABLE_BG,
                borderwidth=0,  # Remove border for a cleaner look
            )
            increment_button.image = (
                plus_image  # Keep a reference to avoid garbage collection
            )
            increment_button.grid(row=row, column=7, sticky="nsew", padx=1, pady=1)

            def update_buttons(qv, dec_btn, inc_btn, max_balance):
                try:
                    value = int(qv.get())
                except Exception:
                    dec_btn.config(state=tk.DISABLED)
                    inc_btn.config(state=tk.DISABLED)
                    return
                if value <= 1:
                    dec_btn.config(state=tk.DISABLED)
                else:
                    dec_btn.config(state=tk.NORMAL)
                if value >= int(max_balance):
                    inc_btn.config(state=tk.DISABLED)
                else:
                    inc_btn.config(state=tk.NORMAL)

            # Entry validation: only allow digits
            def only_digits(P):
                return P.isdigit() or P == ""

            vcmd = (self.root.register(only_digits), "%P")

            def get_max_quantity(balance):
                try:
                    b = int(balance)
                except Exception:
                    b = 1
                return max(1, b)

            def validate_and_snap_quantity(
                *args, qv=None, max_balance=None, dec_btn=None, inc_btn=None
            ):
                max_qty = get_max_quantity(max_balance)
                value_str = str(qv.get())
                if value_str == "" or not value_str.isdigit():
                    qv.set(1)
                    update_buttons(qv, dec_btn, inc_btn, max_qty)
                    return
                value = int(value_str)
                if value < 1:
                    qv.set(1)
                elif value > max_qty:
                    qv.set(max_qty)
                update_buttons(qv, dec_btn, inc_btn, max_qty)

            entry = tk.Entry(
                self.table_frame,
                textvariable=quantity_var,
                font=("Arial", 10),
                justify="center",
                borderwidth=1,
                relief="solid",
                width=5,
                validate="key",
                validatecommand=vcmd,
                bg=HEADER_COLOR,
                fg=TEXT_PRIMARY,
                insertbackground=TEXT_PRIMARY,
            )
            entry.grid(row=row, column=6, sticky="nsew", padx=1, pady=1)
            entry.bind(
                "<FocusOut>",
                lambda e,
                qv=quantity_var,
                mb=balance,
                dec_btn=decrement_button,
                inc_btn=increment_button: validate_and_snap_quantity(
                    qv=qv, max_balance=mb, dec_btn=dec_btn, inc_btn=inc_btn
                ),
            )

            self.quantity_inputs[name] = (
                quantity_var  # Use name as key instead of item_id
            )

            # Attach the trace callback with the correct max_balance and buttons for this row
            quantity_var.trace_add(
                "write",
                lambda *args,
                qv=quantity_var,
                mb=balance,
                dec_btn=decrement_button,
                inc_btn=increment_button: validate_and_snap_quantity(
                    qv=qv, max_balance=mb, dec_btn=dec_btn, inc_btn=inc_btn
                ),
            )

        # Configure column weights for resizing
        for col in range(len(headers)):
            self.table_frame.grid_columnconfigure(col, weight=1)

        # Buttons
        self.button_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.button_frame.pack(fill=tk.X, pady=10)

        self.back_button = tk.Button(
            self.button_frame,
            text="Back",
            command=self.go_back,
            bg=BUTTON_SECONDARY,
            fg=TEXT_PRIMARY,
            font=("Arial", 12, "bold"),
        )
        self.back_button.pack(side=tk.LEFT, padx=10)

        self.confirm_button = tk.Button(
            self.button_frame,
            text="Confirm",
            command=self.confirm_order,
            bg=SUCCESS_COLOR,
            fg=TEXT_PRIMARY,
            font=("Arial", 12, "bold"),
        )
        self.confirm_button.pack(side=tk.RIGHT, padx=10)

        # Add keyboard shortcuts
        self.root.bind("<Escape>", lambda e: self.go_back())
        self.root.bind("<Return>", lambda e: self.confirm_order())

        # Optional: Add shortcut hints to button texts
        self.back_button.config(text="Back (Esc)")
        self.confirm_button.config(text="Confirm (Enter)")

        # Add copyright label at the bottom right
        copyright_label = tk.Label(
            self.root,
            text="© 2025 KWF",
            font=("Arial", 10, "italic"),
            bg=BG_COLOR,
            fg=TEXT_SECONDARY,
        )
        copyright_label.place(relx=1.0, rely=1.0, anchor="se", x=-150, y=-40)

        self.is_closing = False

    def confirm_order(self):
        """Confirm the order and update the database."""
        if getattr(self, "is_closing", False):
            return
        try:
            # Iterate over the selected items and their quantities
            for item in self.selected_items:
                name = item[0]  # The first element is the NAME
                brand = item[1]  # The second element is the BRAND
                item_type = item[2]  # The third element is the TYPE
                location = item[3]  # The fourth element is the LOCATION

                try:
                    quantity = int(self.quantity_inputs[name].get())
                    if quantity <= 0:
                        continue
                except ValueError:
                    messagebox.showerror(
                        "Input Error", f"Invalid quantity for item {name}."
                    )
                    continue

                # Update the database using centralized query helper
                try:
                    queries.update_item_out(self.db, name, quantity)
                except Exception as e:
                    messagebox.showerror(
                        "Database Error",
                        f"Failed to update database for item {name}: {e}",
                    )
                    continue

                # Log the action to JJCIMS.accdb in the new location
                log_file_path = Path(get_db_path())

                # Ensure the directory exists
                log_file_path.parent.mkdir(parents=True, exist_ok=True)

                # Fetch unit_of_measure from ITEMSDB based on the item name
                unit_of_measure = queries.get_unit_of_measure(self.db, name) or "pcs"

                # Create details string with all relevant information
                details = f"Took {quantity} {unit_of_measure} of {brand} {name} ({item_type}) from {location}."

                # log_entry list not used; logs are written to Access DB instead

                # Insert the log entry into the emp_logs table in the Access database
                try:
                    queries.insert_emp_log(self.db, global_state.current_user, details)
                except Exception as e:
                    messagebox.showerror("Log Error", f"Failed to write to logs: {e}")

            # Show success message
            messagebox.showinfo("Success", "Order confirmed and inventory updated!")

            # Ask the user if they want to order again
            response = messagebox.askyesno(
                "Order Again?", "Do you want to order more items?"
            )
            if response:  # Yes, go back to the main browser
                self.is_closing = True
                self.root.destroy()
                from gui.employee_dashboard import MainBrowser

                main_browser = MainBrowser()
                main_browser.run()
            else:  # No, go back to the welcome window
                self.is_closing = True
                self.root.destroy()
                from gui.employee_login import WelcomeWindow

                welcome_window = WelcomeWindow()
                welcome_window.run()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to confirm order: {e}")

    def go_back(self):
        """Go back to the main browser."""
        self.is_closing = True
        self.root.destroy()
        from gui.employee_dashboard import MainBrowser

        main_browser = MainBrowser()
        main_browser.run()

    def run(self):
        self.root.mainloop()


# Define the increment and decrement functions
def increment_quantity(quantity_var, balance):
    """Increment the quantity if it is less than the balance."""
    if quantity_var.get() < int(balance):
        quantity_var.set(quantity_var.get() + 1)


def decrement_quantity(quantity_var):
    """Decrement the quantity if it is greater than 1."""
    if quantity_var.get() > 1:
        quantity_var.set(quantity_var.get() - 1)
