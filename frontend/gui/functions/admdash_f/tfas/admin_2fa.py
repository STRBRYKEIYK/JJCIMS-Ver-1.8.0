import tkinter as tk
import pyotp
from backend.utils.window_icon import set_window_icon
# Sound imports removed
# No scanline import needed


class Admin2FA:
    def __init__(self, parent=None, secret=None, on_success=None):
        self.parent = parent
        self.secret = secret
        self.on_success = on_success

        # Check if parent window still exists before creating overlay
        if parent and not parent.winfo_exists():
            return

        # Create a fullscreen overlay for blur effect
        self.overlay = tk.Toplevel(self.parent) if self.parent else tk.Tk()
        self.overlay.attributes("-alpha", 0.7)  # Semi-transparent
        self.overlay.attributes("-fullscreen", True)
        self.overlay.configure(bg="#000000")  # Dark overlay

        # Set window icon
        set_window_icon(self.overlay)

        # Create borderless window
        self.window = tk.Toplevel(self.overlay)
        self.window.overrideredirect(True)  # Remove window decorations
        self.window.configure(bg="#000000")  # Consistent dark background
        self.window.attributes("-topmost", True)  # Keep on top
        self.window.focus_force()  # Autofocus the window

        # Set window icon
        set_window_icon(self.window)

        # Bind closure events to both windows
        self.window.protocol("WM_DELETE_WINDOW", self.close_windows)
        self.overlay.protocol("WM_DELETE_WINDOW", self.close_windows)

        # Frame for thin border
        self.frame = tk.Frame(self.window, bg="#000000", bd=0)
        self.frame.pack(fill="both", expand=True, padx=2, pady=2)  # 2px border

        self.setup_ui()
        self.center_window(500, 400)

        # Animation for smooth appearance
        self.overlay.attributes("-alpha", 0.0)
        self.fade_in()

        # Sound removed

    def fade_in(self):
        """Smooth fade-in animation for the overlay"""
        alpha = self.overlay.attributes("-alpha")
        if alpha < 0.7:
            alpha += 0.1
            self.overlay.attributes("-alpha", alpha)
            self.overlay.after(20, self.fade_in)

    def fade_out(self, callback):
        """Smooth fade-out animation for the overlay"""
        try:
            if not hasattr(self, "overlay") or not self.overlay.winfo_exists():
                callback()
                return
            alpha = self.overlay.attributes("-alpha")
            if alpha > 0:
                alpha -= 0.1
                self.overlay.attributes("-alpha", alpha)
                # Use a lambda with proper error handling
                self.overlay.after(20, lambda: self.safe_continue_fade_out(callback))
            else:
                self.overlay.after(
                    1, callback
                )  # Schedule callback for next event loop iteration
        except Exception:
            # If there's any error during fade out, just call the callback
            try:
                callback()
            except Exception:
                pass

    def safe_continue_fade_out(self, callback):
        """Safely continue the fade out animation."""
        try:
            if (
                hasattr(self, "overlay")
                and self.overlay
                and self.overlay.winfo_exists()
            ):
                self.fade_out(callback)
            else:
                callback()
        except Exception:
            try:
                callback()
            except Exception:
                pass

    def continue_fade_out(self, callback):
        """Continue the fade out animation."""
        try:
            if hasattr(self, "overlay") and self.overlay.winfo_exists():
                self.fade_out(callback)
            else:
                callback()
        except Exception:
            try:
                callback()
            except Exception:
                pass

    def close_windows(self):
        """Properly close both windows with fade effect"""

        def final_close():
            try:
                # First release any grabs
                try:
                    if hasattr(self, "window") and self.window.winfo_exists():
                        if self.window.grab_current() == self.window:
                            self.window.grab_release()
                    if hasattr(self, "overlay") and self.overlay.winfo_exists():
                        if self.overlay.grab_current() == self.overlay:
                            self.overlay.grab_release()
                except Exception:
                    pass

                # Then destroy windows in the correct order
                if hasattr(self, "window") and self.window.winfo_exists():
                    self.window.destroy()
                if hasattr(self, "overlay") and self.overlay.winfo_exists():
                    self.overlay.destroy()
            except Exception:
                pass

        # Start the fade out if the overlay still exists
        if hasattr(self, "overlay") and self.overlay.winfo_exists():
            try:
                self.fade_out(final_close)
            except Exception:
                # If fade out fails, just close immediately
                final_close()
        else:
            final_close()

    def setup_ui(self):
        # Title label
        title = tk.Label(
            self.frame,
            text="2FA Verification Required",
            font=("Segoe UI", 28, "bold"),
            bg="#000000",
            fg="#800000",
        )
        title.pack(pady=30)
        # Info label
        info = tk.Label(
            self.frame,
            text="Enter your 2FA code:",
            font=("Segoe UI", 14),
            bg="#000000",
            fg="#fffde7",
        )
        info.pack(pady=10)

        # 6 separate Entry fields for 2FA code
        entry_frame = tk.Frame(self.frame, bg="#000000")
        entry_frame.pack(pady=8)
        self.code_entries = []
        entry_width = 3
        for i in range(6):
            entry = tk.Entry(
                entry_frame,
                font=("Segoe UI", 24),
                bg="#23272b",
                fg="#fffde7",
                insertbackground="#fffde7",
                width=entry_width,
                relief="solid",
                justify="center",
            )
            entry.grid(row=0, column=i, padx=4)
            self.code_entries.append(entry)

        # Bind events for auto-advance and backspace
        def limit_to_one_digit(event):
            widget = event.widget
            value = widget.get()
            idx = self.code_entries.index(widget)
            if len(value) > 1:
                widget.delete(1, "end")
                value = widget.get()
            elif value and not value[-1].isdigit():
                widget.delete(len(value) - 1, "end")
                value = widget.get()
            if event.keysym == "BackSpace" and value == "":
                if idx > 0:
                    self.code_entries[idx - 1].focus_set()
                return
            if len(value) == 1:
                if idx < 5:
                    self.code_entries[idx + 1].focus_set()
                else:
                    self.verify_2fa()

        for entry in self.code_entries:
            entry.bind("<KeyRelease>", limit_to_one_digit)

        # Status label
        self.status_label = tk.Label(
            self.frame, text="", font=("Segoe UI", 12), bg="#000000", fg="#b71c1c"
        )
        self.status_label.pack(pady=5)

        # Buttons
        btn_frame = tk.Frame(self.frame, bg="#000000")
        btn_frame.pack(pady=40)
        verify_btn = tk.Button(
            btn_frame,
            text="Verify",
            font=("Segoe UI", 16, "bold"),
            bg="#800000",
            fg="#fffde7",
            width=16,
            height=2,
            command=self.verify_2fa,
        )
        verify_btn.pack(side="left", padx=15)
        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            font=("Segoe UI", 16, "bold"),
            bg="#232b2b",
            fg="#fffde7",
            width=16,
            height=2,
            command=self.close_windows,
        )
        cancel_btn.pack(side="left", padx=15)

        # Bind Enter to Verify and Esc to Cancel
        self.window.bind("<Return>", lambda event: self.verify_2fa())
        self.window.bind("<Escape>", lambda event: self.close_windows())

    def center_window(self, w, h):
        """Center the 2FA window on screen"""
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (w // 2)
        y = (self.window.winfo_screenheight() // 2) - (h // 2)
        self.window.geometry(f"{w}x{h}+{x}+{y}")

    def verify_2fa(self):
        try:
            code = "".join([e.get() for e in self.code_entries])
            if not code or len(code) != 6 or not code.isdigit():
                self.status_label.config(text="Please enter the 6-digit 2FA code.")
                return
            if not self.secret:
                self.status_label.config(text="2FA secret missing.")
                return
            totp = pyotp.TOTP(self.secret)
            if totp.verify(code):
                # Successful verification
                self.window.after(500, lambda: self.safe_close_windows())
                try:
                    if self.on_success:
                        self.on_success()
                except Exception as e:
                    print(f"Error in on_success callback: {e}")
                self.window.after(1000, lambda: self.safe_close_windows())
            else:
                self.status_label.config(text="Invalid 2FA code.")
        except Exception as e:
            print(f"Error in verify_2fa: {e}")
            self.status_label.config(text="Verification error occurred.")

    def safe_close_windows(self):
        """Safely close windows with error handling."""
        try:
            if hasattr(self, "window") and self.window and self.window.winfo_exists():
                self.close_windows()
        except Exception as e:
            print(f"Error closing windows: {e}")

    def show(self):
        try:
            # Ensure proper window state
            if not self.window.winfo_exists() or not self.overlay.winfo_exists():
                return
            # Set initial focus
            self.window.focus_force()
            if hasattr(self, "code_entries") and self.code_entries:
                self.code_entries[0].focus_set()
            # Properly set grab
            self.window.grab_set()
            # Wait for window
            try:
                self.window.wait_window()
            except Exception:
                pass
            # Clean up grab if needed
            try:
                if self.window.grab_current() == self.window:
                    self.window.grab_release()
                if self.overlay.grab_current() == self.overlay:
                    self.overlay.grab_release()
            except Exception:
                pass
        except Exception as e:
            print(f"Error in show method: {e}")
            try:
                self.close_windows()
            except Exception:
                pass


if __name__ == "__main__":
    Admin2FA().window.mainloop()
