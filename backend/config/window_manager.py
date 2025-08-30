import tkinter as tk

class WindowManager:
    def __init__(self):
        self.current_window = None

    def show_window(self, window_class, *args, **kwargs):
        """Hide the current window and show the new one."""
        if self.current_window:
            self.current_window.withdraw()  # Hide the current window
        new_window = window_class(*args, **kwargs)
        self.current_window = new_window
        new_window.run()

    def close_current_window(self):
        """Close the current window."""
        if self.current_window:
            self.current_window.destroy()
            self.current_window = None