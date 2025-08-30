import tkinter as tk

def create_tooltip(widget, text):
    """Create a tooltip for a widget with a black semi-transparent background and white text."""
    tooltip = tk.Toplevel(widget)
    tooltip.withdraw()  # Hide initially
    tooltip.overrideredirect(True)  # Remove window decorations for proper tooltip behavior
    # Use a black background with some transparency (alpha)
    tooltip.attributes("-alpha", 0.92)  # Semi-transparent
    tooltip_label = tk.Label(
        tooltip, text=text, font=("Arial", 10), bg="#000000", fg="#fffde7", relief="solid", borderwidth=1
    )
    tooltip_label.pack()

    def show_tooltip(event):
        tooltip.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
        tooltip.deiconify()

    def hide_tooltip(event):
        tooltip.withdraw()

    widget.bind("<Enter>", show_tooltip)
    widget.bind("<Leave>", hide_tooltip)

def add_tooltips(tooltips):
    """Add tooltips to a dictionary of widgets. Only add to clickable items."""
    for widget, text in tooltips.items():
        # Only add tooltip if widget is a Button or has a 'cursor' attribute set to 'hand2' (clickable)
        if isinstance(widget, tk.Button) or getattr(widget, 'cget', lambda x: None)('cursor') == 'hand2':
            create_tooltip(widget, text)
