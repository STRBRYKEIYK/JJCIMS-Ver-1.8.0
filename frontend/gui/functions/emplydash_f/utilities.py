import tkinter as tk
from tkinter import ttk

def add_tooltip(widget, text):
    """Add a tooltip to a widget."""
    tooltip = tk.Toplevel(widget)
    tooltip.withdraw()
    tooltip.overrideredirect(True)  # Remove window decorations
    tooltip_label = tk.Label(tooltip, text=text, font=("Arial", 10), bg="yellow", relief="solid", borderwidth=1)
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


def update_clock(label, root):
    """Update the clock in the header."""
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    label.config(text=now)
    root.after(1000, lambda: update_clock(label, root))


def focus_next_widget(event):
    """Move focus to the next widget."""
    event.widget.tk_focusNext().focus()
    return "break"