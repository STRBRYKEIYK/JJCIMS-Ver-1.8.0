import tkinter as tk

def configure_window(window, title="Window", width=1024, height=768, resizable=True):
    """Configure a Tkinter window with consistent settings."""
    window.title(title)
    window.geometry(f"{width}x{height}")
    if not resizable:
        window.resizable(False, False)
    else:
        window.resizable(True, True)

def center_window(window):
    """Center the window on the screen."""
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    size = tuple(int(_) for _ in window.geometry().split('+')[0].split('x'))
    x = screen_width // 2 - size[0] // 2
    y = screen_height // 2 - size[1] // 2
    window.geometry(f"{size[0]}x{size[1]}+{x}+{y}")